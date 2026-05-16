from __future__ import annotations

from dataclasses import asdict, dataclass

from .clarification_policy import (
    ClarificationBudget,
    ClarificationDecisionRecord,
    ClarificationRoute,
    MissingInformationKind,
    ResponseReadinessDecision,
    ResponseReadinessStatus,
    evaluate_response_readiness,
)
from .models import CounterpartSignalKind, SubjectVisiblePacket, TransferOutcome
from .runner import run_stage1_scenario, run_stage25_reaction, run_stage3_response
from .transfer_affordance import (
    TransferAffordancePolicy,
    TransferAffordanceRecord,
    TransferAffordanceStatus,
    TransferAffordanceInvocationCandidate,
    TransferAttemptRecord,
    TransferEpisodeRecord,
    TransferResultRecord,
    build_invocation_candidate,
    build_transfer_affordance_record,
    execute_transfer_invocation,
    infer_transfer_affordance_status,
)


STAGE4_SCENARIOS: tuple[str, ...] = (
    "presence_only",
    "resource_claim_contact",
    "mirrored_resource_asymmetry",
    "false_counterpart_claim",
    "blocked_aperture",
    "noisy_signal",
    "transfer_seen_without_trade_token",
    "eval_label_leak_attack",
    "a_deficit_only",
    "b_surplus_claim_only",
    "b_surplus_only",
    "b_need_only",
    "clarification_resolves_missing_need",
    "clarification_loop_guard",
    "claim_then_confirmed_transfer",
    "claim_then_failed_transfer",
    "transfer_affordance_failure",
    "successful_scripted_exchange_cycle",
)


@dataclass(frozen=True, slots=True)
class Stage4StepRecord:
    step_index: int
    packet_id: str
    signal_kind: str
    source_authority: str
    counterpart_claim_marker: bool
    blocked_marker: bool
    contradiction_marker: bool


@dataclass(frozen=True, slots=True)
class ScriptedCounterpartResponseRecord:
    response_record_source: str
    caused_by_transfer_invocation: bool
    causing_invocation_id: str | None
    visible_packet_ref: str
    attempt_id: str | None
    causal_status: str
    signal_kind: str
    transfer_outcome: str
    visible_to_subject: bool


@dataclass(frozen=True, slots=True)
class W06CorrectionBoundarySummary:
    correction_candidate_created: bool
    correction_execution_prohibited: bool
    correction_executed: bool
    future_update_required: bool
    w06_residue_present: bool
    w06_revalidation_required: bool
    w06_claim_blocked: bool
    w06_guardrail_preserved: bool


@dataclass(frozen=True, slots=True)
class Stage4TradeCycleRun:
    run_id: str
    scenario_name: str
    stage: str
    execution_level: str
    subject_tick_used: bool
    owner_surface_used: bool
    adapter_projection_used: bool
    fallback_reasons: tuple[str, ...]
    phase_coverage_verified: bool
    phase_coverage_evidence: tuple[str, ...]
    readiness_decision: ResponseReadinessDecision
    clarification_records: tuple[ClarificationDecisionRecord, ...]
    offer_candidate_emitted: bool
    offer_candidate_id: str | None
    transfer_affordance_record: TransferAffordanceRecord
    transfer_invocation_candidate: TransferAffordanceInvocationCandidate
    transfer_attempt_record: TransferAttemptRecord
    transfer_result_record: TransferResultRecord
    transfer_episode_record: TransferEpisodeRecord
    scripted_b_response_records: tuple[str, ...]
    scripted_b_response_details: tuple[ScriptedCounterpartResponseRecord, ...]
    post_invocation_response_count: int
    passive_transfer_packet_count: int
    exchange_completion_claim: bool
    w06_correction_boundary: W06CorrectionBoundarySummary
    w06_residue_or_revalidation: bool
    claim_boundary: tuple[str, ...]
    steps: tuple[Stage4StepRecord, ...]
    visible_packets: tuple[dict[str, object], ...]
    falsifier_summary: tuple[dict[str, object], ...] = ()
    eval_only: dict[str, object] | None = None


def _claim_or_event_packets(packets: tuple[SubjectVisiblePacket, ...]) -> tuple[SubjectVisiblePacket, ...]:
    return tuple(
        packet
        for packet in packets
        if packet.signal_kind
        in {
            CounterpartSignalKind.PRESENCE_PING,
            CounterpartSignalKind.RESOURCE_STATUS_CLAIM,
            CounterpartSignalKind.BLOCKED,
            CounterpartSignalKind.CONTRADICTION,
            CounterpartSignalKind.TRANSFER_ATTEMPT,
            CounterpartSignalKind.TRANSFER_RESULT,
        }
    )


def _has_deficit_claim(packets: tuple[SubjectVisiblePacket, ...]) -> bool:
    return any(
        packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM
        and packet.reported_level is not None
        and packet.reported_level.value == "deficit"
        for packet in packets
    )


def _has_surplus_claim(packets: tuple[SubjectVisiblePacket, ...]) -> bool:
    return any(
        packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM
        and packet.reported_level is not None
        and packet.reported_level.value == "surplus"
        for packet in packets
    )


def _clarification_progress(target: MissingInformationKind, packets: tuple[SubjectVisiblePacket, ...]) -> bool:
    if target is MissingInformationKind.COUNTERPART_NEED_STATUS:
        return _has_deficit_claim(packets)
    if target is MissingInformationKind.COUNTERPART_RESOURCE_STATUS:
        return _has_surplus_claim(packets)
    if target is MissingInformationKind.APERTURE_STATUS:
        return any(packet.signal_kind is CounterpartSignalKind.BLOCKED for packet in packets)
    if target is MissingInformationKind.TRANSFER_AFFORDANCE_STATUS:
        return any(packet.signal_kind in {CounterpartSignalKind.BLOCKED, CounterpartSignalKind.TRANSFER_RESULT} for packet in packets)
    return False


def run_stage4_clarification_then_offer(
    *,
    scenario_name: str,
    self_state,
    packets: tuple[SubjectVisiblePacket, ...],
    transfer_affordance_status: TransferAffordanceStatus,
    budget: ClarificationBudget,
    stage3_offer_candidate_id: str | None,
) -> tuple[ResponseReadinessDecision, tuple[ClarificationDecisionRecord, ...], bool, str | None]:
    full_decision = evaluate_response_readiness(
        scenario_name=scenario_name,
        self_state=self_state,
        subject_visible_packets=packets,
        transfer_affordance_status=transfer_affordance_status.value,
        budget=budget,
    )
    if full_decision.status in {
        ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER,
        ResponseReadinessStatus.BLOCKED,
        ResponseReadinessStatus.REVALIDATION_REQUIRED,
        ResponseReadinessStatus.OBSERVE_ONLY,
        ResponseReadinessStatus.ABSTAIN,
    }:
        offer_emitted = (
            full_decision.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER
            and stage3_offer_candidate_id is not None
        )
        return full_decision, (), offer_emitted, stage3_offer_candidate_id if offer_emitted else None

    initial_packets = packets[:1] if packets else packets
    decision = evaluate_response_readiness(
        scenario_name=scenario_name,
        self_state=self_state,
        subject_visible_packets=initial_packets,
        transfer_affordance_status=transfer_affordance_status.value,
        budget=budget,
    )
    records: list[ClarificationDecisionRecord] = []
    current_budget = budget
    current_decision = decision
    view_packets = packets

    while (
        current_decision.status is ResponseReadinessStatus.CLARIFICATION_REQUIRED
        and current_decision.clarification_target is not None
        and current_budget.can_query(current_decision.clarification_target)
    ):
        target = current_decision.clarification_target
        next_budget = current_budget.consume(target)
        progress = _clarification_progress(target, view_packets[1:] if len(view_packets) > 1 else ())
        records.append(
            ClarificationDecisionRecord(
                scenario_name=scenario_name,
                route=ClarificationRoute.TARGETED_QUERY,
                target_field=target,
                decision_critical=True,
                progress_made=progress,
                budget_before=current_budget,
                budget_after=next_budget,
                reason_codes=(
                    "g07_targeted_clarification",
                    f"target:{target.value}",
                    "progress_made" if progress else "no_progress",
                ),
            )
        )
        current_budget = next_budget
        if not progress:
            current_decision = evaluate_response_readiness(
                scenario_name=scenario_name,
                self_state=self_state,
                subject_visible_packets=view_packets,
                transfer_affordance_status=transfer_affordance_status.value,
                budget=current_budget,
            )
            if current_decision.status is not ResponseReadinessStatus.CLARIFICATION_REQUIRED:
                break
            continue

        current_decision = evaluate_response_readiness(
            scenario_name=scenario_name,
            self_state=self_state,
            subject_visible_packets=packets,
            transfer_affordance_status=transfer_affordance_status.value,
            budget=current_budget,
        )
        break

    failed_transfer_seen = any(
        packet.signal_kind is CounterpartSignalKind.TRANSFER_RESULT
        and packet.transfer_outcome in {TransferOutcome.FAILED_BLOCKED, TransferOutcome.FAILED_UNKNOWN, TransferOutcome.CONTRADICTED}
        for packet in packets
    )
    if failed_transfer_seen and current_decision.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER:
        current_decision = ResponseReadinessDecision(
            scenario_name=current_decision.scenario_name,
            status=ResponseReadinessStatus.REVALIDATION_REQUIRED,
            critical_missing_fields=current_decision.critical_missing_fields,
            clarification_route=ClarificationRoute.REVALIDATE,
            clarification_target=None,
            clarification_budget_exhausted=current_decision.clarification_budget_exhausted,
            counterpart_claim_refs=current_decision.counterpart_claim_refs,
            self_state_refs=current_decision.self_state_refs,
            evidence_refs=current_decision.evidence_refs,
            reason_codes=current_decision.reason_codes + ("failed_transfer_visible_requires_revalidation",),
            claim_boundary=current_decision.claim_boundary,
        )

    offer_emitted = (
        current_decision.status is ResponseReadinessStatus.SUFFICIENT_FOR_BOUNDED_OFFER
        and stage3_offer_candidate_id is not None
    )
    return current_decision, tuple(records), offer_emitted, stage3_offer_candidate_id if offer_emitted else None


def _build_scripted_counterpart_response_details(
    *,
    packets: tuple[SubjectVisiblePacket, ...],
    invocation_id: str,
    attempt_id: str,
    transfer_attempted: bool,
) -> tuple[ScriptedCounterpartResponseRecord, ...]:
    records: list[ScriptedCounterpartResponseRecord] = []
    for packet in packets:
        if packet.signal_kind not in {CounterpartSignalKind.TRANSFER_ATTEMPT, CounterpartSignalKind.TRANSFER_RESULT}:
            continue
        caused = transfer_attempted
        records.append(
            ScriptedCounterpartResponseRecord(
                response_record_source="post_invocation_world_response" if caused else "passive_scenario_packet",
                caused_by_transfer_invocation=caused,
                causing_invocation_id=invocation_id if caused else None,
                visible_packet_ref=packet.packet_id,
                attempt_id=attempt_id if caused else None,
                causal_status="causally_after_invocation" if caused else "passive_observation",
                signal_kind=packet.signal_kind.value,
                transfer_outcome=packet.transfer_outcome.value,
                visible_to_subject=True,
            )
        )
    return tuple(records)


def _build_w06_correction_boundary(
    *,
    steps,
    readiness: ResponseReadinessDecision,
    transfer_result: TransferResultRecord,
    residue_or_revalidation: bool,
) -> W06CorrectionBoundarySummary:
    created = any(step.phase_trace_summary.w06_correction_candidate_created for step in steps)
    executed = any(step.phase_trace_summary.w06_correction_executed for step in steps)
    execution_prohibited = all(step.phase_trace_summary.w06_execution_prohibited for step in steps)
    residual = residue_or_revalidation or any(step.phase_trace_summary.w06_residual_uncertainty_present for step in steps)
    revalidation_required = (
        readiness.status in {ResponseReadinessStatus.REVALIDATION_REQUIRED, ResponseReadinessStatus.BLOCKED}
        or transfer_result.revalidate_required
    )
    claim_blocked = execution_prohibited and not executed
    return W06CorrectionBoundarySummary(
        correction_candidate_created=created,
        correction_execution_prohibited=execution_prohibited,
        correction_executed=executed,
        future_update_required=revalidation_required,
        w06_residue_present=residual,
        w06_revalidation_required=revalidation_required,
        w06_claim_blocked=claim_blocked,
        w06_guardrail_preserved=claim_blocked and (not created or execution_prohibited),
    )


def run_stage4_offer_then_transfer_attempt(
    *,
    scenario_name: str,
    packets: tuple[SubjectVisiblePacket, ...],
    self_state,
    readiness: ResponseReadinessDecision,
    offer_candidate_id: str | None,
    execute_transfer_affordance: bool,
    force_no_execute: bool,
) -> tuple[
    TransferAffordanceRecord,
    TransferAffordanceInvocationCandidate,
    TransferAttemptRecord,
    TransferResultRecord,
    TransferEpisodeRecord,
]:
    affordance = build_transfer_affordance_record(
        scenario_name=scenario_name,
        packets=packets,
        self_state=self_state,
    )
    policy = TransferAffordancePolicy(
        execute_transfer_affordance=(execute_transfer_affordance and not force_no_execute),
        require_offer_candidate=True,
    )
    invocation = build_invocation_candidate(
        scenario_name=scenario_name,
        readiness=readiness,
        affordance=affordance,
        offer_candidate_id=offer_candidate_id,
        policy=policy,
    )
    attempt, result, episode = execute_transfer_invocation(
        scenario_name=scenario_name,
        invocation=invocation,
        packets=packets,
    )
    return affordance, invocation, attempt, result, episode


def run_stage4_trade_cycle(
    scenario_name: str,
    *,
    include_falsifiers: bool = True,
    include_eval_only: bool = False,
    execute_transfer_affordance: bool = False,
    force_no_execute: bool = False,
    clarification_budget: ClarificationBudget | None = None,
):
    if scenario_name not in STAGE4_SCENARIOS:
        raise ValueError(f"Unsupported Stage 4 scenario: {scenario_name}")

    stage1 = run_stage1_scenario(scenario_name, include_falsifiers=False)
    stage25 = run_stage25_reaction(scenario_name, include_falsifiers=False)
    stage3 = run_stage3_response(scenario_name, include_falsifiers=False)

    packets = _claim_or_event_packets(stage1.emitted_packets)
    budget = clarification_budget or ClarificationBudget()
    stage3_offer = next((item for item in stage3.response_candidates if item.response_kind.value == "offer_candidate"), None)
    stage3_offer_id = stage3_offer.response_id if stage3_offer is not None else None

    transfer_status = infer_transfer_affordance_status(packets)
    readiness, clarification_records, offer_emitted, offer_candidate_id = run_stage4_clarification_then_offer(
        scenario_name=scenario_name,
        self_state=stage25.self_state_probe,
        packets=packets,
        transfer_affordance_status=transfer_status,
        budget=budget,
        stage3_offer_candidate_id=stage3_offer_id,
    )
    (
        affordance_record,
        invocation_candidate,
        attempt_record,
        result_record,
        episode_record,
    ) = run_stage4_offer_then_transfer_attempt(
        scenario_name=scenario_name,
        packets=packets,
        self_state=stage25.self_state_probe,
        readiness=readiness,
        offer_candidate_id=offer_candidate_id,
        execute_transfer_affordance=execute_transfer_affordance,
        force_no_execute=force_no_execute,
    )

    scripted_b_response = tuple(
        f"{packet.packet_id}:{packet.signal_kind.value}:{packet.transfer_outcome.value}"
        for packet in packets
        if packet.signal_kind in {CounterpartSignalKind.TRANSFER_ATTEMPT, CounterpartSignalKind.TRANSFER_RESULT}
    )
    scripted_b_response_details = _build_scripted_counterpart_response_details(
        packets=packets,
        invocation_id=invocation_candidate.invocation_id,
        attempt_id=attempt_record.attempt_id,
        transfer_attempted=attempt_record.attempted,
    )
    post_invocation_response_count = sum(1 for item in scripted_b_response_details if item.caused_by_transfer_invocation)
    passive_transfer_packet_count = sum(1 for item in scripted_b_response_details if not item.caused_by_transfer_invocation)
    residue = result_record.residue_required or readiness.status in {
        ResponseReadinessStatus.REVALIDATION_REQUIRED,
        ResponseReadinessStatus.BLOCKED,
    }
    w06_correction_boundary = _build_w06_correction_boundary(
        steps=stage25.steps,
        readiness=readiness,
        transfer_result=result_record,
        residue_or_revalidation=residue,
    )

    run = Stage4TradeCycleRun(
        run_id=f"stage4:{scenario_name}",
        scenario_name=scenario_name,
        stage="stage4_clarification_to_transfer_affordance_cycle",
        execution_level=stage25.execution_surface.execution_level.value,
        subject_tick_used=stage25.execution_surface.subject_tick_used,
        owner_surface_used=stage25.execution_surface.owner_surface_used,
        adapter_projection_used=stage25.execution_surface.adapter_projection_used,
        fallback_reasons=stage25.execution_surface.fallback_reasons,
        phase_coverage_verified=all(step.phase_trace_summary.phase_coverage_verified for step in stage25.steps),
        phase_coverage_evidence=tuple(
            sorted(
                {
                    evidence
                    for step in stage25.steps
                    for evidence in step.phase_trace_summary.phase_coverage_evidence
                }
            )
        ),
        readiness_decision=readiness,
        clarification_records=clarification_records,
        offer_candidate_emitted=offer_emitted,
        offer_candidate_id=offer_candidate_id,
        transfer_affordance_record=affordance_record,
        transfer_invocation_candidate=invocation_candidate,
        transfer_attempt_record=attempt_record,
        transfer_result_record=result_record,
        transfer_episode_record=episode_record,
        scripted_b_response_records=scripted_b_response,
        scripted_b_response_details=scripted_b_response_details,
        post_invocation_response_count=post_invocation_response_count,
        passive_transfer_packet_count=passive_transfer_packet_count,
        exchange_completion_claim=episode_record.exchange_completion_claim,
        w06_correction_boundary=w06_correction_boundary,
        w06_residue_or_revalidation=residue,
        claim_boundary=(
            "stage4_clarification_to_transfer_affordance_cycle_only",
            "offer_candidate_not_executed_transfer",
            "no_hidden_truth_for_exchange_start",
            "no_autonomous_trade_claim",
            "no_negotiation_claim",
            "no_economic_agency_claim",
        ),
        steps=tuple(
            Stage4StepRecord(
                step_index=step.step_index,
                packet_id=step.packet_id,
                signal_kind=step.world_event_reaction.signal_kind,
                source_authority=step.world_event_reaction.source_authority,
                counterpart_claim_marker=step.counterpart_claim_reaction.claim_detected,
                blocked_marker=step.world_event_reaction.blocked_aperture_seen,
                contradiction_marker=step.world_event_reaction.contradiction_seen,
            )
            for step in stage25.steps
        ),
        visible_packets=tuple(
            {
                "packet_id": packet.packet_id,
                "signal_kind": packet.signal_kind.value,
                "source_authority": packet.source_authority.value,
                "resource_kind": packet.resource_kind.value if packet.resource_kind is not None else None,
                "reported_level": packet.reported_level.value if packet.reported_level is not None else None,
                "aperture_state": packet.aperture_state.value,
                "transfer_outcome": packet.transfer_outcome.value,
                "claim_not_fact_marker": packet.claim_not_fact_marker,
                "hidden_truth_excluded": packet.hidden_truth_excluded,
            }
            for packet in packets
        ),
        falsifier_summary=(),
        eval_only={
            "harness_truth": stage1.eval_only.get("harness_truth", {}),
            "stage25_reaction_markers": stage25.reaction_markers,
            "stage3_selected_response": stage3.selected_response_kind.value,
        }
        if include_eval_only
        else None,
    )

    if include_falsifiers:
        from .falsifiers import run_stage4_cycle_falsifiers

        falsifiers = run_stage4_cycle_falsifiers(run)
        run = Stage4TradeCycleRun(
            run_id=run.run_id,
            scenario_name=run.scenario_name,
            stage=run.stage,
            execution_level=run.execution_level,
            subject_tick_used=run.subject_tick_used,
            owner_surface_used=run.owner_surface_used,
            adapter_projection_used=run.adapter_projection_used,
            fallback_reasons=run.fallback_reasons,
            phase_coverage_verified=run.phase_coverage_verified,
            phase_coverage_evidence=run.phase_coverage_evidence,
            readiness_decision=run.readiness_decision,
            clarification_records=run.clarification_records,
            offer_candidate_emitted=run.offer_candidate_emitted,
            offer_candidate_id=run.offer_candidate_id,
            transfer_affordance_record=run.transfer_affordance_record,
            transfer_invocation_candidate=run.transfer_invocation_candidate,
            transfer_attempt_record=run.transfer_attempt_record,
            transfer_result_record=run.transfer_result_record,
            transfer_episode_record=run.transfer_episode_record,
            scripted_b_response_records=run.scripted_b_response_records,
            scripted_b_response_details=run.scripted_b_response_details,
            post_invocation_response_count=run.post_invocation_response_count,
            passive_transfer_packet_count=run.passive_transfer_packet_count,
            exchange_completion_claim=run.exchange_completion_claim,
            w06_correction_boundary=run.w06_correction_boundary,
            w06_residue_or_revalidation=run.w06_residue_or_revalidation,
            claim_boundary=run.claim_boundary,
            steps=run.steps,
            visible_packets=run.visible_packets,
            falsifier_summary=tuple(asdict(item) for item in falsifiers),
            eval_only=run.eval_only,
        )
    return run


def stage4_trade_cycle_to_dict(
    run: Stage4TradeCycleRun,
    *,
    include_eval_only: bool = False,
    include_transfer_episode: bool = True,
    include_clarification_state: bool = False,
) -> dict[str, object]:
    payload = {
        "run_id": run.run_id,
        "scenario_name": run.scenario_name,
        "stage": run.stage,
        "execution_level": run.execution_level,
        "subject_tick_used": run.subject_tick_used,
        "owner_surface_used": run.owner_surface_used,
        "adapter_projection_used": run.adapter_projection_used,
        "fallback_reasons": list(run.fallback_reasons),
        "phase_coverage_verified": run.phase_coverage_verified,
        "phase_coverage_evidence": list(run.phase_coverage_evidence),
        "readiness_status": run.readiness_decision.status.value,
        "clarification_route": run.readiness_decision.clarification_route.value,
        "offer_candidate_emitted": run.offer_candidate_emitted,
        "offer_candidate_id": run.offer_candidate_id,
        "transfer_affordance": asdict(run.transfer_affordance_record),
        "transfer_invocation_candidate": asdict(run.transfer_invocation_candidate),
        "transfer_attempt_record": asdict(run.transfer_attempt_record),
        "transfer_result_record": asdict(run.transfer_result_record),
        "scripted_b_response_records": list(run.scripted_b_response_records),
        "scripted_b_response_details": [asdict(item) for item in run.scripted_b_response_details],
        "post_invocation_response_count": run.post_invocation_response_count,
        "passive_transfer_packet_count": run.passive_transfer_packet_count,
        "exchange_completion_claim": run.exchange_completion_claim,
        "w06_correction_boundary": asdict(run.w06_correction_boundary),
        "w06_residue_or_revalidation": run.w06_residue_or_revalidation,
        "claim_boundary": list(run.claim_boundary),
        "visible_packets": list(run.visible_packets),
        "falsifier_summary": list(run.falsifier_summary),
    }
    if include_transfer_episode:
        payload["transfer_episode_record"] = asdict(run.transfer_episode_record)
    if include_clarification_state:
        payload["readiness_decision"] = asdict(run.readiness_decision)
        payload["clarification_records"] = [asdict(item) for item in run.clarification_records]
    if include_eval_only and run.eval_only is not None:
        payload["eval_only"] = run.eval_only
    return payload
