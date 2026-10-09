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
# Backend dispatch. A backend module (e.g., mvtec_vit) supplies load_dataset()
# and run_model(); pass --backend to use it. Without one, the hooks explain how
# to wire your own.
# --------------------------------------------------------------------------
_BACKEND = None


def set_backend(module_name):
    global _BACKEND
    if module_name:
        import importlib
        _BACKEND = importlib.import_module(module_name)


def load_dataset(name, data_root):
    """Return list of (item_id, image_path, label) for the named dataset.

    MVTec AD: label 1 for defective ('anomaly'), 0 for 'good'; official test
    split. Delegates to the --backend module when one is set (see mvtec_vit.py).
    """
    if _BACKEND:
        return _BACKEND.load_dataset(name, data_root)
    raise NotImplementedError(
        f"No backend set. Pass --backend mvtec_vit, or wire load_dataset("
        f"'{name}', '{data_root}') to return [(item_id, path, label), ...].")


def run_model(items, model_name, precision, serving_mode):
    """Run inference under a serving mode and return
    (scores, preds, outputs, latencies).

    serving_mode: 'baseline' (unmodified PyTorch) or 'ramses' (LD_PRELOAD layer).
    Because the LD_PRELOAD layer is process-global, the two modes are normally
    run as two separate processes (see --mode single and --compare); the
    in-process 'both' path suits a Python-API backend. Delegates to --backend.
    """
    if _BACKEND:
        return _BACKEND.run_model(items, model_name, precision, serving_mode)
    raise NotImplementedError(
        f"No backend set. Pass --backend mvtec_vit, or wire run_model("
        f"model='{model_name}', serving_mode='{serving_mode}').")


def save_outputs(path, items, scores, preds, outputs, labels):
    import json as _json
    with open(path, "w") as f:
        _json.dump({"item_ids": [i for i, _p, _l in items], "labels": labels,
                    "scores": scores, "preds": preds, "outputs": outputs}, f)
    print(f"wrote per-item outputs to {path}")


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


def accuracy_row(dataset, model, precision, labels, b, r):
    b_scores, b_preds, b_out = b
    r_scores, r_preds, r_out = r
    return {
        "dataset": dataset, "model": model, "precision": precision,
        "n_items": len(labels),
        "baseline_accuracy": accuracy(labels, b_preds),
        "ramses_accuracy": accuracy(labels, r_preds),
        "baseline_auroc": auroc(labels, b_scores),
        "ramses_auroc": auroc(labels, r_scores),
        "output_equivalence": output_equivalence(b_out, r_out, precision),
    }


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="mvtec_ad")
    ap.add_argument("--data-root")
    ap.add_argument("--model", default="vit-h14")
    ap.add_argument("--precision", default="fp16")
    ap.add_argument("--run-id", default="r1")
    ap.add_argument("--backend", default="", help="backend module, e.g. mvtec_vit")
    ap.add_argument("--mode", choices=["both", "single"], default="both",
                    help="'both' runs baseline+ramses in one process (Python-API "
                         "backend); 'single' runs one serving mode (LD_PRELOAD).")
    ap.add_argument("--serving-mode", choices=["baseline", "ramses"], default="baseline")
    ap.add_argument("--outputs-file", default="", help="single-mode: persist per-item outputs here")
    ap.add_argument("--compare", nargs=2, metavar=("BASELINE_JSON", "RAMSES_JSON"),
                    help="compute accuracy + output equivalence from two saved runs")
    ap.add_argument("--out-jsonl", default="industrial.jsonl")
    ap.add_argument("--out-csv", default="industrial_accuracy.csv")
    a = ap.parse_args()
    set_backend(a.backend)

    # Cross-process comparison of two persisted single-mode runs.
    if a.compare:
        import json as _json
        base = _json.load(open(a.compare[0]))
        rams = _json.load(open(a.compare[1]))
        labels = base["labels"]
        row = accuracy_row(a.dataset, a.model, a.precision, labels,
                           (base["scores"], base["preds"], base["outputs"]),
                           (rams["scores"], rams["preds"], rams["outputs"]))
        write_accuracy_csv(a.out_csv, [row])
        print(row)
        return

    if not a.data_root:
        ap.error("--data-root is required unless --compare is used")
    items = load_dataset(a.dataset, a.data_root)
    labels = [lab for _id, _p, lab in items]

    if a.mode == "single":
        t0 = time.time()
        scores, preds, outputs, lat = run_model(items, a.model, a.precision, a.serving_mode)
        write_jsonl(a.out_jsonl, a.model, a.precision, a.serving_mode, items, lat, a.run_id)
        out_file = a.outputs_file or f"outputs_{a.serving_mode}.json"
        save_outputs(out_file, items, scores, preds, outputs, labels)
        print(f"{a.serving_mode}: {len(items)} items in {time.time()-t0:.1f}s. "
              f"Run the other mode, then: --compare <baseline.json> <ramses.json>")
        return

    results = {}
    for mode in ("baseline", "ramses"):
        t0 = time.time()
        scores, preds, outputs, lat = run_model(items, a.model, a.precision, mode)
        results[mode] = (scores, preds, outputs)
        write_jsonl(a.out_jsonl, a.model, a.precision, mode, items, lat, a.run_id)
        print(f"{mode}: {len(items)} items in {time.time()-t0:.1f}s")

    row = accuracy_row(a.dataset, a.model, a.precision, labels,
                       results["baseline"], results["ramses"])
    write_accuracy_csv(a.out_csv, [row])
    print(row)


if __name__ == "__main__":
    main()
