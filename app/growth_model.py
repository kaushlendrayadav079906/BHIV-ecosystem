import time
from typing import Tuple
import numpy as np
import logging
from PIL import Image
from .config import settings

logger = logging.getLogger("plant_ai.growth")

# From app/datasets/Growth/data.yaml: names: ['Flowering', 'Germination', 'Harvesting', 'Vegetative']
_FALLBACK_LABELS = ["Flowering", "Germination", "Harvesting", "Vegetative"]


class GrowthModel:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or str(settings.MODEL_DIR / settings.GROWTH_MODEL)
        self.model = None

    def load(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            logger.info("Loaded growth model from %s", self.model_path)
        except Exception as e:
            logger.warning("Could not load growth model: %s", e)
            self.model = None

    def predict(self, image: Image.Image) -> Tuple[str, float, float]:
        """Return (growth_stage, confidence, inference_time_seconds)"""
        if self.model is None:
            logger.warning("Growth model not loaded; returning default prediction")
            return "Vegetative", 0.6, 0.0

        start = time.time()
        try:
            img_np = np.array(image.convert("RGB"))
            results = self.model.predict(img_np, verbose=False)
        except Exception as e:
            logger.warning("Growth prediction failed: %s; returning default", e)
            return "Vegetative", 0.6, time.time() - start

        elapsed = time.time() - start

        # Handle YOLO classification output
        if results and len(results) > 0:
            r = results[0]
            # Classification model: r.probs exists
            if hasattr(r, "probs") and r.probs is not None:
                probs = r.probs.data.cpu().numpy()
                top_idx = int(np.argmax(probs))
                top_conf = float(probs[top_idx])
                names = r.names if hasattr(r, "names") and r.names else {}
                label = names.get(top_idx) or (_FALLBACK_LABELS[top_idx] if top_idx < len(_FALLBACK_LABELS) else str(top_idx))
                return label, top_conf, elapsed
            # Detection model fallback: use class with highest confidence box
            if hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
                boxes = r.boxes
                top_box = max(boxes, key=lambda b: float(b.conf.cpu().numpy()[0]))
                cls = int(top_box.cls.cpu().numpy()[0])
                conf = float(top_box.conf.cpu().numpy()[0])
                names = self.model.names if hasattr(self.model, "names") else {}
                label = names.get(cls) or (_FALLBACK_LABELS[cls] if cls < len(_FALLBACK_LABELS) else str(cls))
                return label, conf, elapsed

        return "Vegetative", 0.6, elapsed
