#!/usr/bin/env python3
"""Generate LaTeX table bodies from *measured* RAMSES results.

Reads the CSVs produced by analyze_results.py (summary) and compute_stats.py
(stats) and writes booktabs table bodies to paper/tables/*_body.tex. It emits a row
only for data that exists in the CSV: no placeholder numbers are ever written.
If a required CSV is missing the corresponding table body is not generated, and
the LaTeX wrapper's \\IfFileExists guard keeps the paper compilable.

Usage:
    python3 code/make_tables.py --summary code/data/summary.csv \
        --stats code/data/stats.csv --outdir paper/tables \
        --task ttft --model llama4-17b

Standard library only.
"""
import argparse, csv, os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "code", "data")
PAPER_TABLES = os.path.join(REPO_ROOT, "paper", "tables")

# Display order and human labels for systems.
SYS_ORDER = ["default", "flexgen", "swapadvisor", "neo", "specoffload", "vllm",
             "ramses", "ramses_policy_off"]
SYS_LABEL = {"default": "PyTorch (Default)", "flexgen": "FlexGen",
             "swapadvisor": "SwapAdvisor", "neo": "NEO",
             "specoffload": "SpecOffload", "vllm": "vLLM",
             "ramses": "RAMSES", "ramses_policy_off": "RAMSES (policy-off)"}


def read_csv(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def num(row, key, fmt="{:.1f}"):
    v = row.get(key, "")
    if v in ("", None):
        return "--"
    try:
        return fmt.format(float(v))
    except (TypeError, ValueError):
        return str(v)


def sys_sort(rows):
    idx = {s: i for i, s in enumerate(SYS_ORDER)}
    return sorted(rows, key=lambda r: idx.get(r.get("system"), 99))


def write(path, lines):
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path} ({len(lines)} rows)")


def filt(rows, task, model):
    out = []
    for r in rows:
        if task and r.get("task") != task:
            continue
        if model and r.get("model") != model:
            continue
        out.append(r)
    return out


def table_percentiles(summary, task, model, outdir):
    rows = sys_sort(filt(summary, task, model))
    if not rows:
        return
    body = []
    for r in rows:
        body.append(" & ".join([
            SYS_LABEL.get(r["system"], r["system"]),
            num(r, "p50_ms"), num(r, "p95_ms"), num(r, "p99_ms"),
            num(r, "p99_9_ms"), num(r, "max_ms"),
        ]) + r" \\")
    write(os.path.join(outdir, "latency_percentiles_body.tex"), body)


def table_energy(summary, task, model, outdir):
    rows = sys_sort(filt(summary, task, model))
    rows = [r for r in rows if r.get("node_energy_j") not in ("", None)]
    if not rows:
        return
    body = []
    for r in rows:
        body.append(" & ".join([
            SYS_LABEL.get(r["system"], r["system"]),
            num(r, "energy_per_request_j", "{:.2f}"),
            num(r, "energy_per_token_j", "{:.3f}"),
            num(r, "edp_j_ms", "{:.1f}"),
            num(r, "throughput_tps", "{:.2f}"),
        ]) + r" \\")
    write(os.path.join(outdir, "energy_body.tex"), body)


def table_model_validation(summary, task, model, outdir):
    rows = sys_sort(filt(summary, task, model))
    rows = [r for r in rows if r.get("predicted_ms") not in ("", None)]
    if not rows:
        return
    body = []
    for r in rows:
        body.append(" & ".join([
            SYS_LABEL.get(r["system"], r["system"]),
            num(r, "alpha", "{:.2f}"), num(r, "beta", "{:.2f}"),
            num(r, "mae_ms", "{:.1f}"), num(r, "rmse_ms", "{:.1f}"),
            num(r, "prefetch_hit_rate", "{:.2f}"),
        ]) + r" \\")
    write(os.path.join(outdir, "model_validation_body.tex"), body)


def table_policy_off(summary, task, model, outdir):
    rows = {r["system"]: r for r in filt(summary, task, model)}
    if "ramses" not in rows or "ramses_policy_off" not in rows:
        return
    body = []
    for s in ("ramses", "ramses_policy_off"):
        r = rows[s]
        body.append(" & ".join([
            SYS_LABEL[s], num(r, "p99_ms"), num(r, "p99_9_ms"),
            num(r, "energy_per_request_j", "{:.2f}"),
        ]) + r" \\")
    write(os.path.join(outdir, "policy_off_body.tex"), body)


def table_ci(stats, task, model, outdir):
    if not stats:
        return
    rows = sys_sort(filt(stats, task, model))
    if not rows:
        return
    body = []
    for r in rows:
        try:
            mean, lo, hi = float(r["mean"]), float(r["ci95_low"]), float(r["ci95_high"])
            cell = f"{mean:.1f} & [{lo:.1f}, {hi:.1f}]"
        except (KeyError, ValueError):
            cell = "-- & --"
        body.append(f"{SYS_LABEL.get(r['system'], r['system'])} & {cell} & {r.get('runs','--')}" + r" \\")
    write(os.path.join(outdir, "latency_ci_body.tex"), body)


def table_industrial(industrial, outdir):
    if not industrial:
        return
    body = []
    for r in industrial:
        body.append(" & ".join([
            r.get("dataset", "--"), r.get("model", "--"),
            num(r, "baseline_accuracy", "{:.3f}"), num(r, "ramses_accuracy", "{:.3f}"),
            num(r, "baseline_auroc", "{:.3f}"), num(r, "ramses_auroc", "{:.3f}"),
            num(r, "output_equivalence", "{:.3f}"),
        ]) + r" \\")
    write(os.path.join(outdir, "industrial_body.tex"), body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=os.path.join(DATA_DIR, "summary.csv"))
    ap.add_argument("--stats", default=os.path.join(DATA_DIR, "stats.csv"))
    ap.add_argument("--industrial", default=os.path.join(DATA_DIR, "industrial_accuracy.csv"))
    ap.add_argument("--outdir", default=PAPER_TABLES)
    ap.add_argument("--task", default="ttft", help="filter task; empty for all")
    ap.add_argument("--model", default="", help="filter model; empty for all")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    summary = read_csv(a.summary)
    stats = read_csv(a.stats)
    industrial = read_csv(a.industrial)
    task = a.task or None
    model = a.model or None
    if summary is not None:
        table_percentiles(summary, task, model, a.outdir)
        table_energy(summary, task, model, a.outdir)
        table_model_validation(summary, task, model, a.outdir)
        table_policy_off(summary, task, model, a.outdir)
    else:
        print(f"summary CSV not found: {a.summary} -- percentile/energy/"
              "validation/policy tables skipped.")
    table_ci(stats, task, model, a.outdir)
    table_industrial(industrial, a.outdir)


if __name__ == "__main__":
    main()
