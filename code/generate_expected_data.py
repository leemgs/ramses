#!/usr/bin/env python3
"""Generate deterministic, realistic-looking *expected* benchmark fixtures.

These projections are planning targets for comparing future measurements.  They
are not observations and must never be used as paper evidence.
"""
import argparse
import csv
import json
import random
from pathlib import Path


SYSTEM_FACTOR = {
    "default": 1.00, "flexgen": 0.90, "swapadvisor": 0.85, "neo": 0.79,
    "specoffload": 0.75, "vllm": 0.70, "ramses": 0.65,
    "ramses_policy_off": 0.73,
}
MODELS = {
    "llama4-17b": 1.00, "llama3-8b": 0.56, "gpt-j-6b": 0.46,
    "mixtral-8x7b": 1.32, "vit-h14": 0.31,
}
TASK_MS = {"scoring": 310.0, "continuation": 72.0,
           "ttft": 820.0, "generation": 4250.0}
TASK_TOKENS = {"scoring": (128, 0), "continuation": (128, 1),
               "ttft": (128, 1), "generation": (128, 128)}


def write_raw(path, seed, requests_per_run):
    rng = random.Random(seed)
    with path.open("w") as f:
        for system_index, (system, system_factor) in enumerate(SYSTEM_FACTOR.items()):
            for model, model_factor in MODELS.items():
                for task, task_base in TASK_MS.items():
                    input_tokens, output_tokens = TASK_TOKENS[task]
                    for run in range(1, 6):
                        run_bias = rng.gauss(0, 0.012)
                        for request in range(1, requests_per_run + 1):
                            tail = rng.lognormvariate(-3.8, 0.65) - 0.027
                            latency = task_base * model_factor * system_factor
                            latency *= max(0.82, 1 + run_bias + tail)
                            tokens = max(output_tokens, 1)
                            node_energy = (0.19 + latency / 1000 * 0.49) * (1 + 0.02 * system_index)
                            predicted = latency * (1 + rng.gauss(0, 0.018))
                            rec = {
                                "run_id": f"r{run}", "system": system, "task": task,
                                "model": model, "precision": "fp16",
                                "input_tokens": input_tokens, "output_tokens": output_tokens,
                                "batch": 1, "concurrency": 1, "request_count": 1,
                                "latency_ms": round(latency, 4),
                                "alpha": round(0.70 + 0.045 * system_index + 0.06 * model_factor, 4),
                                "beta": round(0.55 + 0.035 * system_index + 0.05 * model_factor, 4),
                                "predicted_ms": round(predicted, 4),
                                "read_bw_gbps": round(4.4 + 0.23 * system_index, 3),
                                "write_bw_gbps": round(2.4 + 0.14 * system_index, 3),
                                "queue_ms": round(max(0.7, 4.6 - 0.42 * system_index), 3),
                                "prefetch_hits": 80 + 2 * system_index,
                                "prefetch_misses": max(4, 20 - 2 * system_index),
                                "bytes_read": 734003200, "bytes_written": 67108864,
                                "gpu_energy_j": round(node_energy * 0.61, 5),
                                "node_energy_j": round(node_energy, 5),
                                "tokens": tokens,
                                "throughput_tps": round(tokens * 1000 / latency, 6),
                                "request_index": request,
                                "data_source": "synthetic_expected_projection_not_measured",
                                "projection_seed": seed,
                            }
                            f.write(json.dumps(rec, separators=(",", ":")) + "\n")


def write_industrial(path):
    rows = [
        ["expected_mvtec_ad", "vit-h14", "fp16", 1725, 0.952, 0.952, 0.981, 0.981, 0.999],
        ["expected_visa", "vit-h14", "fp16", 2162, 0.938, 0.938, 0.972, 0.972, 0.999],
    ]
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["dataset", "model", "precision", "n_items", "baseline_accuracy",
                    "ramses_accuracy", "baseline_auroc", "ramses_auroc",
                    "output_equivalence"])
        w.writerows(rows)


def write_sensitivity(path):
    groups = {
        "block_size_mb": [(1, 486), (2, 451), (4, 421), (8, 437), (16, 474)],
        "sampling_ms": [(100, 430), (200, 421), (400, 449)],
        "hysteresis_pct": [(2, 440), (5, 421), (10, 446)],
        "reuse_window": [(16, 438), (32, 421), (64, 433)],
    }
    with path.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["param", "value", "p99_ms"])
        for param, points in groups.items():
            for value, p99 in points: w.writerow([param, value, p99])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, default=Path(__file__).parent / "data" / "expected")
    ap.add_argument("--seed", type=int, default=5047)
    ap.add_argument("--requests-per-run", type=int, default=8)
    a = ap.parse_args(); a.outdir.mkdir(parents=True, exist_ok=True)
    write_raw(a.outdir / "raw.jsonl", a.seed, a.requests_per_run)
    write_industrial(a.outdir / "industrial_accuracy.csv")
    write_sensitivity(a.outdir / "sensitivity.csv")
    print(f"wrote expected projections to {a.outdir}")


if __name__ == "__main__":
    main()
