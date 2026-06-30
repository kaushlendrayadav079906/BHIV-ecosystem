from io import BytesIO
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile
import logging

logger = logging.getLogger("plant_ai.utils")


def read_imagefile(file: UploadFile) -> Image.Image:
    try:
        contents = file.file.read()
        if not contents:
            raise ValueError("Empty file")
        image = Image.open(BytesIO(contents)).convert("RGB")
        return image
    except UnidentifiedImageError:
        logger.warning("Invalid or unsupported image format uploaded")
        raise
    except Exception:
        logger.warning("Failed to read image file")
        raise
