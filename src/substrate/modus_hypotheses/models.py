from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class IllocutionKind(str, Enum):
    ASSERTIVE_CANDIDATE = "assertive_candidate"
    INTERROGATIVE_CANDIDATE = "interrogative_candidate"
    DIRECTIVE_CANDIDATE = "directive_candidate"
    COMMISSIVE_CANDIDATE = "commissive_candidate"
    EXPRESSIVE_CANDIDATE = "expressive_candidate"
    REPORTED_FORCE_CANDIDATE = "reported_force_candidate"
    QUOTED_FORCE_CANDIDATE = "quoted_force_candidate"
    ECHOIC_FORCE_CANDIDATE = "echoic_force_candidate"
    UNKNOWN_FORCE_CANDIDATE = "unknown_force_candidate"


class EvidentialityState(str, Enum):
    DIRECT = "direct"
    REPORTED = "reported"
    QUOTED = "quoted"
    MIXED = "mixed"
    UNRESOLVED = "unresolved"


class AddressivityKind(str, Enum):
    CURRENT_INTERLOCUTOR = "current_interlocutor"
    REPORTED_PARTICIPANT = "reported_participant"
    QUOTED_SPEAKER = "quoted_speaker"
    UNSPECIFIED_AUDIENCE = "unspecified_audience"
    UNKNOWN_TARGET = "unknown_target"


class ModusUsabilityClass(str, Enum):
    USABLE_BOUNDED = "usable_bounded"
    DEGRADED_BOUNDED = "degraded_bounded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class IllocutionHypothesis:
    hypothesis_id: str
    illocution_kind: IllocutionKind
    confidence_weight: float
    evidence_refs: tuple[str, ...]
    unresolved: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ModalityEvidentialityProfile:
    profile_id: str
    modality_markers: tuple[str, ...]
    evidentiality_state: EvidentialityState
    stance_carriers: tuple[str, ...]
    polarity_packaging: str
    unresolved: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AddressivityHypothesis:
    hypothesis_id: str
    addressivity_kind: AddressivityKind
    target_refs: tuple[str, ...]
    confidence_weight: float
    quoted_or_echo_bound: bool
    unresolved: bool
    reason: str


@dataclass(frozen=True, slots=True)
class QuotedSpeechState:
    quote_or_echo_present: bool
    reported_force_candidate_present: bool
    quoted_force_not_current_commitment: bool
    commitment_transfer_forbidden: bool
    unresolved_source_scope: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ModusHypothesisRecord:
    record_id: str
    source_dictum_candidate_id: str
    illocution_hypotheses: tuple[IllocutionHypothesis, ...]
    modality_profile: ModalityEvidentialityProfile
    addressivity_hypotheses: tuple[AddressivityHypothesis, ...]
    quoted_speech_state: QuotedSpeechState
    uncertainty_entropy: float
    uncertainty_markers: tuple[str, ...]
    downstream_cautions: tuple[str, ...]
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class ModusHypothesisBundle:
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    linked_dictum_candidate_ids: tuple[str, ...]
    hypothesis_records: tuple[ModusHypothesisRecord, ...]
    ambiguity_reasons: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    l06_downstream_not_bound_here: bool
    l06_update_consumer_not_wired_here: bool
    l06_repair_consumer_not_wired_here: bool
    legacy_l04_g01_shortcut_operational_debt: bool
    legacy_shortcut_bypass_risk: bool
    downstream_authority_degraded: bool
    no_final_intent_selection: bool
    no_common_ground_update: bool
    no_repair_planning: bool
    no_psychologizing: bool
    no_commitment_transfer_from_quote: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ModusHypothesisGateDecision:
    accepted: bool
    usability_class: ModusUsabilityClass
    restrictions: tuple[str, ...]
    reason: str
    accepted_record_ids: tuple[str, ...]
    rejected_record_ids: tuple[str, ...]
    bundle_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ModusHypothesisTelemetry:
    source_lineage: tuple[str, ...]
    source_dictum_ref: str
    source_syntax_ref: str
    source_surface_ref: str | None
    hypothesis_record_count: int
    illocution_classes: tuple[str, ...]
    evidentiality_states: tuple[str, ...]
    addressivity_classes: tuple[str, ...]
    low_coverage_mode: bool
    low_coverage_reasons: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    l06_downstream_not_bound_here: bool
    l06_update_consumer_not_wired_here: bool
    l06_repair_consumer_not_wired_here: bool
    legacy_l04_g01_shortcut_operational_debt: bool
    legacy_shortcut_bypass_risk: bool
    attempted_paths: tuple[str, ...]
    downstream_gate: ModusHypothesisGateDecision
    causal_basis: str
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ModusHypothesisResult:
    bundle: ModusHypothesisBundle
    telemetry: ModusHypothesisTelemetry
    confidence: float
    partial_known: bool
    partial_known_reason: str | None
    abstain: bool
    abstain_reason: str | None
    no_final_intent_selection: bool
