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
    parser.add_argument(
        "--internal-candidate",
        action="store_true",
        help="Use ACP01 internal candidate producer mode (non-autonomous, basis-gated)",
    )
    parser.add_argument(
        "--drive",
        action="append",
        default=[],
        help="Internal drive kind for ACP01 mode (repeatable, e.g. --drive water_need)",
    )
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
            use_internal_candidate_producer=bool(args.internal_candidate),
            internal_drive_kinds=tuple(args.drive),
            allow_manual_candidate_provider=True,
            reject_multiple_published_requests=True,
        ),
        candidate_provider=provider,
    )
    manual_candidate_input_any = any(step.manual_candidate_input for step in run.steps)
    manual_override_used_any = any(step.manual_override_used for step in run.steps)

    print("EMBODIED SUBJECT BRIDGE DEMO (P3)")
    print(f"scenario={run.scenario_id}")
    print(f"ticks={len(run.steps)}")
    print(f"internal_candidate_mode={args.internal_candidate}")
    print(f"internal_drive_kinds={tuple(args.drive)}")
    print(f"manual_candidate_input={manual_candidate_input_any}")
    print(f"manual_override_used={manual_override_used_any}")
    print(f"subject_tick_used_any={run.subject_tick_used_any}")
    print(f"world_submissions={run.world_submissions_count}")
    print(f"world_effect_count={run.world_effect_count}")
    print(f"autonomous_action_selection={run.autonomous_action_selection}")

    for step in run.steps:
        print(
            f"tick={step.bridge_tick_index} candidate_count={step.ap01_candidate_count} "
            f"published={step.ap01_published_request_count} submitted={step.world_submission_attempted} "
            f"effect={step.world_effect_status} verdict={step.verdict.value} "
            f"candidate_source={step.candidate_source}"
        )

    if args.internal_candidate and provider is not None and not manual_candidate_input_any:
        print("note=manual_provider_ignored_in_internal_mode_default_boundary")

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
