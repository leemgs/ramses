#!/usr/bin/env python3
"""Task Memory Manager (Section III-B).

Pairs task-level memory control with four NUMA-aware mechanisms:
  (1) NUMA-aware mapping   -- pin process/thread data to local nodes
                              (mbind / numa_alloc_onnode) to cut remote traffic;
  (2) jemalloc-based heap  -- separate small objects from large tensors;
  (3) task-level redistribution -- offload low-reuse tensors to DRAM before
                              VRAM saturates;
  (4) pressure predictor   -- read live utilization + I/O-queue depth and
                              trigger mitigation early.

Memory-access latency model:  T_access = T_local + gamma * T_remote.
Dependency-free reference of Algorithm 2.
"""
from __future__ import annotations


def access_latency(t_local: float, t_remote: float, gamma: float) -> float:
    """T_access = T_local + gamma * T_remote (gamma = remote-NUMA penalty)."""
    return t_local + gamma * t_remote


class PressurePredictor:
    """Lightweight linear predictor over utilization and I/O-queue depth.
    No learned parameters or offline training (consistent with Section III-E)."""
    def __init__(self, w_util=0.7, w_queue=0.3):
        self.w_util, self.w_queue = w_util, w_queue

    def predict(self, utilization: float, io_queue_depth_norm: float) -> float:
        return self.w_util * utilization + self.w_queue * io_queue_depth_norm


class TaskMemoryManager:
    def __init__(self, vram_mb: int, threshold: float = 0.9, gamma: float = 1.6):
        self.vram_mb = vram_mb
        self.threshold = threshold         # fraction of VRAM that triggers offload
        self.gamma = gamma
        self.predictor = PressurePredictor()
        self.small_heap, self.large_heap = {}, {}   # jemalloc-style separation

    def allocate(self, tensor_id: str, size_mb: float):
        (self.small_heap if size_mb < 1.0 else self.large_heap)[tensor_id] = size_mb

    def resident_mb(self):
        return sum(self.small_heap.values()) + sum(self.large_heap.values())

    def maybe_offload(self, reuse_prob):
        """Offload non-critical (low reuse-probability) large tensors to DRAM
        before VRAM saturates; returns the list of offloaded tensor ids."""
        if self.resident_mb() <= self.threshold * self.vram_mb:
            return []
        victims = sorted(self.large_heap, key=lambda k: reuse_prob.get(k, 0.0))
        offloaded = []
        for v in victims:
            if self.resident_mb() <= self.threshold * self.vram_mb:
                break
            offloaded.append(v)
            del self.large_heap[v]
        return offloaded


if __name__ == "__main__":
    print("T_access =", access_latency(1.0, 2.5, gamma=1.6), "us")
    m = TaskMemoryManager(vram_mb=1000, threshold=0.5)
    for i in range(8):
        m.allocate(f"t{i}", 100.0)
    print("resident:", m.resident_mb(), "MB")
    print("offloaded:", m.maybe_offload({f"t{i}": i for i in range(8)}))
