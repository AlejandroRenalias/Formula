"""Data provenance models and enums."""
from enum import Enum
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class DataSource(str, Enum):
    """Source provenance for any telemetry or strategy metric."""
    REAL_FASTF1 = "REAL_FASTF1"
    DERIVED_MODEL = "DERIVED_MODEL"
    SCENARIO_FORECAST = "SCENARIO_FORECAST"
    USER_DEFINED = "USER_DEFINED"
    SYNTHETIC = "SYNTHETIC"
    RULE_INFERENCE = "RULE_INFERENCE"


class DataQuality(str, Enum):
    """Confidence or accuracy rating of data."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ProvenanceMetric(BaseModel, Generic[T]):
    """A typed value paired with its exact origin and quality rating."""
    value: T
    source: DataSource
    quality: DataQuality = DataQuality.HIGH
    notes: Optional[str] = None
