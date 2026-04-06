from __future__ import annotations

from dataclasses import dataclass, replace
import re
from uuid import uuid4

from substrate.affordances.models import AffordanceResult
from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.mode_arbitration.models import ModeArbitrationResult, ModeArbitrationState
from substrate.regulation.models import RegulationResult, RegulationState
from substrate.regulatory_preferences.models import PreferenceState, PreferenceUpdateResult
from substrate.stream_diversification.models import (
    DiversificationDecisionStatus,
    StreamDiversificationResult,
    StreamDiversificationState,
)
from substrate.stream_kernel.models import (
    StreamKernelResult,
    StreamKernelState,
    StreamLinkDecision,
)
from substrate.temporal_validity.models import (
    RevalidationScope,
    TemporalCarryoverItem,
    TemporalCarryoverItemKind,
    TemporalValidityContext,
    TemporalValidityItem,
    TemporalValidityLedgerEvent,
    TemporalValidityLedgerEventKind,
    TemporalValidityResult,
    TemporalValidityState,
    TemporalValidityStatus,
)
from substrate.temporal_validity.policy import evaluate_temporal_validity_downstream_gate
from substrate.temporal_validity.telemetry import (
    build_temporal_validity_telemetry,
    temporal_validity_result_snapshot,
)
from substrate.tension_scheduler.models import (
    TensionSchedulerResult,
    TensionSchedulerState,
    TensionSchedulingMode,
)
from substrate.transition import execute_transition
from substrate.viability_control.models import ViabilityControlResult, ViabilityControlState


ATTEMPTED_TEMPORAL_VALIDITY_PATHS: tuple[str, ...] = (
    "temporal_validity.validate_typed_inputs",
    "temporal_validity.collect_continuity_relevant_items",
    "temporal_validity.evaluate_dependency_hits",
    "temporal_validity.assign_selective_validity_statuses",
    "temporal_validity.propagate_dependency_invalidation",
    "temporal_validity.provisional_grace_handling",
    "temporal_validity.selective_revalidation_scope",
    "temporal_validity.downstream_gate",
)

_TRIGGER_FAMILY_ALIASES: dict[str, str] = {
    "trigger:mode_shift": "family:mode_shift",
    "c04.mode_hold_permission": "family:mode_shift",
    "context:c04_mode_shift": "family:mode_shift",
    "trigger:tension_closed": "family:tension_closed",
    "c02.revisit_basis": "family:tension_closed",
    "trigger:diversification_conflict": "family:diversification_conflict",
    "c03.branch_access_gate": "family:diversification_conflict",
    "trigger:anchor_withdrawal": "family:anchor_withdrawal",
    "trigger:stream_source_withdrawal": "family:anchor_withdrawal",
    "trigger:justification_withdrawal": "family:justification_withdrawal",
}

_INCOMPLETE_GRAPH_STRICT_REVALIDATION_KINDS: tuple[TemporalCarryoverItemKind, ...] = (
    TemporalCarryoverItemKind.MODE_HOLD_PERMISSION,
    TemporalCarryoverItemKind.REVISIT_BASIS,
)

_INCOMPLETE_GRAPH_NO_SAFE_KINDS: tuple[TemporalCarryoverItemKind, ...] = (
    TemporalCarryoverItemKind.CARRIED_ASSUMPTION,
    TemporalCarryoverItemKind.BRANCH_ACCESS_GATE,
    TemporalCarryoverItemKind.PROVISIONAL_BINDING_OR_PERMISSION,
)

_ROOT_ANCHOR_STRICT_DEPENDENT_KINDS: tuple[TemporalCarryoverItemKind, ...] = (
    TemporalCarryoverItemKind.MODE_HOLD_PERMISSION,
    TemporalCarryoverItemKind.REVISIT_BASIS,
)


@dataclass(frozen=True, slots=True)
class _CandidateItem:
    item_id: str
    item_kind: TemporalCarryoverItemKind
    source_provenance: str
    dependency_set: tuple[str, ...]
    dependent_item_ids: tuple[str, ...]
    invalidation_triggers: tuple[str, ...]
    confidence: float
    basis: str


def build_temporal_validity(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
    tension_scheduler_state_or_result: TensionSchedulerState | TensionSchedulerResult,
    diversification_state_or_result: StreamDiversificationState | StreamDiversificationResult,
    mode_arbitration_state_or_result: ModeArbitrationState | ModeArbitrationResult,
    regulation_state_or_result: RegulationState | RegulationResult,
    affordance_result: AffordanceResult,
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
    context: TemporalValidityContext | None = None,
) -> TemporalValidityResult:
    context = context or TemporalValidityContext()
    if not isinstance(context, TemporalValidityContext):
        raise TypeError("context must be TemporalValidityContext")
    if context.step_delta < 1:
        raise ValueError("context.step_delta must be >= 1")
    if not isinstance(affordance_result, AffordanceResult):
        raise TypeError("build_temporal_validity requires typed AffordanceResult")

    stream_state = _extract_stream_input(stream_state_or_result)
    scheduler_state = _extract_scheduler_input(tension_scheduler_state_or_result)
    diversification_state = _extract_diversification_input(diversification_state_or_result)
    mode_state = _extract_mode_input(mode_arbitration_state_or_result)
    _, regulation_ref = _extract_regulation_input(regulation_state_or_result)
    _, preference_ref = _extract_preference_input(preference_state_or_result)
    _, viability_ref = _extract_viability_input(viability_state_or_result)
    prior = context.prior_temporal_validity_state
    if prior is not None and not isinstance(prior, TemporalValidityState):
        raise TypeError("context.prior_temporal_validity_state must be TemporalValidityState")

    candidates = _collect_temporal_candidates(
        stream_state=stream_state,
        scheduler_state=scheduler_state,
        diversification_state=diversification_state,
        mode_state=mode_state,
    )
    items = _evaluate_candidates(
        candidates=candidates,
        stream_state=stream_state,
        context=context,
        prior_state=prior,
    )
    if not context.disable_propagation_logic:
        items = _apply_dependency_propagation(items)

    selective_targets = _select_revalidation_targets(items=items, context=context)
    invalidated_ids = tuple(
        item.item_id
        for item in items
        if item.current_validity_status == TemporalValidityStatus.INVALIDATED
    )
    expired_ids = tuple(
        item.item_id
        for item in items
        if item.current_validity_status == TemporalValidityStatus.EXPIRED
    )
    dependency_contaminated_ids = tuple(
        item.item_id
        for item in items
        if item.current_validity_status == TemporalValidityStatus.DEPENDENCY_CONTAMINATED
    )
    no_safe_reuse_ids = tuple(
        item.item_id
        for item in items
        if item.current_validity_status == TemporalValidityStatus.NO_SAFE_REUSE_CLAIM
    )
    reusable_ids = tuple(
        item.item_id
        for item in items
        if item.current_validity_status == TemporalValidityStatus.STILL_VALID
    )
    provisional_ids = tuple(
        item.item_id
        for item in items
        if item.current_validity_status == TemporalValidityStatus.CONDITIONALLY_CARRIED
    )
    revalidation_ids = tuple(
        item.item_id
        for item in items
        if item.current_validity_status
        in {
            TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION,
            TemporalValidityStatus.NEEDS_FULL_REVALIDATION,
            TemporalValidityStatus.DEPENDENCY_CONTAMINATED,
            TemporalValidityStatus.NO_SAFE_REUSE_CLAIM,
        }
    )

    insufficient_basis_for_revalidation = bool(
        context.dependency_trigger_hits and not selective_targets and not invalidated_ids
    )
    provisional_carry_only = bool(
        provisional_ids and not reusable_ids and not revalidation_ids and not invalidated_ids
    )
    dependency_graph_incomplete = not context.dependency_graph_complete
    invalidation_possible_but_unproven = bool(
        context.context_shift_markers and not invalidated_ids and not revalidation_ids
    )
    selective_scope_uncertain = bool(
        context.disable_selective_scope_handling or dependency_graph_incomplete
    )

    state = TemporalValidityState(
        validity_id=f"temporal-validity-{stream_state.stream_id}",
        stream_id=stream_state.stream_id,
        source_stream_sequence_index=stream_state.sequence_index,
        items=items,
        reusable_item_ids=reusable_ids,
        provisional_item_ids=provisional_ids,
        revalidation_item_ids=revalidation_ids,
        invalidated_item_ids=invalidated_ids,
        expired_item_ids=expired_ids,
        dependency_contaminated_item_ids=dependency_contaminated_ids,
        no_safe_reuse_item_ids=no_safe_reuse_ids,
        selective_scope_targets=selective_targets,
        insufficient_basis_for_revalidation=insufficient_basis_for_revalidation,
        provisional_carry_only=provisional_carry_only,
        dependency_graph_incomplete=dependency_graph_incomplete,
        invalidation_possible_but_unproven=invalidation_possible_but_unproven,
        selective_scope_uncertain=selective_scope_uncertain,
        source_c01_state_ref=f"{stream_state.stream_id}@{stream_state.sequence_index}",
        source_c02_state_ref=(
            f"{scheduler_state.scheduler_id}@{scheduler_state.source_stream_sequence_index}"
        ),
        source_c03_state_ref=(
            f"{diversification_state.diversification_id}@{diversification_state.source_stream_sequence_index}"
        ),
        source_c04_state_ref=(
            f"{mode_state.arbitration_id}@{mode_state.source_stream_sequence_index}"
        ),
        source_regulation_ref=regulation_ref,
        source_affordance_ref=f"affordance-candidates:{len(affordance_result.candidates)}",
        source_preference_ref=preference_ref,
        source_viability_ref=viability_ref,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *context.source_lineage,
                    *stream_state.source_lineage,
                    *scheduler_state.source_lineage,
                    *diversification_state.source_lineage,
                    *mode_state.source_lineage,
                )
            )
        ),
        last_update_provenance="c05.temporal_validity_from_c01_c02_c03_c04",
    )
    gate = evaluate_temporal_validity_downstream_gate(state)
    ledger_events = _build_ledger_events(
        stream_id=state.stream_id,
        items=state.items,
    )
    telemetry = build_temporal_validity_telemetry(
        state=state,
        ledger_events=ledger_events,
        attempted_paths=ATTEMPTED_TEMPORAL_VALIDITY_PATHS,
        downstream_gate=gate,
        causal_basis=(
            "typed dependency-aware temporal validity with selective revalidation and bounded provisional carry discipline"
        ),
    )
    abstain = bool(
        (
            state.insufficient_basis_for_revalidation
            or state.selective_scope_uncertain
            or state.dependency_graph_incomplete
        )
        and not state.reusable_item_ids
    )
    abstain_reason = (
        "insufficient_basis_for_revalidation"
        if state.insufficient_basis_for_revalidation
        else "selective_scope_uncertain"
        if state.selective_scope_uncertain
        else "dependency_graph_incomplete"
        if state.dependency_graph_incomplete and abstain
        else None
    )
    return TemporalValidityResult(
        state=state,
        downstream_gate=gate,
        telemetry=telemetry,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_ttl_only_shortcut_dependency=True,
        no_blanket_reset_dependency=True,
        no_blanket_reuse_dependency=True,
        no_global_recompute_dependency=True,
    )


def temporal_validity_result_to_payload(result: TemporalValidityResult) -> dict[str, object]:
    return temporal_validity_result_snapshot(result)


def persist_temporal_validity_result_via_f01(
    *,
    result: TemporalValidityResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("c05-temporal-validity-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"temporal-validity-step-{result.state.source_stream_sequence_index}",
            "temporal_validity_snapshot": temporal_validity_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _collect_temporal_candidates(
    *,
    stream_state: StreamKernelState,
    scheduler_state: TensionSchedulerState,
    diversification_state: StreamDiversificationState,
    mode_state: ModeArbitrationState,
) -> tuple[TemporalCarryoverItem, ...]:
    entries: list[_CandidateItem] = []
    stream_anchor_id = f"stream-anchor:{stream_state.stream_id}"

    if stream_state.carryover_items or stream_state.unresolved_anchors or stream_state.pending_operations:
        entries.append(
            _CandidateItem(
                item_id=stream_anchor_id,
                item_kind=TemporalCarryoverItemKind.STREAM_ANCHOR,
                source_provenance=stream_state.last_update_provenance,
                dependency_set=(
                    "c01.stream_anchor",
                    f"stream:{stream_state.stream_id}",
                    f"stream_link:{stream_state.link_decision.value}",
                ),
                dependent_item_ids=(),
                invalidation_triggers=(
                    "trigger:stream_link_break",
                    "trigger:stream_source_withdrawal",
                ),
                confidence=stream_state.continuity_confidence,
                basis="c01 continuity carryover basis",
            )
        )

    mode_hold_id = f"mode-hold:{stream_state.stream_id}"
    entries.append(
        _CandidateItem(
            item_id=mode_hold_id,
            item_kind=TemporalCarryoverItemKind.MODE_HOLD_PERMISSION,
            source_provenance=mode_state.last_update_provenance,
            dependency_set=(
                "c04.mode_hold_permission",
                f"mode:{mode_state.active_mode.value}",
                "c01.stream_anchor",
            ),
            dependent_item_ids=(),
            invalidation_triggers=(
                "trigger:mode_shift",
                "trigger:mode_confidence_drop",
            ),
            confidence=mode_state.arbitration_confidence,
            basis="c04 bounded mode continuation permission",
        )
    )

    for entry in scheduler_state.tensions[:3]:
        if entry.scheduling_mode not in {
            TensionSchedulingMode.REVISIT_NOW,
            TensionSchedulingMode.REOPEN_DUE_TO_TRIGGER,
            TensionSchedulingMode.DEFER_UNTIL_CONDITION,
        }:
            continue
        entries.append(
            _CandidateItem(
                item_id=f"revisit-basis:{entry.tension_id}",
                item_kind=TemporalCarryoverItemKind.REVISIT_BASIS,
                source_provenance=entry.provenance,
                dependency_set=(
                    "c02.revisit_basis",
                    f"anchor:{entry.causal_anchor}",
                    f"tension_status:{entry.current_status.value}",
                ),
                dependent_item_ids=(mode_hold_id,),
                invalidation_triggers=(
                    "trigger:tension_closed",
                    "trigger:anchor_withdrawal",
                ),
                confidence=entry.confidence,
                basis="c02 unresolved tension revisit basis",
            )
        )

    branch_id = f"branch-access:{stream_state.stream_id}"
    entries.append(
        _CandidateItem(
            item_id=branch_id,
            item_kind=TemporalCarryoverItemKind.BRANCH_ACCESS_GATE,
            source_provenance=diversification_state.last_update_provenance,
            dependency_set=(
                "c03.branch_access_gate",
                f"decision:{diversification_state.decision_status.value}",
            ),
            dependent_item_ids=(),
            invalidation_triggers=(
                "trigger:no_safe_diversification",
                "trigger:diversification_conflict",
            ),
            confidence=diversification_state.confidence,
            basis="c03 alternative access eligibility basis",
        )
    )

    if (
        diversification_state.decision_status == DiversificationDecisionStatus.JUSTIFIED_RECURRENCE
        or diversification_state.protected_recurrence_classes
    ):
        entries.append(
            _CandidateItem(
                item_id=f"carried-assumption:{stream_state.stream_id}",
                item_kind=TemporalCarryoverItemKind.CARRIED_ASSUMPTION,
                source_provenance=diversification_state.last_update_provenance,
                dependency_set=(
                    "c03.recurrence_justification",
                    "c01.stream_anchor",
                ),
                dependent_item_ids=(mode_hold_id, branch_id),
                invalidation_triggers=(
                    "trigger:justification_withdrawal",
                    "trigger:conflicting_new_basis",
                ),
                confidence=diversification_state.confidence,
                basis="c03 justified recurrence carry assumption",
            )
        )

    if (
        stream_state.link_decision
        in {
            StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
            StreamLinkDecision.AMBIGUOUS_LINK,
        }
        or mode_state.arbitration_confidence < 0.58
    ):
        entries.append(
            _CandidateItem(
                item_id=f"provisional-binding:{stream_state.stream_id}",
                item_kind=TemporalCarryoverItemKind.PROVISIONAL_BINDING_OR_PERMISSION,
                source_provenance=mode_state.last_update_provenance,
                dependency_set=(
                    "c04.provisional_binding",
                    "c01.stream_anchor",
                ),
                dependent_item_ids=(mode_hold_id,),
                invalidation_triggers=(
                    "trigger:provisional_timeout",
                    "trigger:basis_not_revalidated",
                ),
                confidence=min(mode_state.arbitration_confidence, stream_state.continuity_confidence),
                basis="c01/c04 degraded basis allows bounded provisional carry only",
            )
        )

    if not entries:
        return ()

    present_ids = {entry.item_id for entry in entries}
    out: list[TemporalCarryoverItem] = []
    for entry in entries:
        dependents = tuple(dep for dep in entry.dependent_item_ids if dep in present_ids)
        out.append(
            TemporalCarryoverItem(
                item_id=entry.item_id,
                item_kind=entry.item_kind,
                source_provenance=entry.source_provenance,
                dependency_set=entry.dependency_set,
                dependent_item_ids=dependents,
                invalidation_triggers=entry.invalidation_triggers,
                confidence=round(max(0.0, min(1.0, entry.confidence)), 4),
                basis=entry.basis,
            )
        )

    if stream_anchor_id in {item.item_id for item in out}:
        out = [
            replace(
                item,
                dependent_item_ids=tuple(
                    dict.fromkeys(
                        (
                            *item.dependent_item_ids,
                            *(other.item_id for other in out if other.item_id != stream_anchor_id),
                        )
                    )
                ),
            )
            if item.item_id == stream_anchor_id
            else item
            for item in out
        ]
    return tuple(out)


def _evaluate_candidates(
    *,
    candidates: tuple[TemporalCarryoverItem, ...],
    stream_state: StreamKernelState,
    context: TemporalValidityContext,
    prior_state: TemporalValidityState | None,
) -> tuple[TemporalValidityItem, ...]:
    if not candidates:
        return ()
    prior_map = {item.item_id: item for item in prior_state.items} if prior_state else {}
    local_signal_present = bool(context.dependency_trigger_hits or context.context_shift_markers)
    items: list[TemporalValidityItem] = []
    for candidate in candidates:
        prior = prior_map.get(candidate.item_id)
        age_steps = (
            max(0, stream_state.sequence_index - prior.last_validated_sequence_index)
            if prior is not None
            else 0
        )
        full_revalidation = candidate.item_id in context.force_full_revalidation_items
        source_broken = _source_ref_is_broken(candidate.source_provenance, context=context)
        dependency_hit = (
            False
            if context.disable_dependency_trigger_logic
            else _dependency_hit(candidate, context=context)
        )
        weak_basis_no_safe = _should_use_no_safe_reuse_claim(
            candidate=candidate,
            age_steps=age_steps,
            context=context,
            dependency_hit=dependency_hit,
            local_signal_present=local_signal_present,
        )

        status: TemporalValidityStatus
        reusable_now: bool
        scope = RevalidationScope.NONE
        reason = "temporal_validity_assessed"
        grace_remaining = max(0, context.default_grace_window - age_steps)
        provisional_horizon = max(0, context.provisional_horizon_steps - age_steps)
        confidence = round(max(0.0, min(1.0, candidate.confidence)), 4)
        priority = 0.2

        if source_broken:
            status = TemporalValidityStatus.INVALIDATED
            reusable_now = False
            scope = RevalidationScope.ITEM_LOCAL
            reason = "source_withdrawn_or_contradicted"
            priority = 1.0
        elif full_revalidation:
            status = TemporalValidityStatus.NEEDS_FULL_REVALIDATION
            reusable_now = False
            scope = RevalidationScope.BOUNDED_GROUP
            reason = "explicit_full_revalidation_required"
            priority = 0.95
        elif dependency_hit:
            if context.dependency_graph_complete:
                status = TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION
                scope = RevalidationScope.DEPENDENCY_LOCAL
                reason = "relevant_dependency_trigger_hit"
                priority = 0.78
            else:
                status = TemporalValidityStatus.DEPENDENCY_CONTAMINATED
                scope = RevalidationScope.UNKNOWN
                reason = "dependency_hit_with_incomplete_graph"
                priority = 0.86
            reusable_now = False
        elif not context.dependency_graph_complete and candidate.dependency_set:
            if weak_basis_no_safe:
                status = TemporalValidityStatus.NO_SAFE_REUSE_CLAIM
                reusable_now = False
                scope = RevalidationScope.ITEM_LOCAL
                reason = "incomplete_graph_with_weak_basis_no_safe_reuse"
                priority = 0.81
            elif (
                local_signal_present
                and candidate.item_kind in _INCOMPLETE_GRAPH_STRICT_REVALIDATION_KINDS
            ):
                status = TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION
                reusable_now = False
                scope = RevalidationScope.ITEM_LOCAL
                reason = "incomplete_graph_local_unknown_requires_partial_revalidation"
                priority = 0.71
            elif context.allow_provisional_carry and not context.disable_provisional_handling:
                status = TemporalValidityStatus.CONDITIONALLY_CARRIED
                reusable_now = True
                scope = RevalidationScope.ITEM_LOCAL
                reason = "incomplete_graph_nonhit_conditional_carry"
                priority = 0.52
            else:
                status = TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION
                reusable_now = False
                scope = RevalidationScope.ITEM_LOCAL
                reason = "incomplete_graph_nonhit_requires_partial_revalidation"
                priority = 0.67
        elif confidence < 0.28:
            status = TemporalValidityStatus.NO_SAFE_REUSE_CLAIM
            reusable_now = False
            scope = RevalidationScope.ITEM_LOCAL
            reason = "confidence_too_low_for_safe_reuse"
            priority = 0.82
        elif age_steps > context.expire_after_steps:
            status = TemporalValidityStatus.EXPIRED
            reusable_now = False
            scope = RevalidationScope.ITEM_LOCAL
            reason = "expired_without_revalidation"
            priority = 0.84
        elif age_steps > context.default_grace_window:
            if context.allow_provisional_carry and not context.disable_provisional_handling:
                status = TemporalValidityStatus.CONDITIONALLY_CARRIED
                reusable_now = True
                scope = RevalidationScope.ITEM_LOCAL
                reason = "within_bounded_provisional_grace"
                priority = 0.54
            else:
                status = TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION
                reusable_now = False
                scope = RevalidationScope.ITEM_LOCAL
                reason = "grace_window_elapsed_requires_revalidation"
                priority = 0.69
        else:
            status = TemporalValidityStatus.STILL_VALID
            reusable_now = True
            scope = RevalidationScope.NONE
            reason = "dependencies_stable_and_within_validity_window"
            priority = 0.2

        if (
            candidate.item_kind == TemporalCarryoverItemKind.PROVISIONAL_BINDING_OR_PERMISSION
            and status == TemporalValidityStatus.STILL_VALID
        ):
            status = TemporalValidityStatus.CONDITIONALLY_CARRIED
            reusable_now = True
            scope = RevalidationScope.ITEM_LOCAL
            reason = "provisional_binding_cannot_upgrade_to_strong_validity"
            priority = max(priority, 0.46)

        items.append(
            TemporalValidityItem(
                item_id=candidate.item_id,
                item_kind=candidate.item_kind,
                source_provenance=candidate.source_provenance,
                dependency_set=candidate.dependency_set,
                dependent_item_ids=candidate.dependent_item_ids,
                current_validity_status=status,
                reusable_now=reusable_now,
                revalidation_priority=round(max(0.0, min(1.0, priority)), 4),
                revalidation_scope=scope,
                invalidation_triggers=candidate.invalidation_triggers,
                last_validated_sequence_index=stream_state.sequence_index,
                grace_window_remaining=grace_remaining,
                provisional_horizon=provisional_horizon,
                confidence=confidence,
                reason=reason,
                provenance="c05.temporal_validity_item",
            )
        )
    return tuple(items)


def _apply_dependency_propagation(
    items: tuple[TemporalValidityItem, ...],
) -> tuple[TemporalValidityItem, ...]:
    item_map = {item.item_id: item for item in items}
    contaminated_sources = {
        item.item_id
        for item in items
        if item.current_validity_status
        in {
            TemporalValidityStatus.INVALIDATED,
            TemporalValidityStatus.EXPIRED,
            TemporalValidityStatus.DEPENDENCY_CONTAMINATED,
            TemporalValidityStatus.NO_SAFE_REUSE_CLAIM,
            TemporalValidityStatus.NEEDS_FULL_REVALIDATION,
        }
    }
    changed = True
    while changed:
        changed = False
        for source_id in tuple(contaminated_sources):
            source = item_map.get(source_id)
            if source is None:
                continue
            for dependent_id in source.dependent_item_ids:
                dependent = item_map.get(dependent_id)
                if dependent is None:
                    continue
                if dependent.current_validity_status in {
                    TemporalValidityStatus.INVALIDATED,
                    TemporalValidityStatus.EXPIRED,
                    TemporalValidityStatus.DEPENDENCY_CONTAMINATED,
                    TemporalValidityStatus.NO_SAFE_REUSE_CLAIM,
                }:
                    continue
                if (
                    source.item_kind == TemporalCarryoverItemKind.STREAM_ANCHOR
                    and dependent.item_kind not in _ROOT_ANCHOR_STRICT_DEPENDENT_KINDS
                ):
                    if dependent.current_validity_status in {
                        TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION,
                        TemporalValidityStatus.NEEDS_FULL_REVALIDATION,
                    }:
                        continue
                    updated = replace(
                        dependent,
                        current_validity_status=TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION,
                        reusable_now=False,
                        revalidation_priority=max(dependent.revalidation_priority, 0.72),
                        revalidation_scope=RevalidationScope.ITEM_LOCAL,
                        reason=f"root_anchor_review_required_by:{source_id}",
                    )
                    item_map[dependent_id] = updated
                    changed = True
                    continue

                updated = replace(
                    dependent,
                    current_validity_status=TemporalValidityStatus.DEPENDENCY_CONTAMINATED,
                    reusable_now=False,
                    revalidation_priority=max(dependent.revalidation_priority, 0.8),
                    revalidation_scope=RevalidationScope.DEPENDENCY_LOCAL,
                    reason=f"dependency_contaminated_by:{source_id}",
                )
                item_map[dependent_id] = updated
                contaminated_sources.add(dependent_id)
                changed = True
    return tuple(item_map[item.item_id] for item in items)


def _select_revalidation_targets(
    *,
    items: tuple[TemporalValidityItem, ...],
    context: TemporalValidityContext,
) -> tuple[str, ...]:
    affected = tuple(
        item.item_id
        for item in items
        if item.current_validity_status
        in {
            TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION,
            TemporalValidityStatus.NEEDS_FULL_REVALIDATION,
            TemporalValidityStatus.DEPENDENCY_CONTAMINATED,
            TemporalValidityStatus.NO_SAFE_REUSE_CLAIM,
            TemporalValidityStatus.INVALIDATED,
            TemporalValidityStatus.EXPIRED,
        }
    )
    if not affected:
        return ()
    if context.disable_selective_scope_handling:
        return tuple(item.item_id for item in items)
    return tuple(dict.fromkeys(affected))


def _dependency_hit(
    candidate: TemporalCarryoverItem,
    *,
    context: TemporalValidityContext,
) -> bool:
    trigger_hits = _collect_marker_families(context.dependency_trigger_hits)
    shift_hits = _collect_marker_families(context.context_shift_markers)
    triggers = _collect_marker_families(candidate.invalidation_triggers)
    dependencies = _collect_marker_families(candidate.dependency_set)
    if triggers.intersection(trigger_hits):
        return True
    if dependencies.intersection(trigger_hits):
        return True
    if dependencies.intersection(shift_hits):
        return True
    return False


def _collect_marker_families(markers: tuple[str, ...]) -> set[str]:
    families: set[str] = set()
    for marker in markers:
        key = _normalize_marker_key(marker)
        if not key:
            continue
        families.add(key)
        alias = _TRIGGER_FAMILY_ALIASES.get(key)
        if alias is not None:
            families.add(alias)
    return families


def _normalize_marker_key(marker: str) -> str:
    trimmed = marker.strip()
    if not trimmed:
        return ""
    with_separators = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", trimmed)
    canonical = with_separators.lower().replace("-", "_").replace(" ", "")
    return canonical


def _should_use_no_safe_reuse_claim(
    *,
    candidate: TemporalCarryoverItem,
    age_steps: int,
    context: TemporalValidityContext,
    dependency_hit: bool,
    local_signal_present: bool,
) -> bool:
    if context.dependency_graph_complete:
        return False
    if dependency_hit:
        return False
    if not local_signal_present:
        return False
    if candidate.item_kind not in _INCOMPLETE_GRAPH_NO_SAFE_KINDS:
        return False
    if "c01.stream_anchor" not in candidate.dependency_set:
        return False
    weak_confidence = candidate.confidence < 0.68
    aged_basis = age_steps > max(1, context.default_grace_window)
    return weak_confidence or aged_basis


def _source_ref_is_broken(
    source_ref: str,
    *,
    context: TemporalValidityContext,
) -> bool:
    broken_refs = set(context.withdrawn_source_refs).union(context.contradicted_source_refs)
    if source_ref in broken_refs:
        return True
    return any(
        source_ref.startswith(f"{broken}:") or source_ref.startswith(f"{broken}@")
        for broken in broken_refs
    )


def _build_ledger_events(
    *,
    stream_id: str,
    items: tuple[TemporalValidityItem, ...],
) -> tuple[TemporalValidityLedgerEvent, ...]:
    events: list[TemporalValidityLedgerEvent] = []
    for item in items:
        events.append(
            _ledger_event(
                stream_id=stream_id,
                item_id=item.item_id,
                event_kind=TemporalValidityLedgerEventKind.ASSESSED,
                reason=item.reason,
                reason_code="item_assessed",
            )
        )
        kind = {
            TemporalValidityStatus.STILL_VALID: TemporalValidityLedgerEventKind.STILL_VALID,
            TemporalValidityStatus.CONDITIONALLY_CARRIED: TemporalValidityLedgerEventKind.CONDITIONALLY_CARRIED,
            TemporalValidityStatus.NEEDS_PARTIAL_REVALIDATION: TemporalValidityLedgerEventKind.PARTIAL_REVALIDATION_REQUIRED,
            TemporalValidityStatus.NEEDS_FULL_REVALIDATION: TemporalValidityLedgerEventKind.FULL_REVALIDATION_REQUIRED,
            TemporalValidityStatus.INVALIDATED: TemporalValidityLedgerEventKind.INVALIDATED,
            TemporalValidityStatus.EXPIRED: TemporalValidityLedgerEventKind.EXPIRED,
            TemporalValidityStatus.DEPENDENCY_CONTAMINATED: TemporalValidityLedgerEventKind.DEPENDENCY_CONTAMINATED,
            TemporalValidityStatus.NO_SAFE_REUSE_CLAIM: TemporalValidityLedgerEventKind.NO_SAFE_REUSE,
        }[item.current_validity_status]
        events.append(
            _ledger_event(
                stream_id=stream_id,
                item_id=item.item_id,
                event_kind=kind,
                reason=item.reason,
                reason_code=item.current_validity_status.value,
            )
        )
    return tuple(events)


def _ledger_event(
    *,
    stream_id: str,
    item_id: str,
    event_kind: TemporalValidityLedgerEventKind,
    reason: str,
    reason_code: str,
) -> TemporalValidityLedgerEvent:
    return TemporalValidityLedgerEvent(
        event_id=f"c05-ledger-{uuid4().hex[:10]}",
        event_kind=event_kind,
        item_id=item_id,
        stream_id=stream_id,
        reason=reason,
        reason_code=reason_code,
        provenance="c05.temporal_validity_ledger",
    )


def _extract_stream_input(
    stream_state_or_result: StreamKernelState | StreamKernelResult,
) -> StreamKernelState:
    if isinstance(stream_state_or_result, StreamKernelResult):
        return stream_state_or_result.state
    if isinstance(stream_state_or_result, StreamKernelState):
        return stream_state_or_result
    raise TypeError("build_temporal_validity requires StreamKernelState or StreamKernelResult")


def _extract_scheduler_input(
    tension_scheduler_state_or_result: TensionSchedulerState | TensionSchedulerResult,
) -> TensionSchedulerState:
    if isinstance(tension_scheduler_state_or_result, TensionSchedulerResult):
        return tension_scheduler_state_or_result.state
    if isinstance(tension_scheduler_state_or_result, TensionSchedulerState):
        return tension_scheduler_state_or_result
    raise TypeError(
        "build_temporal_validity requires TensionSchedulerState or TensionSchedulerResult"
    )


def _extract_diversification_input(
    diversification_state_or_result: StreamDiversificationState | StreamDiversificationResult,
) -> StreamDiversificationState:
    if isinstance(diversification_state_or_result, StreamDiversificationResult):
        return diversification_state_or_result.state
    if isinstance(diversification_state_or_result, StreamDiversificationState):
        return diversification_state_or_result
    raise TypeError(
        "build_temporal_validity requires StreamDiversificationState or StreamDiversificationResult"
    )


def _extract_mode_input(
    mode_arbitration_state_or_result: ModeArbitrationState | ModeArbitrationResult,
) -> ModeArbitrationState:
    if isinstance(mode_arbitration_state_or_result, ModeArbitrationResult):
        return mode_arbitration_state_or_result.state
    if isinstance(mode_arbitration_state_or_result, ModeArbitrationState):
        return mode_arbitration_state_or_result
    raise TypeError(
        "build_temporal_validity requires ModeArbitrationState or ModeArbitrationResult"
    )


def _extract_regulation_input(
    regulation_state_or_result: RegulationState | RegulationResult,
) -> tuple[RegulationState, str]:
    if isinstance(regulation_state_or_result, RegulationResult):
        state = regulation_state_or_result.state
        return state, f"regulation-step-{state.last_updated_step}"
    if isinstance(regulation_state_or_result, RegulationState):
        state = regulation_state_or_result
        return state, f"regulation-step-{state.last_updated_step}"
    raise TypeError("build_temporal_validity requires RegulationState or RegulationResult")


def _extract_preference_input(
    preference_state_or_result: PreferenceState | PreferenceUpdateResult,
) -> tuple[PreferenceState, str]:
    if isinstance(preference_state_or_result, PreferenceUpdateResult):
        state = preference_state_or_result.updated_preference_state
        return state, f"preference-step-{state.last_updated_step}:{state.schema_version}"
    if isinstance(preference_state_or_result, PreferenceState):
        state = preference_state_or_result
        return state, f"preference-step-{state.last_updated_step}:{state.schema_version}"
    raise TypeError(
        "build_temporal_validity requires PreferenceState or PreferenceUpdateResult"
    )


def _extract_viability_input(
    viability_state_or_result: ViabilityControlState | ViabilityControlResult,
) -> tuple[ViabilityControlState, str]:
    if isinstance(viability_state_or_result, ViabilityControlResult):
        state = viability_state_or_result.state
        return (
            state,
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    if isinstance(viability_state_or_result, ViabilityControlState):
        state = viability_state_or_result
        return (
            state,
            f"viability:{state.calibration_id}:{state.calibration_formula_version}:{state.escalation_stage.value}",
        )
    raise TypeError(
        "build_temporal_validity requires ViabilityControlState or ViabilityControlResult"
    )
