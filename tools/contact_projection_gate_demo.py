from __future__ import annotations

import argparse
import json
from typing import Callable
from dataclasses import asdict

from substrate.contact_projection_gate import (
    ContactProjectionConfig,
    ContactProjectionInput,
    project_contact_frame_to_subject_inputs,
    summarize_projection_result,
)
from substrate.umwelt0_phenomenal_contact import (
    ActionSurfaceDeclaration,
    ContactBuildInput,
    LossinessMarker,
    SourceRef,
    WorldEffectFrame,
    build_phenomenal_contact_frame,
)


def _public_source() -> SourceRef:
    return SourceRef(
        source_id="src:public:1",
        source_kind="provider",
        public=True,
        protected_eval=False,
        scenario_label=False,
        provider_ref="provider:test",
    )


def _protected_source() -> SourceRef:
    return SourceRef(
        source_id="src:protected:1",
        source_kind="eval",
        public=False,
        protected_eval=True,
        scenario_label=False,
        provider_ref="provider:eval",
    )


def _scenario_source() -> SourceRef:
    return SourceRef(
        source_id="src:scenario:1",
        source_kind="scenario",
        public=False,
        protected_eval=False,
        scenario_label=True,
        provider_ref="provider:scenario",
    )


def _build_input(
    *,
    observations: tuple[str, ...],
    effects: tuple[str, ...] = (),
    passive: tuple[str, ...] = (),
    residue: tuple[str, ...] = (),
    uncertainty: tuple[str, ...] = (),
    action_surfaces: tuple[ActionSurfaceDeclaration, ...] = (),
    effect_frames: tuple[WorldEffectFrame, ...] = (),
    source_refs: tuple[SourceRef, ...] = (_public_source(),),
    lossiness_markers: tuple[LossinessMarker, ...] = (),
    requires_lossiness_marker: bool = False,
    protected_eval_present: bool = False,
    scenario_label_present: bool = False,
    worldstate_payload_present: bool = False,
) -> ContactProjectionInput:
    contact = build_phenomenal_contact_frame(
        ContactBuildInput(
            frame_id="demo:frame:1",
            tick_id="tick:demo:1",
            provider_refs=("provider:test",),
            public_observation_refs=observations,
            public_effect_refs=effects,
            passive_event_refs=passive,
            action_surfaces=action_surfaces,
            effect_frames=effect_frames,
            residue_refs=residue,
            uncertainty_refs=uncertainty,
            conflict_refs=(),
            source_refs=source_refs,
            lossiness_markers=lossiness_markers,
            requires_lossiness_marker=requires_lossiness_marker,
            protected_eval_present=protected_eval_present,
            scenario_label_present=scenario_label_present,
            worldstate_payload_present=worldstate_payload_present,
        )
    )
    return ContactProjectionInput(
        projection_id="projection:demo:1",
        contact_result=contact,
        world_effect_frames=effect_frames,
        action_surface_declarations=action_surfaces,
    )


def _case_valid_symbolic_contact() -> ContactProjectionInput:
    return _build_input(
        observations=("resource:ore", "station:forge"),
        effects=("effect:mine:ore",),
        residue=("residue:none",),
    )


def _case_mixed_multichannel_contact() -> ContactProjectionInput:
    return _build_input(
        observations=(
            "resource:ore",
            "knowledge:manual:hint",
            "language:claim:water",
            "sensory:visual:candidate:ore_patch",
            "pressure:hunger",
        ),
        effects=("effect:ambient:1",),
    )


def _case_action_surface_basis() -> ContactProjectionInput:
    surface = ActionSurfaceDeclaration(
        surface_ref="surface:inspect:ore",
        action_kind="inspect",
        source_refs=("src:public:1",),
        target_ref="resource:ore",
    )
    return _build_input(observations=("resource:ore",), action_surfaces=(surface,))


def _case_knowledge_hint_not_truth() -> ContactProjectionInput:
    return _build_input(observations=("knowledge:jei:hint:filter",))


def _case_language_claim_not_truth() -> ContactProjectionInput:
    return _build_input(observations=("language:claim:safe_water",))


def _case_sensory_candidate_not_object_truth() -> ContactProjectionInput:
    return _build_input(observations=("sensory:audio:candidate:pump",))


def _case_request_correlated_effect() -> ContactProjectionInput:
    effect = WorldEffectFrame(
        effect_ref="effect:plate:created",
        effect_kind="resource_transform",
        request_ref="ap01:req:1",
        source_refs=("src:public:1",),
        public_delta_refs=("resource:plate",),
    )
    return _build_input(observations=("resource:ore",), effects=("effect:plate:created",), effect_frames=(effect,))


def _case_passive_event_effect() -> ContactProjectionInput:
    effect = WorldEffectFrame(
        effect_ref="effect:ambient:noise",
        effect_kind="passive_event",
        passive_event_ref="event:ambient:1",
        source_refs=("src:public:1",),
    )
    return _build_input(observations=("system:status:ok",), effects=("effect:ambient:noise",), effect_frames=(effect,))


def _case_hidden_eval_blocked() -> ContactProjectionInput:
    return _build_input(
        observations=("resource:ore",),
        source_refs=(_protected_source(),),
        protected_eval_present=True,
    )


def _case_scenario_label_blocked() -> ContactProjectionInput:
    return _build_input(
        observations=("resource:ore",),
        source_refs=(_scenario_source(),),
        scenario_label_present=True,
    )


def _case_blocked_umwelt0_frame_noop() -> ContactProjectionInput:
    return _build_input(
        observations=("resource:ore",),
        worldstate_payload_present=True,
    )


def _case_oversized_contact_bounded() -> ContactProjectionInput:
    observations = tuple(f"resource:item:{idx}" for idx in range(80))
    return _build_input(observations=observations)


CASES: dict[str, Callable[[], ContactProjectionInput]] = {
    "valid_symbolic_contact": _case_valid_symbolic_contact,
    "mixed_multichannel_contact": _case_mixed_multichannel_contact,
    "action_surface_basis": _case_action_surface_basis,
    "knowledge_hint_not_truth": _case_knowledge_hint_not_truth,
    "language_claim_not_truth": _case_language_claim_not_truth,
    "sensory_candidate_not_object_truth": _case_sensory_candidate_not_object_truth,
    "request_correlated_effect": _case_request_correlated_effect,
    "passive_event_effect": _case_passive_event_effect,
    "hidden_eval_blocked": _case_hidden_eval_blocked,
    "scenario_label_blocked": _case_scenario_label_blocked,
    "blocked_umwelt0_frame_noop": _case_blocked_umwelt0_frame_noop,
    "oversized_contact_bounded": _case_oversized_contact_bounded,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CONTACT-PROJECTION-GATE demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-channels", action="store_true")
    parser.add_argument("--show-basis", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    parser.add_argument("--show-counters", action="store_true")
    parser.add_argument("--show-blocked", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.list_cases:
        for case_id in CASES:
            print(case_id)
        return 0

    if not args.case_id or args.case_id not in CASES:
        print("Specify --case with a valid case id or use --list-cases.")
        return 2

    config = ContactProjectionConfig(max_projected_refs_per_channel=20)
    if args.case_id == "oversized_contact_bounded":
        config = ContactProjectionConfig(max_projected_refs_per_channel=8)

    projected = project_contact_frame_to_subject_inputs(CASES[args.case_id](), config=config)
    summary = summarize_projection_result(projected)
    payload: dict[str, object] = {
        "case_id": args.case_id,
        "projection_status": projected.projection_status,
        "ab_ref_count": projected.counters.projected_ab_ref_count,
        "acp01_basis_count": projected.counters.projected_acp01_basis_count,
        "ap01_lineage_count": projected.counters.projected_ap01_lineage_count,
        "blocked_reasons": projected.blocked_projection_reasons,
        "action_request_emitted": projected.action_request_emitted,
        "world_submission_emitted": projected.world_submission_emitted,
        "fact_claimed": projected.fact_claimed,
        "cause_confirmed": projected.cause_confirmed,
        "mature_recipe_claimed": projected.mature_recipe_claimed,
        "value_assigned": projected.value_assigned,
        "mature_skill_claimed": projected.mature_skill_claimed,
        "automation_claimed": projected.automation_claimed,
        "hidden_eval_used": projected.hidden_eval_used,
        "scenario_label_used": projected.scenario_label_used,
        "bounded_claim": "CONTACT-PROJECTION-GATE projects safe public contact refs into AB/ACP/AP lineage surfaces; it does not select actions or execute the world.",
    }
    if args.show_channels:
        payload["channels"] = projected.projected_ab_input.channel_refs
    if args.show_basis:
        payload["ab_basis"] = projected.projected_ab_input.public_basis_refs
        payload["acp01_basis"] = projected.projected_acp01_basis.public_basis_refs
        payload["ap01_lineage_basis"] = projected.projected_ap01_lineage.public_basis_refs
    if args.show_authority:
        payload["authority_flags"] = asdict(projected.authority_flags)
    if args.show_counters:
        payload["counters"] = asdict(projected.counters)
    if args.show_blocked:
        payload["blocked_projection_reasons"] = projected.blocked_projection_reasons
        payload["ab_blocked"] = projected.projected_ab_input.blocked_reasons
        payload["acp01_blocked"] = projected.projected_acp01_basis.blocked_reasons
        payload["ap01_lineage_blocked"] = projected.projected_ap01_lineage.blocked_reasons

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.report:
        print(f"case_id: {args.case_id}")
        print(f"projection_status: {projected.projection_status}")
        print(f"ab_ref_count: {projected.counters.projected_ab_ref_count}")
        print(f"acp01_basis_count: {projected.counters.projected_acp01_basis_count}")
        print(f"ap01_lineage_count: {projected.counters.projected_ap01_lineage_count}")
        print(f"blocked_reasons: {projected.blocked_projection_reasons}")
        print(f"authority: {asdict(projected.authority_flags)}")
        if args.show_channels:
            print(f"channels: {projected.projected_ab_input.channel_refs}")
        if args.show_basis:
            print(f"ab_basis: {projected.projected_ab_input.public_basis_refs}")
            print(f"acp01_basis: {projected.projected_acp01_basis.public_basis_refs}")
            print(f"ap01_lineage_basis: {projected.projected_ap01_lineage.public_basis_refs}")
        if args.show_counters:
            print(f"counters: {asdict(projected.counters)}")
        if args.show_blocked:
            print(f"ab_blocked: {projected.projected_ab_input.blocked_reasons}")
            print(f"acp01_blocked: {projected.projected_acp01_basis.blocked_reasons}")
            print(f"ap01_lineage_blocked: {projected.projected_ap01_lineage.blocked_reasons}")
        print(f"action/world emission: {projected.action_request_emitted}/{projected.world_submission_emitted}")
        print(f"claims fact/cause/value/recipe/skill/automation: {projected.fact_claimed}/{projected.cause_confirmed}/{projected.value_assigned}/{projected.mature_recipe_claimed}/{projected.mature_skill_claimed}/{projected.automation_claimed}")
        print(f"summary: {summary}")
        return 0

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
