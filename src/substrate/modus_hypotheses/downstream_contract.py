from __future__ import annotations

from dataclasses import dataclass

from substrate.modus_hypotheses.models import (
    ModusHypothesisBundle,
    ModusHypothesisResult,
    ModusUsabilityClass,
)
from substrate.modus_hypotheses.policy import evaluate_modus_hypothesis_downstream_gate


@dataclass(frozen=True, slots=True)
class ModusHypothesisContractView:
    multi_hypothesis_present: bool
    force_alternatives_present: bool
    modality_evidentiality_profile_present: bool
    addressivity_separate_from_force: bool
    quoted_force_separate_from_current_commitment: bool
    uncertainty_entropy_present: bool
    unresolved_slot_pressure_present: bool
    requires_cautions_read: bool
    l06_downstream_absent: bool
    discourse_update_consumer_absent: bool
    repair_trigger_consumer_absent: bool
    legacy_l04_g01_shortcut_operational_debt: bool
    legacy_shortcut_bypass_risk: bool
    usability_class: ModusUsabilityClass
    restrictions: tuple[str, ...]
    requires_restrictions_read: bool
    strong_intent_resolution_permitted: bool
    discourse_update_permission: bool
    repair_planning_permission: bool
    reason: str


def derive_modus_hypothesis_contract_view(
    modus_result_or_bundle: ModusHypothesisResult | ModusHypothesisBundle,
) -> ModusHypothesisContractView:
    if isinstance(modus_result_or_bundle, ModusHypothesisResult):
        bundle = modus_result_or_bundle.bundle
    elif isinstance(modus_result_or_bundle, ModusHypothesisBundle):
        bundle = modus_result_or_bundle
    else:
        raise TypeError(
            "derive_modus_hypothesis_contract_view requires ModusHypothesisResult/ModusHypothesisBundle"
        )

    gate = evaluate_modus_hypothesis_downstream_gate(bundle)
    multi_hypothesis_present = all(
        len(record.illocution_hypotheses) >= 2
        for record in bundle.hypothesis_records
    ) if bundle.hypothesis_records else False
    force_alternatives_present = any(
        len({hyp.illocution_kind for hyp in record.illocution_hypotheses}) >= 2
        for record in bundle.hypothesis_records
    )
    modality_evidentiality_profile_present = all(
        bool(record.modality_profile.modality_markers)
        for record in bundle.hypothesis_records
    ) if bundle.hypothesis_records else False
    addressivity_separate_from_force = all(
        bool(record.addressivity_hypotheses)
        for record in bundle.hypothesis_records
    ) if bundle.hypothesis_records else False
    quoted_force_separate_from_current_commitment = all(
        (not record.quoted_speech_state.quote_or_echo_present)
        or record.quoted_speech_state.quoted_force_not_current_commitment
        for record in bundle.hypothesis_records
    ) if bundle.hypothesis_records else False
    uncertainty_entropy_present = all(
        record.uncertainty_entropy > 0.0
        for record in bundle.hypothesis_records
    ) if bundle.hypothesis_records else False
    unresolved_slot_pressure_present = any(
        "unresolved_argument_slots" in record.uncertainty_markers
        for record in bundle.hypothesis_records
    )

    return ModusHypothesisContractView(
        multi_hypothesis_present=multi_hypothesis_present,
        force_alternatives_present=force_alternatives_present,
        modality_evidentiality_profile_present=modality_evidentiality_profile_present,
        addressivity_separate_from_force=addressivity_separate_from_force,
        quoted_force_separate_from_current_commitment=quoted_force_separate_from_current_commitment,
        uncertainty_entropy_present=uncertainty_entropy_present,
        unresolved_slot_pressure_present=unresolved_slot_pressure_present,
        requires_cautions_read=("downstream_cautions_must_be_read" in gate.restrictions),
        l06_downstream_absent=bundle.l06_downstream_absent,
        discourse_update_consumer_absent=bundle.discourse_update_consumer_absent,
        repair_trigger_consumer_absent=bundle.repair_trigger_consumer_absent,
        legacy_l04_g01_shortcut_operational_debt=bundle.legacy_l04_g01_shortcut_operational_debt,
        legacy_shortcut_bypass_risk=bundle.legacy_shortcut_bypass_risk,
        usability_class=gate.usability_class,
        restrictions=gate.restrictions,
        requires_restrictions_read=True,
        strong_intent_resolution_permitted=False,
        discourse_update_permission=False,
        repair_planning_permission=False,
        reason="l05 contract view exposes bounded force/addressivity hypothesis obligations only",
    )
