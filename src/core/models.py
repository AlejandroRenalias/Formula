"""Core Pydantic models for the F1 Pit Wall Strategy System."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.core.provenance import DataSource, DataQuality, ProvenanceMetric


class TireCompound(str, Enum):
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


class TrackStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    VSC = "VSC"
    SAFETY_CAR = "SAFETY_CAR"
    RED_FLAG = "RED_FLAG"


class PitAction(str, Enum):
    BOX_NOW = "BOX_NOW"
    STAY_OUT = "STAY_OUT"


class PaceMode(str, Enum):
    PUSH = "PUSH"
    NORMAL = "NORMAL"
    CONSERVE = "CONSERVE"


class StrategyIntent(str, Enum):
    BASELINE = "BASELINE"
    UNDERCUT = "UNDERCUT"
    OVERCUT = "OVERCUT"
    COVER = "COVER"
    EXTEND = "EXTEND"
    WEATHER_CROSSOVER = "WEATHER_CROSSOVER"
    SAFETY_CAR_OPPORTUNITY = "SAFETY_CAR_OPPORTUNITY"


class StrategyObjective(str, Enum):
    MAXIMIZE_EXPECTED_POSITION = "MAXIMIZE_EXPECTED_POSITION"
    PROTECT_TRACK_POSITION = "PROTECT_TRACK_POSITION"
    MAXIMIZE_POINTS = "MAXIMIZE_POINTS"
    CHASE_WIN = "CHASE_WIN"


class RiskProfile(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    BALANCED = "BALANCED"
    AGGRESSIVE = "AGGRESSIVE"


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LapObservation(BaseModel):
    """Lap timing and condition observation for a driver."""
    lap_number: int
    lap_time_s: float
    s1_time_s: Optional[float] = None
    s2_time_s: Optional[float] = None
    s3_time_s: Optional[float] = None
    compound: TireCompound
    tyre_age_laps: int
    track_status: TrackStatus = TrackStatus.GREEN
    is_pit_in_lap: bool = False
    is_pit_out_lap: bool = False
    usable_for_pace_model: bool = True
    timestamp: Optional[datetime] = None


class ObservedWeather(BaseModel):
    """Empirical weather observations from track sensors."""
    track_temp_c: ProvenanceMetric[float]
    air_temp_c: ProvenanceMetric[float]
    rainfall: ProvenanceMetric[bool]
    humidity_pct: ProvenanceMetric[float]
    wind_speed_kmh: Optional[ProvenanceMetric[float]] = None


class WeatherForecast(BaseModel):
    """Scenario or radar forecast for upcoming laps."""
    rain_probability: ProvenanceMetric[float] = Field(..., description="0.0 to 1.0 probability")
    expected_arrival_laps: ProvenanceMetric[Optional[int]] = Field(
        ..., description="Estimated laps until rain reaches circuit (None if no rain predicted)"
    )
    intensity: ProvenanceMetric[str] = Field(..., description="DRY, LIGHT, MODERATE, HEAVY")
    confidence: DataQuality = DataQuality.MEDIUM


class CompetitorState(BaseModel):
    """State of a rival driver at the current knowledge cutoff."""
    driver: str
    team: str
    position: int
    current_compound: TireCompound
    tyre_age_laps: int
    gap_to_subject_s: float = Field(..., description="Positive = ahead of subject, Negative = behind subject")
    last_lap_time_s: Optional[float] = None
    is_in_pit: bool = False
    pit_stop_count: int = 0


class SubjectDriverState(BaseModel):
    """State of the driver we are managing."""
    driver: str
    team: str
    position: int
    current_compound: TireCompound
    stint_length_laps: int
    total_pit_stops: int
    used_compounds: List[TireCompound]
    last_lap_time_s: float


class DerivedPaceMetrics(BaseModel):
    """Pace and degradation calculated deterministically by Python models."""
    recent_pace_trend_s_per_lap: ProvenanceMetric[float]
    degradation_rate_s_per_lap: ProvenanceMetric[float]
    clean_air_potential_lap_time_s: ProvenanceMetric[float]
    pace_confidence: DataQuality = DataQuality.HIGH


class PitLossMetrics(BaseModel):
    """Pit loss and rejoin calculations computed deterministically."""
    green_pit_loss_s: float = 21.5
    vsc_pit_loss_s: float = 12.5
    sc_pit_loss_s: float = 9.5
    current_pit_loss_s: float
    expected_rejoin_position: int
    expected_rejoin_gap_to_traffic_s: float
    rejoin_traffic_density_penalty_s: float = 0.0


class RaceState(BaseModel):
    """Complete snapshot of race state with strict knowledge cutoff."""
    current_lap: int
    total_laps: int
    timestamp: datetime
    knowledge_cutoff: datetime
    subject_driver: SubjectDriverState
    competitors: List[CompetitorState]
    track_status: TrackStatus
    observed_weather: ObservedWeather
    weather_forecast: WeatherForecast
    lap_history: List[LapObservation]
    derived_pace: DerivedPaceMetrics
    pit_loss: PitLossMetrics
    objective: StrategyObjective = StrategyObjective.MAXIMIZE_EXPECTED_POSITION
    risk_profile: RiskProfile = RiskProfile.BALANCED

    @field_validator("knowledge_cutoff")
    @classmethod
    def validate_cutoff(cls, v: datetime, info: Any) -> datetime:
        timestamp = info.data.get("timestamp")
        if timestamp and v > timestamp:
            raise ValueError(f"Knowledge cutoff {v} cannot exceed current timestamp {timestamp}")
        return v


class StrategyCandidate(BaseModel):
    """A distinct strategy option generated by Python for specialists to score."""
    candidate_id: str = Field(..., description="Stable semantic ID, e.g. 'box_now_sc_hard'")
    ui_label: str = Field(default="A", description="UI display letter: 'A', 'B', 'C', 'D'")
    pit_action: PitAction
    pace_mode: PaceMode
    target_compound: Optional[TireCompound] = None
    intent: StrategyIntent
    target_driver: Optional[str] = Field(default=None, description="Rival target if intent is COVER or UNDERCUT")
    target_lap: int
    description: str
    estimated_time_delta_s: float = 0.0
    candidate_strategy_score: float = 0.0
    factors: Dict[str, float] = Field(default_factory=dict, description="Auditable breakdown of scoring factors")


class AgentReport(BaseModel):
    """Structured report produced by a specialist agent evaluating candidates."""
    agent_name: str
    role: str
    recommended_candidate_id: str
    candidate_scores: Dict[str, float] = Field(..., description="Mapping of candidate_id -> total score")
    candidate_factors: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Candidate ID -> detailed sub-factor breakdown"
    )
    confidence: ConfidenceLevel
    rationale: str
    key_risks: List[str]
    veto: bool = False
    veto_reason: Optional[str] = None


class LLMChiefResolution(BaseModel):
    """Validated, immutable LLM interpretation of a deterministic decision."""
    model_config = ConfigDict(frozen=True)

    confirmed_candidate_id: str = Field(..., description="Candidate ID the Chief endorses.")
    overridden: bool = Field(default=False)
    override_reason: Optional[str] = Field(default=None)
    strategic_rationale: str = Field(...)
    minority_concerns_acknowledged: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel
    cited_evidence_ids: List[str] = Field(default_factory=list)
    uncertainty: Optional[str] = None

    def validate_against_evidence(self, evidence: Any, decision: Any) -> None:
        """Reject unknown candidates/evidence and silent or reasonless overrides."""
        valid_candidate_ids = {c.candidate_id for c in evidence.candidates}
        if self.confirmed_candidate_id not in valid_candidate_ids:
            raise ValueError(
                f"Chief confirmed candidate ID '{self.confirmed_candidate_id}' "
                "is not in the supplied evidence packet candidates."
            )

        deterministic_winner = decision.selected_candidate.candidate_id
        diverges = self.confirmed_candidate_id != deterministic_winner
        if diverges and not self.overridden:
            raise ValueError(
                f"Chief endorsed '{self.confirmed_candidate_id}' but deterministic winner is "
                f"'{deterministic_winner}'. Set overridden=True and populate override_reason."
            )
        if self.overridden and not self.override_reason:
            raise ValueError(
                "Chief resolution has overridden=True but override_reason is empty. "
                "An explicit reason is required."
            )

        valid_ids = set()
        for candidate in evidence.candidates:
            valid_ids.update(candidate.factors.keys())
        for report in evidence.specialist_evaluations:
            for factors in report.candidate_factors.values():
                valid_ids.update(factors.keys())
        valid_ids.update([
            "track_temp_c", "air_temp_c", "rainfall", "humidity_pct", "wind_speed_kmh",
            "rain_probability", "expected_arrival_laps", "intensity",
            "recent_pace_trend_s_per_lap", "degradation_rate_s_per_lap",
            "clean_air_potential_lap_time_s", "green_pit_loss_s", "vsc_pit_loss_s",
            "sc_pit_loss_s", "current_pit_loss_s", "expected_rejoin_position",
            "expected_rejoin_gap_to_traffic_s", "rejoin_traffic_density_penalty_s",
            "track_status",
        ])
        for ref in self.cited_evidence_ids:
            if ref not in valid_ids:
                raise ValueError(
                    f"Chief cited evidence ID '{ref}' is not a valid factor or metric ID "
                    "from the supplied evidence packet."
                )


class NextTrigger(BaseModel):
    """Conditions under which the next strategy meeting should be called."""
    condition_description: str
    trigger_type: str
    threshold_value: Optional[float] = None


class StrategyDecision(BaseModel):
    """Final deterministic decision plus optional LLM resolution metadata."""
    lap: int
    selected_candidate: StrategyCandidate
    all_candidates: List[StrategyCandidate] = Field(
        default_factory=list, description="All evaluated candidates with precomputed scores and factor breakdowns"
    )
    pit_action: PitAction
    target_compound: Optional[TireCompound]
    pace_mode: PaceMode
    intent: StrategyIntent
    target_driver: Optional[str] = None
    rationale: str
    expected_advantage_s: float
    confidence: ConfidenceLevel
    specialist_evaluations: List[AgentReport]
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Final aggregated factors")
    next_triggers: List[NextTrigger]
    conflict_detected: bool = False
    conflict_summary: Optional[str] = None
    debate_held: bool = False
    debate_transcript: Optional[str] = None
    rejected_candidates: Dict[str, str] = Field(
        default_factory=dict,
        description="Candidate ID -> deterministic legality rejection reason.",
    )
    # This is interpretation metadata only. The deterministic winner, scores,
    # candidate list, and evidence remain the authoritative fields above.
    llm_chief_resolution: Optional[LLMChiefResolution] = Field(
        default=None,
        description="Optional validated LLM Chief resolution; never replaces deterministic results.",
    )
