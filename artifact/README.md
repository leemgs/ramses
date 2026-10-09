# RAMSES reproducibility artifact

Hierarchical memory orchestration for single-node industrial AI inference.
This directory is the self-contained artifact for the paper: it contains the
orchestrator layer, the synthetic-trace generator, the baseline invocation
scripts, the measurement schema, the raw request-level data, and the analysis
scripts that regenerate **every table and figure** in the manuscript.

It is released so that other researchers can inspect, rerun, and build on the
work. Paper-facing outputs are written to the sibling `../paper/tables/` and
`../paper/figures/` directories; the LaTeX manuscript lives in `../paper/`.

## Layout

```
.
├── orchestrator/            # RAMSES runtime (Section III)
│   ├── ramses_preload.c     #   GPU Booster LD_PRELOAD interception layer (III-C)
│   ├── Makefile             #   build libramses.so (portable or -DRAMSES_WITH_CUDA)
│   ├── regime_controller.py #   Regime Analyzer + Policy Engine (III-D/E)
│   ├── gpu_process_allocator.py  # GPU Process Allocator (III-A, Algorithm 1)
│   ├── task_memory_manager.py    # Task Memory Manager  (III-B, Algorithm 2)
│   └── gpu_booster.py            # GPU Booster swap planner (III-C, Algorithm 3)
├── baselines/               # exact invocations for every compared system
│   ├── run_baselines.sh     #   default/FlexGen/SwapAdvisor/NEO/SpecOffload/vLLM/RAMSES
│   └── llama4_compat_patch.md#   vLLM 0.5.3 Llama-4 compatibility patch
├── generate_trace.py        # 72-hour parameterized synthetic arrival trace
├── measurement-schema.json  # one-JSON-record-per-request schema
├── collect_energy.py        # synchronized whole-node energy (NVML + RAPL)
├── eval_industrial.py, mvtec_vit.py   # named industrial task (MVTec AD/VisA/AI4I)
├── analyze_results.py, compute_stats.py  # percentiles, MAE/RMSE, CIs, tests
├── make_tables.py, make_figures.py    # regenerate paper tables / figures
├── reproduce.sh             # one command: tables + figures + replay + tests
├── data/
│   ├── actual/              # released measured data (raw.jsonl + derived CSVs)
│   └── expected/            # pre-experiment projections — never cited
└── tests/                   # unit tests for the analysis + metric code
```

## Quick start

```sh
# Reproduce every table and figure from the released data, then self-verify:
./reproduce.sh                 # tables + figures + control-plane replay + tests

# Or individually:
./reproduce.sh tables          # -> ../paper/tables/*_body.tex
./reproduce.sh figures         # -> ../paper/figures/*.png   (needs matplotlib)
./reproduce.sh verify          # operating-model replay + unit tests
```

All paper numbers come from `data/actual/raw.jsonl` (16,000 request-level
records: eight serving configurations x five models x four task types x five
restarts). The principal workload is Llama-4 17B, TTFT, so the paper tables use
`--task ttft --model llama4-17b`; `reproduce.sh` pins those filters.

## Orchestrator (Section III)

The GPU Booster is an `LD_PRELOAD` interception layer over the CUDA runtime and
caching allocator. Build it and load it in front of an unmodified serving
process:

```sh
cd orchestrator && make           # -> libramses.so (no CUDA toolkit needed to build)
RAMSES_VRAM_RESERVE_MB=4096 RAMSES_LOG=counters.jsonl \
  LD_PRELOAD=$PWD/libramses.so python serve.py ...
```

The control plane reproduces the operating-model validation (regime mix, mean
`beta`, prediction MAE/RMSE, prefetch-hit rate) directly from the released log,
without a GPU:

```sh
python3 orchestrator/regime_controller.py --replay data/actual/raw.jsonl
```

The three module files (`gpu_process_allocator.py`, `task_memory_manager.py`,
`gpu_booster.py`) are dependency-free references of Algorithms 1–3 and run
standalone (`python3 orchestrator/<file>.py`).

## Baselines

`baselines/run_baselines.sh` records the exact, version-pinned command line for
each configuration (see `baselines/` and `BASELINE_MANIFEST.md`). Inspect the
invocations without installing the baselines:

```sh
DRY_RUN=1 ./baselines/run_baselines.sh all
```

## Synthetic trace

```sh
python3 generate_trace.py --hours 72 --seed 5047 --output data/trace.csv
```

Nominal 10 ms cadence with 1.5 ms Gaussian jitter (truncated at 1 ms) and
independent 1.2%-probability anomaly bursts (concurrency 2–6). These are
generator parameters, not a released factory log; recalibrate against your own
traces before drawing field conclusions.

## Reproducibility notes

- `data/expected/` holds deterministic pre-experiment projections used only to
  size the experiment matrix; every row is marked
  `synthetic_expected_projection_not_measured` and is excluded from every table,
  figure, test, and claim. Only `data/actual/` feeds the paper.
- `make_tables.py` / `make_figures.py` emit output only for data present in the
  CSVs; absent metrics produce no rows or figures (never placeholder numbers).
- A full on-device run requires CUDA-capable hardware, NUMA/NVMe tools, the
  baseline ports, and a synchronized whole-node power meter; `preflight.sh`
  fails fast when these prerequisites are absent.

## Citing

If you build on this work, please cite the paper (see `../paper/`). Issues and
pull requests that improve portability or add baselines are welcome.
