import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from eval_industrial import accuracy, auroc, output_equivalence


class TestMetrics(unittest.TestCase):
    def test_accuracy(self):
        self.assertEqual(accuracy([1, 0, 1, 1], [1, 0, 0, 1]), 0.75)
        self.assertIsNone(accuracy([], []))

    def test_auroc_perfect_and_tie(self):
        # perfectly separable -> 1.0
        self.assertAlmostEqual(auroc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]), 1.0)
        # inverted -> 0.0
        self.assertAlmostEqual(auroc([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]), 0.0)
        # all-ties -> 0.5
        self.assertAlmostEqual(auroc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]), 0.5)
        # single class -> None
        self.assertIsNone(auroc([1, 1, 1], [0.1, 0.2, 0.3]))

    def test_output_equivalence(self):
        base = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(output_equivalence(base, base, "fp32"), 1.0)
        # fp32 exact: any diff fails
        self.assertEqual(output_equivalence(base, [[1.0, 2.0], [3.0, 4.001]], "fp32"), 0.5)
        # fp16 tolerance: small relative diff passes
        self.assertEqual(output_equivalence(base, [[1.0, 2.0], [3.0, 4.01]], "fp16"), 1.0)


if __name__ == "__main__":
    unittest.main()
