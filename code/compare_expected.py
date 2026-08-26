#!/usr/bin/env python3
"""Compare measured summary rows with synthetic planning expectations.

The comparison is deliberately lossless: configurations present on only one
side are retained and labelled instead of disappearing from the report.
"""
import argparse
import csv

KEYS = ("system", "task", "model", "precision", "input_tokens",
        "output_tokens", "batch", "concurrency")
METRICS = ("p50_ms", "p95_ms", "p99_ms", "energy_per_request_j")
SYNTHETIC_MARKER = "synthetic_expected_projection_not_measured"


def read(path):
    with open(path, newline="") as f:
        return {tuple(r[k] for k in KEYS): r for r in csv.DictReader(f)}


def ensure_measured(rows):
    synthetic = [key for key, row in rows.items()
                 if row.get("data_source") == SYNTHETIC_MARKER]
    if synthetic:
        raise SystemExit(
            f"actual input contains {len(synthetic)} synthetic projection row(s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expected")
    ap.add_argument("actual")
    ap.add_argument("output")
    a = ap.parse_args()
    expected, actual = read(a.expected), read(a.actual)
    ensure_measured(actual)
    rows = []
    for key in sorted(expected.keys() | actual.keys()):
        row = dict(zip(KEYS, key))
        expected_row, actual_row = expected.get(key), actual.get(key)
        if expected_row and actual_row:
            row["comparison_status"] = "matched"
        elif expected_row:
            row["comparison_status"] = "expected_only"
        else:
            row["comparison_status"] = "actual_only"
        for metric in METRICS:
            e = float(expected_row[metric]) if expected_row else None
            measured = float(actual_row[metric]) if actual_row else None
            row[f"expected_{metric}"] = e if e is not None else ""
            row[f"actual_{metric}"] = measured if measured is not None else ""
            row[f"delta_{metric}_pct"] = (
                100 * (measured - e) / e
                if e not in (None, 0) and measured is not None else ""
            )
        rows.append(row)
    if not expected or not actual:
        raise SystemExit("expected and actual inputs must both contain rows")
    with open(a.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    matched = sum(row["comparison_status"] == "matched" for row in rows)
    print(f"wrote {len(rows)} comparison rows ({matched} matched) to {a.output}")


if __name__ == "__main__":
    main()
