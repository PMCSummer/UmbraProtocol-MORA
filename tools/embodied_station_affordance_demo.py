from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.station_affordance import (  # noqa: E402
    list_station_affordance_cases,
    run_station_affordance_ablations,
    run_station_affordance_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P14 station affordance proof demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="station_visible_not_usable")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-affordance", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    parser.add_argument("--show-deltas", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_affordance: bool,
    show_falsifiers: bool,
    show_deltas: bool,
) -> str:
    lines: list[str] = []
    lines.append("STATION AFFORDANCE REPORT (P14)")
    lines.append(f"scenario_id={payload['scenario_id']} station_ref={payload['station_ref']}")
    lines.append(
        "affordance: "
        f"proximity_status={payload['proximity_status']} input_status={payload['input_status']} "
        f"blocked_status={payload['blocked_status']} affordance_status={payload['affordance_status']}"
    )
    lines.append(
        "gate status: "
        f"station_use_candidate_status={payload['station_use_candidate_status']} "
        f"ap01_publication_status={payload['ap01_publication_status']} "
        f"world_submission_status={payload['world_submission_status']}"
    )
    lines.append(
        "effect path: "
        f"effect_status={payload['effect_status']} effect_refs={payload['effect_refs']} "
        f"inventory_delta_refs={payload['inventory_delta_refs']} world_delta_refs={payload['world_delta_refs']}"
    )
    lines.append(
        "boundaries: "
        f"mature_schema_created={payload['mature_schema_created']} hidden_recipe_used={payload['hidden_recipe_used']} "
        f"fact_claimed={payload['fact_claimed']} cause_confirmed={payload['cause_confirmed']}"
    )
    if show_affordance:
        lines.append(f"public_station_basis={payload['public_station_basis']}")
    if show_deltas:
        lines.append(f"attempt_record={payload['attempt_record']}")
    if show_falsifiers:
        lines.append(f"falsifiers={payload['falsifier_results']}")
    lines.append(
        "claim boundary: P14 validates bounded station affordance only; "
        "not recipe learning, not automation, not general tool use, not consciousness proof."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for item in list_station_affordance_cases():
            print(item.scenario_id)
        return 0

    run = run_station_affordance_case(args.scenario)
    payload = asdict(run)
    payload["ablation_summary"] = [asdict(item) for item in run_station_affordance_ablations()]

    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_affordance=bool(args.show_affordance),
                show_falsifiers=bool(args.show_falsifiers),
                show_deltas=bool(args.show_deltas),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
