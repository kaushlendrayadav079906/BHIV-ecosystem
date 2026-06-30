import time
from typing import Tuple, List, Dict
import logging
from PIL import Image
from .config import settings

logger = logging.getLogger("plant_ai.part")


class PartModel:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or str(settings.MODEL_DIR / settings.PART_MODEL)
        self.model = None

    def load(self):
        try:
            # Lazy import to keep dependency optional until runtime
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            logger.info("Loaded part detection model from %s", self.model_path)
        except Exception as e:
            logger.warning("Could not load part detection model: %s", e)
            self.model = None

    def predict(self, image: Image.Image) -> Tuple[str, float, float, List[Dict]]:
        """Run detection and return top class, confidence, inference_time_seconds, and raw detections list."""
        if self.model is None:
            logger.warning("Part model not loaded; returning empty detections")
            return None, 0.0, 0.0, []

        start = time.time()
        try:
            # ultralytics accepts filepath or numpy array
            import numpy as np
            img_np = np.array(image.convert("RGB"))
            results = self.model.predict(img_np, verbose=False)
        except Exception as e:
            logger.warning("Part detection failed: %s; returning empty", e)
            elapsed = time.time() - start
            return None, 0.0, elapsed, []

        elapsed = time.time() - start
        detections = []
        top_class = None
        top_conf = 0.0

        if results and len(results) > 0:
            r = results[0]
            boxes = r.boxes
            for b in boxes:
                cls = int(b.cls.cpu().numpy()[0]) if hasattr(b, 'cls') else int(b.cls)
                conf = float(b.conf.cpu().numpy()[0]) if hasattr(b, 'conf') else float(b.conf)
                label = self.model.names.get(cls, str(cls)) if hasattr(self.model, 'names') else str(cls)
                detections.append({"class": label, "confidence": conf, "xyxy": b.xyxy.tolist() if hasattr(b, 'xyxy') else None})
                if conf > top_conf:
                    top_conf = conf
                    top_class = label

        return top_class, top_conf, elapsed, detections
