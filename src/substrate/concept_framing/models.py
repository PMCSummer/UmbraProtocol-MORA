from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class FrameFamily(str, Enum):
    DESCRIPTIVE_LITERAL = "descriptive_literal"
    EVALUATIVE = "evaluative"
    NORMATIVE = "normative"
    THREAT_RELEVANT = "threat_relevant"
    DEPENDENCY_RELEVANT = "dependency_relevant"
    OBLIGATION_RELEVANT = "obligation_relevant"
    IDENTITY_RELEVANT = "identity_relevant"
    EXTERNAL_CONTEXT_ONLY = "external_context_only"


class FramingStatus(str, Enum):
    DOMINANT_PROVISIONAL_FRAME = "dominant_provisional_frame"
    COMPETING_FRAMES = "competing_frames"
    UNDERFRAMED_MEANING = "underframed_meaning"
    BLOCKED_HIGH_IMPACT_FRAME = "blocked_high_impact_frame"
    CONTEXT_ONLY_FRAME_HINT = "context_only_frame_hint"
    DISCARDED_OVERREACH = "discarded_overreach"


class FramingUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


class VulnerabilityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"


class ReframingConditionKind(str, Enum):
    REOPEN_ON_CLARIFICATION_ANSWER = "reopen_on_clarification_answer"
    REOPEN_ON_CORRECTION = "reopen_on_correction"
    REOPEN_ON_QUOTE_REPAIR = "reopen_on_quote_repair"
    REOPEN_ON_TARGET_REBINDING = "reopen_on_target_rebinding"
    REOPEN_ON_TEMPORAL_DISAMBIGUATION = "reopen_on_temporal_disambiguation"
    REOPEN_ON_STRONGER_BINDING_EVIDENCE = "reopen_on_stronger_binding_evidence"
    REOPEN_ON_DISCOURSE_CONTINUATION = "reopen_on_discourse_continuation"


@dataclass(frozen=True, slots=True)
class VulnerabilityProfile:
    vulnerability_level: VulnerabilityLevel
    dimensions: tuple[str, ...]
    fragility_reasons: tuple[str, ...]
    high_impact: bool
    impact_radius: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReframingCondition:
    condition_id: str
    condition_kind: ReframingConditionKind
    trigger_reason: str
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class ConceptFramingRecord:
    framing_id: str
    acquisition_id: str
    semantic_unit_id: str | None
    frame_family: FrameFamily
    framing_status: FramingStatus
    frame_components: tuple[str, ...]
    framing_basis: tuple[str, ...]
    alternative_framings: tuple[FrameFamily, ...]
    vulnerability_profile: VulnerabilityProfile
    unresolved_dependencies: tuple[str, ...]
    reframing_conditions: tuple[ReframingCondition, ...]
    downstream_cautions: tuple[str, ...]
    downstream_permissions: tuple[str, ...]
    context_anchor: str
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class FramingCompetitionLink:
    competition_id: str
    member_framing_ids: tuple[str, ...]
    competing_framing_ids: tuple[str, ...]
    compatible_framing_ids: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class ConceptFramingBundle:
    source_acquisition_ref: str
    source_perspective_chain_ref: str
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_acquisition_ids: tuple[str, ...]
    linked_proposition_ids: tuple[str, ...]
    linked_semantic_unit_ids: tuple[str, ...]
    framing_records: tuple[ConceptFramingRecord, ...]
    competition_links: tuple[FramingCompetitionLink, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    l06_update_proposal_absent: bool
    repair_trigger_basis_incomplete: bool
    no_final_semantic_closure: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ConceptFramingGateDecision:
    accepted: bool
    usability_class: FramingUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_framing_ids: tuple[str, ...]
    rejected_framing_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ConceptFramingTelemetry:
    source_lineage: tuple[str, ...]
    source_acquisition_ref: str
    source_perspective_chain_ref: str
    source_applicability_ref: str
    source_runtime_graph_ref: str
    source_grounded_ref: str
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    framing_record_count: int
    competition_link_count: int
    frame_families: tuple[str, ...]
    framing_statuses: tuple[str, ...]
    vulnerability_levels: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    l06_update_proposal_absent: bool
    repair_trigger_basis_incomplete: bool
    attempted_paths: tuple[str, ...]
    downstream_gate: ConceptFramingGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ConceptFramingResult:
    bundle: ConceptFramingBundle
    telemetry: ConceptFramingTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_semantic_closure: bool
