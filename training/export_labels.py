"""
Run once after training to save class labels alongside the model weights.
Usage: python training/export_labels.py
"""
import json
from pathlib import Path

# species_dataset has class folders directly (no train/ subfolder)
TRAIN_DIR = Path("app/datasets/species_dataset")
OUTPUT = Path("weights/species_model.json")

# Collect only directory names (skip README.md etc), sorted alphabetically
# This matches torchvision ImageFolder ordering used during training
labels = sorted([d.name for d in TRAIN_DIR.iterdir() if d.is_dir()])

OUTPUT.parent.mkdir(exist_ok=True)
with open(OUTPUT, "w") as f:
    json.dump(labels, f, indent=2)

print(f"Saved {len(labels)} class labels to {OUTPUT}")
print("Classes:", labels)
