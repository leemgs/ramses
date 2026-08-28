#!/usr/bin/env python3
"""MVTec AD + ViT backend for eval_industrial.py (Reviewer R3-8).

Provides the two hooks eval_industrial expects:
  * load_dataset(name, data_root) -> [(item_id, image_path, label), ...]
  * run_model(items, model, precision, serving_mode) -> (scores, preds, outputs, latencies)

Anomaly detection follows a simple, reproducible deep-feature-distance protocol
(cf. SPADE): a pretrained ViT embeds each image; a reference mean is fit on the
'train/good' images; the anomaly score is the Euclidean distance of a test
embedding to that mean. AUROC (threshold-free, the standard MVTec AD metric) is
the primary number; a 95th-percentile threshold on train-good distances yields
a hard label for accuracy. `outputs` returns the raw embeddings so that
baseline-vs-RAMSES output equivalence can be checked.

Dataset scanning and scoring are pure Python (unit tested). The ViT embedder is
a guarded import of timm/torch used only when embeddings are computed.
"""
import os, time, math

_STATE = {"root": None, "category": os.environ.get("MVTEC_CATEGORY", "bottle")}


# --------------------------------------------------------------------------
# Dataset scanning (pure, testable)
# --------------------------------------------------------------------------
def scan_split(root, category, split):
    """Return [(item_id, path, label)] for a MVTec AD split.

    Layout: <root>/<category>/<split>/<defect_type>/<img>. Label 0 for
    defect_type == 'good', else 1.
    """
    base = os.path.join(root, category, split)
    items = []
    if not os.path.isdir(base):
        return items
    for defect in sorted(os.listdir(base)):
        d = os.path.join(base, defect)
        if not os.path.isdir(d):
            continue
        label = 0 if defect == "good" else 1
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                item_id = f"{category}/{split}/{defect}/{fn}"
                items.append((item_id, os.path.join(d, fn), label))
    return items


def load_dataset(name, data_root):
    _STATE["root"] = data_root
    cat = _STATE["category"]
    items = scan_split(data_root, cat, "test")
    if not items:
        raise FileNotFoundError(
            f"No MVTec AD test images under {data_root}/{cat}/test. "
            "Set MVTEC_CATEGORY and check the dataset layout.")
    return items


# --------------------------------------------------------------------------
# Scoring (pure, testable)
# --------------------------------------------------------------------------
def reference_mean(embeddings):
    n = len(embeddings)
    dim = len(embeddings[0])
    return [sum(e[i] for e in embeddings) / n for i in range(dim)]


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def percentile(xs, p):
    ys = sorted(xs)
    if not ys:
        return 0.0
    k = (len(ys) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return ys[lo] if lo == hi else ys[lo] * (hi - k) + ys[hi] * (k - lo)


# --------------------------------------------------------------------------
# ViT embedder (guarded import)
# --------------------------------------------------------------------------
class Embedder:
    def __init__(self, model_name, precision):
        try:
            import torch, timm
            from timm.data import resolve_data_config, create_transform
            from PIL import Image
        except ImportError as e:
            raise SystemExit(f"mvtec_vit requires torch, timm, pillow: {e}")
        self.torch, self.Image = torch, Image
        name = {"vit-h14": "vit_huge_patch14_clip_224"}.get(model_name, model_name)
        self.model = timm.create_model(name, pretrained=True, num_classes=0)
        self.model.eval()
        self.dtype = torch.float16 if precision.lower() in ("fp16", "float16") else torch.float32
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device, self.dtype if self.device == "cuda" else torch.float32)
        cfg = resolve_data_config({}, model=self.model)
        self.tf = create_transform(**cfg)

    def embed(self, path):
        img = self.Image.open(path).convert("RGB")
        x = self.tf(img).unsqueeze(0).to(self.device)
        if self.device == "cuda":
            x = x.to(self.dtype)
        with self.torch.no_grad():
            feat = self.model(x)
        return feat.float().cpu().flatten().tolist()


# --------------------------------------------------------------------------
# run_model hook
# --------------------------------------------------------------------------
def run_model(items, model, precision, serving_mode):
    root, cat = _STATE["root"], _STATE["category"]
    embedder = Embedder(model, precision)

    # Fit reference on train/good.
    train_good = scan_split(root, cat, "train")
    train_good = [it for it in train_good if it[2] == 0]
    if not train_good:
        raise FileNotFoundError(f"No train/good images under {root}/{cat}/train/good")
    ref_embs = [embedder.embed(p) for _id, p, _l in train_good]
    ref = reference_mean(ref_embs)
    thr = percentile([euclidean(e, ref) for e in ref_embs], 95)

    scores, preds, outputs, latencies = [], [], [], []
    for _id, path, _label in items:
        t0 = time.perf_counter()
        emb = embedder.embed(path)
        latencies.append((time.perf_counter() - t0) * 1e3)
        d = euclidean(emb, ref)
        scores.append(d)
        preds.append(1 if d > thr else 0)
        outputs.append(emb)  # raw embedding for output-equivalence check
    return scores, preds, outputs, latencies
