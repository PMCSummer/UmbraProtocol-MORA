from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Callable

from substrate.cost1_action_cost_efficiency import (
    ActionCostVectorInput,
    CostComparisonInput,
    build_action_cost_vector,
    build_cost_comparison_frame,
    cost_comparison_no_action_fixture,
    cost_hint_permission_blocked_fixture,
    declared_observed_mismatch_fixture,
    hidden_backend_cost_blocked_fixture,
    material_vs_energy_tradeoff_fixture,
    observed_cost_fixture,
    provider_declared_cost_fixture,
    risk_vs_material_fixture,
    scalar_hiding_blocked_fixture,
    setup_time_fixture,
    station_occupation_fixture,
    summarize_cost_conformance,
    throughput_repeated_fixture,
    throughput_single_run_fixture,
    tool_wear_fixture,
    unknown_dimension_fixture,
    value_assignment_blocked_fixture,
)


def _case_material_vs_energy_tradeoff() -> CostComparisonInput:
    return material_vs_energy_tradeoff_fixture()


def _case_provider_declared_cost() -> ActionCostVectorInput:
    return provider_declared_cost_fixture()


def _case_observed_cost() -> ActionCostVectorInput:
    return observed_cost_fixture()


def _case_unknown_dimension() -> ActionCostVectorInput:
    return unknown_dimension_fixture()


def _case_scalar_hiding_blocked() -> ActionCostVectorInput:
    return scalar_hiding_blocked_fixture()


def _case_risk_vs_material() -> CostComparisonInput:
    return risk_vs_material_fixture()


def _case_setup_time_tradeoff() -> ActionCostVectorInput:
    return setup_time_fixture()


def _case_tool_wear() -> ActionCostVectorInput:
    return tool_wear_fixture()


def _case_station_occupation() -> ActionCostVectorInput:
    return station_occupation_fixture()


def _case_throughput_single_run() -> ActionCostVectorInput:
    frame = throughput_single_run_fixture()
    return ActionCostVectorInput(
        vector_id="cost:v:throughput_single",
        candidate_ref=frame.candidate_ref,
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:throughput",),
        dimensions=(),
        metadata_refs=(f"throughput_status:{frame.support_status.value}",),
    )


def _case_throughput_repeated() -> ActionCostVectorInput:
    frame = throughput_repeated_fixture()
    return ActionCostVectorInput(
        vector_id="cost:v:throughput_repeated",
        candidate_ref=frame.candidate_ref,
        candidate_kind="micro_operation",
        current_pressure_context_refs=("pressure:throughput",),
        dimensions=(),
        metadata_refs=(f"throughput_status:{frame.support_status.value}",),
    )


def _case_declared_observed_mismatch() -> CostComparisonInput:
    vector, delta = declared_observed_mismatch_fixture()
    return CostComparisonInput(
        comparison_id="cost:cmp:declared_observed_mismatch",
        vectors=(vector,),
        context_refs=("ctx:mismatch",),
        pressure_refs=("pressure:energy_budget",),
        deltas=(delta,),
    )


def _case_cost_comparison_no_action() -> CostComparisonInput:
    return cost_comparison_no_action_fixture()


def _case_hidden_backend_cost_blocked() -> ActionCostVectorInput:
    return hidden_backend_cost_blocked_fixture()


def _case_cost_hint_permission_blocked() -> CostComparisonInput:
    return cost_hint_permission_blocked_fixture()


def _case_value_assignment_blocked() -> CostComparisonInput:
    return value_assignment_blocked_fixture()


VECTOR_CASES: dict[str, Callable[[], ActionCostVectorInput]] = {
    "provider_declared_cost": _case_provider_declared_cost,
    "observed_cost": _case_observed_cost,
    "unknown_dimension": _case_unknown_dimension,
    "scalar_hiding_blocked": _case_scalar_hiding_blocked,
    "setup_time_tradeoff": _case_setup_time_tradeoff,
    "tool_wear": _case_tool_wear,
    "station_occupation": _case_station_occupation,
    "throughput_single_run": _case_throughput_single_run,
    "throughput_repeated": _case_throughput_repeated,
    "hidden_backend_cost_blocked": _case_hidden_backend_cost_blocked,
}

COMPARISON_CASES: dict[str, Callable[[], CostComparisonInput]] = {
    "material_vs_energy_tradeoff": _case_material_vs_energy_tradeoff,
    "risk_vs_material": _case_risk_vs_material,
    "declared_observed_mismatch": _case_declared_observed_mismatch,
    "cost_comparison_no_action": _case_cost_comparison_no_action,
    "cost_hint_permission_blocked": _case_cost_hint_permission_blocked,
    "value_assignment_blocked": _case_value_assignment_blocked,
}

CASES: tuple[str, ...] = tuple((*VECTOR_CASES.keys(), *COMPARISON_CASES.keys()))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="COST1 action cost comparison demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-vectors", action="store_true")
    parser.add_argument("--show-dimensions", action="store_true")
    parser.add_argument("--show-comparison", action="store_true")
    parser.add_argument("--show-mismatch", action="store_true")
    parser.add_argument("--show-throughput", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    parser.add_argument("--show-blocked", action="store_true")
    parser.add_argument("--show-counters", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.list_cases:
        for case_id in CASES:
            print(case_id)
        return 0

    if not args.case_id or args.case_id not in CASES:
        print("Specify --case with valid id; use --list-cases.")
        return 2

    throughput_payload: dict[str, object] | None = None
    if args.case_id in VECTOR_CASES:
        if args.case_id == "throughput_single_run":
            frame = throughput_single_run_fixture()
            throughput_payload = {"status": frame.support_status.value, "repeated_trace_count": frame.repeated_trace_count}
        if args.case_id == "throughput_repeated":
            frame = throughput_repeated_fixture()
            throughput_payload = {"status": frame.support_status.value, "repeated_trace_count": frame.repeated_trace_count}
        result = build_action_cost_vector(VECTOR_CASES[args.case_id]())
    else:
        result = build_cost_comparison_frame(COMPARISON_CASES[args.case_id]())
    summary = summarize_cost_conformance(result)

    payload: dict[str, object] = {
        "case_id": args.case_id,
        "validation_status": result.status.value,
        "compared_candidates": result.comparison.compared_candidate_refs if result.comparison else tuple(item.candidate_ref for item in result.vectors),
        "cost_vector_refs": result.vector_refs,
        "dimension_breakdown": result.comparison.dimension_breakdown_refs if result.comparison else tuple(item.dimension.value for item in result.vectors[0].dimensions) if result.vectors else (),
        "evidence_classifications": tuple(item.evidence_kind.value for vector in result.vectors for item in vector.dimensions),
        "unknown_missing_dimensions": tuple(item for vector in result.vectors for item in vector.missing_dimension_refs),
        "warnings": result.warnings,
        "mismatch_residue_refs": result.comparison.mismatch_residue_refs if result.comparison else (),
        "throughput_support_status": throughput_payload["status"] if throughput_payload else None,
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "authority_flags": asdict(result.authority_flags),
        "ap01_request_emitted": False,
        "action_selected": False,
        "world_submission_emitted": False,
        "value_assigned": False,
        "fact_claimed": False,
        "cause_confirmed": False,
        "mature_recipe_claimed": False,
        "mature_skill_claimed": False,
        "automation_claimed": False,
        "bounded_claim": "COST1 compares explicit cost dimensions with evidence classes and uncertainty; it does not select actions, emit AP01, or execute the world.",
    }
    if args.show_vectors:
        payload["vectors"] = [item.vector_id for item in result.vectors]
    if args.show_dimensions:
        payload["dimensions"] = {
            item.vector_id: [f"{dim.dimension.value}:{dim.evidence_kind.value}:{dim.status.value}" for dim in item.dimensions]
            for item in result.vectors
        }
    if args.show_comparison and result.comparison is not None:
        payload["comparison"] = {
            "comparison_id": result.comparison.comparison_id,
            "lower_by_dimension": result.comparison.lower_cost_candidate_refs_by_dimension,
            "higher_by_dimension": result.comparison.higher_cost_candidate_refs_by_dimension,
            "unresolved_candidates": result.comparison.unresolved_candidate_refs,
        }
    if args.show_mismatch and result.comparison is not None:
        payload["mismatch"] = result.comparison.mismatch_residue_refs
    if args.show_throughput:
        payload["throughput"] = throughput_payload
    if args.show_authority:
        payload["authority"] = asdict(result.authority_flags)
    if args.show_blocked:
        payload["blocked"] = tuple(item.value for item in result.blocked_reasons)
    if args.show_counters:
        payload["counters"] = asdict(result.counters)

    if args.json:
        payload["summary"] = summary
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.report:
        print(f"case_id: {payload['case_id']}")
        print(f"validation_status: {payload['validation_status']}")
        print(f"compared_candidates: {payload['compared_candidates']}")
        print(f"cost_vector_refs: {payload['cost_vector_refs']}")
        print(f"unknown_missing_dimensions: {payload['unknown_missing_dimensions']}")
        print(f"warnings: {payload['warnings']}")
        print(f"blocked_reasons: {payload['blocked_reasons']}")
        if args.show_dimensions:
            print(f"dimensions: {payload.get('dimensions', {})}")
        if args.show_comparison:
            print(f"comparison: {payload.get('comparison', {})}")
        if args.show_mismatch:
            print(f"mismatch: {payload.get('mismatch', ())}")
        if args.show_throughput:
            print(f"throughput: {payload.get('throughput', {})}")
        if args.show_authority:
            print(f"authority: {payload.get('authority', {})}")
        if args.show_counters:
            print(f"counters: {payload.get('counters', {})}")
        print("action/AP01/world/value/fact/cause/recipe/skill/automation: False/False/False/False/False/False/False/False/False")
        print(f"summary: {summary}")
        return 0

    payload["summary"] = summary
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
