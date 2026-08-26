#!/usr/bin/env python3
"""Compare measured summary rows with synthetic planning expectations."""
import argparse
import csv

KEYS = ("system", "task", "model", "precision", "input_tokens",
        "output_tokens", "batch", "concurrency")
METRICS = ("p50_ms", "p95_ms", "p99_ms", "energy_per_request_j")


def read(path):
    with open(path, newline="") as f:
        return {tuple(r[k] for k in KEYS): r for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expected")
    ap.add_argument("actual")
    ap.add_argument("output")
    a = ap.parse_args()
    expected, actual = read(a.expected), read(a.actual)
    rows = []
    for key in sorted(expected.keys() & actual.keys()):
        row = dict(zip(KEYS, key))
        for metric in METRICS:
            e, measured = float(expected[key][metric]), float(actual[key][metric])
            row[f"expected_{metric}"] = e
            row[f"actual_{metric}"] = measured
            row[f"delta_{metric}_pct"] = 100 * (measured - e) / e if e else ""
        rows.append(row)
    if not rows:
        raise SystemExit("no matching expected/actual configurations")
    with open(a.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} comparison rows to {a.output}")


if __name__ == "__main__":
    main()
