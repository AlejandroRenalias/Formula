"""Tyre compound characteristics and stint models."""
from typing import Dict
from pydantic import BaseModel
from src.core.models import TireCompound


class CompoundSpecs(BaseModel):
    compound: TireCompound
    base_pace_delta_s: float  # Relative to Soft (Soft = 0.0, Medium = +0.4s, Hard = +0.9s)
    expected_life_laps: int
    cliff_lap_threshold: int
    degradation_base_rate_s_per_lap: float


TYRE_SPECS: Dict[TireCompound, CompoundSpecs] = {
    TireCompound.SOFT: CompoundSpecs(
        compound=TireCompound.SOFT,
        base_pace_delta_s=0.0,
        expected_life_laps=18,
        cliff_lap_threshold=15,
        degradation_base_rate_s_per_lap=0.12,
    ),
    TireCompound.MEDIUM: CompoundSpecs(
        compound=TireCompound.MEDIUM,
        base_pace_delta_s=0.4,
        expected_life_laps=28,
        cliff_lap_threshold=24,
        degradation_base_rate_s_per_lap=0.07,
    ),
    TireCompound.HARD: CompoundSpecs(
        compound=TireCompound.HARD,
        base_pace_delta_s=0.9,
        expected_life_laps=40,
        cliff_lap_threshold=35,
        degradation_base_rate_s_per_lap=0.04,
    ),
    TireCompound.INTERMEDIATE: CompoundSpecs(
        compound=TireCompound.INTERMEDIATE,
        base_pace_delta_s=6.5,  # When track is wet
        expected_life_laps=30,
        cliff_lap_threshold=25,
        degradation_base_rate_s_per_lap=0.10,
    ),
    TireCompound.WET: CompoundSpecs(
        compound=TireCompound.WET,
        base_pace_delta_s=12.0,
        expected_life_laps=35,
        cliff_lap_threshold=30,
        degradation_base_rate_s_per_lap=0.15,
    ),
}


class TyreModel:
    """Estimates tyre degradation and stint health."""

    @classmethod
    def lap_delta_s(cls, compound: TireCompound, age: int, degradation_scale: float = 1.0,
                    cliff_rate_s: float = 0.15) -> float:
        """Simple projection loss: compound offset, linear wear and post-cliff wear."""
        specs = cls.get_compound_specs(compound)
        return (specs.base_pace_delta_s + specs.degradation_base_rate_s_per_lap * age * degradation_scale
                + max(0, age - specs.cliff_lap_threshold) * cliff_rate_s)

    @staticmethod
    def get_compound_specs(compound: TireCompound) -> CompoundSpecs:
        return TYRE_SPECS.get(compound, TYRE_SPECS[TireCompound.MEDIUM])

    @staticmethod
    def estimate_tyre_condition(compound: TireCompound, stint_laps: int) -> float:
        """Returns estimated health ratio from 1.0 (fresh) down to 0.0 (dead)."""
        specs = TyreModel.get_compound_specs(compound)
        if stint_laps <= 0:
            return 1.0
        if stint_laps >= specs.expected_life_laps:
            return 0.05
        return max(0.0, 1.0 - (stint_laps / specs.expected_life_laps))
