# Anonymized review artifact

`generate_trace.py` produces a parameterized synthetic arrival schedule intended for sustained-load testing. It is synthetic, not a released factory log. The default seed is fixed for reproduction.

```sh
python3 artifact/generate_trace.py --hours 72 --seed 5047 --output trace.csv
```

Columns are timestamp, request class, and requested concurrency. The nominal periodic component is 10 ms with Gaussian jitter (standard deviation 1.5 ms, truncated at 1 ms); anomaly bursts occur independently with probability 0.012 per arrival and concurrency 2–6. These are generator parameters, not claims about a specific plant. Users must recalibrate them against their own traces. The manuscript's model-serving measurements require the RAMSES runtime and baseline ports; this generator only reproduces request timing.

## Measurement pipeline

`measurement-schema.json` defines request-level records for the four latency tasks, model validation counters, and synchronized node/GPU energy. `analyze_results.py` computes median/P95/P99/P99.9/max, model MAE/RMSE, prefetch hit rate, bidirectional traffic summaries, energy/request, energy/token, and EDP from **supplied measurements**. It never fabricates absent fields.

```sh
artifact/preflight.sh
python3 artifact/analyze_results.py raw.jsonl summary.csv
python3 -m unittest discover -s artifact/tests -v
```

A publishable run requires CUDA-capable hardware, NUMA/NVMe tools, the RAMSES runtime, baseline ports, and a synchronized whole-node power meter. The preflight script fails when these prerequisites are absent.

## Implementation provenance

The only discoverable implementation is the separate `leemgs/mball` prototype at commit `f4bd8198a941da81f28b1462885e37185e33773e`. Its source labels GPU allocation as mocked and disk swap as an example/emulation; it is therefore **not** imported or represented as a production RAMSES runtime, GPUDirect Storage implementation, or evidence for the manuscript's quantitative results.
