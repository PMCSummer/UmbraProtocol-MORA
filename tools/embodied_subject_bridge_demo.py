from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.bridge_trace import SubjectWorldBridgeConfig
from experiments.embodied_playground.candidate_provider import ManualCandidateProvider, ManualCandidateSpec
from experiments.embodied_playground.scenarios import list_grid_world_scenarios
from experiments.embodied_playground.subject_bridge import run_subject_world_bridge


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P3 SubjectWorldBridge demo (observe -> subject_tick -> AP01 -> world effect).")
    parser.add_argument("--list-scenarios", action="store_true", help="List available grid scenarios")
    parser.add_argument("--scenario", default="empty_room_presence", help="Scenario id")
    parser.add_argument("--manual-action", default=None, help="Manual action kind for candidate provider")
    parser.add_argument("--target", default=None, help="Optional target ref for manual action")
    parser.add_argument("--ticks", type=int, default=1, help="Number of bridge ticks")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument("--include-eval-only", action="store_true", help="Include eval-only section in output")
    return parser.parse_args()


def _provider_from_args(args: argparse.Namespace) -> ManualCandidateProvider | None:
    if not args.manual_action:
        return None
    return ManualCandidateProvider(
        plans_by_tick={
            1: (
                ManualCandidateSpec(
                    action_kind=args.manual_action,
                    target_ref=args.target,
                    intended_effect=f"{args.manual_action}_effect",
                ),
            )
        }
    )


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for scenario_id in list_grid_world_scenarios():
            print(scenario_id)
        return 0

    provider = _provider_from_args(args)
    run = run_subject_world_bridge(
        scenario_id=args.scenario,
        config=SubjectWorldBridgeConfig(
            subject_id="subject_a",
            max_ticks=max(1, args.ticks),
            execute_world_actions=True,
            include_eval_only=bool(args.include_eval_only),
            allow_manual_candidate_provider=True,
            reject_multiple_published_requests=True,
        ),
        candidate_provider=provider,
    )

    print("EMBODIED SUBJECT BRIDGE DEMO (P3)")
    print(f"scenario={run.scenario_id}")
    print(f"ticks={len(run.steps)}")
    print(f"manual_candidate_input={provider is not None}")
    print(f"subject_tick_used_any={run.subject_tick_used_any}")
    print(f"world_submissions={run.world_submissions_count}")
    print(f"world_effect_count={run.world_effect_count}")
    print(f"autonomous_action_selection={run.autonomous_action_selection}")

    for step in run.steps:
        print(
            f"tick={step.bridge_tick_index} candidate_count={step.ap01_candidate_count} "
            f"published={step.ap01_published_request_count} submitted={step.world_submission_attempted} "
            f"effect={step.world_effect_status} verdict={step.verdict.value}"
        )

    if args.json:
        payload = {
            "run": asdict(run),
        }
        if not args.include_eval_only and "eval_only" in payload["run"]:
            payload["run"].pop("eval_only", None)
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
