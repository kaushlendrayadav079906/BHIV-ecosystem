"""
Model Accuracy Evaluation — All 3 Models
Run from project root: python evaluate_models.py
"""
import json
import time
import random
from pathlib import Path
import numpy as np

WEIGHTS   = Path("weights")
DATASETS  = Path("app/datasets")
SPECIES_DIR  = DATASETS / "species_dataset"
GROWTH_DIR   = DATASETS / "Growth"
PART_DIR     = DATASETS / "Plant Part Detection"

print("=" * 65)
print("  PLANT INTELLIGENCE — MODEL ACCURACY EVALUATION")
print("=" * 65)

# ── COMMON IMPORTS ──────────────────────────────────────────────
import torch
import torchvision.transforms as T
from PIL import Image

# ── MODEL 1: SPECIES ────────────────────────────────────────────
print("\n[MODEL 1] Species Classification (ViT)")
print("─" * 65)

try:
    import timm

    # Load labels
    with open(WEIGHTS / "species_classes.json") as f:
        data = json.load(f)
    if isinstance(data, dict) and "class_names" in data:
        labels = data["class_names"]
    else:
        labels = data
    print(f"  Classes : {len(labels)}")

    # Load model
    checkpoint = torch.load(WEIGHTS / "species_model.pth", map_location="cpu", weights_only=True)
    arch = "vit_base_patch16_224"
    if isinstance(checkpoint, dict) and "architecture" in checkpoint:
        arch = checkpoint["architecture"]
    sd = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint
    
    head_key = next((k for k in sd if k.endswith(".weight") and "head" in k), None)
    if head_key is None:
        head_key = [k for k in sd if k.endswith(".weight")][-1]
    num_classes = sd[head_key].shape[0]
    
    import torch.nn as nn
    if "resnet" in arch.lower():
        model = timm.create_model(arch, pretrained=False, num_classes=num_classes)
        model.fc = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(2048, 512),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(512),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
    else:
        model = timm.create_model(arch, pretrained=False, num_classes=num_classes)
        
    model.load_state_dict(sd)
    model.eval()
    print(f"  Model   : {arch}, {num_classes} classes")

    transform = T.Compose([
        T.Resize((224, 224)),
        T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    # Sample images from dataset — max 5 per class, max 100 total
    class_dirs = sorted([d for d in SPECIES_DIR.iterdir() if d.is_dir()])
    samples = []
    for cls_dir in class_dirs:
        cls_name = cls_dir.name
        if cls_name not in labels:
            continue
        cls_idx  = labels.index(cls_name)
        imgs     = list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.png")) + list(cls_dir.glob("*.jpeg"))
        chosen   = random.sample(imgs, min(5, len(imgs)))
        for img_path in chosen:
            samples.append((img_path, cls_idx, cls_name))

    random.shuffle(samples)
    samples = samples[:100]

    correct = top3_correct = total = 0
    conf_sum = 0.0
    wrong_list = []

    for img_path, true_idx, true_name in samples:
        try:
            img  = Image.open(img_path).convert("RGB")
            x    = transform(img).unsqueeze(0)
            with torch.no_grad():
                probs = torch.softmax(model(x), dim=1).numpy()[0]
            top1 = int(np.argmax(probs))
            top3 = np.argsort(-probs)[:3].tolist()
            conf = float(probs[top1])
            conf_sum += conf
            total    += 1
            if top1 == true_idx:
                correct += 1
            if true_idx in top3:
                top3_correct += 1
            else:
                pred_name = labels[top1] if top1 < len(labels) else str(top1)
                wrong_list.append(f"    True={true_name} → Pred={pred_name} ({conf*100:.1f}%)")
        except Exception:
            pass

    if total > 0:
        top1_acc  = correct / total * 100
        top3_acc  = top3_correct / total * 100
        avg_conf  = conf_sum / total * 100
        print(f"\n  Evaluated : {total} images")
        print(f"  Top-1 Acc : {top1_acc:.1f}%  {'✅ GOOD' if top1_acc >= 80 else '⚠️  NEEDS IMPROVEMENT' if top1_acc >= 60 else '❌ POOR'}")
        print(f"  Top-3 Acc : {top3_acc:.1f}%")
        print(f"  Avg Conf  : {avg_conf:.1f}%")
        if wrong_list:
            print(f"\n  Sample misclassifications (first 5):")
            for w in wrong_list[:5]:
                print(w)
    else:
        print("  ❌ No images found to evaluate")

except Exception as e:
    print(f"  ❌ Species evaluation failed: {e}")

# ── MODEL 2: GROWTH STAGE ───────────────────────────────────────
print("\n\n[MODEL 2] Growth Stage Detection (YOLO)")
print("─" * 65)

try:
    from ultralytics import YOLO

    growth_model = YOLO(str(WEIGHTS / "growth_stage.pt"))
    names = growth_model.names
    print(f"  Classes : {list(names.values())}")

    val_img_dir = GROWTH_DIR / "valid" / "images"
    val_lbl_dir = GROWTH_DIR / "valid" / "labels"

    if not val_img_dir.exists():
        print(f"  ⚠️  Validation images not found at {val_img_dir}")
    else:
        img_files = list(val_img_dir.glob("*.jpg")) + list(val_img_dir.glob("*.png"))
        img_files = random.sample(img_files, min(80, len(img_files)))
        print(f"  Evaluating {len(img_files)} validation images...")

        correct = total = no_pred = 0

        for img_path in img_files:
            lbl_path = val_lbl_dir / (img_path.stem + ".txt")
            if not lbl_path.exists():
                continue
            try:
                with open(lbl_path) as f:
                    lines = [l.strip() for l in f if l.strip()]
                if not lines:
                    continue
                true_cls = int(lines[0].split()[0])

                img_np = np.array(Image.open(img_path).convert("RGB"))
                results = growth_model.predict(img_np, verbose=False)
                r = results[0]

                pred_cls = None
                if hasattr(r, "probs") and r.probs is not None:
                    pred_cls = int(r.probs.data.cpu().numpy().argmax())
                elif hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
                    top_box  = max(r.boxes, key=lambda b: float(b.conf.cpu().numpy()[0]))
                    pred_cls = int(top_box.cls.cpu().numpy()[0])

                if pred_cls is None:
                    no_pred += 1
                    continue

                total += 1
                if pred_cls == true_cls:
                    correct += 1
            except Exception:
                pass

        if total > 0:
            acc = correct / total * 100
            print(f"  Evaluated : {total} images ({no_pred} skipped — no detections)")
            print(f"  Accuracy  : {acc:.1f}%  {'✅ GOOD' if acc >= 70 else '⚠️  NEEDS IMPROVEMENT' if acc >= 50 else '❌ POOR'}")
        else:
            print("  ❌ No valid label+image pairs found")

except Exception as e:
    print(f"  ❌ Growth evaluation failed: {e}")

# ── MODEL 3: PLANT PART DETECTION ───────────────────────────────
print("\n\n[MODEL 3] Plant Part Detection (YOLO)")
print("─" * 65)

try:
    from ultralytics import YOLO

    part_model  = YOLO(str(WEIGHTS / "Plant part.pt"))
    names       = part_model.names
    print(f"  Classes : {list(names.values())}")

    val_img_dir = PART_DIR / "valid" / "images"
    val_lbl_dir = PART_DIR / "valid" / "labels"

    if not val_img_dir.exists():
        print(f"  ⚠️  Validation images not found at {val_img_dir}")
    else:
        img_files = list(val_img_dir.glob("*.jpg")) + list(val_img_dir.glob("*.png"))
        img_files = random.sample(img_files, min(80, len(img_files)))
        print(f"  Evaluating {len(img_files)} validation images...")

        tp = fp = fn = 0
        iou_scores = []

        for img_path in img_files:
            lbl_path = val_lbl_dir / (img_path.stem + ".txt")
            if not lbl_path.exists():
                continue
            try:
                with open(lbl_path) as f:
                    lines = [l.strip().split() for l in f if l.strip()]
                if not lines:
                    continue
                true_classes = set(int(l[0]) for l in lines)

                img_np  = np.array(Image.open(img_path).convert("RGB"))
                results = part_model.predict(img_np, verbose=False)
                r = results[0]

                if hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
                    pred_classes = set(int(b.cls.cpu().numpy()[0]) for b in r.boxes)
                    matched = true_classes & pred_classes
                    tp += len(matched)
                    fp += len(pred_classes - true_classes)
                    fn += len(true_classes - pred_classes)
                else:
                    fn += len(true_classes)

            except Exception:
                pass

        total_pred = tp + fp
        total_true = tp + fn
        precision  = tp / total_pred * 100 if total_pred > 0 else 0
        recall     = tp / total_true * 100 if total_true > 0 else 0
        f1         = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        print(f"  Evaluated : {len(img_files)} images")
        print(f"  Precision : {precision:.1f}%")
        print(f"  Recall    : {recall:.1f}%")
        print(f"  F1 Score  : {f1:.1f}%  {'✅ GOOD' if f1 >= 60 else '⚠️  NEEDS IMPROVEMENT' if f1 >= 40 else '❌ POOR'}")

except Exception as e:
    print(f"  ❌ Part evaluation failed: {e}")

# ── SUMMARY ─────────────────────────────────────────────────────
print("\n\n" + "=" * 65)
print("  ACCURACY SUMMARY")
print("=" * 65)
print("  Model 1 — Species (ViT-Base/16)  : Top-1 Accuracy")
print("  Model 2 — Growth Stage (YOLO)    : Classification Accuracy")
print("  Model 3 — Plant Part (YOLO)      : Precision / Recall / F1")
print("\n  Rating Scale:")
print("    ✅ GOOD               ≥ 80% (Species) / ≥ 70% (Growth) / ≥ 60% F1 (Part)")
print("    ⚠️  NEEDS IMPROVEMENT  ≥ 60% (Species) / ≥ 50% (Growth) / ≥ 40% F1 (Part)")
print("    ❌ POOR               Below above thresholds — retrain recommended")
print("=" * 65)
