from __future__ import annotations

from substrate.world_entry_contract.models import WorldEntryContractResult


def world_entry_contract_snapshot(result: WorldEntryContractResult) -> dict[str, object]:
    if not isinstance(result, WorldEntryContractResult):
        raise TypeError("world_entry_contract_snapshot requires WorldEntryContractResult")
    return {
        "episode": {
            "world_episode_id": result.episode.world_episode_id,
            "observation_basis_present": result.episode.observation_basis_present,
            "action_trace_present": result.episode.action_trace_present,
            "effect_basis_present": result.episode.effect_basis_present,
            "effect_feedback_correlated": result.episode.effect_feedback_correlated,
            "episode_scope": result.episode.episode_scope,
            "world_presence_mode": result.episode.world_presence_mode.value,
            "evidence_window": result.episode.evidence_window,
            "source_lineage": result.episode.source_lineage,
            "provenance": result.episode.provenance,
            "confidence": result.episode.confidence,
            "reliability": result.episode.reliability,
            "degraded": result.episode.degraded,
            "incomplete": result.episode.incomplete,
        },
        "claim_admissions": tuple(
            {
                "claim_class": item.claim_class.value,
                "status": item.status.value,
                "admitted": item.admitted,
                "required_basis": item.required_basis,
                "missing_basis": item.missing_basis,
                "reason": item.reason,
            }
            for item in result.claim_admissions
        ),
        "forbidden_claim_classes": result.forbidden_claim_classes,
        "world_grounded_transition_admissible": result.world_grounded_transition_admissible,
        "world_effect_success_admissible": result.world_effect_success_admissible,
        "w01_admission": {
            "typed_world_episode_exists": result.w01_admission.typed_world_episode_exists,
            "observation_action_effect_linkable": result.w01_admission.observation_action_effect_linkable,
            "basis_inspectable_and_provenance_aware": result.w01_admission.basis_inspectable_and_provenance_aware,
            "missing_world_fallback_explicit": result.w01_admission.missing_world_fallback_explicit,
            "forbidden_claims_machine_readable": result.w01_admission.forbidden_claims_machine_readable,
            "rt01_world_seam_consumable_without_w01_rebrand": (
                result.w01_admission.rt01_world_seam_consumable_without_w01_rebrand
            ),
            "admission_ready": result.w01_admission.admission_ready,
            "restrictions": result.w01_admission.restrictions,
            "reason": result.w01_admission.reason,
        },
        "scope_marker": {
            "scope": result.scope_marker.scope,
            "admission_layer_only": result.scope_marker.admission_layer_only,
            "w01_implemented": result.scope_marker.w01_implemented,
            "w_line_implemented": result.scope_marker.w_line_implemented,
            "repo_wide_adoption": result.scope_marker.repo_wide_adoption,
            "reason": result.scope_marker.reason,
        },
        "telemetry": {
            "world_episode_id": result.telemetry.world_episode_id,
            "world_presence_mode": result.telemetry.world_presence_mode.value,
            "confidence": result.telemetry.confidence,
            "reliability": result.telemetry.reliability,
            "degraded": result.telemetry.degraded,
            "incomplete": result.telemetry.incomplete,
            "forbidden_claim_classes": result.telemetry.forbidden_claim_classes,
            "w01_admission_ready": result.telemetry.w01_admission_ready,
            "restrictions": result.telemetry.restrictions,
            "reason": result.telemetry.reason,
            "emitted_at": result.telemetry.emitted_at,
        },
        "reason": result.reason,
    }
