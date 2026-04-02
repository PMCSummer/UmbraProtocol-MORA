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


class LexicalConflictState(str, Enum):
    NONE = "none"
    SENSE_CONFLICT = "sense_conflict"
    ENTRY_CONFLICT = "entry_conflict"
    EVIDENCE_CONFLICT = "evidence_conflict"


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


@dataclass(frozen=True, slots=True)
class LexicalEntryProposal:
    surface_form: str
    canonical_form: str | None
    language_code: str
    part_of_speech_candidates: tuple[str, ...]
    sense_hypotheses: tuple[LexicalSenseHypothesis, ...]
    composition_profile: LexicalCompositionProfile | None = None
    reference_profile: LexicalReferenceProfile | None = None
    confidence: float = 0.5
    evidence_ref: str = ""
    conflict_hint: bool = False


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


@dataclass(frozen=True, slots=True)
class LexiconGateDecision:
    accepted: bool
    restrictions: tuple[str, ...]
    reason: str
    accepted_entry_ids: tuple[str, ...]
    rejected_entry_ids: tuple[str, ...]
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
    downstream_gate: LexiconGateDecision
    attempted_paths: tuple[str, ...]
    causal_basis: str
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
class LexiconQueryResult:
    query_records: tuple[LexiconQueryRecord, ...]
    state: LexiconState
    downstream_gate: LexiconGateDecision
    telemetry: LexicalTelemetry
    no_final_meaning_resolution_performed: bool
    abstain: bool
    abstain_reason: str | None
