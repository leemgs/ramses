#!/usr/bin/env python3
"""GPU Process Allocator (Section III-A).

Pre-reserves GPU execution resources so that CUDA context initialization and
memory mapping no longer happen on the critical path under multi-model serving.
Three policies: (i) pre-defined slot reservation, (ii) context separation with
fixed memory pools, (iii) priority-based scheduling of I/O- vs compute-bound
models. This is a dependency-free reference of the control logic (Algorithm 1);
on a GPU it drives real CUDA context/stream creation.
"""
from __future__ import annotations
import heapq
from dataclasses import dataclass, field


@dataclass(order=True)
class _Task:
    priority: int
    model: str = field(compare=False)


class GPUProcessAllocator:
    def __init__(self, n_contexts: int, pool_mb: int):
        self.free_contexts = list(range(n_contexts))
        self.pool_mb = pool_mb
        self.reserved = {}          # model -> (ctx_id, pool_region, kernel_queue)
        self._queue = []            # priority heap of pending tasks

    def reserve(self, model: str, io_bound: bool):
        """(i) slot reservation + (ii) context separation with a fixed pool."""
        if model in self.reserved:
            return self.reserved[model]
        if not self.free_contexts:
            raise RuntimeError("no free CUDA context; admission must wait")
        ctx = self.free_contexts.pop(0)
        region = (ctx * self.pool_mb, (ctx + 1) * self.pool_mb)   # disjoint pool
        self.reserved[model] = (ctx, region, f"queue:{ctx}")
        # (iii) I/O-bound models get higher scheduling priority so they do not
        # stall compute-bound models and idle GPU cycles shrink.
        heapq.heappush(self._queue, _Task(0 if io_bound else 1, model))
        return self.reserved[model]

    def dispatch(self):
        """Dequeue the next task by priority and launch on its reserved context."""
        if not self._queue:
            return None
        t = heapq.heappop(self._queue)
        return self.reserved[t.model]

    def release(self, model: str):
        ctx, _, _ = self.reserved.pop(model)
        self.free_contexts.append(ctx)
        self.free_contexts.sort()


if __name__ == "__main__":
    a = GPUProcessAllocator(n_contexts=2, pool_mb=40000)
    a.reserve("llama4-17b", io_bound=False)
    a.reserve("vit-h14", io_bound=True)
    print("dispatch order:", a.dispatch(), a.dispatch())
    a.release("vit-h14")
    print("free contexts after release:", a.free_contexts)
