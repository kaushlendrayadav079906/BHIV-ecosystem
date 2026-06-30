from pathlib import Path


class Settings:
    PROJECT_NAME: str = "Plant Intelligence Capability"
    MODEL_DIR: Path = Path(__file__).resolve().parents[1] / "weights"
    SPECIES_MODEL: str = "species_model.pth"
    SPECIES_LABELS: str = "species_classes.json"
    GROWTH_MODEL: str = "growth_stage.pt"
    PART_MODEL: str = "Plant part.pt"
    UNKNOWN_CONFIDENCE_THRESHOLD: float = 0.7
    LOGGER_LEVEL: str = "INFO"


settings = Settings()
