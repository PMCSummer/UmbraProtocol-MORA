from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


class SubjectMode(str, Enum):
    HOLD_CURRENT_STREAM = "hold_current_stream"
    REVISIT_UNRESOLVED_TENSION = "revisit_unresolved_tension"
    RECOVERY_MODE = "recovery_mode"
    DIVERSIFICATION_PROBE = "diversification_probe"
    PASSIVE_MONITORING = "passive_monitoring"
    OUTPUT_PREPARATION = "output_preparation"
    SAFE_IDLE = "safe_idle"


class EndogenousTickKind(str, Enum):
    ENDOGENOUS = "endogenous"
    EXTERNAL_REACTIVE = "external_reactive"
    DEGRADED_ENDOGENOUS = "degraded_endogenous"
    QUIESCENT = "quiescent"


class HoldSwitchDecision(str, Enum):
    CONTINUE_CURRENT_MODE = "continue_current_mode"
    SWITCH_TO_MODE = "switch_to_mode"
    FORCED_HOLD_DUE_TO_SURVIVAL = "forced_hold_due_to_survival"
    SAFE_IDLE_ONLY = "safe_idle_only"
    NO_CLEAR_MODE_WINNER = "no_clear_mode_winner"
    ARBITRATION_CONFLICT = "arbitration_conflict"
    INSUFFICIENT_INTERNAL_BASIS = "insufficient_internal_basis"
    FORCED_REARBITRATION = "forced_rearbitration"


class InterruptibilityClass(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BLOCKED = "blocked"


class ModeArbitrationUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class C04RestrictionCode(StrEnum):
    MODE_ARBITRATION_STATE_MUST_BE_READ = "mode_arbitration_state_must_be_read"
    ENDOGENOUS_TICK_CONTRACT_MUST_BE_READ = "endogenous_tick_contract_must_be_read"
    ACTIVE_MODE_MUST_BE_READ = "active_mode_must_be_read"
    CANDIDATE_MODES_MUST_BE_READ = "candidate_modes_must_be_read"
    ARBITRATION_BASIS_MUST_BE_READ = "arbitration_basis_must_be_read"
    MODE_PRIORITY_VECTOR_MUST_BE_READ = "mode_priority_vector_must_be_read"
    HOLD_SWITCH_DECISION_MUST_BE_READ = "hold_switch_decision_must_be_read"
    INTERRUPTIBILITY_MUST_BE_READ = "interruptibility_must_be_read"
    DWELL_BUDGET_MUST_BE_READ = "dwell_budget_must_be_read"
    SAFE_IDLE_MUST_BE_READ = "safe_idle_must_be_read"
    SURVIVAL_INTERRUPT_MUST_BE_READ = "survival_interrupt_must_be_read"
    NO_PLANNER_MODE_BACKFILL = "no_planner_mode_backfill"
    NO_BACKGROUND_LOOP_SHORTCUT = "no_background_loop_shortcut"
    NO_EXTERNAL_TURN_SUBSTITUTION = "no_external_turn_substitution"
    NO_CLEAR_MODE_WINNER_PRESENT = "no_clear_mode_winner_present"
    ARBITRATION_CONFLICT_PRESENT = "arbitration_conflict_present"
    INSUFFICIENT_INTERNAL_BASIS_PRESENT = "insufficient_internal_basis_present"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"


class ModeArbitrationLedgerEventKind(str, Enum):
    ASSESSED = "assessed"
    HOLD = "hold"
    SWITCH = "switch"
    FORCED_HOLD = "forced_hold"
    SAFE_IDLE = "safe_idle"
    REARBITRATION = "rearbitration"


@dataclass(frozen=True, slots=True)
class ModePriorityScore:
    mode: SubjectMode
    score: float
    enabled: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ModeArbitrationLedgerEvent:
    event_id: str
    event_kind: ModeArbitrationLedgerEventKind
    tick_id: str
    stream_id: str
    mode: SubjectMode | None
    reason: str
    reason_code: str
    provenance: str


@dataclass(frozen=True, slots=True)
class ModeArbitrationState:
    arbitration_id: str
    tick_id: str
    stream_id: str
    source_stream_sequence_index: int
    active_mode: SubjectMode
    candidate_modes: tuple[SubjectMode, ...]
    arbitration_basis: tuple[str, ...]
    mode_priority_vector: tuple[ModePriorityScore, ...]
    hold_or_switch_decision: HoldSwitchDecision
    interruptibility: InterruptibilityClass
    dwell_budget_remaining: int
    forced_rearbitration: bool
    endogenous_tick_kind: EndogenousTickKind
    endogenous_tick_allowed: bool
    external_turn_present: bool
    handoff_reason: str
    arbitration_confidence: float
    source_c01_state_ref: str
    source_c02_state_ref: str
    source_c03_state_ref: str
    source_regulation_ref: str
    source_affordance_ref: str
    source_preference_ref: str
    source_viability_ref: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class ModeArbitrationContext:
    prior_mode_arbitration_state: ModeArbitrationState | None = None
    source_lineage: tuple[str, ...] = ()
    step_delta: int = 1
    external_turn_present: bool = False
    allow_endogenous_tick: bool = True
    force_rearbitration: bool = False
    weak_external_event: bool = False
    closure_progress_event: bool = False
    resource_budget: float = 1.0
    cooldown_active: bool = False
    default_dwell_budget: int = 2
    min_confidence_for_switch: float = 0.58
    conflict_margin: float = 0.08
    recent_failed_modes: tuple[SubjectMode, ...] = ()
    recent_completed_modes: tuple[SubjectMode, ...] = ()
    expected_schema_version: str = "c04.mode_arbitration.v1"


@dataclass(frozen=True, slots=True)
class ModeArbitrationGateDecision:
    accepted: bool
    usability_class: ModeArbitrationUsabilityClass
    restrictions: tuple[C04RestrictionCode, ...]
    reason: str
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ModeArbitrationTelemetry:
    source_lineage: tuple[str, ...]
    arbitration_id: str
    tick_id: str
    stream_id: str
    source_stream_sequence_index: int
    active_mode: SubjectMode
    candidate_count: int
    basis_count: int
    hold_or_switch_decision: HoldSwitchDecision
    endogenous_tick_kind: EndogenousTickKind
    endogenous_tick_allowed: bool
    external_turn_present: bool
    dwell_budget_remaining: int
    forced_rearbitration: bool
    arbitration_confidence: float
    interruptibility: InterruptibilityClass
    mode_priority_vector: tuple[ModePriorityScore, ...]
    ledger_events: tuple[ModeArbitrationLedgerEvent, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: ModeArbitrationGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ModeArbitrationResult:
    state: ModeArbitrationState
    downstream_gate: ModeArbitrationGateDecision
    telemetry: ModeArbitrationTelemetry
    abstain: bool
    abstain_reason: str | None
    no_planner_mode_selection_dependency: bool
    no_background_loop_dependency: bool
    no_external_turn_substitution_dependency: bool
