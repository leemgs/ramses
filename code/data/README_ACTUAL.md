# Benchmark data lifecycle

## `actual/`: measured benchmark results

The files in `actual/` contain measurements collected from real benchmark runs. They cover eight serving configurations, five model families, four latency tasks, five restarts, and 20 requests per run, for up to 16,000 request-level observations.

These files are **measured results** and may be used as evidence or cited only when their experimental provenance and collection conditions are documented and verified.

Generate the summaries and statistical results with:

```sh
python3 code/analyze_results.py code/data/actual/raw.jsonl \
        code/data/actual/summary.csv

python3 code/compute_stats.py code/data/actual/raw.jsonl \
        code/data/actual/stats.csv --baseline default --compare ramses
```

The measurements were collected using batch size 1, concurrency 1, FP16, two A100 80 GB-class GPUs, 512 GB DRAM, and Gen4 NVMe storage.

The benchmark matrix covers scoring, continuation, time to first token (TTFT), and generation workloads for GPT-J 6B, Llama-3 8B, Llama-4 17B, Mixtral 8x7B, and ViT-H/14. Reported latency, bandwidth, energy, accuracy, and sensitivity values are derived from benchmark traces, datasets, and hardware telemetry.

Each JSONL or CSV row derived from a completed measurement carries:

```text
data_source=actual_measurement_measured
```

This marker identifies the row as a measured observation. It does not replace the associated provenance records or independently verify the validity of the measurement.

## Adding and processing measurements

Place real request-level logs in:

```text
code/data/actual/raw.jsonl
```

Then generate:

```text
code/data/actual/summary.csv
code/data/actual/stats.csv
```

Keep the following provenance information alongside the measurements:

* Hardware and software configurations
* Dataset and workload versions
* Random seeds and benchmark parameters
* Failure and retry logs
* Software and container digests
* Power and performance telemetry
* Experiment dates and run identifiers

## Comparing expected and actual results

Compare the measured results with the corresponding expected dataset without overwriting either dataset:

```sh
python3 code/compare_actual.py code/data/expected/summary.csv \
        code/data/actual/summary.csv \
        code/data/actual/comparison.csv
```

The comparison report retains the union of both matrices and labels each row as:

* `matched`: present in both expected and actual datasets
* `expected_only`: present only in the expected dataset
* `actual_only`: present only in the measured dataset

This makes missing measurements and newly tested configurations explicit during review. The comparison script also verifies that the actual input carries the required measured-provenance marker.

## Publication use

Files derived from `actual/` may be used to generate publication tables and figures when their provenance and experimental conditions have been verified.

```text
make_tables.py
make_figures.py
```

These scripts validate that each actual input row contains a measured-provenance marker.

During review, compare absolute and relative errors, confidence intervals, failures, and unsupported configurations under identical system, model, task, precision, batch, concurrency, and cache settings.

Never substitute an expected or synthetic value for a missing measured result.
