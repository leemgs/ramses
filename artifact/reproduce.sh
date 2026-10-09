#!/usr/bin/env bash
# =============================================================================
# One-command reproduction of every table and figure in the paper from the
# released request-level data. Rename-safe: resolves its own directory, so it
# works whether this folder is called code/ or artifact/.
#
#   ./reproduce.sh            # tables + figures + control-plane replay + tests
#   ./reproduce.sh tables     # regenerate paper/tables/*_body.tex only
#   ./reproduce.sh figures    # regenerate paper/figures/*.png only
#   ./reproduce.sh verify     # control-plane replay + unit tests only
# =============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
DATA="$HERE/data/actual"
PY="${PYTHON:-python3}"

tables() {
  echo "==> Regenerating tables -> paper/tables/*_body.tex"
  "$PY" "$HERE/make_tables.py" \
      --summary "$DATA/summary.csv" --stats "$DATA/stats.csv" \
      --qos "$DATA/qos_timeseries.csv" \
      --loadtime "$DATA/loadtime_vram.csv" --industrial "$DATA/industrial_accuracy.csv" \
      --task ttft --model llama4-17b --outdir "$ROOT/paper/tables"
}

figures() {
  echo "==> Regenerating figures -> paper/figures/*.png"
  if ! "$PY" -c "import matplotlib" 2>/dev/null; then
    echo "    matplotlib not installed; skipping (pip install matplotlib to enable)."
    return 0
  fi
  "$PY" "$HERE/make_figures.py" \
      --summary "$DATA/summary.csv" --stats "$DATA/stats.csv" \
      --sensitivity "$DATA/sensitivity.csv" --outdir "$ROOT/paper/figures" --task ttft --model llama4-17b
}

verify() {
  echo "==> Control-plane replay (operating-model validation)"
  "$PY" "$HERE/orchestrator/regime_controller.py" --replay "$DATA/raw.jsonl"
  echo "==> Unit tests"
  "$PY" -m pytest -q "$HERE/tests" 2>/dev/null || "$PY" -m unittest discover -s "$HERE/tests" -v
}

case "${1:-all}" in
  tables)  tables ;;
  figures) figures ;;
  verify)  verify ;;
  all)     tables; figures; verify ;;
  *) echo "usage: $0 [all|tables|figures|verify]" >&2; exit 2 ;;
esac
echo "==> Done."
