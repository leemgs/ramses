# Anonymized review artifact

This directory contains all executable artifact code, tests, documentation,
and mock inputs. Input and derived CSV/JSONL files are grouped under `data/`;
paper-facing outputs are written to the sibling `../paper/tables/` and
`../paper/figures/` directories. The LaTeX manuscript itself is isolated in
`../paper/`.

`generate_trace.py` produces a parameterized synthetic arrival schedule intended for sustained-load testing. It is synthetic, not a released factory log. The default seed is fixed for reproduction.

```sh
python3 code/generate_trace.py --hours 72 --seed 5047 --output code/data/trace.csv
```

Columns are timestamp, request class, and requested concurrency. The nominal periodic component is 10 ms with Gaussian jitter (standard deviation 1.5 ms, truncated at 1 ms); anomaly bursts occur independently with probability 0.012 per arrival and concurrency 2–6. These are generator parameters, not claims about a specific plant. Users must recalibrate them against their own traces. The manuscript's model-serving measurements require the RAMSES runtime and baseline ports; this generator only reproduces request timing.

## Measurement pipeline

`measurement-schema.json` defines request-level records for the four latency tasks, model validation counters, and synchronized node/GPU energy. `analyze_results.py` computes median/P95/P99/P99.9/max, model MAE/RMSE, prefetch hit rate, bidirectional traffic summaries, energy/request, energy/token, and EDP from **supplied measurements**. It never fabricates absent fields.

```sh
code/preflight.sh
python3 code/analyze_results.py code/data/actual/raw.jsonl code/data/actual/summary.csv
python3 code/compute_stats.py code/data/actual/raw.jsonl code/data/actual/stats.csv \
        --baseline default --compare ramses
python3 -m unittest discover -s code/tests -v
```

`compute_stats.py` reports run-level mean, standard deviation, and Student-t
95% confidence intervals, plus a two-sample significance test between systems.
See `AUTHOR_DATA_GUIDE.md` for the step-by-step procedure to populate the raw
measurements (B) and the named industrial task with accuracy (C).

## Generating paper tables and figures

The manuscript's new tables and figures are populated from the CSVs above, so
no numbers are hand-entered. The LaTeX wrappers in `paper/tables/` include the
generated bodies through `\IfFileExists` guards, so the paper compiles both
before and after the data is produced.

```sh
# tables -> paper/tables/*_body.tex  (percentiles, energy, model validation,
#                                  policy-off, industrial accuracy, CI)
python3 code/make_tables.py --summary code/data/actual/summary.csv \
        --stats code/data/actual/stats.csv --industrial code/data/actual/industrial_accuracy.csv \
        --outdir paper/tables --task ttft

# figures -> paper/figures/*.png  (consolidated w/ error bars, energy-latency,
#                               measured phase overlay, sensitivity)
python3 code/make_figures.py --summary code/data/actual/summary.csv \
        --stats code/data/actual/stats.csv --sensitivity code/data/actual/sensitivity.csv \
        --outdir paper/figures

# named industrial task (accuracy + output equivalence) -> JSONL + CSV
python3 code/eval_industrial.py --dataset mvtec_ad --data-root /path/to/mvtec \
        --model vit-h14 --precision fp16 \
        --out-jsonl code/data/actual/industrial.jsonl \
        --out-csv code/data/actual/industrial_accuracy.csv
```

The `code/data/expected/` directory contains deterministic, realistic-looking
planning projections. They are isolated from `code/data/actual/`, which is
reserved for future measurements. Expected values must not be cited or used to
generate publication tables. See [`data/README.md`](data/README.md) for the
regeneration and expected-versus-actual comparison workflow.

The expected matrix contains 16,000 request projections spanning eight
systems, five models, four tasks, five runs, and 20 requests per run. Every row
is marked `synthetic_expected_projection_not_measured`.

`make_tables.py` and `make_figures.py` emit output only for data present in the
CSVs; absent metrics produce no rows or figures (never placeholder numbers).

## Whole-node energy (R3-11)

`collect_energy.py` integrates GPU (NVML) and CPU package + DRAM (Intel RAPL)
energy over the same monotonic window, handles counter wrap, and supports idle
subtraction. It writes `gpu_energy_j` and `node_energy_j` (plus a per-component
breakdown and instrument metadata) that drop straight into the measurement
schema. On a host without RAPL/NVML it reports energy as unavailable rather than
guessing.

```sh
python3 code/collect_energy.py --idle-seconds 5 --out energy.json -- \
        python run_inference.py --system ramses ...
```

## Named industrial task (R3-8)

`eval_industrial.py` computes task accuracy/AUROC and baseline-vs-RAMSES output
equivalence; `mvtec_vit.py` is a concrete MVTec AD + ViT backend (deep-feature-
distance anomaly detection; embeddings returned for the equivalence check).
Because the RAMSES `LD_PRELOAD` layer is process-global, run each serving mode in
its own process and compare:

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

The dataset scanning, scoring, energy integration, and metric math are unit
tested (`python3 -m unittest discover -s code/tests`); the ViT embedder and
serving hooks run in the author's GPU environment. Real outputs belong in
`data/actual/`, never in `data/expected/`.

A publishable run requires CUDA-capable hardware, NUMA/NVMe tools, the RAMSES runtime, baseline ports, and a synchronized whole-node power meter. The preflight script fails when these prerequisites are absent.

## Implementation provenance

The only discoverable implementation is the separate `leemgs/mball` prototype at commit `f4bd8198a941da81f28b1462885e37185e33773e`. Its source labels GPU allocation as mocked and disk swap as an example/emulation; it is therefore **not** imported or represented as a production RAMSES runtime, GPUDirect Storage implementation, or evidence for the manuscript's quantitative results.

## Free Colab GPU smoke test

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leemgs/ramses/blob/main/code/colab_experiment.ipynb)

Open [`colab_experiment.ipynb`](colab_experiment.ipynb) in Google Colab and explicitly select a GPU runtime. The notebook pins dependencies, records GPU/driver/software provenance, fails if CUDA is unavailable, measures scoring/continuation/TTFT/generation separately, and exports schema-compatible JSONL. Because free accelerator assignment is interactive, capacity-limited, and not guaranteed, it cannot be launched non-interactively from this repository or used as a substitute for the A100/GDS/whole-node-power experiments. Its tiny-GPT-2 values are supplemental artifact smoke tests, not RAMSES effectiveness results.
