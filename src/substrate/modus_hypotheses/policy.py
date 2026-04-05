from __future__ import annotations

from substrate.modus_hypotheses.models import (
    AddressivityKind,
    IllocutionKind,
    L05CautionCode,
    L05RestrictionCode,
    ModusHypothesisBundle,
    ModusHypothesisGateDecision,
    ModusHypothesisResult,
    ModusUsabilityClass,
)


def evaluate_modus_hypothesis_downstream_gate(
    modus_result_or_bundle: object,
) -> ModusHypothesisGateDecision:
    if isinstance(modus_result_or_bundle, ModusHypothesisResult):
        bundle = modus_result_or_bundle.bundle
    elif isinstance(modus_result_or_bundle, ModusHypothesisBundle):
        bundle = modus_result_or_bundle
    else:
        raise TypeError(
            "modus hypothesis gate requires typed ModusHypothesisResult/ModusHypothesisBundle"
        )

    restrictions: list[str] = [
        L05RestrictionCode.L05_OBJECT_PRESENCE_NOT_LAWFUL_RESOLUTION,
        L05RestrictionCode.DICTUM_NOT_EQUAL_FORCE,
        L05RestrictionCode.LIKELY_ILLOCUTION_NOT_SETTLED_INTENT,
        L05RestrictionCode.ACCEPTED_HYPOTHESIS_NOT_SETTLED_INTENT,
        L05RestrictionCode.QUOTED_FORCE_NOT_CURRENT_COMMITMENT,
        L05RestrictionCode.ADDRESSIVITY_NOT_SELF_APPLICABILITY,
        L05RestrictionCode.PUNCTUATION_FORM_NOT_LAWFUL_FORCE_RESOLUTION,
        L05RestrictionCode.ILLOCUTION_ALTERNATIVES_MUST_BE_READ,
        L05RestrictionCode.UNCERTAINTY_ENTROPY_MUST_BE_READ,
        L05RestrictionCode.MODALITY_PROFILE_MUST_BE_READ,
        L05RestrictionCode.EVIDENTIALITY_PROFILE_MUST_BE_READ,
        L05RestrictionCode.ADDRESSIVITY_HYPOTHESES_MUST_BE_READ,
        L05RestrictionCode.DOWNSTREAM_CAUTIONS_MUST_BE_READ,
        L05RestrictionCode.L05_OUTPUT_NOT_L06_UPDATE,
        L05RestrictionCode.L05_OUTPUT_NOT_REPAIR_PLAN,
        L05RestrictionCode.NO_FINAL_INTENT_SELECTION,
        L05RestrictionCode.NO_COMMON_GROUND_UPDATE,
        L05RestrictionCode.NO_REPAIR_PLANNING,
    ]

    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    has_single_label_collapse = False
    has_weight_shape_violation = False
    has_addressivity_gap = False
    has_quote_commitment_leak = False
    has_entropy_gap = False
    has_caution_gap = False
    has_unresolved_slot_pressure = False

    for record in bundle.hypothesis_records:
        kinds = {hyp.illocution_kind for hyp in record.illocution_hypotheses}
        hypothesis_count = len(record.illocution_hypotheses)
        weights_sum = sum(hyp.confidence_weight for hyp in record.illocution_hypotheses)
        has_unknown = IllocutionKind.UNKNOWN_FORCE_CANDIDATE in kinds

        if hypothesis_count < 2:
            has_single_label_collapse = True
        if len(kinds) < 2:
            has_single_label_collapse = True
        if not (0.98 <= weights_sum <= 1.02):
            has_weight_shape_violation = True
        if not has_unknown:
            has_weight_shape_violation = True
        if record.uncertainty_entropy <= 0.0:
            has_entropy_gap = True
        if "unresolved_argument_slots" in record.uncertainty_markers:
            has_unresolved_slot_pressure = True

        addressivity_kinds = {hyp.addressivity_kind for hyp in record.addressivity_hypotheses}
        if not record.addressivity_hypotheses:
            has_addressivity_gap = True
        if AddressivityKind.UNKNOWN_TARGET not in addressivity_kinds and record.modality_profile.unresolved:
            has_addressivity_gap = True
        if "unresolved_argument_slots" in record.uncertainty_markers and AddressivityKind.UNKNOWN_TARGET not in addressivity_kinds:
            has_addressivity_gap = True

        if (
            record.quoted_speech_state.quote_or_echo_present
            and not record.quoted_speech_state.quoted_force_not_current_commitment
        ):
            has_quote_commitment_leak = True
        if (
            record.quoted_speech_state.quote_or_echo_present
            and L05CautionCode.QUOTED_FORCE_NOT_CURRENT_COMMITMENT
            not in record.downstream_cautions
        ):
            has_quote_commitment_leak = True
        required_cautions = {
            L05CautionCode.LIKELY_ILLOCUTION_NOT_SETTLED_INTENT,
            L05CautionCode.ADDRESSIVITY_NOT_SELF_APPLICABILITY,
            L05CautionCode.DICTUM_NOT_EQUAL_FORCE,
        }
        if not required_cautions.issubset(set(record.downstream_cautions)):
            has_caution_gap = True

        lawful = not any(
            (
                hypothesis_count < 2,
                len(kinds) < 2,
                not (0.98 <= weights_sum <= 1.02),
                not has_unknown,
                not record.addressivity_hypotheses,
                record.uncertainty_entropy <= 0.0,
                not required_cautions.issubset(set(record.downstream_cautions)),
            )
        )
        if lawful and record.confidence >= 0.2:
            accepted_ids.append(record.record_id)
        else:
            rejected_ids.append(record.record_id)

    if has_single_label_collapse:
        restrictions.append(L05RestrictionCode.SINGLE_LABEL_FORCE_COLLAPSE_DETECTED)
    if has_weight_shape_violation:
        restrictions.append(L05RestrictionCode.ILLOCUTION_WEIGHT_SHAPE_VIOLATION)
    if has_addressivity_gap:
        restrictions.append(L05RestrictionCode.ADDRESSIVITY_HYPOTHESIS_GAP_DETECTED)
    if has_quote_commitment_leak:
        restrictions.append(L05RestrictionCode.QUOTED_FORCE_COMMITMENT_LEAK_DETECTED)
    if has_entropy_gap:
        restrictions.append(L05RestrictionCode.ENTROPY_CONTRACT_GAP_DETECTED)
    if has_caution_gap:
        restrictions.append(
            L05RestrictionCode.DOWNSTREAM_CAUTIONS_CONTRACT_GAP_DETECTED
        )
    if has_unresolved_slot_pressure:
        restrictions.append(L05RestrictionCode.UNRESOLVED_SLOT_PRESSURE_MUST_BE_READ)

    if bundle.l06_downstream_not_bound_here:
        restrictions.append(L05RestrictionCode.L06_DOWNSTREAM_NOT_BOUND_HERE)
    if bundle.l06_update_consumer_not_wired_here:
        restrictions.append(L05RestrictionCode.L06_UPDATE_CONSUMER_NOT_WIRED_HERE)
    if bundle.l06_repair_consumer_not_wired_here:
        restrictions.append(L05RestrictionCode.L06_REPAIR_CONSUMER_NOT_WIRED_HERE)
    if bundle.legacy_l04_g01_shortcut_operational_debt:
        restrictions.append(
            L05RestrictionCode.LEGACY_L04_G01_SHORTCUT_OPERATIONAL_DEBT
        )
    if bundle.legacy_shortcut_bypass_risk:
        restrictions.append(L05RestrictionCode.LEGACY_SHORTCUT_BYPASS_RISK)
        restrictions.append(L05RestrictionCode.LEGACY_SHORTCUT_BYPASS_FORBIDDEN)

    accepted = bool(accepted_ids)
    if not accepted:
        usability_class = ModusUsabilityClass.BLOCKED
        reason = "l05 produced no lawful hypothesis records for downstream use"
        restrictions.append(L05RestrictionCode.NO_USABLE_L05_RECORDS)
    else:
        usability_class = ModusUsabilityClass.USABLE_BOUNDED
        reason = "typed l05 hypothesis bundle emitted with bounded uncertainty restrictions"

    degraded = (
        bundle.low_coverage_mode
        or bool(bundle.ambiguity_reasons)
        or bundle.downstream_authority_degraded
        or bundle.l06_downstream_not_bound_here
        or bundle.l06_update_consumer_not_wired_here
        or bundle.l06_repair_consumer_not_wired_here
        or has_single_label_collapse
        or has_weight_shape_violation
        or has_addressivity_gap
        or has_quote_commitment_leak
        or has_entropy_gap
        or has_caution_gap
        or has_unresolved_slot_pressure
    )
    if degraded:
        restrictions.append(L05RestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        restrictions.append(
            L05RestrictionCode.DEGRADED_L05_REQUIRES_RESTRICTIONS_READ
        )
    if degraded and accepted:
        usability_class = ModusUsabilityClass.DEGRADED_BOUNDED

    return ModusHypothesisGateDecision(
        accepted=accepted,
        usability_class=usability_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        accepted_record_ids=tuple(dict.fromkeys(accepted_ids)),
        rejected_record_ids=tuple(dict.fromkeys(rejected_ids)),
        bundle_ref=bundle.source_dictum_ref,
    )
