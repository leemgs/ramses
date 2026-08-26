# Benchmark data lifecycle

## `expected/`: synthetic planning targets

The files in `expected/` are deterministic projections for sizing experiments,
checking pipeline behavior, and comparing future measurements against an
explicit prior expectation. They cover eight serving configurations, five
model families, four latency tasks, five restarts, and 20 requests per run
(16,000 request-level projections in total).
They are **not measured results, not evidence, and not suitable for citation**.

Regenerate them and their summaries with:

```sh
python3 code/generate_expected_data.py
python3 code/analyze_results.py code/data/expected/raw.jsonl \
        code/data/expected/summary.csv
python3 code/compute_stats.py code/data/expected/raw.jsonl \
        code/data/expected/stats.csv --baseline default --compare ramses
```

The projections assume batch 1, concurrency 1, FP16, a two-A100 80 GB-class
server, 512 GB DRAM, and Gen4 NVMe. They use idealized system/model effects and
deterministic log-normal request noise. The matrix covers scoring,
continuation, TTFT, and generation for GPT-J 6B, Llama-3 8B, Llama-4 17B,
Mixtral 8x7B, and ViT-H/14. Latency, bandwidth, energy, accuracy, and
sensitivity are engineering hypotheses, not hardware-, dataset-, trace-, or
meter-derived observations. Do not tune an implementation merely to reproduce
them.

Every expected JSONL/CSV row carries
`data_source=synthetic_expected_projection_not_measured`. Never remove this
marker unless the row has been replaced by a traceable observation.

## `actual/`: future measurements

Place real request-level logs in `actual/raw.jsonl`, then generate
`actual/summary.csv` and `actual/stats.csv`. Keep provenance, failure logs,
software/container digests, and power telemetry alongside the measurements.

Compare matching configurations without overwriting either dataset:

```sh
python3 code/compare_expected.py code/data/expected/summary.csv \
        code/data/actual/summary.csv code/data/actual/comparison.csv
```

The comparison report retains the union of both matrices and labels every row
as `matched`, `expected_only`, or `actual_only`; this makes missing and newly
measured configurations explicit during review. It also rejects an "actual"
input carrying the synthetic provenance marker.

Only files derived from `actual/` may be used to generate publication tables
and figures. `make_tables.py` and `make_figures.py` fail closed if an input row
contains a synthetic provenance marker.

For review, compare absolute and relative error, confidence intervals,
failures, and unsupported configurations at identical system/model/task/
precision/batch/concurrency/cache settings. Never silently substitute an
expected row for a missing measured run.
