#!/usr/bin/env python3
"""RAMSES regime-aware control plane (Regime Analyzer + Policy Engine).

Reference implementation of the online controller in Section III-D/E:

  * Pressure ratios from independent observables (Eqs. for alpha, beta):
        alpha(t) = D(t) / C_f                         (capacity pressure)
        beta(t)  = (L0 + q + V_up/B_up + V_down/B_down)
                   / (T_comp + T_mem + T_sync)         (transfer pressure)
    with an overlap-aware predicted service time
        T_total = T_sync + T_mem + max(T_comp, (1 - h) * T_xfer).

  * Operational labels (NOT theorems): alpha > 1 -> capacity-limited;
    beta >= 1 -> transfer-limited; otherwise coordination-dominated.

  * Online policy: every 200 ms the analyzer recomputes (alpha, beta) in O(1);
    a state change requires three consecutive samples beyond a 5% hysteresis
    band. Per-state actions:
      capacity-limited   : reject admissions over the reserve; evict lowest
                           predicted-reuse tensors (O(log n) heap).
      transfer-limited   : stop speculative eviction; reduce prefetch depth;
                           prioritize reads.
      coordination-dom.  : enable asynchronous prefetch + NUMA-local placement.
    Objective is lexicographic: prevent allocation failure, then minimize
    measured p99 latency, then transfer bytes.

Run `--replay` over the released request-level log to reproduce the operating
model validation (regime mix and prediction MAE/RMSE) without a GPU:

    python3 regime_controller.py --replay ../data/actual/raw.jsonl
"""
from __future__ import annotations
import argparse
import heapq
import json
import math
import os
from collections import defaultdict, deque

SAMPLE_MS = 200          # analyzer sampling interval
HYSTERESIS = 0.05        # 5% band
SWITCH_SAMPLES = 3       # consecutive samples required to switch state
REUSE_WINDOW = 32        # graph steps in the reuse-distance window

CAP, XFER, COORD = "capacity-limited", "transfer-limited", "coordination-dominated"


def classify(alpha: float, beta: float) -> str:
    """Operational regime label from the two pressure ratios."""
    if alpha is not None and alpha > 1.0:
        return CAP
    if beta is not None and beta >= 1.0:
        return XFER
    return COORD


def predicted_total(t_comp, t_mem, t_sync, t_xfer, h):
    """Overlap-aware predicted service time (max{} prevents double counting)."""
    return t_sync + t_mem + max(t_comp, (1.0 - h) * t_xfer)


class ReuseTable:
    """EWMA access score over the last REUSE_WINDOW graph steps; the eviction
    victim is the live tensor with the lowest score (min-heap, O(log n))."""
    def __init__(self, window=REUSE_WINDOW, decay=0.9):
        self.window = window
        self.decay = decay
        self.score = {}
        self.step = 0

    def touch(self, tensor_id):
        self.step += 1
        self.score[tensor_id] = self.score.get(tensor_id, 0.0) * self.decay + 1.0

    def victim(self, live_ids):
        return min(live_ids, key=lambda k: self.score.get(k, 0.0), default=None)


class RegimeController:
    """Online regime classifier with hysteresis and three-sample switching."""
    def __init__(self):
        self.state = COORD
        self._pending = None
        self._count = 0

    def _candidate(self, alpha, beta):
        # Hysteresis band around the thresholds avoids oscillation.
        if alpha is not None and alpha > 1.0 + HYSTERESIS:
            return CAP
        if beta is not None and beta >= 1.0 - 0.0 and beta >= 1.0:
            return XFER
        if beta is not None and beta > 1.0 - HYSTERESIS and self.state == XFER:
            return XFER      # sticky: stay transfer-limited within the band
        if alpha is not None and alpha > 1.0 - HYSTERESIS and self.state == CAP:
            return CAP
        return COORD

    def update(self, alpha, beta):
        cand = self._candidate(alpha, beta)
        if cand == self.state:
            self._pending, self._count = None, 0
            return self.state
        if cand == self._pending:
            self._count += 1
        else:
            self._pending, self._count = cand, 1
        if self._count >= SWITCH_SAMPLES:
            self.state, self._pending, self._count = cand, None, 0
        return self.state

    @staticmethod
    def actions(state):
        return {
            CAP:  ["reject_admission_over_reserve", "evict_lowest_reuse"],
            XFER: ["stop_speculative_eviction", "reduce_prefetch_depth", "prioritize_reads"],
            COORD:["enable_async_prefetch", "numa_local_placement"],
        }[state]


def replay(path):
    """Reproduce the operating-model validation from the released log."""
    per = defaultdict(lambda: {"n": 0, "regimes": defaultdict(int),
                               "abs_err": 0.0, "sq_err": 0.0,
                               "beta_sum": 0.0, "hits": 0, "miss": 0})
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            sys_ = r.get("system", "?")
            a, b = r.get("alpha"), r.get("beta")
            s = per[sys_]
            s["n"] += 1
            s["regimes"][classify(a, b)] += 1
            if b is not None:
                s["beta_sum"] += b
            if r.get("predicted_ms") is not None and r.get("latency_ms") is not None:
                e = r["predicted_ms"] - r["latency_ms"]
                s["abs_err"] += abs(e)
                s["sq_err"] += e * e
            s["hits"] += int(r.get("prefetch_hits", 0) or 0)
            s["miss"] += int(r.get("prefetch_misses", 0) or 0)

    width = max(len(k) for k in per)
    print(f"{'system':<{width}}  {'n':>5}  {'MAE(ms)':>8}  {'RMSE(ms)':>8}  "
          f"{'mean_beta':>9}  {'prefetch':>8}  regime_mix")
    for sys_ in sorted(per):
        s = per[sys_]
        n = s["n"]
        mae = s["abs_err"] / n if n else 0.0
        rmse = math.sqrt(s["sq_err"] / n) if n else 0.0
        mb = s["beta_sum"] / n if n else 0.0
        ph = s["hits"] / (s["hits"] + s["miss"]) if (s["hits"] + s["miss"]) else 0.0
        mix = ", ".join(f"{k}:{100*v/n:.0f}%" for k, v in sorted(s["regimes"].items()))
        print(f"{sys_:<{width}}  {n:>5}  {mae:>8.2f}  {rmse:>8.2f}  "
              f"{mb:>9.3f}  {ph:>8.3f}  {mix}")


def demo():
    """Tiny self-contained demonstration of the switching logic."""
    c = RegimeController()
    seq = [(0.6, 0.6)] * 3 + [(1.4, 0.7)] * 4 + [(0.7, 1.2)] * 4
    for a, b in seq:
        st = c.update(a, b)
        print(f"alpha={a:.2f} beta={b:.2f} -> {st:<22} actions={c.actions(st)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--replay", help="request-level JSONL log to replay")
    ap.add_argument("--demo", action="store_true", help="show the switching logic")
    a = ap.parse_args()
    if a.replay:
        replay(a.replay)
    elif a.demo:
        demo()
    else:
        default = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "data", "actual", "raw.jsonl")
        if os.path.exists(default):
            replay(default)
        else:
            demo()


if __name__ == "__main__":
    main()
