from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


DEFAULT_LEXICON_SCHEMA_VERSION = "lexicon.schema.v1"
DEFAULT_LEXICON_VERSION = "lexicon.seed.v1"
DEFAULT_LEXICON_TAXONOMY_VERSION = "lexicon.taxonomy.v1"


class LexicalCoarseSemanticType(str, Enum):
    UNKNOWN = "unknown"
    ENTITY = "entity"
    EVENT = "event"
    ATTRIBUTE = "attribute"
    OPERATOR = "operator"
    DEICTIC = "deictic"
    TEMPORAL = "temporal"
    QUANTIFIER = "quantifier"
    PRONOMINAL = "pronominal"


class LexicalCompositionRole(str, Enum):
    CONTENT = "content"
    OPERATOR = "operator"
    MODIFIER = "modifier"
    PARTICIPANT = "participant"
    REFERENTIAL_CARRIER = "referential_carrier"
    UNKNOWN = "unknown"


class LexicalAcquisitionStatus(str, Enum):
    STABLE = "stable"
    PROVISIONAL = "provisional"
    UNKNOWN = "unknown"
    CONFLICTED = "conflicted"
    FROZEN = "frozen"


class LexicalAcquisitionMode(str, Enum):
    SEED = "seed"
    DIRECT_CURATION = "direct_curation"
    EPISODE_PROMOTION = "episode_promotion"
    UNKNOWN = "unknown"


class LexicalConflictState(str, Enum):
    NONE = "none"
    SENSE_CONFLICT = "sense_conflict"
    ENTRY_CONFLICT = "entry_conflict"
    EVIDENCE_CONFLICT = "evidence_conflict"


class LexicalSenseStatus(str, Enum):
    STABLE = "stable"
    PROVISIONAL = "provisional"
    UNKNOWN = "unknown"
    CONFLICTED = "conflicted"
    FROZEN = "frozen"


class LexicalExampleStatus(str, Enum):
    ILLUSTRATIVE = "illustrative"
    PROVISIONAL = "provisional"
    STABLE = "stable"
    CONFLICTED = "conflicted"


class LexicalEpisodeStatus(str, Enum):
    RECORDED = "recorded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING = "conflicting"
    CONSOLIDATED = "consolidated"
    BLOCKED = "blocked"


class LexicalUnknownClass(str, Enum):
    UNKNOWN_WORD = "unknown_word"
    PARTIAL_LEXICAL_HYPOTHESIS = "partial_lexical_hypothesis"
    KNOWN_SYNTAX_UNKNOWN_LEXEME = "known_syntax_unknown_lexeme"
    KNOWN_LEXEME_UNKNOWN_SENSE_IN_CONTEXT = "known_lexeme_unknown_sense_in_context"


class LexicalHypothesisStatus(str, Enum):
    PROVISIONAL = "provisional"
    PROMOTION_ELIGIBLE = "promotion_eligible"
    STABLE_PROMOTED = "stable_promoted"
    CONFLICTED = "conflicted"
    FROZEN = "frozen"
    UNKNOWN = "unknown"


class LexiconUpdateKind(str, Enum):
    CREATE_ENTRY = "create_entry"
    UPDATE_ENTRY = "update_entry"
    REGISTER_UNKNOWN = "register_unknown"
    REGISTER_CONFLICT = "register_conflict"
    FREEZE_UPDATE = "freeze_update"
    NO_CLAIM = "no_claim"
    DECAY = "decay"


@dataclass(frozen=True, slots=True)
class SurfaceFormRecord:
    form: str
    normalized_form: str
    locale_hint: str | None
    variant_kind: str
    confidence: float
    provenance: str


@dataclass(frozen=True, slots=True)
class LexicalExampleRecord:
    example_id: str
    example_text: str
    linked_entry_id: str
    linked_sense_id: str | None
    status: LexicalExampleStatus
    illustrative_only: bool
    provenance: str


@dataclass(frozen=True, slots=True)
class LexicalSenseRecord:
    sense_id: str
    sense_family: str
    sense_label: str
    coarse_semantic_type: LexicalCoarseSemanticType
    compatibility_cues: tuple[str, ...]
    anti_cues: tuple[str, ...]
    confidence: float
    provisional: bool
    provenance: str
    status: LexicalSenseStatus = LexicalSenseStatus.PROVISIONAL
    evidence_count: int = 1
    conflict_markers: tuple[str, ...] = ()
    example_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalCompositionProfile:
    role_hints: tuple[LexicalCompositionRole, ...]
    argument_structure_hints: tuple[str, ...]
    can_introduce_predicate_frame: bool
    behaves_as_modifier: bool
    behaves_as_operator: bool
    behaves_as_participant: bool
    behaves_as_referential_carrier: bool
    scope_sensitive: bool
    negation_sensitive: bool
    remains_underspecified: bool


@dataclass(frozen=True, slots=True)
class LexicalReferenceProfile:
    pronoun_like: bool
    deictic: bool
    entity_introducing: bool
    anaphora_prone: bool
    quote_sensitive: bool
    requires_context: bool
    can_remain_unresolved: bool


@dataclass(frozen=True, slots=True)
class LexicalAcquisitionState:
    status: LexicalAcquisitionStatus
    evidence_count: int
    last_supporting_evidence_ref: str | None
    revision_count: int
    frozen_update: bool
    staleness_steps: int
    decay_marker: float
    blocked_reason: str | None = None


@dataclass(frozen=True, slots=True)
class LexicalEntry:
    entry_id: str
    canonical_form: str
    surface_variants: tuple[SurfaceFormRecord, ...]
    language_code: str
    part_of_speech_candidates: tuple[str, ...]
    sense_records: tuple[LexicalSenseRecord, ...]
    composition_profile: LexicalCompositionProfile
    reference_profile: LexicalReferenceProfile
    acquisition_state: LexicalAcquisitionState
    confidence: float
    conflict_state: LexicalConflictState
    provenance: str
    lemma: str | None = None
    aliases: tuple[str, ...] = ()
    examples: tuple[LexicalExampleRecord, ...] = ()
    entry_status: LexicalAcquisitionStatus = LexicalAcquisitionStatus.UNKNOWN
    acquisition_mode: LexicalAcquisitionMode = LexicalAcquisitionMode.UNKNOWN
    schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    lexicon_version: str = DEFAULT_LEXICON_VERSION
    taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION


@dataclass(frozen=True, slots=True)
class UnknownLexicalItem:
    unknown_id: str
    surface_form: str
    occurrence_ref: str
    partial_pos_hint: str | None
    no_strong_meaning_claim: bool
    candidate_similarity_hints: tuple[str, ...]
    confidence: float
    provenance: str
    unknown_class: LexicalUnknownClass = LexicalUnknownClass.UNKNOWN_WORD


@dataclass(frozen=True, slots=True)
class LexiconBlockedUpdate:
    surface_form: str
    reason: str
    frozen: bool
    provenance: str
    compatibility_marker: str | None = None


@dataclass(frozen=True, slots=True)
class LexiconState:
    entries: tuple[LexicalEntry, ...]
    unknown_items: tuple[UnknownLexicalItem, ...]
    usage_episodes: tuple[LexicalUsageEpisode, ...] = ()
    provisional_hypotheses: tuple[ProvisionalLexicalHypothesis, ...] = ()
    unresolved_updates: tuple[LexiconBlockedUpdate, ...] = ()
    conflict_index: tuple[str, ...] = ()
    frozen_updates: tuple[LexiconBlockedUpdate, ...] = ()
    schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    lexicon_version: str = DEFAULT_LEXICON_VERSION
    taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION
    last_updated_step: int = 0


@dataclass(frozen=True, slots=True)
class LexicalSenseHypothesis:
    sense_family: str
    sense_label: str
    coarse_semantic_type: LexicalCoarseSemanticType
    compatibility_cues: tuple[str, ...] = ()
    anti_cues: tuple[str, ...] = ()
    confidence: float = 0.5
    provisional: bool = True
    status_hint: LexicalSenseStatus | None = None
    example_texts: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalEntryProposal:
    surface_form: str
    canonical_form: str | None
    language_code: str
    part_of_speech_candidates: tuple[str, ...]
    sense_hypotheses: tuple[LexicalSenseHypothesis, ...]
    lemma: str | None = None
    aliases: tuple[str, ...] = ()
    entry_example_texts: tuple[str, ...] = ()
    composition_profile: LexicalCompositionProfile | None = None
    reference_profile: LexicalReferenceProfile | None = None
    confidence: float = 0.5
    evidence_ref: str = ""
    conflict_hint: bool = False


@dataclass(frozen=True, slots=True)
class LexicalUsageEpisode:
    episode_id: str
    observed_surface_form: str
    observed_lemma_hint: str | None
    language_code: str
    observed_context_keys: tuple[str, ...]
    source_kind: str
    proposed_sense_hypotheses: tuple[LexicalSenseHypothesis, ...]
    proposed_role_hints: tuple[LexicalCompositionRole, ...]
    usage_span: str | None
    confidence: float
    evidence_quality: float
    step_index: int
    episode_status: LexicalEpisodeStatus
    provenance: str
    schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    lexicon_version: str = DEFAULT_LEXICON_VERSION
    taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION
    blocked_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ProvisionalLexicalHypothesis:
    hypothesis_id: str
    target_surface_form: str
    target_lemma: str | None
    language_code: str
    candidate_entry_id: str | None
    candidate_sense_bundle: tuple[LexicalSenseHypothesis, ...]
    candidate_role_hints: tuple[LexicalCompositionRole, ...]
    supporting_episode_ids: tuple[str, ...]
    conflicting_episode_ids: tuple[str, ...]
    support_count: int
    conflict_count: int
    status: LexicalHypothesisStatus
    promotion_eligibility: bool
    blocked_reasons: tuple[str, ...]
    confidence: float
    evidence_quality: float
    provenance: str
    promoted_entry_id: str | None = None
    schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    lexicon_version: str = DEFAULT_LEXICON_VERSION
    taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION


@dataclass(frozen=True, slots=True)
class UnknownLexicalObservation:
    surface_form: str
    occurrence_ref: str
    partial_pos_hint: str | None = None
    candidate_similarity_hints: tuple[str, ...] = ()
    confidence: float = 0.2
    provenance: str = ""


@dataclass(frozen=True, slots=True)
class LexiconUpdateContext:
    source_lineage: tuple[str, ...] = ()
    expected_schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    expected_lexicon_version: str = DEFAULT_LEXICON_VERSION
    expected_taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION
    step_delta: int = 1
    decay_per_step: float = 0.02
    min_evidence_for_stable: int = 3
    stable_confidence_threshold: float = 0.7
    freeze_on_conflict: bool = True
    freeze_on_ambiguous_target: bool = True
    ambiguous_target_score_margin: float = 0.2
    allow_competing_entry_on_ambiguous_target: bool = False


@dataclass(frozen=True, slots=True)
class LexicalEpisodeRecordContext:
    source_lineage: tuple[str, ...] = ()
    expected_schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    expected_lexicon_version: str = DEFAULT_LEXICON_VERSION
    expected_taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION
    min_episode_confidence: float = 0.35
    min_episode_evidence_quality: float = 0.35
    min_support_for_promotion: int = 3
    promotion_confidence_threshold: float = 0.7
    freeze_on_conflict: bool = True
    step_delta: int = 1


@dataclass(frozen=True, slots=True)
class LexicalHypothesisConsolidationContext:
    source_lineage: tuple[str, ...] = ()
    expected_schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    expected_lexicon_version: str = DEFAULT_LEXICON_VERSION
    expected_taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION
    min_support_for_promotion: int = 3
    promotion_confidence_threshold: float = 0.7
    step_delta: int = 1


@dataclass(frozen=True, slots=True)
class LexiconQueryRequest:
    surface_form: str
    language_code: str | None = None
    allow_provisional: bool = True
    include_unknown_items: bool = True


@dataclass(frozen=True, slots=True)
class LexiconQueryContext:
    source_lineage: tuple[str, ...] = ()
    expected_schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION
    expected_lexicon_version: str = DEFAULT_LEXICON_VERSION
    expected_taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION
    context_keys: tuple[str, ...] = ()
    syntax_known_lexical_gap_forms: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LexicalUnknownState:
    unknown_class: LexicalUnknownClass
    query_form: str
    entry_ids: tuple[str, ...] = ()
    hypothesis_ids: tuple[str, ...] = ()
    unknown_item_ids: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class LexiconUpdateEvent:
    event_id: str
    entry_id: str | None
    update_kind: LexiconUpdateKind
    reason_tags: tuple[str, ...]
    provenance: str


@dataclass(frozen=True, slots=True)
class LexiconQueryRecord:
    query_form: str
    matched_entry_ids: tuple[str, ...]
    matched_sense_ids: tuple[str, ...]
    unknown_item_ids: tuple[str, ...]
    context_blocked_entry_ids: tuple[str, ...]
    ambiguity_reasons: tuple[str, ...]
    no_final_meaning_resolution_performed: bool
    unknown_states: tuple[LexicalUnknownState, ...] = ()
    dominant_unknown_class: LexicalUnknownClass | None = None
    hard_unknown_or_capped: bool = False
    strong_lexical_claim_permitted: bool = False


@dataclass(frozen=True, slots=True)
class LexiconGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_entry_ids: tuple[str, ...]
    rejected_entry_ids: tuple[str, ...]
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class LexicalLearningGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_hypothesis_ids: tuple[str, ...]
    rejected_hypothesis_ids: tuple[str, ...]
    state_ref: str | None = None


@dataclass(frozen=True, slots=True)
class LexicalTelemetry:
    source_lineage: tuple[str, ...]
    processed_entry_ids: tuple[str, ...]
    new_entry_count: int
    updated_entry_count: int
    provisional_entry_count: int
    stable_entry_count: int
    unknown_item_count: int
    conflict_entry_count: int
    blocked_update_count: int
    ambiguity_reasons: tuple[str, ...]
    queried_forms: tuple[str, ...]
    matched_entry_ids: tuple[str, ...]
    no_match_count: int
    compatibility_markers: tuple[str, ...]
    downstream_gate: LexiconGateDecision | LexicalLearningGateDecision
    attempted_paths: tuple[str, ...]
    causal_basis: str
    unknown_state_classes: tuple[LexicalUnknownClass, ...] = ()
    processed_episode_ids: tuple[str, ...] = ()
    processed_hypothesis_ids: tuple[str, ...] = ()
    recorded_episode_count: int = 0
    promoted_hypothesis_count: int = 0
    conflicted_hypothesis_count: int = 0
    frozen_hypothesis_count: int = 0
    insufficient_episode_count: int = 0
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class LexiconSnapshot:
    state: LexiconState
    telemetry: LexicalTelemetry
    no_final_meaning_resolution_performed: bool
    kind: str
    abstain: bool
    abstain_reason: str | None


@dataclass(frozen=True, slots=True)
class LexiconUpdateResult:
    updated_state: LexiconState
    update_events: tuple[LexiconUpdateEvent, ...]
    blocked_updates: tuple[LexiconBlockedUpdate, ...]
    downstream_gate: LexiconGateDecision
    telemetry: LexicalTelemetry
    no_final_meaning_resolution_performed: bool
    abstain: bool
    abstain_reason: str | None


@dataclass(frozen=True, slots=True)
class LexicalEpisodeRecordResult:
    updated_state: LexiconState
    recorded_episode_ids: tuple[str, ...]
    blocked_episode_ids: tuple[str, ...]
    updated_hypothesis_ids: tuple[str, ...]
    downstream_gate: LexicalLearningGateDecision
    telemetry: LexicalTelemetry
    no_final_meaning_resolution_performed: bool
    abstain: bool
    abstain_reason: str | None


@dataclass(frozen=True, slots=True)
class LexicalHypothesisUpdateResult:
    updated_state: LexiconState
    promoted_hypothesis_ids: tuple[str, ...]
    frozen_hypothesis_ids: tuple[str, ...]
    conflicted_hypothesis_ids: tuple[str, ...]
    downstream_gate: LexicalLearningGateDecision
    telemetry: LexicalTelemetry
    no_final_meaning_resolution_performed: bool
    abstain: bool
    abstain_reason: str | None


@dataclass(frozen=True, slots=True)
class LexiconQueryResult:
    query_records: tuple[LexiconQueryRecord, ...]
    state: LexiconState
    downstream_gate: LexiconGateDecision
    telemetry: LexicalTelemetry
    no_final_meaning_resolution_performed: bool
    abstain: bool
    abstain_reason: str | None
