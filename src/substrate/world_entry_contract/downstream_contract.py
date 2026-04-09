from __future__ import annotations

from dataclasses import dataclass

from substrate.world_entry_contract.models import WorldEntryContractResult


@dataclass(frozen=True, slots=True)
class WorldEntryContractView:
    world_episode_id: str
    world_presence_mode: str
    observation_basis_present: bool
    action_trace_present: bool
    effect_basis_present: bool
    effect_feedback_correlated: bool
    confidence: float
    reliability: str
    degraded: bool
    incomplete: bool
    forbidden_claim_classes: tuple[str, ...]
    world_grounded_transition_admissible: bool
    world_effect_success_admissible: bool
    w01_admission_ready: bool
    w01_admission_restrictions: tuple[str, ...]
    scope_marker: str
    scope_rt01_contour_only: bool
    scope_admission_layer_only: bool
    scope_w01_implemented: bool
    scope_w_line_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    requires_restrictions_read: bool
    reason: str


def derive_world_entry_contract_view(result: WorldEntryContractResult) -> WorldEntryContractView:
    if not isinstance(result, WorldEntryContractResult):
        raise TypeError("derive_world_entry_contract_view requires WorldEntryContractResult")
    return WorldEntryContractView(
        world_episode_id=result.episode.world_episode_id,
        world_presence_mode=result.episode.world_presence_mode.value,
        observation_basis_present=result.episode.observation_basis_present,
        action_trace_present=result.episode.action_trace_present,
        effect_basis_present=result.episode.effect_basis_present,
        effect_feedback_correlated=result.episode.effect_feedback_correlated,
        confidence=result.episode.confidence,
        reliability=result.episode.reliability,
        degraded=result.episode.degraded,
        incomplete=result.episode.incomplete,
        forbidden_claim_classes=result.forbidden_claim_classes,
        world_grounded_transition_admissible=result.world_grounded_transition_admissible,
        world_effect_success_admissible=result.world_effect_success_admissible,
        w01_admission_ready=result.w01_admission.admission_ready,
        w01_admission_restrictions=result.w01_admission.restrictions,
        scope_marker=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.scope == "rt01_contour_only",
        scope_admission_layer_only=result.scope_marker.admission_layer_only,
        scope_w01_implemented=result.scope_marker.w01_implemented,
        scope_w_line_implemented=result.scope_marker.w_line_implemented,
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        requires_restrictions_read=True,
        reason=result.w01_admission.reason,
    )
