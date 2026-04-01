from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SourceClass(str, Enum):
    SENSOR = "sensor"
    REPORTER = "reporter"
    RECALL_AGENT = "recall_agent"
    INFERENCE_ENGINE = "inference_engine"
    ASSUMPTIVE = "assumptive"
    UNKNOWN = "unknown"


class ModalityClass(str, Enum):
    SENSOR_STREAM = "sensor_stream"
    USER_TEXT = "user_text"
    MEMORY_TRACE = "memory_trace"
    DERIVATION_NOTE = "derivation_note"
    HYPOTHETICAL_NOTE = "hypothetical_note"
    UNSPECIFIED = "unspecified"


class EpistemicStatus(str, Enum):
    OBSERVATION = "observation"
    REPORT = "report"
    RECALL = "recall"
    INFERENCE = "inference"
    ASSUMPTION = "assumption"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClaimPolarity(str, Enum):
    AFFIRM = "affirm"
    DENY = "deny"
    UNSPECIFIED = "unspecified"


@dataclass(frozen=True, slots=True)
class InputMaterial:
    material_id: str
    content: str


@dataclass(frozen=True, slots=True)
class SupportMarker:
    basis: str
    evidence_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ContestationMarker:
    reason: str
    contested_by: str | None = None


@dataclass(frozen=True, slots=True)
class ConflictMarker:
    conflicting_unit_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class UnknownMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class AbstentionMarker:
    reason: str


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    source_id: str | None
    source_class: SourceClass | None = None
    modality: ModalityClass | None = None
    confidence_hint: ConfidenceLevel | None = None
    support_note: str | None = None
    contestation_note: str | None = None
    claim_key: str | None = None
    claim_polarity: ClaimPolarity = ClaimPolarity.UNSPECIFIED


@dataclass(frozen=True, slots=True)
class EpistemicUnit:
    unit_id: str
    material_id: str
    content: str
    source_id: str
    source_class: SourceClass
    modality: ModalityClass
    status: EpistemicStatus
    confidence: ConfidenceLevel
    support: SupportMarker | None = None
    contestation: ContestationMarker | None = None
    conflict: ConflictMarker | None = None
    unknown: UnknownMarker | None = None
    abstention: AbstentionMarker | None = None
    claim_key: str | None = None
    claim_polarity: ClaimPolarity = ClaimPolarity.UNSPECIFIED
    classification_basis: str = ""
    grounded_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


@dataclass(frozen=True, slots=True)
class GroundingContext:
    existing_units: tuple[EpistemicUnit, ...] = ()
    require_observation: bool = False


@dataclass(frozen=True, slots=True)
class DownstreamAllowance:
    can_treat_as_observation: bool
    should_abstain: bool
    claim_strength: str
    restrictions: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class GroundingTelemetry:
    material_id: str
    material_content: str
    source_class: SourceClass
    modality: ModalityClass
    status: EpistemicStatus
    confidence: ConfidenceLevel
    attempted_paths: tuple[str, ...]
    support_basis: str | None
    contestation_reason: str | None
    conflict_reason: str | None
    unknown_reason: str | None
    abstain_reason: str | None
    classification_basis: str
    downstream_claim_strength: str
    downstream_restrictions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EpistemicResult:
    unit: EpistemicUnit
    allowance: DownstreamAllowance
    telemetry: GroundingTelemetry
