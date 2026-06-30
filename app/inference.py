import time
import logging
from typing import Optional, Dict, Any
from PIL import Image

from .config import settings
from .species_model import SpeciesModel
from .growth_model import GrowthModel
from .part_model import PartModel
from . import evidence, explain

logger = logging.getLogger("plant_ai.inference")


class InferenceEngine:
    def __init__(self):
        self.species_model: Optional[SpeciesModel] = None
        self.growth_model: Optional[GrowthModel] = None
        self.part_model: Optional[PartModel] = None
        self.loaded = False

    def load_models(self):
        if self.loaded:
            return
        self.species_model = SpeciesModel()
        self.species_model.load()

        self.growth_model = GrowthModel()
        self.growth_model.load()

        self.part_model = PartModel()
        self.part_model.load()

        self.loaded = True
        loaded_count = sum([
            self.species_model.model is not None,
            self.growth_model.model is not None,
            self.part_model.model is not None,
        ])
        logger.info("Model initialization complete: %d/3 models loaded.", loaded_count)

    def model_status(self) -> Dict[str, bool]:
        return {
            "species_model": self.species_model is not None and self.species_model.model is not None,
            "growth_model": self.growth_model is not None and self.growth_model.model is not None,
            "part_model": self.part_model is not None and self.part_model.model is not None,
        }

    def identify(self, image: Image.Image) -> Dict[str, Any]:
        if not self.loaded:
            raise RuntimeError("Models not loaded")

        start = time.time()

        species, conf, alternatives, s_t = self.species_model.predict(image)
        species_display = species

        growth, g_conf, g_t = self.growth_model.predict(image)

        part_top_class, part_top_conf, part_t, detections = self.part_model.predict(image)

        inference_total = time.time() - start

        return {
            "plant_species": species_display,
            "plant_part": part_top_class,
            "plant_part_confidence": round(part_top_conf, 4),
            "growth_stage": growth,
            "growth_confidence": round(g_conf, 4),
            "confidence": round(conf, 4),
            "alternatives": alternatives,
            "model_version": "Species-v1",
            "inference_time": self._format_time(inference_total),
        }

    def analyze(self, image: Image.Image) -> Dict[str, Any]:
        if not self.loaded:
            raise RuntimeError("Models not loaded")

        start = time.time()

        species, s_conf, alternatives, s_t = self.species_model.predict(image)
        species_display = species

        growth, g_conf, g_t = self.growth_model.predict(image)

        part_top_class, part_top_conf, part_t, detections = self.part_model.predict(image)

        observations = evidence.generate_observations(
            image=image,
            detections=detections,
            species=species_display,
            growth=growth,
            model_version="PlantAI-v1.0",
            evidence_source="Image Analysis",
        )

        # Filter observations below confidence threshold
        observations = [
            obs for obs in observations
            if obs["confidence"] >= settings.UNKNOWN_CONFIDENCE_THRESHOLD
        ]

        explanation = explain.generate_explanation(
            species=species_display,
            parts=detections,
            growth=growth,
            observations=observations,
        )

        inference_total = time.time() - start

        return {
            "plant_species": species_display,
            "plant_part": part_top_class,
            "plant_part_confidence": round(part_top_conf, 4),
            "growth_stage": growth,
            "growth_confidence": round(g_conf, 4),
            "confidence": round(s_conf, 4),
            "observations": observations,
            "explanation": explanation,
            "alternatives": alternatives,
            "model_version": "PlantAI v1.0",
            "inference_time": self._format_time(inference_total),
        }

    def shutdown(self):
        # If any model requires explicit cleanup, do it here
        self.loaded = False

    def _format_time(self, seconds: float) -> str:
        if seconds < 0.5:
            ms = int(seconds * 1000)
            return f"{ms} ms"
        else:
            return f"{seconds:.2f} sec"


engine = InferenceEngine()
