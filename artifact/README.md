# Anonymized review artifact

`generate_trace.py` produces a parameterized synthetic arrival schedule intended for sustained-load testing. It is synthetic, not a released factory log. The default seed is fixed for reproduction.

```sh
python3 artifact/generate_trace.py --hours 72 --seed 5047 --output trace.csv
```

Columns are timestamp, request class, and requested concurrency. The nominal periodic component is 10 ms with Gaussian jitter (standard deviation 1.5 ms, truncated at 1 ms); anomaly bursts occur independently with probability 0.012 per arrival and concurrency 2–6. These are generator parameters, not claims about a specific plant. Users must recalibrate them against their own traces. The manuscript's model-serving measurements require the RAMSES runtime and baseline ports; this generator only reproduces request timing.
