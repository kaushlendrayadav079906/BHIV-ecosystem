from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import Any
from . import inference, schemas, config, utils

logger = logging.getLogger("plant_ai.routes")
router = APIRouter()

_engine = inference.engine


async def initialize_resources():
    try:
        _engine.load_models()
        logger.info("Resources initialized")
    except Exception as e:
        logger.warning("Some models failed to load, but server will continue: %s", e)


async def shutdown_resources():
    try:
        _engine.shutdown()
    except Exception:
        logger.exception("Error during shutdown")


@router.get("/health", response_model=schemas.HealthResponse)
async def health():
    status = _engine.model_status() if _engine.loaded else {}
    return {
        "status": "running",
        "version": config.settings.PROJECT_NAME,
        "model_version": "1.0.0",
        "models_loaded": status,
    }


@router.get("/capabilities", response_model=schemas.CapabilitiesResponse)
async def capabilities():
    return {
        "species_detection": True,
        "growth_stage": True,
        "plant_part_detection": True,
        "structured_evidence": True,
        "explainability": True,
    }


@router.post("/identify", response_model=None)
async def identify(image: UploadFile = File(...)):
    if image is None:
        raise HTTPException(status_code=400, detail={"error": "missing_image"})

    try:
        pil_image = utils.read_imagefile(image)
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "invalid_image"})

    try:
        result = _engine.identify(pil_image)
        return result
    except Exception as e:
        logger.exception("Identify failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": "inference_failed"})


@router.post("/analyze", response_model=None)
async def analyze(image: UploadFile = File(...)):
    if image is None:
        raise HTTPException(status_code=400, detail={"error": "missing_image"})

    try:
        pil_image = utils.read_imagefile(image)
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "invalid_image"})

    try:
        result = _engine.analyze(pil_image)
        return result
    except Exception as e:
        logger.exception("Analyze failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": "inference_failed"})
