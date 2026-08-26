#!/usr/bin/env python3
"""Compute run-level means, standard deviations, 95% confidence intervals, and
two-sample significance tests from *measured* RAMSES JSONL records.

This complements analyze_results.py (which reports latency percentiles and
model/energy aggregates). It never synthesizes data: every statistic is
computed from the supplied request-level logs. Standard library only.

Usage:
    python3 compute_stats.py raw.jsonl stats.csv [--metric latency_ms] \
        [--baseline default --compare ramses]

- CIs are Student-t intervals over per-run means (df = runs - 1).
- The optional --baseline/--compare pair prints a conservative Welch t-test
  (df = min(n1, n2) - 1) between two systems for each matched task/config.
"""
import argparse, csv, json, math, statistics
from collections import defaultdict

REQ = {"run_id", "system", "task", "latency_ms", "input_tokens", "output_tokens",
       "batch", "concurrency", "request_count", "precision", "model"}
GROUP = ("system", "task", "model", "precision", "input_tokens", "output_tokens",
         "batch", "concurrency")
CONFIG = ("task", "model", "precision", "input_tokens", "output_tokens", "batch", "concurrency")

# Two-sided t critical values at 95% for small df; NormalDist fallback for large df.
T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
       8: 2.306, 9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 30: 2.042}


def t_crit(df):
    if df <= 0:
        return float("nan")
    if df in T95:
        return T95[df]
    keys = [k for k in T95 if k <= df]
    return T95[max(keys)] if keys else 1.960  # conservative for large df


def load(path, metric):
    rows = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            missing = REQ - r.keys()
            if missing:
                raise ValueError(f"line {n}: missing {sorted(missing)}")
            if metric not in r:
                raise ValueError(f"line {n}: missing metric field '{metric}'")
            rows.append(r)
    if not rows:
        raise ValueError("no measurement records")
    return rows


def run_means(rows, metric):
    """Return {group_key: {run_id: mean_metric}}."""
    per_run = defaultdict(lambda: defaultdict(list))
    for r in rows:
        key = tuple(r[k] for k in GROUP)
        per_run[key][r["run_id"]].append(float(r[metric]))
    return {g: {rid: statistics.fmean(v) for rid, v in runs.items()}
            for g, runs in per_run.items()}


def summarize(rows, metric):
    out = []
    for key, runs in sorted(run_means(rows, metric).items()):
        means = list(runs.values())
        n = len(means)
        mean = statistics.fmean(means)
        sd = statistics.stdev(means) if n > 1 else 0.0
        half = t_crit(n - 1) * sd / math.sqrt(n) if n > 1 else 0.0
        d = dict(zip(GROUP, key))
        d.update(metric=metric, runs=n, mean=mean, std=sd,
                 ci95_low=mean - half, ci95_high=mean + half)
        out.append(d)
    return out


def welch(a, b):
    na, nb = len(a), len(b)
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va = statistics.variance(a) if na > 1 else 0.0
    vb = statistics.variance(b) if nb > 1 else 0.0
    se = math.sqrt(va / na + vb / nb) if (va or vb) else 0.0
    t = (ma - mb) / se if se else float("inf")
    df = min(na, nb) - 1  # conservative
    return t, df, t_crit(df), ma, mb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--metric", default="latency_ms")
    ap.add_argument("--baseline")
    ap.add_argument("--compare")
    a = ap.parse_args()

    rows = load(a.input, a.metric)
    summary = summarize(rows, a.metric)
    with open(a.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(summary)
    print(f"wrote {len(summary)} group rows to {a.output}")

    if a.baseline and a.compare:
        rm = run_means(rows, a.metric)
        # index run means by (system, config)
        by_sys = defaultdict(dict)
        for key, runs in rm.items():
            d = dict(zip(GROUP, key))
            by_sys[d["system"]][tuple(d[k] for k in CONFIG)] = list(runs.values())
        base, comp = by_sys.get(a.baseline, {}), by_sys.get(a.compare, {})
        print(f"\nWelch t-test ({a.compare} vs {a.baseline}), 95% two-sided:")
        for cfg in sorted(set(base) & set(comp)):
            t, df, tc, mc, mb = welch(comp[cfg], base[cfg])
            sig = "significant" if abs(t) > tc else "not significant"
            print(f"  {dict(zip(CONFIG, cfg))}: "
                  f"{a.compare}={mc:.3f} {a.baseline}={mb:.3f} "
                  f"t={t:.3f} df={df} tcrit={tc:.3f} -> {sig}")


if __name__ == "__main__":
    main()
