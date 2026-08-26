#!/usr/bin/env python3
"""Generate deterministic planning projections for the RAMSES experiment matrix.

The generated values are deliberately marked as synthetic expectations.  They
are useful for sizing experiments, testing the analysis pipeline, and comparing
future observations against an explicit pre-experiment hypothesis.  They are
not measurements and must never be reported as experimental evidence.
"""
import argparse
import csv
import json
import random
from pathlib import Path


SOURCE = "synthetic_expected_projection_not_measured"
SYSTEM_FACTORS = {
    "default": (1.00, 1.00, 0.00),
    "flexgen": (0.90, 0.95, 0.04),
    "swapadvisor": (0.87, 0.93, 0.07),
    "neo": (0.82, 0.91, 0.10),
    "specoffload": (0.80, 0.90, 0.12),
    "vllm": (0.75, 0.88, 0.15),
    "ramses_policy_off": (0.71, 0.87, 0.18),
    "ramses": (0.65, 0.85, 0.24),
}
MODELS = {
    # model: (relative scale, approximate state GiB, input tokens, output tokens)
    "gpt-j-6b": (0.48, 12.0, 128, 64),
    "llama3-8b": (0.60, 16.0, 128, 64),
    "llama4-17b": (1.00, 34.0, 128, 64),
    "mixtral-8x7b": (1.48, 90.0, 128, 64),
    "vit-h14": (0.34, 5.0, 0, 0),
}
TASK_BASE_MS = {
    "scoring": 310.0,
    "continuation": 42.0,
    "ttft": 820.0,
    "generation": 5300.0,
}


def write_raw(path, seed, requests_per_run):
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as out:
        for system, (latency_factor, energy_factor, coordination) in SYSTEM_FACTORS.items():
            for model, (scale, state_gib, input_tokens, output_tokens) in MODELS.items():
                for task, task_base in TASK_BASE_MS.items():
                    task_out = 1 if task in ("continuation", "ttft") else output_tokens
                    tokens = max(task_out, 1)
                    capacity_pressure = min(1.35, 0.55 + state_gib / 160.0)
                    transfer_pressure = min(1.30, 0.58 + state_gib / 180.0 - coordination * 0.35)
                    model_factor = scale * (0.82 if task == "continuation" else 1.0)
                    expected_latency = task_base * model_factor * latency_factor
                    if model == "vit-h14" and task in ("continuation", "generation"):
                        expected_latency *= 0.55
                    for run in range(1, 6):
                        run_shift = rng.gauss(0.0, 0.018)
                        for request in range(1, requests_per_run + 1):
                            tail = rng.lognormvariate(0.0, 0.075)
                            latency = expected_latency * (1.0 + run_shift) * tail
                            predicted = latency * (1.0 + rng.gauss(0.0, 0.025))
                            read_gb = state_gib * (0.035 if task == "generation" else 0.055)
                            read_gb *= max(0.35, 1.0 - coordination)
                            write_gb = read_gb * (0.10 if task != "generation" else 0.22)
                            node_power_w = 510.0 * energy_factor + 55.0 * scale
                            gpu_share = 0.61 + min(scale, 1.5) * 0.06
                            node_energy = node_power_w * latency / 1000.0
                            rec = {
                                "run_id": f"r{run}", "system": system, "task": task,
                                "model": model, "precision": "fp16",
                                "input_tokens": input_tokens, "output_tokens": task_out,
                                "batch": 1, "concurrency": 1, "request_count": 1,
                                "latency_ms": round(latency, 4),
                                "alpha": round(capacity_pressure, 4),
                                "beta": round(transfer_pressure, 4),
                                "predicted_ms": round(predicted, 4),
                                "read_bw_gbps": round(4.7 + coordination * 6.0, 4),
                                "write_bw_gbps": round(2.5 + coordination * 3.0, 4),
                                "queue_ms": round(max(0.35, 5.0 - coordination * 15.0), 4),
                                "prefetch_hits": round(76 + coordination * 88),
                                "prefetch_misses": round(max(3, 24 - coordination * 70)),
                                "bytes_read": round(read_gb * 1024**3),
                                "bytes_written": round(write_gb * 1024**3),
                                "gpu_energy_j": round(node_energy * gpu_share, 4),
                                "node_energy_j": round(node_energy, 4),
                                "tokens": tokens,
                                "throughput_tps": round(tokens * 1000.0 / latency, 6),
                                "data_source": SOURCE,
                                "projection_seed": seed,
                                "projection_request": request,
                            }
                            out.write(json.dumps(rec, separators=(",", ":")) + "\n")


def write_industrial(path):
    fields = ["dataset", "model", "precision", "n_items", "baseline_accuracy",
              "ramses_accuracy", "baseline_auroc", "ramses_auroc",
              "output_equivalence", "data_source"]
    rows = [
        ["expected_mvtec_ad", "vit-h14", "fp16", 1725, .941, .941, .978, .978, .998, SOURCE],
        ["expected_visa", "vit-h14", "fp16", 1200, .928, .928, .965, .965, .998, SOURCE],
        ["expected_ai4i_2020", "llama3-8b", "fp16", 2000, .901, .901, .944, .944, .997, SOURCE],
    ]
    with path.open("w", newline="") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


def write_sensitivity(path):
    rows = {
        "block_size_mb": [(1, 498), (2, 458), (4, 421), (8, 439), (16, 482)],
        "sampling_ms": [(100, 429), (200, 421), (400, 451)],
        "hysteresis_pct": [(2, 443), (5, 421), (10, 448)],
        "reuse_window": [(16, 441), (32, 421), (64, 435)],
    }
    with path.open("w", newline="") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["param", "value", "p99_ms", "data_source"])
        for param, values in rows.items():
            for value, p99 in values:
                writer.writerow([param, value, p99, SOURCE])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path,
                        default=Path(__file__).resolve().parent / "data")
    parser.add_argument("--seed", type=int, default=20260826)
    parser.add_argument("--requests-per-run", type=int, default=20)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    write_raw(args.outdir / "raw.jsonl", args.seed, args.requests_per_run)
    write_industrial(args.outdir / "industrial_accuracy.csv")
    write_sensitivity(args.outdir / "sensitivity.csv")
    print(f"wrote synthetic planning projections to {args.outdir}")


if __name__ == "__main__":
    main()
