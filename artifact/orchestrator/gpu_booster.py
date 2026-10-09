#!/usr/bin/env python3
"""GPU Booster with swap support (Section III-C).

Selects inactive tensors by execution-graph reuse distance, schedules
block-aligned (4 MB) asynchronous VRAM<->NVMe transfers overlapped with compute
on dedicated streams, and partially reloads only the portion of a swapped tensor
the next kernel needs. Output equivalence against the unoptimized baseline is
checked bitwise for FP32 and within tolerance for FP16.

On a GPU this plan is executed over a GPUDirect Storage direct path (or a
pinned-host-buffer staged path as a fallback) by the LD_PRELOAD layer
(ramses_preload.c). Here it is a dependency-free reference of Algorithm 3.
"""
from __future__ import annotations
import math

BLOCK_BYTES = 4 * 1024 * 1024    # 4 MB, matched to the NVMe erase-block size


def align_blocks(n_bytes: int) -> int:
    """Round a transfer up to whole 4 MB blocks (block rounding is counted in
    the measured transfer volume)."""
    return math.ceil(n_bytes / BLOCK_BYTES) * BLOCK_BYTES


class GPUBooster:
    def __init__(self):
        self.swapped = {}            # tensor_id -> aligned byte size on NVMe

    def plan_evictions(self, live, reuse_score, bytes_needed):
        """Rank eviction candidates by ascending reuse score and pick enough to
        free `bytes_needed`. Returns (victims, bytes_freed)."""
        order = sorted(live, key=lambda k: reuse_score.get(k, 0.0))
        victims, freed = [], 0
        for t in order:
            if freed >= bytes_needed:
                break
            victims.append(t)
            freed += align_blocks(live[t])
        return victims, freed

    def swap_out(self, tensor_id, size_bytes):
        aligned = align_blocks(size_bytes)
        self.swapped[tensor_id] = aligned
        return aligned               # bytes written to NVMe (async DMA)

    def partial_reload(self, tensor_id, needed_bytes):
        """Fetch only the blocks the next kernel needs."""
        if tensor_id not in self.swapped:
            return 0
        fetch = min(align_blocks(needed_bytes), self.swapped[tensor_id])
        if fetch >= self.swapped[tensor_id]:
            del self.swapped[tensor_id]
        return fetch                 # bytes read from NVMe (async DMA)

    @staticmethod
    def output_equivalent(baseline, ramses, precision="fp16", tol=1e-3):
        if precision == "fp32":
            return baseline == ramses
        return all(abs(a - b) <= tol for a, b in zip(baseline, ramses))


if __name__ == "__main__":
    b = GPUBooster()
    live = {"w0": 10_000_000, "w1": 6_000_000, "w2": 20_000_000}
    victims, freed = b.plan_evictions(live, {"w0": 0.1, "w1": 0.9, "w2": 0.2}, 12_000_000)
    print("evict:", victims, "freed:", freed, "bytes")
    for v in victims:
        b.swap_out(v, live[v])
    print("partial reload w0:", b.partial_reload("w0", 1_000_000), "bytes")
    print("FP32 equivalent:", b.output_equivalent([1.0, 2.0], [1.0, 2.0], "fp32"))
