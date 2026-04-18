from __future__ import annotations

from substrate.o03_strategy_class_evaluation import O03StrategyClass, O03StrategyEvaluationResult
from substrate.p01_project_formation.models import (
    P01AdmissibilityVerdict,
    P01ArbitrationOutcome,
    P01ArbitrationRecord,
    P01AuthoritySourceKind,
    P01CommitmentGrade,
    P01IntentionStackState,
    P01PriorityClass,
    P01ProjectEntry,
    P01ProjectFormationGateDecision,
    P01ProjectFormationResult,
    P01ProjectSignalInput,
    P01ProjectStatus,
    P01ScopeMarker,
    P01Telemetry,
)

_HIGH_AUTHORITY = {
    P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
    P01AuthoritySourceKind.STANDING_OBLIGATION,
    P01AuthoritySourceKind.SYSTEM_MAINTENANCE_REQUIREMENT,
    P01AuthoritySourceKind.CONTINUATION_COMMITMENT,
    P01AuthoritySourceKind.POLICY_GUARDRAIL_REQUIREMENT,
}

_AUTHORITY_WEIGHT = {
    P01AuthoritySourceKind.DISALLOWED_SELF_GENERATED_IDEA: 0,
    P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION: 1,
    P01AuthoritySourceKind.CLARIFICATION_REQUIRED_PRECONDITION: 2,
    P01AuthoritySourceKind.CONTINUATION_COMMITMENT: 3,
    P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE: 4,
    P01AuthoritySourceKind.STANDING_OBLIGATION: 5,
    P01AuthoritySourceKind.SYSTEM_MAINTENANCE_REQUIREMENT: 5,
    P01AuthoritySourceKind.POLICY_GUARDRAIL_REQUIREMENT: 6,
}

_PRIORITY_WEIGHT = {
    P01PriorityClass.BACKGROUND: 0,
    P01PriorityClass.DEFERRED: 1,
    P01PriorityClass.SECONDARY: 2,
    P01PriorityClass.PRIMARY: 3,
    P01PriorityClass.BLOCKING: 4,
}


def build_p01_project_formation(
    *,
    tick_id: str,
    tick_index: int,
    signals: tuple[P01ProjectSignalInput, ...] = (),
    prior_state: P01IntentionStackState | None = None,
    o03_result: O03StrategyEvaluationResult | None = None,
    source_lineage: tuple[str, ...] = (),
    formation_enabled: bool = True,
) -> P01ProjectFormationResult:
    if not formation_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    typed_signals = tuple(signal for signal in signals if isinstance(signal, P01ProjectSignalInput))
    prior_entries = _prior_entries(prior_state)
    prior_by_id = {entry.project_id: entry for entry in prior_entries}
    prior_by_identity = {entry.project_identity_key: entry for entry in prior_entries}

    active_projects: list[P01ProjectEntry] = []
    candidate_projects: list[P01ProjectEntry] = []
    suspended_projects: list[P01ProjectEntry] = []
    rejected_candidates: list[P01ProjectEntry] = []
    arbitration_records: list[P01ArbitrationRecord] = []

    no_safe_project_formation = False
    grounded_context_underconstrained = False
    prompt_local_capture_risk = False
    conflicting_authority = False
    blocked_pending_grounding = False
    candidate_only_without_activation_basis = False
    stale_active_project_detected = False
    o03_conservative_pressure = bool(
        isinstance(o03_result, O03StrategyEvaluationResult)
        and o03_result.state.strategy_class
        in {
            O03StrategyClass.MANIPULATION_RISK_HIGH,
            O03StrategyClass.HIGH_LOCAL_GAIN_BUT_HIGH_ENTROPY,
            O03StrategyClass.STRATEGY_CLASS_UNDERCONSTRAINED,
            O03StrategyClass.NO_SAFE_CLASSIFICATION,
        }
    )

    if not typed_signals:
        no_safe_project_formation = True
        grounded_context_underconstrained = True

    entries_by_conflict: dict[str, list[P01ProjectEntry]] = {}
    for index, signal in enumerate(typed_signals):
        identity_key = _normalize_identity_key(signal.target_summary)
        prior_match = _resolve_prior_match(
            signal=signal,
            prior_by_id=prior_by_id,
            prior_by_identity=prior_by_identity,
        )
        project_id = (
            prior_match.project_id
            if prior_match is not None
            else f"p01-project:{tick_id}:{index + 1}"
        )
        carryover_basis = (
            signal.continuation_of_prior_project_id
            if signal.continuation_of_prior_project_id
            else "identity_dedup"
            if prior_match is not None
            else None
        )

        verdict, status = _admissibility_and_status(
            signal=signal,
            o03_conservative_pressure=o03_conservative_pressure,
        )
        commitment_grade = _commitment_grade(signal, status=status)
        priority = signal.priority_hint or _priority_from_authority(signal.authority_source_kind)
        stale_risk_marker = bool(
            not signal.temporal_validity_marker
            or signal.missing_precondition_marker
            or signal.clarification_block_marker
            or (prior_match is not None and prior_match.stale_risk_marker)
        )
        if status is P01ProjectStatus.BLOCKED_BY_MISSING_PRECONDITION:
            blocked_pending_grounding = True
            candidate_only_without_activation_basis = True
        if verdict is P01AdmissibilityVerdict.INSUFFICIENT_BASIS_FOR_PROJECT:
            grounded_context_underconstrained = True
            candidate_only_without_activation_basis = True
        if verdict is P01AdmissibilityVerdict.CONFLICTING_AUTHORITY:
            conflicting_authority = True
        if status is P01ProjectStatus.CANDIDATE_ONLY:
            candidate_only_without_activation_basis = True
        if (
            signal.authority_source_kind is P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION
            and status is P01ProjectStatus.CANDIDATE_ONLY
        ):
            prompt_local_capture_risk = True

        entry = P01ProjectEntry(
            project_id=project_id,
            project_identity_key=identity_key,
            project_class=signal.signal_kind,
            source_of_authority=signal.authority_source_kind,
            objective_summary_or_typed_target=signal.target_summary,
            commitment_grade=commitment_grade,
            priority_class=priority,
            activation_conditions=_activation_conditions(signal),
            suspension_conditions=("temporal_validity_lost", "missing_precondition"),
            termination_conditions=("completion_evidence_present", "policy_disallow"),
            dependency_refs=_dependency_refs(signal),
            current_status=status,
            admissibility_verdict=verdict,
            provenance=signal.provenance,
            formation_trace_refs=(
                f"signal:{signal.signal_id}",
                f"authority:{signal.authority_source_kind.value}",
                f"verdict:{verdict.value}",
            ),
            carryover_basis=carryover_basis,
            stale_risk_marker=stale_risk_marker,
        )
        if signal.conflict_group_id:
            entries_by_conflict.setdefault(signal.conflict_group_id, []).append(entry)

        if status is P01ProjectStatus.ACTIVE:
            active_projects.append(entry)
        elif status is P01ProjectStatus.CANDIDATE_ONLY:
            candidate_projects.append(entry)
        elif status in {P01ProjectStatus.SUSPENDED, P01ProjectStatus.BLOCKED_BY_MISSING_PRECONDITION}:
            suspended_projects.append(entry)
        elif status in {
            P01ProjectStatus.REJECTED,
            P01ProjectStatus.CONFLICTED,
            P01ProjectStatus.TERMINATED,
            P01ProjectStatus.COMPLETED_CANDIDATE_ONLY,
        }:
            rejected_candidates.append(entry)

    _ingest_prior_carryover(
        prior_entries=prior_entries,
        emitted_ids={entry.project_id for entry in (*active_projects, *candidate_projects, *suspended_projects, *rejected_candidates)},
        active_projects=active_projects,
        suspended_projects=suspended_projects,
    )

    for conflict_group_id, entries in entries_by_conflict.items():
        if len(entries) <= 1:
            continue
        conflicting_authority = True
        sorted_entries = sorted(
            entries,
            key=lambda item: (
                _AUTHORITY_WEIGHT[item.source_of_authority],
                _PRIORITY_WEIGHT[item.priority_class],
            ),
            reverse=True,
        )
        winner = sorted_entries[0]
        second = sorted_entries[1]
        if (
            _AUTHORITY_WEIGHT[winner.source_of_authority]
            == _AUTHORITY_WEIGHT[second.source_of_authority]
            and _PRIORITY_WEIGHT[winner.priority_class]
            == _PRIORITY_WEIGHT[second.priority_class]
        ):
            outcome = P01ArbitrationOutcome.NO_SAFE_RESOLUTION
            no_safe_project_formation = True
            _mark_conflicted(entries, active_projects, rejected_candidates)
            arbitration_records.append(
                P01ArbitrationRecord(
                    arbitration_id=f"p01-arb:{tick_id}:{conflict_group_id}",
                    conflict_group_id=conflict_group_id,
                    involved_project_ids=tuple(item.project_id for item in entries),
                    outcome=outcome,
                    reason="same authority/priority on conflicting project signals",
                    provenance="p01.project_formation.arbitration",
                )
            )
            continue

        weaker = tuple(item for item in sorted_entries[1:])
        _reject_weaker_conflicts(weaker, active_projects, rejected_candidates)
        arbitration_records.append(
            P01ArbitrationRecord(
                arbitration_id=f"p01-arb:{tick_id}:{conflict_group_id}",
                conflict_group_id=conflict_group_id,
                involved_project_ids=tuple(item.project_id for item in sorted_entries),
                outcome=P01ArbitrationOutcome.REJECT_WEAKER_SOURCE,
                reason="authority/priority arbitration rejected weaker conflicting signals",
                provenance="p01.project_formation.arbitration",
            )
        )

    if not active_projects and (candidate_projects or suspended_projects):
        no_safe_project_formation = True
    if all(not signal.grounded_basis_present for signal in typed_signals):
        grounded_context_underconstrained = True
    if o03_conservative_pressure and not active_projects:
        candidate_only_without_activation_basis = True

    justification_links = tuple(
        dict.fromkeys(
            (
                f"signal_count:{len(typed_signals)}",
                f"active_projects:{len(active_projects)}",
                f"candidate_projects:{len(candidate_projects)}",
                f"suspended_projects:{len(suspended_projects)}",
                f"arbitration_records:{len(arbitration_records)}",
                f"o03_guard:{str(o03_conservative_pressure).lower()}",
            )
        )
    )
    source_lineage_full = tuple(
        dict.fromkeys(
            (
                *source_lineage,
                *(prior_state.source_lineage if isinstance(prior_state, P01IntentionStackState) else ()),
                *(
                    o03_result.state.source_lineage
                    if isinstance(o03_result, O03StrategyEvaluationResult)
                    else ()
                ),
            )
        )
    )
    state = P01IntentionStackState(
        stack_id=f"p01-stack:{tick_id}",
        active_projects=tuple(active_projects),
        candidate_projects=tuple(candidate_projects),
        suspended_projects=tuple(suspended_projects),
        rejected_candidates=tuple(rejected_candidates),
        arbitration_records=tuple(arbitration_records),
        no_safe_project_formation=no_safe_project_formation,
        grounded_context_underconstrained=grounded_context_underconstrained,
        prompt_local_capture_risk=prompt_local_capture_risk,
        bypass_resistance_status=(
            "prompt_local_substitution_guard_triggered"
            if prompt_local_capture_risk
            else "no_prompt_local_capture_detected"
        ),
        conflicting_authority=conflicting_authority,
        blocked_pending_grounding=blocked_pending_grounding,
        candidate_only_without_activation_basis=candidate_only_without_activation_basis,
        stale_active_project_detected=stale_active_project_detected,
        justification_links=justification_links,
        provenance="p01.project_formation.policy",
        source_lineage=source_lineage_full,
        last_update_provenance="p01.project_formation.policy",
    )
    gate = _build_gate(state)
    scope_marker = P01ScopeMarker(
        scope="rt01_hosted_p01_first_slice",
        rt01_hosted_only=True,
        p01_first_slice_only=True,
        p02_not_implemented=True,
        p03_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="bounded p01 slice; p02/p03/p04 and broad planner stack remain open",
    )
    telemetry = P01Telemetry(
        stack_id=state.stack_id,
        tick_index=tick_index,
        active_project_count=len(state.active_projects),
        candidate_project_count=len(state.candidate_projects),
        suspended_project_count=len(state.suspended_projects),
        rejected_project_count=len(state.rejected_candidates),
        arbitration_count=len(state.arbitration_records),
        no_safe_project_formation=state.no_safe_project_formation,
        conflicting_authority=state.conflicting_authority,
        blocked_pending_grounding=state.blocked_pending_grounding,
        prompt_local_capture_risk=state.prompt_local_capture_risk,
        downstream_consumer_ready=gate.project_handoff_consumer_ready,
    )
    reason = (
        "p01 formed bounded intention stack with authority-sensitive admissibility, project identity dedup and conflict arbitration"
    )
    return P01ProjectFormationResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=reason,
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> P01ProjectFormationResult:
    state = P01IntentionStackState(
        stack_id=f"p01-stack:{tick_id}",
        active_projects=(),
        candidate_projects=(),
        suspended_projects=(),
        rejected_candidates=(),
        arbitration_records=(),
        no_safe_project_formation=True,
        grounded_context_underconstrained=True,
        prompt_local_capture_risk=False,
        bypass_resistance_status="p01_disabled",
        conflicting_authority=False,
        blocked_pending_grounding=False,
        candidate_only_without_activation_basis=True,
        stale_active_project_detected=False,
        justification_links=("p01_disabled",),
        provenance="p01.project_formation.disabled",
        source_lineage=source_lineage,
        last_update_provenance="p01.project_formation.disabled",
    )
    gate = P01ProjectFormationGateDecision(
        intention_stack_consumer_ready=False,
        authority_bound_consumer_ready=False,
        project_handoff_consumer_ready=False,
        restrictions=(
            "p01_disabled",
            "no_safe_project_formation",
            "candidate_only_without_activation_basis",
        ),
        reason="p01 project formation disabled in ablation context",
    )
    scope_marker = P01ScopeMarker(
        scope="rt01_hosted_p01_first_slice",
        rt01_hosted_only=True,
        p01_first_slice_only=True,
        p02_not_implemented=True,
        p03_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="p01 disabled path",
    )
    telemetry = P01Telemetry(
        stack_id=state.stack_id,
        tick_index=tick_index,
        active_project_count=0,
        candidate_project_count=0,
        suspended_project_count=0,
        rejected_project_count=0,
        arbitration_count=0,
        no_safe_project_formation=True,
        conflicting_authority=False,
        blocked_pending_grounding=False,
        prompt_local_capture_risk=False,
        downstream_consumer_ready=False,
    )
    return P01ProjectFormationResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _build_gate(
    state: P01IntentionStackState,
) -> P01ProjectFormationGateDecision:
    intention_stack_ready = bool(state.active_projects or state.candidate_projects)
    authority_bound_ready = bool(
        not state.conflicting_authority and not state.prompt_local_capture_risk
    )
    project_handoff_ready = bool(
        authority_bound_ready
        and bool(state.active_projects)
        and not state.no_safe_project_formation
        and not state.blocked_pending_grounding
    )
    restrictions: list[str] = []
    if state.no_safe_project_formation:
        restrictions.append("no_safe_project_formation")
    if state.grounded_context_underconstrained:
        restrictions.append("grounded_context_underconstrained")
    if state.prompt_local_capture_risk:
        restrictions.append("prompt_local_capture_risk")
    if state.conflicting_authority:
        restrictions.append("conflicting_authority")
    if state.blocked_pending_grounding:
        restrictions.append("blocked_pending_grounding")
    if state.candidate_only_without_activation_basis:
        restrictions.append("candidate_only_without_activation_basis")
    if state.stale_active_project_detected:
        restrictions.append("stale_active_project_detected")
    if not project_handoff_ready:
        restrictions.append("project_handoff_not_ready")
    return P01ProjectFormationGateDecision(
        intention_stack_consumer_ready=intention_stack_ready,
        authority_bound_consumer_ready=authority_bound_ready,
        project_handoff_consumer_ready=project_handoff_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="p01 gate exposes bounded intention-stack, authority and handoff readiness",
    )


def _admissibility_and_status(
    *,
    signal: P01ProjectSignalInput,
    o03_conservative_pressure: bool,
) -> tuple[P01AdmissibilityVerdict, P01ProjectStatus]:
    if signal.authority_source_kind is P01AuthoritySourceKind.DISALLOWED_SELF_GENERATED_IDEA:
        return (
            P01AdmissibilityVerdict.REJECTED_AS_OUT_OF_SCOPE,
            P01ProjectStatus.REJECTED,
        )
    if signal.policy_disallow_marker:
        return (
            P01AdmissibilityVerdict.REJECTED_AS_OUT_OF_SCOPE,
            P01ProjectStatus.REJECTED,
        )
    if signal.completion_evidence_present:
        return (
            P01AdmissibilityVerdict.ADMITTED,
            P01ProjectStatus.TERMINATED,
        )
    if signal.missing_precondition_marker or signal.clarification_block_marker:
        return (
            P01AdmissibilityVerdict.BLOCKED_PENDING_GROUNDING,
            P01ProjectStatus.BLOCKED_BY_MISSING_PRECONDITION,
        )
    if not signal.grounded_basis_present:
        return (
            P01AdmissibilityVerdict.INSUFFICIENT_BASIS_FOR_PROJECT,
            P01ProjectStatus.CANDIDATE_ONLY,
        )
    if signal.authority_source_kind is P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION:
        return (
            P01AdmissibilityVerdict.CANDIDATE_ONLY,
            P01ProjectStatus.CANDIDATE_ONLY,
        )
    if not signal.temporal_validity_marker:
        return (
            P01AdmissibilityVerdict.ADMITTED,
            P01ProjectStatus.SUSPENDED,
        )
    if o03_conservative_pressure and signal.authority_source_kind not in _HIGH_AUTHORITY:
        return (
            P01AdmissibilityVerdict.CANDIDATE_ONLY,
            P01ProjectStatus.CANDIDATE_ONLY,
        )
    return (P01AdmissibilityVerdict.ADMITTED, P01ProjectStatus.ACTIVE)


def _activation_conditions(signal: P01ProjectSignalInput) -> tuple[str, ...]:
    conditions = ["grounded_basis_present", f"authority:{signal.authority_source_kind.value}"]
    if signal.resource_bound_marker:
        conditions.append("resource_bound")
    if signal.open_loop_marker:
        conditions.append("open_loop_present")
    if signal.persistent_obligation_marker:
        conditions.append("persistent_obligation")
    return tuple(conditions)


def _dependency_refs(signal: P01ProjectSignalInput) -> tuple[str, ...]:
    refs: list[str] = []
    if signal.continuation_of_prior_project_id:
        refs.append(signal.continuation_of_prior_project_id)
    if signal.blocker_present:
        refs.append(f"blocker:{signal.signal_id}")
    return tuple(refs)


def _priority_from_authority(authority: P01AuthoritySourceKind) -> P01PriorityClass:
    if authority in {
        P01AuthoritySourceKind.POLICY_GUARDRAIL_REQUIREMENT,
        P01AuthoritySourceKind.STANDING_OBLIGATION,
    }:
        return P01PriorityClass.BLOCKING
    if authority in {
        P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
        P01AuthoritySourceKind.SYSTEM_MAINTENANCE_REQUIREMENT,
    }:
        return P01PriorityClass.PRIMARY
    if authority is P01AuthoritySourceKind.CONTINUATION_COMMITMENT:
        return P01PriorityClass.SECONDARY
    if authority is P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION:
        return P01PriorityClass.DEFERRED
    return P01PriorityClass.BACKGROUND


def _commitment_grade(
    signal: P01ProjectSignalInput,
    *,
    status: P01ProjectStatus,
) -> P01CommitmentGrade:
    if status in {P01ProjectStatus.REJECTED, P01ProjectStatus.TERMINATED}:
        return P01CommitmentGrade.NONE
    if signal.authority_source_kind in {
        P01AuthoritySourceKind.STANDING_OBLIGATION,
        P01AuthoritySourceKind.SYSTEM_MAINTENANCE_REQUIREMENT,
        P01AuthoritySourceKind.POLICY_GUARDRAIL_REQUIREMENT,
    }:
        return P01CommitmentGrade.OBLIGATION_BOUND
    if signal.persistent_obligation_marker or signal.authority_source_kind is P01AuthoritySourceKind.CONTINUATION_COMMITMENT:
        return P01CommitmentGrade.PERSISTENT_BUT_BOUNDED
    if status is P01ProjectStatus.ACTIVE:
        return P01CommitmentGrade.TASK_BOUND
    return P01CommitmentGrade.PROVISIONAL


def _prior_entries(prior_state: P01IntentionStackState | None) -> tuple[P01ProjectEntry, ...]:
    if not isinstance(prior_state, P01IntentionStackState):
        return ()
    return tuple(
        dict.fromkeys(
            (
                *prior_state.active_projects,
                *prior_state.candidate_projects,
                *prior_state.suspended_projects,
                *prior_state.rejected_candidates,
            )
        )
    )


def _resolve_prior_match(
    *,
    signal: P01ProjectSignalInput,
    prior_by_id: dict[str, P01ProjectEntry],
    prior_by_identity: dict[str, P01ProjectEntry],
) -> P01ProjectEntry | None:
    if signal.continuation_of_prior_project_id:
        entry = prior_by_id.get(signal.continuation_of_prior_project_id)
        if entry is not None:
            return entry
    return prior_by_identity.get(_normalize_identity_key(signal.target_summary))


def _normalize_identity_key(text: str) -> str:
    normalized = " ".join(str(text or "").strip().lower().split())
    if not normalized:
        return "project:unspecified"
    token = "".join(ch for ch in normalized if ch.isalnum() or ch in {" ", "-", "_"}).strip()
    token = token.replace(" ", "_")
    if not token:
        return "project:unspecified"
    return token[:72]


def _ingest_prior_carryover(
    *,
    prior_entries: tuple[P01ProjectEntry, ...],
    emitted_ids: set[str],
    active_projects: list[P01ProjectEntry],
    suspended_projects: list[P01ProjectEntry],
) -> None:
    for entry in prior_entries:
        if entry.project_id in emitted_ids:
            continue
        if entry.current_status is P01ProjectStatus.ACTIVE and not entry.stale_risk_marker:
            active_projects.append(entry)
            continue
        if entry.current_status in {
            P01ProjectStatus.ACTIVE,
            P01ProjectStatus.CANDIDATE_ONLY,
            P01ProjectStatus.BLOCKED_BY_MISSING_PRECONDITION,
            P01ProjectStatus.SUSPENDED,
        }:
            suspended_projects.append(
                P01ProjectEntry(
                    project_id=entry.project_id,
                    project_identity_key=entry.project_identity_key,
                    project_class=entry.project_class,
                    source_of_authority=entry.source_of_authority,
                    objective_summary_or_typed_target=entry.objective_summary_or_typed_target,
                    commitment_grade=entry.commitment_grade,
                    priority_class=entry.priority_class,
                    activation_conditions=entry.activation_conditions,
                    suspension_conditions=entry.suspension_conditions,
                    termination_conditions=entry.termination_conditions,
                    dependency_refs=entry.dependency_refs,
                    current_status=P01ProjectStatus.SUSPENDED,
                    admissibility_verdict=entry.admissibility_verdict,
                    provenance=entry.provenance,
                    formation_trace_refs=entry.formation_trace_refs,
                    carryover_basis=entry.project_id,
                    stale_risk_marker=entry.stale_risk_marker,
                )
            )


def _mark_conflicted(
    entries: list[P01ProjectEntry],
    active_projects: list[P01ProjectEntry],
    rejected_candidates: list[P01ProjectEntry],
) -> None:
    active_ids = {item.project_id for item in active_projects}
    for entry in entries:
        if entry.project_id in active_ids:
            active_projects[:] = [
                item for item in active_projects if item.project_id != entry.project_id
            ]
        rejected_candidates.append(
            P01ProjectEntry(
                project_id=entry.project_id,
                project_identity_key=entry.project_identity_key,
                project_class=entry.project_class,
                source_of_authority=entry.source_of_authority,
                objective_summary_or_typed_target=entry.objective_summary_or_typed_target,
                commitment_grade=P01CommitmentGrade.PROVISIONAL,
                priority_class=entry.priority_class,
                activation_conditions=entry.activation_conditions,
                suspension_conditions=entry.suspension_conditions,
                termination_conditions=entry.termination_conditions,
                dependency_refs=entry.dependency_refs,
                current_status=P01ProjectStatus.CONFLICTED,
                admissibility_verdict=P01AdmissibilityVerdict.CONFLICTING_AUTHORITY,
                provenance=entry.provenance,
                formation_trace_refs=entry.formation_trace_refs,
                carryover_basis=entry.carryover_basis,
                stale_risk_marker=True,
            )
        )


def _reject_weaker_conflicts(
    weaker: tuple[P01ProjectEntry, ...],
    active_projects: list[P01ProjectEntry],
    rejected_candidates: list[P01ProjectEntry],
) -> None:
    active_ids = {item.project_id for item in active_projects}
    for entry in weaker:
        if entry.project_id in active_ids:
            active_projects[:] = [
                item for item in active_projects if item.project_id != entry.project_id
            ]
        rejected_candidates.append(
            P01ProjectEntry(
                project_id=entry.project_id,
                project_identity_key=entry.project_identity_key,
                project_class=entry.project_class,
                source_of_authority=entry.source_of_authority,
                objective_summary_or_typed_target=entry.objective_summary_or_typed_target,
                commitment_grade=P01CommitmentGrade.PROVISIONAL,
                priority_class=entry.priority_class,
                activation_conditions=entry.activation_conditions,
                suspension_conditions=entry.suspension_conditions,
                termination_conditions=entry.termination_conditions,
                dependency_refs=entry.dependency_refs,
                current_status=P01ProjectStatus.CONFLICTED,
                admissibility_verdict=P01AdmissibilityVerdict.CONFLICTING_AUTHORITY,
                provenance=entry.provenance,
                formation_trace_refs=entry.formation_trace_refs,
                carryover_basis=entry.carryover_basis,
                stale_risk_marker=entry.stale_risk_marker,
            )
        )

