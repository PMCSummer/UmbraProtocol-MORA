from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ResourceKind(str, Enum):
    FOOD = "food"
    WATER = "water"


class ResourceLevel(str, Enum):
    DEFICIT = "deficit"
    SUFFICIENT = "sufficient"
    SURPLUS = "surplus"
    UNKNOWN = "unknown"


class CounterpartSignalKind(str, Enum):
    PRESENCE_PING = "presence_ping"
    RESOURCE_STATUS_CLAIM = "resource_status_signal"
    ITEM_SEEN_AT_APERTURE = "object_seen_at_aperture"
    TRANSFER_ATTEMPT = "object_transfer_attempt"
    TRANSFER_RESULT = "object_transfer_result"
    ABSENCE = "absence_signal"
    BLOCKED = "blocked_signal"
    CONTRADICTION = "contradiction_signal"


class SignalAuthority(str, Enum):
    HARNESS_TRUTH = "harness_truth"
    COUNTERPART_CLAIM = "counterpart_claim"
    OBSERVED_EVENT = "observed_event"
    INFERRED_BY_HARNESS_FOR_EVAL_ONLY = "inferred_by_harness_for_eval_only"


class ApertureState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    NOISY = "noisy"
    BLOCKED = "blocked"


class TransferOutcome(str, Enum):
    NOT_ATTEMPTED = "not_attempted"
    SUCCEEDED = "succeeded"
    FAILED_BLOCKED = "failed_blocked"
    FAILED_UNKNOWN = "failed_unknown"
    CONTRADICTED = "contradicted"


class ScenarioStage(str, Enum):
    STAGE_0_PACKET_DRY_RUN = "stage_0_packet_dry_run"
    STAGE_1_SCRIPTED_COUNTERPART = "stage_1_scripted_counterpart"


@dataclass(frozen=True, slots=True)
class ResourceInventoryTruth:
    actor_id: str
    resource_levels: dict[ResourceKind, ResourceLevel]
    hidden_from_subject: bool = True


@dataclass(frozen=True, slots=True)
class CounterpartEmission:
    emission_id: str
    source_actor_id: str
    signal_kind: CounterpartSignalKind
    resource_kind: ResourceKind | None
    reported_level: ResourceLevel | None
    item_kind: ResourceKind | None
    aperture_state: ApertureState
    source_authority: SignalAuthority
    emitted_at_step: int
    provenance_ref: tuple[str, ...]
    visible_to_subject: bool
    eval_truth_ref: str | None = None
    transfer_outcome: TransferOutcome = TransferOutcome.NOT_ATTEMPTED
    notes: str = ""


@dataclass(frozen=True, slots=True)
class SubjectVisiblePacket:
    packet_id: str
    source_id: str
    source_authority: SignalAuthority
    signal_kind: CounterpartSignalKind
    resource_kind: ResourceKind | None
    reported_level: ResourceLevel | None
    aperture_state: ApertureState
    timestamp_or_step: int
    provenance_ref: tuple[str, ...]
    hidden_truth_excluded: bool
    claim_not_fact_marker: bool
    transfer_outcome: TransferOutcome = TransferOutcome.NOT_ATTEMPTED
    item_kind: ResourceKind | None = None


@dataclass(frozen=True, slots=True)
class ScenarioStep:
    step_index: int
    scripted_b_emission: CounterpartEmission | None
    subject_visible_packets: tuple[SubjectVisiblePacket, ...]
    harness_truth_snapshot_ref: str
    expected_phase_obligations: tuple[str, ...]
    eval_only_success_labels: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FalsifierResult:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_id: str
    stage: ScenarioStage
    steps: tuple[ScenarioStep, ...]
    emitted_packets: tuple[SubjectVisiblePacket, ...]
    phase_obligation_summary: tuple[str, ...]
    falsifier_results: tuple[FalsifierResult, ...]
    trace_summary: dict[str, object]
    success_labels: tuple[str, ...]
    claim_discipline_markers: tuple[str, ...]
    eval_only: dict[str, object] = field(default_factory=dict)
