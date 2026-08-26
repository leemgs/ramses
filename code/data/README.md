# Expected mock data for experiment planning

The files in this directory are deterministic **pre-experiment projections**,
not observations. They provide a complete expected-value matrix for pipeline
testing, experiment sizing, and comparison with future measurements.

## Scope and assumptions

- Systems: PyTorch default, FlexGen, SwapAdvisor, NEO, SpecOffload, vLLM,
  RAMSES policy-off, and RAMSES.
- Models: GPT-J 6B, Llama-3 8B, Llama-4 17B, Mixtral 8x7B, and ViT-H/14.
- Tasks: scoring, continuation, TTFT, and generation.
- Repetition: five projected runs and 20 requests per run for every
  system/model/task combination.
- Hardware hypothesis: one serving node with 2x A100 80 GB, 512 GB DRAM, and
  Gen4 NVMe, matching the manuscript's planned testbed.
- The latency, bandwidth, energy, accuracy, and sensitivity values are
  engineering hypotheses selected to be plausible and internally consistent;
  they are not derived from hardware, a factory trace, MVTec AD, or a power
  meter.

Every JSONL/CSV result carries
`data_source=synthetic_expected_projection_not_measured`. Generated paper
tables and figures display a synthetic-expectation warning. Never remove that
marker unless the file has been replaced with traceable observations.

## Regeneration

From the repository root:

```sh
python3 code/generate_expected_mock_data.py
python3 code/analyze_results.py code/data/raw.jsonl code/data/summary.csv
python3 code/compute_stats.py code/data/raw.jsonl code/data/stats.csv \
        --baseline default --compare ramses
python3 code/make_tables.py
python3 code/make_figures.py
```

The generator uses seed `20260826` by default. Change it only to study pipeline
robustness; changing the seed does not turn projections into measurements.

## Comparing real measurements

1. Preserve these files or regenerate them in a separate planning directory.
2. Store real request-level logs separately and label their provenance.
3. Compare measured and expected values by identical system, model, task,
   precision, batch, concurrency, and cache protocol.
4. Report absolute error, relative error, confidence intervals, failures, and
   any unsupported configurations; do not silently replace missing runs.
5. Regenerate manuscript tables only from measured inputs and verify that no
   `synthetic_expected_projection_not_measured` marker remains.
