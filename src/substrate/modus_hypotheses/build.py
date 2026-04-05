from __future__ import annotations

import math

from substrate.contracts import RuntimeState, TransitionKind, TransitionRequest, TransitionResult, WriterIdentity
from substrate.dictum_candidates.models import (
    DictumCandidate,
    DictumCandidateBundle,
    DictumCandidateResult,
    DictumPolarity,
)
from substrate.modus_hypotheses.models import (
    AddressivityHypothesis,
    AddressivityKind,
    EvidentialityState,
    IllocutionHypothesis,
    IllocutionKind,
    L05CautionCode,
    L05CoverageCode,
    ModalityEvidentialityProfile,
    ModusHypothesisBundle,
    ModusHypothesisRecord,
    ModusHypothesisResult,
    QuotedSpeechState,
)
from substrate.modus_hypotheses.policy import evaluate_modus_hypothesis_downstream_gate
from substrate.modus_hypotheses.telemetry import (
    build_modus_hypothesis_telemetry,
    modus_hypothesis_result_snapshot,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "l05.validate_typed_inputs",
    "l05.illocution_hypothesis_bundle",
    "l05.modality_evidentiality_projection",
    "l05.addressivity_hypothesis_projection",
    "l05.quoted_echoic_separation",
    "l05.ambiguity_entropy_preservation",
    "l05.downstream_gate",
)


def build_modus_hypotheses(
    dictum_result_or_bundle: DictumCandidateResult | DictumCandidateBundle,
) -> ModusHypothesisResult:
    dictum_bundle, source_lineage = _extract_dictum_input(dictum_result_or_bundle)
    if not dictum_bundle.dictum_candidates:
        return _abstain_result(
            dictum_bundle=dictum_bundle,
            source_lineage=source_lineage,
            reason="l04 dictum candidate bundle is empty",
        )

    records = tuple(
        _build_record(record_index=idx, candidate=candidate)
        for idx, candidate in enumerate(dictum_bundle.dictum_candidates, start=1)
    )
    ambiguity_reasons = tuple(
        dict.fromkeys(
            (
                *(ambiguity.reason for ambiguity in dictum_bundle.ambiguities),
                *(conflict.reason for conflict in dictum_bundle.conflicts),
                *(unknown.reason for unknown in dictum_bundle.unknowns),
                *(reason for record in records for reason in record.uncertainty_markers),
            )
        )
    )
    low_coverage_reasons: list[str] = list(dictum_bundle.blocked_candidate_reasons)
    if dictum_bundle.unknowns:
        low_coverage_reasons.append("dictum_unknowns_present")
    if dictum_bundle.conflicts:
        low_coverage_reasons.append("dictum_conflicts_present")
    if dictum_bundle.ambiguities:
        low_coverage_reasons.append("dictum_ambiguities_present")

    # L06 exists in-repo, but this L05 path is not yet runtime-bound to a live L06 consumer route.
    l06_downstream_not_bound_here = True
    l06_update_consumer_not_wired_here = True
    l06_repair_consumer_not_wired_here = True
    legacy_l04_g01_shortcut_operational_debt = True
    legacy_shortcut_bypass_risk = True
    low_coverage_reasons.extend(
        [
            L05CoverageCode.L06_DOWNSTREAM_NOT_BOUND_HERE,
            L05CoverageCode.L06_UPDATE_CONSUMER_NOT_WIRED_HERE,
            L05CoverageCode.L06_REPAIR_CONSUMER_NOT_WIRED_HERE,
            L05CoverageCode.LEGACY_L04_G01_SHORTCUT_OPERATIONAL_DEBT,
            L05CoverageCode.LEGACY_SHORTCUT_BYPASS_RISK,
        ]
    )

    bundle = ModusHypothesisBundle(
        source_dictum_ref=dictum_bundle.source_lexical_grounding_ref,
        source_syntax_ref=dictum_bundle.source_syntax_ref,
        source_surface_ref=dictum_bundle.source_surface_ref,
        linked_dictum_candidate_ids=tuple(
            candidate.dictum_candidate_id for candidate in dictum_bundle.dictum_candidates
        ),
        hypothesis_records=records,
        ambiguity_reasons=ambiguity_reasons,
        low_coverage_mode=bool(low_coverage_reasons),
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        l06_downstream_not_bound_here=l06_downstream_not_bound_here,
        l06_update_consumer_not_wired_here=l06_update_consumer_not_wired_here,
        l06_repair_consumer_not_wired_here=l06_repair_consumer_not_wired_here,
        legacy_l04_g01_shortcut_operational_debt=legacy_l04_g01_shortcut_operational_debt,
        legacy_shortcut_bypass_risk=legacy_shortcut_bypass_risk,
        downstream_authority_degraded=True,
        no_final_intent_selection=True,
        no_common_ground_update=True,
        no_repair_planning=True,
        no_psychologizing=True,
        no_commitment_transfer_from_quote=True,
        reason="l05 emitted force/modality/addressivity hypotheses without discourse update planning",
    )
    gate = evaluate_modus_hypothesis_downstream_gate(bundle)
    telemetry = build_modus_hypothesis_telemetry(
        bundle=bundle,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    dictum_bundle.source_lexical_grounding_ref,
                    dictum_bundle.source_syntax_ref,
                    *((dictum_bundle.source_surface_ref,) if dictum_bundle.source_surface_ref else ()),
                    *source_lineage,
                )
            )
        ),
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="l04 dictum candidates projected into bounded illocution/modality/addressivity hypotheses",
    )
    partial_known_reason = (
        "; ".join(bundle.ambiguity_reasons)
        if bundle.ambiguity_reasons
        else ("; ".join(bundle.low_coverage_reasons) if bundle.low_coverage_reasons else None)
    )
    return ModusHypothesisResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=_estimate_result_confidence(bundle),
        partial_known=bool(bundle.ambiguity_reasons or bundle.low_coverage_mode),
        partial_known_reason=partial_known_reason,
        abstain=not gate.accepted,
        abstain_reason=None if gate.accepted else gate.reason,
        no_final_intent_selection=True,
    )


def modus_hypothesis_result_to_payload(result: ModusHypothesisResult) -> dict[str, object]:
    return modus_hypothesis_result_snapshot(result)


def persist_modus_hypothesis_result_via_f01(
    *,
    result: ModusHypothesisResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("l05-modus-illocution-addressivity-hypotheses",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"modus-hypotheses-step-{transition_id}",
            "modus_hypothesis_snapshot": modus_hypothesis_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_dictum_input(
    dictum_result_or_bundle: DictumCandidateResult | DictumCandidateBundle,
) -> tuple[DictumCandidateBundle, tuple[str, ...]]:
    if isinstance(dictum_result_or_bundle, DictumCandidateResult):
        return dictum_result_or_bundle.bundle, dictum_result_or_bundle.telemetry.source_lineage
    if isinstance(dictum_result_or_bundle, DictumCandidateBundle):
        return dictum_result_or_bundle, ()
    raise TypeError("build_modus_hypotheses requires DictumCandidateResult or DictumCandidateBundle")


def _build_record(*, record_index: int, candidate: DictumCandidate) -> ModusHypothesisRecord:
    illocution_hypotheses = _illocution_hypotheses(candidate, record_index)
    modality_profile = _modality_profile(candidate, record_index)
    addressivity_hypotheses = _addressivity_hypotheses(candidate, record_index)
    quote_state = _quoted_speech_state(candidate)
    entropy = _entropy(illocution_hypotheses)
    uncertainty_markers = _uncertainty_markers(candidate, entropy)
    cautions = _downstream_cautions(candidate, entropy, quote_state)

    return ModusHypothesisRecord(
        record_id=f"modus-record-{record_index}",
        source_dictum_candidate_id=candidate.dictum_candidate_id,
        illocution_hypotheses=illocution_hypotheses,
        modality_profile=modality_profile,
        addressivity_hypotheses=addressivity_hypotheses,
        quoted_speech_state=quote_state,
        uncertainty_entropy=entropy,
        uncertainty_markers=uncertainty_markers,
        downstream_cautions=cautions,
        confidence=_record_confidence(candidate.confidence, entropy, modality_profile.unresolved),
        provenance="l05 force/addressivity hypothesis layer over l04 dictum candidate",
    )


def _has_quote_or_echo_signal(candidate: DictumCandidate) -> bool:
    return candidate.quotation_sensitive or any(
        "quotation" in reason.lower() for reason in candidate.ambiguity_reasons
    )


def _has_unresolved_reference_or_deixis_slot(candidate: DictumCandidate) -> bool:
    return any(
        slot.unresolved
        and (
            "reference" in (slot.unresolved_reason or "")
            or "deixis" in (slot.unresolved_reason or "")
        )
        for slot in candidate.argument_slots
    )


def _has_source_scope_ambiguity(candidate: DictumCandidate) -> bool:
    return any("source" in reason.lower() for reason in candidate.ambiguity_reasons)


def _illocution_hypotheses(
    candidate: DictumCandidate,
    record_index: int,
) -> tuple[IllocutionHypothesis, ...]:
    question_like = any("interrog" in marker.marker_kind.lower() for marker in candidate.scope_markers)
    conditional_like = any("conditional" in marker.marker_kind.lower() for marker in candidate.scope_markers)
    deontic_like = any(
        "obligation" in marker.marker_kind.lower() or "deontic" in marker.marker_kind.lower()
        for marker in candidate.scope_markers
    )
    quote_or_echo = _has_quote_or_echo_signal(candidate)
    unresolved = any(slot.unresolved for slot in candidate.argument_slots) or any(
        marker.ambiguous for marker in candidate.scope_markers
    )
    negation_like = bool(candidate.negation_markers) or candidate.polarity is DictumPolarity.NEGATED

    weighted: list[tuple[IllocutionKind, float, str, tuple[str, ...], bool]] = [
        (
            IllocutionKind.ASSERTIVE_CANDIDATE,
            0.34,
            "default dictum-candidate force remains assertive-like but provisional",
            (candidate.predicate_frame.frame_id,),
            unresolved,
        ),
        (
            IllocutionKind.UNKNOWN_FORCE_CANDIDATE,
            0.22,
            "unknown force remains first-class to avoid top-1 collapse",
            tuple(reason for reason in candidate.ambiguity_reasons) or ("no_clear_force_resolver",),
            True,
        ),
    ]
    if question_like:
        weighted.append(
            (
                IllocutionKind.INTERROGATIVE_CANDIDATE,
                0.32,
                "interrogative-like cue from scope marker",
                tuple(marker.scope_marker_id for marker in candidate.scope_markers if "interrog" in marker.marker_kind.lower()),
                True,
            )
        )
    if deontic_like:
        weighted.append(
            (
                IllocutionKind.DIRECTIVE_CANDIDATE,
                0.28,
                "deontic/obligation marker suggests directive-like force",
                tuple(marker.scope_marker_id for marker in candidate.scope_markers if ("obligation" in marker.marker_kind.lower() or "deontic" in marker.marker_kind.lower())),
                True,
            )
        )
    if conditional_like:
        weighted.append(
            (
                IllocutionKind.COMMISSIVE_CANDIDATE,
                0.18,
                "conditional structure keeps commissive/planning reading provisional",
                tuple(marker.scope_marker_id for marker in candidate.scope_markers if "conditional" in marker.marker_kind.lower()),
                True,
            )
        )
    if negation_like:
        weighted.append(
            (
                IllocutionKind.EXPRESSIVE_CANDIDATE,
                0.14,
                "negation can package corrective/expressive stance without settling intent",
                tuple(marker.negation_marker_id for marker in candidate.negation_markers) or ("negation_from_polarity",),
                True,
            )
        )
    if unresolved:
        weighted.append(
            (
                IllocutionKind.UNKNOWN_FORCE_CANDIDATE,
                0.34,
                "unresolved slot/scope signals increase unknown-force mass",
                tuple(
                    slot.slot_id
                    for slot in candidate.argument_slots
                    if slot.unresolved
                )
                or tuple(
                    marker.scope_marker_id
                    for marker in candidate.scope_markers
                    if marker.ambiguous
                )
                or ("unresolved_force_basis",),
                True,
            )
        )
    if quote_or_echo:
        weighted.append(
            (
                IllocutionKind.REPORTED_FORCE_CANDIDATE,
                0.3,
                "quoted/report-sensitive dictum keeps reported-force alternative explicit",
                (candidate.predicate_frame.frame_id, "quotation_sensitive"),
                True,
            )
        )
        weighted.append(
            (
                IllocutionKind.QUOTED_FORCE_CANDIDATE,
                0.28,
                "quoted/echoic force remains separate from current-speaker commitment",
                (candidate.predicate_frame.frame_id, "quotation_sensitive"),
                True,
            )
        )
        weighted.append(
            (
                IllocutionKind.ECHOIC_FORCE_CANDIDATE,
                0.16,
                "echoic reading remains possible when quote-sensitive markers are present",
                tuple(reason for reason in candidate.ambiguity_reasons if "quotation" in reason.lower()) or ("quotation_sensitive_content",),
                True,
            )
        )

    normalized = _normalize_weighted_hypotheses(weighted)
    return tuple(
        IllocutionHypothesis(
            hypothesis_id=f"illocution-{record_index}-{hypothesis_index}",
            illocution_kind=kind,
            confidence_weight=weight,
            evidence_refs=evidence_refs,
            unresolved=unresolved_flag,
            reason=reason,
        )
        for hypothesis_index, (kind, weight, reason, evidence_refs, unresolved_flag) in enumerate(normalized, start=1)
    )


def _modality_profile(candidate: DictumCandidate, record_index: int) -> ModalityEvidentialityProfile:
    modality_markers: list[str] = []
    if candidate.negation_markers or candidate.polarity is DictumPolarity.NEGATED:
        modality_markers.append("negation_carrier")
    if any("conditional" in marker.marker_kind.lower() for marker in candidate.scope_markers):
        modality_markers.append("conditional_carrier")
    if any(marker.unresolved for marker in candidate.temporal_markers):
        modality_markers.append("temporal_anchor_unresolved")
    if any(marker.unresolved for marker in candidate.magnitude_markers):
        modality_markers.append("magnitude_packaging_unresolved")
    if not modality_markers:
        modality_markers.append("modality_not_resolved_from_l04")

    has_quote = _has_quote_or_echo_signal(candidate)
    if has_quote and _has_source_scope_ambiguity(candidate):
        evidentiality = EvidentialityState.MIXED
    elif has_quote:
        evidentiality = EvidentialityState.QUOTED
    elif _has_unresolved_reference_or_deixis_slot(candidate):
        evidentiality = EvidentialityState.UNRESOLVED
    else:
        evidentiality = EvidentialityState.DIRECT

    stance_carriers = tuple(
        dict.fromkeys(
            (
                f"polarity:{candidate.polarity.value}",
                *(f"scope:{marker.marker_kind}" for marker in candidate.scope_markers),
                *(f"negation:{marker.negation_marker_id}" for marker in candidate.negation_markers),
            )
        )
    )
    return ModalityEvidentialityProfile(
        profile_id=f"modality-profile-{record_index}",
        modality_markers=tuple(modality_markers),
        evidentiality_state=evidentiality,
        stance_carriers=stance_carriers,
        polarity_packaging=candidate.polarity.value,
        unresolved=bool(
            any(slot.unresolved for slot in candidate.argument_slots)
            or any(marker.ambiguous for marker in candidate.scope_markers)
            or any(marker.scope_ambiguous for marker in candidate.negation_markers)
        ),
        reason="l05 modality/evidentiality profile remains hypothesis-only and candidate-bound",
    )


def _addressivity_hypotheses(
    candidate: DictumCandidate,
    record_index: int,
) -> tuple[AddressivityHypothesis, ...]:
    unresolved_target = _has_unresolved_reference_or_deixis_slot(candidate)
    quote_or_echo = _has_quote_or_echo_signal(candidate)
    weighted: list[tuple[AddressivityKind, float, tuple[str, ...], bool, bool, str]] = [
        (
            AddressivityKind.CURRENT_INTERLOCUTOR,
            0.36 if not quote_or_echo else 0.18,
            (candidate.predicate_frame.frame_id,),
            quote_or_echo,
            True,
            "current-interlocutor reading remains provisional",
        ),
        (
            AddressivityKind.UNSPECIFIED_AUDIENCE,
            0.3,
            tuple(slot.slot_id for slot in candidate.argument_slots) or (candidate.predicate_frame.frame_id,),
            False,
            True,
            "addressivity can remain audience-unspecified at l05",
        ),
    ]
    if quote_or_echo:
        weighted.append(
            (
                AddressivityKind.REPORTED_PARTICIPANT,
                0.28,
                ("quotation_sensitive", candidate.predicate_frame.frame_id),
                True,
                True,
                "reported participant is separated from current addressee under quote-sensitive dictum",
            )
        )
        weighted.append(
            (
                AddressivityKind.QUOTED_SPEAKER,
                0.22,
                ("quotation_sensitive",),
                True,
                True,
                "quoted-speaker target remains separate from current speaker commitment",
            )
        )
    if unresolved_target:
        weighted.append(
            (
                AddressivityKind.UNKNOWN_TARGET,
                0.34,
                tuple(slot.slot_id for slot in candidate.argument_slots if slot.unresolved),
                quote_or_echo,
                True,
                "target remains unresolved from l04 unresolved reference/deixis signals",
            )
        )

    normalized = _normalize_weighted_addressivity(weighted)
    return tuple(
        AddressivityHypothesis(
            hypothesis_id=f"addressivity-{record_index}-{hypothesis_index}",
            addressivity_kind=kind,
            target_refs=target_refs,
            confidence_weight=weight,
            quoted_or_echo_bound=quoted_or_echo_bound,
            unresolved=unresolved,
            reason=reason,
        )
        for hypothesis_index, (kind, weight, target_refs, quoted_or_echo_bound, unresolved, reason) in enumerate(normalized, start=1)
    )


def _quoted_speech_state(candidate: DictumCandidate) -> QuotedSpeechState:
    quote_or_echo = _has_quote_or_echo_signal(candidate)
    unresolved_source = quote_or_echo or _has_source_scope_ambiguity(candidate)
    return QuotedSpeechState(
        quote_or_echo_present=quote_or_echo,
        reported_force_candidate_present=quote_or_echo,
        quoted_force_not_current_commitment=quote_or_echo,
        commitment_transfer_forbidden=True,
        unresolved_source_scope=unresolved_source,
        reason="quoted/echoic force remains separable from current-speaker commitment at l05",
    )


def _uncertainty_markers(candidate: DictumCandidate, entropy: float) -> tuple[str, ...]:
    markers: list[str] = []
    if any(slot.unresolved for slot in candidate.argument_slots):
        markers.append("unresolved_argument_slots")
    if any(marker.ambiguous for marker in candidate.scope_markers):
        markers.append("scope_ambiguity")
    if any(marker.scope_ambiguous for marker in candidate.negation_markers):
        markers.append("negation_scope_ambiguity")
    if candidate.quotation_sensitive:
        markers.append("quoted_or_echoic_force_present")
    if entropy > 0.45:
        markers.append("high_illocution_entropy")
    if not markers:
        markers.append("bounded_uncertainty_preserved")
    return tuple(dict.fromkeys(markers))


def _downstream_cautions(
    candidate: DictumCandidate,
    entropy: float,
    quote_state: QuotedSpeechState,
) -> tuple[str, ...]:
    cautions = [
        L05CautionCode.LIKELY_ILLOCUTION_NOT_SETTLED_INTENT,
        L05CautionCode.ADDRESSIVITY_NOT_SELF_APPLICABILITY,
        L05CautionCode.DICTUM_NOT_EQUAL_FORCE,
    ]
    if entropy >= 0.35:
        cautions.append(L05CautionCode.FORCE_ALTERNATIVES_MUST_BE_READ)
    if quote_state.quote_or_echo_present:
        cautions.append(L05CautionCode.QUOTED_FORCE_NOT_CURRENT_COMMITMENT)
    if any(slot.unresolved for slot in candidate.argument_slots):
        cautions.append(L05CautionCode.ADDRESSIVITY_TARGET_UNRESOLVED)
    return tuple(dict.fromkeys(cautions))


def _normalize_weighted_hypotheses(
    weighted: list[tuple[IllocutionKind, float, str, tuple[str, ...], bool]],
) -> list[tuple[IllocutionKind, float, str, tuple[str, ...], bool]]:
    by_kind: dict[IllocutionKind, tuple[float, str, tuple[str, ...], bool]] = {}
    for kind, weight, reason, evidence_refs, unresolved in weighted:
        prev = by_kind.get(kind)
        if prev is None or weight > prev[0]:
            by_kind[kind] = (weight, reason, evidence_refs, unresolved)
    total = sum(weight for weight, _, _, _ in by_kind.values())
    if total <= 0:
        return [
            (
                IllocutionKind.UNKNOWN_FORCE_CANDIDATE,
                1.0,
                "weight normalization fallback",
                ("weight_fallback",),
                True,
            )
        ]
    normalized = [
        (kind, round(weight / total, 4), reason, evidence_refs, unresolved)
        for kind, (weight, reason, evidence_refs, unresolved) in by_kind.items()
    ]
    normalized.sort(key=lambda item: item[1], reverse=True)
    if len(normalized) == 1:
        normalized.append(
            (
                IllocutionKind.UNKNOWN_FORCE_CANDIDATE,
                round(max(0.0001, 1.0 - normalized[0][1]), 4),
                "fallback unknown force candidate to avoid single-label collapse",
                ("single_label_fallback",),
                True,
            )
        )
    return _renormalize(normalized)


def _normalize_weighted_addressivity(
    weighted: list[tuple[AddressivityKind, float, tuple[str, ...], bool, bool, str]],
) -> list[tuple[AddressivityKind, float, tuple[str, ...], bool, bool, str]]:
    by_kind: dict[AddressivityKind, tuple[float, tuple[str, ...], bool, bool, str]] = {}
    for kind, weight, target_refs, quoted_or_echo_bound, unresolved, reason in weighted:
        prev = by_kind.get(kind)
        if prev is None or weight > prev[0]:
            by_kind[kind] = (weight, target_refs, quoted_or_echo_bound, unresolved, reason)
    total = sum(weight for weight, _, _, _, _ in by_kind.values())
    if total <= 0:
        return [
            (
                AddressivityKind.UNKNOWN_TARGET,
                1.0,
                ("addressivity_fallback",),
                False,
                True,
                "addressivity fallback",
            )
        ]
    normalized = [
        (kind, round(weight / total, 4), target_refs, quoted_or_echo_bound, unresolved, reason)
        for kind, (weight, target_refs, quoted_or_echo_bound, unresolved, reason) in by_kind.items()
    ]
    normalized.sort(key=lambda item: item[1], reverse=True)
    if len(normalized) == 1:
        normalized.append(
            (
                AddressivityKind.UNKNOWN_TARGET,
                round(max(0.0001, 1.0 - normalized[0][1]), 4),
                ("addressivity_single_label_fallback",),
                False,
                True,
                "fallback unknown target to avoid single-label addressivity collapse",
            )
        )
    return _renormalize(normalized)


def _renormalize(weighted):
    total = sum(item[1] for item in weighted)
    if total <= 0:
        return weighted
    renormalized = list(weighted)
    for idx, item in enumerate(renormalized):
        renormalized[idx] = tuple([*item[:1], round(item[1] / total, 4), *item[2:]])  # type: ignore[list-item]
    # Correct residual rounding drift on top hypothesis.
    drift = round(1.0 - sum(item[1] for item in renormalized), 4)
    if renormalized and abs(drift) > 0:
        first = renormalized[0]
        renormalized[0] = tuple([*first[:1], round(first[1] + drift, 4), *first[2:]])  # type: ignore[list-item]
    return renormalized


def _entropy(illocution_hypotheses: tuple[IllocutionHypothesis, ...]) -> float:
    if not illocution_hypotheses:
        return 0.0
    probs = [max(1e-8, hyp.confidence_weight) for hyp in illocution_hypotheses]
    h = -sum(prob * math.log2(prob) for prob in probs)
    denom = math.log2(len(probs)) if len(probs) > 1 else 1.0
    return round(max(0.0, min(1.0, h / denom)), 4)


def _record_confidence(
    candidate_confidence: float,
    entropy: float,
    unresolved_modality: bool,
) -> float:
    value = (candidate_confidence * 0.62) + ((1.0 - entropy) * 0.24) + 0.16
    if unresolved_modality:
        value -= 0.08
    return max(0.1, min(0.9, round(value, 4)))


def _estimate_result_confidence(bundle: ModusHypothesisBundle) -> float:
    base = 0.68
    if bundle.low_coverage_mode:
        base -= min(0.28, len(bundle.low_coverage_reasons) * 0.04)
    base -= min(0.18, len(bundle.ambiguity_reasons) * 0.02)
    if not bundle.hypothesis_records:
        base -= 0.2
    return max(0.08, min(0.9, round(base, 4)))


def _abstain_result(
    *,
    dictum_bundle: DictumCandidateBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> ModusHypothesisResult:
    bundle = ModusHypothesisBundle(
        source_dictum_ref=dictum_bundle.source_lexical_grounding_ref,
        source_syntax_ref=dictum_bundle.source_syntax_ref,
        source_surface_ref=dictum_bundle.source_surface_ref,
        linked_dictum_candidate_ids=(),
        hypothesis_records=(),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=(
            L05CoverageCode.ABSTAIN,
            L05CoverageCode.L06_DOWNSTREAM_NOT_BOUND_HERE,
            L05CoverageCode.L06_UPDATE_CONSUMER_NOT_WIRED_HERE,
            L05CoverageCode.L06_REPAIR_CONSUMER_NOT_WIRED_HERE,
            L05CoverageCode.LEGACY_L04_G01_SHORTCUT_OPERATIONAL_DEBT,
            L05CoverageCode.LEGACY_SHORTCUT_BYPASS_RISK,
        ),
        l06_downstream_not_bound_here=True,
        l06_update_consumer_not_wired_here=True,
        l06_repair_consumer_not_wired_here=True,
        legacy_l04_g01_shortcut_operational_debt=True,
        legacy_shortcut_bypass_risk=True,
        downstream_authority_degraded=True,
        no_final_intent_selection=True,
        no_common_ground_update=True,
        no_repair_planning=True,
        no_psychologizing=True,
        no_commitment_transfer_from_quote=True,
        reason="l05 abstained due to insufficient l04 dictum basis",
    )
    gate = evaluate_modus_hypothesis_downstream_gate(bundle)
    telemetry = build_modus_hypothesis_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="invalid or empty l04 input -> l05 abstain",
    )
    return ModusHypothesisResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_intent_selection=True,
    )
