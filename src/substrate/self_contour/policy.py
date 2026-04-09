from __future__ import annotations

from substrate.self_contour.models import (
    AttributionClass,
    AttributionSourceStatus,
    BoundaryBreachRisk,
    ForbiddenSelfWorldShortcut,
    SLineAdmissionCriteria,
    SMinimalBoundaryState,
    SMinimalContourResult,
    SMinimalGateDecision,
    SMinimalScopeMarker,
    SMinimalTelemetry,
)
from substrate.world_adapter import WorldAdapterResult
from substrate.world_entry_contract import WorldEntryContractResult


def build_s_minimal_contour(
    *,
    tick_id: str,
    world_entry_result: WorldEntryContractResult,
    world_adapter_result: WorldAdapterResult,
    require_self_side_claim: bool = False,
    require_world_side_claim: bool = False,
    require_self_controlled_transition_claim: bool = False,
    source_lineage: tuple[str, ...] = (),
) -> SMinimalContourResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(world_entry_result, WorldEntryContractResult):
        raise TypeError("world_entry_result must be WorldEntryContractResult")
    if not isinstance(world_adapter_result, WorldAdapterResult):
        raise TypeError("world_adapter_result must be WorldAdapterResult")

    episode = world_entry_result.episode
    self_basis = bool(episode.action_trace_present and episode.confidence >= 0.35)
    world_basis = bool(episode.observation_basis_present)

    controllability = _derive_controllability(episode.action_trace_present, episode.effect_feedback_correlated)
    ownership = _derive_ownership(episode.action_trace_present, episode.effect_feedback_correlated)
    confidence = max(0.0, min(1.0, (episode.confidence + controllability + ownership) / 3.0))
    source_status = _derive_source_status(self_basis=self_basis, world_basis=world_basis, confidence=confidence)
    underconstrained = source_status is AttributionSourceStatus.UNDERCONSTRAINED or (
        source_status is AttributionSourceStatus.MIXED and confidence < 0.55
    )
    degraded = bool(episode.degraded or underconstrained)
    breach_risk = _derive_boundary_risk(source_status=source_status, degraded=degraded, confidence=confidence)

    self_owned_allowed = bool(self_basis and ownership >= 0.55 and confidence >= 0.45)
    self_caused_allowed = bool(self_owned_allowed and (episode.effect_feedback_correlated or not episode.effect_basis_present))
    self_control_allowed = bool(self_caused_allowed and controllability >= 0.7)
    externally_caused_allowed = bool(world_basis and (not episode.action_trace_present or not episode.effect_feedback_correlated))
    world_perturbation_allowed = bool(world_basis and not self_control_allowed)
    mixed_attribution = source_status in {
        AttributionSourceStatus.MIXED,
        AttributionSourceStatus.UNDERCONSTRAINED,
    }
    no_safe_self_claim = not self_owned_allowed
    no_safe_world_claim = not externally_caused_allowed and not world_perturbation_allowed

    forbidden: list[str] = []
    restrictions: list[str] = [
        "s_minimal_contour_must_be_read",
        "sprint8b_not_full_s_line",
        "self_world_boundary_requires_typed_basis",
    ]
    if require_self_side_claim and not self_owned_allowed:
        forbidden.append(ForbiddenSelfWorldShortcut.SELF_CLAIM_WITHOUT_SELF_BASIS.value)
        restrictions.append("self_side_claim_requires_self_basis")
    if require_self_side_claim and not episode.action_trace_present:
        forbidden.append(
            ForbiddenSelfWorldShortcut.OWNERSHIP_CLAIM_WITHOUT_ACTION_OR_BOUNDARY_BASIS.value
        )
    if require_self_controlled_transition_claim and not self_control_allowed:
        forbidden.append(
            ForbiddenSelfWorldShortcut.CONTROL_CLAIM_WITHOUT_CONTROLLABILITY_BASIS.value
        )
        restrictions.append("self_control_claim_requires_controllability_basis")
    if require_self_side_claim and episode.effect_basis_present and not episode.action_trace_present:
        forbidden.append(ForbiddenSelfWorldShortcut.EXTERNAL_EVENT_REFRAMED_AS_SELF_OWNED.value)
    if require_world_side_claim and not world_basis:
        forbidden.append(ForbiddenSelfWorldShortcut.SELF_STATE_REFRAMED_AS_WORLD_FACT.value)
        restrictions.append("world_side_claim_requires_world_basis")
    if (
        require_self_side_claim
        and require_world_side_claim
        and source_status is AttributionSourceStatus.MIXED
        and confidence < 0.7
    ):
        forbidden.append(
            ForbiddenSelfWorldShortcut.MIXED_ATTRIBUTION_WITHOUT_UNCERTAINTY_MARKING.value
        )
        restrictions.append("mixed_attribution_requires_explicit_uncertainty_marking")

    attribution_class = _derive_attribution_class(
        self_control_allowed=self_control_allowed,
        self_caused_allowed=self_caused_allowed,
        self_owned_allowed=self_owned_allowed,
        externally_caused_allowed=externally_caused_allowed,
        world_perturbation_allowed=world_perturbation_allowed,
        mixed_attribution=mixed_attribution,
        no_safe_self_claim=no_safe_self_claim,
    )

    state = SMinimalBoundaryState(
        boundary_state_id=f"s-boundary:{tick_id}",
        self_attribution_basis_present=self_basis,
        world_attribution_basis_present=world_basis,
        controllability_estimate=controllability,
        ownership_estimate=ownership,
        attribution_confidence=confidence,
        internal_vs_external_source_status=source_status,
        boundary_breach_risk=breach_risk,
        attribution_class=attribution_class,
        no_safe_self_claim=no_safe_self_claim,
        no_safe_world_claim=no_safe_world_claim,
        degraded=degraded,
        underconstrained=underconstrained,
        source_lineage=tuple(
            dict.fromkeys((*source_lineage, *episode.source_lineage, *world_adapter_result.state.source_lineage))
        ),
        provenance="sprint8b.s_minimal_contour",
    )
    gate = SMinimalGateDecision(
        self_owned_state_claim_allowed=self_owned_allowed,
        self_caused_change_claim_allowed=self_caused_allowed,
        self_controlled_transition_claim_allowed=self_control_allowed,
        externally_caused_change_claim_allowed=externally_caused_allowed,
        world_caused_perturbation_claim_allowed=world_perturbation_allowed,
        mixed_or_underconstrained_attribution=mixed_attribution,
        no_safe_self_claim=no_safe_self_claim,
        no_safe_world_claim=no_safe_world_claim,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="s-minimal contour computed bounded self/world attribution and controllability discipline",
    )
    admission = _build_s_line_admission(
        gate=gate,
        state=state,
    )
    scope_marker = _build_scope_marker()
    telemetry = SMinimalTelemetry(
        boundary_state_id=state.boundary_state_id,
        attribution_class=state.attribution_class,
        source_status=state.internal_vs_external_source_status,
        boundary_breach_risk=state.boundary_breach_risk,
        controllability_estimate=state.controllability_estimate,
        ownership_estimate=state.ownership_estimate,
        attribution_confidence=state.attribution_confidence,
        degraded=state.degraded,
        underconstrained=state.underconstrained,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return SMinimalContourResult(
        state=state,
        gate=gate,
        admission=admission,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="sprint8b.s_minimal_contour",
    )


def _derive_controllability(action_present: bool, correlated_effect: bool) -> float:
    if action_present and correlated_effect:
        return 0.85
    if action_present:
        return 0.62
    return 0.2


def _derive_ownership(action_present: bool, correlated_effect: bool) -> float:
    if action_present and correlated_effect:
        return 0.82
    if action_present:
        return 0.58
    return 0.18


def _derive_source_status(
    *,
    self_basis: bool,
    world_basis: bool,
    confidence: float,
) -> AttributionSourceStatus:
    if self_basis and not world_basis:
        return AttributionSourceStatus.INTERNAL_DOMINANT
    if world_basis and not self_basis:
        return AttributionSourceStatus.EXTERNAL_DOMINANT
    if self_basis and world_basis:
        return AttributionSourceStatus.MIXED if confidence < 0.75 else AttributionSourceStatus.INTERNAL_DOMINANT
    return AttributionSourceStatus.UNDERCONSTRAINED


def _derive_boundary_risk(
    *,
    source_status: AttributionSourceStatus,
    degraded: bool,
    confidence: float,
) -> BoundaryBreachRisk:
    if source_status is AttributionSourceStatus.UNDERCONSTRAINED:
        return BoundaryBreachRisk.HIGH
    if degraded or confidence < 0.45:
        return BoundaryBreachRisk.MEDIUM
    return BoundaryBreachRisk.LOW


def _derive_attribution_class(
    *,
    self_control_allowed: bool,
    self_caused_allowed: bool,
    self_owned_allowed: bool,
    externally_caused_allowed: bool,
    world_perturbation_allowed: bool,
    mixed_attribution: bool,
    no_safe_self_claim: bool,
) -> AttributionClass:
    if self_control_allowed:
        return AttributionClass.SELF_CONTROLLED_TRANSITION_CLAIM
    if self_caused_allowed:
        return AttributionClass.SELF_CAUSED_CHANGE_CLAIM
    if self_owned_allowed:
        return AttributionClass.SELF_OWNED_STATE_CLAIM
    if externally_caused_allowed:
        return AttributionClass.EXTERNALLY_CAUSED_CHANGE_CLAIM
    if world_perturbation_allowed:
        return AttributionClass.WORLD_CAUSED_PERTURBATION_CLAIM
    if mixed_attribution:
        return AttributionClass.MIXED_OR_UNDERCONSTRAINED_ATTRIBUTION
    if no_safe_self_claim:
        return AttributionClass.NO_SAFE_SELF_CLAIM
    return AttributionClass.NO_SAFE_WORLD_CLAIM


def _build_s_line_admission(
    *,
    gate: SMinimalGateDecision,
    state: SMinimalBoundaryState,
) -> SLineAdmissionCriteria:
    s_minimal_contour_materialized = bool(state.boundary_state_id)
    typed_boundary_surface_exists = True
    ownership_controllability_discipline_exists = (
        state.controllability_estimate >= 0.0 and state.ownership_estimate >= 0.0
    )
    forbidden_shortcuts_machine_readable = True
    rt01_path_affecting_consumption_ready = True
    future_s01_s05_remain_open = True
    full_self_model_implemented = False
    admission_ready_for_s01 = (
        s_minimal_contour_materialized
        and typed_boundary_surface_exists
        and ownership_controllability_discipline_exists
        and forbidden_shortcuts_machine_readable
        and rt01_path_affecting_consumption_ready
    )
    restrictions = (
        "sprint8b_s_minimal_contour_only",
        "future_s01_s05_not_implemented_in_this_pass",
        "full_self_model_not_claimable",
    )
    reason = (
        "s-minimal contour provides bounded enabling substrate for later S01-S05"
        if admission_ready_for_s01
        else "s-minimal contour admission remains incomplete"
    )
    return SLineAdmissionCriteria(
        s_minimal_contour_materialized=s_minimal_contour_materialized,
        typed_boundary_surface_exists=typed_boundary_surface_exists,
        ownership_controllability_discipline_exists=ownership_controllability_discipline_exists,
        forbidden_shortcuts_machine_readable=forbidden_shortcuts_machine_readable,
        rt01_path_affecting_consumption_ready=rt01_path_affecting_consumption_ready,
        future_s01_s05_remain_open=future_s01_s05_remain_open,
        full_self_model_implemented=full_self_model_implemented,
        admission_ready_for_s01=admission_ready_for_s01,
        restrictions=restrictions,
        reason=reason,
    )


def _build_scope_marker() -> SMinimalScopeMarker:
    return SMinimalScopeMarker(
        scope="rt01_contour_only",
        minimal_contour_only=True,
        s01_s05_implemented=False,
        full_self_model_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "sprint8b provides bounded S-minimal contour only; full S01-S05 and self-model stack remain open"
        ),
    )
