from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


class DiversificationTransitionClass(str, Enum):
    ACTIVE_REVISIT_ROUTE = "active_revisit_route"
    SURVIVAL_PROTECTED_ROUTE = "survival_protected_route"
    RECOVERY_REVISIT_ROUTE = "recovery_revisit_route"
    FOCUS_RECURRENCE_ROUTE = "focus_recurrence_route"
    BACKGROUND_MONITOR_ROUTE = "background_monitor_route"


class StagnationSignature(str, Enum):
    REPEATED_ROUTE_LOW_PROGRESS = "repeated_route_low_progress"
    REPEATED_REOPEN_WITHOUT_NEW_INPUT = "repeated_reopen_without_new_input"
    LOOPING_REVISIT_WITHOUT_DELTA = "looping_revisit_without_delta"
    STAGNANT_BACKGROUND_CYCLE = "stagnant_background_cycle"
    DOMINANT_ROUTE_WHILE_ALTERNATIVES_AVAILABLE = (
        "dominant_route_while_alternatives_available"
    )


class AlternativePathClass(str, Enum):
    RAISE_BRANCH_CANDIDATE = "raise_branch_candidate"
    REFRAME_TENSION_ACCESS = "reframe_tension_access"
    SWITCH_PROCESSING_MODE_CANDIDATE = "switch_processing_mode_candidate"
    REQUEST_NEW_INPUT_CANDIDATE = "request_new_input_candidate"
    SAFE_PAUSE_CANDIDATE = "safe_pause_candidate"
    SHIFT_REGULATION_OPTION_CLASS_CANDIDATE = "shift_regulation_option_class_candidate"
    REVIVE_DORMANT_BRANCH_CANDIDATE = "revive_dormant_branch_candidate"


class DiversificationDecisionStatus(str, Enum):
    JUSTIFIED_RECURRENCE = "justified_recurrence"
    STAGNATION_DETECTED = "stagnation_detected"
    ALTERNATIVE_PATH_OPENING = "alternative_path_opening"
    NO_SAFE_DIVERSIFICATION = "no_safe_diversification"
    AMBIGUOUS_STAGNATION = "ambiguous_stagnation"


class ProgressEvidenceClass(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class StreamDiversificationUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class C03RestrictionCode(StrEnum):
    DIVERSIFICATION_STATE_MUST_BE_READ = "diversification_state_must_be_read"
    STAGNATION_SIGNATURES_MUST_BE_READ = "stagnation_signatures_must_be_read"
    REDUNDANCY_SCORES_MUST_BE_READ = "redundancy_scores_must_be_read"
    DIVERSIFICATION_PRESSURE_MUST_BE_READ = "diversification_pressure_must_be_read"
    REPEAT_JUSTIFICATION_MUST_BE_READ = "repeat_justification_must_be_read"
    PROTECTED_RECURRENCE_MUST_BE_READ = "protected_recurrence_must_be_read"
    ALTERNATIVE_CLASSES_MUST_BE_READ = "alternative_classes_must_be_read"
    NO_SAFE_DIVERSIFICATION_MUST_BE_READ = "no_safe_diversification_must_be_read"
    DIVERSIFICATION_CONFLICT_WITH_SURVIVAL_MUST_BE_READ = (
        "diversification_conflict_with_survival_must_be_read"
    )
    STRUCTURAL_STAGNATION_NOT_TEXT_ANTIREPEAT = (
        "structural_stagnation_not_text_antirepeat"
    )
    RANDOMNESS_NOT_DIVERSIFICATION = "randomness_not_diversification"
    REPEAT_DETECTED_BUT_JUSTIFIED_MUST_BE_READ = (
        "repeat_detected_but_justified_must_be_read"
    )
    LOW_CONFIDENCE_STAGNATION_MUST_BE_READ = "low_confidence_stagnation_must_be_read"
    PROGRESS_EVIDENCE_CLASS_MUST_BE_READ = "progress_evidence_class_must_be_read"
    PROGRESS_EVIDENCE_AXES_MUST_BE_READ = "progress_evidence_axes_must_be_read"
    EDGE_BAND_APPLIED_MUST_BE_READ = "edge_band_applied_must_be_read"
    ALTERNATIVE_ACTIONABILITY_MUST_BE_READ = "alternative_actionability_must_be_read"
    SURVIVAL_FILTERED_ALTERNATIVES_MUST_BE_READ = (
        "survival_filtered_alternatives_must_be_read"
    )
    NO_SAFE_DIVERSIFICATION_CLAIM_PRESENT = "no_safe_diversification_claim_present"
    STAGNATION_SIGNATURE_PRESENT = "stagnation_signature_present"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"


class DiversificationLedgerEventKind(str, Enum):
    ASSESSED = "assessed"
    STAGNATION_SIGNATURE = "stagnation_signature"
    REPEAT_GATED = "repeat_gated"
    ALTERNATIVE_OPENED = "alternative_opened"
    PROTECTED_RECURRENCE = "protected_recurrence"
    NO_SAFE_DIVERSIFICATION = "no_safe_diversification"
    PRESSURE_RAISED = "pressure_raised"
    PRESSURE_DECAYED = "pressure_decayed"
    PRESSURE_RESET = "pressure_reset"


@dataclass(frozen=True, slots=True)
class DiversificationPathCount:
    path_key: str
    count: int


@dataclass(frozen=True, slots=True)
class DiversificationRedundancyScore:
    path_id: str
    transition_class: DiversificationTransitionClass
    repetition_count: int
    progress_delta: float
    redundancy_score: float
    repeat_requires_justification: bool
    protected_recurrence: bool


@dataclass(frozen=True, slots=True)
class DiversificationPathAssessment:
    assessment_id: str
    path_id: str
    tension_id: str
    causal_anchor: str
    transition_class: DiversificationTransitionClass
    current_status: str
    current_mode: str
    revisit_priority: float
    repetition_count: int
    progress_delta: float
    progress_evidence_axes: int
    progress_evidence_class: ProgressEvidenceClass
    new_causal_input: bool
    edge_band_applied: bool
    stagnation_signatures: tuple[StagnationSignature, ...]
    redundancy_score: float
    repeat_requires_justification: bool
    protected_recurrence: bool
    alternative_classes: tuple[AlternativePathClass, ...]
    actionable_alternative_classes: tuple[AlternativePathClass, ...]
    survival_filtered_alternatives: bool
    no_safe_diversification: bool
    confidence: float
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class DiversificationLedgerEvent:
    event_id: str
    event_kind: DiversificationLedgerEventKind
    path_id: str
    tension_id: str
    stream_id: str
    reason: str
    reason_code: str
    provenance: str


@dataclass(frozen=True, slots=True)
class StreamDiversificationState:
    diversification_id: str
    stream_id: str
    source_stream_sequence_index: int
    source_scheduler_id: str
    path_assessments: tuple[DiversificationPathAssessment, ...]
    recent_path_counts: tuple[DiversificationPathCount, ...]
    stagnation_signatures: tuple[StagnationSignature, ...]
    redundancy_scores: tuple[DiversificationRedundancyScore, ...]
    diversification_pressure: float
    allowed_alternative_classes: tuple[AlternativePathClass, ...]
    actionable_alternative_classes: tuple[AlternativePathClass, ...]
    repeat_requires_justification_for: tuple[str, ...]
    protected_recurrence_classes: tuple[DiversificationTransitionClass, ...]
    decision_status: DiversificationDecisionStatus
    no_safe_diversification: bool
    diversification_conflict_with_survival: bool
    low_confidence_stagnation: bool
    confidence: float
    source_c01_state_ref: str
    source_c02_state_ref: str
    source_regulation_ref: str
    source_affordance_ref: str
    source_preference_ref: str
    source_viability_ref: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class StreamDiversificationContext:
    prior_diversification_state: StreamDiversificationState | None = None
    source_lineage: tuple[str, ...] = ()
    step_delta: int = 1
    strong_progress_threshold: float = 0.65
    low_progress_threshold: float = 0.2
    progress_edge_band: float = 0.08
    pressure_edge_band: float = 0.06
    minimum_progress_axes_for_meaningful: int = 2
    stagnation_pressure_gain: float = 0.22
    pressure_decay_on_shift: float = 0.28
    disable_structural_stagnation_detection: bool = False
    disable_repeat_justification_gating: bool = False
    expected_schema_version: str = "c03.stream_diversification.v1"


@dataclass(frozen=True, slots=True)
class StreamDiversificationGateDecision:
    accepted: bool
    usability_class: StreamDiversificationUsabilityClass
    restrictions: tuple[C03RestrictionCode, ...]
    reason: str
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class StreamDiversificationTelemetry:
    source_lineage: tuple[str, ...]
    diversification_id: str
    stream_id: str
    source_stream_sequence_index: int
    path_count: int
    stagnation_signature_count: int
    repeat_requires_justification_count: int
    protected_recurrence_count: int
    no_safe_diversification_count: int
    actionable_alternative_count: int
    edge_band_applied_count: int
    survival_filtered_alternative_count: int
    diversification_pressure: float
    decision_status: DiversificationDecisionStatus
    allowed_alternative_classes: tuple[str, ...]
    transition_classes: tuple[str, ...]
    ledger_events: tuple[DiversificationLedgerEvent, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: StreamDiversificationGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class StreamDiversificationResult:
    state: StreamDiversificationState
    downstream_gate: StreamDiversificationGateDecision
    telemetry: StreamDiversificationTelemetry
    abstain: bool
    abstain_reason: str | None
    no_text_antirepeat_dependency: bool
    no_randomness_dependency: bool
    no_planner_arbitration_dependency: bool
