from __future__ import annotations

from dataclasses import asdict

from .falsifiers import run_symbolic_trade_falsifiers
from .packets import packet_to_dict
from .scenario import build_stage1_result, list_symbolic_trade_scenarios, stage0_packet_dry_run_result, with_falsifier_results
from .telemetry import summarize_result


def run_stage0_packet_dry_run(*, include_falsifiers: bool = True):
    result = stage0_packet_dry_run_result()
    if include_falsifiers:
        result = with_falsifier_results(result, run_symbolic_trade_falsifiers(result))
    return result


def run_stage1_scenario(scenario_id: str, *, include_falsifiers: bool = True):
    result = build_stage1_result(scenario_id)
    if include_falsifiers:
        result = with_falsifier_results(result, run_symbolic_trade_falsifiers(result))
    return result


def list_scenarios() -> tuple[str, ...]:
    return list_symbolic_trade_scenarios()


def result_to_dict(result, *, include_eval_only: bool = False) -> dict[str, object]:
    steps = []
    for step in result.steps:
        steps.append(
            {
                "step_index": step.step_index,
                "signal_kind": step.scripted_b_emission.signal_kind.value if step.scripted_b_emission else None,
                "subject_visible_packets": [packet_to_dict(packet) for packet in step.subject_visible_packets],
                "expected_phase_obligations": list(step.expected_phase_obligations),
            }
        )

    payload = {
        "scenario_id": result.scenario_id,
        "stage": result.stage.value,
        "packet_count": len(result.emitted_packets),
        "steps": steps,
        "phase_obligation_summary": list(result.phase_obligation_summary),
        "falsifier_results": [asdict(item) for item in result.falsifier_results],
        "trace_summary": result.trace_summary,
        "success_labels": list(result.success_labels),
        "claim_discipline_markers": list(result.claim_discipline_markers),
        "telemetry": summarize_result(result),
    }
    if include_eval_only:
        payload["eval_only"] = result.eval_only
    return payload
