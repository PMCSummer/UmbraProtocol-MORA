from __future__ import annotations

from dataclasses import asdict

from .affordance_responsibility import (
    AffordanceEpisodeResponsibilityRecord,
    AffordanceProvenanceMode,
    AffordanceResponsibilityTrace,
    AffordanceSelectionRecord,
    AffordanceSelectionStatus,
    AffordanceUseRequest,
    ModuleResponsibilityLedger,
    ResponsibilityVerdict,
    WorldActuatorEnvelope,
    affordance_trace_to_dict,
)
from .clarification_policy import MissingInformationKind
from .models import ResourceKind
from .stage4_trade_cycle_runner import STAGE4_SCENARIOS, run_stage4_trade_cycle
from .transfer_affordance import TransferAffordanceStatus


STAGE5_SCENARIOS: tuple[str, ...] = STAGE4_SCENARIOS


def _counterpart_sets(stage4_run) -> tuple[set[str], set[str]]:
    surplus: set[str] = set()
    deficit: set[str] = set()
    for packet in stage4_run.visible_packets:
        if packet.get("signal_kind") != "resource_status_signal":
            continue
        if packet.get("source_authority") != "counterpart_claim":
            continue
        resource = packet.get("resource_kind")
        level = packet.get("reported_level")
        if not resource or not level:
            continue
        if level == "surplus":
            surplus.add(resource)
        elif level == "deficit":
            deficit.add(resource)
    return surplus, deficit


def _self_sets(stage4_run) -> tuple[set[str], set[str]]:
    deficits: set[str] = set()
    if MissingInformationKind.SELF_DEFICIT not in set(stage4_run.readiness_decision.critical_missing_fields):
        deficits.add("self_deficit_marker_present")
    surpluses: set[str] = set()
    if stage4_run.transfer_affordance_record.resource_kind is not None:
        surpluses.add(stage4_run.transfer_affordance_record.resource_kind.value)
    return deficits, surpluses


def _selection_status(stage4_run) -> tuple[AffordanceSelectionStatus, tuple[str, ...], tuple[str, ...]]:
    required = (
        "offer_candidate_emitted",
        "phase_coverage_verified",
        "readiness_sufficient_for_bounded_offer",
        "affordance_available",
        "claim_boundary_preserved",
    )
    missing: list[str] = []
    if not stage4_run.offer_candidate_emitted:
        missing.append("offer_candidate_emitted")
    if not stage4_run.phase_coverage_verified:
        missing.append("phase_coverage_verified")
    if stage4_run.readiness_decision.status.value != "sufficient_for_bounded_offer":
        missing.append("readiness_sufficient_for_bounded_offer")
    if stage4_run.transfer_affordance_record.status is not TransferAffordanceStatus.AVAILABLE:
        missing.append("affordance_available")
    if "no_hidden_truth_for_exchange_start" not in set(stage4_run.claim_boundary):
        missing.append("claim_boundary_preserved")

    if not stage4_run.offer_candidate_emitted:
        return AffordanceSelectionStatus.NOT_SELECTED_NO_OFFER_CANDIDATE, required, tuple(missing)
    if stage4_run.transfer_affordance_record.status is TransferAffordanceStatus.BLOCKED:
        return AffordanceSelectionStatus.NOT_SELECTED_BLOCKED, required, tuple(missing)
    if stage4_run.transfer_affordance_record.status is TransferAffordanceStatus.CONTESTED:
        return AffordanceSelectionStatus.NOT_SELECTED_CONTESTED, required, tuple(missing)
    if missing:
        return AffordanceSelectionStatus.NOT_SELECTED_INSUFFICIENT_INFORMATION, required, tuple(missing)
    return AffordanceSelectionStatus.SELECTED_FOR_INVOCATION_REQUEST, required, ()


def _build_ledger(stage4_run, *, selection_status: AffordanceSelectionStatus) -> ModuleResponsibilityLedger:
    unresolved: list[str] = []
    if not stage4_run.phase_coverage_verified:
        unresolved.append("phase_coverage_unverified")
    if selection_status is not AffordanceSelectionStatus.SELECTED_FOR_INVOCATION_REQUEST:
        unresolved.append("selection_not_ready")
    if stage4_run.transfer_affordance_record.status is not TransferAffordanceStatus.AVAILABLE:
        unresolved.append(f"affordance_status:{stage4_run.transfer_affordance_record.status.value}")
    return ModuleResponsibilityLedger(
        W01_responsibility="admits visible packets and preserves claim-vs-fact markers only",
        W02_responsibility="bounded regularity support only; no one-shot truth promotion",
        W03_responsibility="bounded candidate support only; no universal exchange schema",
        W04_responsibility="applicability/permission gate only; no action execution",
        W05_responsibility="desired/predicted/observed/permitted separation only",
        W06_responsibility="residue/revalidation and non-executed correction boundary",
        A02_gap_responsibility="emits blocked/contested/missing affordance gap markers",
        A04_affordance_binding_responsibility="binds external aperture-transfer affordance as harness metadata",
        P02_episode_responsibility="separates candidate, attempt, observed result, verification",
        V_communication_responsibility="offer/request remain communicative candidates only",
        world_actuator_responsibility="external harness/world execution only when explicit flag is present",
        out_of_scope_modules=(
            "autonomous_trade_understanding",
            "natural_language_negotiation",
            "economic_agency",
            "subject_motor_control",
            "learning_update_execution",
        ),
        unresolved_gaps=tuple(unresolved),
    )


def _response_record_maps(stage4_run) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    passive: list[dict[str, object]] = []
    causal: list[dict[str, object]] = []
    for item in stage4_run.scripted_b_response_details:
        entry = asdict(item)
        if item.caused_by_transfer_invocation:
            causal.append(entry)
        else:
            passive.append(entry)
    return tuple(passive), tuple(causal)


def _completion_basis_chain(
    *,
    stage4_run,
    selection_record: AffordanceSelectionRecord,
    request: AffordanceUseRequest,
    envelope: WorldActuatorEnvelope,
    passive_refs: tuple[str, ...],
    causal_refs: tuple[str, ...],
) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    checks = {
        "offer_candidate_exists": bool(stage4_run.offer_candidate_id),
        "affordance_selected": selection_record.selection_status is AffordanceSelectionStatus.SELECTED_FOR_INVOCATION_REQUEST,
        "invocation_request_exists": bool(request.selected_affordance_ref),
        "invocation_request_valid": request.request_valid,
        "explicit_stage5_execution_flag": envelope.explicit_execution_flag,
        "world_actuator_invoked": envelope.invoked,
        "invocation_id_present": bool(envelope.invocation_id),
        "attempt_id_present": bool(envelope.attempt_id),
        "causal_post_invocation_refs_present": bool(causal_refs),
        "passive_not_used_as_causal": not bool(set(passive_refs) & set(causal_refs)),
        "transfer_result_succeeded": stage4_run.transfer_result_record.outcome.value == "succeeded",
        "episode_verified": stage4_run.transfer_episode_record.verified,
        "no_hidden_truth_for_completion": True,
        "no_eval_only_for_completion": True,
        "no_scenario_label_for_completion": True,
        "no_w06_correction_execution_for_completion": not stage4_run.w06_correction_boundary.correction_executed,
    }
    missing = tuple(name for name, ok in checks.items() if not ok)
    return all(checks.values()), tuple(name for name, ok in checks.items() if ok), missing


def run_stage5_affordance_trace(
    scenario_id: str,
    *,
    include_falsifiers: bool = True,
    include_eval_only: bool = False,
    execute_world_actuator: bool = False,
) -> AffordanceResponsibilityTrace:
    if scenario_id not in STAGE5_SCENARIOS:
        raise ValueError(f"Unsupported Stage 5 scenario: {scenario_id}")

    stage4_run = run_stage4_trade_cycle(
        scenario_id,
        include_falsifiers=False,
        include_eval_only=include_eval_only,
        execute_transfer_affordance=execute_world_actuator,
        force_no_execute=False,
    )
    counterpart_surplus, _counterpart_deficit = _counterpart_sets(stage4_run)
    self_deficits, _self_surpluses = _self_sets(stage4_run)
    status, required_preconditions, missing_preconditions = _selection_status(stage4_run)

    selected = status is AffordanceSelectionStatus.SELECTED_FOR_INVOCATION_REQUEST
    give_resource: str | None = stage4_run.transfer_affordance_record.resource_kind.value if stage4_run.transfer_affordance_record.resource_kind else None
    requested_receive: str | None = None
    if "self_deficit_marker_present" in self_deficits and counterpart_surplus:
        requested_receive = sorted(counterpart_surplus)[0]
    if requested_receive is None and counterpart_surplus:
        requested_receive = sorted(counterpart_surplus)[0]

    phase_refs = tuple(
        sorted(
            {
                ref
                for ref in stage4_run.phase_coverage_evidence
                if ref.split(":", 1)[0] in {"W01", "W02", "W03", "W04", "W05", "W06"}
            }
        )
    )
    selection_record = AffordanceSelectionRecord(
        selection_id=f"{scenario_id}:stage5:selection:1",
        response_candidate_ref=stage4_run.offer_candidate_id,
        selected_affordance_id=stage4_run.transfer_affordance_record.affordance_id if selected else None,
        selected_affordance_kind=stage4_run.transfer_affordance_record.affordance_kind.value if selected else None,
        selected_affordance_source=stage4_run.transfer_affordance_record.authority_ref,
        selected_affordance_status=stage4_run.transfer_affordance_record.status.value,
        why_this_affordance=(
            "offer_candidate_visible",
            "self_surplus_marker_present",
            "counterpart_claim_relation_visible_as_claim_not_fact",
            "external_aperture_transfer_affordance_mapped",
        ),
        rejected_alternatives=("no_internal_transfer_execution_surface", "no_trade_specific_magic_channel"),
        required_preconditions=required_preconditions,
        missing_preconditions=missing_preconditions,
        permission_status=stage4_run.readiness_decision.status.value,
        selection_status=status,
        source_phase_refs=phase_refs,
        provenance_mode=(
            AffordanceProvenanceMode.REAL_SUBJECT_TICK_SURFACE
            if stage4_run.subject_tick_used and stage4_run.phase_coverage_verified
            else AffordanceProvenanceMode.HARNESS_COMPATIBLE_PROJECTION
        ),
    )

    may_send = selected and execute_world_actuator
    request = AffordanceUseRequest(
        request_id=f"{scenario_id}:stage5:affordance_request:1",
        selected_affordance_ref=selection_record.selected_affordance_id,
        give_resource=give_resource if selected else None,
        requested_or_expected_receive_resource=requested_receive if selected else None,
        target_counterpart_ref="counterpart_b",
        intended_effect="bounded_external_transfer_attempt_request",
        required_permissions=(
            "w04_applicability_not_blocked",
            "w05_permission_channel_not_predicted_override",
            "w06_correction_non_execution_guard",
            "explicit_world_actuator_flag_required",
        ),
        prohibited_interpretations=(
            "no_autonomous_trade_claim",
            "no_negotiation_claim",
            "no_hidden_truth_claim",
            "no_subject_motor_control_claim",
        ),
        execution_requested=execute_world_actuator,
        request_valid=selected and stage4_run.transfer_affordance_record.status is TransferAffordanceStatus.AVAILABLE,
        execution_prohibited_until_world_actuator=True,
        may_be_sent_to_world_actuator=may_send,
        must_not_execute_inside_subject=True,
        source_phase_refs=phase_refs,
        claim_boundary=(
            "invocation_request_not_execution",
            "must_not_execute_inside_subject",
            "counterpart_claim_not_fact",
        ),
    )

    envelope = WorldActuatorEnvelope(
        actuator_id=f"{scenario_id}:stage5:world_actuator:aperture_transfer",
        actuator_kind="external_world_actuator",
        invocation_request_ref=request.request_id if request.may_be_sent_to_world_actuator else None,
        explicit_execution_flag=execute_world_actuator,
        invocation_id=stage4_run.transfer_invocation_candidate.invocation_id if stage4_run.transfer_attempt_record.attempted else None,
        precondition_check_result="passed" if request.may_be_sent_to_world_actuator else "blocked_or_not_requested",
        invoked=stage4_run.transfer_attempt_record.attempted,
        invocation_reason=tuple(stage4_run.transfer_attempt_record.reason_codes),
        blocked_reason=tuple(stage4_run.transfer_invocation_candidate.reason_codes) if not stage4_run.transfer_attempt_record.attempted else (),
        attempt_id=stage4_run.transfer_attempt_record.attempt_id if stage4_run.transfer_attempt_record.attempted else None,
        observed_result_ref=stage4_run.transfer_result_record.result_id if stage4_run.transfer_result_record.observed else None,
        actuator_authority="harness_world_execution_surface",
        subject_motor_control_claim="not_claimed",
    )

    passive_records, causal_records = _response_record_maps(stage4_run)
    passive_refs = tuple(
        item.visible_packet_ref
        for item in stage4_run.scripted_b_response_details
        if not item.caused_by_transfer_invocation
    )
    causal_refs = tuple(
        item.visible_packet_ref
        for item in stage4_run.scripted_b_response_details
        if item.caused_by_transfer_invocation
    )
    completion_chain_verified, completion_basis, completion_basis_missing = _completion_basis_chain(
        stage4_run=stage4_run,
        selection_record=selection_record,
        request=request,
        envelope=envelope,
        passive_refs=passive_refs,
        causal_refs=causal_refs,
    )
    failed_or_blocked_reason = tuple(stage4_run.transfer_result_record.reason_codes)
    if not failed_or_blocked_reason and stage4_run.transfer_invocation_candidate.reason_codes:
        failed_or_blocked_reason = tuple(stage4_run.transfer_invocation_candidate.reason_codes)

    episode = AffordanceEpisodeResponsibilityRecord(
        episode_id=f"{scenario_id}:stage5:episode:1",
        offer_candidate_ref=stage4_run.offer_candidate_id,
        selection_ref=selection_record.selection_id,
        invocation_request_ref=request.request_id if request.may_be_sent_to_world_actuator else None,
        actuator_envelope_ref=envelope.actuator_id,
        observed_result_ref=envelope.observed_result_ref,
        causing_invocation_id=envelope.invocation_id if causal_refs else None,
        causing_attempt_id=envelope.attempt_id if causal_refs else None,
        verification_status="verified" if stage4_run.transfer_episode_record.verified else "unverified",
        completion_claim=stage4_run.transfer_episode_record.exchange_completion_claim,
        completion_basis=completion_basis,
        completion_basis_chain_verified=completion_chain_verified,
        completion_basis_missing=completion_basis_missing,
        completion_authority="episode_verification_chain",
        used_transfer_result_as_sole_authority=False,
        used_eval_only_for_completion=False,
        used_hidden_truth_for_completion=False,
        used_scenario_label_for_completion=False,
        used_w06_correction_execution_for_completion=stage4_run.w06_correction_boundary.correction_executed,
        residue_status=(
            "residue_or_revalidation_present"
            if stage4_run.w06_residue_or_revalidation
            else "no_residue"
        ),
        failed_or_blocked_reason=failed_or_blocked_reason,
        passive_packet_refs=passive_refs,
        causal_post_invocation_refs=causal_refs,
        claim_boundary=(
            "candidate_attempt_result_verification_separated",
            "passive_packet_not_causal_response",
            "transfer_result_not_completion_oracle",
        ),
    )

    ledger = _build_ledger(stage4_run, selection_status=selection_record.selection_status)

    if not stage4_run.phase_coverage_verified:
        verdict = ResponsibilityVerdict.TRACE_INCOMPLETE
    elif selection_record.selection_status is AffordanceSelectionStatus.SELECTED_FOR_INVOCATION_REQUEST and not execute_world_actuator:
        verdict = ResponsibilityVerdict.CANDIDATE_ONLY_NO_REQUEST
    elif selection_record.selection_status is AffordanceSelectionStatus.SELECTED_FOR_INVOCATION_REQUEST:
        verdict = ResponsibilityVerdict.READY_FOR_BOUNDED_AFFORDANCE_REQUEST
    else:
        verdict = ResponsibilityVerdict.BLOCKED_OR_REVALIDATE

    records = (
        {"record_type": "selection_record", **asdict(selection_record)},
        {"record_type": "affordance_use_request", **asdict(request)},
        {"record_type": "world_actuator_envelope", **asdict(envelope)},
        {"record_type": "episode_record", **asdict(episode)},
    )

    trace = AffordanceResponsibilityTrace(
        trace_id=f"{scenario_id}:stage5:affordance_responsibility_trace",
        scenario_id=scenario_id,
        stage4_run_id=stage4_run.run_id,
        execution_level=stage4_run.execution_level,
        subject_tick_used=stage4_run.subject_tick_used,
        phase_coverage_verified=stage4_run.phase_coverage_verified,
        phase_coverage_evidence=stage4_run.phase_coverage_evidence,
        phase_evidence_source_run_id=stage4_run.run_id,
        stage4_phase_coverage_evidence=stage4_run.phase_coverage_evidence,
        responsibility_verdict=verdict,
        claim_boundary=(
            "stage5_affordance_responsibility_trace_only",
            "offer_selection_request_execution_separated",
            "no_autonomous_trade_claim",
            "no_subject_motor_control_claim",
            "no_learning_update_execution_claim",
        ),
        evidence_visibility_boundary=(
            "visible_packets_and_stage4_trace_only",
            "no_hidden_inventory_for_decision",
            "no_eval_only_for_decision",
        ),
        selection_record=selection_record,
        affordance_use_request=request,
        world_actuator_envelope=envelope,
        episode_record=episode,
        module_responsibility_ledger=ledger,
        transfer_result=stage4_run.transfer_result_record.outcome,
        visible_packets=stage4_run.visible_packets,
        passive_response_records=passive_records,
        causal_response_records=causal_records,
        records=records,
        falsifier_summary=(),
        eval_only=stage4_run.eval_only if include_eval_only else None,
    )

    if include_falsifiers:
        from .falsifiers import run_stage5_affordance_trace_falsifiers

        falsifiers = run_stage5_affordance_trace_falsifiers(trace)
        trace = AffordanceResponsibilityTrace(
            trace_id=trace.trace_id,
            scenario_id=trace.scenario_id,
            stage4_run_id=trace.stage4_run_id,
            execution_level=trace.execution_level,
            subject_tick_used=trace.subject_tick_used,
            phase_coverage_verified=trace.phase_coverage_verified,
            phase_coverage_evidence=trace.phase_coverage_evidence,
            phase_evidence_source_run_id=trace.phase_evidence_source_run_id,
            stage4_phase_coverage_evidence=trace.stage4_phase_coverage_evidence,
            responsibility_verdict=trace.responsibility_verdict,
            claim_boundary=trace.claim_boundary,
            evidence_visibility_boundary=trace.evidence_visibility_boundary,
            selection_record=trace.selection_record,
            affordance_use_request=trace.affordance_use_request,
            world_actuator_envelope=trace.world_actuator_envelope,
            episode_record=trace.episode_record,
            module_responsibility_ledger=trace.module_responsibility_ledger,
            transfer_result=trace.transfer_result,
            visible_packets=trace.visible_packets,
            passive_response_records=trace.passive_response_records,
            causal_response_records=trace.causal_response_records,
            records=trace.records,
            falsifier_summary=tuple(asdict(item) for item in falsifiers),
            eval_only=trace.eval_only,
        )
    return trace


def stage5_affordance_trace_to_dict(
    trace: AffordanceResponsibilityTrace,
    *,
    include_eval_only: bool = False,
    include_affordance_records: bool = True,
    include_affordance_ledger: bool = False,
) -> dict[str, object]:
    return affordance_trace_to_dict(
        trace,
        include_eval_only=include_eval_only,
        include_affordance_records=include_affordance_records,
        include_affordance_ledger=include_affordance_ledger,
    )
