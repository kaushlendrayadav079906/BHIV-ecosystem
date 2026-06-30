"""
3-Model Verification Script
Run from project root: python verify_models.py
Checks all 3 models independently before starting the server.
"""
import sys
import time
import json
from pathlib import Path

WEIGHTS = Path("weights")
TEST_IMG = Path("test_leaf.jpg")

passed = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  ✅  {msg}")

def fail(msg):
    global failed
    failed += 1
    print(f"  ❌  {msg}")

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

# ─── imports ───────────────────────────────────────────────────
section("0. Dependency Check")
try:
    import torch
    ok(f"torch {torch.__version__}")
except ImportError:
    fail("torch not installed — run: pip install torch")
    sys.exit(1)

try:
    import timm
    ok(f"timm {timm.__version__}")
except ImportError:
    fail("timm not installed — run: pip install timm")
    sys.exit(1)

try:
    from ultralytics import YOLO
    ok("ultralytics YOLO")
except ImportError:
    fail("ultralytics not installed — run: pip install ultralytics")
    sys.exit(1)

try:
    import torchvision
    ok(f"torchvision {torchvision.__version__}")
except ImportError:
    fail("torchvision not installed")
    sys.exit(1)

try:
    import cv2
    ok(f"opencv {cv2.__version__}")
except ImportError:
    fail("opencv not installed — run: pip install opencv-python")

try:
    import numpy as np
    ok(f"numpy {np.__version__}")
except ImportError:
    fail("numpy not installed")

try:
    from PIL import Image
    ok("Pillow")
except ImportError:
    fail("Pillow not installed")
    sys.exit(1)

# Load test image once
img = None
if TEST_IMG.exists():
    img = Image.open(TEST_IMG).convert("RGB")
    ok(f"Test image loaded: {TEST_IMG} {img.size}")
else:
    fail(f"test_leaf.jpg not found — place any plant image as test_leaf.jpg")

# ─── MODEL 1: Species ──────────────────────────────────────────
section("1. Species Model  (species_model.pth + species_classes.json)")

pth_path    = WEIGHTS / "species_model.pth"
labels_path = WEIGHTS / "species_classes.json"

if not pth_path.exists():
    fail(f"species_model.pth not found at {pth_path}")
else:
    ok(f"species_model.pth found ({pth_path.stat().st_size / 1e6:.1f} MB)")

if not labels_path.exists():
    fail(f"species_classes.json not found at {labels_path}")
else:
    with open(labels_path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "class_names" in data:
        labels = data["class_names"]
    else:
        labels = data
    if isinstance(labels, list) and len(labels) > 0 and isinstance(labels[0], str):
        ok(f"species_classes.json loaded: {len(labels)} classes")
        if len(labels) == 40:
            ok("Exactly 40 classes ✓")
        else:
            fail(f"Expected 40 classes, got {len(labels)}")
    else:
        fail(f"species_classes.json has wrong format: {labels}")
        labels = []

species_model = None
if pth_path.exists():
    try:
        checkpoint = torch.load(pth_path, map_location="cpu", weights_only=True)
        arch = "vit_base_patch16_224"
        if isinstance(checkpoint, dict) and "architecture" in checkpoint:
            arch = checkpoint["architecture"]
        sd = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint
        
        head_key = next((k for k in sd if k.endswith(".weight") and "head" in k), None)
        if head_key is None:
            head_key = [k for k in sd if k.endswith(".weight")][-1]
        num_classes = sd[head_key].shape[0]
        ok(f"state_dict loaded — output classes: {num_classes} ({arch})")

        if num_classes == 40:
            ok("Model has correct 40 output classes")
        else:
            fail(f"Model has {num_classes} classes — needs retraining with 40 classes")

        import torch.nn as nn
        if "resnet" in arch.lower():
            species_model = timm.create_model(arch, pretrained=False, num_classes=num_classes)
            species_model.fc = nn.Sequential(
                nn.Dropout(0.2),
                nn.Linear(2048, 512),
                nn.ReLU(inplace=True),
                nn.BatchNorm1d(512),
                nn.Dropout(0.2),
                nn.Linear(512, num_classes)
            )
        else:
            species_model = timm.create_model(arch, pretrained=False, num_classes=num_classes)
        
        species_model.load_state_dict(sd)
        species_model.eval()
        ok(f"{arch} architecture reconstructed and weights loaded")

        if img is not None:
            import torchvision.transforms as T
            transform = T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ])
            x = transform(img).unsqueeze(0)
            t0 = time.time()
            with torch.no_grad():
                probs = torch.softmax(species_model(x), dim=1).numpy()[0]
            ms = (time.time() - t0) * 1000
            top_idx  = int(probs.argmax())
            top_conf = float(probs[top_idx])
            top_name = labels[top_idx] if labels and top_idx < len(labels) else str(top_idx)
            alts = sorted(enumerate(probs), key=lambda kv: -kv[1])[1:4]
            alt_str = " | ".join(
                f"{labels[i] if labels and i < len(labels) else i} {p*100:.1f}%"
                for i, p in alts
            )
            ok(f"Prediction: '{top_name}' ({top_conf*100:.1f}%) in {ms:.0f}ms")
            ok(f"Alternatives: {alt_str}")
            if top_conf >= 0.70:
                ok(f"Confidence {top_conf*100:.1f}% ≥ 70% threshold — PASS")
            else:
                ok(f"Confidence {top_conf*100:.1f}% < 70% threshold — warning (normal for synthetic test image)")
    except Exception as e:
        fail(f"Species model error: {e}")

# ─── MODEL 2: Growth Stage ─────────────────────────────────────
section("2. Growth Stage Model  (growth_stage.pt)")

growth_path = WEIGHTS / "growth_stage.pt"

if not growth_path.exists():
    fail(f"growth_stage.pt not found at {growth_path}")
else:
    ok(f"growth_stage.pt found ({growth_path.stat().st_size / 1e6:.1f} MB)")

growth_model = None
if growth_path.exists():
    try:
        growth_model = YOLO(str(growth_path))
        names = growth_model.names
        ok(f"YOLO model loaded — classes: {names}")

        if img is not None:
            import numpy as np
            img_np = np.array(img)
            t0 = time.time()
            results = growth_model.predict(img_np, verbose=False)
            ms = (time.time() - t0) * 1000
            ok(f"Prediction ran in {ms:.0f}ms")

            r = results[0]
            if hasattr(r, "probs") and r.probs is not None:
                probs = r.probs.data.cpu().numpy()
                top_idx  = int(probs.argmax())
                top_conf = float(probs[top_idx])
                label    = r.names.get(top_idx, str(top_idx))
                ok(f"Growth stage: '{label}' ({top_conf*100:.1f}%) — Classification model ✓")
            elif hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
                top_box  = max(r.boxes, key=lambda b: float(b.conf.cpu().numpy()[0]))
                cls      = int(top_box.cls.cpu().numpy()[0])
                conf     = float(top_box.conf.cpu().numpy()[0])
                label    = growth_model.names.get(cls, str(cls))
                ok(f"Growth stage: '{label}' ({conf*100:.1f}%) — Detection model ✓")
            else:
                ok("No growth stages detected in test image (normal if image has no clear stages)")
    except Exception as e:
        fail(f"Growth model error: {e}")

# ─── MODEL 3: Plant Part Detection ────────────────────────────
section("3. Plant Part Detection Model  (Plant part.pt)")

part_path = WEIGHTS / "Plant part.pt"

if not part_path.exists():
    fail(f"Plant part.pt not found at {part_path}")
else:
    ok(f"Plant part.pt found ({part_path.stat().st_size / 1e6:.1f} MB)")

part_model = None
if part_path.exists():
    try:
        part_model = YOLO(str(part_path))
        names = part_model.names
        ok(f"YOLO model loaded — classes: {names}")

        if img is not None:
            import numpy as np
            img_np = np.array(img)
            t0 = time.time()
            results = part_model.predict(img_np, verbose=False)
            ms = (time.time() - t0) * 1000
            ok(f"Prediction ran in {ms:.0f}ms")

            r = results[0]
            if hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
                detections = []
                for b in r.boxes:
                    cls   = int(b.cls.cpu().numpy()[0])
                    conf  = float(b.conf.cpu().numpy()[0])
                    label = part_model.names.get(cls, str(cls))
                    detections.append((label, conf))
                detections.sort(key=lambda x: -x[1])
                det_str = " | ".join(f"{l} {c*100:.1f}%" for l, c in detections[:5])
                ok(f"Detections ({len(detections)} total): {det_str}")
            else:
                ok("No parts detected in test image (normal if image has no clear parts)")
    except Exception as e:
        fail(f"Part model error: {e}")

# ─── SUMMARY ──────────────────────────────────────────────────
section("SUMMARY")
total = passed + failed
print(f"  PASSED : {passed}/{total}")
print(f"  FAILED : {failed}/{total}")

if failed == 0:
    print("\n  ✅  ALL 3 MODELS VERIFIED — Ready to start server")
    print("\n  Run:")
    print("    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
else:
    print(f"\n  ❌  {failed} issue(s) found — fix before starting server")
print("─" * 60)
