#!/usr/bin/env python3
"""Named industrial-task evaluation scaffold (Reviewer R3-8).

Purpose: report *task accuracy* on a named, reproducible industrial dataset
(default target: MVTec AD visual defect inspection with a ViT classifier) and
verify *output equivalence* between the baseline serving path and RAMSES, so
the paper can state that RAMSES preserves task accuracy while improving
latency/VRAM/energy.

What is complete and runnable here (standard library only):
  * accuracy(), auroc()            -- metric computation
  * output_equivalence()           -- bitwise (fp32) / tolerance (fp16) match
  * write_jsonl(), write_accuracy_csv() -- schema-compatible outputs

What the author wires to their environment (clearly marked hooks):
  * load_dataset()  -- return (item_id, image_path, label) for the named set
  * run_model()     -- run the ViT/LLM under a given serving mode and return
                       per-item scores + raw output tensors

The scaffold never invents metric values: it computes them only from real model
outputs the hooks return.

Usage:
    python3 eval_industrial.py --dataset mvtec_ad --data-root /path/to/mvtec \
        --model vit-h14 --precision fp16 --out-jsonl industrial.jsonl \
        --out-csv industrial_accuracy.csv
"""
import argparse, csv, json, time


# --------------------------------------------------------------------------
# Metrics (complete, dependency-free)
# --------------------------------------------------------------------------
def accuracy(y_true, y_pred):
    if not y_true:
        return None
    return sum(int(a == b) for a, b in zip(y_true, y_pred)) / len(y_true)


def auroc(y_true, scores):
    """Rank-based AUROC for binary labels (1=positive/defect). Pure python."""
    pairs = sorted(zip(scores, y_true), key=lambda p: p[0])
    n = len(pairs)
    n_pos = sum(y for _, y in pairs)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    # average ranks (1-indexed) with tie handling
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    sum_pos_ranks = sum(r for r, (_, y) in zip(ranks, pairs) if y == 1)
    return (sum_pos_ranks - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def output_equivalence(base_outputs, ramses_outputs, precision):
    """Fraction of items whose RAMSES output matches the baseline.

    fp32 -> exact (bitwise) match; fp16/bf16 -> within a relative tolerance.
    Each output is a flat sequence of floats.
    """
    if not base_outputs:
        return None
    tol = 0.0 if precision.lower() in ("fp32", "float32") else 1e-2
    matches = 0
    for a, b in zip(base_outputs, ramses_outputs):
        if len(a) != len(b):
            continue
        if tol == 0.0:
            ok = all(x == y for x, y in zip(a, b))
        else:
            ok = all(abs(x - y) <= tol * (abs(x) + 1e-9) for x, y in zip(a, b))
        matches += int(ok)
    return matches / len(base_outputs)


# --------------------------------------------------------------------------
# Author integration hooks (wire to your environment)
# --------------------------------------------------------------------------
def load_dataset(name, data_root):
    """Return list of (item_id, image_path, label) for the named dataset.

    MVTec AD: label 1 for defective ('anomaly'), 0 for 'good'. Use the official
    test split. VisA is analogous. Replace the body with your loader.
    """
    raise NotImplementedError(
        f"Wire load_dataset('{name}', '{data_root}') to your dataset loader. "
        "Return [(item_id, image_path, label), ...] from the official test split.")


def run_model(items, model_name, precision, serving_mode):
    """Run inference under a serving mode and return (scores, outputs, latencies).

    Args:
      items: list of (item_id, image_path, label)
      serving_mode: 'baseline' (unmodified PyTorch) or 'ramses' (LD_PRELOAD layer)
    Returns:
      scores    : list[float]  per-item positive-class score (for AUROC)
      preds     : list[int]    per-item predicted label (for accuracy)
      outputs   : list[list[float]] per-item raw logits (for equivalence)
      latencies : list[float]  per-item latency in ms
    Wire this to your ViT-H/14 (or LLM) + serving backend.
    """
    raise NotImplementedError(
        f"Wire run_model(model='{model_name}', precision='{precision}', "
        f"serving_mode='{serving_mode}') to your inference + serving backend.")


# --------------------------------------------------------------------------
# Output writers (schema-compatible)
# --------------------------------------------------------------------------
def write_jsonl(path, model, precision, serving_mode, items, latencies, run_id):
    with open(path, "a") as f:
        for (item_id, _p, _l), lat in zip(items, latencies):
            rec = {
                "run_id": run_id, "system": serving_mode, "task": "scoring",
                "latency_ms": lat, "input_tokens": 0, "output_tokens": 0,
                "batch": 1, "concurrency": 1, "request_count": 1,
                "precision": precision, "model": model, "item_id": item_id,
            }
            f.write(json.dumps(rec) + "\n")


def write_accuracy_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}")


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="mvtec_ad")
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--model", default="vit-h14")
    ap.add_argument("--precision", default="fp16")
    ap.add_argument("--run-id", default="r1")
    ap.add_argument("--out-jsonl", default="industrial.jsonl")
    ap.add_argument("--out-csv", default="industrial_accuracy.csv")
    a = ap.parse_args()

    items = load_dataset(a.dataset, a.data_root)
    labels = [lab for _id, _p, lab in items]

    results = {}
    for mode in ("baseline", "ramses"):
        t0 = time.time()
        scores, preds, outputs, lat = run_model(items, a.model, a.precision, mode)
        results[mode] = (scores, preds, outputs, lat)
        write_jsonl(a.out_jsonl, a.model, a.precision, mode, items, lat, a.run_id)
        print(f"{mode}: {len(items)} items in {time.time()-t0:.1f}s")

    b_scores, b_preds, b_out, _ = results["baseline"]
    r_scores, r_preds, r_out, _ = results["ramses"]
    rows = [{
        "dataset": a.dataset, "model": a.model, "precision": a.precision,
        "n_items": len(items),
        "baseline_accuracy": accuracy(labels, b_preds),
        "ramses_accuracy": accuracy(labels, r_preds),
        "baseline_auroc": auroc(labels, b_scores),
        "ramses_auroc": auroc(labels, r_scores),
        "output_equivalence": output_equivalence(b_out, r_out, a.precision),
    }]
    write_accuracy_csv(a.out_csv, rows)
    print(rows[0])


if __name__ == "__main__":
    main()
