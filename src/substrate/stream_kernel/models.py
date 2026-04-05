from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


class StreamLinkDecision(str, Enum):
    CONTINUED_EXISTING_STREAM = "continued_existing_stream"
    STARTED_NEW_STREAM = "started_new_stream"
    RESUMED_INTERRUPTED_STREAM = "resumed_interrupted_stream"
    OPENED_BRANCH = "opened_branch"
    FORCED_RELEASE = "forced_release"
    AMBIGUOUS_LINK = "ambiguous_link"
    LOW_CONFIDENCE_CONTINUATION = "low_confidence_continuation"
    FORCED_NEW_STREAM = "forced_new_stream"


class StreamInterruptionStatus(str, Enum):
    NONE = "none"
    INTERRUPTED = "interrupted"
    RESUMED = "resumed"


class StreamBranchStatus(str, Enum):
    NONE = "none"
    BRANCH_OPENED = "branch_opened"
    BRANCH_CONFLICT = "branch_conflict"


class StreamDecayState(str, Enum):
    NONE = "none"
    DECAYING = "decaying"
    STALE = "stale"
    RELEASED = "released"


class CarryoverClass(str, Enum):
    SURVIVAL_VIABILITY_ANCHOR = "survival_viability_anchor"
    UNRESOLVED_OPERATIONAL_PROCESS = "unresolved_operational_process"
    HELD_FOCUS_ANCHOR = "held_focus_anchor"
    PENDING_OUTPUT_OR_RECOVERY = "pending_output_or_recovery"
    INTERRUPTION_MARKER = "interruption_marker"


class StreamKernelUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class C01RestrictionCode(StrEnum):
    STREAM_STATE_MUST_BE_READ = "stream_state_must_be_read"
    CARRYOVER_ITEMS_MUST_BE_READ = "carryover_items_must_be_read"
    UNRESOLVED_ANCHORS_MUST_BE_READ = "unresolved_anchors_must_be_read"
    PENDING_OPERATIONS_MUST_BE_READ = "pending_operations_must_be_read"
    INTERRUPTION_STATUS_MUST_BE_READ = "interruption_status_must_be_read"
    BRANCH_STATUS_MUST_BE_READ = "branch_status_must_be_read"
    DECAY_STATE_MUST_BE_READ = "decay_state_must_be_read"
    STALE_MARKERS_MUST_BE_READ = "stale_markers_must_be_read"
    AMBIGUOUS_LINK_MUST_NOT_BE_LAUNDERED = "ambiguous_link_must_not_be_laundered"
    LOW_CONFIDENCE_CONTINUATION_MUST_BE_READ = (
        "low_confidence_continuation_must_be_read"
    )
    FORCED_NEW_STREAM_MUST_BE_READ = "forced_new_stream_must_be_read"
    FORCED_RELEASE_MUST_BE_READ = "forced_release_must_be_read"
    CONTINUITY_NOT_TRANSCRIPT_REPLAY = "continuity_not_transcript_replay"
    CONTINUITY_NOT_MEMORY_RETRIEVAL = "continuity_not_memory_retrieval"
    CONTINUITY_NOT_PLANNER_HIDDEN_FLAG = "continuity_not_planner_hidden_flag"
    STREAM_OBJECT_PRESENCE_NOT_CONTINUITY = "stream_object_presence_not_continuity"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"


class StreamLedgerEventKind(str, Enum):
    RETAIN = "retain"
    NEW_STREAM = "new_stream"
    RESUME = "resume"
    INTERRUPT = "interrupt"
    BRANCH = "branch"
    DECAY = "decay"
    STALE = "stale"
    RELEASE = "release"


@dataclass(frozen=True, slots=True)
class StreamCarryoverItem:
    item_id: str
    carryover_class: CarryoverClass
    anchor_key: str
    source_ref: str
    strength: float
    created_sequence_index: int
    last_seen_sequence_index: int
    decay_steps: int
    stale: bool
    provisional: bool
    released: bool
    reason: str


@dataclass(frozen=True, slots=True)
class StreamLedgerEvent:
    event_id: str
    event_kind: StreamLedgerEventKind
    stream_id: str
    item_id: str | None
    anchor_key: str | None
    reason: str
    reason_code: str
    provenance: str


@dataclass(frozen=True, slots=True)
class StreamKernelState:
    stream_id: str
    sequence_index: int
    link_decision: StreamLinkDecision
    carryover_items: tuple[StreamCarryoverItem, ...]
    unresolved_anchors: tuple[str, ...]
    pending_operations: tuple[str, ...]
    interruption_status: StreamInterruptionStatus
    branch_status: StreamBranchStatus
    decay_state: StreamDecayState
    stale_markers: tuple[str, ...]
    continuity_confidence: float
    source_regulation_ref: str
    source_affordance_ref: str
    source_preference_ref: str
    source_viability_ref: str
    source_lineage: tuple[str, ...]
    last_update_provenance: str


@dataclass(frozen=True, slots=True)
class StreamKernelContext:
    prior_stream_state: StreamKernelState | None = None
    source_lineage: tuple[str, ...] = ()
    step_delta: int = 1
    interruption_signal: bool = False
    resume_signal: bool = False
    force_new_stream: bool = False
    allow_branch_opening: bool = True
    require_strong_link: bool = False
    stale_after_steps: int = 2
    release_after_steps: int = 4
    disable_anchor_linking: bool = False
    expected_schema_version: str = "c01.stream.v1"


@dataclass(frozen=True, slots=True)
class StreamKernelGateDecision:
    accepted: bool
    usability_class: StreamKernelUsabilityClass
    restrictions: tuple[C01RestrictionCode, ...]
    reason: str
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class StreamKernelTelemetry:
    source_lineage: tuple[str, ...]
    stream_id: str
    sequence_index: int
    link_decision: StreamLinkDecision
    carryover_count: int
    unresolved_anchor_count: int
    pending_operation_count: int
    interruption_status: StreamInterruptionStatus
    branch_status: StreamBranchStatus
    decay_state: StreamDecayState
    stale_marker_count: int
    continuity_confidence: float
    source_regulation_ref: str
    source_affordance_ref: str
    source_preference_ref: str
    source_viability_ref: str
    ledger_events: tuple[StreamLedgerEvent, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: StreamKernelGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class StreamKernelResult:
    state: StreamKernelState
    downstream_gate: StreamKernelGateDecision
    telemetry: StreamKernelTelemetry
    abstain: bool
    abstain_reason: str | None
    no_downstream_scheduler_selection_performed: bool
    no_transcript_replay_dependency: bool
    no_memory_retrieval_dependency: bool
    no_planner_hidden_flag_dependency: bool
