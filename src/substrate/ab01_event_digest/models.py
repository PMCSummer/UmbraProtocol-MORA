from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AB1EventDigestKind(str, Enum):
    EFFECT_MISMATCH = "effect_mismatch"
    UNEXPECTED_BLOCK = "unexpected_block"
    INVENTORY_DELTA_MISMATCH = "inventory_delta_mismatch"
    BODY_DELTA_MISMATCH = "body_delta_mismatch"
    DELAYED_EFFECT_DETECTED = "delayed_effect_detected"
    MISSING_EXPECTED_EFFECT = "missing_expected_effect"
    ANOMALOUS_CHANGE = "anomalous_change"
    PATTERN_BREAK = "pattern_break"
    UNKNOWN_PUBLIC_ANOMALY = "unknown_public_anomaly"


class AB1DigestStatus(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    BLOCKED = "blocked"


class AB1CompressionQuality(str, Enum):
    LOSSLESS = "lossless"
    LOSSY = "lossy"


@dataclass(frozen=True, slots=True)
class AB1EventDigestInput:
    tick_ref: str
    source_refs: tuple[str, ...]
    observation_refs: tuple[str, ...]
    raw_window_refs: tuple[str, ...] = ()
    raw_window_missing_reason: str | None = None
    effect_refs: tuple[str, ...] = ()
    residue_refs: tuple[str, ...] = ()
    expected_refs: tuple[str, ...] = ()
    observed_refs: tuple[str, ...] = ()
    anomaly_markers: tuple[str, ...] = ()
    effect_status: str | None = None
    delayed_effect_ticks: int | None = None
    expected_inventory_delta: int | None = None
    observed_inventory_delta: int | None = None
    expected_body_delta: bool | None = None
    observed_body_delta: bool | None = None
    magnitude: float = 0.0
    noise_level: float = 0.0
    compression_method: str = "ab1_public_event_digest_v1"
    compression_quality: AB1CompressionQuality = AB1CompressionQuality.LOSSLESS
    prediction_error_signal: float | None = None
    efference_mismatch_present: bool = False
    public_only: bool = True
    hidden_eval_excluded: bool = True
    scenario_label_excluded: bool = True
    source: str = "ab01_event_digest_input"


@dataclass(frozen=True, slots=True)
class AB1EventDigest:
    event_id: str
    event_kind: AB1EventDigestKind
    source_refs: tuple[str, ...]
    observation_refs: tuple[str, ...]
    raw_window_refs: tuple[str, ...]
    raw_window_missing_reason: str | None
    effect_refs: tuple[str, ...]
    residue_refs: tuple[str, ...]
    expected_refs: tuple[str, ...]
    observed_refs: tuple[str, ...]
    magnitude: float
    direction: int | None
    confidence: float
    uncertainty: float
    compression_method: str
    compression_quality: AB1CompressionQuality
    digest_status: AB1DigestStatus
    lossiness: bool
    explicit_non_causal_closure: bool = True
    cause_claimed: bool = False
    hidden_eval_used: bool = False
    scenario_label_used: bool = False
    blocked_status: bool = False
    weak_status: bool = False


@dataclass(frozen=True, slots=True)
class AB1ScopeMarker:
    scope: str
    event_digest_only: bool
    no_hypothesis_authority: bool
    no_action_candidate_authority: bool
    no_ap01_request_authority: bool
    no_execution_authority: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AB1Telemetry:
    tick_ref: str
    digest_count: int
    strong_count: int
    weak_count: int
    blocked_count: int
    unsafe_basis_count: int
    no_digest_count: int
    hidden_eval_excluded: bool
    scenario_label_excluded: bool
    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class AB1EventDigestResult:
    tick_ref: str
    digests: tuple[AB1EventDigest, ...]
    telemetry: AB1Telemetry
    scope_marker: AB1ScopeMarker
    reason_codes: tuple[str, ...]
    source_lineage: tuple[str, ...]
