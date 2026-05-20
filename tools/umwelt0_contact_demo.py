from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass, replace
from typing import Any

from substrate.umwelt0_phenomenal_contact import (
    ActionSurfaceDeclaration,
    ContactBuildInput,
    LossinessMarker,
    SourceRef,
    WorldEffectFrame,
    build_phenomenal_contact_frame,
    summarize_contact_conformance,
)


def _source_public() -> SourceRef:
    return SourceRef(
        source_id="src:public:demo",
        source_kind="world_provider",
        public=True,
        protected_eval=False,
        scenario_label=False,
        provider_ref="provider:demo",
    )


def _source_protected() -> SourceRef:
    return SourceRef(
        source_id="src:protected:demo",
        source_kind="eval_fixture",
        public=False,
        protected_eval=True,
        scenario_label=False,
        provider_ref="provider:eval",
    )


def _source_scenario() -> SourceRef:
    return SourceRef(
        source_id="src:scenario:demo",
        source_kind="scenario_label",
        public=False,
        protected_eval=False,
        scenario_label=True,
        provider_ref="provider:scenario",
    )


def _base_input() -> ContactBuildInput:
    return ContactBuildInput(
        frame_id="umwelt0:demo:frame",
        tick_id="demo:tick:1",
        provider_refs=("provider:demo",),
        public_observation_refs=("obs:public:1",),
        public_effect_refs=("effect:public:1",),
        source_refs=(_source_public(),),
        residue_refs=("residue:1",),
    )


def _cases() -> dict[str, ContactBuildInput]:
    base = _base_input()
    return {
        "valid_public_contact": base,
        "missing_source_refs": replace(base, source_refs=()),
        "protected_eval_blocked": replace(
            base,
            source_refs=(_source_protected(),),
            protected_eval_present=True,
        ),
        "scenario_label_blocked": replace(
            base,
            source_refs=(_source_scenario(),),
            scenario_label_present=True,
        ),
        "action_surface_no_authority": replace(
            base,
            action_surfaces=(
                ActionSurfaceDeclaration(
                    surface_ref="surface:inspect",
                    action_kind="inspect",
                    source_refs=("src:public:demo",),
                ),
            ),
        ),
        "action_policy_rejected": replace(
            base,
            action_surfaces=(
                ActionSurfaceDeclaration(
                    surface_ref="surface:route",
                    action_kind="inspect",
                    source_refs=("src:public:demo",),
                    selected_action_ref="ap01:selected:1",
                ),
            ),
        ),
        "request_correlated_effect": replace(
            base,
            effect_frames=(
                WorldEffectFrame(
                    effect_ref="effect:request:1",
                    effect_kind="output_appeared",
                    request_ref="ap01:req:1",
                    source_refs=("src:public:demo",),
                ),
            ),
        ),
        "passive_public_event_effect": replace(
            base,
            effect_frames=(
                WorldEffectFrame(
                    effect_ref="effect:passive:1",
                    effect_kind="ambient_change",
                    passive_event_ref="event:passive:1",
                    source_refs=("src:public:demo",),
                ),
            ),
        ),
        "effect_without_request_or_passive_blocked": replace(
            base,
            effect_frames=(
                WorldEffectFrame(
                    effect_ref="effect:bad:1",
                    effect_kind="output_appeared",
                    source_refs=("src:public:demo",),
                ),
            ),
        ),
        "true_recipe_blocked": replace(base, true_recipe_present=True),
        "full_map_blocked": replace(base, full_map_present=True),
        "lossy_partial_contact": replace(
            base,
            public_observation_refs=("obs:compressed:1",),
            lossiness_markers=(
                LossinessMarker(
                    marker_id="loss:1",
                    kind="compressed",
                    description="compressed provider contact",
                ),
            ),
            uncertainty_refs=("uncertain:partial",),
            requires_lossiness_marker=True,
        ),
        "empty_contact_noop": replace(
            base,
            public_observation_refs=(),
            public_effect_refs=(),
            residue_refs=(),
            uncertainty_refs=(),
            conflict_refs=(),
            action_surfaces=(),
            effect_frames=(),
        ),
    }


def _to_json_ready(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _to_json_ready(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_ready(v) for v in value]
    if hasattr(value, "value"):
        return getattr(value, "value")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UMWELT0 contact membrane demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    parser.add_argument("--show-counters", action="store_true")
    parser.add_argument("--show-blocked", action="store_true")
    args = parser.parse_args(argv)

    cases = _cases()
    if args.list_cases:
        for case_id in sorted(cases):
            print(case_id)
        return 0

    if not args.case:
        parser.error("--case is required unless --list-cases is used")

    if args.case not in cases:
        print(f"unknown case: {args.case}")
        return 1

    result = build_phenomenal_contact_frame(cases[args.case])
    summary = summarize_contact_conformance(result)
    payload = {
        "case_id": args.case,
        "validation_status": result.phenomenal_contact_frame.validation_status.value,
        "accepted_refs": list(result.accepted_refs),
        "blocked_reasons": [item.value for item in result.blocked_reasons],
        "authority_flags": _to_json_ready(result.phenomenal_contact_frame.authority_flags),
        "counters": _to_json_ready(result.counters),
        "hidden_eval_used": result.phenomenal_contact_frame.hidden_eval_used,
        "scenario_label_used": result.phenomenal_contact_frame.scenario_label_used,
        "backend_truth_excluded": result.phenomenal_contact_frame.backend_truth_excluded,
        "action_request_emitted": result.phenomenal_contact_frame.action_request_emitted,
        "world_submission_emitted": result.phenomenal_contact_frame.world_submission_emitted,
        "fact_claimed": result.phenomenal_contact_frame.fact_claimed,
        "cause_confirmed": result.phenomenal_contact_frame.cause_confirmed,
        "mature_recipe_claimed": result.phenomenal_contact_frame.mature_recipe_claimed,
        "automation_claimed": result.phenomenal_contact_frame.automation_claimed,
        "bounded_claim": (
            "UMWELT0 builds source-bound public contact/effect frames with explicit uncertainty/lossiness "
            "and zero action/publication/execution authority."
        ),
        "summary": summary,
    }

    if args.json:
        print(json.dumps(_to_json_ready(payload), indent=2, ensure_ascii=False))
        return 0

    print(f"case_id: {args.case}")
    print(f"validation_status: {payload['validation_status']}")
    print(f"accepted_refs: {len(result.accepted_refs)}")
    if args.show_blocked or args.report:
        print(f"blocked_reasons: {payload['blocked_reasons']}")
    if args.show_authority or args.report:
        print(f"authority_flags: {payload['authority_flags']}")
    if args.show_counters or args.report:
        print(f"counters: {payload['counters']}")
    print(f"hidden_eval_used: {payload['hidden_eval_used']}")
    print(f"scenario_label_used: {payload['scenario_label_used']}")
    print(f"backend_truth_excluded: {payload['backend_truth_excluded']}")
    print(f"action_request_emitted: {payload['action_request_emitted']}")
    print(f"world_submission_emitted: {payload['world_submission_emitted']}")
    print(f"fact_claimed: {payload['fact_claimed']}")
    print(f"cause_confirmed: {payload['cause_confirmed']}")
    print(f"mature_recipe_claimed: {payload['mature_recipe_claimed']}")
    print(f"automation_claimed: {payload['automation_claimed']}")
    print(f"bounded_claim: {payload['bounded_claim']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
