import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from collect_energy import integrate, EnergyMeter


class FakeRapl:
    def __init__(self, seq):
        self._seq = list(seq)
        self.domains = {"package-0": ("x", 1000000), "dram": ("y", 1000000)}

    def read(self):
        return self._seq.pop(0)


class FakeNvml:
    def __init__(self, vals):
        self.ok = True
        self._vals = list(vals)

    def total_energy_j(self):
        return self._vals.pop(0)


class TestEnergy(unittest.TestCase):
    def test_integrate_plain(self):
        self.assertAlmostEqual(integrate(1_000_000, 3_000_000, 0), 2.0)

    def test_integrate_wrap(self):
        # counter wraps once at 1e6 uJ: 900000 -> 100000 == 200000 uJ = 0.2 J
        self.assertAlmostEqual(integrate(900_000, 100_000, 1_000_000), 0.2)

    def test_meter_aggregates_and_subtracts_idle(self):
        rapl = FakeRapl([
            {"package-0": (0, 1_000_000), "dram": (0, 1_000_000)},
            {"package-0": (2_000_000, 1_000_000), "dram": (500_000, 1_000_000)},
        ])
        nvml = FakeNvml([10.0, 25.0])  # 15 J on GPU
        m = EnergyMeter(rapl=rapl, nvml=nvml)
        with m:
            pass
        r = m.result()
        self.assertAlmostEqual(r["components_j"]["package-0"], 2.0)
        self.assertAlmostEqual(r["components_j"]["dram"], 0.5)
        self.assertAlmostEqual(r["components_j"]["gpu"], 15.0)
        self.assertAlmostEqual(r["node_energy_j"], 17.5)
        self.assertTrue(r["nvml_available"])


if __name__ == "__main__":
    unittest.main()
