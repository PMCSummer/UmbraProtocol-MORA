from __future__ import annotations

from substrate.a_line_normalization import ALineNormalizationResult
from substrate.m_minimal import MMinimalResult, RiskLevel
from substrate.n_minimal.models import (
    ForbiddenNarrativeShortcut,
    NLineAdmissionCriteria,
    NMinimalCommitmentState,
    NMinimalGateDecision,
    NMinimalResult,
    NMinimalScopeMarker,
    NMinimalTelemetry,
    NarrativeCommitmentStatus,
    NarrativeRiskLevel,
)
from substrate.self_contour import SMinimalContourResult
from substrate.world_entry_contract import WorldEntryContractResult


def build_n_minimal(
    *,
    tick_id: str,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    claim_pressure: bool = False,
    source_lineage: tuple[str, ...] = (),
) -> NMinimalResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(world_entry_result, WorldEntryContractResult):
        raise TypeError("world_entry_result must be WorldEntryContractResult")
    if not isinstance(s_minimal_result, SMinimalContourResult):
        raise TypeError("s_minimal_result must be SMinimalContourResult")
    if not isinstance(a_line_result, ALineNormalizationResult):
        raise TypeError("a_line_result must be ALineNormalizationResult")
    if not isinstance(m_minimal_result, MMinimalResult):
        raise TypeError("m_minimal_result must be MMinimalResult")

    self_basis_present = bool(s_minimal_result.state.self_attribution_basis_present)
    world_basis_present = bool(world_entry_result.episode.observation_basis_present)
    memory_basis_present = bool(
        m_minimal_result.state.bounded_persistence_allowed
        and not m_minimal_result.gate.no_safe_memory_claim
    )
    capability_basis_present = bool(
        a_line_result.gate.available_capability_claim_allowed
        and not a_line_result.gate.no_safe_capability_claim
    )
    world_basis_linked = bool(
        world_entry_result.world_grounded_transition_admissible
        and world_entry_result.episode.action_trace_present
    )
    self_basis_stable = bool(
        self_basis_present
        and not s_minimal_result.state.underconstrained
        and s_minimal_result.state.attribution_class.value
        != "mixed_or_underconstrained_attribution"
    )
    memory_basis_stable = bool(
        memory_basis_present
        and not m_minimal_result.state.review_required
        and m_minimal_result.state.stale_risk is RiskLevel.LOW
        and m_minimal_result.state.conflict_risk is RiskLevel.LOW
    )
    capability_basis_stable = bool(
        capability_basis_present
        and not a_line_result.state.underconstrained
        and not a_line_result.gate.policy_conditioned_capability_present
    )
    lawful_basis_score = sum(
        (
            1 if self_basis_stable else 0,
            1 if world_basis_linked else 0,
            1 if memory_basis_stable else 0,
            1 if capability_basis_stable else 0,
        )
    )
    narrative_basis_present = bool(
        self_basis_present
        or world_basis_present
        or memory_basis_present
        or capability_basis_present
    )
    ambiguity_residue = bool(
        s_minimal_result.state.underconstrained
        or s_minimal_result.state.attribution_class.value
        == "mixed_or_underconstrained_attribution"
        or world_entry_result.episode.incomplete
        or a_line_result.state.underconstrained
        or m_minimal_result.state.review_required
    )
    contradiction_risk = _derive_contradiction_risk(
        s_no_safe_self=s_minimal_result.gate.no_safe_self_claim,
        s_no_safe_world=s_minimal_result.gate.no_safe_world_claim,
        m_conflict=m_minimal_result.state.conflict_risk,
        m_no_safe=m_minimal_result.gate.no_safe_memory_claim,
        ambiguity_residue=ambiguity_residue,
    )
    confidence = max(
        0.0,
        min(
            1.0,
            (
                world_entry_result.episode.confidence
                + s_minimal_result.state.attribution_confidence
                + a_line_result.state.confidence
                + m_minimal_result.state.confidence
            )
            / 4.0,
        ),
    )
    underconstrained = bool(
        not narrative_basis_present
        or confidence < 0.52
        or lawful_basis_score < 2
        or (ambiguity_residue and lawful_basis_score < 3)
    )
    degraded = bool(
        underconstrained
        or world_entry_result.episode.degraded
        or s_minimal_result.state.degraded
        or a_line_result.state.degraded
        or m_minimal_result.state.degraded
    )

    commitment_status = _derive_commitment_status(
        narrative_basis_present=narrative_basis_present,
        contradiction_risk=contradiction_risk,
        underconstrained=underconstrained,
        ambiguity_residue=ambiguity_residue,
        self_basis_present=self_basis_present,
        world_basis_present=world_basis_present,
        memory_basis_present=memory_basis_present,
        capability_basis_present=capability_basis_present,
        lawful_basis_score=lawful_basis_score,
        world_basis_linked=world_basis_linked,
        confidence=confidence,
    )
    lawful_tentative_safe = bool(
        commitment_status is NarrativeCommitmentStatus.TENTATIVE_NARRATIVE_CLAIM
        and lawful_basis_score >= 2
        and contradiction_risk in {NarrativeRiskLevel.LOW, NarrativeRiskLevel.MEDIUM}
        and confidence >= 0.62
        and not underconstrained
    )
    bounded_commitment_allowed = bool(
        commitment_status is NarrativeCommitmentStatus.BOUNDED_NARRATIVE_COMMITMENT
        and contradiction_risk is NarrativeRiskLevel.LOW
        and not ambiguity_residue
        and not degraded
        and confidence >= 0.7
    )
    no_safe_narrative_claim = bool(
        commitment_status is NarrativeCommitmentStatus.NO_SAFE_NARRATIVE_CLAIM
        or contradiction_risk is NarrativeRiskLevel.HIGH
    )
    safe_narrative_commitment_allowed = bool(
        bounded_commitment_allowed or lawful_tentative_safe
    )

    state = NMinimalCommitmentState(
        narrative_commitment_id=f"n-commitment:{tick_id}",
        commitment_status=commitment_status,
        commitment_scope="rt01_bounded_narrative_commitment",
        narrative_basis_present=narrative_basis_present,
        self_basis_present=self_basis_present,
        world_basis_present=world_basis_present,
        memory_basis_present=memory_basis_present,
        capability_basis_present=capability_basis_present,
        ambiguity_residue=ambiguity_residue,
        contradiction_risk=contradiction_risk,
        confidence=confidence,
        degraded=degraded,
        underconstrained=underconstrained,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *world_entry_result.episode.source_lineage,
                    *s_minimal_result.state.source_lineage,
                    *a_line_result.state.source_lineage,
                    *m_minimal_result.state.source_lineage,
                )
            )
        ),
        provenance="sprint8e.n_minimal",
    )

    forbidden: list[str] = []
    restrictions: list[str] = [
        "n_minimal_contract_must_be_read",
        "sprint8e_not_n01_n02_n03_n04_build",
        "narrative_commitment_basis_must_be_load_bearing",
    ]
    if not state.narrative_basis_present:
        forbidden.append(ForbiddenNarrativeShortcut.PROSE_WITHOUT_COMMITMENT_BASIS.value)
        restrictions.append("narrative_commitment_requires_basis")
    if not state.self_basis_present:
        forbidden.append(
            ForbiddenNarrativeShortcut.NARRATIVE_REFRAMED_AS_SELF_TRUTH_WITHOUT_BASIS.value
        )
    if not state.world_basis_present:
        forbidden.append(
            ForbiddenNarrativeShortcut.NARRATIVE_REFRAMED_AS_WORLD_TRUTH_WITHOUT_BASIS.value
        )
    if not state.memory_basis_present:
        forbidden.append(
            ForbiddenNarrativeShortcut.NARRATIVE_REFRAMED_AS_MEMORY_TRUTH_WITHOUT_BASIS.value
        )
    if not state.capability_basis_present:
        forbidden.append(
            ForbiddenNarrativeShortcut.NARRATIVE_REFRAMED_AS_CAPABILITY_TRUTH_WITHOUT_BASIS.value
        )
    if state.ambiguity_residue and (
        state.commitment_status in {
            NarrativeCommitmentStatus.BOUNDED_NARRATIVE_COMMITMENT,
            NarrativeCommitmentStatus.TENTATIVE_NARRATIVE_CLAIM,
        }
        or claim_pressure
    ):
        forbidden.append(
            ForbiddenNarrativeShortcut.AMBIGUITY_ERASED_FROM_NARRATIVE_CLAIM.value
        )
        if claim_pressure:
            restrictions.append("ambiguity_hiding_attempt_under_claim_pressure")
    if (
        state.contradiction_risk in {NarrativeRiskLevel.MEDIUM, NarrativeRiskLevel.HIGH}
        and (
            state.commitment_status
            is not NarrativeCommitmentStatus.CONTRADICTION_MARKED_NARRATIVE
            or claim_pressure
        )
    ):
        forbidden.append(
            ForbiddenNarrativeShortcut.CONTRADICTION_HIDDEN_BY_FLUENT_WORDING.value
        )
        if claim_pressure:
            restrictions.append("contradiction_hiding_attempt_under_claim_pressure")
    if any("testkit" in token for token in state.source_lineage):
        forbidden.append(
            ForbiddenNarrativeShortcut.NARRATIVE_SURFACE_INFERRED_FROM_TESTKIT_ONLY.value
        )
    if state.ambiguity_residue:
        restrictions.append("narrative_ambiguity_must_be_preserved")
    if state.contradiction_risk in {NarrativeRiskLevel.MEDIUM, NarrativeRiskLevel.HIGH}:
        restrictions.append("narrative_contradiction_must_be_explicitly_marked")
    if no_safe_narrative_claim:
        restrictions.append("no_safe_narrative_claim_requires_repair_or_abstain")
    if bounded_commitment_allowed:
        restrictions.append("bounded_narrative_commitment_basis_confirmed")
    elif lawful_tentative_safe:
        restrictions.append("lawful_tentative_narrative_basis_confirmed")

    gate = NMinimalGateDecision(
        safe_narrative_commitment_allowed=safe_narrative_commitment_allowed,
        bounded_commitment_allowed=bounded_commitment_allowed,
        no_safe_narrative_claim=no_safe_narrative_claim,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="n-minimal produced typed bounded narrative commitment discipline without opening N01-N04",
    )
    admission = _build_n_line_admission(state=state, gate=gate)
    scope_marker = _build_scope_marker()
    telemetry = NMinimalTelemetry(
        narrative_commitment_id=state.narrative_commitment_id,
        commitment_status=state.commitment_status,
        commitment_scope=state.commitment_scope,
        ambiguity_residue=state.ambiguity_residue,
        contradiction_risk=state.contradiction_risk,
        confidence=state.confidence,
        degraded=state.degraded,
        underconstrained=state.underconstrained,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        n01_admission_ready=admission.admission_ready_for_n01,
        reason=admission.reason,
    )
    return NMinimalResult(
        state=state,
        gate=gate,
        admission=admission,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="sprint8e.n_minimal",
    )


def _derive_contradiction_risk(
    *,
    s_no_safe_self: bool,
    s_no_safe_world: bool,
    m_conflict: RiskLevel,
    m_no_safe: bool,
    ambiguity_residue: bool,
) -> NarrativeRiskLevel:
    if m_conflict is RiskLevel.HIGH or (s_no_safe_self and s_no_safe_world):
        return NarrativeRiskLevel.HIGH
    if m_conflict is RiskLevel.MEDIUM or ambiguity_residue or s_no_safe_self or m_no_safe:
        return NarrativeRiskLevel.MEDIUM
    return NarrativeRiskLevel.LOW


def _derive_commitment_status(
    *,
    narrative_basis_present: bool,
    contradiction_risk: NarrativeRiskLevel,
    underconstrained: bool,
    ambiguity_residue: bool,
    self_basis_present: bool,
    world_basis_present: bool,
    memory_basis_present: bool,
    capability_basis_present: bool,
    lawful_basis_score: int,
    world_basis_linked: bool,
    confidence: float,
) -> NarrativeCommitmentStatus:
    if not narrative_basis_present:
        return NarrativeCommitmentStatus.NO_SAFE_NARRATIVE_CLAIM
    if contradiction_risk is NarrativeRiskLevel.HIGH:
        return NarrativeCommitmentStatus.CONTRADICTION_MARKED_NARRATIVE
    if ambiguity_residue and not underconstrained and lawful_basis_score >= 3:
        return NarrativeCommitmentStatus.AMBIGUITY_PRESERVING_NARRATIVE
    if underconstrained:
        if ambiguity_residue:
            return NarrativeCommitmentStatus.AMBIGUITY_PRESERVING_NARRATIVE
        return NarrativeCommitmentStatus.UNDERCONSTRAINED_NARRATIVE_SURFACE
    if (
        self_basis_present
        and world_basis_present
        and memory_basis_present
        and capability_basis_present
        and world_basis_linked
        and confidence >= 0.7
    ):
        return NarrativeCommitmentStatus.BOUNDED_NARRATIVE_COMMITMENT
    if lawful_basis_score >= 3 and confidence >= 0.6:
        return NarrativeCommitmentStatus.TENTATIVE_NARRATIVE_CLAIM
    return NarrativeCommitmentStatus.TENTATIVE_NARRATIVE_CLAIM


def _build_n_line_admission(
    *,
    state: NMinimalCommitmentState,
    gate: NMinimalGateDecision,
) -> NLineAdmissionCriteria:
    typed_narrative_commitment_surface_exists = bool(state.narrative_commitment_id)
    commitment_states_machine_readable = True
    machine_readable_forbidden_shortcuts = True
    rt01_path_affecting_consumption_ready = True
    n01_implemented = False
    n02_implemented = False
    n03_implemented = False
    n04_implemented = False

    blockers: list[str] = []
    if not state.narrative_basis_present:
        blockers.append("narrative_basis_missing")
    if not state.self_basis_present:
        blockers.append("self_basis_missing")
    if not state.world_basis_present:
        blockers.append("world_basis_missing")
    if not state.memory_basis_present:
        blockers.append("memory_basis_missing")
    if not state.capability_basis_present:
        blockers.append("capability_basis_missing")
    if state.ambiguity_residue:
        blockers.append("ambiguity_residue_open")
    if state.contradiction_risk in {NarrativeRiskLevel.MEDIUM, NarrativeRiskLevel.HIGH}:
        blockers.append("contradiction_risk_open")
    if state.underconstrained:
        blockers.append("narrative_underconstrained")
    if state.degraded:
        blockers.append("narrative_surface_degraded")
    if state.confidence < 0.65:
        blockers.append("narrative_confidence_below_readiness_threshold")
    if gate.no_safe_narrative_claim:
        blockers.append("no_safe_narrative_claim")
    if not gate.safe_narrative_commitment_allowed:
        blockers.append("safe_narrative_commitment_not_available")

    admission_ready_for_n01 = (
        typed_narrative_commitment_surface_exists
        and commitment_states_machine_readable
        and machine_readable_forbidden_shortcuts
        and rt01_path_affecting_consumption_ready
        and not n01_implemented
        and not n02_implemented
        and not n03_implemented
        and not n04_implemented
        and not blockers
    )
    restrictions = tuple(
        dict.fromkeys(
            (
                "sprint8e_n_minimal_only",
                "n01_n02_n03_n04_not_implemented_in_this_pass",
                "full_narrative_line_not_claimable",
                *blockers,
            )
        )
    )
    reason = (
        "n-minimal provides bounded narrative commitment basis for opening N01 later"
        if admission_ready_for_n01
        else "n-minimal admission remains incomplete because narrative commitment blockers are open"
    )
    return NLineAdmissionCriteria(
        typed_narrative_commitment_surface_exists=typed_narrative_commitment_surface_exists,
        commitment_states_machine_readable=commitment_states_machine_readable,
        machine_readable_forbidden_shortcuts=machine_readable_forbidden_shortcuts,
        rt01_path_affecting_consumption_ready=rt01_path_affecting_consumption_ready,
        n01_implemented=n01_implemented,
        n02_implemented=n02_implemented,
        n03_implemented=n03_implemented,
        n04_implemented=n04_implemented,
        admission_ready_for_n01=admission_ready_for_n01,
        blockers=tuple(blockers),
        restrictions=restrictions,
        reason=reason,
    )


def _build_scope_marker() -> NMinimalScopeMarker:
    return NMinimalScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        n_minimal_only=True,
        readiness_gate_only=True,
        n01_implemented=False,
        n02_implemented=False,
        n03_implemented=False,
        n04_implemented=False,
        full_narrative_line_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "sprint8e provides bounded n-minimal contour only; n01-n04 and full narrative line remain separate"
        ),
    )
