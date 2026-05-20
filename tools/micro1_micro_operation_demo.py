from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Callable

from substrate.micro1_micro_operation_frame import (
    MicroOperationGraphInput,
    MicroOperationInput,
    build_micro_operation_frame,
    build_micro_operation_graph,
    summarize_micro_operation_conformance,
)
from substrate.micro1_micro_operation_frame.fixtures import (
    ap01_lineage_reference_fixture,
    bounded_graph_fixture,
    effect_without_request_unresolved_fixture,
    failed_operation_residue_fixture,
    hidden_precondition_rejected_fixture,
    inspect_unknown_resource_fixture,
    macro_factory_action_blocked_fixture,
    move_toward_resource_fixture,
    provider_hint_basis_fixture,
    repair_check_fixture,
    store_resource_fixture,
    use_station_candidate_fixture,
)


def _case_inspect_unknown_resource() -> MicroOperationInput:
    return inspect_unknown_resource_fixture()


def _case_move_toward_resource() -> MicroOperationInput:
    return move_toward_resource_fixture()


def _case_use_station_candidate() -> MicroOperationInput:
    return use_station_candidate_fixture()


def _case_store_resource() -> MicroOperationInput:
    return store_resource_fixture()


def _case_repair_check() -> MicroOperationInput:
    return repair_check_fixture()


def _case_provider_hint_basis() -> MicroOperationInput:
    return provider_hint_basis_fixture()


def _case_quest_permission_blocked() -> MicroOperationInput:
    return quest_objective_blocked_fixture()


def _case_macro_factory_action_blocked() -> MicroOperationInput:
    return macro_factory_action_blocked_fixture()


def _case_ap01_lineage_reference() -> MicroOperationInput:
    return ap01_lineage_reference_fixture()


def _case_failed_operation_residue() -> MicroOperationInput:
    return failed_operation_residue_fixture()


def _case_effect_without_request_unresolved() -> MicroOperationInput:
    return effect_without_request_unresolved_fixture()


def _case_success_requires_effect() -> MicroOperationInput:
    src = inspect_unknown_resource_fixture()
    return MicroOperationInput(
        operation_id="micro1:success_without_effect",
        operation_kind=src.operation_kind,
        basis=src.basis,
        target_affordance_refs=src.target_affordance_refs,
        action_surface_refs=src.action_surface_refs,
        constraints=src.constraints,
        expected_effects=src.expected_effects,
        lineage=src.lineage,
        status_hint=src.status_hint.SUCCEEDED,
    )


def _case_hidden_precondition_rejected() -> MicroOperationInput:
    return hidden_precondition_rejected_fixture()


def _case_bounded_operation_graph() -> MicroOperationGraphInput:
    return bounded_graph_fixture()


OP_CASES: dict[str, Callable[[], MicroOperationInput]] = {
    "inspect_unknown_resource": _case_inspect_unknown_resource,
    "move_toward_resource": _case_move_toward_resource,
    "use_station_candidate": _case_use_station_candidate,
    "store_resource": _case_store_resource,
    "repair_check": _case_repair_check,
    "provider_hint_basis": _case_provider_hint_basis,
    "quest_permission_blocked": _case_quest_permission_blocked,
    "macro_factory_action_blocked": _case_macro_factory_action_blocked,
    "ap01_lineage_reference": _case_ap01_lineage_reference,
    "failed_operation_residue": _case_failed_operation_residue,
    "effect_without_request_unresolved": _case_effect_without_request_unresolved,
    "success_requires_effect": _case_success_requires_effect,
    "hidden_precondition_rejected": _case_hidden_precondition_rejected,
}

GRAPH_CASES: dict[str, Callable[[], MicroOperationGraphInput]] = {
    "bounded_operation_graph": _case_bounded_operation_graph,
}

CASES: tuple[str, ...] = tuple((*OP_CASES.keys(), *GRAPH_CASES.keys()))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MICRO1 micro-operation demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-basis", action="store_true")
    parser.add_argument("--show-lineage", action="store_true")
    parser.add_argument("--show-residue", action="store_true")
    parser.add_argument("--show-graph", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    parser.add_argument("--show-blocked", action="store_true")
    parser.add_argument("--show-counters", action="store_true")
    return parser


def _build_payload(case_id: str) -> dict[str, object]:
    if case_id in OP_CASES:
        result = build_micro_operation_frame(OP_CASES[case_id]())
    else:
        result = build_micro_operation_graph(GRAPH_CASES[case_id]())

    summary = summarize_micro_operation_conformance(result)
    operation = result.operation
    graph = result.graph
    lineage = operation.lineage if operation is not None else None

    payload: dict[str, object] = {
        "case_id": case_id,
        "validation_status": result.status.value,
        "operation_status": result.operation_status.value if result.operation_status is not None else None,
        "operation_kind": operation.operation_kind.value if operation is not None else None,
        "basis_refs": operation.basis.pressure_refs if operation is not None else (),
        "target_affordance_refs": operation.target_affordance_refs if operation is not None else (),
        "action_surface_refs": operation.action_surface_refs if operation is not None else (),
        "expected_effect_refs": operation.expected_effects.expected_effect_refs if operation is not None else (),
        "ap01_lineage_refs": (lineage.ap01_request_ref,) if lineage and lineage.ap01_request_ref else (),
        "observed_effect_refs": lineage.observed_effect_refs if lineage is not None else (),
        "residue_next_pressure_refs": lineage.next_pressure_refs if lineage is not None else (),
        "blocked_reasons": tuple(reason.value for reason in result.blocked_reasons),
        "authority_flags": asdict(result.authority_flags),
        "action_request_emitted": False,
        "world_submission_emitted": False,
        "action_selected": False,
        "fact_claimed": False,
        "cause_confirmed": False,
        "value_assigned": False,
        "mature_recipe_claimed": False,
        "mature_skill_claimed": False,
        "automation_claimed": False,
        "bounded_claim": "MICRO1 validates bounded public-basis micro-operations and lineage only; it does not select actions, publish AP01, or execute the world.",
        "summary": summary,
    }
    if graph is not None:
        payload["graph_status"] = graph.graph_status.value
        payload["graph_operation_refs"] = graph.operation_refs
        payload["graph_blocked_edges"] = graph.blocked_edges
    return payload


def main() -> int:
    args = _parser().parse_args()
    if args.list_cases:
        for case_id in CASES:
            print(case_id)
        return 0

    if not args.case_id or args.case_id not in CASES:
        print("Specify --case with a valid id, or use --list-cases.")
        return 2

    payload = _build_payload(args.case_id)
    summary = payload.pop("summary")

    if not args.show_basis:
        payload.pop("basis_refs", None)
    if not args.show_lineage:
        payload.pop("ap01_lineage_refs", None)
        payload.pop("observed_effect_refs", None)
    if not args.show_residue:
        payload.pop("residue_next_pressure_refs", None)
    if not args.show_graph:
        payload.pop("graph_status", None)
        payload.pop("graph_operation_refs", None)
        payload.pop("graph_blocked_edges", None)
    if not args.show_authority:
        payload.pop("authority_flags", None)
    if not args.show_blocked:
        payload.pop("blocked_reasons", None)
    if not args.show_counters and isinstance(summary, dict):
        summary.pop("counters", None)

    if args.json:
        payload["summary"] = summary
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.report:
        print(f"case_id: {payload['case_id']}")
        print(f"validation_status: {payload['validation_status']}")
        print(f"operation_status: {payload['operation_status']}")
        print(f"operation_kind: {payload['operation_kind']}")
        if args.show_basis:
            print(f"basis_refs: {payload.get('basis_refs', ())}")
        print(f"target_affordance_refs: {payload['target_affordance_refs']}")
        print(f"action_surface_refs: {payload['action_surface_refs']}")
        print(f"expected_effect_refs: {payload['expected_effect_refs']}")
        if args.show_lineage:
            print(f"ap01_lineage_refs: {payload.get('ap01_lineage_refs', ())}")
            print(f"observed_effect_refs: {payload.get('observed_effect_refs', ())}")
        if args.show_residue:
            print(f"residue_next_pressure_refs: {payload.get('residue_next_pressure_refs', ())}")
        if args.show_graph:
            print(f"graph_status: {payload.get('graph_status')}")
            print(f"graph_operation_refs: {payload.get('graph_operation_refs', ())}")
            print(f"graph_blocked_edges: {payload.get('graph_blocked_edges', ())}")
        if args.show_blocked:
            print(f"blocked_reasons: {payload.get('blocked_reasons', ())}")
        if args.show_authority:
            print(f"authority_flags: {payload.get('authority_flags', {})}")
        print("action/world emission: False/False")
        print("claims fact/cause/value/recipe/skill/automation: False/False/False/False/False/False")
        print(f"summary: {summary}")
        return 0

    payload["summary"] = summary
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
