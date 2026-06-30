from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger("plant_ai.evidence")


def _timestamp_utc() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _make_observation(
    idx: int,
    observation_type: str,
    value: str,
    confidence: float,
    supporting_features: List[str],
    model_version: str,
    evidence_source: str,
) -> Dict[str, Any]:
    return {
        "observation_id": f"OBS{idx:03d}",
        "type": observation_type,
        "value": value,
        "confidence": round(float(confidence), 4),
        "supporting_features": supporting_features,
        "timestamp": _timestamp_utc(),
        "model_version": model_version,
        "evidence_source": evidence_source,
    }


def _leaf_colour_from_hsv(hsv_image: np.ndarray) -> (str, float, List[str]):
    supporting = ["Average HSV", "Green Pixel Ratio"]
    lower_green = np.array([25, 40, 40])
    upper_green = np.array([95, 255, 255])
    green_mask = cv2.inRange(hsv_image, lower_green, upper_green)

    green_ratio = float(np.count_nonzero(green_mask)) / float(green_mask.size)
    if green_ratio < 0.02:
        return "Unknown", 0.0, ["No green pixels"]

    mean_s = float(cv2.mean(hsv_image[:, :, 1], mask=green_mask)[0])
    mean_v = float(cv2.mean(hsv_image[:, :, 2], mask=green_mask)[0])

    if mean_s < 40 and mean_v < 100:
        value = "Brown"
    elif mean_v < 60:
        value = "Dark Green"
    elif mean_v < 120:
        value = "Medium Green"
    elif mean_v < 180:
        value = "Light Green"
    else:
        value = "Yellow Green"

    conf = min(1.0, 0.5 + green_ratio * (mean_s / 255.0) * 2.0)
    return value, conf, supporting


def _leaf_shape_from_mask(mask: np.ndarray) -> (str, float, List[str]):
    supporting = ["Contour Aspect Ratio", "Polygon Approximation"]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "Unknown", 0.0, supporting

    contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(contour)
    if area < 200:
        return "Unknown", 0.0, supporting

    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w) / float(h) if h > 0 else 0.0
    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
    verts = len(approx)

    if verts >= 8:
        shape = "Palmate"
    elif aspect_ratio >= 0.9 and aspect_ratio <= 1.1:
        shape = "Round"
    elif aspect_ratio < 0.6:
        shape = "Linear"
    elif aspect_ratio >= 1.2 and verts <= 5:
        shape = "Lanceolate"
    elif aspect_ratio >= 0.8:
        shape = "Oval"
    else:
        shape = "Heart"

    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull) if hull is not None and cv2.contourArea(hull) > 0 else area
    solidity = area / hull_area if hull_area else 0.0
    confidence = min(1.0, 0.4 + solidity * 0.6)
    return shape, confidence, supporting


def _leaf_texture_from_gray(gray_image: np.ndarray, mask: Optional[np.ndarray]) -> (str, float, List[str]):
    supporting = ["Laplacian Variance", "Texture Energy"]
    if mask is not None:
        gray_image = cv2.bitwise_and(gray_image, gray_image, mask=mask)

    lap = cv2.Laplacian(gray_image, cv2.CV_64F)
    variance = float(np.var(lap))

    if variance < 120.0:
        texture = "Smooth"
    elif variance < 450.0:
        texture = "Medium"
    else:
        texture = "Rough"

    confidence = min(1.0, 0.2 + (variance / 1000.0))
    return texture, confidence, supporting


def _stem_health_from_detections(detections: List[Dict[str, Any]]) -> (str, float, List[str]):
    supporting = ["Part Detection"]
    stem_detections = [d for d in detections if d.get("class", "").lower() == "stem"]
    if not stem_detections:
        return "Not Detected", 0.75, supporting
    top = max(stem_detections, key=lambda x: x.get("confidence", 0.0))
    confidence = float(top.get("confidence", 0.0))
    value = "Healthy Appearance" if confidence >= 0.7 else "Dry Appearance"
    return value, confidence, supporting


def _presence_from_detections(detections: List[Dict[str, Any]], labels: List[str]) -> (str, float, List[str]):
    supporting = ["Part Detection"]
    normalized = [label.lower() for label in labels]
    matches = [d for d in detections if d.get("class", "").lower() in normalized]
    if not matches:
        return "Not Present", 0.75, supporting
    top = max(matches, key=lambda x: x.get("confidence", 0.0))
    return "Present", float(top.get("confidence", 0.0)), supporting


def _visible_pest_indicators(detections: List[Dict[str, Any]]) -> (str, float, List[str]):
    supporting = ["Part Detection"]
    pest_labels = ["pest", "insect", "aphid", "mite", "worm"]
    matches = [d for d in detections if d.get("class", "").lower() in pest_labels]
    if not matches:
        return "Not Present", 0.75, supporting
    top = max(matches, key=lambda x: x.get("confidence", 0.0))
    return "Present", float(top.get("confidence", 0.0)), supporting


def _nutrient_deficiency_from_hsv(hsv_image: np.ndarray) -> (str, float, List[str]):
    supporting = ["Yellow Pixel Ratio", "Saturation Drop"]
    yellow_lower = np.array([15, 40, 100])
    yellow_upper = np.array([40, 255, 255])
    yellow_mask = cv2.inRange(hsv_image, yellow_lower, yellow_upper)
    yellow_ratio = float(np.count_nonzero(yellow_mask)) / float(yellow_mask.size)

    if yellow_ratio > 0.03:
        value = "Possible Chlorosis"
        confidence = min(1.0, yellow_ratio * 3.0)
    else:
        value = "No Visible Indicators"
        confidence = 0.95

    return value, confidence, supporting


def _water_stress_from_mask(mask: np.ndarray) -> (str, float, List[str]):
    supporting = ["Leaf Contour", "Shape Distortion"]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "No Visible Indicators", 0.0, supporting

    contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(contour)
    x, y, w, h = cv2.boundingRect(contour)
    rect_area = float(w * h) if w > 0 and h > 0 else 1.0
    extent = area / rect_area

    if extent < 0.5:
        return "Leaf Curling", 0.75, supporting
    if extent < 0.75:
        return "Leaf Drooping", 0.55, supporting
    return "No Visible Indicators", 0.95, supporting


def _mechanical_damage_from_mask(mask: np.ndarray) -> (str, float, List[str]):
    supporting = ["Edge Irregularity", "Contour Solidity"]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "No Damage", 0.0, supporting

    contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(contour)
    hull = cv2.convexHull(contour)
    hull_area = float(cv2.contourArea(hull)) if hull is not None and cv2.contourArea(hull) > 0 else max(area, 1.0)
    solidity = area / hull_area

    if solidity < 0.8:
        return "Broken Edge", 0.85, supporting
    if solidity < 0.95:
        return "Torn Leaf", 0.65, supporting
    return "No Damage", 0.95, supporting


def _unknown_abnormalities(mask: np.ndarray) -> (str, float, List[str]):
    supporting = ["Small Contour Count", "Mask Coverage"]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "Unknown Observation", 0.2, supporting

    small_contours = [c for c in contours if cv2.contourArea(c) < 300]
    small_ratio = float(len(small_contours)) / float(len(contours)) if contours else 0.0
    if small_ratio > 0.4 and len(small_contours) >= 3:
        return "Unknown Observation", min(1.0, small_ratio + 0.2), supporting
    return "No Unknown Abnormalities", 0.95, supporting


def generate_observations(
    image: Any,
    detections: List[Dict[str, Any]],
    species: str,
    growth: str,
    model_version: str = "PlantAI-v1.0",
    evidence_source: str = "Image Analysis",
) -> List[Dict[str, Any]]:
    observations: List[Dict[str, Any]] = []

    if hasattr(image, "convert"):
        img = np.array(image.convert("RGB"))
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:
        img = np.array(image)
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    lower_leaf = np.array([20, 30, 30])
    upper_leaf = np.array([100, 255, 255])
    leaf_mask = cv2.inRange(hsv, lower_leaf, upper_leaf)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    lc_value, lc_conf, lc_support = _leaf_colour_from_hsv(hsv)
    observations.append(_make_observation(1, "Leaf Colour", lc_value, lc_conf, lc_support, model_version, evidence_source))

    ls_value, ls_conf, ls_support = _leaf_shape_from_mask(leaf_mask)
    observations.append(_make_observation(2, "Leaf Shape", ls_value, ls_conf, ls_support, model_version, evidence_source))

    lt_value, lt_conf, lt_support = _leaf_texture_from_gray(gray, leaf_mask)
    observations.append(_make_observation(3, "Leaf Texture", lt_value, lt_conf, lt_support, model_version, evidence_source))

    sh_value, sh_conf, sh_support = _stem_health_from_detections(detections)
    observations.append(_make_observation(4, "Stem Health", sh_value, sh_conf, sh_support, model_version, evidence_source))

    fp_value, fp_conf, fp_support = _presence_from_detections(detections, ["flower", "blossom"])
    observations.append(_make_observation(5, "Flower Presence", fp_value, fp_conf, fp_support, model_version, evidence_source))

    fr_value, fr_conf, fr_support = _presence_from_detections(detections, ["fruit"])
    observations.append(_make_observation(6, "Fruit Condition", fr_value, fr_conf, fr_support, model_version, evidence_source))

    pest_value, pest_conf, pest_support = _visible_pest_indicators(detections)
    observations.append(_make_observation(7, "Visible Pest Indicators", pest_value, pest_conf, pest_support, model_version, evidence_source))

    nd_value, nd_conf, nd_support = _nutrient_deficiency_from_hsv(hsv)
    observations.append(_make_observation(8, "Visible Nutrient Deficiency Indicators", nd_value, nd_conf, nd_support, model_version, evidence_source))

    ws_value, ws_conf, ws_support = _water_stress_from_mask(leaf_mask)
    observations.append(_make_observation(9, "Visible Water Stress Indicators", ws_value, ws_conf, ws_support, model_version, evidence_source))

    md_value, md_conf, md_support = _mechanical_damage_from_mask(leaf_mask)
    observations.append(_make_observation(10, "Mechanical Damage", md_value, md_conf, md_support, model_version, evidence_source))

    ua_value, ua_conf, ua_support = _unknown_abnormalities(leaf_mask)
    observations.append(_make_observation(11, "Unknown Abnormalities", ua_value, ua_conf, ua_support, model_version, evidence_source))

    return observations
