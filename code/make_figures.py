#!/usr/bin/env python3
"""Generate paper figures from *measured* RAMSES results (matplotlib).

Every figure is drawn from the CSVs produced by analyze_results.py and
compute_stats.py; nothing is hard-coded. If the required columns are absent the
corresponding figure is skipped (no synthetic points are drawn).

Figures:
  1. consolidated_results.png  -- normalized load/VRAM/latency per system with
                                  95% CI error bars (Fig. 3 replacement).
  2. energy_latency.png        -- measured (energy, latency) points per system,
                                  RAMSES convex hull (Fig. 4).
  3. phase_measured.png        -- measured (alpha, beta) operating points over
                                  the classification thresholds (Fig. 2 overlay).
  4. sensitivity.png           -- p99 vs block size / controller parameter sweep.

Usage:
    python3 code/make_figures.py --summary code/data/summary.csv \
        --stats code/data/stats.csv --sensitivity code/data/sensitivity.csv \
        --outdir paper/figures --task ttft

Requires matplotlib and numpy in the author's environment.
"""
import argparse, csv, os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "code", "data")
PAPER_FIGURES = os.path.join(REPO_ROOT, "paper", "figures")


def read_csv(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def fval(row, key):
    v = row.get(key, "")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def filt(rows, task, model):
    out = []
    for r in rows or []:
        if task and r.get("task") != task:
            continue
        if model and r.get("model") != model:
            continue
        out.append(r)
    return out


def mark_projection(ax, rows):
    if any("synthetic" in r.get("data_source", "") for r in rows or []):
        ax.text(0.5, 0.5, "SYNTHETIC EXPECTATION\\nNOT MEASURED",
                transform=ax.transAxes, ha="center", va="center", rotation=25,
                fontsize=12, color="crimson", alpha=0.24, weight="bold", zorder=10)


def fig_energy_latency(summary, task, model, outdir, plt):
    import numpy as np
    rows = filt(summary, task, model)
    pts = [(r.get("system"), fval(r, "energy_per_request_j"), fval(r, "p50_ms"))
           for r in rows]
    pts = [(s, e, l) for s, e, l in pts if e is not None and l is not None]
    if not pts:
        print("skip energy_latency: no energy/latency points")
        return
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    base = [(e, l) for s, e, l in pts if s != "ramses"]
    ram = [(e, l) for s, e, l in pts if s == "ramses"]
    if base:
        be, bl = zip(*base)
        ax.scatter(be, bl, c="0.6", label="Baselines", zorder=2)
    if ram:
        re, rl = zip(*sorted(ram))
        ax.plot(re, rl, "-o", color="#1b7837", label="RAMSES", zorder=3)
    ax.set_xlabel("Energy per request (J)")
    ax.set_ylabel("Median latency (ms)")
    mark_projection(ax, rows)
    ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(outdir, "energy_latency.png"), dpi=200)
    print("wrote energy_latency.png")


def fig_phase(summary, task, model, outdir, plt):
    rows = filt(summary, task, model)
    pts = [(r.get("system"), fval(r, "alpha"), fval(r, "beta")) for r in rows]
    pts = [(s, a, b) for s, a, b in pts if a is not None and b is not None]
    if not pts:
        print("skip phase_measured: no (alpha,beta) points")
        return
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    ax.axvline(1.0, ls="--", c="0.5"); ax.axhline(1.0, ls="--", c="0.5")
    for s, a, b in pts:
        c = "#1b7837" if s == "ramses" else "0.4"
        ax.scatter(a, b, c=c)
        ax.annotate(s, (a, b), fontsize=6, xytext=(2, 2), textcoords="offset points")
    ax.set_xlabel(r"$\alpha = D / C_f$ (capacity pressure)")
    ax.set_ylabel(r"$\beta$ (transfer pressure)")
    mark_projection(ax, rows)
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "phase_measured.png"), dpi=200)
    print("wrote phase_measured.png")


def fig_consolidated(stats, outdir, plt):
    """Normalized load/VRAM/latency per system with 95% CI error bars.

    Expects stats.csv rows with metric in {load_ms, peak_vram_mb, latency_ms}.
    Values are normalized to the 'default' system per metric.
    """
    import numpy as np
    if not stats:
        print("skip consolidated: no stats.csv")
        return
    metrics = ["load_ms", "peak_vram_mb", "latency_ms"]
    present = sorted({r["metric"] for r in stats} & set(metrics))
    if not present:
        print("skip consolidated: none of load_ms/peak_vram_mb/latency_ms in stats")
        return
    systems = [s for s in ["default", "flexgen", "swapadvisor", "neo",
                           "specoffload", "vllm", "ramses"]
               if any(r["system"] == s for r in stats)]
    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    width = 0.8 / max(len(present), 1)
    x = np.arange(len(systems))
    for i, m in enumerate(present):
        base = next((float(r["mean"]) for r in stats
                     if r["metric"] == m and r["system"] == "default"), None)
        if not base:
            continue
        means, errs = [], []
        for s in systems:
            r = next((r for r in stats if r["metric"] == m and r["system"] == s), None)
            if r:
                means.append(100 * float(r["mean"]) / base)
                errs.append(100 * (float(r["ci95_high"]) - float(r["mean"])) / base)
            else:
                means.append(0); errs.append(0)
        ax.bar(x + i * width, means, width, yerr=errs, capsize=2, label=m)
    ax.set_xticks(x + width * (len(present) - 1) / 2)
    ax.set_xticklabels(systems, rotation=30, ha="right", fontsize=7)
    ax.set_ylabel("Normalized to Default (%)")
    mark_projection(ax, stats)
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(os.path.join(outdir, "consolidated_results.png"), dpi=200)
    print("wrote consolidated_results.png")


def fig_sensitivity(sens, outdir, plt):
    """Expects sensitivity.csv with columns: param, value, p99_ms."""
    if not sens:
        print("skip sensitivity: no sensitivity.csv")
        return
    from collections import defaultdict
    groups = defaultdict(list)
    for r in sens:
        try:
            groups[r["param"]].append((float(r["value"]), float(r["p99_ms"])))
        except (KeyError, ValueError):
            continue
    if not groups:
        print("skip sensitivity: no usable rows")
        return
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    for p, pts in sorted(groups.items()):
        pts.sort()
        xs, ys = zip(*pts)
        ax.plot(xs, ys, "-o", label=p)
    ax.set_xlabel("Parameter value"); ax.set_ylabel("p99 latency (ms)")
    mark_projection(ax, sens)
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(os.path.join(outdir, "sensitivity.png"), dpi=200)
    print("wrote sensitivity.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default=os.path.join(DATA_DIR, "summary.csv"))
    ap.add_argument("--stats", default=os.path.join(DATA_DIR, "stats.csv"))
    ap.add_argument("--sensitivity", default=os.path.join(DATA_DIR, "sensitivity.csv"))
    ap.add_argument("--outdir", default=PAPER_FIGURES)
    ap.add_argument("--task", default="ttft")
    ap.add_argument("--model", default="llama4-17b")
    a = ap.parse_args()
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise SystemExit("matplotlib is required: pip install matplotlib numpy")

    os.makedirs(a.outdir, exist_ok=True)
    summary = read_csv(a.summary)
    stats = read_csv(a.stats)
    sens = read_csv(a.sensitivity)
    task = a.task or None
    model = a.model or None
    if summary:
        fig_energy_latency(summary, task, model, a.outdir, plt)
        fig_phase(summary, task, model, a.outdir, plt)
    else:
        print("no summary.csv: energy/phase figures skipped")
    fig_consolidated(filt(stats, task, model), a.outdir, plt)
    fig_sensitivity(sens, a.outdir, plt)


if __name__ == "__main__":
    main()
