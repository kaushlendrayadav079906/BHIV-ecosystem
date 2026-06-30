from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class HealthResponse(BaseModel):
    status: str
    version: str
    model_version: str
    models_loaded: Dict[str, bool] = {}


class Observation(BaseModel):
    observation_id: str
    type: str
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    supporting_features: List[str]
    timestamp: str
    model_version: str
    evidence_source: str


class ExplanationDetail(BaseModel):
    part: Optional[str]
    confidence: float
    role: str


class Explanation(BaseModel):
    summary: str
    details: List[ExplanationDetail] = []
    growth_signal: str
    observation_count: int


class AnalyzeResponse(BaseModel):
    plant_species: Optional[str]
    plant_part: Optional[str]
    growth_stage: Optional[str]
    confidence: Optional[float]
    observations: List[Observation] = []
    explanation: Optional[Explanation] = None
    alternatives: List[dict] = []
    model_version: str
    inference_time: str


class UnknownResponse(BaseModel):
    status: str
    confidence: float
    reason: str


class CapabilitiesResponse(BaseModel):
    species_detection: bool
    growth_stage: bool
    plant_part_detection: bool
    structured_evidence: bool
    explainability: bool
