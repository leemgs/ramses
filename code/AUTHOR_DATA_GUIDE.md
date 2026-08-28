# 저자 작성 가이드 — B(실측 데이터)·C(산업 태스크) 채우기

이 문서는 TII 재제출 전에 **저자가 직접** 채워야 하는 두 축을 단계별로 안내합니다.

- **B. 실제 원시 측정 데이터** — 이미 보유하신 2×A100 실험 결과를 스키마에 맞춰
  넣고, 논문의 표/그림 수치를 원시 로그에서 재계산합니다. (리뷰어 R2-6/10, R3-1/2/3/6/9/11)
- **C. 이름있는 재현 가능 산업 태스크 + 정확도** — 지연/메모리뿐 아니라 *task
  accuracy* 를 보고합니다. (리뷰어 R3-8, R2-3/4)

핵심 원칙(리뷰어가 가장 민감하게 봄):
> 어떤 수치도 정규화 막대그래프에서 역산하지 않습니다. 모든 값은 request-level
> 로그(JSONL)에서 파이프라인으로 계산되어야 하며, 측정하지 않은 필드는 비워 둡니다.

파이프라인 파일: `measurement-schema.json`(레코드 정의), `analyze_results.py`(백분위·
MAE/RMSE·에너지 집계), `compute_stats.py`(평균·표준편차·95% CI·유의성 검정),
`generate_trace.py`(72h 합성 트레이스), `preflight.sh`(하드웨어 점검).

---

## PART B — 실제 원시 측정 데이터

### B0. 측정 매트릭스 정의
각 조합마다 **독립 재시작 5회**(run_id = r1..r5) 이상 측정합니다.

- systems: `default`(PyTorch), `flexgen`, `swapadvisor`, `neo`, `specoffload`,
  `vllm`, `ramses`, 그리고 컨트롤러 절제용 `ramses_policy_off`.
- tasks: `scoring`(순전파 1회), `continuation`(warm decode 1스텝),
  `ttft`(도착→첫 토큰), `generation`(도착→마지막 토큰).
- configs: 논문에서 쓴 모델(Llama-4 17B, Llama-3 8B, GPT-J 6B, Mixtral 8×7B,
  ViT-H/14), precision(fp16/fp32), input/output length, batch(1,8…), concurrency.
- cold/warm 캐시 각각. 실패 요청도 분모에 포함.

### B1. JSONL 레코드 만들기 (필드별 측정법)
`measurement-schema.json`의 한 줄 = 요청 1건. 필수 11개 + 선택(모델/에너지) 필드.

| 필드 | 측정 방법 |
|---|---|
| `latency_ms` | task별 벽시계. scoring/continuation은 단일 스텝, ttft는 도착→첫 토큰, generation은 도착→종료. `torch.cuda.synchronize()` 후 계측 |
| `input_tokens`/`output_tokens` | 토크나이저 출력 길이 |
| `batch`/`concurrency`/`request_count` | 러너 설정값 |
| `precision`/`model`/`system`/`run_id` | 실행 메타데이터 |
| `alpha` | `D/C_f`. D=해당 스텝 상주+요구 바이트, C_f=VRAM+DRAM 가용용량 |
| `beta` | `(L0+q+V↑/B↑+V↓/B↓)/(T_comp+T_mem+T_sync)` — 아래 카운터로 계산 |
| `predicted_ms` | 식 (T_total)에 측정값 대입한 예측치 (→ MAE/RMSE 자동 산출) |
| `read_bw_gbps`/`write_bw_gbps` | 방향별 실효 대역폭. `nvme`/`iostat`를 실험과 동일 블록·큐깊이로 |
| `queue_ms` | 스토리지 큐잉 지연 |
| `prefetch_hits`/`prefetch_misses` | GPU Booster 계측 카운터 |
| `bytes_read`/`bytes_written` | 방향별 전송량(블록 라운딩 포함) |
| `gpu_energy_j` | NVML 200ms 적분, idle 차감 |
| `node_energy_j` | **whole-node**: CPU+DRAM(RAPL) + NVMe + GPU 동기 적분 (R3-11, 아래 B4) |
| `tokens`/`throughput_tps` | 에너지/토큰·TP/W 계산용 |

레코드 예시(한 줄):
```json
{"run_id":"r1","system":"ramses","task":"ttft","model":"llama4-17b","precision":"fp16","input_tokens":128,"output_tokens":1,"batch":1,"concurrency":1,"request_count":1,"latency_ms":552.3,"alpha":0.83,"beta":0.71,"predicted_ms":561.0,"read_bw_gbps":6.1,"write_bw_gbps":3.4,"queue_ms":2.2,"prefetch_hits":181,"prefetch_misses":19,"bytes_read":734003200,"bytes_written":0,"gpu_energy_j":214.7,"node_energy_j":401.9,"tokens":1,"throughput_tps":1.81}
```

### B2. 전체 노드 에너지 측정 (R3-11 — 가장 중요)
GPU-only NVML만으로는 부족합니다. **`code/collect_energy.py`** 가 동일 monotonic
클록으로 GPU(NVML)+CPU package/DRAM(RAPL)을 적분하고 카운터 wrap과 idle 차감을
처리해 `gpu_energy_j`/`node_energy_j`를 산출합니다.
```sh
python3 code/collect_energy.py --idle-seconds 5 --out energy.json -- \
        python run_inference.py --system ramses ...
```
- **NVMe**: 드라이브 전력(가능하면 PDU 분해) 또는 실측 전력 모델을 컴포넌트에 추가.
- **(권장) 랙 PDU**: Yokogawa WT310E 등으로 절대 whole-node 확인.
- 산출된 `node_energy_j`/`gpu_energy_j`를 각 JSONL 레코드(`data/actual/`)에 기록하면
  `analyze_results.py`가 J/req·J/token·EDP를 자동 계산합니다.
- RAPL/NVML이 없으면 조작 대신 unavailable로 정직 표기합니다.

### B3. 파이프라인 실행
```sh
code/preflight.sh                                   # 하드웨어/툴 점검 (fail-closed)
python3 code/analyze_results.py code/data/actual/raw.jsonl code/data/actual/summary.csv
python3 code/compute_stats.py code/data/actual/raw.jsonl code/data/actual/stats.csv \
        --metric latency_ms --baseline default --compare ramses
python3 -m unittest discover -s code/tests -v
```
- `summary.csv`: (system,task,config)별 median/P95/P99/P99.9/max, MAE/RMSE,
  prefetch hit rate, 방향별 트래픽, energy/request, energy/token, EDP.
- `stats.csv`: run 평균·표준편차·**95% CI**, 그리고 콘솔에 Welch t-검정(유의성).

### B4. 통계 보고 (R3-9)
- 각 대표 수치에 **평균 ± 95% CI**(`stats.csv`)를 붙입니다.
- RAMSES vs 각 baseline은 `compute_stats.py --baseline <sys> --compare ramses`로
  유의성(t, df, tcrit, significant 여부)을 첨부. 필요 시 Wilcoxon로 보강.

### B5. 컨트롤러 policy-off 절제 (R3-6)
`ramses`와 `ramses_policy_off`를 **동일 trace·seed**로 페어 실행(3 모듈 유지,
regime switching만 off). 두 시스템의 p99/에너지 차이를 표로. 논문 §III-F가
이 실험을 이미 서술하므로, 결과 표만 채우면 됩니다.

### B6. 파라미터·블록크기 민감도 (R2-6, R3-7)
- 블록크기 sweep: 1/2/4/8/16 MB → latency·유효대역폭 곡선(4 MB 선택 근거).
- 컨트롤러: sampling(100/200/400ms), hysteresis(2/5/10%), reuse window(16/32/64)
  각각 1축 sweep → p99 민감도. 새 그림/표 1개로 §IV에 추가 권장.

### B7. baseline 재현성 (R3-9)
`BASELINE_MANIFEST.md`의 `record` 칸을 실제 값으로: 각 시스템의 커밋/이미지
digest, 포트/패치, precision, cold/warm 프로토콜, 튜닝 예산, vLLM Llama-4 패치.

### B8. 논문 반영 위치
| 데이터 | 넣을 곳 |
|---|---|
| per-task 절대 백분위표 | §IV-A 뒤 새 표(또는 보충자료), 본문에서 참조 |
| CI·유의성 | Table IV(ablation), Fig. 3 캡션, §IV 각 수치 |
| whole-node 에너지(J/req, J/token, EDP) | §IV Energy 절 표로 승격(현재 GPU-only 옆) |
| policy-off 결과 | §III-F / §IV ablation |
| 민감도 곡선 | §IV 새 그림 |
| 측정 α/β·잔차 | Fig. 2에 측정 operating point 오버레이 + MAE/RMSE 한 줄 |

---

## PART C — 이름있는 산업 태스크 + 정확도 (R3-8)

리뷰어 요구: **최소 1개의 이름있고 재현 가능한 산업 태스크**를 데이터셋·프롬프트·
입출력 길이·precision·배치·정확도(task accuracy)와 함께. 가능하면 PLC/TSN
hardware/software-in-the-loop.

### C1. Fig. 1의 3개 워크로드 → 공개 데이터셋 매핑(권장안)
| 산업 워크로드 | 공개 데이터셋(named) | 모델 | 정확도 지표 |
|---|---|---|---|
| 실시간 시각 검사 | **MVTec AD** 또는 **VisA**(제조 결함 탐지) | ViT-H/14 | image-AUROC / 분류 정확도 |
| 예지보전(로그/센서 이상 설명) | **NASA C-MAPSS** 또는 **AI4I 2020**(센서)→요약/이상판정 텍스트화 | Llama-4 17B | 이상판정 F1 / 정확도 |
| 디지털 트윈 상태 질의응답 | 도메인 QA(예: 공정 로그 기반 QA 세트) | Llama-3 8B / Mixtral | Exact-Match / F1 |

최소 요건은 **1개**(예: MVTec AD + ViT-H/14)면 충족됩니다. 나머지는 선택.

### C2. task accuracy 측정
- 데이터셋 공식 split·metric 사용(예: MVTec AD는 image-level AUROC).
- 각 태스크에 dataset 버전, 샘플 수, 프롬프트/전처리, precision, expert/tensor
  placement, concurrency, request mix를 명시.

### C2-bis. 바로 실행 가능한 백엔드 (`code/mvtec_vit.py`)
`code/mvtec_vit.py` 가 MVTec AD 로더 + ViT(deep-feature-distance) 이상탐지를
구현합니다. LD_PRELOAD는 프로세스 전역이므로 **모드별 별도 프로세스 → compare**로
정확도·출력동등성을 산출합니다:
```sh
MVTEC_CATEGORY=bottle python3 code/eval_industrial.py --backend mvtec_vit \
    --data-root /path/to/mvtec --mode single --serving-mode baseline \
    --outputs-file out_baseline.json
LD_PRELOAD=/path/to/ramses.so MVTEC_CATEGORY=bottle \
    python3 code/eval_industrial.py --backend mvtec_vit \
    --data-root /path/to/mvtec --mode single --serving-mode ramses \
    --outputs-file out_ramses.json
python3 code/eval_industrial.py --compare out_baseline.json out_ramses.json \
    --out-csv code/data/actual/industrial_accuracy.csv
```
그런 다음 `make_tables.py --industrial code/data/actual/industrial_accuracy.csv`로
`paper/tables/industrial_body.tex`를 생성하면 Table가 채워집니다.

### C3. 출력 동등성(가장 방어적인 "정확도" 논거)
RAMSES는 서빙 최적화이지 모델 변경이 아니므로, **동일 입력에 대해 baseline과
동일 출력**임을 보이면 "정확도 불변 + 지연/메모리 개선"이 성립:
- FP32: 비트 동일(bitwise) 비교, FP16: 허용오차 내 일치율(%) 보고.
- 결과: "task accuracy는 baseline과 동일(출력 동등), 개선은 지연/VRAM/에너지에서".
- 이는 §III-C(출력 동등성 검사)와 직접 연결되며 별도 표 1개면 충분.

### C4. (선택) PLC/TSN in-the-loop
실물 PLC가 없으면 software-in-the-loop로도 리뷰어 요구를 상당 부분 충족:
- PLC: **OpenPLC** 시뮬레이터로 scan-cycle(예 10 ms) 구동, 추론 결과를 제어
  변수로 피드백.
- TSN: Linux `tc`(802.1Qbv/taprio qdisc) 또는 ns-3 TSN 모듈로 타임슬롯 윈도우.
- 보고: 추론 완료가 scan-cycle 내 들어오는 비율(QoS), 놓친 사이클 처리.
- **주의**: 여기서도 "deadline 보장/SIL"이 아니라 QoS 관측으로만 기술(현 §III-G
  disclaimer 유지).

### C5. 논문 반영 위치
- §IV에 "Named Industrial Task Evaluation" 서브섹션 신설:
  데이터셋·정확도 표 + 출력 동등성 표.
- Abstract/Introduction에 "on a named industrial defect-inspection task
  (MVTec AD), RAMSES preserves task accuracy while reducing …" 한 문장 추가.
- Table I의 RAMSES 행 근거 강화(이름있는 태스크로 평가).

---

## 제출 전 최종 체크리스트
- [ ] `raw.jsonl` (모든 system×task×config×5run, cold/warm) 를 `code/data/`에 포함
- [ ] `summary.csv`, `stats.csv` 재생성 후 본문 수치와 일치 확인
- [ ] whole-node 에너지(J/req·J/token·EDP) 표 승격
- [ ] policy-off·민감도 결과 표/그림 추가
- [ ] `BASELINE_MANIFEST.md` 전 칸 실제 값
- [ ] C: 최소 1개 named 태스크 정확도 + 출력 동등성 표
- [ ] §IV-C-1 baseline별 개선율이 Fig. 3 막대와 정합(이전 메모의 잠재 불일치 확인)
- [ ] PDF 클린 빌드(`pdflatex→bibtex→pdflatex×2`) 및 수식/그림 육안 검토
- [ ] cover letter + point-by-point(REVIEW_RESPONSE.md)에 신규 결과 반영
