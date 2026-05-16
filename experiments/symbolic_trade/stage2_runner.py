from __future__ import annotations

from dataclasses import asdict
import json

from .falsifiers import run_stage2_trace_falsifiers, run_symbolic_trade_falsifiers
from .phase_adapters import AdapterState, adapt_w01, adapt_w02, adapt_w03, adapt_w04, adapt_w05, adapt_w06
from .runner import run_stage1_scenario
from .subject_trace import (
    PhaseReactionSummary,
    Stage2TraceVerdict,
    SubjectTraceRun,
    SubjectTraceStep,
    SubjectVisiblePacketRef,
    phase_record_from_adapter,
    subject_trace_run_to_dict,
)


def run_stage2_trace_scenario(scenario_id: str, *, include_falsifiers: bool = True) -> SubjectTraceRun:
    stage1 = run_stage1_scenario(scenario_id, include_falsifiers=False)
    adapter_state = AdapterState(seen_claim_counts={})
    steps: list[SubjectTraceStep] = []
    coverage = {"W01", "W02", "W03", "W04", "W05", "W06"}

    for step in stage1.steps:
        phase_records = []
        packet_refs = []
        blocked = 0
        revalidate = 0
        uncertain = 0
        hint_only = 0
        correction = 0
        residue = 0

        for packet in step.subject_visible_packets:
            packet_refs.append(
                SubjectVisiblePacketRef(
                    packet_id=packet.packet_id,
                    step_index=step.step_index,
                    signal_kind=packet.signal_kind.value,
                    source_authority=packet.source_authority.value,
                )
            )

            trace_id = f"{scenario_id}:step:{step.step_index}:packet:{packet.packet_id}"

            w01_in, w01_out = adapt_w01(packet, trace_id=trace_id, step_index=step.step_index)
            rec = phase_record_from_adapter(w01_in, w01_out)
            phase_records.append(rec)

            w02_in, w02_out = adapt_w02(packet, trace_id=trace_id, state=adapter_state)
            rec = phase_record_from_adapter(w02_in, w02_out)
            phase_records.append(rec)

            w03_in, w03_out = adapt_w03(packet, trace_id=trace_id, state=adapter_state)
            rec = phase_record_from_adapter(w03_in, w03_out)
            phase_records.append(rec)

            w04_in, w04_out = adapt_w04(packet, trace_id=trace_id)
            rec = phase_record_from_adapter(w04_in, w04_out)
            phase_records.append(rec)

            w05_in, w05_out = adapt_w05(packet, trace_id=trace_id, w04_status=w04_out.decision_status)
            rec = phase_record_from_adapter(w05_in, w05_out)
            phase_records.append(rec)

            w06_in, w06_out = adapt_w06(packet, trace_id=trace_id, w05_status=w05_out.decision_status)
            rec = phase_record_from_adapter(w06_in, w06_out)
            phase_records.append(rec)

            for record in phase_records[-6:]:
                if "blocked" in record.decision_status:
                    blocked += 1
                if "revalidate" in record.decision_status or any("revalidate" in marker for marker in record.uncertainty_markers):
                    revalidate += 1
                if record.uncertainty_markers:
                    uncertain += 1
                if "hint_only" in record.decision_status:
                    hint_only += 1
                if any("correction_candidate_created:true" == x for x in record.downstream_permission_delta):
                    correction += 1
                if any("residue" in marker for marker in record.uncertainty_markers):
                    residue += 1

        steps.append(
            SubjectTraceStep(
                step_index=step.step_index,
                packet_refs=tuple(packet_refs),
                phase_records=tuple(phase_records),
                reaction_summary=PhaseReactionSummary(
                    blocked_count=blocked,
                    revalidate_count=revalidate,
                    uncertain_count=uncertain,
                    hint_only_count=hint_only,
                    correction_candidate_count=correction,
                    residue_count=residue,
                ),
            )
        )

    flattened = [record for step in steps for record in step.phase_records]
    phase_codes = {record.phase_code for record in flattened}
    coverage_complete = coverage.issubset(phase_codes)
    serialized_phase_records = json.dumps([asdict(record) for record in flattened], sort_keys=True).lower()
    forbidden_trace_markers = (
        "harness_truth",
        "mutually_beneficial_trade_possible_eval_only",
        "eval_only",
        "success_labels",
        "inferred_by_harness_for_eval_only",
    )
    no_hidden_truth_leak = not any(marker in serialized_phase_records for marker in forbidden_trace_markers)
    claim_boundary = all(
        not any("trade_intent" in code for code in record.reason_codes)
        for record in flattened
    )

    verdict = Stage2TraceVerdict(
        status="trace_ready" if coverage_complete and no_hidden_truth_leak and claim_boundary else "trace_contested",
        coverage_complete=coverage_complete,
        no_hidden_truth_leak=no_hidden_truth_leak,
        claim_boundary_preserved=claim_boundary,
        adapter_projection_used=True,
        reason_codes=(
            "w01_to_w06_coverage_complete" if coverage_complete else "missing_phase_coverage",
            "no_hidden_truth_in_trace" if no_hidden_truth_leak else "hidden_truth_or_eval_label_detected",
            "claim_boundary_preserved" if claim_boundary else "claim_boundary_violation",
        ),
    )

    run = SubjectTraceRun(
        scenario_id=scenario_id,
        stage="stage_2_subject_adapter_trace_through",
        packet_count=len(stage1.emitted_packets),
        steps=tuple(steps),
        phase_coverage=tuple(sorted(phase_codes)),
        phase_obligation_summary=stage1.phase_obligation_summary,
        stage2_trace_verdict=verdict,
        falsifier_results=(),
        claim_boundary=(
            "stage2_trace_only_no_autonomous_trade_claim",
            "no_negotiation_claim",
            "no_social_cognition_claim",
        ),
        eval_only=stage1.eval_only,
    )

    if include_falsifiers:
        stage1_falsifiers = run_symbolic_trade_falsifiers(stage1)
        stage2_falsifiers = run_stage2_trace_falsifiers(run)
        merged = [asdict(item) for item in stage1_falsifiers] + [asdict(item) for item in stage2_falsifiers]
        run = SubjectTraceRun(
            scenario_id=run.scenario_id,
            stage=run.stage,
            packet_count=run.packet_count,
            steps=run.steps,
            phase_coverage=run.phase_coverage,
            phase_obligation_summary=run.phase_obligation_summary,
            stage2_trace_verdict=run.stage2_trace_verdict,
            falsifier_results=tuple(merged),
            claim_boundary=run.claim_boundary,
            eval_only=run.eval_only,
        )
    return run


def stage2_trace_to_dict(run: SubjectTraceRun, *, include_eval_only: bool = False) -> dict[str, object]:
    return subject_trace_run_to_dict(run, include_eval_only=include_eval_only)
