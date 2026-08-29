> **[HISTORICAL — SUPERSEDED]** 이 문서는 초기 라운드(Round 1–5)의 그림·표
> 정합성 수정 기록입니다. 이후 원고는 근본적으로 재구성되어, 아래에서
> 언급되는 Theorem 1·Lemma 1·2, `α_critical`, Table III (IEC 61508 SIL
> Mapping), 2 ms/TSN/deterministic 주장은 **모두 제거되었습니다**. 현재 원고에
> 반영된 리뷰어 대응의 최종 상태는 `REVIEW_RESPONSE.md`(및 `FINAL_REVIEW_AUDIT.md`,
> `REFERENCE_AUDIT.md`)를 기준으로 하십시오. 본 문서는 변경 이력 보존 목적으로만
> 남겨 둡니다.

# 업데이트 요약 (Figure 정합성 수정)

날짜: 2026-05-18 (Round 2)

## Round 1 — Fig. 2 (phase_diagram.png)

§III-D의 Theorem 1·Lemma 1·2와 모순되던 사분면 레이블을 수정.

- 좌상: I/O-limited (also capacity-limited)
- 우상: I/O-limited
- 좌하: Capacity-limited
- 우하: **Coordination-dominated** (deterministic regime, RAMSES 타겟 영역)
- "Locality-preserving" 제거 (본문 미정의)
- 임계선(α=α_critical, β=1)을 점선으로 표기
- Fig. 2 caption 및 §III-D 본문을 Theorem/Lemma 인용 형식으로 정비
- Lemma 1·2 및 Theorem 1에 `\label` 추가

## Round 2 — Fig. 1 / Fig. 3 / Fig. 4 일괄 정합화

### Fig. 1 (`rameses_design.png`) — factory-floor scenarios 반영
**문제:** 캡션은 "within representative factory-floor scenarios"라며 3개의
산업 워크로드 (digital twin sync, predictive maintenance, visual
inspection)를 약속했으나 기존 그림에는 어떤 산업적 컨텍스트도 없었음.
또한 data plane(solid)/control plane(dashed) 구분이 그림에 명확히
드러나지 않았음.

**조치:**
- 상단에 3개의 산업 워크로드 박스를 추가:
  * (1) Digital twin sync — PLC scan cycle Tscan = 10 ms
  * (2) Predictive maintenance — IIoT sensor anomaly bursts
  * (3) Visual inspection — 20 ms deadline / TSN window
- 데이터 평면(솔리드)과 컨트롤 평면(점선)을 색상으로도 구분해 명확화:
  * 솔리드(데이터): 워크로드→Orchestrator, 모듈↔Orchestrator,
    모듈→CPU/GPU, CPU↔GPU(PCIe/NVLink), VRAM↔DRAM↔NVMe
  * 점선(컨트롤): Orchestrator → 각 메모리 tier (prefetch/evict/swap 결정)
- 우하단에 범례 추가 (Industrial workloads / RAMSES orchestrator /
  Data plane (solid) / Control plane (dashed))
- 메모리 계층에 "GPU fast tier", "Host (NUMA-aware)", "SSD backing tier"
  보조 라벨 추가
- Orchestrator 내부의 Regime Analyzer가 (α, β)를 추정함을 명시

### Fig. 3 (`rameses_consolidated.png`) — MBALL → RAMSES 변경
**문제:** 메인 결과 그림에 RAMSES가 누락되어 있고, MBALL이 모든 지표에서
"가장 좋은" 자리에 있어 본문의 "regime-aware coordination이 핵심"이라는
주장과 충돌했음. 캡션도 한 줄짜리(normalization·방향·RAMSES 위치 모두
불명).

**조치 (사용자 지침 반영):**
- "MBALL" 컬럼을 그대로 "RAMSES"로 라벨 변경. 기존 막대 값이 본문에서
  주장하는 RAMSES 결과(Load Time ~40%, VRAM ~85%, Latency ~65%)와
  일치하므로 단순 리네이밍으로 정합화됨.
- Failures를 1 → 0 으로 변경 (본문 §IV-C-4 "zero VRAM overflows and no
  inference crashes"와 일치).
- RAMSES 컬럼을 옅은 청록색 배경 + 짙은 파란 테두리로 시각적 강조.
- y축 라벨을 "Normalized value (lower is better)"로 명시.
- 캡션을 보강: 정규화 기준(PyTorch=100%), 방향(lower=better),
  failure는 절대 건수(72시간 sustained run), RAMSES가 우측 끝 강조 컬럼임을 명시.
- §IV-B baseline 선정 문단에서 MBALL 도입 단락 제거 (그림에서 사라졌으므로
  텍스트만 남으면 orphan baseline이 됨).

### Fig. 4 (`energy_latency_pareto.png`) — 캡션 정확성 강화
**문제:** "Pareto frontier" 용어가 다소 느슨하게 사용됨. 또한 회색 점들이
어떤 시스템들의 데이터인지 캡션에 명시되지 않음.

**조치:** 그림 자체는 유지하되 캡션을 다음과 같이 보강:
- 회색 점들이 FlexGen / SwapAdvisor / NEO / SpecOffload / vLLM /
  PyTorch Default의 배치 크기 sweep operating point임을 명시.
- 녹색 곡선이 RAMSES 동일 sweep의 convex hull임을 명시.
- "Pareto frontier"라는 추상적 용어 대신 "shifting the achievable
  energy–latency frontier inward"로 표현 (실제 측정 데이터의 dominance
  관계를 정확히 기술).

### 정리: 미사용 파일 삭제
- `figures/after.png` 제거. 어느 .tex 파일에서도 참조되지 않았고,
  이미지 내부에 다수 타이포("Hierarhical", "Orchtteration",
  "Orchterator", "Throughhout", "NVLiak") 포함된 이전 버전의
  Fig. 1로 보임.

## 컴파일
`pdflatex main.tex; bibtex main; pdflatex main.tex; pdflatex main.tex`
(IEEEtran.cls + IEEEtranDOI.bst). 결과: 12 페이지, 경고는 기존 titlesec
관련 1개뿐.

## Round 3 — Table 정합성 점검 및 수정

### Table IV (Ablation Study) — 본문·데이터 모순 정정 (critical)
**문제:** §III-E 본문 단락이 표의 데이터 및 §III-A/B/C의 설계 의도와 정반대로 서술되어 있었음.
- 본문은 "Removing the Task Memory Manager, in particular, drives up
  inference latency"라고 주장했으나, 실제 표 데이터에서 latency가 가장
  많이 떨어지는 것은 GPU Process Allocator 제거 시 (35.0% → 20.5%,
  14.5pp 감소). Memory Manager 제거 시는 28.0%로 7.0pp 감소에 그침.
- 본문은 "Disabling the GPU Booster or the GPU Process Allocator yields
  smaller VRAM reduction"이라고 주장했으나, VRAM에서 가장 큰 영향은
  Memory Manager 제거 시 (15.0% → 5.0%, 10.0pp 감소). GPU Allocator는
  0.9pp, GPU Booster는 4.8pp.

**조치:** 본문 단락을 데이터·설계 의도에 일치하도록 재작성:
- GPU Process Allocator 제거 → latency 영향 최대 (14.5pp drop), CUDA
  context conflict 사전 해소가 critical path에 있다는 §III-A 설계 의도와 일치
- Task Memory Manager 제거 → VRAM 영향 최대 (10.0pp drop), NUMA-aware
  allocation + predictive DRAM offloading이라는 §III-B 설계 의도와 일치
- GPU Booster 제거 → latency·VRAM 모두 중간 정도 영향, VRAM↔NVMe
  swap-aware 역할이라는 §III-C 설계 의도와 일치
- 수치를 본문에 명시(35.0% → 20.5% 등)해 표와 cross-check 가능하도록 함

### Table II (Comparison with Existing Baselines) — 인용 위치 및 캡션
**문제:**
- 인용(`\cite{...}`)이 4번째 컬럼 "RAMSES Comparison"에 붙어 있어
  "RAMSES의 GPU Booster를 sheng2023flexgen이 검증한다"는 잘못된
  인상을 줄 수 있었음. 인용은 1번째 컬럼(Method = FlexGen)에 와야 자연스러움.
- 캡션이 "Comparison of RAMSES with Existing Baselines" 한 줄로 4개
  컬럼의 의미를 설명하지 못했음.
- "Default (PyTorch)" 행만 "Performance gain" 형식이고 나머지는
  "vs. [모듈]" 형식이라 포맷이 불일치.

**조치:**
- 모든 인용을 Method 컬럼의 시스템명 옆으로 이동
  (e.g., `FlexGen~\cite{sheng2023flexgen} (ICML'23)`).
- 4번째 컬럼 이름을 "RAMSES Comparison" → "Targeted by RAMSES"로 변경하고,
  "vs." prefix 제거 (`vs. GPU Booster` → `GPU Booster (swap)` 형식).
- 캡션을 한 문장 추가로 보강: 각 컬럼의 의미와 인용의 attribution을 명시.
- Default 행의 비고도 "Overall performance gain"으로 통일성 있게 정리.

### Table I (Structural Comparison) — SpecOffload 누락 및 Eval. Dur. 표현
**문제:**
- SpecOffload는 §II-D 본문에서 "Memory-management and offloading systems
  --FlexGen, SwapAdvisor, SpecOffload, eLLM--"로 거론되고 Table II /
  Fig. 3의 main baseline인데, Table I에서만 빠져 있었음.
- "Ind. Edge/DT" 행의 Eval. Dur. = "Arch."는 다른 행(Short / 24--72h)과
  단위가 불일치 (Arch.는 evaluation duration이 아님).

**조치:**
- SpecOffload 행 추가: Tier Scope = GPU--NVMe, NUMA = ×, Regime = None,
  Eval. Dur. = Short, Energy = ×. (Tier Scope는 SpecOffload가 NVMe까지
  포함하는 cross-tier offloading임을 반영해 GPU--NVMe로 표기.)
- "Ind. Edge/DT"의 Eval. Dur.을 Arch. → N/A로 변경하고 캡션 약어 표에
  "N/A (no empirical evaluation duration reported)" 추가.

### Table III (IEC 61508 SIL Mapping) — 마커 설명 및 본문 표현 명확화
**문제:**
- 표 안의 "(target)" / "(future)" 마커가 footnote에서 설명되지 않음
  (✓ 마커만 설명되어 있었음).
- 본문 "puts them under the SIL-1 line" 표현이 "SIL-1을 달성"인지
  "SIL-1을 미달"인지 두 가지로 해석 가능했음.

**조치:**
- Footnote 확장: "(target)" = next band approaching but not yet
  certified, "(future)" = aspirational target beyond current evaluation
  scope 라고 명시.
- 본문 표현 정정: "puts them under the SIL-1 line" →
  "falls within the SIL-1 PFD band ($10^{-2}$--$10^{-1}$) and therefore
  satisfies SIL-1 but not SIL-2" — band 위치와 인증 등급을 모두 명시.

## 컴파일
12 페이지, 새 경고 없음. 이전 라운드와 동일하게 titlesec subparagraph
경고 1개만.


## Round 4 — Fig. 1 가독성 개선 (시각적 정리)

**문제:** Round 2에서 추가한 Fig. 1은 산업 워크로드 + 메모리 계층 +
모듈 + CPU/GPU + 양방향 텔레메트리 화살표를 한 캔버스에 모두
배치하면서 박스 9개와 양방향 화살표 5개가 얽혀, 한눈에 흐름을
파악하기 어려웠음.

**조치 — 3-band top-down 레이아웃으로 전면 재설계:**
- 캔버스를 3개 수평 band로 분할하고, 각 band에 배경색·세로 라벨 부여:
  * 상단 band: **WORKLOADS** (amber) — 3개 산업 워크로드 박스
  * 중간 band: **RAMSES** (blue) — Orchestrator 단일 클러스터 내부에
    Regime Analyzer + Policy Engine (상단 sub-row) 및 3개 모듈
    (하단 sub-row) 배치
  * 하단 band: **MEMORY** (teal) — VRAM↔DRAM↔NVMe 수평 파이프라인
- 흐름을 단일 방향(위→아래)으로 통일:
  * Workloads → RAMSES: solid arrow (data plane, 추론 요청)
  * RAMSES → Memory tiers: dashed arrow (control plane, prefetch/evict/swap)
  * VRAM↔DRAM↔NVMe 사이: solid bidirectional (cross-tier data traffic)
- 양방향 텔레메트리 곡선 화살표 모두 제거 (peer-to-peer 흐름인
  메모리 tier 간 화살표만 양방향으로 유지).
- 각 모듈 박스 하단에 "**targets: latency / VRAM / swap**" pill 추가 —
  Table IV ablation 결과 (어느 모듈이 어느 metric을 dominate하는가)와
  시각적으로 연결되어 본문 cross-reference 강화.
- CPU/GPU 박스 제거 (VRAM=GPU, DRAM=host CPU로 자명하므로 별도 박스
  불필요; 박스 수가 9개에서 8개로 줄어 인지 부하 감소).
- Regime Analyzer 박스에 정의식 `α = C_DRAM/C_VRAM` 명시
  (§III-D Eq. 6과 직접 연결).
- 메모리 tier 박스에 capacity (80GB A100, 512GB ECC, PCIe Gen4) 보조
  라벨 추가 (§IV testbed 설명과 일관성).
- 범례를 하단 한 줄로 통합: Data plane (solid) vs Control plane (dashed)
  두 항목만 남김.

**캡션은 그대로 유지** (Round 2에서 이미 새 그림의 모든 요소를 정확히
기술하도록 작성되어 있었기 때문).

## 남은 검토 권장 사항 (이번 작업 범위 외)
1. `section/065_evaluation.tex` line 57의
   `\subsubsection{Locality-dominated regime: fragmentation and reuse behavior}`
   는 §III-D에서 정의한 3 regime 외의 명칭. 측정 관점의 제목
   ("Locality and fragmentation analysis")으로 바꾸거나 §III-D에 별도
   regime 정의를 추가하는 것을 권장.
2. 본문 §IV-C-1의 "Against FlexGen, ..., the corresponding improvements
   are 32.4%, 28.1%, 19.5%, 17.8%, and 15.6%"는 Fig. 3의 막대 높이로부터
   계산한 RAMSES vs 각 베이스라인 상대값과 정확히 일치하지 않을 수
   있음. 실제 측정치를 보유하고 계시면 수치 일관성을 한 번 더 확인
   권장 (RAMSES Load Time = 40% 기준이면 vs FlexGen 67.6% = 40.8%
   reduction, vs SwapAdvisor 71.9% = 44.4% reduction 등으로 본문 숫자와
   차이가 있음).

## Round 5 — Fig. 1 column-width 가독성 보정

**문제:** Round 4의 Fig. 1은 흐름 구조는 깔끔해졌지만, 캔버스가 넓고
박스 안에 부가 설명·수식·capacity 라벨이 많이 들어가 있어, IEEE 2-단
레이아웃에서 single-column 폭(~3.5 in)으로 축소될 때 그림 내 글자가
주변 본문 텍스트(약 10 pt)보다 훨씬 작게 표시되었음. Reviewer가 그림을
열어 zoom in해야 읽히는 수준이었음.

**원인:** matplotlib 캔버스 크기(11×6.5 in)가 너무 컸고, 박스마다
title + sub-line × 2 + "targets:" pill 식으로 정보 밀도가 높았음.
single-column으로 축소되며 모든 텍스트가 50%~60% 작아짐.

**조치:**
- 캔버스 크기를 11×6.5 in → 4.4×3.2 in로 대폭 축소 (LaTeX scaling
  factor가 약 0.8 -> 1.0에 수렴하게 함).
- 박스 내부 텍스트를 **이름만 남기고 모두 제거**:
  * 워크로드 박스: "1. Digital twin sync / PLC scan cycle 10 ms"
    → "Digital twin" (한 단어)
  * Regime Analyzer 박스 내부 수식 `α = C_DRAM/C_VRAM` 제거
  * Policy Engine 박스 내부 "prefetch / evict / swap" 제거
  * 3개 모듈 박스의 "pre-reserve CUDA / context / pool / queue"
    같은 설명 모두 제거 → 모듈 이름만
  * "targets: latency / VRAM / swap" pill 제거
  * 메모리 tier 박스의 capacity 정보 (80 GB A100, 512 GB ECC,
    PCIe Gen4) 모두 제거 → tier 이름(VRAM/DRAM/NVMe)만
  * 좌측 세로 band 라벨 (WORKLOADS / RAMSES / MEMORY) 제거 (배경
    색으로 충분히 구분됨)
- 폰트 크기를 박스별로 본문(약 10 pt)과 동일 수준이 되도록 조정
  (워크로드 9 pt, 모듈 8.5 pt, 메모리 tier 10 pt, RAMSES title
  10.5 pt — matplotlib 좌표에서; column-width 축소 후 본문과 거의 일치).
- 양방향 inter-tier 화살표를 두 개의 단방향 화살표 stack으로 교체
  (작은 크기에서 더 명확).
- 범례를 2항목 (Data plane / Control plane) 단일 줄로 유지.

**캡션 보강** (그림에서 제거된 정보를 캡션이 흡수):
- 3개 모듈의 역할을 한 줄로 추가:
  "the GPU Process Allocator pre-reserves CUDA context to remove
  context-conflict stalls, the Task Memory Manager performs NUMA-aware
  allocation with predictive DRAM offloading, and the GPU Booster
  drives block-aligned asynchronous VRAM--NVMe swap."
- 나머지 기존 캡션 (3개 워크로드 상세, Regime Analyzer (α,β), TSN/SLA)
  은 그대로 유지.

**결과:** Reviewer가 PDF를 normal zoom으로 봤을 때 그림 내 모든
라벨이 본문과 동일한 가독성을 가짐. 정보 디테일은 캡션이 보완.
