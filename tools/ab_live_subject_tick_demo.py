from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from substrate.ab01_event_digest import AB1EventDigestInput, build_ab1_event_digests  # noqa: E402
from substrate.ab02_hypothesis_seed import AB2HypothesisSeedInput, build_ab2_hypothesis_seeds  # noqa: E402
from substrate.ab03_hypothesis_frontier import AB3FrontierInput, build_ab3_hypothesis_frontier  # noqa: E402
from substrate.ab_subject_tick_integration import (  # noqa: E402
    ABLiveTickConfig,
    ABLiveTickInput,
    run_ab_live_subject_tick_contour,
)


def _frontier():
    ab1 = build_ab1_event_digests(
        AB1EventDigestInput(
            tick_ref="ab-int:demo:ab1",
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            raw_window_refs=("obs:1",),
            effect_refs=("effect:1",),
            residue_refs=("residue:1",),
            expected_refs=("expected:1",),
            observed_refs=("observed:1",),
            anomaly_markers=("uncertain:1",),
            effect_status="blocked",
            magnitude=0.6,
            noise_level=0.1,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tools.ab_int",
        )
    )
    ab2 = build_ab2_hypothesis_seeds(
        AB2HypothesisSeedInput(
            tick_ref="ab-int:demo:ab2",
            event_digests=ab1.digests,
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tools.ab_int",
        )
    )
    ab3 = build_ab3_hypothesis_frontier(
        AB3FrontierInput(
            tick_ref="ab-int:demo:ab3",
            seed_set=ab2.seed_set,
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            disconfirming_evidence_refs=("conflict:1",),
            ambiguous_evidence=True,
            require_competing_hypotheses=True,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tools.ab_int",
        )
    )
    return ab3.frontier


def _case_input(case_id: str) -> tuple[ABLiveTickInput, ABLiveTickConfig]:
    frontier = _frontier()
    base = ABLiveTickInput(
        tick_id=f"ab-int:demo:{case_id}",
        public_observation_refs=("obs:1",),
        public_effect_refs=("effect:1",),
        residue_refs=("residue:1",),
        uncertainty_refs=("uncertain:1",),
        conflict_refs=(),
        ap01_request_refs=(),
        action_effect_refs=(),
        prior_frontier_refs=(),
        prior_ab_state_refs=(),
        recipe_candidate_refs=(),
        precursor_candidate_refs=(),
        value_chain_refs=(),
        factory_chain_refs=(),
        protected_eval_present=False,
        scenario_label_present=False,
    )
    cfg = ABLiveTickConfig(enable_ab_live_contour=True)

    if case_id == "public_effect_mismatch_creates_digest_seed_frontier":
        return base, cfg
    if case_id == "prior_frontier_correlated_effect_updates_support":
        return (
            ABLiveTickInput(
                **{**asdict(base), "prior_frontier_refs": (frontier.frontier_id,), "prior_frontier_object": frontier, "ap01_request_refs": ("ap01:req:1",), "action_effect_refs": ("action_effect:1",)}
            ),
            cfg,
        )
    if case_id == "ap01_effect_creates_bounded_attribution":
        return (
            ABLiveTickInput(
                **{**asdict(base), "prior_frontier_refs": (frontier.frontier_id,), "prior_frontier_object": frontier, "ap01_request_refs": ("ap01:req:1",), "action_effect_refs": ("action_effect:1",)}
            ),
            cfg,
        )
    if case_id == "open_frontier_creates_epistemic_basis_before_acp01":
        return (
            ABLiveTickInput(
                **{**asdict(base), "prior_frontier_refs": (frontier.frontier_id,), "prior_frontier_object": frontier, "conflict_refs": ("conflict:1",)}
            ),
            cfg,
        )
    if case_id == "recipe_candidate_creates_ab7_constraints":
        return (
            ABLiveTickInput(
                **{
                    **asdict(base),
                    "prior_frontier_refs": (frontier.frontier_id,),
                    "prior_frontier_object": frontier,
                    "ap01_request_refs": ("ap01:req:1",),
                    "action_effect_refs": ("action_effect:1",),
                    "recipe_candidate_refs": ("recipe_candidate:r1",),
                    "precursor_candidate_refs": ("precursor:p1",),
                    "value_chain_refs": ("value_chain:1",),
                    "p13_credit_refs": ("p13:credit:1",),
                    "p14_station_affordance_refs": ("p14:affordance:1",),
                }
            ),
            cfg,
        )
    if case_id == "protected_eval_input_blocked":
        return ABLiveTickInput(**{**asdict(base), "protected_eval_present": True}), cfg
    if case_id == "scenario_label_blocked":
        return ABLiveTickInput(**{**asdict(base), "scenario_label_present": True}), cfg
    if case_id == "disabled_ab_live_preserves_subject_tick_behavior":
        return base, ABLiveTickConfig(enable_ab_live_contour=False)
    if case_id == "repeated_ticks_without_new_evidence":
        return (
            ABLiveTickInput(
                **{
                    **asdict(base),
                    "public_observation_refs": (),
                    "public_effect_refs": (),
                    "residue_refs": (),
                    "uncertainty_refs": (),
                    "conflict_refs": (),
                }
            ),
            cfg,
        )
    raise ValueError(f"unknown case: {case_id}")


def _cases() -> tuple[str, ...]:
    return (
        "public_effect_mismatch_creates_digest_seed_frontier",
        "prior_frontier_correlated_effect_updates_support",
        "ap01_effect_creates_bounded_attribution",
        "open_frontier_creates_epistemic_basis_before_acp01",
        "recipe_candidate_creates_ab7_constraints",
        "protected_eval_input_blocked",
        "scenario_label_blocked",
        "disabled_ab_live_preserves_subject_tick_behavior",
        "repeated_ticks_without_new_evidence",
    )


def _falsifier_summary(payload: dict[str, object]) -> dict[str, bool]:
    traces = payload["stage_traces"]
    ran_any = any(item["ran"] for item in traces)
    return {
        "ab_live_tick_claims_fact": bool(payload["fact_claimed"]),
        "AB4_bypasses_ACP01": bool(payload["action_request_emitted"]),
        "AB5_effect_as_truth_oracle": bool(payload["cause_confirmed"]),
        "AB7_recipe_candidate_as_skill": bool(payload["automation_claimed"] or payload["mature_recipe_claimed"]),
        "hidden_eval_in_tick": bool(payload["hidden_eval_used"]),
        "scenario_label_in_tick": bool(payload["scenario_label_used"]),
        "AB_live_emits_action_request": bool(payload["action_request_emitted"]),
        "AB_live_world_submission": bool(payload["world_submission_emitted"]),
        "AB_live_ignores_public_basis_refs": ran_any and not bool(payload["public_basis_refs"]),
    }


def _report(case_id: str, ticks: int, payload: dict[str, object], *, show_stages: bool, show_counters: bool, show_epistemic_basis: bool, show_authority: bool) -> str:
    lines: list[str] = []
    lines.append("AB LIVE SUBJECT_TICK CONTOUR REPORT")
    lines.append(f"case_id={case_id}")
    lines.append(f"tick_count={ticks}")
    lines.append(
        f"ab1={len(payload['ab1_event_digest_refs'])} ab2={len(payload['ab2_seed_set_refs'])} "
        f"ab3={len(payload['ab3_frontier_refs'])} ab4={len(payload['ab4_epistemic_basis_refs'])} "
        f"ab5={len(payload['ab5_update_refs'])} ab6={len(payload['ab6_attribution_refs'])} ab7={len(payload['ab7_constraint_refs'])}"
    )
    if show_stages:
        lines.append(f"stage_traces={payload['stage_traces']}")
    if show_counters:
        lines.append(f"counters={payload['ab_live_counters']}")
    if show_epistemic_basis:
        lines.append(f"epistemic_basis_refs={payload['ab4_epistemic_basis_refs']}")
    if show_authority:
        lines.append(
            f"fact_claimed={payload['fact_claimed']} cause_confirmed={payload['cause_confirmed']} "
            f"action_request_emitted={payload['action_request_emitted']} world_submission_emitted={payload['world_submission_emitted']} "
            f"automation_claimed={payload['automation_claimed']} mature_recipe_claimed={payload['mature_recipe_claimed']} "
            f"hidden_eval_used={payload['hidden_eval_used']} scenario_label_used={payload['scenario_label_used']}"
        )
    lines.append(f"falsifier_summary={_falsifier_summary(payload)}")
    lines.append(
        "claim boundary: AB live contour emits bounded explanatory/epistemic/attribution/constraint artifacts only; "
        "no fact closure, no AP01 publication authority, no world execution authority, no mature automation claim."
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="AB live subject_tick contour demo")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="public_effect_mismatch_creates_digest_seed_frontier")
    parser.add_argument("--ticks", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-stages", action="store_true")
    parser.add_argument("--show-counters", action="store_true")
    parser.add_argument("--show-epistemic-basis", action="store_true")
    parser.add_argument("--show-authority", action="store_true")
    args = parser.parse_args()

    if args.list_cases:
        for case in _cases():
            print(case)
        return 0

    if args.case not in _cases():
        raise SystemExit(f"unknown case: {args.case}")

    run_payload = None
    for idx in range(max(1, args.ticks)):
        candidate_input, cfg = _case_input(args.case)
        if args.ticks > 1:
            candidate_input = ABLiveTickInput(**{**asdict(candidate_input), "tick_id": f"{candidate_input.tick_id}:{idx + 1}"})
        run = run_ab_live_subject_tick_contour(candidate_input, cfg)
        run_payload = asdict(run)

    assert run_payload is not None
    if args.report or (not args.report and not args.json):
        print(
            _report(
                args.case,
                max(1, args.ticks),
                run_payload,
                show_stages=bool(args.show_stages),
                show_counters=bool(args.show_counters),
                show_epistemic_basis=bool(args.show_epistemic_basis),
                show_authority=bool(args.show_authority),
            )
        )
    if args.json:
        print(json.dumps(run_payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
