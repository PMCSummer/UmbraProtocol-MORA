from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ab3_hypothesis_frontier_probe import (
    list_ab3_probe_cases,
    run_ab3_probe_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AB3 Hypothesis Frontier demo.")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="blocked_movement_effect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-frontier", action="store_true")
    parser.add_argument("--show-source-refs", action="store_true")
    parser.add_argument("--show-conflicts", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_frontier: bool,
    show_source_refs: bool,
    show_conflicts: bool,
) -> str:
    lines: list[str] = []
    lines.append("AB3 HYPOTHESIS FRONTIER REPORT")
    lines.append(f"tick_ref={payload['tick_ref']}")
    lines.append(
        "hypothesis_count="
        f"{payload['telemetry']['hypothesis_count']} unresolved_conflicts={payload['telemetry']['unresolved_conflict_count']} "
        f"missing_evidence={payload['telemetry']['missing_evidence_count']} unsafe_basis={payload['telemetry']['unsafe_basis_count']}"
    )
    frontier = payload["frontier"]
    if frontier is None:
        lines.append("frontier=None closure_status=blocked fact_claimed=False")
    else:
        lines.append(
            f"frontier_id={frontier['frontier_id']} hypothesis_count={len(frontier['hypotheses'])} "
            f"leader_hypothesis_id={frontier['leader_hypothesis_id']} closure_status={frontier['closure_status']} "
            f"fact_claimed={frontier['fact_claimed']} selected_fact_hypothesis_id={frontier['selected_fact_hypothesis_id']} "
            f"cause_confirmed={frontier['cause_confirmed']}"
        )
        lines.append(f"confidence_distribution={frontier['confidence_distribution']}")
        lines.append(f"discriminating_tests={frontier['discriminating_tests']}")
        lines.append(f"missing_evidence={frontier['missing_evidence']}")
        if show_conflicts:
            lines.append(f"unresolved_conflicts={frontier['unresolved_conflicts']}")
        if show_source_refs:
            lines.append(f"source_seed_set_refs={frontier['source_seed_set_refs']}")
            lines.append(f"source_event_refs={frontier['source_event_refs']}")
            lines.append(f"source_residue_refs={frontier['source_residue_refs']}")
            lines.append(f"source_effect_refs={frontier['source_effect_refs']}")
        if show_frontier:
            for item in frontier["hypotheses"]:
                lines.append(
                    f"hypothesis_id={item['hypothesis_id']} kind={item['hypothesis_kind']} "
                    f"bucket={item['support_bucket']} support_score={item['support_score']} "
                    f"confidence={item['confidence']} fact_status={item['fact_status']} cause_confirmed={item['cause_confirmed']}"
                )
    lines.append("claim boundary: AB3 maintains bounded frontier only; no fact/cause closure, no AP01 request, no full abduction/consciousness claim.")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_cases:
        for case in list_ab3_probe_cases():
            print(case.case_id)
        return 0

    result = run_ab3_probe_case(args.case)
    payload = asdict(result)
    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_frontier=bool(args.show_frontier),
                show_source_refs=bool(args.show_source_refs),
                show_conflicts=bool(args.show_conflicts),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
