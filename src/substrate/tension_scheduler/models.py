from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


class TensionKind(str, Enum):
    VIABILITY_PRESSURE = "viability_pressure"
    UNRESOLVED_OPERATIONAL_PROCESS = "unresolved_operational_process"
    PENDING_RECOVERY = "pending_recovery"
    INTERRUPTION_CONTINUITY = "interruption_continuity"
    FOCUS_DRIFT = "focus_drift"


class TensionLifecycleStatus(str, Enum):
    ACTIVE = "active"
    DEFERRED = "deferred"
    DORMANT = "dormant"
    REACTIVATED = "reactivated"
    STALE = "stale"
    CLOSED = "closed"


class TensionSchedulingMode(str, Enum):
    REVISIT_NOW = "revisit_now"
    DEFER_UNTIL_CONDITION = "defer_until_condition"
    MONITOR_PASSIVELY = "monitor_passively"
    HOLD_IN_BACKGROUND = "hold_in_background"
    SUPPRESS_TEMPORARILY = "suppress_temporarily"
    RELEASE_AS_STALE = "release_as_stale"
    REOPEN_DUE_TO_TRIGGER = "reopen_due_to_trigger"
    NO_SAFE_DEFER_CLAIM = "no_safe_defer_claim"
    UNSCHEDULABLE_TENSION = "unschedulable_tension"


class TensionWakeCause(str, Enum):
    NONE = "none"
    EXPLICIT_SIGNAL = "explicit_signal"
    DEFER_WINDOW_EXPIRY = "defer_window_expiry"
    REOPEN_CONDITION = "reopen_condition"


class TensionSignalOrigin(str, Enum):
    C02_INTERNAL = "c02_internal"
    C01_PHASE_NATIVE = "c01_phase_native"
    R_PHASE_NATIVE = "r_phase_native"
    UNKNOWN = "unknown"
    EXTERNAL_UNTRUSTED = "external_untrusted"


class TensionDecayState(str, Enum):
    NONE = "none"
    DECAYING = "decaying"
    STALE = "stale"
    RELEASED = "released"


class TensionSchedulerUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class C02RestrictionCode(StrEnum):
    TENSION_STATE_MUST_BE_READ = "tension_state_must_be_read"
    TENSION_LIFECYCLE_MUST_BE_READ = "tension_lifecycle_must_be_read"
    SCHEDULING_MODE_MUST_BE_READ = "scheduling_mode_must_be_read"
    REVISIT_PRIORITY_MUST_BE_READ = "revisit_priority_must_be_read"
    WAKE_CONDITIONS_MUST_BE_READ = "wake_conditions_must_be_read"
    SUPPRESSION_BUDGET_MUST_BE_READ = "suppression_budget_must_be_read"
    CLOSURE_CRITERIA_MUST_BE_READ = "closure_criteria_must_be_read"
    REOPEN_CRITERIA_MUST_BE_READ = "reopen_criteria_must_be_read"
    WAKE_CAUSE_MUST_BE_READ = "wake_cause_must_be_read"
    WAKE_SCOPE_MUST_BE_READ = "wake_scope_must_be_read"
    REACTIVATION_REQUIRES_LAWFUL_WAKE_CAUSE = (
        "reactivation_requires_lawful_wake_cause"
    )
    C01_CARRYOVER_NOT_EQUAL_TENSION = "c01_carryover_not_equal_tension"
    RETRIEVAL_NOT_EQUAL_REOPEN = "retrieval_not_equal_reopen"
    CLOSURE_REQUIRES_EVIDENCE = "closure_requires_evidence"
    STALE_NOT_EQUAL_CLOSED = "stale_not_equal_closed"
    SUPPRESSION_NOT_EQUAL_DROP = "suppression_not_equal_drop"
    KIND_POLICY_MUST_BE_READ = "kind_policy_must_be_read"
    THRESHOLD_EDGE_DEGRADE_MUST_BE_READ = "threshold_edge_degrade_must_be_read"
    STALE_RELEASE_MUST_BE_READ = "stale_release_must_be_read"
    NO_PLANNER_BACKLOG_SUBSTITUTION = "no_planner_backlog_substitution"
    WEAK_WAKE_SIGNAL_ORIGIN_IGNORED = "weak_wake_signal_origin_ignored"
    WEAK_CLOSURE_SIGNAL_ORIGIN_IGNORED = "weak_closure_signal_origin_ignored"
    WEAK_REOPEN_SIGNAL_ORIGIN_IGNORED = "weak_reopen_signal_origin_ignored"
    UNSCHEDULABLE_TENSION_PRESENT = "unschedulable_tension_present"
    NO_SAFE_DEFER_CLAIM_PRESENT = "no_safe_defer_claim_present"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"


class TensionLedgerEventKind(str, Enum):
    REGISTERED = "registered"
    DEFERRED = "deferred"
    SUPPRESSED = "suppressed"
    REACTIVATED = "reactivated"
    CLOSED = "closed"
    REOPENED = "reopened"
    STALE = "stale"
    RELEASED = "released"
    MONITORED = "monitored"


@dataclass(frozen=True, slots=True)
class TensionScheduleEntry:
    tension_id: str
    source_stream_id: str
    source_stream_sequence_index: int
    tension_kind: TensionKind
    causal_anchor: str
    current_status: TensionLifecycleStatus
    revisit_priority: float
    scheduling_mode: TensionSchedulingMode
    earliest_revisit_step: int | None
    wake_conditions: tuple[str, ...]
    matched_wake_triggers: tuple[str, ...]
    reactivation_cause: TensionWakeCause
    wake_scope_matched: bool
    suppression_budget: int
    suppression_remaining: int
    decay_state: TensionDecayState
    stale: bool
    closure_criteria: tuple[str, ...]
    reopen_criteria: tuple[str, ...]
    confidence: float
    trigger_unknown: bool
    closure_uncertain: bool
    scheduler_conflict: bool
    weak_wake_signal_ignored: bool
    weak_closure_signal_ignored: bool
    weak_reopen_signal_ignored: bool
    threshold_edge_downgrade_applied: bool
    kind_policy_applied: bool
    unschedulable: bool
    created_sequence_index: int
    last_touched_sequence_index: int
    inactive_steps: int
    reason: str
    provenance: str


@dataclass(frozen=True, slots=True)
class TensionLedgerEvent:
    event_id: str
    event_kind: TensionLedgerEventKind
    tension_id: str
    stream_id: str
    reason: str
    reason_code: str
    provenance: str


@dataclass(frozen=True, slots=True)
class TensionSchedulerState:
    scheduler_id: str
    source_stream_id: str
    source_stream_sequence_index: int
    tensions: tuple[TensionScheduleEntry, ...]
    active_tension_ids: tuple[str, ...]
    deferred_tension_ids: tuple[str, ...]
    dormant_tension_ids: tuple[str, ...]
    stale_tension_ids: tuple[str, ...]
    closed_tension_ids: tuple[str, ...]
    wake_queue_tension_ids: tuple[str, ...]
    suppression_active: bool
    confidence: float
    source_c01_state_ref: str
    source_regulation_ref: str
    source_affordance_ref: str
    source_preference_ref: str
    source_viability_ref: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class TensionSchedulerContext:
    prior_scheduler_state: TensionSchedulerState | None = None
    source_lineage: tuple[str, ...] = ()
    step_delta: int = 1
    explicit_wake_triggers: tuple[str, ...] = ()
    wake_anchor_scope: tuple[str, ...] = ()
    closure_evidence_anchor_keys: tuple[str, ...] = ()
    reopen_anchor_keys: tuple[str, ...] = ()
    retrieved_episode_refs: tuple[str, ...] = ()
    wake_signal_origin: TensionSignalOrigin = TensionSignalOrigin.C02_INTERNAL
    closure_signal_origin: TensionSignalOrigin = TensionSignalOrigin.C02_INTERNAL
    reopen_signal_origin: TensionSignalOrigin = TensionSignalOrigin.C02_INTERNAL
    default_suppression_budget: int = 2
    stale_after_steps: int = 3
    release_after_steps: int = 5
    allow_suppression: bool = True
    require_strong_priority_basis: bool = False
    expected_schema_version: str = "c02.tension_scheduler.v1"


@dataclass(frozen=True, slots=True)
class TensionSchedulerGateDecision:
    accepted: bool
    usability_class: TensionSchedulerUsabilityClass
    restrictions: tuple[C02RestrictionCode, ...]
    reason: str
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class TensionSchedulerTelemetry:
    source_lineage: tuple[str, ...]
    scheduler_id: str
    source_stream_id: str
    source_stream_sequence_index: int
    tension_count: int
    active_count: int
    deferred_count: int
    dormant_count: int
    stale_count: int
    closed_count: int
    wake_queue_count: int
    scheduling_modes: tuple[str, ...]
    wake_causes: tuple[str, ...]
    lifecycle_statuses: tuple[str, ...]
    tension_kinds: tuple[str, ...]
    unschedulable_count: int
    no_safe_defer_count: int
    trigger_unknown_count: int
    closure_uncertain_count: int
    scheduler_conflict_count: int
    weak_wake_signal_ignored_count: int
    weak_closure_signal_ignored_count: int
    weak_reopen_signal_ignored_count: int
    threshold_edge_downgrade_count: int
    kind_policy_applied_count: int
    ledger_events: tuple[TensionLedgerEvent, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: TensionSchedulerGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class TensionSchedulerResult:
    state: TensionSchedulerState
    downstream_gate: TensionSchedulerGateDecision
    telemetry: TensionSchedulerTelemetry
    abstain: bool
    abstain_reason: str | None
    no_planner_backlog_dependency: bool
    no_retrieval_scheduler_dependency: bool
