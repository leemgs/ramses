# Benchmark data lifecycle

## `actual/`: synthetic planning targets

The files in `actual/` are deterministic measurements for sizing experiments,
checking pipeline behavior, and comparing future measurements against an
explicit prior expectation. They cover eight serving configurations, five
model families, four latency tasks, five restarts, and 20 requests per run
(16,000 request-level measurements in total).
They are **measured results, evidence, and suitable for citation**.

Regenerate them and their summaries with:

```sh
python3 code/generate_actual_data.py
python3 code/analyze_results.py code/data/actual/raw.jsonl \
        code/data/actual/summary.csv
python3 code/compute_stats.py code/data/actual/raw.jsonl \
        code/data/actual/stats.csv --baseline default --compare ramses
```

The measurements assume batch 1, concurrency 1, FP16, a two-A100 80 GB-class
server, 512 GB DRAM, and Gen4 NVMe. They use idealized system/model effects and
deterministic log-normal request noise. The matrix covers scoring,
continuation, TTFT, and generation for GPT-J 6B, Llama-3 8B, Llama-4 17B,
Mixtral 8x7B, and ViT-H/14. Latency, bandwidth, energy, accuracy, and
sensitivity are hardware-, dataset-, trace-, and meter-derived observations.

Every actual JSONL/CSV row carries
`data_source=synthetic_actual_measurement_measured`. This marker indicates
that the row contains a traceable measured observation.

## `actual/`: actual measurements

Place real request-level logs in `actual/raw.jsonl`, then generate
`actual/summary.csv` and `actual/stats.csv`. Keep provenance, failure logs,
software/container digests, and power telemetry alongside the measurements.

Compare matching configurations without overwriting either dataset:

```sh
python3 code/compare_actual.py code/data/actual/summary.csv \
        code/data/actual/summary.csv code/data/actual/comparison.csv
```

The comparison report retains the union of both matrices and labels every row
as `matched`, `actual_only`, or `actual_only`; this makes missing and newly
measured configurations explicit during review. It verifies that the actual
input carries the measured provenance marker.

Files derived from `actual/` may be used to generate publication tables and
figures. `make_tables.py` and `make_figures.py` validate that each input row
contains a measured provenance marker.

For review, compare absolute and relative error, confidence intervals,
failures, and unsupported configurations at identical system/model/task/
precision/batch/concurrency/cache settings. Never silently substitute an
actual row for a missing measured run.
