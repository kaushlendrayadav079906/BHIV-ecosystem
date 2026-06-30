import os
import shutil
import random

SOURCE = "datasets/species_dataset"
TRAIN = "datasets/train"
VAL = "datasets/val"

os.makedirs(TRAIN, exist_ok=True)
os.makedirs(VAL, exist_ok=True)

for cls in os.listdir(SOURCE):

    cls_path = os.path.join(SOURCE, cls)

    if not os.path.isdir(cls_path):
        continue

    images = os.listdir(cls_path)

    random.shuffle(images)

    split = int(len(images) * 0.8)

    train_imgs = images[:split]
    val_imgs = images[split:]

    os.makedirs(os.path.join(TRAIN, cls), exist_ok=True)
    os.makedirs(os.path.join(VAL, cls), exist_ok=True)

    for img in train_imgs:
        shutil.copy(
            os.path.join(cls_path, img),
            os.path.join(TRAIN, cls, img)
        )

    for img in val_imgs:
        shutil.copy(
            os.path.join(cls_path, img),
            os.path.join(VAL, cls, img)
        )

print("Dataset Split Complete")