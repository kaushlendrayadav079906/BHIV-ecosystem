import json
import time
from pathlib import Path
from typing import Tuple, List
import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np
import logging
from .config import settings

logger = logging.getLogger("plant_ai.species")


class SpeciesModel:
    def __init__(self, model_path: str = None, device: str = None):
        self.model_path = model_path or str(settings.MODEL_DIR / settings.SPECIES_MODEL)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.labels = None

        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def _load_labels(self, num_classes: int):
        """Load class labels from config-specified JSON, fallback to same-name .json."""
        candidates = [
            Path(settings.MODEL_DIR / settings.SPECIES_LABELS),
            Path(self.model_path).with_suffix(".json"),
        ]
        for labels_path in candidates:
            if labels_path.exists():
                try:
                    with open(labels_path) as f:
                        data = json.load(f)
                    if isinstance(data, dict) and "class_names" in data:
                        data = data["class_names"]
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], str):
                        if len(data) != num_classes:
                            logger.warning(
                                "Labels file has %d entries but model has %d classes "
                                "— model may need retraining",
                                len(data), num_classes,
                            )
                        self.labels = data
                        logger.info("Loaded %d class labels from %s", len(self.labels), labels_path)
                        return
                    else:
                        logger.warning("Labels file %s has wrong format, expected list of strings", labels_path)
                except Exception as e:
                    logger.warning("Could not read labels file %s: %s", labels_path, e)
        logger.warning("No valid labels file found — species will be reported as class indices")

    def load(self):
        try:
            import timm
            import torch.nn as nn
            checkpoint = torch.load(self.model_path, map_location=self.device)
            arch = "vit_base_patch16_224"  # default fallback
            if isinstance(checkpoint, dict) and "architecture" in checkpoint:
                arch = checkpoint["architecture"]
            
            state_dict = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint
            if not isinstance(state_dict, dict):
                logger.warning("Unexpected checkpoint format in %s; skipping", self.model_path)
                return

            # Infer num_classes from the final linear layer weight shape
            head_key = next((k for k in state_dict if k.endswith(".weight") and "head" in k), None)
            if head_key is None:
                # fallback: last weight tensor
                head_key = [k for k in state_dict if k.endswith(".weight")][-1]
            num_classes = state_dict[head_key].shape[0]

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
            
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()
            self.model = model
            self._load_labels(num_classes)
            logger.info("Species model loaded: %d classes (%s)", num_classes, arch)
        except Exception as e:
            logger.warning("Could not load species model: %s", e)
            self.model = None

    def predict(self, image: Image.Image) -> Tuple[str, float, List[Tuple[str, float]], float]:
        """Return top species, confidence, alternatives list, and inference time (seconds)."""
        if self.model is None:
            logger.warning("Species model not loaded; returning default prediction")
            return "Unknown Species", 0.5, [{"species": "Neem", "confidence": 0.3}], 0.0

        start = time.time()
        try:
            img = image.convert("RGB")
            x = self.transform(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                out = self.model(x)
                if isinstance(out, tuple) or isinstance(out, list):
                    out = out[0]
                probs = torch.softmax(out, dim=1).cpu().numpy()[0]
        except Exception as e:
            logger.warning("Species prediction failed: %s; returning default", e)
            elapsed = time.time() - start
            return "Unknown Species", 0.5, [], elapsed

        elapsed = time.time() - start

        top_idx = int(np.argmax(probs))
        top_conf = float(probs[top_idx])
        species = str(top_idx)
        if self.labels:
            try:
                species = self.labels[top_idx]
            except Exception:
                pass

        alternatives = []
        sorted_idx = np.argsort(-probs)
        for idx in sorted_idx[1:4]:
            alt_label = str(idx)
            if self.labels:
                try:
                    alt_label = self.labels[int(idx)]
                except Exception:
                    pass
            alternatives.append({"species": alt_label, "confidence": float(probs[int(idx)])})

        return species, top_conf, alternatives, elapsed
