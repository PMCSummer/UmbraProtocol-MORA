from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True, slots=True)
class SubjectVisiblePacketRef:
    packet_id: str
    step_index: int
    signal_kind: str
    source_authority: str


@dataclass(frozen=True, slots=True)
class PhaseAdapterInput:
    trace_id: str
    phase_code: str
    input_refs: tuple[str, ...]
    source_packet_ids: tuple[str, ...]
    adapter_source: str


@dataclass(frozen=True, slots=True)
class PhaseAdapterOutput:
    trace_id: str
    phase_code: str
    output_refs: tuple[str, ...]
    decision_status: str
    reason_codes: tuple[str, ...]
    uncertainty_markers: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    downstream_permission_delta: tuple[str, ...]
    execution_prohibited: bool
    adapter_limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseTraceRecord:
    trace_id: str
    phase_code: str
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    decision_status: str
    reason_codes: tuple[str, ...]
    uncertainty_markers: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    downstream_permission_delta: tuple[str, ...]
    execution_prohibited: bool
    adapter_limitations: tuple[str, ...]
    source_packet_ids: tuple[str, ...]
    adapter_source: str


@dataclass(frozen=True, slots=True)
class PhaseReactionSummary:
    blocked_count: int
    revalidate_count: int
    uncertain_count: int
    hint_only_count: int
    correction_candidate_count: int
    residue_count: int


@dataclass(frozen=True, slots=True)
class SubjectTraceStep:
    step_index: int
    packet_refs: tuple[SubjectVisiblePacketRef, ...]
    phase_records: tuple[PhaseTraceRecord, ...]
    reaction_summary: PhaseReactionSummary


@dataclass(frozen=True, slots=True)
class Stage2TraceVerdict:
    status: str
    coverage_complete: bool
    no_hidden_truth_leak: bool
    claim_boundary_preserved: bool
    adapter_projection_used: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectTraceRun:
    scenario_id: str
    stage: str
    packet_count: int
    steps: tuple[SubjectTraceStep, ...]
    phase_coverage: tuple[str, ...]
    phase_obligation_summary: tuple[str, ...]
    stage2_trace_verdict: Stage2TraceVerdict
    falsifier_results: tuple[dict[str, object], ...] = ()
    claim_boundary: tuple[str, ...] = ()
    eval_only: dict[str, object] = field(default_factory=dict)


def phase_record_from_adapter(adapter_input: PhaseAdapterInput, adapter_output: PhaseAdapterOutput) -> PhaseTraceRecord:
    return PhaseTraceRecord(
        trace_id=adapter_input.trace_id,
        phase_code=adapter_input.phase_code,
        input_refs=adapter_input.input_refs,
        output_refs=adapter_output.output_refs,
        decision_status=adapter_output.decision_status,
        reason_codes=adapter_output.reason_codes,
        uncertainty_markers=adapter_output.uncertainty_markers,
        prohibited_claims=adapter_output.prohibited_claims,
        downstream_permission_delta=adapter_output.downstream_permission_delta,
        execution_prohibited=adapter_output.execution_prohibited,
        adapter_limitations=adapter_output.adapter_limitations,
        source_packet_ids=adapter_input.source_packet_ids,
        adapter_source=adapter_input.adapter_source,
    )


def subject_trace_run_to_dict(run: SubjectTraceRun, *, include_eval_only: bool = False) -> dict[str, object]:
    steps = []
    for step in run.steps:
        phase_records = []
        for record in step.phase_records:
            phase_records.append(asdict(record))
        steps.append(
            {
                "step_index": step.step_index,
                "packet_refs": [asdict(item) for item in step.packet_refs],
                "phase_records": phase_records,
                "reaction_summary": asdict(step.reaction_summary),
            }
        )

    payload = {
        "scenario_id": run.scenario_id,
        "stage": run.stage,
        "packet_count": run.packet_count,
        "phase_coverage": list(run.phase_coverage),
        "phase_obligation_summary": list(run.phase_obligation_summary),
        "stage2_trace_verdict": asdict(run.stage2_trace_verdict),
        "falsifier_results": list(run.falsifier_results),
        "claim_boundary": list(run.claim_boundary),
        "steps": steps,
    }
    if include_eval_only:
        payload["eval_only"] = run.eval_only
    return payload
