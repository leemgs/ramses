#!/usr/bin/env python3
"""Synchronized whole-node energy measurement for RAMSES (Reviewer R3-11).

Integrates GPU (NVML) and CPU package + DRAM (Intel RAPL) energy over the same
monotonic window, with counter-wrap handling and optional idle subtraction, and
emits the schema fields (`node_energy_j`, `gpu_energy_j`) plus a per-component
breakdown and instrument metadata (sampling, idle protocol, dropped samples).

This never fabricates readings: RAPL and NVML values come from the kernel and
driver. On a host without those interfaces the reader returns no domains and the
corresponding energy is reported as unavailable rather than guessed.

Design for testability: energy integration is a pure function (`integrate`) and
the RAPL/NVML sources are injectable, so the wrap/aggregation logic is unit
tested without hardware.

CLI (author's measured host):
    # wrap an inference command and print integrated node energy
    python3 collect_energy.py --idle-seconds 5 -- python run_inference.py ...
"""
import argparse, glob, json, os, subprocess, time


# --------------------------------------------------------------------------
# Pure integration (unit tested)
# --------------------------------------------------------------------------
def integrate(start_uj, end_uj, wrap_uj):
    """Return joules between two RAPL microjoule counter reads, handling one
    wrap of the counter (max range `wrap_uj`)."""
    delta = end_uj - start_uj
    if delta < 0 and wrap_uj:
        delta += wrap_uj
    return max(delta, 0) / 1e6


# --------------------------------------------------------------------------
# RAPL source (CPU package + DRAM); injectable for tests
# --------------------------------------------------------------------------
class RaplReader:
    """Reads Intel RAPL energy counters from /sys/class/powercap."""

    def __init__(self, root="/sys/class/powercap"):
        self.domains = {}  # name -> (energy_path, wrap_uj)
        for d in sorted(glob.glob(os.path.join(root, "intel-rapl:*"))):
            name_f = os.path.join(d, "name")
            energy_f = os.path.join(d, "energy_uj")
            range_f = os.path.join(d, "max_energy_range_uj")
            if not (os.path.exists(name_f) and os.path.exists(energy_f)):
                continue
            try:
                name = open(name_f).read().strip()
                wrap = int(open(range_f).read()) if os.path.exists(range_f) else 0
            except OSError:
                continue
            key = name if name not in self.domains else f"{name}:{os.path.basename(d)}"
            self.domains[key] = (energy_f, wrap)

    def read(self):
        out = {}
        for key, (path, wrap) in self.domains.items():
            try:
                out[key] = (int(open(path).read()), wrap)
            except (OSError, ValueError):
                continue
        return out


# --------------------------------------------------------------------------
# NVML source (GPU); optional
# --------------------------------------------------------------------------
class NvmlReader:
    def __init__(self):
        self.ok = False
        try:
            import pynvml
            pynvml.nvmlInit()
            self.pynvml = pynvml
            self.handles = [pynvml.nvmlDeviceGetHandleByIndex(i)
                            for i in range(pynvml.nvmlDeviceGetCount())]
            self.ok = True
        except Exception:
            self.pynvml = None
            self.handles = []

    def total_energy_j(self):
        """Sum of per-GPU total energy (mJ counter since driver load) -> J."""
        if not self.ok:
            return None
        total_mj = 0
        for h in self.handles:
            try:
                total_mj += self.pynvml.nvmlDeviceGetTotalEnergyConsumption(h)
            except Exception:
                return None
        return total_mj / 1e3


class EnergyMeter:
    """Context manager integrating node energy over the enclosed work."""

    def __init__(self, rapl=None, nvml=None, idle_power_w=None):
        self.rapl = rapl if rapl is not None else RaplReader()
        self.nvml = nvml if nvml is not None else NvmlReader()
        self.idle_power_w = idle_power_w or {}  # domain -> watts to subtract
        self.dropped = 0

    def __enter__(self):
        self.t0 = time.monotonic()
        self.rapl0 = self.rapl.read()
        self.gpu0 = self.nvml.total_energy_j()
        return self

    def __exit__(self, *exc):
        self.t1 = time.monotonic()
        rapl1 = self.rapl.read()
        gpu1 = self.nvml.total_energy_j()
        self.duration_s = self.t1 - self.t0
        self.components = {}
        for key, (e0, wrap) in self.rapl0.items():
            if key in rapl1:
                self.components[key] = integrate(e0, rapl1[key][0], wrap)
            else:
                self.dropped += 1
        if self.gpu0 is not None and gpu1 is not None:
            self.components["gpu"] = max(gpu1 - self.gpu0, 0.0)
        # idle subtraction (power * duration) per named domain
        for dom, watts in self.idle_power_w.items():
            if dom in self.components:
                self.components[dom] = max(
                    self.components[dom] - watts * self.duration_s, 0.0)
        return False

    def result(self):
        comp = self.components
        gpu = comp.get("gpu")
        node = sum(v for v in comp.values())
        return {
            "duration_s": self.duration_s,
            "gpu_energy_j": gpu,
            "node_energy_j": node if comp else None,
            "components_j": comp,
            "rapl_domains": sorted(self.rapl.domains),
            "nvml_available": self.nvml.ok,
            "dropped_samples": self.dropped,
            "idle_subtracted": dict(self.idle_power_w),
        }


def measure_idle(seconds, rapl=None, nvml=None):
    """Measure idle power (W) per component over `seconds` for later subtraction."""
    m = EnergyMeter(rapl=rapl, nvml=nvml)
    with m:
        time.sleep(seconds)
    r = m.result()
    dur = r["duration_s"] or 1.0
    return {k: v / dur for k, v in r["components_j"].items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idle-seconds", type=float, default=0.0,
                    help="measure idle power first and subtract it")
    ap.add_argument("--out", default="", help="write result JSON to this path")
    ap.add_argument("cmd", nargs=argparse.REMAINDER,
                    help="-- command to run under measurement")
    a = ap.parse_args()

    idle = measure_idle(a.idle_seconds) if a.idle_seconds > 0 else {}
    meter = EnergyMeter(idle_power_w=idle)
    cmd = a.cmd[1:] if a.cmd and a.cmd[0] == "--" else a.cmd
    with meter:
        if cmd:
            subprocess.run(cmd, check=False)
        else:
            print("no command given; measuring a 1 s idle window")
            time.sleep(1.0)
    res = meter.result()
    print(json.dumps(res, indent=2))
    if not res["components_j"]:
        print("WARNING: no RAPL/NVML domains found; energy is unavailable on "
              "this host (do not report a fabricated value).")
    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2)


if __name__ == "__main__":
    main()
