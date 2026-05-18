from __future__ import annotations

from .models import (
    AB1CompressionQuality,
    AB1DigestStatus,
    AB1EventDigest,
    AB1EventDigestInput,
    AB1EventDigestKind,
    AB1EventDigestResult,
    AB1ScopeMarker,
)
from .telemetry import build_ab1_telemetry

_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "test_label",
    "hidden",
    "eval",
    "private",
)


def build_ab1_event_digests(candidate_input: AB1EventDigestInput) -> AB1EventDigestResult:
    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    if unsafe_reasons:
        digests: tuple[AB1EventDigest, ...] = ()
    else:
        digest = _build_single_digest(candidate_input)
        digests = (digest,) if digest is not None else ()

    telemetry = build_ab1_telemetry(
        candidate_input=candidate_input,
        digests=digests,
        unsafe_basis_count=len(unsafe_reasons),
    )
    scope_marker = AB1ScopeMarker(
        scope="ab01_event_digest_anomaly_compression",
        event_digest_only=True,
        no_hypothesis_authority=True,
        no_action_candidate_authority=True,
        no_ap01_request_authority=True,
        no_execution_authority=True,
        reason="ab1 emits bounded event digests without causal closure or action authority",
    )
    return AB1EventDigestResult(
        tick_ref=candidate_input.tick_ref,
        digests=digests,
        telemetry=telemetry,
        scope_marker=scope_marker,
        reason_codes=tuple(unsafe_reasons) if unsafe_reasons else ("digest_emitted" if digests else "no_digest"),
        source_lineage=("ab01_event_digest.policy",),
    )


def _build_single_digest(candidate_input: AB1EventDigestInput) -> AB1EventDigest | None:
    event_kind = _select_event_kind(candidate_input)
    if event_kind is None:
        return None
    if not candidate_input.observed_refs:
        return None

    if event_kind in {
        AB1EventDigestKind.EFFECT_MISMATCH,
        AB1EventDigestKind.UNEXPECTED_BLOCK,
        AB1EventDigestKind.DELAYED_EFFECT_DETECTED,
        AB1EventDigestKind.MISSING_EXPECTED_EFFECT,
    } and not candidate_input.effect_refs:
        return None
    if event_kind in {
        AB1EventDigestKind.PATTERN_BREAK,
        AB1EventDigestKind.ANOMALOUS_CHANGE,
    } and not candidate_input.raw_window_refs and not candidate_input.raw_window_missing_reason:
        return None
    if event_kind is AB1EventDigestKind.PATTERN_BREAK and not candidate_input.residue_refs:
        return None
    if event_kind in {
        AB1EventDigestKind.BODY_DELTA_MISMATCH,
        AB1EventDigestKind.INVENTORY_DELTA_MISMATCH,
    } and not candidate_input.observed_refs:
        return None

    confidence = _compute_confidence(candidate_input, event_kind)
    uncertainty = round(max(0.0, 1.0 - confidence), 3)
    weak = confidence < 0.65 or (not candidate_input.raw_window_refs)
    blocked = False
    digest_status = AB1DigestStatus.WEAK if weak else AB1DigestStatus.STRONG
    direction = None
    if candidate_input.expected_body_delta is not None and candidate_input.observed_body_delta is not None:
        direction = 1 if candidate_input.observed_body_delta else -1

    event_id = f"ab1:{candidate_input.tick_ref}:{event_kind.value}"
    return AB1EventDigest(
        event_id=event_id,
        event_kind=event_kind,
        source_refs=tuple(candidate_input.source_refs),
        observation_refs=tuple(candidate_input.observation_refs),
        raw_window_refs=tuple(candidate_input.raw_window_refs),
        raw_window_missing_reason=candidate_input.raw_window_missing_reason,
        effect_refs=tuple(candidate_input.effect_refs),
        residue_refs=tuple(candidate_input.residue_refs),
        expected_refs=tuple(candidate_input.expected_refs),
        observed_refs=tuple(candidate_input.observed_refs),
        magnitude=float(candidate_input.magnitude),
        direction=direction,
        confidence=confidence,
        uncertainty=uncertainty,
        compression_method=candidate_input.compression_method,
        compression_quality=candidate_input.compression_quality,
        digest_status=digest_status,
        lossiness=(candidate_input.compression_quality is AB1CompressionQuality.LOSSY),
        explicit_non_causal_closure=True,
        cause_claimed=False,
        hidden_eval_used=False,
        scenario_label_used=False,
        blocked_status=blocked,
        weak_status=weak,
    )


def _select_event_kind(candidate_input: AB1EventDigestInput) -> AB1EventDigestKind | None:
    if not candidate_input.observation_refs:
        return None

    effect_status = (candidate_input.effect_status or "").lower()
    if effect_status in {"blocked", "observed_failure", "failed"}:
        return AB1EventDigestKind.UNEXPECTED_BLOCK

    if (
        candidate_input.expected_inventory_delta is not None
        and candidate_input.observed_inventory_delta is not None
        and candidate_input.expected_inventory_delta != candidate_input.observed_inventory_delta
    ):
        return AB1EventDigestKind.INVENTORY_DELTA_MISMATCH

    if (
        candidate_input.expected_body_delta is not None
        and candidate_input.observed_body_delta is not None
        and candidate_input.expected_body_delta != candidate_input.observed_body_delta
    ):
        return AB1EventDigestKind.BODY_DELTA_MISMATCH

    if candidate_input.delayed_effect_ticks is not None and candidate_input.delayed_effect_ticks > 0:
        return AB1EventDigestKind.DELAYED_EFFECT_DETECTED

    if candidate_input.expected_refs and candidate_input.observed_refs and (
        set(candidate_input.expected_refs) != set(candidate_input.observed_refs)
    ):
        return AB1EventDigestKind.EFFECT_MISMATCH

    if candidate_input.expected_refs and not candidate_input.observed_refs:
        return AB1EventDigestKind.MISSING_EXPECTED_EFFECT

    if "pattern_break" in candidate_input.anomaly_markers:
        return AB1EventDigestKind.PATTERN_BREAK
    if "residue_pattern_break" in candidate_input.anomaly_markers:
        return AB1EventDigestKind.PATTERN_BREAK

    if candidate_input.magnitude >= 0.35 and candidate_input.noise_level <= 0.5:
        return AB1EventDigestKind.ANOMALOUS_CHANGE

    if candidate_input.magnitude >= 0.2 and candidate_input.noise_level <= 0.7:
        return AB1EventDigestKind.UNKNOWN_PUBLIC_ANOMALY

    return None


def _compute_confidence(candidate_input: AB1EventDigestInput, event_kind: AB1EventDigestKind) -> float:
    confidence = 0.72
    if not candidate_input.raw_window_refs:
        confidence -= 0.25
    if not candidate_input.effect_refs and event_kind in {
        AB1EventDigestKind.EFFECT_MISMATCH,
        AB1EventDigestKind.UNEXPECTED_BLOCK,
        AB1EventDigestKind.DELAYED_EFFECT_DETECTED,
        AB1EventDigestKind.MISSING_EXPECTED_EFFECT,
    }:
        confidence -= 0.25
    if not candidate_input.residue_refs and event_kind in {
        AB1EventDigestKind.UNEXPECTED_BLOCK,
        AB1EventDigestKind.EFFECT_MISMATCH,
    }:
        confidence -= 0.1
    if candidate_input.prediction_error_signal is not None:
        confidence += min(abs(candidate_input.prediction_error_signal), 1.0) * 0.1
    confidence -= min(max(candidate_input.noise_level, 0.0), 1.0) * 0.25
    confidence = max(0.05, min(0.95, confidence))
    return round(confidence, 3)


def _unsafe_basis_reasons(candidate_input: AB1EventDigestInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.public_only:
        reasons.append("public_only_required")
    if not candidate_input.hidden_eval_excluded:
        reasons.append("hidden_eval_exclusion_required")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_exclusion_required")
    if not candidate_input.source_refs:
        reasons.append("source_refs_required")

    values_to_check = (
        tuple(candidate_input.source_refs)
        + tuple(candidate_input.observation_refs)
        + tuple(candidate_input.raw_window_refs)
        + tuple(candidate_input.effect_refs)
        + tuple(candidate_input.residue_refs)
        + tuple(candidate_input.expected_refs)
        + tuple(candidate_input.observed_refs)
        + tuple(candidate_input.anomaly_markers)
    )
    lowered_values = " ".join(str(item).lower() for item in values_to_check)
    for marker in _FORBIDDEN_MARKERS:
        if marker in lowered_values:
            if marker in {"hidden", "eval", "private"}:
                reasons.append("hidden_eval_marker_in_decision_basis")
            else:
                reasons.append("scenario_marker_in_decision_basis")
            break
    return list(dict.fromkeys(reasons))
