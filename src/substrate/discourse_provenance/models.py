from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AssertionMode(str, Enum):
    DIRECT_CURRENT_COMMITMENT = "direct_current_commitment"
    REPORTED_EXTERNAL_COMMITMENT = "reported_external_commitment"
    QUOTED_EXTERNAL_CONTENT = "quoted_external_content"
    ATTRIBUTED_BELIEF = "attributed_belief"
    REMEMBERED_CONTENT = "remembered_content"
    HYPOTHETICAL_BRANCH = "hypothetical_branch"
    QUESTION_FRAME = "question_frame"
    DENIAL_FRAME = "denial_frame"
    IRONIC_META_PERSPECTIVE_CANDIDATE = "ironic_meta_perspective_candidate"
    MIXED = "mixed"
    UNRESOLVED = "unresolved"


class PerspectiveSourceClass(str, Enum):
    CURRENT_UTTERER = "current_utterer"
    REPORTED_SOURCE = "reported_source"
    QUOTED_SPEAKER = "quoted_speaker"
    BELIEVER = "believer"
    NARRATOR = "narrator"
    REMEMBERER = "rememberer"
    IMAGINER = "imaginer"
    QUESTIONER = "questioner"
    DENIER = "denier"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PerspectiveOwnerClass(str, Enum):
    CURRENT_UTTERER = "current_utterer"
    EXTERNAL_OWNER = "external_owner"
    MIXED_OWNER = "mixed_owner"
    UNRESOLVED_OWNER = "unresolved_owner"


class CrossTurnAttachmentState(str, Enum):
    STABLE = "stable"
    REATTACHED = "reattached"
    REPAIR_PENDING = "repair_pending"
    UNKNOWN = "unknown"


class ProvenanceUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class PerspectiveChainRecord:
    chain_id: str
    proposition_id: str
    semantic_unit_id: str | None
    discourse_level: int
    current_anchor: str
    provenance_path: tuple[str, ...]
    perspective_stack: tuple[str, ...]
    commitment_owner: PerspectiveOwnerClass
    perspective_owner: PerspectiveOwnerClass
    assertion_mode: AssertionMode
    source_class: PerspectiveSourceClass
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class CommitmentLineageRecord:
    lineage_id: str
    proposition_id: str
    commitment_owner: PerspectiveOwnerClass
    ownership_conflict: bool
    lineage_path: tuple[str, ...]
    downstream_constraints: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class PerspectiveWrappedProposition:
    wrapper_id: str
    proposition_id: str
    semantic_unit_id: str | None
    commitment_owner: PerspectiveOwnerClass
    perspective_owner: PerspectiveOwnerClass
    assertion_mode: AssertionMode
    source_class: PerspectiveSourceClass
    discourse_level: int
    provenance_path: tuple[str, ...]
    perspective_stack: tuple[str, ...]
    downstream_constraints: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class CrossTurnProvenanceLink:
    link_id: str
    chain_id: str
    previous_anchor: str | None
    current_anchor: str
    attachment_state: CrossTurnAttachmentState
    repair_reason: str | None
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class PerspectiveChainBundle:
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_proposition_ids: tuple[str, ...]
    linked_semantic_unit_ids: tuple[str, ...]
    chain_records: tuple[PerspectiveChainRecord, ...]
    commitment_lineages: tuple[CommitmentLineageRecord, ...]
    wrapped_propositions: tuple[PerspectiveWrappedProposition, ...]
    cross_turn_links: tuple[CrossTurnProvenanceLink, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    no_truth_upgrade: bool
    reason: str


@dataclass(frozen=True, slots=True)
class PerspectiveChainGateDecision:
    accepted: bool
    usability_class: ProvenanceUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_chain_ids: tuple[str, ...]
    rejected_chain_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class PerspectiveChainTelemetry:
    source_lineage: tuple[str, ...]
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    chain_record_count: int
    commitment_lineage_count: int
    wrapped_proposition_count: int
    cross_turn_link_count: int
    assertion_modes: tuple[str, ...]
    source_classes: tuple[str, ...]
    perspective_owners: tuple[str, ...]
    commitment_owners: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: PerspectiveChainGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class PerspectiveChainResult:
    bundle: PerspectiveChainBundle
    telemetry: PerspectiveChainTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_truth_upgrade: bool
