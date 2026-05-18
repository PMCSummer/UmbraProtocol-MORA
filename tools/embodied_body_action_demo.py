from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.body_action_falsifiers import run_p10_falsifier_suite
from experiments.embodied_playground.body_action_proof import (
    list_p10_scenarios,
    run_body_action_proof_case,
    run_p10_ablation_checks,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P10 body-action proof demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="internal_move_forward_open")
    parser.add_argument("--ticks", type=int, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--show-effect-feedback", action="store_true")
    return parser.parse_args()


def _render_report(payload: dict[str, object], *, show_effect_feedback: bool) -> str:
    lines: list[str] = []
    lines.append("BODY ACTION PROOF REPORT (P10)")
    lines.append(f"scenario={payload['scenario_id']} world={payload['world_scenario_id']} ticks={payload['ticks']}")
    lines.append(
        "path: "
        f"subject_tick_used={payload['subject_tick_used']} "
        f"acp01_used={payload['acp01_used']} "
        f"manual_provider_used={payload['manual_provider_used']}"
    )
    lines.append(
        "counts: "
        f"ap01_published={payload['ap01_published_count']} "
        f"world_submissions={payload['world_submission_count']} "
        f"effect_feedback_count={payload['effect_feedback_count']}"
    )
    lines.append(
        "repeat-policy: "
        f"policy={payload['repeated_body_action_policy']} "
        f"repeated_publish_expected={payload['repeated_publish_expected']} "
        f"stale_candidate_detected={payload['stale_candidate_detected']}"
    )
    lines.append("steps:")
    for step in payload["step_summaries"]:
        lines.append(
            f"  tick={step['bridge_tick_index']} "
            f"published={step['ap01_published_count']} "
            f"submitted={step['world_submission_count']} "
            f"request_ref={step['ap01_request_ref']} "
            f"envelope_ref={step['envelope_ref']} "
            f"effect_ref={step['world_effect_id']} "
            f"effect_correlated={step['effect_correlated_to_request']} "
            f"effect_status={step['effect_status']} "
            f"body_delta={step['body_delta']} "
            f"inventory_delta={step['inventory_delta']} "
            f"world_delta_public={step['world_delta_public']}"
        )
        if show_effect_feedback:
            lines.append(
                f"    next_tick_previous_effect_refs={step['previous_effect_refs_in_next_tick']}"
            )
    lines.append("claim boundary: P10 body-action proof only, no planning/autonomy/consciousness claim.")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for spec in list_p10_scenarios():
            print(spec.scenario_id)
        return 0

    run = run_body_action_proof_case(
        scenario_id=args.scenario,
        ticks=args.ticks,
        strict_internal_mode=bool(args.strict),
    )
    payload = asdict(run)
    report_text = _render_report(payload, show_effect_feedback=bool(args.show_effect_feedback))
    payload["falsifier_summary"] = run_p10_falsifier_suite(run, report_text=report_text)
    payload["ablation_summary"] = [asdict(item) for item in run_p10_ablation_checks()]

    if args.report or (not args.report and not args.json):
        print(report_text)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
