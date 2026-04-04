from __future__ import annotations

from substrate.modus_hypotheses.models import (
    AddressivityKind,
    IllocutionKind,
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
        "l05_object_presence_not_lawful_resolution",
        "dictum_not_equal_force",
        "likely_illocution_not_settled_intent",
        "accepted_hypothesis_not_settled_intent",
        "quoted_force_not_current_commitment",
        "addressivity_not_self_applicability",
        "punctuation_form_not_lawful_force_resolution",
        "illocution_alternatives_must_be_read",
        "uncertainty_entropy_must_be_read",
        "modality_profile_must_be_read",
        "evidentiality_profile_must_be_read",
        "addressivity_hypotheses_must_be_read",
        "downstream_cautions_must_be_read",
        "l05_output_not_l06_update",
        "l05_output_not_repair_plan",
        "no_final_intent_selection",
        "no_common_ground_update",
        "no_repair_planning",
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
            and "quoted_force_not_current_commitment" not in record.downstream_cautions
        ):
            has_quote_commitment_leak = True
        required_cautions = {
            "likely_illocution_not_settled_intent",
            "addressivity_not_self_applicability",
            "dictum_not_equal_force",
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
        restrictions.append("single_label_force_collapse_detected")
    if has_weight_shape_violation:
        restrictions.append("illocution_weight_shape_violation")
    if has_addressivity_gap:
        restrictions.append("addressivity_hypothesis_gap_detected")
    if has_quote_commitment_leak:
        restrictions.append("quoted_force_commitment_leak_detected")
    if has_entropy_gap:
        restrictions.append("entropy_contract_gap_detected")
    if has_caution_gap:
        restrictions.append("downstream_cautions_contract_gap_detected")
    if has_unresolved_slot_pressure:
        restrictions.append("unresolved_slot_pressure_must_be_read")

    if bundle.l06_downstream_not_bound_here:
        restrictions.append("l06_downstream_not_bound_here")
    if bundle.l06_update_consumer_not_wired_here:
        restrictions.append("l06_update_consumer_not_wired_here")
    if bundle.l06_repair_consumer_not_wired_here:
        restrictions.append("l06_repair_consumer_not_wired_here")
    if bundle.legacy_l04_g01_shortcut_operational_debt:
        restrictions.append("legacy_l04_g01_shortcut_operational_debt")
    if bundle.legacy_shortcut_bypass_risk:
        restrictions.append("legacy_shortcut_bypass_risk")
        restrictions.append("legacy_shortcut_bypass_forbidden")

    accepted = bool(accepted_ids)
    if not accepted:
        usability_class = ModusUsabilityClass.BLOCKED
        reason = "l05 produced no lawful hypothesis records for downstream use"
        restrictions.append("no_usable_l05_records")
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
        restrictions.append("downstream_authority_degraded")
        restrictions.append("degraded_l05_requires_restrictions_read")
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
