# RAMSES

RAMSES 연구 저장소는 논문 소스와 재현용 코드를 서로 독립적으로 관리할 수
있도록 다음 두 작업 공간으로 구성됩니다.

## Directory layout

| Directory | Purpose |
| --- | --- |
| [`paper/`](paper/) | IEEE 논문을 빌드하는 데 필요한 LaTeX 소스, 참고문헌, 클래스, 표, 그림 및 제출 문서 |
| [`code/`](code/) | 측정 데이터 분석, 통계 계산, 표·그림 생성 코드, 테스트, 실행 문서 및 `data/`의 모의 데이터 |

### Paper workspace

논문은 `paper/`를 작업 디렉터리로 사용해 빌드합니다. 자세한 구성은
[`paper/README.md`](paper/README.md)를 참고하세요.

```sh
cd paper
latexmk -pdf main.tex
```

### Code workspace

분석 파이프라인은 저장소 루트에서 실행합니다. 전체 명령과 데이터 주의사항은
[`code/README.md`](code/README.md)에 정리되어 있습니다.

```sh
python3 code/analyze_results.py code/data/raw.jsonl code/data/summary.csv
python3 code/compute_stats.py code/data/raw.jsonl code/data/stats.csv \
        --baseline default --compare ramses
python3 code/make_tables.py
python3 code/make_figures.py
python3 -m unittest discover -s code/tests -v
```

`code/data/`에 포함된 값은 파이프라인 점검용 합성 데이터이며 논문의 실측
결과로 인용해서는 안 됩니다. 출판 전 실제 측정 데이터로 교체해야 합니다.
