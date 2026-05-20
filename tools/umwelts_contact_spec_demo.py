from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from typing import Callable

from substrate.umwelts_symbolic_contact import (
    ContactChannelDeclaration,
    ContactLossinessRequirement,
    ContactSourceRequirement,
    UMWELTSChannelKind,
    UMWELTSRefKind,
    generic_grid_fixture,
    language_sensor_fixture,
    symbolic_factory_fixture,
    validate_contact_spec,
)


def _case_minimal_symbolic_world():
    return generic_grid_fixture()


def _case_generic_grid_fixture():
    return generic_grid_fixture()


def _case_symbolic_factory_fixture():
    return symbolic_factory_fixture()


def _case_mixed_multichannel_spec():
    return language_sensor_fixture()


def _case_knowledge_provider_hint():
    return symbolic_factory_fixture()


def _case_language_contact_testimony():
    return language_sensor_fixture()


def _case_sensory_candidate_channel():
    return language_sensor_fixture()


def _case_selected_action_rejected():
    spec = generic_grid_fixture()
    bad_surface = replace(spec.action_surface_declarations[0], action_kind="selected_action")
    return replace(spec, action_surface_declarations=(bad_surface, *spec.action_surface_declarations[1:]))


def _case_true_recipe_rejected():
    return replace(symbolic_factory_fixture(), metadata={"true_recipe": "ore->plate"})


def _case_full_map_rejected():
    return replace(generic_grid_fixture(), metadata={"full_map": "all"})


def _case_backend_worldstate_rejected():
    return replace(generic_grid_fixture(), metadata={"worldstate": "{raw}"})


def _case_unknown_channel_bounded():
    spec = generic_grid_fixture()
    unknown_channel = ContactChannelDeclaration(
        channel_id="ch:unknown",
        channel_kind=UMWELTSChannelKind.UNKNOWN_PUBLIC,
        public=True,
        requires_source_refs=True,
        requires_lossiness_when_partial=True,
        allows_unknown_refs=True,
        max_refs=4,
    )
    from substrate.umwelts_symbolic_contact import PublicRefDeclaration, ContactUncertaintyRequirement

    unknown_ref = PublicRefDeclaration(
        ref_id="unknown:public:1",
        ref_kind=UMWELTSRefKind.UNCERTAINTY,
        channel_id="ch:unknown",
        source_requirements=ContactSourceRequirement(required=True, source_refs=("src:grid:public",)),
        uncertainty_policy=ContactUncertaintyRequirement(required_when_ambiguous=True, uncertainty_refs=("uncertain:unknown",)),
    )
    return replace(
        spec,
        channel_declarations=(*spec.channel_declarations, unknown_channel),
        public_ref_declarations=(*spec.public_ref_declarations, unknown_ref),
    )


def _case_provider_truth_rejected():
    spec = symbolic_factory_fixture()
    bad_provider = replace(
        spec.provider_declarations[0],
        truth_authority=True,
        hint_only=False,
    )
    return replace(spec, provider_declarations=(bad_provider,))


CASES: dict[str, Callable[[], object]] = {
    "minimal_symbolic_world": _case_minimal_symbolic_world,
    "generic_grid_fixture": _case_generic_grid_fixture,
    "symbolic_factory_fixture": _case_symbolic_factory_fixture,
    "mixed_multichannel_spec": _case_mixed_multichannel_spec,
    "knowledge_provider_hint": _case_knowledge_provider_hint,
    "language_contact_testimony": _case_language_contact_testimony,
    "sensory_candidate_channel": _case_sensory_candidate_channel,
    "selected_action_rejected": _case_selected_action_rejected,
    "true_recipe_rejected": _case_true_recipe_rejected,
    "full_map_rejected": _case_full_map_rejected,
    "backend_worldstate_rejected": _case_backend_worldstate_rejected,
    "unknown_channel_bounded": _case_unknown_channel_bounded,
    "provider_truth_rejected": _case_provider_truth_rejected,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UMWELT-S ContactSpec/IR demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-ir", action="store_true")
    parser.add_argument("--show-channels", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    parser.add_argument("--show-blocked", action="store_true")
    parser.add_argument("--show-conformance", action="store_true")
    return parser


def _build_payload(case_id: str) -> dict[str, object]:
    spec = CASES[case_id]()
    result = validate_contact_spec(spec)  # type: ignore[arg-type]
    payload: dict[str, object] = {
        "case_id": case_id,
        "spec_id": result.spec_id,
        "validation_status": result.status.value,
        "normalized_ir_status": result.normalized_ir.conformance_status.value if result.normalized_ir else None,
        "channel_count": result.counters.channel_count,
        "ref_count": result.counters.ref_count,
        "action_surface_count": result.counters.action_surface_count,
        "effect_surface_count": result.counters.effect_surface_count,
        "provider_count": result.counters.provider_count,
        "blocked_reasons": result.blocked_reasons,
        "authority_flags": asdict(result.authority_flags),
        "umwelt0_conformance": {
            "has_plan": result.umwelt0_construction_plan is not None,
            "plan_id": result.umwelt0_construction_plan.plan_id if result.umwelt0_construction_plan else None,
        },
        "action_request_emitted": result.action_request_emitted,
        "world_action_emitted": result.world_action_emitted,
        "fact_claimed": result.fact_claimed,
        "cause_confirmed": result.cause_confirmed,
        "value_assigned": result.value_assigned,
        "mature_recipe_claimed": result.mature_recipe_claimed,
        "mature_skill_claimed": result.mature_skill_claimed,
        "automation_claimed": result.automation_claimed,
        "bounded_claim": "UMWELT-S validates and normalizes symbolic contact declarations into Contact IR and UMWELT0-compatible construction plans without planner, oracle, or action authority.",
    }
    payload["_result"] = result
    return payload


def main() -> int:
    args = _parser().parse_args()
    if args.list_cases:
        for case_id in CASES:
            print(case_id)
        return 0

    if not args.case_id or args.case_id not in CASES:
        print("Specify --case with a valid case id or use --list-cases.")
        return 2

    payload = _build_payload(args.case_id)
    result = payload.pop("_result")

    if args.show_ir and result.normalized_ir is not None:
        payload["ir"] = {
            "ir_id": result.normalized_ir.ir_id,
            "blocked_items": result.normalized_ir.blocked_items,
            "trace": result.normalized_ir.traces,
        }
    if args.show_channels and result.normalized_ir is not None:
        payload["channels"] = [
            {"channel_id": item.channel_id, "channel_kind": item.channel_kind.value, "max_refs": item.max_refs}
            for item in result.normalized_ir.normalized_channels
        ]
    if args.show_authority:
        payload["authority"] = asdict(result.authority_flags)
    if args.show_blocked:
        payload["blocked"] = result.blocked_reasons
    if args.show_conformance and result.umwelt0_construction_plan is not None:
        payload["conformance"] = {
            "plan_id": result.umwelt0_construction_plan.plan_id,
            "public_observation_refs": result.umwelt0_construction_plan.public_observation_refs,
            "public_effect_refs": result.umwelt0_construction_plan.public_effect_refs,
            "action_surface_refs": result.umwelt0_construction_plan.action_surface_refs,
            "effect_surface_refs": result.umwelt0_construction_plan.effect_surface_refs,
            "source_refs": result.umwelt0_construction_plan.source_refs,
            "lossiness_refs": result.umwelt0_construction_plan.lossiness_refs,
            "blocked_reasons": result.umwelt0_construction_plan.blocked_reasons,
        }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.report:
        print(f"case_id: {payload['case_id']}")
        print(f"spec_id: {payload['spec_id']}")
        print(f"validation_status: {payload['validation_status']}")
        print(f"normalized_ir_status: {payload['normalized_ir_status']}")
        print(f"counts: channels={payload['channel_count']} refs={payload['ref_count']} actions={payload['action_surface_count']} effects={payload['effect_surface_count']} providers={payload['provider_count']}")
        print(f"blocked_reasons: {payload['blocked_reasons']}")
        print(f"authority_flags: {payload['authority_flags']}")
        print(f"umwelt0_conformance: {payload['umwelt0_conformance']}")
        print(f"no_action_emission: {payload['action_request_emitted']} / {payload['world_action_emitted']}")
        print(f"no_claims(fact/cause/value/recipe/skill/automation): {payload['fact_claimed']}/{payload['cause_confirmed']}/{payload['value_assigned']}/{payload['mature_recipe_claimed']}/{payload['mature_skill_claimed']}/{payload['automation_claimed']}")
        if "ir" in payload:
            print(f"ir: {payload['ir']}")
        if "channels" in payload:
            print(f"channels: {payload['channels']}")
        if "conformance" in payload:
            print(f"conformance: {payload['conformance']}")
        print(f"bounded_claim: {payload['bounded_claim']}")
        return 0

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

