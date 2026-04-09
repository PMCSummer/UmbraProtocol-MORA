from __future__ import annotations

from substrate.world_adapter.models import WorldAdapterResult, WorldEffectStatus
from substrate.world_entry_contract.models import (
    W01AdmissionCriteria,
    WorldClaimAdmission,
    WorldClaimClass,
    WorldClaimStatus,
    WorldEntryContractResult,
    WorldEntryEpisode,
    WorldEntryScopeMarker,
    WorldEntryTelemetry,
    WorldPresenceMode,
)


def build_world_entry_contract(
    *,
    tick_id: str,
    world_adapter_result: WorldAdapterResult,
    source_lineage: tuple[str, ...] = (),
) -> WorldEntryContractResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(world_adapter_result, WorldAdapterResult):
        raise TypeError("world_adapter_result must be WorldAdapterResult")

    state = world_adapter_result.state
    gate = world_adapter_result.gate
    observation_present = state.last_observation_packet is not None
    action_present = state.last_action_packet is not None
    effect_present = state.last_effect_packet is not None
    evidence_window = _derive_evidence_window(world_adapter_result)
    episode = WorldEntryEpisode(
        world_episode_id=f"world-episode:{tick_id}",
        observation_basis_present=observation_present,
        action_trace_present=action_present,
        effect_basis_present=effect_present,
        effect_feedback_correlated=gate.effect_feedback_correlated,
        episode_scope="rt01_tick_world_entry",
        world_presence_mode=WorldPresenceMode(state.world_link_status.value),
        evidence_window=evidence_window,
        source_lineage=tuple(dict.fromkeys((*source_lineage, *state.source_lineage))),
        provenance="sprint8a.w_entry_contract_from_world_adapter",
        confidence=state.world_grounding_confidence,
        reliability=_derive_reliability(world_adapter_result),
        degraded=state.adapter_degraded or state.world_link_status.value in {"unavailable", "degraded"},
        incomplete=not (observation_present and action_present and effect_present and gate.effect_feedback_correlated),
    )

    available_basis = _available_basis_tokens(world_adapter_result)
    claim_admissions = (
        _claim_admission(
            claim_class=WorldClaimClass.EXTERNALLY_EFFECTED_CHANGE_CLAIM,
            admitted=gate.externally_effected_change_claim_allowed,
            required_basis=(
                "observation_basis_present",
                "action_trace_present",
                "effect_basis_present",
                "effect_feedback_correlated",
            ),
            available_basis=available_basis,
            reason_if_forbidden="world effect claim requires linked observation/action/effect basis",
        ),
        _claim_admission(
            claim_class=WorldClaimClass.WORLD_GROUNDED_SUCCESS_CLAIM,
            admitted=(
                gate.world_grounded_transition_allowed
                and gate.world_action_success_claim_allowed
            ),
            required_basis=(
                "world_grounded_transition_allowed",
                "action_trace_present",
                "effect_basis_present",
                "effect_feedback_correlated",
                "effect_success_observed",
            ),
            available_basis=available_basis,
            reason_if_forbidden="world-grounded success claim requires lawful grounded transition + correlated success feedback",
        ),
        _claim_admission(
            claim_class=WorldClaimClass.ENVIRONMENT_STATE_CHANGE_CLAIM,
            admitted=(
                gate.world_grounded_transition_allowed
                and gate.externally_effected_change_claim_allowed
            ),
            required_basis=(
                "world_grounded_transition_allowed",
                "observation_basis_present",
                "action_trace_present",
                "effect_basis_present",
                "effect_feedback_correlated",
            ),
            available_basis=available_basis,
            reason_if_forbidden="environment change claim requires world-grounded and correlated effect basis",
        ),
        _claim_admission(
            claim_class=WorldClaimClass.ACTION_SUCCESS_IN_WORLD_CLAIM,
            admitted=gate.world_action_success_claim_allowed,
            required_basis=(
                "action_trace_present",
                "effect_basis_present",
                "effect_feedback_correlated",
                "effect_success_observed",
            ),
            available_basis=available_basis,
            reason_if_forbidden="action-success claim in world requires correlated success effect feedback",
        ),
        _claim_admission(
            claim_class=WorldClaimClass.STABLE_WORLD_REGULARIZATION_CLAIM,
            admitted=(
                gate.world_action_success_claim_allowed
                and not state.adapter_degraded
                and state.world_grounding_confidence >= 0.75
            ),
            required_basis=(
                "world_grounded_transition_allowed",
                "action_trace_present",
                "effect_basis_present",
                "effect_feedback_correlated",
                "effect_success_observed",
                "adapter_not_degraded",
                "confidence_high",
            ),
            available_basis=available_basis,
            reason_if_forbidden="stable world regularization claim requires correlated success with non-degraded high-confidence basis",
        ),
        _claim_admission(
            claim_class=WorldClaimClass.WORLD_CALIBRATION_CLAIM,
            admitted=(
                gate.world_grounded_transition_allowed
                and observation_present
                and state.world_grounding_confidence >= 0.6
            ),
            required_basis=(
                "adapter_presence",
                "adapter_available",
                "observation_basis_present",
                "confidence_sufficient",
            ),
            available_basis=available_basis,
            reason_if_forbidden="world calibration claim requires available observation basis with sufficient confidence",
        ),
    )
    forbidden_claim_classes = tuple(
        admission.claim_class.value
        for admission in claim_admissions
        if not admission.admitted
    )

    w01_admission = _build_w01_admission(
        episode=episode,
        claim_admissions=claim_admissions,
        world_adapter_result=world_adapter_result,
    )
    scope_marker = _build_scope_marker()
    telemetry = WorldEntryTelemetry(
        world_episode_id=episode.world_episode_id,
        world_presence_mode=episode.world_presence_mode,
        confidence=episode.confidence,
        reliability=episode.reliability,
        degraded=episode.degraded,
        incomplete=episode.incomplete,
        forbidden_claim_classes=forbidden_claim_classes,
        w01_admission_ready=w01_admission.admission_ready,
        restrictions=w01_admission.restrictions,
        reason=w01_admission.reason,
    )
    return WorldEntryContractResult(
        episode=episode,
        claim_admissions=claim_admissions,
        forbidden_claim_classes=forbidden_claim_classes,
        world_grounded_transition_admissible=gate.world_grounded_transition_allowed,
        world_effect_success_admissible=gate.world_action_success_claim_allowed,
        w01_admission=w01_admission,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="sprint8a.w_entry_admission_contract",
    )


def _derive_evidence_window(result: WorldAdapterResult) -> tuple[str | None, str | None]:
    state = result.state
    start = None
    end = None
    if state.last_observation_packet is not None:
        start = state.last_observation_packet.observed_at
        end = state.last_observation_packet.observed_at
    if state.last_action_packet is not None and start is None:
        start = state.last_action_packet.requested_at
    if state.last_effect_packet is not None:
        if start is None:
            start = state.last_effect_packet.observed_at
        end = state.last_effect_packet.observed_at
    return start, end


def _derive_reliability(result: WorldAdapterResult) -> str:
    state = result.state
    if not state.adapter_presence or not state.adapter_available:
        return "unavailable"
    if state.adapter_degraded:
        return "degraded"
    if (
        state.effect_feedback_correlated
        and state.effect_status in {WorldEffectStatus.OBSERVED_SUCCESS, WorldEffectStatus.OBSERVED_FAILURE}
    ):
        return "effect_confirmed"
    if state.last_observation_packet is not None:
        return "observation_only"
    return "limited"


def _available_basis_tokens(result: WorldAdapterResult) -> set[str]:
    state = result.state
    gate = result.gate
    basis: set[str] = set()
    if state.adapter_presence:
        basis.add("adapter_presence")
    if state.adapter_available:
        basis.add("adapter_available")
    if not state.adapter_degraded:
        basis.add("adapter_not_degraded")
    if state.last_observation_packet is not None:
        basis.add("observation_basis_present")
    if state.last_action_packet is not None:
        basis.add("action_trace_present")
    if state.last_effect_packet is not None:
        basis.add("effect_basis_present")
    if gate.effect_feedback_correlated:
        basis.add("effect_feedback_correlated")
    if gate.world_grounded_transition_allowed:
        basis.add("world_grounded_transition_allowed")
    if state.effect_status is WorldEffectStatus.OBSERVED_SUCCESS:
        basis.add("effect_success_observed")
    if state.world_grounding_confidence >= 0.75:
        basis.add("confidence_high")
    if state.world_grounding_confidence >= 0.6:
        basis.add("confidence_sufficient")
    return basis


def _claim_admission(
    *,
    claim_class: WorldClaimClass,
    admitted: bool,
    required_basis: tuple[str, ...],
    available_basis: set[str],
    reason_if_forbidden: str,
) -> WorldClaimAdmission:
    missing = tuple(token for token in required_basis if token not in available_basis)
    if admitted:
        status = WorldClaimStatus.ALLOWED
        reason = "lawful world basis available"
    elif missing and len(missing) == len(required_basis):
        status = WorldClaimStatus.NOT_ADMISSIBLE
        reason = "required world basis absent"
    elif missing:
        status = WorldClaimStatus.UNDERCONSTRAINED
        reason = "partial world basis present but insufficient for lawful claim"
    else:
        status = WorldClaimStatus.FORBIDDEN
        reason = reason_if_forbidden
    return WorldClaimAdmission(
        claim_class=claim_class,
        status=status,
        admitted=admitted,
        required_basis=required_basis,
        missing_basis=missing,
        reason=reason,
    )


def _build_w01_admission(
    *,
    episode: WorldEntryEpisode,
    claim_admissions: tuple[WorldClaimAdmission, ...],
    world_adapter_result: WorldAdapterResult,
) -> W01AdmissionCriteria:
    typed_world_episode_exists = bool(episode.world_episode_id)
    observation_action_effect_linkable = (
        episode.observation_basis_present
        and episode.action_trace_present
        and episode.effect_basis_present
        and episode.effect_feedback_correlated
    )
    basis_inspectable_and_provenance_aware = bool(episode.provenance and episode.source_lineage)
    if episode.observation_basis_present:
        basis_inspectable_and_provenance_aware = basis_inspectable_and_provenance_aware and bool(
            world_adapter_result.state.last_observation_packet is not None
            and world_adapter_result.state.last_observation_packet.provenance
        )
    if episode.action_trace_present:
        basis_inspectable_and_provenance_aware = basis_inspectable_and_provenance_aware and bool(
            world_adapter_result.state.last_action_packet is not None
            and world_adapter_result.state.last_action_packet.provenance
        )
    if episode.effect_basis_present:
        basis_inspectable_and_provenance_aware = basis_inspectable_and_provenance_aware and bool(
            world_adapter_result.state.last_effect_packet is not None
            and world_adapter_result.state.last_effect_packet.provenance
        )
    missing_world_fallback_explicit = any(
        token in world_adapter_result.gate.restrictions
        for token in (
            "world_adapter_absent",
            "world_adapter_unavailable",
            "world_adapter_degraded",
            "observation_missing_for_world_grounding",
            "action_emitted_without_effect_feedback",
            "effect_feedback_without_action_trace",
            "effect_feedback_not_correlated_with_action",
        )
    ) or world_adapter_result.gate.world_grounded_transition_allowed
    forbidden_claims_machine_readable = bool(claim_admissions)
    rt01_world_seam_consumable_without_w01_rebrand = True
    admission_ready = (
        typed_world_episode_exists
        and observation_action_effect_linkable
        and basis_inspectable_and_provenance_aware
        and missing_world_fallback_explicit
        and forbidden_claims_machine_readable
        and rt01_world_seam_consumable_without_w01_rebrand
    )
    restrictions: list[str] = [
        "w_entry_contract_is_admission_layer_only",
        "sprint8a_not_w01_build",
    ]
    if not observation_action_effect_linkable:
        restrictions.append("w01_admission_requires_linked_observation_action_effect_episode")
    if not basis_inspectable_and_provenance_aware:
        restrictions.append("w01_admission_requires_inspectable_provenance")
    if not missing_world_fallback_explicit:
        restrictions.append("w01_admission_requires_explicit_missing_world_fallback")
    if not forbidden_claims_machine_readable:
        restrictions.append("w01_admission_requires_machine_readable_forbidden_claims")
    reason = (
        "w-entry admission criteria satisfied for bounded W01 opening"
        if admission_ready
        else "w-entry contract remains preparatory; admission criteria are not fully met"
    )
    return W01AdmissionCriteria(
        typed_world_episode_exists=typed_world_episode_exists,
        observation_action_effect_linkable=observation_action_effect_linkable,
        basis_inspectable_and_provenance_aware=basis_inspectable_and_provenance_aware,
        missing_world_fallback_explicit=missing_world_fallback_explicit,
        forbidden_claims_machine_readable=forbidden_claims_machine_readable,
        rt01_world_seam_consumable_without_w01_rebrand=(
            rt01_world_seam_consumable_without_w01_rebrand
        ),
        admission_ready=admission_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
    )


def _build_scope_marker() -> WorldEntryScopeMarker:
    return WorldEntryScopeMarker(
        scope="rt01_contour_only",
        admission_layer_only=True,
        w01_implemented=False,
        w_line_implemented=False,
        repo_wide_adoption=False,
        reason="sprint8a w-entry contract is bounded admission layer and not w-line closure",
    )
