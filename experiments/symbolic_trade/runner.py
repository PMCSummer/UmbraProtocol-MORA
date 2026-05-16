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


def run_stage2_trace(scenario_id: str, *, include_falsifiers: bool = True):
    from .stage2_runner import run_stage2_trace_scenario

    return run_stage2_trace_scenario(scenario_id, include_falsifiers=include_falsifiers)


def run_stage25_reaction(scenario_id: str, *, include_falsifiers: bool = True):
    from .stage25_runner import run_stage25_reaction_probe

    return run_stage25_reaction_probe(scenario_id, include_falsifiers=include_falsifiers)


def run_stage3_response(scenario_id: str, *, include_falsifiers: bool = True):
    from .stage3_runner import run_stage3_response_probe

    return run_stage3_response_probe(scenario_id, include_falsifiers=include_falsifiers)


def run_stage4_cycle(
    scenario_id: str,
    *,
    include_falsifiers: bool = True,
    include_eval_only: bool = False,
    execute_transfer_affordance: bool = False,
    no_execute_transfer_affordance: bool = False,
):
    from .stage4_trade_cycle_runner import run_stage4_trade_cycle

    return run_stage4_trade_cycle(
        scenario_id,
        include_falsifiers=include_falsifiers,
        include_eval_only=include_eval_only,
        execute_transfer_affordance=execute_transfer_affordance,
        force_no_execute=no_execute_transfer_affordance,
    )


def run_stage5_affordance_trace(
    scenario_id: str,
    *,
    include_falsifiers: bool = True,
    include_eval_only: bool = False,
    execute_world_actuator: bool = False,
):
    from .stage5_affordance_trace_runner import run_stage5_affordance_trace

    return run_stage5_affordance_trace(
        scenario_id,
        include_falsifiers=include_falsifiers,
        include_eval_only=include_eval_only,
        execute_world_actuator=execute_world_actuator,
    )


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


def stage2_result_to_dict(result, *, include_eval_only: bool = False) -> dict[str, object]:
    from .stage2_runner import stage2_trace_to_dict

    return stage2_trace_to_dict(result, include_eval_only=include_eval_only)


def stage25_result_to_dict(result, *, include_eval_only: bool = False) -> dict[str, object]:
    from .stage25_runner import stage25_reaction_result_to_dict

    return stage25_reaction_result_to_dict(result, include_eval_only=include_eval_only)


def stage3_result_to_dict(
    result,
    *,
    include_eval_only: bool = False,
    include_response_candidates: bool = True,
) -> dict[str, object]:
    from .stage3_runner import serialize_stage3_response_run

    return serialize_stage3_response_run(
        result,
        include_eval_only=include_eval_only,
        include_response_candidates=include_response_candidates,
    )


def stage4_result_to_dict(
    result,
    *,
    include_eval_only: bool = False,
    include_transfer_episode: bool = True,
    include_clarification_state: bool = False,
) -> dict[str, object]:
    from .stage4_trade_cycle_runner import stage4_trade_cycle_to_dict

    return stage4_trade_cycle_to_dict(
        result,
        include_eval_only=include_eval_only,
        include_transfer_episode=include_transfer_episode,
        include_clarification_state=include_clarification_state,
    )


def stage5_result_to_dict(
    result,
    *,
    include_eval_only: bool = False,
    include_affordance_records: bool = True,
    include_affordance_ledger: bool = False,
) -> dict[str, object]:
    from .stage5_affordance_trace_runner import stage5_affordance_trace_to_dict

    return stage5_affordance_trace_to_dict(
        result,
        include_eval_only=include_eval_only,
        include_affordance_records=include_affordance_records,
        include_affordance_ledger=include_affordance_ledger,
    )
