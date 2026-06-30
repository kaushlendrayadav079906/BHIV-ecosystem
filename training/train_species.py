import json
import torch
import timm
import torch.nn as nn
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from torch.utils.data import Subset

# ── Paths (update DATASET_DIR if different in Colab) ──────────────────────────
DATASET_DIR = "species_dataset"   # flat folder: species_dataset/Neem/*, etc.
MODEL_OUT   = "species_model.pth"
LABELS_OUT  = "species_model.json"

# ── Transforms ────────────────────────────────────────────────────────────────
train_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# ── Dataset (flat folder — no train/val split on disk) ────────────────────────
full_dataset = datasets.ImageFolder(DATASET_DIR, transform=train_transform)
num_classes  = len(full_dataset.classes)
print(f"Classes ({num_classes}): {full_dataset.classes}")

# 80/20 split
indices = list(range(len(full_dataset)))
train_idx, val_idx = train_test_split(indices, test_size=0.2,
                                       stratify=full_dataset.targets, random_state=42)

train_set = Subset(full_dataset, train_idx)
val_set   = Subset(full_dataset, val_idx)
# apply val transform to val subset
val_set.dataset = datasets.ImageFolder(DATASET_DIR, transform=val_transform)
val_set.indices = val_idx

train_loader = DataLoader(train_set, batch_size=32, shuffle=True,  num_workers=2)
val_loader   = DataLoader(val_set,   batch_size=32, shuffle=False, num_workers=2)

print(f"Train: {len(train_set)} | Val: {len(val_set)}")

# ── Model ─────────────────────────────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)

model = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=num_classes)
model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)

# ── Training ──────────────────────────────────────────────────────────────────
best_val_acc = 0.0

for epoch in range(10):
    model.train()
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        loss = criterion(model(images), labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    scheduler.step()

    # Validation
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            preds = model(images).argmax(dim=1)
            correct += (preds == labels).sum().item()
            total   += labels.size(0)
    val_acc = correct / total
    print(f"Epoch {epoch+1}/10  Loss={running_loss:.4f}  Val Acc={val_acc:.4f}")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), MODEL_OUT)
        print(f"  ✅ Best model saved (val_acc={val_acc:.4f})")

# ── Save labels JSON (MUST be uploaded with the .pth file) ────────────────────
with open(LABELS_OUT, "w") as f:
    json.dump(full_dataset.classes, f, indent=2)

print(f"\nDone! Upload both files to weights/")
print(f"  → {MODEL_OUT}")
print(f"  → {LABELS_OUT}  (classes: {full_dataset.classes})")