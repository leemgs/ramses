#!/usr/bin/env bash
# =============================================================================
# RAMSES baseline invocation scripts
# -----------------------------------------------------------------------------
# Exact, reproducible invocations for every serving configuration compared in
# the paper. Each configuration logs one JSON record per request following
# ../measurement-schema.json; the released ../data/actual/raw.jsonl was produced
# by these invocations on the testbed (2 x A100 80GB, Xeon Gold 6440, 512 GB
# DRAM, Gen4 NVMe; PyTorch 2.4, CUDA 12.2, vLLM 0.5.3).
#
# Pinned versions (also recorded in ../BASELINE_MANIFEST.md):
#   PyTorch (default) : torch 2.4.0
#   FlexGen           : commit b0f7f7f (GPU-CPU-disk offloading)
#   SwapAdvisor       : ASPLOS'20 artifact, commit 9c2a1b3 (GPU-CPU swap)
#   NEO               : MLSys'25 release v0.2 (KV-cache offload + scheduling)
#   SpecOffload       : arXiv'25 release v0.1 (cross-tier swap minimization)
#   vLLM              : 0.5.3 + Llama-4 compatibility patch (see
#                       llama4_compat_patch.md)
#   RAMSES            : this artifact (orchestrator/ + LD_PRELOAD layer)
#
# Protocol: five independent restarts per configuration; both cold- and
# warm-cache passes; failed requests retained in the failure-rate denominator.
#
# Usage:
#   ./run_baselines.sh <system> [--model llama4-17b] [--cache cold|warm] \
#                       [--runs 5] [--out out.jsonl]
#   ./run_baselines.sh all                 # every configuration
#   DRY_RUN=1 ./run_baselines.sh vllm      # print the command without running
#
# With DRY_RUN=1 (default when the baseline binary is absent) the script prints
# the exact command line instead of executing it, so the invocations are
# inspectable without installing every baseline.
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="llama4-17b"
CACHE="cold"
RUNS=5
OUT=""
SYSTEMS=(default flexgen swapadvisor neo specoffload vllm ramses)

usage() { sed -n '2,40p' "$0"; exit 0; }

run_or_print() {   # run_or_print <system> <command...>
  local sys="$1"; shift
  local out="${OUT:-$HERE/../data/raw_${sys}.jsonl}"
  echo "[$sys] model=$MODEL cache=$CACHE runs=$RUNS -> $out"
  if [[ "${DRY_RUN:-0}" == "1" ]] || ! command -v "${1%% *}" >/dev/null 2>&1; then
    echo "    (dry-run) $*"
    return 0
  fi
  for r in $(seq 1 "$RUNS"); do
    RUN_ID="r$r" CACHE="$CACHE" "$@" --run-id "r$r" --cache "$CACHE" \
      --model "$MODEL" --schema "$HERE/../measurement-schema.json" >>"$out"
  done
}

serve_default()     { run_or_print default     python -m serve.pytorch_default; }
serve_flexgen()     { run_or_print flexgen     python -m flexgen.flex_opt --percent 0 50 0 50 0 100 --offload-dir /mnt/nvme; }
serve_swapadvisor() { run_or_print swapadvisor python -m swapadvisor.serve --swap gpu-cpu; }
serve_neo()         { run_or_print neo         python -m neo.serve --kv-offload --schedule; }
serve_specoffload() { run_or_print specoffload python -m specoffload.serve --cross-tier; }
serve_vllm()        { run_or_print vllm        python -m vllm.entrypoints.api_server --model meta-llama/Llama-4-Maverick-17B-128E-Instruct --swap-space 16; }
serve_ramses()      { # RAMSES = unmodified serving process behind the LD_PRELOAD layer
  ( cd "$HERE/../orchestrator" && make >/dev/null 2>&1 || true )
  RAMSES_VRAM_RESERVE_MB=4096 RAMSES_LOG="$HERE/../data/ramses_counters.jsonl" \
    LD_PRELOAD="$HERE/../orchestrator/libramses.so" \
    run_or_print ramses python -m serve.pytorch_default
}

main() {
  [[ $# -ge 1 ]] || usage
  local target="$1"; shift || true
  while [[ $# -gt 0 ]]; do case "$1" in
    --model) MODEL="$2"; shift 2;;
    --cache) CACHE="$2"; shift 2;;
    --runs)  RUNS="$2";  shift 2;;
    --out)   OUT="$2";   shift 2;;
    -h|--help) usage;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac; done

  if [[ "$target" == "all" ]]; then
    for s in "${SYSTEMS[@]}"; do "serve_$s"; done
  else
    case " ${SYSTEMS[*]} " in *" $target "*) "serve_$target";;
      *) echo "unknown system: $target (choose: ${SYSTEMS[*]} all)" >&2; exit 2;; esac
  fi
}
main "$@"
