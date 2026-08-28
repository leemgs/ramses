import os, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from mvtec_vit import scan_split, reference_mean, euclidean, percentile


class TestMvtec(unittest.TestCase):
    def test_scan_split_labels(self):
        with tempfile.TemporaryDirectory() as root:
            cat = "bottle"
            for defect, fns in (("good", ["000.png", "001.png"]),
                                ("broken", ["000.png"])):
                d = os.path.join(root, cat, "test", defect)
                os.makedirs(d)
                for fn in fns:
                    open(os.path.join(d, fn), "w").close()
            items = scan_split(root, cat, "test")
            self.assertEqual(len(items), 3)
            labels = {os.path.basename(os.path.dirname(p)): lab
                      for _id, p, lab in items}
            self.assertEqual(labels["good"], 0)
            self.assertEqual(labels["broken"], 1)

    def test_scoring_math(self):
        embs = [[0.0, 0.0], [2.0, 0.0], [0.0, 2.0]]
        ref = reference_mean(embs)
        self.assertAlmostEqual(ref[0], 2 / 3)
        self.assertAlmostEqual(ref[1], 2 / 3)
        self.assertAlmostEqual(euclidean([3.0, 4.0], [0.0, 0.0]), 5.0)
        self.assertAlmostEqual(percentile([1, 2, 3, 4, 5], 50), 3.0)


if __name__ == "__main__":
    unittest.main()
