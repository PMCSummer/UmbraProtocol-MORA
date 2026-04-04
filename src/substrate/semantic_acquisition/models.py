from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AcquisitionStatus(str, Enum):
    STABLE_PROVISIONAL = "stable_provisional"
    WEAK_PROVISIONAL = "weak_provisional"
    COMPETING_PROVISIONAL = "competing_provisional"
    BLOCKED_PENDING_CLARIFICATION = "blocked_pending_clarification"
    CONTEXT_ONLY = "context_only"
    DISCARDED_AS_INCOHERENT = "discarded_as_incoherent"


class StabilityClass(str, Enum):
    STABLE = "stable"
    WEAK = "weak"
    COMPETING = "competing"
    BLOCKED = "blocked"
    CONTEXT_ONLY = "context_only"
    INCOHERENT = "incoherent"


class RevisionConditionKind(str, Enum):
    REOPEN_ON_CORRECTION = "reopen_on_correction"
    REOPEN_ON_QUOTE_REPAIR = "reopen_on_quote_repair"
    REOPEN_ON_TARGET_REBINDING = "reopen_on_target_rebinding"
    REOPEN_ON_TEMPORAL_DISAMBIGUATION = "reopen_on_temporal_disambiguation"
    REOPEN_ON_CLARIFICATION_ANSWER = "reopen_on_clarification_answer"
    REOPEN_ON_STRONGER_BINDING_EVIDENCE = "reopen_on_stronger_binding_evidence"


class AcquisitionUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class SupportConflictProfile:
    support_score: float
    conflict_score: float
    support_reasons: tuple[str, ...]
    conflict_reasons: tuple[str, ...]
    unresolved_slots: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RevisionCondition:
    condition_id: str
    condition_kind: RevisionConditionKind
    trigger_reason: str
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class ProvisionalAcquisitionRecord:
    acquisition_id: str
    proposition_id: str
    semantic_unit_id: str | None
    acquisition_status: AcquisitionStatus
    stability_class: StabilityClass
    support_conflict_profile: SupportConflictProfile
    revision_conditions: tuple[RevisionCondition, ...]
    downstream_permissions: tuple[str, ...]
    cluster_id: str
    compatible_acquisition_ids: tuple[str, ...]
    competing_acquisition_ids: tuple[str, ...]
    blocked_reason: str | None
    context_anchor: str
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class AcquisitionClusterLink:
    cluster_id: str
    member_acquisition_ids: tuple[str, ...]
    compatible_member_ids: tuple[str, ...]
    competing_member_ids: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class SemanticAcquisitionBundle:
    source_perspective_chain_ref: str
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_proposition_ids: tuple[str, ...]
    linked_semantic_unit_ids: tuple[str, ...]
    acquisition_records: tuple[ProvisionalAcquisitionRecord, ...]
    cluster_links: tuple[AcquisitionClusterLink, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    no_final_semantic_closure: bool
    reason: str


@dataclass(frozen=True, slots=True)
class SemanticAcquisitionGateDecision:
    accepted: bool
    usability_class: AcquisitionUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_acquisition_ids: tuple[str, ...]
    rejected_acquisition_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class SemanticAcquisitionTelemetry:
    source_lineage: tuple[str, ...]
    source_perspective_chain_ref: str
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    acquisition_record_count: int
    cluster_link_count: int
    acquisition_statuses: tuple[str, ...]
    stability_classes: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    attempted_paths: tuple[str, ...]
    downstream_gate: SemanticAcquisitionGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class SemanticAcquisitionResult:
    bundle: SemanticAcquisitionBundle
    telemetry: SemanticAcquisitionTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_semantic_closure: bool
