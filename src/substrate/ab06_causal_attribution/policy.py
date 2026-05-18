from __future__ import annotations

from .models import (
    AB6AttributionCandidate,
    AB6AttributionKind,
    AB6CausalAttributionFrame,
    AB6CausalAttributionInput,
    AB6CausalAttributionResult,
    AB6ClosureStatus,
    AB6ScopeMarker,
    AB6SupportStatus,
)
from .telemetry import build_ab6_telemetry

_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "test_label",
    "hidden",
    "eval",
    "private",
)
_WORLD_SPECIFIC_TOKENS: tuple[str, ...] = (
    "water",
    "flask",
    "ore",
    "filter",
    "station",
    "recipe",
    "minecraft",
)


def build_ab6_causal_attribution(candidate_input: AB6CausalAttributionInput) -> AB6CausalAttributionResult:
    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    frame: AB6CausalAttributionFrame | None = None
    if not unsafe_reasons:
        frame = _build_frame(candidate_input)
    telemetry = build_ab6_telemetry(
        candidate_input=candidate_input,
        frame=frame,
        unsafe_basis_count=len(unsafe_reasons),
    )
    scope_marker = AB6ScopeMarker(
        scope="ab06_self_world_causal_attribution_integration",
        causal_attribution_only=True,
        no_hypothesis_update_authority=True,
        no_epistemic_action_selection_authority=True,
        no_action_candidate_authority=True,
        no_ap01_request_authority=True,
        no_execution_authority=True,
        no_full_causal_truth_authority=True,
        reason="ab6 emits bounded attribution frame only; no fact closure, no action/publication authority",
    )
    if unsafe_reasons:
        reason_codes = tuple(unsafe_reasons)
    elif frame is None:
        reason_codes = ("no_attribution_frame_emitted",)
    else:
        reason_codes = ("attribution_frame_emitted",)
    return AB6CausalAttributionResult(
        tick_ref=candidate_input.tick_ref,
        frame=frame,
        telemetry=telemetry,
        scope_marker=scope_marker,
        reason_codes=reason_codes,
        source_lineage=("ab06_causal_attribution.policy",),
    )


def _build_frame(candidate_input: AB6CausalAttributionInput) -> AB6CausalAttributionFrame | None:
    if not candidate_input.source_frontier_refs:
        return None
    if not candidate_input.source_effect_refs and not candidate_input.source_event_digest_refs:
        return None

    candidates = _build_candidates(candidate_input)
    if not candidates:
        return None

    supported = tuple(
        dict.fromkeys(
            item.attribution_kind.value for item in candidates if item.support_status in {AB6SupportStatus.SUPPORTED, AB6SupportStatus.WEAK}
        )
    )
    blocked = tuple(
        dict.fromkeys(item.attribution_kind.value for item in candidates if item.support_status is AB6SupportStatus.BLOCKED)
    )
    unresolved = tuple(
        dict.fromkeys(item.attribution_kind.value for item in candidates if item.support_status is AB6SupportStatus.UNRESOLVED)
    )

    mixed_required = candidate_input.mixed_marker or bool(candidate_input.source_request_refs and candidate_input.external_event_refs)
    mixed_preserved = (not mixed_required) or ("mixed_cause" in supported or "mixed_cause" in unresolved or "mixed_cause" in blocked)
    unknown_required = candidate_input.unknown_marker or (
        not candidate_input.source_request_refs and not candidate_input.external_event_refs and not candidate_input.other_actor_refs
    )
    unknown_preserved = (not unknown_required) or ("unknown_cause" in supported or "unknown_cause" in unresolved or "unknown_cause" in blocked)

    missing_evidence = tuple(dict.fromkeys(code for item in candidates for code in item.missing_evidence))
    closure_status = _closure_status(
        supported=supported,
        blocked=blocked,
        unresolved=unresolved,
        mixed_preserved=mixed_preserved,
        unknown_preserved=unknown_preserved,
    )
    uncertainty = _uncertainty(
        unresolved_count=len(unresolved),
        blocked_count=len(blocked),
        supported_count=len(supported),
        unknown_preserved=unknown_preserved,
    )

    return AB6CausalAttributionFrame(
        attribution_frame_id=f"ab6:{candidate_input.tick_ref}:frame",
        source_frontier_refs=tuple(candidate_input.source_frontier_refs),
        source_update_refs=tuple(candidate_input.source_update_refs),
        source_event_digest_refs=tuple(candidate_input.source_event_digest_refs),
        source_effect_refs=tuple(candidate_input.source_effect_refs),
        source_request_refs=tuple(candidate_input.source_request_refs),
        source_candidate_refs=tuple(candidate_input.source_candidate_refs),
        source_observation_refs=tuple(candidate_input.source_observation_refs),
        timing_refs=tuple(candidate_input.timing_refs),
        attribution_candidates=candidates,
        supported_attribution_kinds=supported,
        blocked_attribution_kinds=blocked,
        unresolved_attribution_kinds=unresolved,
        mixed_cause_preserved=mixed_preserved,
        unknown_preserved=unknown_preserved,
        uncertainty=uncertainty,
        missing_evidence=missing_evidence,
        closure_status=closure_status,
        fact_claimed=False,
        cause_confirmed=False,
        hidden_eval_used=False,
        scenario_label_used=False,
        action_request_emitted=False,
        world_submission_emitted=False,
    )


def _build_candidates(candidate_input: AB6CausalAttributionInput) -> tuple[AB6AttributionCandidate, ...]:
    result: list[AB6AttributionCandidate] = []
    if candidate_input.source_request_refs:
        status = AB6SupportStatus.SUPPORTED if candidate_input.effect_correlated and candidate_input.source_effect_refs and not candidate_input.blocked_action else AB6SupportStatus.WEAK
        if not candidate_input.source_effect_refs or not candidate_input.effect_correlated or candidate_input.blocked_action:
            status = AB6SupportStatus.BLOCKED
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.SELF_ACTION,
                status=status,
                supports=("ap01_request_present", "effect_correlated" if candidate_input.effect_correlated else "effect_not_correlated"),
                does_not_explain=("external_only_change",),
                required=("ap01_request_ref", "effect_ref", "effect_correlation"),
                present=tuple(dict.fromkeys((*candidate_input.source_request_refs, *candidate_input.source_effect_refs))),
                missing=_missing(
                    has_request=bool(candidate_input.source_request_refs),
                    has_effect=bool(candidate_input.source_effect_refs),
                    correlated=candidate_input.effect_correlated,
                    blocked=candidate_input.blocked_action,
                ),
                confidence=0.72 if status is AB6SupportStatus.SUPPORTED else 0.42,
            )
        )
    else:
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.SELF_ACTION,
                status=AB6SupportStatus.BLOCKED,
                supports=("ap01_request_absent",),
                does_not_explain=("world_only_change",),
                required=("ap01_request_ref",),
                present=(),
                missing=("ap01_request_ref_required",),
                confidence=0.1,
            )
        )

    if candidate_input.other_actor_refs:
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.OTHER_ACTOR,
                status=AB6SupportStatus.SUPPORTED,
                supports=("other_actor_marker_present",),
                does_not_explain=("self_intent_without_ap01",),
                required=("other_actor_marker", "effect_ref"),
                present=tuple(dict.fromkeys((*candidate_input.other_actor_refs, *candidate_input.source_effect_refs))),
                missing=() if candidate_input.source_effect_refs else ("effect_ref_required",),
                confidence=0.66,
            )
        )
    elif candidate_input.external_event_refs:
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.WORLD_PROCESS,
                status=AB6SupportStatus.SUPPORTED,
                supports=("external_world_marker_present",),
                does_not_explain=("self_action_without_ap01",),
                required=("external_event_ref", "effect_ref"),
                present=tuple(dict.fromkeys((*candidate_input.external_event_refs, *candidate_input.source_effect_refs))),
                missing=() if candidate_input.source_effect_refs else ("effect_ref_required",),
                confidence=0.61,
            )
        )

    if candidate_input.delayed_marker and candidate_input.source_request_refs:
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.DELAYED_SELF_EFFECT,
                status=AB6SupportStatus.WEAK if candidate_input.source_effect_refs else AB6SupportStatus.BLOCKED,
                supports=("delay_marker_present", "prior_request_present"),
                does_not_explain=("immediate_self_cause_closure",),
                required=("ap01_request_ref", "timing_ref", "effect_ref"),
                present=tuple(dict.fromkeys((*candidate_input.source_request_refs, *candidate_input.timing_refs, *candidate_input.source_effect_refs))),
                missing=() if candidate_input.source_effect_refs and candidate_input.timing_refs else ("timing_or_effect_ref_required",),
                confidence=0.48,
            )
        )

    if candidate_input.mixed_marker or (candidate_input.source_request_refs and candidate_input.external_event_refs):
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.MIXED_CAUSE,
                status=AB6SupportStatus.SUPPORTED if candidate_input.source_effect_refs else AB6SupportStatus.WEAK,
                supports=("self_and_external_evidence_present",),
                does_not_explain=("single_cause_certainty",),
                required=("ap01_request_ref", "external_event_ref", "effect_ref"),
                present=tuple(
                    dict.fromkeys(
                        (*candidate_input.source_request_refs, *candidate_input.external_event_refs, *candidate_input.source_effect_refs)
                    )
                ),
                missing=() if candidate_input.source_effect_refs else ("effect_ref_required",),
                confidence=0.58,
            )
        )

    if candidate_input.sensor_mismatch_marker:
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.SENSOR_OR_PROJECTION_ERROR,
                status=AB6SupportStatus.WEAK,
                supports=("mismatch_marker_present",),
                does_not_explain=("confirmed_world_truth",),
                required=("event_digest_or_observation_mismatch_ref",),
                present=tuple(dict.fromkeys((*candidate_input.source_event_digest_refs, *candidate_input.source_observation_refs))),
                missing=()
                if (candidate_input.source_event_digest_refs or candidate_input.source_observation_refs)
                else ("mismatch_ref_required",),
                confidence=0.53,
            )
        )

    if candidate_input.unknown_marker or (
        not candidate_input.source_request_refs and not candidate_input.external_event_refs and not candidate_input.other_actor_refs
    ):
        result.append(
            _candidate(
                candidate_input=candidate_input,
                kind=AB6AttributionKind.UNKNOWN_CAUSE,
                status=AB6SupportStatus.WEAK,
                supports=("insufficient_public_causal_basis",),
                does_not_explain=("final_cause_identity",),
                required=("public_effect_ref",),
                present=tuple(candidate_input.source_effect_refs),
                missing=() if candidate_input.source_effect_refs else ("public_effect_ref_required",),
                confidence=0.35,
            )
        )

    return tuple(result)


def _candidate(
    *,
    candidate_input: AB6CausalAttributionInput,
    kind: AB6AttributionKind,
    status: AB6SupportStatus,
    supports: tuple[str, ...],
    does_not_explain: tuple[str, ...],
    required: tuple[str, ...],
    present: tuple[str, ...],
    missing: tuple[str, ...],
    confidence: float,
) -> AB6AttributionCandidate:
    evidence_refs = tuple(
        dict.fromkeys(
            (
                *candidate_input.source_frontier_refs,
                *candidate_input.source_update_refs,
                *candidate_input.source_event_digest_refs,
                *candidate_input.source_effect_refs,
                *candidate_input.source_request_refs,
                *candidate_input.source_candidate_refs,
                *candidate_input.source_observation_refs,
                *candidate_input.timing_refs,
                *candidate_input.external_event_refs,
                *candidate_input.other_actor_refs,
            )
        )
    )
    return AB6AttributionCandidate(
        attribution_id=f"ab6:{candidate_input.tick_ref}:{kind.value}",
        attribution_kind=kind,
        supports=supports,
        does_not_explain=does_not_explain,
        required_evidence=required,
        present_evidence=present,
        missing_evidence=missing,
        evidence_refs=evidence_refs if evidence_refs else ("insufficient_evidence_refs",),
        ap01_request_refs=tuple(candidate_input.source_request_refs),
        effect_refs=tuple(candidate_input.source_effect_refs),
        timing_refs=tuple(candidate_input.timing_refs),
        confidence=round(max(0.05, min(0.85, confidence)), 3),
        confidence_policy="evidence_bounded",
        support_status=status,
        forbidden_fact_closure=True,
    )


def _missing(*, has_request: bool, has_effect: bool, correlated: bool, blocked: bool) -> tuple[str, ...]:
    out: list[str] = []
    if not has_request:
        out.append("ap01_request_ref_required")
    if not has_effect:
        out.append("effect_ref_required")
    if not correlated:
        out.append("effect_correlation_required")
    if blocked:
        out.append("blocked_effect_cannot_support_success")
    return tuple(out)


def _closure_status(
    *,
    supported: tuple[str, ...],
    blocked: tuple[str, ...],
    unresolved: tuple[str, ...],
    mixed_preserved: bool,
    unknown_preserved: bool,
) -> AB6ClosureStatus:
    if not supported and blocked:
        return AB6ClosureStatus.BLOCKED
    if unresolved or (not mixed_preserved) or (not unknown_preserved):
        return AB6ClosureStatus.OPEN
    if supported:
        return AB6ClosureStatus.PROVISIONALLY_ATTRIBUTED
    return AB6ClosureStatus.OPEN


def _uncertainty(
    *,
    unresolved_count: int,
    blocked_count: int,
    supported_count: int,
    unknown_preserved: bool,
) -> float:
    value = 0.2 + (0.12 * unresolved_count) + (0.08 * blocked_count) - (0.05 * supported_count)
    if unknown_preserved:
        value += 0.08
    return round(max(0.05, min(0.95, value)), 3)


def _unsafe_basis_reasons(candidate_input: AB6CausalAttributionInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.public_only:
        reasons.append("public_only_required")
    if not candidate_input.hidden_eval_excluded:
        reasons.append("hidden_eval_exclusion_required")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_exclusion_required")
    if not candidate_input.source_frontier_refs:
        reasons.append("source_frontier_refs_required")
    joined = " ".join(
        str(item).lower()
        for item in (
            *candidate_input.source_frontier_refs,
            *candidate_input.source_update_refs,
            *candidate_input.source_event_digest_refs,
            *candidate_input.source_effect_refs,
            *candidate_input.source_request_refs,
            *candidate_input.source_candidate_refs,
            *candidate_input.source_observation_refs,
            *candidate_input.timing_refs,
            *candidate_input.external_event_refs,
            *candidate_input.other_actor_refs,
        )
    )
    for marker in _FORBIDDEN_MARKERS:
        if marker in joined:
            if marker in {"hidden", "eval", "private"}:
                reasons.append("hidden_eval_marker_in_attribution_basis")
            else:
                reasons.append("scenario_marker_in_attribution_basis")
            break
    for token in _WORLD_SPECIFIC_TOKENS:
        if token in joined:
            reasons.append("world_specific_marker_forbidden_in_ab6_substrate")
            break
    return list(dict.fromkeys(reasons))
