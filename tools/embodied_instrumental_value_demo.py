from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.instrumental_value import (  # noqa: E402
    list_instrumental_value_cases,
    run_instrumental_value_ablations,
    run_instrumental_value_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P16 instrumental value demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="resource_with_need_and_recipe_chain")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-value", action="store_true")
    parser.add_argument("--show-chains", action="store_true")
    parser.add_argument("--show-readiness", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_value: bool,
    show_chains: bool,
    show_readiness: bool,
    show_falsifiers: bool,
) -> str:
    lines: list[str] = []
    lines.append("INSTRUMENTAL VALUE REPORT (P16)")
    lines.append(f"scenario_id={payload['scenario_id']}")
    lines.append(f"resource_refs={payload['resource_refs']} need_refs={payload['public_need_refs']}")
    lines.append(
        "readiness: "
        f"candidates={payload['value_readiness_assessment']['value_candidate_count']} "
        f"weak={payload['value_readiness_assessment']['weak_value_count']} "
        f"provisional={payload['value_readiness_assessment']['provisional_value_count']} "
        f"blocked={payload['value_readiness_assessment']['blocked_value_count']} "
        f"disconfirmed={payload['value_readiness_assessment']['disconfirmed_value_count']}"
    )
    lines.append(
        f"blocked_reasons={payload['blocked_reasons']} intrinsic_value_claimed={payload['intrinsic_value_claimed']} "
        f"mature_automation_claimed={payload['mature_automation_claimed']} action_request_emitted={payload['action_request_emitted']} "
        f"world_submission_emitted={payload['world_submission_emitted']} hidden_eval_used={payload['hidden_eval_used']}"
    )

    if show_value:
        lines.append(f"instrumental_value_frames={payload['instrumental_value_frames']}")
    if show_chains:
        lines.append(f"value_chains={payload['value_chains']}")
        lines.append(f"means_candidates={payload['means_candidates']}")
    if show_readiness:
        lines.append(f"value_readiness_assessment={payload['value_readiness_assessment']}")
    if show_falsifiers:
        lines.append(f"falsifier_results={payload['falsifier_results']}")

    lines.append(
        "claim boundary: P16 assigns bounded instrumental means-value only; "
        "no intrinsic value learning, no automation execution, no consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for item in list_instrumental_value_cases():
            print(item.scenario_id)
        return 0

    run = run_instrumental_value_case(args.scenario)
    payload = asdict(run)
    payload["ablation_summary"] = [asdict(item) for item in run_instrumental_value_ablations()]

    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_value=bool(args.show_value),
                show_chains=bool(args.show_chains),
                show_readiness=bool(args.show_readiness),
                show_falsifiers=bool(args.show_falsifiers),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
