from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from substrate.p17b_live_symbolic_minifactory import (
    adapter_solution_sequence_blocked_fixture,
    blocked_station_fixture,
    contactspec_factory_script_blocked_fixture,
    cost_winner_permission_blocked_fixture,
    failed_intermediate_stops_chain_fixture,
    hidden_recipe_blocked_fixture,
    missing_ap01_blocks_step_fixture,
    missing_resource_blocks_chain_fixture,
    noop_not_completion_fixture,
    p17_proof_not_live_execution_fixture,
    provider_hint_truth_blocked_fixture,
    replay_trace_fixture,
    residue_recovery_partial_fixture,
    successful_bounded_chain_fixture,
    summarize_p17b_run,
    unverified_intermediate_blocks_downstream_fixture,
)


CASES = {
    "successful_bounded_chain": successful_bounded_chain_fixture,
    "missing_ap01_blocks_step": missing_ap01_blocks_step_fixture,
    "failed_intermediate_stops_chain": failed_intermediate_stops_chain_fixture,
    "unverified_intermediate_blocks_downstream": unverified_intermediate_blocks_downstream_fixture,
    "missing_resource_blocks_chain": missing_resource_blocks_chain_fixture,
    "blocked_station": blocked_station_fixture,
    "hidden_recipe_blocked": hidden_recipe_blocked_fixture,
    "adapter_solution_sequence_blocked": adapter_solution_sequence_blocked_fixture,
    "contactspec_factory_script_blocked": contactspec_factory_script_blocked_fixture,
    "cost_winner_permission_blocked": cost_winner_permission_blocked_fixture,
    "provider_hint_truth_blocked": provider_hint_truth_blocked_fixture,
    "p17_proof_not_live_execution": p17_proof_not_live_execution_fixture,
    "noop_not_completion": noop_not_completion_fixture,
    "residue_recovery_partial": residue_recovery_partial_fixture,
    "replay_trace": replay_trace_fixture,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="P17B live symbolic mini-factory demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-need", action="store_true")
    parser.add_argument("--show-steps", action="store_true")
    parser.add_argument("--show-world0", action="store_true")
    parser.add_argument("--show-micro", action="store_true")
    parser.add_argument("--show-cost", action="store_true")
    parser.add_argument("--show-ap01", action="store_true")
    parser.add_argument("--show-effects", action="store_true")
    parser.add_argument("--show-verification", action="store_true")
    parser.add_argument("--show-residue", action="store_true")
    parser.add_argument("--show-advance", action="store_true")
    parser.add_argument("--show-trace", action="store_true")
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

    run = CASES[args.case]().run
    payload: dict[str, object] = {
        "case_id": args.case,
        "run_id": run.run_id,
        "final_status": run.final_status.value,
        "step_statuses": tuple(trace.status.value for trace in run.step_traces),
        "need_refs": tuple(dict.fromkeys((run.need.need_id, run.need.target_ref, *run.need.pressure_refs, *run.need.public_basis_refs))),
        "micro_refs": tuple(ref for trace in run.step_traces for ref in trace.micro_operation_refs),
        "cost_refs": tuple(ref for trace in run.step_traces for ref in trace.cost_comparison_refs),
        "world0_refs": run.world0_run_refs,
        "ap01_refs": tuple(ref for trace in run.step_traces for ref in trace.ap01_request_refs),
        "execution_refs": tuple(ref for trace in run.step_traces for ref in trace.backend_execution_refs),
        "effect_refs": tuple(ref for trace in run.step_traces for ref in trace.world_effect_feedback_refs),
        "verified_intermediates": tuple(ref for trace in run.step_traces for ref in trace.verified_intermediate_refs),
        "residue_refs": run.residue_refs,
        "blocked_reasons": tuple(reason.value for reason in run.blocked_reasons),
        "advance_decisions": tuple(
            {
                "decision_id": item.decision_id,
                "current_step_ref": item.current_step_ref,
                "next_step_ref": item.next_step_ref,
                "advance_allowed": item.advance_allowed,
                "missing_intermediate_refs": item.missing_intermediate_refs,
                "blocked_reasons": tuple(reason.value for reason in item.blocked_reasons),
            }
            for item in run.advance_decisions
        ),
        "counters": asdict(run.counters),
        "authority_flags": asdict(run.authority_flags),
        "bounded_claim": (
            "P17B validates a bounded live symbolic mini-factory chain through WORLD0/AP01/effect verification; "
            "it does not claim general factory automation or autonomy."
        ),
        "summary": summarize_p17b_run(run),
    }

    if args.show_need:
        payload["need"] = asdict(run.need)
    if args.show_steps or args.show_trace:
        payload["step_traces"] = tuple(
            {
                "step_id": trace.step_id,
                "status": trace.status.value,
                "cycle_refs": trace.cycle_refs,
                "ap01_request_refs": trace.ap01_request_refs,
                "backend_execution_refs": trace.backend_execution_refs,
                "world_effect_feedback_refs": trace.world_effect_feedback_refs,
                "observed_effect_refs": trace.observed_effect_refs,
                "expected_effect_refs": trace.expected_effect_refs,
                "verified_intermediate_refs": trace.verified_intermediate_refs,
                "residue_refs": trace.residue_refs,
                "blocked_reasons": tuple(reason.value for reason in trace.blocked_reasons),
            }
            for trace in run.step_traces
        )
    if args.show_world0:
        payload["world0_refs"] = run.world0_run_refs
    if args.show_micro:
        payload["micro_refs"] = payload["micro_refs"]
    if args.show_cost:
        payload["cost_refs"] = payload["cost_refs"]
    if args.show_ap01:
        payload["ap01_refs"] = payload["ap01_refs"]
    if args.show_effects:
        payload["effect_refs"] = payload["effect_refs"]
    if args.show_verification:
        payload["verification_records"] = tuple(asdict(item) for item in run.verification_records)
    if args.show_residue:
        payload["residue_stop_frames"] = tuple(asdict(item) for item in run.residue_stop_frames)
    if args.show_advance:
        payload["advance_decisions"] = payload["advance_decisions"]
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
        print(f"final_status: {payload['final_status']}")
        print(f"step_statuses: {payload['step_statuses']}")
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

