from __future__ import annotations

from substrate.a_line_normalization import ALineNormalizationResult
from substrate.m_minimal.models import (
    ForbiddenMemoryShortcut,
    MLineAdmissionCriteria,
    MMinimalGateDecision,
    MMinimalLifecycleState,
    MMinimalResult,
    MMinimalScopeMarker,
    MMinimalTelemetry,
    MemoryLifecycleStatus,
    MemoryRetentionClass,
    RiskLevel,
)
from substrate.self_contour import SMinimalContourResult
from substrate.world_entry_contract import WorldEntryContractResult


def build_m_minimal(
    *,
    tick_id: str,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    c05_validity_action: str,
    source_lineage: tuple[str, ...] = (),
) -> MMinimalResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(world_entry_result, WorldEntryContractResult):
        raise TypeError("world_entry_result must be WorldEntryContractResult")
    if not isinstance(s_minimal_result, SMinimalContourResult):
        raise TypeError("s_minimal_result must be SMinimalContourResult")
    if not isinstance(a_line_result, ALineNormalizationResult):
        raise TypeError("a_line_result must be ALineNormalizationResult")

    world_basis = bool(world_entry_result.episode.observation_basis_present)
    self_basis = bool(s_minimal_result.state.self_attribution_basis_present)
    capability_basis = bool(
        a_line_result.state.availability_basis_present
        and not a_line_result.gate.no_safe_capability_claim
    )
    provenance_basis = bool(
        (world_basis or self_basis)
        and (source_lineage or world_entry_result.episode.source_lineage)
    )
    underconstrained = bool(
        world_entry_result.episode.incomplete
        or s_minimal_result.state.underconstrained
        or a_line_result.state.underconstrained
    )
    confidence = max(
        0.0,
        min(
            1.0,
            (
                world_entry_result.episode.confidence
                + s_minimal_result.state.attribution_confidence
                + a_line_result.state.confidence
            )
            / 3.0,
        ),
    )
    reliability = (
        "degraded"
        if world_entry_result.episode.degraded or a_line_result.state.degraded
        else "bounded"
        if confidence >= 0.7
        else "provisional"
    )
    stale_risk = _derive_stale_risk(
        c05_validity_action=c05_validity_action,
        underconstrained=underconstrained,
        degraded=world_entry_result.episode.degraded or a_line_result.state.degraded,
    )
    conflict_risk = _derive_conflict_risk(
        mixed_or_underconstrained=s_minimal_result.gate.mixed_or_underconstrained_attribution,
        no_safe_self=s_minimal_result.gate.no_safe_self_claim,
        no_safe_world=s_minimal_result.gate.no_safe_world_claim,
        a_no_safe=a_line_result.gate.no_safe_capability_claim,
    )
    review_required = bool(
        underconstrained
        or stale_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}
        or conflict_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}
    )
    bounded_persistence_allowed = bool(
        world_basis
        and self_basis
        and capability_basis
        and provenance_basis
        and not underconstrained
        and stale_risk is RiskLevel.LOW
        and conflict_risk is RiskLevel.LOW
        and confidence >= 0.65
    )
    temporary_carry_allowed = bool(
        (world_basis or self_basis) and not bounded_persistence_allowed
    )
    no_safe_memory_claim = bool(
        not (world_basis or self_basis)
        or not provenance_basis
        or conflict_risk is RiskLevel.HIGH
    )
    reactivation_eligible = bool(
        review_required
        and not no_safe_memory_claim
        and confidence >= 0.45
    )
    decay_eligible = bool(stale_risk is RiskLevel.HIGH and not bounded_persistence_allowed)
    pruning_eligible = bool(
        conflict_risk is RiskLevel.HIGH
        or (stale_risk is RiskLevel.HIGH and confidence < 0.5)
    )
    lifecycle_status = _derive_lifecycle_status(
        no_safe_memory_claim=no_safe_memory_claim,
        pruning_eligible=pruning_eligible,
        conflict_risk=conflict_risk,
        stale_risk=stale_risk,
        review_required=review_required,
        reactivation_eligible=reactivation_eligible,
        decay_eligible=decay_eligible,
        bounded_persistence_allowed=bounded_persistence_allowed,
    )
    retention_class = _derive_retention_class(lifecycle_status)
    degraded = bool(
        underconstrained
        or world_entry_result.episode.degraded
        or a_line_result.state.degraded
        or s_minimal_result.state.degraded
    )

    state = MMinimalLifecycleState(
        memory_item_id=f"m-memory-item:{tick_id}",
        memory_packet_id=f"m-memory-packet:{tick_id}",
        lifecycle_status=lifecycle_status,
        retention_class=retention_class,
        bounded_persistence_allowed=bounded_persistence_allowed,
        temporary_carry_allowed=temporary_carry_allowed,
        review_required=review_required,
        reactivation_eligible=reactivation_eligible,
        decay_eligible=decay_eligible,
        pruning_eligible=pruning_eligible,
        stale_risk=stale_risk,
        conflict_risk=conflict_risk,
        confidence=confidence,
        reliability=reliability,
        degraded=degraded,
        underconstrained=underconstrained,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *world_entry_result.episode.source_lineage,
                    *s_minimal_result.state.source_lineage,
                    *a_line_result.state.source_lineage,
                )
            )
        ),
        provenance="sprint8d.m_minimal",
    )

    forbidden: list[str] = []
    restrictions: list[str] = [
        "m_minimal_contract_must_be_read",
        "sprint8d_not_m01_m02_m03_build",
        "memory_lifecycle_states_must_be_respected",
    ]
    if state.lifecycle_status is MemoryLifecycleStatus.TEMPORARY_CARRY:
        forbidden.append(
            ForbiddenMemoryShortcut.TEMPORARY_MEMORY_REFRAMED_AS_STABLE_FACT.value
        )
        restrictions.append("temporary_memory_requires_bounded_carry_only")
    if state.stale_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}:
        forbidden.append(
            ForbiddenMemoryShortcut.STALE_MEMORY_REFRAMED_AS_CURRENT_TRUTH.value
        )
        restrictions.append("stale_memory_requires_review_or_revalidation")
    if state.conflict_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}:
        forbidden.append(
            ForbiddenMemoryShortcut.CONFLICT_MARKED_MEMORY_SILENTLY_MERGED.value
        )
        restrictions.append("conflict_marked_memory_must_not_be_silently_merged")
    if not provenance_basis:
        forbidden.append(ForbiddenMemoryShortcut.NO_PROVENANCE_MEMORY_CLAIM.value)
        restrictions.append("memory_claim_requires_provenance")
    if state.review_required:
        forbidden.append(
            ForbiddenMemoryShortcut.UNREVIEWED_MEMORY_REUSED_AS_SAFE_BASIS.value
        )
        restrictions.append("review_required_memory_must_not_support_strong_claim")
    if state.reactivation_eligible and not state.bounded_persistence_allowed:
        restrictions.append("reactivation_candidate_requires_review_before_safe_reuse")
    if state.bounded_persistence_allowed and not self_basis:
        forbidden.append(
            ForbiddenMemoryShortcut.RETAINED_MEMORY_REFRAMED_AS_IDENTITY_WITHOUT_BASIS.value
        )
    if any("testkit" in token for token in state.source_lineage):
        forbidden.append(
            ForbiddenMemoryShortcut.MEMORY_SURFACE_INFERRED_FROM_TESTKIT_ONLY.value
        )
    if no_safe_memory_claim:
        restrictions.append("no_safe_memory_claim_requires_repair_or_abstain")
    if state.bounded_persistence_allowed:
        restrictions.append("bounded_retained_memory_basis_confirmed")

    gate = MMinimalGateDecision(
        safe_memory_claim_allowed=(
            state.bounded_persistence_allowed
            and state.stale_risk is RiskLevel.LOW
            and state.conflict_risk is RiskLevel.LOW
            and not state.review_required
        ),
        bounded_retained_claim_allowed=state.bounded_persistence_allowed,
        no_safe_memory_claim=no_safe_memory_claim,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="m-minimal produced typed memory lifecycle economy with bounded safe reuse discipline",
    )
    admission = _build_m_line_admission(state=state, gate=gate)
    scope_marker = _build_scope_marker()
    telemetry = MMinimalTelemetry(
        memory_item_id=state.memory_item_id,
        lifecycle_status=state.lifecycle_status,
        retention_class=state.retention_class,
        stale_risk=state.stale_risk,
        conflict_risk=state.conflict_risk,
        confidence=state.confidence,
        reliability=state.reliability,
        degraded=state.degraded,
        underconstrained=state.underconstrained,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        m01_admission_ready=admission.admission_ready_for_m01,
        reason=admission.reason,
    )
    return MMinimalResult(
        state=state,
        gate=gate,
        admission=admission,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="sprint8d.m_minimal",
    )


def _derive_stale_risk(
    *,
    c05_validity_action: str,
    underconstrained: bool,
    degraded: bool,
) -> RiskLevel:
    if c05_validity_action in {
        "halt_reuse_and_rebuild_scope",
        "suspend_until_revalidation_basis",
    }:
        return RiskLevel.HIGH
    if underconstrained or degraded:
        return RiskLevel.MEDIUM
    if c05_validity_action in {
        "run_selective_revalidation",
        "run_bounded_revalidation",
    } and underconstrained:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _derive_conflict_risk(
    *,
    mixed_or_underconstrained: bool,
    no_safe_self: bool,
    no_safe_world: bool,
    a_no_safe: bool,
) -> RiskLevel:
    if a_no_safe or (no_safe_self and no_safe_world):
        return RiskLevel.HIGH
    if mixed_or_underconstrained or no_safe_self:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _derive_lifecycle_status(
    *,
    no_safe_memory_claim: bool,
    pruning_eligible: bool,
    conflict_risk: RiskLevel,
    stale_risk: RiskLevel,
    review_required: bool,
    reactivation_eligible: bool,
    decay_eligible: bool,
    bounded_persistence_allowed: bool,
) -> MemoryLifecycleStatus:
    if no_safe_memory_claim:
        return MemoryLifecycleStatus.NO_SAFE_MEMORY_CLAIM
    if pruning_eligible:
        return MemoryLifecycleStatus.PRUNING_CANDIDATE
    if conflict_risk is RiskLevel.HIGH:
        return MemoryLifecycleStatus.CONFLICT_MARKED_MEMORY
    if stale_risk is RiskLevel.HIGH:
        return MemoryLifecycleStatus.STALE_MEMORY_SURFACE
    if reactivation_eligible:
        return MemoryLifecycleStatus.REACTIVATION_CANDIDATE
    if review_required:
        return MemoryLifecycleStatus.REVIEW_REQUIRED
    if decay_eligible:
        return MemoryLifecycleStatus.DECAY_CANDIDATE
    if bounded_persistence_allowed:
        return MemoryLifecycleStatus.BOUNDED_RETAINED
    return MemoryLifecycleStatus.TEMPORARY_CARRY


def _derive_retention_class(status: MemoryLifecycleStatus) -> MemoryRetentionClass:
    if status is MemoryLifecycleStatus.BOUNDED_RETAINED:
        return MemoryRetentionClass.BOUNDED
    if status is MemoryLifecycleStatus.TEMPORARY_CARRY:
        return MemoryRetentionClass.TRANSIENT
    if status is MemoryLifecycleStatus.REACTIVATION_CANDIDATE:
        return MemoryRetentionClass.REACTIVATION
    if status is MemoryLifecycleStatus.DECAY_CANDIDATE:
        return MemoryRetentionClass.DECAY
    if status is MemoryLifecycleStatus.PRUNING_CANDIDATE:
        return MemoryRetentionClass.PRUNING
    if status is MemoryLifecycleStatus.NO_SAFE_MEMORY_CLAIM:
        return MemoryRetentionClass.UNSAFE
    return MemoryRetentionClass.REVIEW


def _build_m_line_admission(
    *,
    state: MMinimalLifecycleState,
    gate: MMinimalGateDecision,
) -> MLineAdmissionCriteria:
    typed_memory_lifecycle_surface_exists = bool(state.memory_item_id and state.memory_packet_id)
    lifecycle_states_machine_readable = True
    safe_lifecycle_discipline_materialized = bool(
        state.retention_class and state.lifecycle_status
    )
    machine_readable_forbidden_shortcuts = True
    rt01_path_affecting_consumption_ready = True
    stale_risk_unacceptable = state.stale_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}
    conflict_risk_unacceptable = state.conflict_risk in {
        RiskLevel.MEDIUM,
        RiskLevel.HIGH,
    }
    reactivation_requires_review = (
        state.lifecycle_status is MemoryLifecycleStatus.REACTIVATION_CANDIDATE
        and state.review_required
    )
    temporary_carry_not_stable_enough = (
        state.lifecycle_status is MemoryLifecycleStatus.TEMPORARY_CARRY
        or (state.temporary_carry_allowed and not state.bounded_persistence_allowed)
    )
    no_safe_memory_basis = gate.no_safe_memory_claim
    provenance_insufficient = "memory_claim_requires_provenance" in gate.restrictions
    lifecycle_underconstrained = state.underconstrained or state.degraded
    m01_implemented = False
    m02_implemented = False
    m03_implemented = False

    blockers: list[str] = []
    if temporary_carry_not_stable_enough:
        blockers.append("temporary_carry_not_stable_enough")
    if stale_risk_unacceptable:
        blockers.append("stale_risk_unacceptable")
    if conflict_risk_unacceptable:
        blockers.append("conflict_risk_unacceptable")
    if reactivation_requires_review:
        blockers.append("reactivation_requires_review")
    if no_safe_memory_basis:
        blockers.append("no_safe_memory_basis")
    if provenance_insufficient:
        blockers.append("provenance_insufficient")
    if lifecycle_underconstrained:
        blockers.append("lifecycle_underconstrained")
    if not state.bounded_persistence_allowed:
        blockers.append("bounded_persistence_not_safe")
    if state.review_required:
        blockers.append("review_required_before_memory_admission")
    if state.stale_risk is RiskLevel.HIGH:
        blockers.append("stale_memory_surface_unresolved")
    if state.conflict_risk is RiskLevel.HIGH:
        blockers.append("conflict_marked_memory_unresolved")
    if state.confidence < 0.65:
        blockers.append("memory_confidence_below_readiness_threshold")
    if lifecycle_underconstrained:
        blockers.append("memory_surface_degraded")

    structurally_present_but_not_ready = bool(
        typed_memory_lifecycle_surface_exists and bool(blockers)
    )

    admission_ready_for_m01 = (
        typed_memory_lifecycle_surface_exists
        and lifecycle_states_machine_readable
        and safe_lifecycle_discipline_materialized
        and machine_readable_forbidden_shortcuts
        and rt01_path_affecting_consumption_ready
        and not m01_implemented
        and not m02_implemented
        and not m03_implemented
        and not blockers
    )
    restrictions = tuple(
        dict.fromkeys(
            (
                "sprint8d_m_minimal_only",
                "m01_m02_m03_not_implemented_in_this_pass",
                "full_memory_stack_not_claimable",
                *blockers,
            )
        )
    )
    reason = (
        "m-minimal surface provides bounded memory lifecycle basis for opening M01 later"
        if admission_ready_for_m01
        else "m-minimal admission remains incomplete because lifecycle safety/quality blockers are open"
    )
    return MLineAdmissionCriteria(
        typed_memory_lifecycle_surface_exists=typed_memory_lifecycle_surface_exists,
        lifecycle_states_machine_readable=lifecycle_states_machine_readable,
        safe_lifecycle_discipline_materialized=safe_lifecycle_discipline_materialized,
        machine_readable_forbidden_shortcuts=machine_readable_forbidden_shortcuts,
        rt01_path_affecting_consumption_ready=rt01_path_affecting_consumption_ready,
        structurally_present_but_not_ready=structurally_present_but_not_ready,
        stale_risk_unacceptable=stale_risk_unacceptable,
        conflict_risk_unacceptable=conflict_risk_unacceptable,
        reactivation_requires_review=reactivation_requires_review,
        temporary_carry_not_stable_enough=temporary_carry_not_stable_enough,
        no_safe_memory_basis=no_safe_memory_basis,
        provenance_insufficient=provenance_insufficient,
        lifecycle_underconstrained=lifecycle_underconstrained,
        m01_implemented=m01_implemented,
        m02_implemented=m02_implemented,
        m03_implemented=m03_implemented,
        admission_ready_for_m01=admission_ready_for_m01,
        blockers=tuple(blockers),
        restrictions=restrictions,
        reason=reason,
    )


def _build_scope_marker() -> MMinimalScopeMarker:
    return MMinimalScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        m_minimal_only=True,
        readiness_gate_only=True,
        m01_implemented=False,
        m02_implemented=False,
        m03_implemented=False,
        full_memory_stack_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "sprint8d provides bounded m-minimal contour only; m01-m03 and full memory stack remain separate"
        ),
    )
