from __future__ import annotations

from dataclasses import asdict

from .falsifiers import run_stage3_response_falsifiers
from .models import CounterpartSignalKind, ResourceKind, ResourceLevel
from .response_candidates import (
    AResponseCandidate,
    AResponseCandidateRun,
    AResponseKind,
    ResponseVerdict,
    response_candidate_run_to_dict,
)
from .runner import run_stage1_scenario, run_stage25_reaction


def _self_state_sets(stage25_run) -> tuple[set[str], set[str]]:
    deficits = {item.split(":", 1)[0] for item in stage25_run.self_state_probe.deficit_markers}
    surpluses = {item.split(":", 1)[0] for item in stage25_run.self_state_probe.surplus_markers}
    return deficits, surpluses


def _claim_relation(stage1_result) -> tuple[set[str], set[str], tuple[str, ...]]:
    claim_surplus: set[str] = set()
    claim_deficit: set[str] = set()
    evidence_refs: list[str] = []
    for packet in stage1_result.emitted_packets:
        if packet.signal_kind is not CounterpartSignalKind.RESOURCE_STATUS_CLAIM:
            continue
        if packet.resource_kind is None or packet.reported_level is None:
            continue
        evidence_refs.append(f"counterpart_claim:{packet.packet_id}")
        if packet.reported_level is ResourceLevel.SURPLUS:
            claim_surplus.add(packet.resource_kind.value)
        elif packet.reported_level is ResourceLevel.DEFICIT:
            claim_deficit.add(packet.resource_kind.value)
    return claim_surplus, claim_deficit, tuple(evidence_refs)


def _phase_refs(stage25_run) -> tuple[tuple[str, ...], tuple[str, ...]]:
    phase_refs: set[str] = set()
    coverage: set[str] = set()
    for step in stage25_run.steps:
        coverage.update(step.phase_trace_summary.phase_coverage)
        phase_refs.update(step.phase_trace_summary.phase_coverage_evidence)
    return tuple(sorted(phase_refs)), tuple(sorted(coverage))


def _packet_step_index_map(stage1_result) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for step in stage1_result.steps:
        for packet in step.subject_visible_packets:
            mapping[packet.packet_id] = step.step_index
    return mapping


def _stage25_step_map(stage25_run):
    return {step.packet_id: step for step in stage25_run.steps}


def extract_response_candidates_from_reaction_trace(
    scenario_name: str,
    stage1_result,
    stage25_run,
) -> tuple[AResponseCandidate, ...]:
    deficits, surpluses = _self_state_sets(stage25_run)
    claim_surplus, claim_deficit, claim_evidence = _claim_relation(stage1_result)
    phase_evidence_refs, phase_coverage = _phase_refs(stage25_run)
    packet_ids = tuple(packet.packet_id for packet in stage1_result.emitted_packets)
    evidence_refs = tuple(f"packet:{packet_id}" for packet_id in packet_ids) + claim_evidence
    packet_step_map = _packet_step_index_map(stage1_result)
    stage25_step_map = _stage25_step_map(stage25_run)

    has_presence = any(packet.signal_kind is CounterpartSignalKind.PRESENCE_PING for packet in stage1_result.emitted_packets)
    has_claim = bool(claim_evidence)
    has_blocked = any(packet.signal_kind is CounterpartSignalKind.BLOCKED for packet in stage1_result.emitted_packets)
    has_contradiction = any(packet.signal_kind is CounterpartSignalKind.CONTRADICTION for packet in stage1_result.emitted_packets)
    has_transfer_attempt = any(packet.signal_kind is CounterpartSignalKind.TRANSFER_ATTEMPT for packet in stage1_result.emitted_packets)
    has_transfer_success = any(
        packet.signal_kind is CounterpartSignalKind.TRANSFER_RESULT and packet.transfer_outcome.value == "succeeded"
        for packet in stage1_result.emitted_packets
    )
    has_transfer_failed = any(
        packet.signal_kind is CounterpartSignalKind.TRANSFER_RESULT and packet.transfer_outcome.value != "succeeded"
        for packet in stage1_result.emitted_packets
    )

    complementarity_visible = bool(deficits.intersection(claim_surplus) and surpluses.intersection(claim_deficit))
    phase_verified = all(step.phase_trace_summary.phase_coverage_verified for step in stage25_run.steps)
    execution_real = stage25_run.execution_surface.execution_level.value == "full_subject_tick_execution"
    w04_clean = all(
        not step.world_event_reaction.blocked_aperture_seen and step.phase_trace_summary.w04_clean_applicability_allowed
        for step in stage25_run.steps
        if step.world_event_reaction.signal_kind in {
            CounterpartSignalKind.RESOURCE_STATUS_CLAIM.value,
            CounterpartSignalKind.TRANSFER_ATTEMPT.value,
            CounterpartSignalKind.TRANSFER_RESULT.value,
        }
    )
    w05_boundary_clean = all(
        not step.phase_trace_summary.w05_desired_as_observed and not step.phase_trace_summary.w05_predicted_as_permitted
        for step in stage25_run.steps
    )
    w06_boundary_clean = all(
        step.phase_trace_summary.w06_execution_prohibited and not step.phase_trace_summary.w06_correction_executed
        for step in stage25_run.steps
    )
    uncertainty_refs = tuple(
        f"{step.packet_id}:{marker}"
        for step in stage25_run.steps
        for marker in step.phase_trace_summary.reason_codes + step.phase_trace_summary.prohibited_claims
        if "residue" in marker or "revalidate" in marker or "contested" in marker
    )

    claim_boundary = (
        "candidate_not_executed_trade",
        "no_autonomous_trade_claim",
        "no_hidden_truth_claim",
        "no_negotiation_claim",
    )
    prohibited_claims = (
        "no_autonomous_trade_claim",
        "no_hidden_truth_claim",
        "no_negotiation_claim",
        "no_executed_transfer_claim",
        "no_economic_agency_claim",
        "desired_not_evidence",
        "predicted_not_permission",
    )

    candidates: list[AResponseCandidate] = []

    def _add(
        response_kind: AResponseKind,
        requested_effect: str,
        *,
        confidence: float,
        permitted_status: str,
        reason_codes: tuple[str, ...],
        target_ref: str | None = "counterpart_b",
        object_ref: str | None = None,
        source_step_id: str = "step:0",
        candidate_packet_ids: tuple[str, ...] = (),
        basis_summary: tuple[str, ...] = (),
    ) -> None:
        resolved_packet_ids = candidate_packet_ids or packet_ids
        candidate_evidence_refs = tuple(f"packet:{packet_id}" for packet_id in resolved_packet_ids) + tuple(
            item for item in claim_evidence if item.split(":", 1)[1] in resolved_packet_ids
        )
        candidate_step_ids = tuple(
            dict.fromkeys(
                f"step:{packet_step_map[packet_id]}"
                for packet_id in resolved_packet_ids
                if packet_id in packet_step_map
            )
        )
        candidate_phase_refs: list[str] = []
        for packet_id in resolved_packet_ids:
            step_record = stage25_step_map.get(packet_id)
            if step_record is None:
                continue
            summary = step_record.phase_trace_summary
            candidate_phase_refs.extend(
                (
                    f"W01:{packet_id}:claim_not_fact_preserved:{str(step_record.counterpart_claim_reaction.claim_not_fact_preserved).lower()}",
                    f"W04:{packet_id}:clean_applicability_allowed:{str(summary.w04_clean_applicability_allowed).lower()}",
                    f"W05:{packet_id}:desired_as_observed:{str(summary.w05_desired_as_observed).lower()}",
                    f"W05:{packet_id}:predicted_as_permitted:{str(summary.w05_predicted_as_permitted).lower()}",
                    f"W06:{packet_id}:execution_prohibited:{str(summary.w06_execution_prohibited).lower()}",
                    f"W06:{packet_id}:residual_uncertainty_present:{str(summary.w06_residual_uncertainty_present).lower()}",
                )
            )
            candidate_phase_refs.extend(
                item
                for item in summary.phase_coverage_evidence
                if item.split(":", 1)[0] in {"W01", "W02", "W03", "W04", "W05", "W06"}
            )
        forbidden_basis_markers = (
            "hidden_truth_not_used",
            "eval_only_not_used",
            "scenario_label_not_used",
            "mirrored_oracle_not_used",
            "trade_shortcut_not_used",
            "desired_not_evidence",
            "predicted_not_permission",
        )
        candidates.append(
            AResponseCandidate(
                response_id=f"{scenario_name}:{response_kind.value}:{len(candidates)+1}",
                scenario_name=scenario_name,
                source_step_id=source_step_id,
                source_step_ids=candidate_step_ids or ("step:0",),
                response_kind=response_kind,
                target_ref=target_ref,
                object_ref=object_ref,
                requested_effect=requested_effect,
                confidence=confidence,
                permitted_status=permitted_status,
                evidence_refs=candidate_evidence_refs or evidence_refs,
                phase_evidence_refs=tuple(dict.fromkeys(candidate_phase_refs)) or phase_evidence_refs,
                prohibited_claims=prohibited_claims,
                reason_codes=reason_codes,
                boundary_markers=(
                    "counterpart_claim_not_fact",
                    "desired_not_evidence",
                    "predicted_not_permission",
                    "execution_prohibited",
                ),
                execution_prohibited=True,
                claim_boundary=claim_boundary,
                hidden_truth_used=False,
                eval_only_used=False,
                trade_shortcut_used=False,
                derived_from_real_subject_tick=execution_real,
                extraction_method="stage25_tick_trace_extraction",
                source_phase_coverage=phase_coverage,
                residual_uncertainty_refs=uncertainty_refs,
                response_basis_summary=basis_summary or (
                    "visible_only_packet_basis",
                    "self_state_markers_are_not_world_evidence",
                    "counterpart_claim_markers_are_not_facts",
                    "candidate_not_executed",
                ),
                forbidden_basis_markers=forbidden_basis_markers,
            )
        )

    if has_presence and not has_claim:
        _add(
            AResponseKind.ACKNOWLEDGE_PRESENCE,
            "acknowledge_counterpart_presence",
            confidence=0.35,
            permitted_status="observe_only",
            reason_codes=("presence_observed", "no_resource_relation_visible"),
            candidate_packet_ids=tuple(
                packet.packet_id
                for packet in stage1_result.emitted_packets
                if packet.signal_kind is CounterpartSignalKind.PRESENCE_PING
            ),
            basis_summary=(
                "presence_signal_visible",
                "no_counterpart_resource_claim_visible",
                "no_transfer_authorization",
            ),
        )

    if has_claim and not complementarity_visible:
        _add(
            AResponseKind.REQUEST_CLARIFICATION,
            "request_counterpart_status_clarification",
            confidence=0.32,
            permitted_status="revalidate_required",
            reason_codes=("counterpart_claim_visible", "no_complementarity_relation_visible"),
            candidate_packet_ids=tuple(
                packet.packet_id
                for packet in stage1_result.emitted_packets
                if packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM
            ),
            basis_summary=(
                "counterpart_resource_claim_visible",
                "claim_not_fact_boundary_preserved",
                "complementarity_not_established_from_visible_evidence",
            ),
        )

    if has_blocked:
        _add(
            AResponseKind.BLOCK_DUE_CONSTRAINT,
            "block_transfer_due_to_aperture_constraint",
            confidence=0.8,
            permitted_status="blocked",
            reason_codes=("blocked_aperture_visible", "w04_constraint_boundary"),
            candidate_packet_ids=tuple(
                packet.packet_id
                for packet in stage1_result.emitted_packets
                if packet.signal_kind in {CounterpartSignalKind.BLOCKED, CounterpartSignalKind.TRANSFER_RESULT}
            ),
            basis_summary=(
                "blocked_aperture_event_visible",
                "w04_constraint_prevents_clean_applicability",
                "no_transfer_candidate_under_blocked_path",
            ),
        )

    if has_contradiction:
        _add(
            AResponseKind.REVALIDATE_BEFORE_RESPONSE,
            "revalidate_counterpart_claim_before_response",
            confidence=0.78,
            permitted_status="revalidate_required",
            reason_codes=("contradiction_visible", "w06_residual_uncertainty_retained"),
            candidate_packet_ids=tuple(
                packet.packet_id
                for packet in stage1_result.emitted_packets
                if packet.signal_kind is CounterpartSignalKind.CONTRADICTION
            ),
            basis_summary=(
                "contradiction_or_noise_visible",
                "claim_not_fact_boundary_preserved",
                "revalidate_before_response_required",
            ),
        )

    if (
        complementarity_visible
        and phase_verified
        and w05_boundary_clean
        and w06_boundary_clean
        and not has_blocked
        and not has_contradiction
    ):
        if has_transfer_success and has_transfer_attempt and has_claim:
            _add(
                AResponseKind.OFFER_CANDIDATE,
                "bounded_offer_candidate_not_executed",
                confidence=0.57,
                permitted_status="bounded_candidate",
                reason_codes=(
                    "visible_claim_relation_present",
                    "transfer_event_confirmed",
                    "w04_w05_w06_boundaries_preserved",
                ),
                object_ref="resource_token",
                candidate_packet_ids=tuple(
                    packet.packet_id
                    for packet in stage1_result.emitted_packets
                    if packet.signal_kind
                    in {
                        CounterpartSignalKind.RESOURCE_STATUS_CLAIM,
                        CounterpartSignalKind.TRANSFER_ATTEMPT,
                        CounterpartSignalKind.TRANSFER_RESULT,
                    }
                ),
                basis_summary=(
                    "visible_counterpart_claim_relation_present",
                    "transfer_confirmation_visible_as_observation_not_hidden_truth",
                    "self_state_asymmetry_marker_present_without_permission_upgrade",
                    "w04_w05_w06_boundaries_preserved",
                ),
            )
        elif w04_clean:
            _add(
                AResponseKind.TRANSFER_ATTEMPT_CANDIDATE,
                "bounded_transfer_attempt_candidate_not_executed",
                confidence=0.53,
                permitted_status="bounded_candidate",
                reason_codes=(
                    "visible_claim_relation_present",
                    "resource_asymmetry_candidate",
                    "w04_permitted_boundary_compatible",
                    "w05_permission_channel_clean",
                    "w06_execution_prohibited_preserved",
                ),
                object_ref="resource_token",
                candidate_packet_ids=tuple(
                    packet.packet_id
                    for packet in stage1_result.emitted_packets
                    if packet.signal_kind
                    in {
                        CounterpartSignalKind.RESOURCE_STATUS_CLAIM,
                        CounterpartSignalKind.TRANSFER_ATTEMPT,
                        CounterpartSignalKind.TRANSFER_RESULT,
                    }
                ),
                basis_summary=(
                    "visible_counterpart_claim_relation_present",
                    "self_state_asymmetry_marker_present_without_permission_upgrade",
                    "bounded_complementarity_candidate_without_oracle",
                    "w04_w05_w06_boundaries_preserved",
                ),
            )
        else:
            _add(
                AResponseKind.OFFER_CANDIDATE,
                "bounded_offer_candidate_not_executed",
                confidence=0.46,
                permitted_status="bounded_candidate",
                reason_codes=(
                    "visible_claim_relation_present",
                    "resource_asymmetry_candidate",
                    "w04_w05_w06_boundaries_preserved",
                ),
                object_ref="resource_token",
                candidate_packet_ids=tuple(
                    packet.packet_id
                    for packet in stage1_result.emitted_packets
                    if packet.signal_kind in {CounterpartSignalKind.RESOURCE_STATUS_CLAIM, CounterpartSignalKind.PRESENCE_PING}
                ),
                basis_summary=(
                    "visible_counterpart_claim_relation_present",
                    "self_state_asymmetry_marker_present_without_permission_upgrade",
                    "bounded_complementarity_candidate_without_oracle",
                    "w04_w05_w06_boundaries_preserved",
                ),
            )

    if has_transfer_failed and not has_blocked:
        _add(
            AResponseKind.REVALIDATE_BEFORE_RESPONSE,
            "revalidate_after_failed_transfer_observation",
            confidence=0.7,
            permitted_status="revalidate_required",
            reason_codes=("transfer_failure_observed", "no_clean_transfer_route"),
            candidate_packet_ids=tuple(
                packet.packet_id
                for packet in stage1_result.emitted_packets
                if packet.signal_kind in {CounterpartSignalKind.TRANSFER_RESULT, CounterpartSignalKind.TRANSFER_ATTEMPT}
            ),
            basis_summary=(
                "transfer_failure_observed",
                "no_clean_transfer_route",
                "revalidation_required_before_any_candidate",
            ),
        )

    if not candidates:
        _add(
            AResponseKind.OBSERVE_ONLY,
            "retain_observation_only",
            confidence=0.2,
            permitted_status="observe_only",
            reason_codes=("insufficient_visible_evidence_for_candidate",),
            target_ref=None,
            candidate_packet_ids=packet_ids,
            basis_summary=(
                "insufficient_visible_evidence_for_candidate",
                "no_permission_upgrade",
                "observation_only_path",
            ),
        )

    return tuple(candidates)


def classify_stage3_response(candidates: tuple[AResponseCandidate, ...]) -> tuple[AResponseKind, str | None, ResponseVerdict]:
    priority = (
        AResponseKind.BLOCK_DUE_CONSTRAINT,
        AResponseKind.REVALIDATE_BEFORE_RESPONSE,
        AResponseKind.TRANSFER_ATTEMPT_CANDIDATE,
        AResponseKind.OFFER_CANDIDATE,
        AResponseKind.REQUEST_CLARIFICATION,
        AResponseKind.REQUEST_STATUS,
        AResponseKind.ACKNOWLEDGE_PRESENCE,
        AResponseKind.OBSERVE_ONLY,
        AResponseKind.ABSTAIN,
        AResponseKind.NO_RESPONSE,
    )
    by_kind = {item.response_kind: item for item in candidates}
    selected = next((by_kind[k] for k in priority if k in by_kind), None)
    if selected is None:
        return AResponseKind.NO_RESPONSE, None, ResponseVerdict.NO_CANDIDATE
    verdict_map = {
        AResponseKind.OBSERVE_ONLY: ResponseVerdict.OBSERVE_ONLY,
        AResponseKind.ACKNOWLEDGE_PRESENCE: ResponseVerdict.OBSERVE_ONLY,
        AResponseKind.REQUEST_STATUS: ResponseVerdict.CLARIFICATION_NEEDED,
        AResponseKind.REQUEST_CLARIFICATION: ResponseVerdict.CLARIFICATION_NEEDED,
        AResponseKind.ABSTAIN: ResponseVerdict.REVALIDATION_NEEDED,
        AResponseKind.REVALIDATE_BEFORE_RESPONSE: ResponseVerdict.REVALIDATION_NEEDED,
        AResponseKind.BLOCK_DUE_CONSTRAINT: ResponseVerdict.BLOCKED,
        AResponseKind.OFFER_CANDIDATE: ResponseVerdict.BOUNDED_OFFER_CANDIDATE,
        AResponseKind.TRANSFER_ATTEMPT_CANDIDATE: ResponseVerdict.BOUNDED_TRANSFER_ATTEMPT_CANDIDATE,
        AResponseKind.NO_RESPONSE: ResponseVerdict.NO_CANDIDATE,
    }
    return selected.response_kind, selected.response_id, verdict_map[selected.response_kind]


def run_stage3_response_probe(
    scenario_name: str,
    *,
    include_falsifiers: bool = True,
) -> AResponseCandidateRun:
    stage1 = run_stage1_scenario(scenario_name, include_falsifiers=False)
    stage25 = run_stage25_reaction(scenario_name, include_falsifiers=False)
    response_candidates = extract_response_candidates_from_reaction_trace(scenario_name, stage1, stage25)
    selected_kind, selected_id, verdict = classify_stage3_response(response_candidates)
    phase_verified = all(step.phase_trace_summary.phase_coverage_verified for step in stage25.steps)
    phase_evidence = tuple(
        sorted(
            {
                ref
                for step in stage25.steps
                for ref in step.phase_trace_summary.phase_coverage_evidence
            }
        )
    )
    run = AResponseCandidateRun(
        run_id=f"stage3:{scenario_name}",
        scenario_name=scenario_name,
        execution_level=stage25.execution_surface.execution_level.value,
        subject_tick_used=stage25.execution_surface.subject_tick_used,
        owner_surface_used=stage25.execution_surface.owner_surface_used,
        adapter_projection_used=stage25.execution_surface.adapter_projection_used,
        fallback_reasons=stage25.execution_surface.fallback_reasons,
        phase_coverage_verified=phase_verified,
        phase_coverage_evidence=phase_evidence,
        response_candidates=response_candidates,
        selected_response_kind=selected_kind,
        selected_response_id=selected_id,
        response_verdict=verdict,
        claim_boundary=(
            "stage3_response_candidate_probe_only",
            "candidate_not_executed_trade",
            "no_autonomous_exchange_claim",
            "no_negotiation_claim",
            "no_economic_agency_claim",
            "no_subjective_need_awareness_claim",
        ),
        eval_only={
            "harness_truth": stage1.eval_only.get("harness_truth", {}),
            "success_labels": stage1.success_labels,
            "stage25_execution_surface": asdict(stage25.execution_surface),
            "stage25_reaction_markers": stage25.reaction_markers,
        },
    )
    if include_falsifiers:
        results = run_stage3_response_falsifiers(run)
        run = AResponseCandidateRun(
            run_id=run.run_id,
            scenario_name=run.scenario_name,
            execution_level=run.execution_level,
            subject_tick_used=run.subject_tick_used,
            owner_surface_used=run.owner_surface_used,
            adapter_projection_used=run.adapter_projection_used,
            fallback_reasons=run.fallback_reasons,
            phase_coverage_verified=run.phase_coverage_verified,
            phase_coverage_evidence=run.phase_coverage_evidence,
            response_candidates=run.response_candidates,
            selected_response_kind=run.selected_response_kind,
            selected_response_id=run.selected_response_id,
            response_verdict=run.response_verdict,
            claim_boundary=run.claim_boundary,
            falsifier_summary=tuple(asdict(item) for item in results),
            eval_only=run.eval_only,
        )
    return run


def serialize_stage3_response_run(
    run: AResponseCandidateRun,
    *,
    include_eval_only: bool = False,
    include_response_candidates: bool = True,
) -> dict[str, object]:
    return response_candidate_run_to_dict(
        run,
        include_eval_only=include_eval_only,
        include_response_candidates=include_response_candidates,
    )
