#!/usr/bin/env bash
set -uo pipefail
failed=0
check(){ if command -v "$1" >/dev/null; then printf 'PASS %s\n' "$1"; else printf 'MISSING %s\n' "$1"; failed=1; fi; }
for x in python3 nvidia-smi numactl nvme iostat; do check "$x"; done
[ -e /dev/nvidia0 ] && echo 'PASS /dev/nvidia0' || { echo 'MISSING /dev/nvidia0'; failed=1; }
[ -d /sys/class/powercap ] && echo 'PASS /sys/class/powercap' || { echo 'MISSING /sys/class/powercap'; failed=1; }
exit "$failed"
