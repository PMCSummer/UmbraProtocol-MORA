from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from substrate.world0_generic_runner import (
    WorldRunnerAuthorityFlags,
    adapter_action_selection_blocked_fixture,
    ap01_execution_fixture,
    backend_worldstate_blocked_fixture,
    blocked_contact_fixture,
    contactspec_plan_blocked_fixture,
    effect_without_correlation_blocked_fixture,
    factory_solution_blocked_fixture,
    failed_backend_execution_fixture,
    no_ap01_no_execution_fixture,
    noop_world_fixture,
    passive_event_fixture,
    replay_trace_fixture,
    run_world_loop,
    scenario_label_blocked_fixture,
    summarize_runner_conformance,
    timeout_max_tick_fixture,
    two_backend_grid_fixture,
    two_backend_inventory_fixture,
)


CASES = {
    "noop_cycle": noop_world_fixture,
    "ap01_execution": ap01_execution_fixture,
    "blocked_contact": blocked_contact_fixture,
    "passive_event": passive_event_fixture,
    "failed_backend_execution": failed_backend_execution_fixture,
    "adapter_action_selection_blocked": adapter_action_selection_blocked_fixture,
    "contactspec_plan_blocked": contactspec_plan_blocked_fixture,
    "backend_worldstate_blocked": backend_worldstate_blocked_fixture,
    "scenario_label_blocked": scenario_label_blocked_fixture,
    "two_backend_grid": two_backend_grid_fixture,
    "two_backend_inventory": two_backend_inventory_fixture,
    "factory_solution_blocked": factory_solution_blocked_fixture,
    "timeout_max_tick": timeout_max_tick_fixture,
    "replay_trace": replay_trace_fixture,
    "no_ap01_no_execution": no_ap01_no_execution_fixture,
    "effect_without_correlation_blocked": effect_without_correlation_blocked_fixture,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="WORLD0 generic runner demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-trace", action="store_true")
    parser.add_argument("--show-contact", action="store_true")
    parser.add_argument("--show-projection", action="store_true")
    parser.add_argument("--show-tick", action="store_true")
    parser.add_argument("--show-ap01", action="store_true")
    parser.add_argument("--show-execution", action="store_true")
    parser.add_argument("--show-effect", action="store_true")
    parser.add_argument("--show-residue", action="store_true")
    parser.add_argument("--show-counters", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    parser.add_argument("--show-blocked", action="store_true")
    args = parser.parse_args()

    if args.list_cases:
        for case_id in CASES:
            print(case_id)
        return 0
    if not args.case:
        parser.error("--case is required unless --list-cases is used")

    bundle = CASES[args.case]()
    result = run_world_loop(bundle.loop_input, adapter=bundle.adapter)
    summary = summarize_runner_conformance(result)
    payload: dict[str, object] = {
        "case_id": args.case,
        "run_id": result.run_id,
        "cycle_ids": tuple(item.cycle_id for item in result.cycle_traces),
        "cycle_status": tuple(item.cycle_status.value for item in result.cycle_traces),
        "execution_status": tuple(item.execution_status.value for item in result.cycle_traces),
        "contact_refs": tuple(ref for trace in result.cycle_traces for ref in trace.contact_frame_refs),
        "projection_refs": tuple(ref for trace in result.cycle_traces for ref in trace.projection_refs),
        "subject_tick_refs": tuple(trace.subject_tick_ref for trace in result.cycle_traces if trace.subject_tick_ref),
        "ap01_refs": tuple(ref for trace in result.cycle_traces for ref in trace.ap01_request_refs),
        "backend_execution_refs": tuple(ref for trace in result.cycle_traces for ref in trace.backend_execution_refs),
        "effect_feedback_refs": tuple(ref for trace in result.cycle_traces for ref in trace.world_effect_frame_refs),
        "residue_refs": result.residue_refs,
        "uncertainty_refs": result.uncertainty_refs,
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "counters": asdict(result.counters),
        "authority_flags": asdict(WorldRunnerAuthorityFlags()),
        "no_runner_action_selection": result.no_action_selected_by_runner,
        "no_runner_ap01_creation": result.no_ap01_created_by_runner,
        "no_execution_without_ap01": result.no_world_submission_without_ap01,
        "no_backend_worldstate_to_subject": True,
        "no_automation_factory_autonomy_claim": (
            not result.automation_claimed and not result.factory_solution_hardcoded
        ),
        "bounded_claim": (
            "WORLD0 orchestrates contact->projection->tick->AP01-bound execution->effect feedback; "
            "it does not select actions, create AP01, or claim autonomy/factory completion."
        ),
        "summary": summary,
    }

    if args.show_trace:
        payload["trace"] = tuple(
            {
                "cycle_id": item.cycle_id,
                "contact_spec_ref": item.contact_spec_ref,
                "cycle_status": item.cycle_status.value,
                "execution_status": item.execution_status.value,
                "blocked_reasons": tuple(reason.value for reason in item.blocked_reasons),
                "contact_frame_refs": item.contact_frame_refs,
                "projection_refs": item.projection_refs,
                "subject_tick_ref": item.subject_tick_ref,
                "ap01_request_refs": item.ap01_request_refs,
                "backend_execution_refs": item.backend_execution_refs,
                "world_effect_frame_refs": item.world_effect_frame_refs,
            }
            for item in result.cycle_traces
        )
    if args.show_contact:
        payload["contact_refs"] = payload["contact_refs"]
    if args.show_projection:
        payload["projection_refs"] = payload["projection_refs"]
    if args.show_tick:
        payload["subject_tick_refs"] = payload["subject_tick_refs"]
    if args.show_ap01:
        payload["ap01_refs"] = payload["ap01_refs"]
    if args.show_execution:
        payload["backend_execution_refs"] = payload["backend_execution_refs"]
    if args.show_effect:
        payload["effect_feedback_refs"] = payload["effect_feedback_refs"]
    if args.show_residue:
        payload["residue_refs"] = payload["residue_refs"]
    if args.show_counters:
        payload["counters"] = payload["counters"]
    if args.show_authority:
        payload["authority_flags"] = payload["authority_flags"]
    if args.show_blocked:
        payload["blocked_reasons"] = payload["blocked_reasons"]

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"case_id: {payload['case_id']}")
        print(f"run_id: {payload['run_id']}")
        print(f"cycle_ids: {payload['cycle_ids']}")
        print(f"cycle_status: {payload['cycle_status']}")
        print(f"execution_status: {payload['execution_status']}")
        print(f"blocked_reasons: {payload['blocked_reasons']}")
        if args.report or args.show_counters:
            print(f"counters: {payload['counters']}")
        if args.report or args.show_authority:
            print(f"authority_flags: {payload['authority_flags']}")
        if args.report:
            print(f"summary: {payload['summary']}")
            print(f"bounded_claim: {payload['bounded_claim']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
