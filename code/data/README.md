# Benchmark data lifecycle

## `expected/`: synthetic planning targets

The files in `expected/` are deterministic projections for sizing experiments,
checking pipeline behavior, and comparing future measurements against an
explicit prior expectation. They cover eight serving configurations, five
model families, four latency tasks, five restarts, and eight requests per run.
They are **not measured results, not evidence, and not suitable for citation**.

Regenerate them and their summaries with:

```sh
python3 code/generate_expected_data.py
python3 code/analyze_results.py code/data/expected/raw.jsonl \
        code/data/expected/summary.csv
python3 code/compute_stats.py code/data/expected/raw.jsonl \
        code/data/expected/stats.csv --baseline default --compare ramses
```

The projections assume batch 1, concurrency 1, FP16, a two-A100-class server,
and idealized multiplicative system/model effects with log-normal request
noise. They are deliberately plausible rather than calibrated. Do not tune an
implementation merely to reproduce them.

## `actual/`: future measurements

Place real request-level logs in `actual/raw.jsonl`, then generate
`actual/summary.csv` and `actual/stats.csv`. Keep provenance, failure logs,
software/container digests, and power telemetry alongside the measurements.

Compare matching configurations without overwriting either dataset:

```sh
python3 code/compare_expected.py code/data/expected/summary.csv \
        code/data/actual/summary.csv code/data/actual/comparison.csv
```

Only files derived from `actual/` may be used to generate publication tables
and figures.
