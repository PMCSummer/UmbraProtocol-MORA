from __future__ import annotations

from substrate.a_line_normalization.models import (
    A04ReadinessCriteria,
    ALineCapabilityState,
    ALineGateDecision,
    ALineNormalizationResult,
    ALineScopeMarker,
    ALineTelemetry,
    CapabilityClass,
    CapabilityStatus,
    ForbiddenCapabilityShortcut,
)
from substrate.self_contour import SMinimalContourResult
from substrate.world_entry_contract import WorldEntryContractResult


def build_a_line_normalization(
    *,
    tick_id: str,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
    source_lineage: tuple[str, ...] = (),
) -> ALineNormalizationResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(world_entry_result, WorldEntryContractResult):
        raise TypeError("world_entry_result must be WorldEntryContractResult")
    if not isinstance(s_minimal_result, SMinimalContourResult):
        raise TypeError("s_minimal_result must be SMinimalContourResult")

    world_basis = bool(world_entry_result.episode.observation_basis_present)
    self_basis = bool(s_minimal_result.state.self_attribution_basis_present)
    availability_basis_present = bool(world_basis or self_basis)
    controllability_basis = bool(s_minimal_result.gate.self_controlled_transition_claim_allowed)
    legitimacy_dependency_present = True
    underconstrained = bool(
        world_entry_result.episode.incomplete and (world_basis or self_basis)
    )
    policy_conditioned = bool(
        availability_basis_present
        and (
            c05_validity_action
            in {
                "run_selective_revalidation",
                "run_bounded_revalidation",
                "suspend_until_revalidation_basis",
                "halt_reuse_and_rebuild_scope",
            }
            or c04_execution_mode_claim in {"hold_safe_idle", "idle"}
        )
    )
    world_conditioned = bool(
        world_basis
        and (
            not world_entry_result.world_grounded_transition_admissible
            or not world_entry_result.world_effect_success_admissible
        )
    )
    self_conditioned = bool(self_basis and not controllability_basis)
    available_capability = bool(
        availability_basis_present
        and not underconstrained
        and not policy_conditioned
        and (
            world_entry_result.world_grounded_transition_admissible
            or s_minimal_result.gate.self_owned_state_claim_allowed
        )
    )
    no_safe_capability_claim = bool(
        not available_capability
        and not underconstrained
        and not world_conditioned
        and not self_conditioned
    )
    degraded = bool(
        underconstrained
        or policy_conditioned
        or world_entry_result.episode.degraded
        or s_minimal_result.state.degraded
    )
    confidence = max(
        0.0,
        min(
            1.0,
            (
                world_entry_result.episode.confidence
                + s_minimal_result.state.attribution_confidence
            )
            / 2.0,
        ),
    )
    capability_class = _derive_capability_class(
        available=available_capability,
        policy_conditioned=policy_conditioned,
        world_conditioned=world_conditioned,
        self_conditioned=self_conditioned,
        world_basis=world_basis,
    )
    capability_status = _derive_capability_status(
        available=available_capability,
        underconstrained=underconstrained,
        policy_conditioned=policy_conditioned,
        world_conditioned=world_conditioned,
        self_conditioned=self_conditioned,
        availability_basis_present=availability_basis_present,
    )
    state = ALineCapabilityState(
        capability_id=f"a-capability:{tick_id}",
        affordance_id=f"a-affordance:{tick_id}",
        capability_class=capability_class,
        capability_status=capability_status,
        availability_basis_present=availability_basis_present,
        world_dependency_present=world_basis,
        self_dependency_present=self_basis,
        controllability_dependency_present=controllability_basis,
        legitimacy_dependency_present=legitimacy_dependency_present,
        confidence=confidence,
        degraded=degraded,
        underconstrained=underconstrained,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *world_entry_result.episode.source_lineage,
                    *s_minimal_result.state.source_lineage,
                )
            )
        ),
        provenance="sprint8c.a_line_normalization",
    )

    forbidden: list[str] = []
    restrictions: list[str] = [
        "a_line_normalization_contract_must_be_read",
        "sprint8c_not_a04_or_a05_build",
        "capability_shortcuts_must_be_machine_readable",
    ]
    if not availability_basis_present:
        forbidden.append(ForbiddenCapabilityShortcut.CAPABILITY_CLAIM_WITHOUT_BASIS.value)
        forbidden.append(
            ForbiddenCapabilityShortcut.AFFORDANCE_CLAIM_WITHOUT_WORLD_OR_SELF_BASIS.value
        )
        restrictions.append("a_capability_claim_requires_world_or_self_basis")
    if no_safe_capability_claim:
        forbidden.append(
            ForbiddenCapabilityShortcut.UNAVAILABLE_CAPABILITY_REFRAMED_AS_AVAILABLE.value
        )
        restrictions.append("a_unavailable_capability_must_not_be_treated_as_available")
    if policy_conditioned:
        forbidden.append(
            ForbiddenCapabilityShortcut.POLICY_GATED_CAPABILITY_REFRAMED_AS_FREE_ACTION.value
        )
        restrictions.append("a_policy_gated_capability_requires_legitimacy_gate")
    if underconstrained:
        forbidden.append(
            ForbiddenCapabilityShortcut.UNDERCONSTRAINED_CAPABILITY_PRESENTED_AS_READY.value
        )
        restrictions.append("a_underconstrained_capability_requires_revalidation")
    if any("testkit" in token for token in state.source_lineage):
        forbidden.append(ForbiddenCapabilityShortcut.CAPABILITY_INFERRED_FROM_TESTKIT_ONLY.value)
    if world_entry_result.episode.effect_basis_present and not world_entry_result.episode.action_trace_present:
        forbidden.append(ForbiddenCapabilityShortcut.HIDDEN_EXTERNAL_MEANS_CLAIM.value)
    if available_capability:
        restrictions.append("a_available_capability_basis_confirmed")
    if policy_conditioned:
        restrictions.append("a_policy_conditioned_not_freely_executable")
    if underconstrained:
        restrictions.append("a_underconstrained_not_available_capability")
    if no_safe_capability_claim:
        restrictions.append("a_no_safe_capability_claim_requires_repair_or_abstain")

    gate = ALineGateDecision(
        available_capability_claim_allowed=available_capability,
        world_conditioned_capability_claim_allowed=world_conditioned and world_basis,
        self_conditioned_capability_claim_allowed=self_conditioned and self_basis,
        policy_conditioned_capability_present=policy_conditioned,
        underconstrained_capability=underconstrained,
        no_safe_capability_claim=no_safe_capability_claim,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="a-line normalization produced bounded capability substrate for a01-a03 without opening a04/a05",
    )
    a04_readiness = _build_a04_readiness(
        state=state,
        gate=gate,
    )
    scope_marker = _build_scope_marker()
    telemetry = ALineTelemetry(
        capability_id=state.capability_id,
        capability_status=state.capability_status,
        capability_class=state.capability_class,
        confidence=state.confidence,
        degraded=state.degraded,
        underconstrained=state.underconstrained,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        a04_admission_ready=a04_readiness.admission_ready_for_a04,
        reason=a04_readiness.reason,
    )
    return ALineNormalizationResult(
        state=state,
        gate=gate,
        a04_readiness=a04_readiness,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="sprint8c.a_line_normalization",
    )


def _derive_capability_class(
    *,
    available: bool,
    policy_conditioned: bool,
    world_conditioned: bool,
    self_conditioned: bool,
    world_basis: bool,
) -> CapabilityClass:
    if policy_conditioned:
        return CapabilityClass.POLICY_CONDITIONED_AFFORDANCE
    if world_conditioned or world_basis:
        return CapabilityClass.WORLD_CONDITIONED_AFFORDANCE
    if self_conditioned:
        return CapabilityClass.SELF_CONDITIONED_AFFORDANCE
    if available:
        return CapabilityClass.INTERNAL_AFFORDANCE
    return CapabilityClass.SELF_CONDITIONED_AFFORDANCE


def _derive_capability_status(
    *,
    available: bool,
    underconstrained: bool,
    policy_conditioned: bool,
    world_conditioned: bool,
    self_conditioned: bool,
    availability_basis_present: bool,
) -> CapabilityStatus:
    if available:
        return CapabilityStatus.AVAILABLE_CAPABILITY
    if underconstrained:
        return CapabilityStatus.UNDERCONSTRAINED_CAPABILITY
    if policy_conditioned:
        return CapabilityStatus.POLICY_CONDITIONED_CAPABILITY
    if world_conditioned:
        return CapabilityStatus.WORLD_CONDITIONED_CAPABILITY
    if self_conditioned:
        return CapabilityStatus.SELF_CONDITIONED_CAPABILITY
    if availability_basis_present:
        return CapabilityStatus.NO_SAFE_CAPABILITY_CLAIM
    return CapabilityStatus.UNAVAILABLE_CAPABILITY


def _build_a04_readiness(
    *,
    state: ALineCapabilityState,
    gate: ALineGateDecision,
) -> A04ReadinessCriteria:
    typed_a01_a03_substrate_exists = bool(state.capability_id and state.affordance_id)
    capability_states_machine_readable = True
    dependency_linkage_world_self_policy_inspectable = (
        state.world_dependency_present
        or state.self_dependency_present
        or state.legitimacy_dependency_present
    )
    capability_basis_missing = not state.availability_basis_present
    world_dependency_unmet = not state.world_dependency_present
    self_dependency_unmet = not state.self_dependency_present
    policy_legitimacy_unmet = (
        not state.legitimacy_dependency_present
        or gate.policy_conditioned_capability_present
    )
    underconstrained_capability_surface = bool(
        state.underconstrained or gate.underconstrained_capability
    )
    external_means_not_justified = (
        ForbiddenCapabilityShortcut.HIDDEN_EXTERNAL_MEANS_CLAIM.value
        in gate.forbidden_shortcuts
    )
    forbidden_shortcuts_machine_readable = True
    rt01_path_affecting_consumption_ready = True
    a04_implemented = False
    a05_touched = False

    blockers: list[str] = []
    if capability_basis_missing:
        blockers.append("capability_basis_missing")
    if world_dependency_unmet:
        blockers.append("world_dependency_unmet")
    if self_dependency_unmet:
        blockers.append("self_dependency_unmet")
    if policy_legitimacy_unmet:
        blockers.append("policy_legitimacy_unmet")
    if underconstrained_capability_surface:
        blockers.append("underconstrained_capability_surface")
    if external_means_not_justified:
        blockers.append("external_means_not_justified")
    if not gate.available_capability_claim_allowed:
        blockers.append("available_capability_basis_insufficient")
    if gate.no_safe_capability_claim:
        blockers.append("no_safe_capability_claim")
    if state.capability_status is not CapabilityStatus.AVAILABLE_CAPABILITY:
        blockers.append("structurally_present_but_not_ready")
    if state.degraded:
        blockers.append("capability_surface_degraded")
    if state.confidence < 0.65:
        blockers.append("capability_confidence_below_readiness_threshold")
    structurally_present_but_not_ready = bool(
        typed_a01_a03_substrate_exists
        and (
            state.capability_status is not CapabilityStatus.AVAILABLE_CAPABILITY
            or bool(blockers)
        )
    )

    admission_ready_for_a04 = (
        typed_a01_a03_substrate_exists
        and capability_states_machine_readable
        and dependency_linkage_world_self_policy_inspectable
        and not structurally_present_but_not_ready
        and not capability_basis_missing
        and not world_dependency_unmet
        and not self_dependency_unmet
        and not policy_legitimacy_unmet
        and not underconstrained_capability_surface
        and not external_means_not_justified
        and forbidden_shortcuts_machine_readable
        and rt01_path_affecting_consumption_ready
        and not a04_implemented
        and not a05_touched
        and state.confidence >= 0.65
        and not state.degraded
        and state.capability_status is CapabilityStatus.AVAILABLE_CAPABILITY
        and not blockers
    )
    restrictions = tuple(
        dict.fromkeys(
            (
                "sprint8c_normalizes_a01_a03_only",
                "a04_not_implemented_in_this_pass",
                "a05_untouched_in_this_pass",
                "a04_readiness_requires_quality_negative_controls",
                *blockers,
            )
        )
    )
    reason = (
        "a-line substrate basis is sufficient for opening a04 admission gate later"
        if admission_ready_for_a04
        else "a-line normalization remains bounded; a04 admission blockers are still open"
    )
    return A04ReadinessCriteria(
        typed_a01_a03_substrate_exists=typed_a01_a03_substrate_exists,
        capability_states_machine_readable=capability_states_machine_readable,
        dependency_linkage_world_self_policy_inspectable=(
            dependency_linkage_world_self_policy_inspectable
        ),
        structurally_present_but_not_ready=structurally_present_but_not_ready,
        capability_basis_missing=capability_basis_missing,
        world_dependency_unmet=world_dependency_unmet,
        self_dependency_unmet=self_dependency_unmet,
        policy_legitimacy_unmet=policy_legitimacy_unmet,
        underconstrained_capability_surface=underconstrained_capability_surface,
        external_means_not_justified=external_means_not_justified,
        forbidden_shortcuts_machine_readable=forbidden_shortcuts_machine_readable,
        rt01_path_affecting_consumption_ready=rt01_path_affecting_consumption_ready,
        a04_implemented=a04_implemented,
        a05_touched=a05_touched,
        admission_ready_for_a04=admission_ready_for_a04,
        blockers=tuple(blockers),
        restrictions=restrictions,
        reason=reason,
    )


def _build_scope_marker() -> ALineScopeMarker:
    return ALineScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        a_line_normalization_only=True,
        readiness_gate_only=True,
        a04_implemented=False,
        a05_touched=False,
        full_agency_stack_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "sprint8c normalizes a01-a03 capability substrate in bounded rt01 contour; a04 and a05 remain separate"
        ),
    )
