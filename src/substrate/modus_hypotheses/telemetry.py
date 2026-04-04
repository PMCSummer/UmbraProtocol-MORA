from __future__ import annotations

from substrate.modus_hypotheses.models import (
    ModusHypothesisBundle,
    ModusHypothesisGateDecision,
    ModusHypothesisResult,
    ModusHypothesisTelemetry,
)


def build_modus_hypothesis_telemetry(
    *,
    bundle: ModusHypothesisBundle,
    source_lineage: tuple[str, ...],
    attempted_paths: tuple[str, ...],
    downstream_gate: ModusHypothesisGateDecision,
    causal_basis: str,
) -> ModusHypothesisTelemetry:
    return ModusHypothesisTelemetry(
        source_lineage=source_lineage,
        source_dictum_ref=bundle.source_dictum_ref,
        source_syntax_ref=bundle.source_syntax_ref,
        source_surface_ref=bundle.source_surface_ref,
        hypothesis_record_count=len(bundle.hypothesis_records),
        illocution_classes=tuple(
            dict.fromkeys(
                hypothesis.illocution_kind.value
                for record in bundle.hypothesis_records
                for hypothesis in record.illocution_hypotheses
            )
        ),
        evidentiality_states=tuple(
            dict.fromkeys(
                record.modality_profile.evidentiality_state.value
                for record in bundle.hypothesis_records
            )
        ),
        addressivity_classes=tuple(
            dict.fromkeys(
                hypothesis.addressivity_kind.value
                for record in bundle.hypothesis_records
                for hypothesis in record.addressivity_hypotheses
            )
        ),
        low_coverage_mode=bundle.low_coverage_mode,
        low_coverage_reasons=bundle.low_coverage_reasons,
        ambiguity_reasons=bundle.ambiguity_reasons,
        l06_downstream_not_bound_here=bundle.l06_downstream_not_bound_here,
        l06_update_consumer_not_wired_here=bundle.l06_update_consumer_not_wired_here,
        l06_repair_consumer_not_wired_here=bundle.l06_repair_consumer_not_wired_here,
        legacy_l04_g01_shortcut_operational_debt=bundle.legacy_l04_g01_shortcut_operational_debt,
        legacy_shortcut_bypass_risk=bundle.legacy_shortcut_bypass_risk,
        attempted_paths=attempted_paths,
        downstream_gate=downstream_gate,
        causal_basis=causal_basis,
    )


def modus_hypothesis_result_snapshot(result: ModusHypothesisResult) -> dict[str, object]:
    bundle = result.bundle
    return {
        "confidence": result.confidence,
        "partial_known": result.partial_known,
        "partial_known_reason": result.partial_known_reason,
        "abstain": result.abstain,
        "abstain_reason": result.abstain_reason,
        "no_final_intent_selection": result.no_final_intent_selection,
        "bundle": {
            "source_dictum_ref": bundle.source_dictum_ref,
            "source_syntax_ref": bundle.source_syntax_ref,
            "source_surface_ref": bundle.source_surface_ref,
            "linked_dictum_candidate_ids": bundle.linked_dictum_candidate_ids,
            "ambiguity_reasons": bundle.ambiguity_reasons,
            "low_coverage_mode": bundle.low_coverage_mode,
            "low_coverage_reasons": bundle.low_coverage_reasons,
            "l06_downstream_not_bound_here": bundle.l06_downstream_not_bound_here,
            "l06_update_consumer_not_wired_here": bundle.l06_update_consumer_not_wired_here,
            "l06_repair_consumer_not_wired_here": bundle.l06_repair_consumer_not_wired_here,
            "legacy_l04_g01_shortcut_operational_debt": bundle.legacy_l04_g01_shortcut_operational_debt,
            "legacy_shortcut_bypass_risk": bundle.legacy_shortcut_bypass_risk,
            "downstream_authority_degraded": bundle.downstream_authority_degraded,
            "no_final_intent_selection": bundle.no_final_intent_selection,
            "no_common_ground_update": bundle.no_common_ground_update,
            "no_repair_planning": bundle.no_repair_planning,
            "no_psychologizing": bundle.no_psychologizing,
            "no_commitment_transfer_from_quote": bundle.no_commitment_transfer_from_quote,
            "reason": bundle.reason,
            "hypothesis_records": tuple(
                {
                    "record_id": record.record_id,
                    "source_dictum_candidate_id": record.source_dictum_candidate_id,
                    "uncertainty_entropy": record.uncertainty_entropy,
                    "uncertainty_markers": record.uncertainty_markers,
                    "downstream_cautions": record.downstream_cautions,
                    "confidence": record.confidence,
                    "provenance": record.provenance,
                    "illocution_hypotheses": tuple(
                        {
                            "hypothesis_id": hypothesis.hypothesis_id,
                            "illocution_kind": hypothesis.illocution_kind.value,
                            "confidence_weight": hypothesis.confidence_weight,
                            "evidence_refs": hypothesis.evidence_refs,
                            "unresolved": hypothesis.unresolved,
                            "reason": hypothesis.reason,
                        }
                        for hypothesis in record.illocution_hypotheses
                    ),
                    "modality_profile": {
                        "profile_id": record.modality_profile.profile_id,
                        "modality_markers": record.modality_profile.modality_markers,
                        "evidentiality_state": record.modality_profile.evidentiality_state.value,
                        "stance_carriers": record.modality_profile.stance_carriers,
                        "polarity_packaging": record.modality_profile.polarity_packaging,
                        "unresolved": record.modality_profile.unresolved,
                        "reason": record.modality_profile.reason,
                    },
                    "addressivity_hypotheses": tuple(
                        {
                            "hypothesis_id": hypothesis.hypothesis_id,
                            "addressivity_kind": hypothesis.addressivity_kind.value,
                            "target_refs": hypothesis.target_refs,
                            "confidence_weight": hypothesis.confidence_weight,
                            "quoted_or_echo_bound": hypothesis.quoted_or_echo_bound,
                            "unresolved": hypothesis.unresolved,
                            "reason": hypothesis.reason,
                        }
                        for hypothesis in record.addressivity_hypotheses
                    ),
                    "quoted_speech_state": {
                        "quote_or_echo_present": record.quoted_speech_state.quote_or_echo_present,
                        "reported_force_candidate_present": record.quoted_speech_state.reported_force_candidate_present,
                        "quoted_force_not_current_commitment": record.quoted_speech_state.quoted_force_not_current_commitment,
                        "commitment_transfer_forbidden": record.quoted_speech_state.commitment_transfer_forbidden,
                        "unresolved_source_scope": record.quoted_speech_state.unresolved_source_scope,
                        "reason": record.quoted_speech_state.reason,
                    },
                }
                for record in bundle.hypothesis_records
            ),
        },
        "telemetry": {
            "source_lineage": result.telemetry.source_lineage,
            "source_dictum_ref": result.telemetry.source_dictum_ref,
            "source_syntax_ref": result.telemetry.source_syntax_ref,
            "source_surface_ref": result.telemetry.source_surface_ref,
            "hypothesis_record_count": result.telemetry.hypothesis_record_count,
            "illocution_classes": result.telemetry.illocution_classes,
            "evidentiality_states": result.telemetry.evidentiality_states,
            "addressivity_classes": result.telemetry.addressivity_classes,
            "low_coverage_mode": result.telemetry.low_coverage_mode,
            "low_coverage_reasons": result.telemetry.low_coverage_reasons,
            "ambiguity_reasons": result.telemetry.ambiguity_reasons,
            "l06_downstream_not_bound_here": result.telemetry.l06_downstream_not_bound_here,
            "l06_update_consumer_not_wired_here": result.telemetry.l06_update_consumer_not_wired_here,
            "l06_repair_consumer_not_wired_here": result.telemetry.l06_repair_consumer_not_wired_here,
            "legacy_l04_g01_shortcut_operational_debt": result.telemetry.legacy_l04_g01_shortcut_operational_debt,
            "legacy_shortcut_bypass_risk": result.telemetry.legacy_shortcut_bypass_risk,
            "attempted_paths": result.telemetry.attempted_paths,
            "downstream_gate": {
                "accepted": result.telemetry.downstream_gate.accepted,
                "usability_class": result.telemetry.downstream_gate.usability_class.value,
                "restrictions": result.telemetry.downstream_gate.restrictions,
                "reason": result.telemetry.downstream_gate.reason,
                "accepted_record_ids": result.telemetry.downstream_gate.accepted_record_ids,
                "rejected_record_ids": result.telemetry.downstream_gate.rejected_record_ids,
            },
            "causal_basis": result.telemetry.causal_basis,
        },
    }
