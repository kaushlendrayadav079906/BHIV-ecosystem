"""
Species Model Audit Script
Run from project root: python audit_species_model.py
"""
import json
import sys
import time
from pathlib import Path

WEIGHTS_DIR  = Path("weights")
MODEL_PATH   = WEIGHTS_DIR / "species_model.pth"
LABELS_PATH  = WEIGHTS_DIR / "species_classes.json"
TEST_IMAGE   = Path("test_leaf.jpg")
MODEL_ARCH   = "vit_base_patch16_224"
EXPECTED_CLS = 40

results = {}

def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results[name] = status
    mark = "✅" if passed else "❌"
    print(f"  {mark} [{status}] {name}")
    if detail:
        print(f"         → {detail}")

print("=" * 65)
print("  PLANT INTELLIGENCE — SPECIES MODEL AUDIT")
print("=" * 65)

# ── CHECK 1: Files exist ────────────────────────────────────────
print("\n[1] File presence")
check("species_model.pth exists", MODEL_PATH.exists(),
      str(MODEL_PATH) if MODEL_PATH.exists() else f"Missing at {MODEL_PATH}")
check("species_classes.json exists", LABELS_PATH.exists(),
      str(LABELS_PATH) if LABELS_PATH.exists() else f"Missing at {LABELS_PATH}")

if not MODEL_PATH.exists():
    print("\n❌ Cannot continue — species_model.pth missing.")
    sys.exit(1)

# ── CHECK 2: Labels JSON ────────────────────────────────────────
print("\n[2] Labels JSON content")
labels = None
if LABELS_PATH.exists():
    with open(LABELS_PATH) as f:
        data = json.load(f)
    if isinstance(data, dict) and "class_names" in data:
        labels = data["class_names"]
    else:
        labels = data
    check("Labels is a list", isinstance(labels, list),
          f"type={type(labels).__name__}")
    check("Labels has 40 entries", len(labels) == EXPECTED_CLS,
          f"found {len(labels)} entries")
    check("All entries are strings", all(isinstance(l, str) for l in labels),
          f"first 5: {labels[:5] if isinstance(labels, list) else None}")
    check("No folder-name contamination",
          isinstance(labels, list) and labels != ["species_dataset"] and "species_dataset" not in labels,
          f"first={labels[0] if isinstance(labels, list) and labels else None}, last={labels[-1] if isinstance(labels, list) and labels else None}")
else:
    check("Labels JSON readable", False, "File missing")

# ── CHECK 3: Load state_dict ────────────────────────────────────
print("\n[3] Model file format")
checkpoint = None
num_classes = 0
try:
    import torch
    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
    is_dict = isinstance(checkpoint, dict)
    check("Saved as state_dict (dict)", is_dict,
          f"type={type(checkpoint).__name__}")

    if is_dict:
        if "model_state_dict" in checkpoint:
            sd = checkpoint["model_state_dict"]
            check("Checkpoint contains model_state_dict", True, f"keys: {list(checkpoint.keys())}")
        else:
            sd = checkpoint
            check("Checkpoint contains model_state_dict", False, "Loading raw checkpoint as state_dict")

        all_tensors = all(isinstance(v, torch.Tensor) for v in sd.values())
        check("All state_dict values are tensors", all_tensors,
              f"keys sample: {list(sd.keys())[:3]}")

        head_key = next((k for k in sd if k.endswith(".weight") and "head" in k), None)
        if head_key is None:
            head_key = [k for k in sd if k.endswith(".weight")][-1]
        num_classes = sd[head_key].shape[0]
        check("Model output = 40 classes", num_classes == EXPECTED_CLS,
              f"head key='{head_key}', shape={sd[head_key].shape}, num_classes={num_classes}")
    else:
        check("Model output = 40 classes", False, "Cannot inspect — not a state_dict")

except Exception as e:
    check("State dict loadable", False, str(e))

# ── CHECK 4: Labels match model ─────────────────────────────────
print("\n[4] Labels vs Model alignment")
if labels is not None and num_classes > 0:
    check("Label count matches model output",
          len(labels) == num_classes,
          f"labels={len(labels)}, model={num_classes}")
else:
    check("Label count matches model output", False,
          "Cannot check — labels or model failed to load")

# ── CHECK 5: timm architecture loads ───────────────────────────
print("\n[5] timm model reconstruction")
model = None
try:
    import timm
    check("timm importable", True, f"timm version={timm.__version__}")
    if checkpoint is not None and num_classes > 0:
        try:
            model = timm.create_model(MODEL_ARCH, pretrained=False, num_classes=num_classes)
            sd = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint
            model.load_state_dict(sd)
            model.eval()
            check("ViT model loads with state_dict", True,
                  f"arch={MODEL_ARCH}, classes={num_classes}")
        except Exception as e:
            check("ViT model loads with state_dict", False, str(e))
            model = None
    else:
        check("ViT model loads with state_dict", False,
              "Skipped — checkpoint or num_classes unavailable")
except ImportError:
    check("timm importable", False, "Run: pip install timm")

# ── CHECK 6: Single image prediction ───────────────────────────
print("\n[6] Image prediction test")
if model is not None and TEST_IMAGE.exists():
    try:
        import torchvision.transforms as T
        import numpy as np
        from PIL import Image

        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        img = Image.open(TEST_IMAGE).convert("RGB")
        x = transform(img).unsqueeze(0)

        t0 = time.time()
        with torch.no_grad():
            probs = torch.softmax(model(x), dim=1).numpy()[0]
        elapsed_ms = (time.time() - t0) * 1000

        top_idx  = int(np.argmax(probs))
        top_conf = float(probs[top_idx])
        top_name = labels[top_idx] if labels and top_idx < len(labels) else str(top_idx)

        alts = sorted(enumerate(probs), key=lambda kv: -kv[1])[1:4]
        alt_str = ", ".join(
            f"{labels[i] if labels and i < len(labels) else i} ({p*100:.1f}%)"
            for i, p in alts
        )

        check("Prediction runs without error", True, f"inference={elapsed_ms:.0f}ms")
        check("Confidence is a valid probability",
              0.0 <= top_conf <= 1.0, f"conf={top_conf:.4f}")
        check("Top prediction is a known label",
              labels is not None and top_idx < len(labels),
              f"predicted='{top_name}' ({top_conf*100:.1f}%)")

        print(f"\n  📊 Prediction Result:")
        print(f"     Species     : {top_name}")
        print(f"     Confidence  : {top_conf*100:.1f}%")
        print(f"     Alternatives: {alt_str}")
        print(f"     Inference   : {elapsed_ms:.0f} ms")

        if top_conf < 0.70:
            print(f"  ⚠️  Confidence {top_conf*100:.1f}% is BELOW 70% threshold")
            print(f"     → API will return 'Unknown Plant' — model may need more training")
        else:
            print(f"  ✅  Confidence above 70% threshold — API will return full result")

    except Exception as e:
        check("Prediction runs without error", False, str(e))

elif not TEST_IMAGE.exists():
    print(f"  ⚠️  [SKIP] test_leaf.jpg not found — place any plant image as test_leaf.jpg")
else:
    print(f"  ⚠️  [SKIP] Model not loaded — cannot run prediction")

# ── CHECK 7: FastAPI deployment readiness ──────────────────────
print("\n[7] FastAPI deployment readiness")
config_path = Path("app/config.py")
init_path   = Path("app/__init__.py")
config_text = config_path.read_text() if config_path.exists() else ""

check("app/__init__.py exists",    init_path.exists())
check("app/config.py exists",      config_path.exists())
check("SPECIES_LABELS in config",  "SPECIES_LABELS" in config_text)
check("species_classes.json in config",
      "species_classes.json" in config_text)

# ── SUMMARY ────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  AUDIT SUMMARY")
print("=" * 65)
passed = sum(1 for v in results.values() if v == "PASS")
failed = sum(1 for v in results.values() if v == "FAIL")
print(f"  PASSED : {passed}")
print(f"  FAILED : {failed}")
print(f"  TOTAL  : {len(results)}")

if failed == 0:
    print("\n  ✅ ALL CHECKS PASSED — Model is ready for FastAPI deployment")
else:
    print("\n  ❌ ISSUES FOUND:")
    for name, status in results.items():
        if status == "FAIL":
            print(f"     • {name}")

print("=" * 65)
