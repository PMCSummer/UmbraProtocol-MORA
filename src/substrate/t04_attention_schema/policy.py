from __future__ import annotations

from substrate.t03_hypothesis_competition import T03CompetitionResult, T03ConvergenceStatus
from substrate.t04_attention_schema.models import (
    ForbiddenT04Shortcut,
    T04AttentionOwner,
    T04AttentionSchemaResult,
    T04AttentionSchemaState,
    T04AttentionTarget,
    T04FocusMode,
    T04FocusTargetStatus,
    T04GateDecision,
    T04ReportabilityStatus,
    T04ScopeMarker,
    T04Telemetry,
)

_REVALIDATE_ACTIONS = {
    "run_selective_revalidation",
    "run_bounded_revalidation",
    "suspend_until_revalidation_basis",
    "halt_reuse_and_rebuild_scope",
}


def build_t04_attention_schema(
    *,
    tick_id: str,
    t03_result: T03CompetitionResult,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
    source_lineage: tuple[str, ...] = (),
) -> T04AttentionSchemaResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(t03_result, T03CompetitionResult):
        raise TypeError("t03_result must be T03CompetitionResult")

    ranked_candidates = tuple(
        sorted(t03_result.state.candidates, key=lambda item: item.competition_score, reverse=True)
    )
    focus_targets = _build_focus_targets(ranked_candidates=ranked_candidates, t03_result=t03_result)
    peripheral_targets = _build_peripheral_targets(
        ranked_candidates=ranked_candidates,
        t03_result=t03_result,
    )
    attention_owner = _derive_attention_owner(
        focus_targets=focus_targets,
        t03_result=t03_result,
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
    )
    stability_estimate = _derive_stability_estimate(t03_result=t03_result)
    control_estimate = _derive_control_estimate(
        t03_result=t03_result,
        attention_owner=attention_owner,
        c04_execution_mode_claim=c04_execution_mode_claim,
    )
    redirect_cost = _derive_redirect_cost(
        peripheral_targets=peripheral_targets,
        t03_result=t03_result,
    )
    focus_mode = _derive_focus_mode(
        focus_targets=focus_targets,
        peripheral_targets=peripheral_targets,
        stability_estimate=stability_estimate,
    )
    reportability_status = _derive_reportability_status(
        focus_targets=focus_targets,
        control_estimate=control_estimate,
        stability_estimate=stability_estimate,
    )
    forbidden = _derive_forbidden_shortcuts(
        focus_targets=focus_targets,
        peripheral_targets=peripheral_targets,
        attention_owner=attention_owner,
        reportability_status=reportability_status,
        stability_estimate=stability_estimate,
        t03_result=t03_result,
        c05_validity_action=c05_validity_action,
    )
    gate = _build_gate(
        focus_targets=focus_targets,
        peripheral_targets=peripheral_targets,
        attention_owner=attention_owner,
        control_estimate=control_estimate,
        reportability_status=reportability_status,
        t03_result=t03_result,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
    )
    state = T04AttentionSchemaState(
        schema_id=f"t04-attention-schema:{tick_id}",
        source_t03_competition_id=t03_result.state.competition_id,
        focus_targets=focus_targets,
        peripheral_targets=peripheral_targets,
        attention_owner=attention_owner,
        focus_mode=focus_mode,
        control_estimate=round(control_estimate, 3),
        stability_estimate=round(stability_estimate, 3),
        redirect_cost=round(redirect_cost, 3),
        reportability_status=reportability_status,
        source_authority_tags=tuple(
            dict.fromkeys(
                (
                    *t03_result.state.source_authority_tags,
                    f"C04:mode={c04_execution_mode_claim}",
                    f"C05:validity_action={c05_validity_action}",
                )
            )
        ),
        source_lineage=tuple(dict.fromkeys((*source_lineage, *t03_result.state.source_lineage))),
        provenance="t04.attention_schema.focus_ownership_model",
    )
    scope_marker = _build_scope_marker()
    telemetry = T04Telemetry(
        schema_id=state.schema_id,
        source_t03_competition_id=state.source_t03_competition_id,
        focus_targets_count=len(state.focus_targets),
        peripheral_targets_count=len(state.peripheral_targets),
        attention_owner=state.attention_owner,
        focus_mode=state.focus_mode,
        control_estimate=state.control_estimate,
        stability_estimate=state.stability_estimate,
        redirect_cost=state.redirect_cost,
        reportability_status=state.reportability_status,
        focus_ownership_consumer_ready=gate.focus_ownership_consumer_ready,
        reportable_focus_consumer_ready=gate.reportable_focus_consumer_ready,
        peripheral_preservation_ready=gate.peripheral_preservation_ready,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return T04AttentionSchemaResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="t04.first_bounded_attention_schema_slice",
    )


def _build_focus_targets(
    *,
    ranked_candidates: tuple[object, ...],
    t03_result: T03CompetitionResult,
) -> tuple[T04AttentionTarget, ...]:
    leader_id = (
        t03_result.state.current_leader_hypothesis_id
        or t03_result.state.provisional_frontrunner_hypothesis_id
    )
    if leader_id is None:
        return ()
    by_id = {item.hypothesis_id: item for item in ranked_candidates}
    leader = by_id.get(leader_id)
    if leader is None:
        return ()
    status = (
        T04FocusTargetStatus.FOCUS
        if t03_result.state.current_leader_hypothesis_id is not None
        else T04FocusTargetStatus.PROVISIONAL
    )
    return (
        T04AttentionTarget(
            target_id=f"hypothesis:{leader.hypothesis_id}",
            source_hypothesis_id=leader.hypothesis_id,
            prominence_score=round(max(0.0, leader.competition_score), 3),
            owner_confidence=round(max(0.0, 1.0 - leader.unresolved_load * 0.35), 3),
            status=status,
            provenance="t04.focus.from_t03_leader_or_frontrunner",
        ),
    )


def _build_peripheral_targets(
    *,
    ranked_candidates: tuple[object, ...],
    t03_result: T03CompetitionResult,
) -> tuple[T04AttentionTarget, ...]:
    targets: list[T04AttentionTarget] = []
    tied_ids = set(t03_result.state.tied_competitor_ids)
    leader_id = (
        t03_result.state.current_leader_hypothesis_id
        or t03_result.state.provisional_frontrunner_hypothesis_id
    )
    for item in ranked_candidates:
        if item.hypothesis_id == leader_id:
            continue
        if item.hypothesis_id in tied_ids:
            status = T04FocusTargetStatus.MIXED
        else:
            status = T04FocusTargetStatus.PERIPHERAL
        targets.append(
            T04AttentionTarget(
                target_id=f"hypothesis:{item.hypothesis_id}",
                source_hypothesis_id=item.hypothesis_id,
                prominence_score=round(max(0.0, item.competition_score), 3),
                owner_confidence=round(max(0.0, 1.0 - item.unresolved_load * 0.35), 3),
                status=status,
                provenance="t04.peripheral.from_t03_competitor",
            )
        )
    for conflict_id in t03_result.state.publication_frontier.unresolved_conflicts:
        targets.append(
            T04AttentionTarget(
                target_id=f"conflict:{conflict_id}",
                source_hypothesis_id=None,
                prominence_score=0.25,
                owner_confidence=0.2,
                status=T04FocusTargetStatus.MIXED,
                provenance="t04.peripheral.from_t03_unresolved_conflict",
            )
        )
    for slot_id in t03_result.state.publication_frontier.open_slots:
        targets.append(
            T04AttentionTarget(
                target_id=f"slot:{slot_id}",
                source_hypothesis_id=None,
                prominence_score=0.2,
                owner_confidence=0.15,
                status=T04FocusTargetStatus.PROVISIONAL,
                provenance="t04.peripheral.from_t03_open_slot",
            )
        )
    unique: dict[str, T04AttentionTarget] = {}
    for item in targets:
        unique[item.target_id] = item
    return tuple(unique.values())


def _derive_attention_owner(
    *,
    focus_targets: tuple[T04AttentionTarget, ...],
    t03_result: T03CompetitionResult,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
) -> T04AttentionOwner:
    if not focus_targets:
        return T04AttentionOwner.UNASSIGNED
    if c05_validity_action in _REVALIDATE_ACTIONS:
        return T04AttentionOwner.VALIDITY_GUARDED
    if t03_result.state.honest_nonconvergence:
        return T04AttentionOwner.MIXED_OR_PROVISIONAL
    if c04_execution_mode_claim in {"continue_stream", "run_revisit", "prepare_output"}:
        return T04AttentionOwner.SELF_GUIDED
    return T04AttentionOwner.MIXED_OR_PROVISIONAL


def _derive_stability_estimate(*, t03_result: T03CompetitionResult) -> float:
    base_map = {
        T03ConvergenceStatus.STABLE_LOCAL_CONVERGENCE: 0.82,
        T03ConvergenceStatus.PROVISIONAL_CONVERGENCE: 0.58,
        T03ConvergenceStatus.CONTINUE_COMPETING: 0.46,
        T03ConvergenceStatus.HONEST_NONCONVERGENCE: 0.34,
    }
    base = base_map[t03_result.state.convergence_status]
    unresolved_penalty = min(0.25, 0.03 * len(t03_result.state.publication_frontier.open_slots))
    conflict_penalty = min(
        0.25, 0.05 * len(t03_result.state.publication_frontier.unresolved_conflicts)
    )
    return max(0.0, min(1.0, base - unresolved_penalty - conflict_penalty))


def _derive_control_estimate(
    *,
    t03_result: T03CompetitionResult,
    attention_owner: T04AttentionOwner,
    c04_execution_mode_claim: str,
) -> float:
    score = 0.42
    if attention_owner is T04AttentionOwner.SELF_GUIDED:
        score += 0.28
    if attention_owner is T04AttentionOwner.VALIDITY_GUARDED:
        score -= 0.14
    if t03_result.state.convergence_status is T03ConvergenceStatus.STABLE_LOCAL_CONVERGENCE:
        score += 0.18
    elif t03_result.state.convergence_status is T03ConvergenceStatus.HONEST_NONCONVERGENCE:
        score -= 0.14
    if c04_execution_mode_claim in {"monitor_only", "idle", "hold_safe_idle"}:
        score -= 0.08
    return max(0.0, min(1.0, score))


def _derive_redirect_cost(
    *,
    peripheral_targets: tuple[T04AttentionTarget, ...],
    t03_result: T03CompetitionResult,
) -> float:
    base = 0.12
    base += 0.08 * len(peripheral_targets)
    base += 0.06 * len(t03_result.state.publication_frontier.unresolved_conflicts)
    if t03_result.state.honest_nonconvergence:
        base += 0.15
    return max(0.0, min(1.0, base))


def _derive_focus_mode(
    *,
    focus_targets: tuple[T04AttentionTarget, ...],
    peripheral_targets: tuple[T04AttentionTarget, ...],
    stability_estimate: float,
) -> T04FocusMode:
    if not focus_targets:
        return T04FocusMode.PERIPHERAL_SCAN
    if len(focus_targets) > 1:
        return T04FocusMode.SPLIT_FOCUS
    if peripheral_targets and stability_estimate < 0.65:
        return T04FocusMode.GUARDED_SINGLE_FOCUS
    return T04FocusMode.SINGLE_FOCUS


def _derive_reportability_status(
    *,
    focus_targets: tuple[T04AttentionTarget, ...],
    control_estimate: float,
    stability_estimate: float,
) -> T04ReportabilityStatus:
    if not focus_targets:
        return T04ReportabilityStatus.NOT_REPORTABLE
    if control_estimate >= 0.62 and stability_estimate >= 0.72:
        return T04ReportabilityStatus.REPORTABLE_STABLE
    if control_estimate >= 0.42 and stability_estimate >= 0.45:
        return T04ReportabilityStatus.REPORTABLE_PROVISIONAL
    return T04ReportabilityStatus.NOT_REPORTABLE


def _derive_forbidden_shortcuts(
    *,
    focus_targets: tuple[T04AttentionTarget, ...],
    peripheral_targets: tuple[T04AttentionTarget, ...],
    attention_owner: T04AttentionOwner,
    reportability_status: T04ReportabilityStatus,
    stability_estimate: float,
    t03_result: T03CompetitionResult,
    c05_validity_action: str,
) -> tuple[str, ...]:
    shortcuts: list[str] = []
    uncertainty_present = bool(
        t03_result.state.honest_nonconvergence
        or t03_result.state.tied_competitor_ids
        or t03_result.state.publication_frontier.unresolved_conflicts
        or t03_result.state.publication_frontier.open_slots
    )
    if uncertainty_present and not peripheral_targets:
        shortcuts.append(ForbiddenT04Shortcut.PERIPHERAL_UNCERTAINTY_COLLAPSED.value)
    if (
        focus_targets
        and attention_owner is T04AttentionOwner.SELF_GUIDED
        and c05_validity_action in _REVALIDATE_ACTIONS
    ):
        shortcuts.append(ForbiddenT04Shortcut.HIGHEST_SALIENCE_AS_ATTENTION_SCHEMA.value)
    if (
        reportability_status is T04ReportabilityStatus.REPORTABLE_STABLE
        and stability_estimate < 0.72
    ):
        shortcuts.append(ForbiddenT04Shortcut.REPORTABILITY_OVERSTATED_WHEN_UNSTABLE.value)
    if attention_owner.value.strip() == "":
        shortcuts.append(ForbiddenT04Shortcut.OWNERSHIP_DROPPED_FROM_EXPORT.value)
    return tuple(dict.fromkeys(shortcuts))


def _build_gate(
    *,
    focus_targets: tuple[T04AttentionTarget, ...],
    peripheral_targets: tuple[T04AttentionTarget, ...],
    attention_owner: T04AttentionOwner,
    control_estimate: float,
    reportability_status: T04ReportabilityStatus,
    t03_result: T03CompetitionResult,
    forbidden_shortcuts: tuple[str, ...],
) -> T04GateDecision:
    focus_ownership_consumer_ready = bool(
        focus_targets
        and attention_owner in {T04AttentionOwner.SELF_GUIDED, T04AttentionOwner.VALIDITY_GUARDED}
        and control_estimate >= 0.45
    )
    reportable_focus_consumer_ready = reportability_status in {
        T04ReportabilityStatus.REPORTABLE_STABLE,
        T04ReportabilityStatus.REPORTABLE_PROVISIONAL,
    }
    uncertainty_present = bool(
        t03_result.state.honest_nonconvergence
        or t03_result.state.tied_competitor_ids
        or t03_result.state.publication_frontier.unresolved_conflicts
        or t03_result.state.publication_frontier.open_slots
    )
    peripheral_preservation_ready = bool(not uncertainty_present or peripheral_targets)
    restrictions: list[str] = [
        "t04_attention_schema_contract_must_be_read",
        "t04_focus_peripheral_split_must_be_read",
        "t04_attention_owner_must_be_read",
        "t04_reportability_vs_stability_must_be_read",
    ]
    if not focus_ownership_consumer_ready:
        restrictions.append("t04_focus_ownership_consumer_not_ready")
    if not reportable_focus_consumer_ready:
        restrictions.append("t04_reportable_focus_consumer_not_ready")
    if not peripheral_preservation_ready:
        restrictions.append("t04_peripheral_preservation_not_ready")
    if forbidden_shortcuts:
        restrictions.append("t04_forbidden_shortcut_detected")
    return T04GateDecision(
        focus_ownership_consumer_ready=focus_ownership_consumer_ready,
        reportable_focus_consumer_ready=reportable_focus_consumer_ready,
        peripheral_preservation_ready=peripheral_preservation_ready,
        forbidden_shortcuts=forbidden_shortcuts,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "t04 produced bounded attention schema with explicit focus ownership and peripheral preservation over t03 frontier"
        ),
    )


def _build_scope_marker() -> T04ScopeMarker:
    return T04ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        t04_first_slice_only=True,
        o01_implemented=False,
        o02_implemented=False,
        o03_implemented=False,
        full_attention_line_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "first bounded t04 slice only; o-line and full attention/global-workspace semantics remain out of scope"
        ),
    )
