from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.mini_factory_chain import (  # noqa: E402
    list_mini_factory_cases,
    run_mini_factory_chain_ablations,
    run_mini_factory_chain_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P17 mini-factory chain demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="full_chain_verified")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-chain", action="store_true")
    parser.add_argument("--show-steps", action="store_true")
    parser.add_argument("--show-residue", action="store_true")
    parser.add_argument("--show-verification", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    return parser.parse_args()


def _render_report(payload: dict[str, object], *, show_chain: bool, show_steps: bool, show_residue: bool, show_verification: bool, show_falsifiers: bool) -> str:
    lines: list[str] = []
    lines.append("MINI-FACTORY CHAIN REPORT (P17)")
    lines.append(f"scenario_id={payload['scenario_id']}")
    lines.append(f"chain_goal_refs={payload['chain_goal_refs']}")
    lines.append(
        f"chain_complete={payload['completion_assessment']['chain_complete']} "
        f"completion_status={payload['completion_assessment']['completion_status']} "
        f"verified_step_count={payload['completion_assessment']['verified_step_count']} "
        f"required_step_count={payload['completion_assessment']['required_step_count']}"
    )
    lines.append(
        f"ap01_request_refs={payload['ap01_request_refs']} action_effect_refs={payload['action_effect_refs']} "
        f"automation_claimed={payload['completion_assessment']['automation_claimed']} "
        f"mature_factory_skill_claimed={payload['completion_assessment']['mature_factory_skill_claimed']} "
        f"hidden_eval_used={payload['hidden_eval_used']} action_request_emitted={payload['action_request_emitted']} "
        f"world_submission_emitted={payload['world_submission_emitted']}"
    )

    if show_chain:
        lines.append(f"completion_assessment={payload['completion_assessment']}")
        lines.append(f"readiness={payload['readiness']}")
    if show_steps:
        lines.append(f"chain_step_traces={payload['chain_step_traces']}")
    if show_residue:
        lines.append(f"chain_residue_records={payload['chain_residue_records']}")
    if show_verification:
        lines.append(f"intermediate_verification_records={payload['intermediate_verification_records']}")
    if show_falsifiers:
        lines.append(f"falsifier_results={payload['falsifier_results']}")

    lines.append(
        "claim boundary: P17 is bounded per-step chain verification with residue propagation only; "
        "no general automation, no mature factory skill, no consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for item in list_mini_factory_cases():
            print(item.scenario_id)
        return 0

    run = run_mini_factory_chain_case(args.scenario)
    payload = asdict(run)
    payload["ablation_summary"] = [asdict(item) for item in run_mini_factory_chain_ablations()]

    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_chain=bool(args.show_chain),
                show_steps=bool(args.show_steps),
                show_residue=bool(args.show_residue),
                show_verification=bool(args.show_verification),
                show_falsifiers=bool(args.show_falsifiers),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
