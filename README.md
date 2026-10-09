# RAMSES — Hierarchical Memory Orchestration for Single-Node Industrial AI Inference

RAMSES is a single-node hierarchical-memory orchestrator that coordinates GPU
video RAM (VRAM), host DRAM, and NVMe for large-model inference. It combines GPU
resource preallocation, NUMA-aware host allocation, and asynchronous
block-aligned swapping, and selects admission / prefetch / eviction actions from
two observable pressure ratios under a regime-aware control plane.

This repository holds both the paper and a self-contained reproducibility
artifact, kept in separate workspaces. The artifact is released so other
researchers can inspect, rerun, and build on the work.

> The manuscript PDF (`paper/main.pdf`) is anonymized for **double-blind**
> review (IEEE Transactions on Industrial Informatics). Author identity is
> restored at camera-ready by setting `\newcommand{\anonymous}{0}` in
> `paper/main.tex`.

## Directory layout

| Directory | Purpose |
| --- | --- |
| [`paper/`](paper/) | LaTeX sources, bibliography, class/tables/figures, and the submission documents (cover letter, point-by-point response). Builds `main.pdf` (10 pages). |
| [`artifact/`](artifact/) | The reproducibility artifact: orchestrator runtime, synthetic-trace generator, baseline invocation scripts, measurement schema, raw request-level data, and the analysis scripts that regenerate every table and figure. |

## Paper workspace

```sh
cd paper
latexmk -pdf main.tex          # or: pdflatex; bibtex; pdflatex; pdflatex
```

Submission documents: [`paper/COVER_LETTER.md`](paper/COVER_LETTER.md) and
[`paper/Response_to_Reviewers_TII-26-5047.docx`](paper/).

## Artifact workspace

Full details in [`artifact/README.md`](artifact/README.md).

```sh
# Reproduce every table and figure from the released data, then self-verify:
./artifact/reproduce.sh            # tables + figures + control-plane replay + tests

# Build and load the GPU Booster LD_PRELOAD interception layer (Section III-C):
cd artifact/orchestrator && make
RAMSES_VRAM_RESERVE_MB=4096 LD_PRELOAD=$PWD/libramses.so python serve.py ...

# Reproduce the operating-model validation from the released log (no GPU needed):
python3 artifact/orchestrator/regime_controller.py --replay artifact/data/actual/raw.jsonl

# Inspect the exact, version-pinned baseline invocations:
DRY_RUN=1 ./artifact/baselines/run_baselines.sh all
```

### What is inside `artifact/`

| Path | Role |
| --- | --- |
| `orchestrator/ramses_preload.c`, `Makefile` | GPU Booster `LD_PRELOAD` CUDA interception layer (Section III-C) |
| `orchestrator/regime_controller.py` | Regime Analyzer + Policy Engine (Section III-D/E), with a `--replay` mode |
| `orchestrator/{gpu_process_allocator,task_memory_manager,gpu_booster}.py` | References of Algorithms 1–3 (Sections III-A/B/C) |
| `baselines/run_baselines.sh`, `llama4_compat_patch.md` | Exact invocations for default/FlexGen/SwapAdvisor/NEO/SpecOffload/vLLM/RAMSES |
| `generate_trace.py` | 72-hour parameterized synthetic arrival trace |
| `measurement-schema.json` | One-JSON-record-per-request schema |
| `collect_energy.py` | Synchronized whole-node energy (GPU NVML + CPU/DRAM RAPL) |
| `eval_industrial.py`, `mvtec_vit.py` | Named industrial task (MVTec AD / VisA / AI4I 2020) |
| `make_tables.py`, `make_figures.py`, `analyze_results.py`, `compute_stats.py` | Regenerate tables/figures; percentiles, MAE/RMSE, confidence intervals |
| `data/actual/` | Released measured data (`raw.jsonl` — 16,000 request records — and derived CSVs) |
| `data/expected/` | Pre-experiment projections only; never cited in the paper |
| `tests/` | Unit tests for the analysis and metric code |

All paper numbers trace back to `artifact/data/actual/raw.jsonl` (eight serving
configurations × five models × four task types × five restarts). `reproduce.sh`
pins the principal-workload filters (`--task ttft --model llama4-17b`) so the
regenerated tables match the manuscript exactly. Values under
`artifact/data/expected/` are synthetic planning projections marked
`synthetic_expected_projection_not_measured` and are excluded from every table,
figure, test, and claim.

## Reproducibility status

- `./artifact/reproduce.sh` regenerates the committed table bodies with zero diff.
- The orchestrator interception layer compiles with a plain C toolchain (no CUDA
  toolkit required to build); the full on-device swap transport builds with
  `make cuda`.
- The 18 unit tests pass (`python3 -m unittest discover -s artifact/tests`).
- A full on-device run requires CUDA-capable hardware, NUMA/NVMe tools, the
  baseline ports, and a synchronized whole-node power meter; `artifact/preflight.sh`
  fails fast when these are absent.

## License and citation

If you build on this work, please cite the paper (see `paper/`). Issues and pull
requests that improve portability or add baselines are welcome.
