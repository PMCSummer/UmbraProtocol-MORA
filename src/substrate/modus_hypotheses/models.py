from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, StrEnum


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


class L05RestrictionCode(StrEnum):
    L05_OBJECT_PRESENCE_NOT_LAWFUL_RESOLUTION = "l05_object_presence_not_lawful_resolution"
    DICTUM_NOT_EQUAL_FORCE = "dictum_not_equal_force"
    LIKELY_ILLOCUTION_NOT_SETTLED_INTENT = "likely_illocution_not_settled_intent"
    ACCEPTED_HYPOTHESIS_NOT_SETTLED_INTENT = "accepted_hypothesis_not_settled_intent"
    QUOTED_FORCE_NOT_CURRENT_COMMITMENT = "quoted_force_not_current_commitment"
    ADDRESSIVITY_NOT_SELF_APPLICABILITY = "addressivity_not_self_applicability"
    PUNCTUATION_FORM_NOT_LAWFUL_FORCE_RESOLUTION = (
        "punctuation_form_not_lawful_force_resolution"
    )
    ILLOCUTION_ALTERNATIVES_MUST_BE_READ = "illocution_alternatives_must_be_read"
    UNCERTAINTY_ENTROPY_MUST_BE_READ = "uncertainty_entropy_must_be_read"
    MODALITY_PROFILE_MUST_BE_READ = "modality_profile_must_be_read"
    EVIDENTIALITY_PROFILE_MUST_BE_READ = "evidentiality_profile_must_be_read"
    ADDRESSIVITY_HYPOTHESES_MUST_BE_READ = "addressivity_hypotheses_must_be_read"
    DOWNSTREAM_CAUTIONS_MUST_BE_READ = "downstream_cautions_must_be_read"
    L05_OUTPUT_NOT_L06_UPDATE = "l05_output_not_l06_update"
    L05_OUTPUT_NOT_REPAIR_PLAN = "l05_output_not_repair_plan"
    NO_FINAL_INTENT_SELECTION = "no_final_intent_selection"
    NO_COMMON_GROUND_UPDATE = "no_common_ground_update"
    NO_REPAIR_PLANNING = "no_repair_planning"
    SINGLE_LABEL_FORCE_COLLAPSE_DETECTED = "single_label_force_collapse_detected"
    ILLOCUTION_WEIGHT_SHAPE_VIOLATION = "illocution_weight_shape_violation"
    ADDRESSIVITY_HYPOTHESIS_GAP_DETECTED = "addressivity_hypothesis_gap_detected"
    QUOTED_FORCE_COMMITMENT_LEAK_DETECTED = "quoted_force_commitment_leak_detected"
    ENTROPY_CONTRACT_GAP_DETECTED = "entropy_contract_gap_detected"
    DOWNSTREAM_CAUTIONS_CONTRACT_GAP_DETECTED = (
        "downstream_cautions_contract_gap_detected"
    )
    EVIDENCE_FACTORIZATION_GAP_DETECTED = "evidence_factorization_gap_detected"
    UNRESOLVED_SLOT_PRESSURE_MUST_BE_READ = "unresolved_slot_pressure_must_be_read"
    L06_DOWNSTREAM_NOT_BOUND_HERE = "l06_downstream_not_bound_here"
    L06_UPDATE_CONSUMER_NOT_WIRED_HERE = "l06_update_consumer_not_wired_here"
    L06_REPAIR_CONSUMER_NOT_WIRED_HERE = "l06_repair_consumer_not_wired_here"
    LEGACY_L04_G01_SHORTCUT_OPERATIONAL_DEBT = (
        "legacy_l04_g01_shortcut_operational_debt"
    )
    LEGACY_SHORTCUT_BYPASS_RISK = "legacy_shortcut_bypass_risk"
    LEGACY_SHORTCUT_BYPASS_FORBIDDEN = "legacy_shortcut_bypass_forbidden"
    NO_USABLE_L05_RECORDS = "no_usable_l05_records"
    DOWNSTREAM_AUTHORITY_DEGRADED = "downstream_authority_degraded"
    DEGRADED_L05_REQUIRES_RESTRICTIONS_READ = (
        "degraded_l05_requires_restrictions_read"
    )


class L05CautionCode(StrEnum):
    LIKELY_ILLOCUTION_NOT_SETTLED_INTENT = "likely_illocution_not_settled_intent"
    ADDRESSIVITY_NOT_SELF_APPLICABILITY = "addressivity_not_self_applicability"
    DICTUM_NOT_EQUAL_FORCE = "dictum_not_equal_force"
    FORCE_ALTERNATIVES_MUST_BE_READ = "force_alternatives_must_be_read"
    QUOTED_FORCE_NOT_CURRENT_COMMITMENT = "quoted_force_not_current_commitment"
    ADDRESSIVITY_TARGET_UNRESOLVED = "addressivity_target_unresolved"


class L05CoverageCode(StrEnum):
    ABSTAIN = "abstain"
    L06_DOWNSTREAM_NOT_BOUND_HERE = "l06_downstream_not_bound_here"
    L06_UPDATE_CONSUMER_NOT_WIRED_HERE = "l06_update_consumer_not_wired_here"
    L06_REPAIR_CONSUMER_NOT_WIRED_HERE = "l06_repair_consumer_not_wired_here"
    LEGACY_L04_G01_SHORTCUT_OPERATIONAL_DEBT = (
        "legacy_l04_g01_shortcut_operational_debt"
    )
    LEGACY_SHORTCUT_BYPASS_RISK = "legacy_shortcut_bypass_risk"


class ModusEvidenceKind(StrEnum):
    FORCE_CUE = "force_cue"
    ADDRESSIVITY_CUE = "addressivity_cue"
    QUOTATION_CUE = "quotation_cue"
    MODALITY_CUE = "modality_cue"
    SCOPE_CUE = "scope_cue"
    POLARITY_CUE = "polarity_cue"
    UNRESOLVED_SLOT_CUE = "unresolved_slot_cue"


@dataclass(frozen=True, slots=True)
class ModusEvidenceRecord:
    evidence_id: str
    source_dictum_candidate_id: str
    evidence_kind: ModusEvidenceKind
    source_ref_ids: tuple[str, ...]
    supports_dimensions: tuple[str, ...]
    unresolved: bool
    reason: str


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
    evidence_records: tuple[ModusEvidenceRecord, ...]
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
