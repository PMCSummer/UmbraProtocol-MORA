from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.recipe_precursor_learning import (  # noqa: E402
    list_recipe_precursor_cases,
    run_recipe_precursor_ablations,
    run_recipe_precursor_learning_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P15 recipe/precursor candidate learning demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="one_success_trace_provisional_only")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-traces", action="store_true")
    parser.add_argument("--show-candidates", action="store_true")
    parser.add_argument("--show-confounders", action="store_true")
    parser.add_argument("--show-maturity", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_traces: bool,
    show_candidates: bool,
    show_confounders: bool,
    show_maturity: bool,
    show_falsifiers: bool,
) -> str:
    lines: list[str] = []
    lines.append("RECIPE/PRECURSOR LEARNING REPORT (P15)")
    lines.append(f"scenario_id={payload['scenario_id']} lived_trace_count={len(payload['lived_trace_records'])}")
    lines.append(
        f"recipe_candidates={len(payload['recipe_candidates'])} precursor_candidates={len(payload['precursor_candidates'])} "
        f"confounders={len(payload['confounder_records'])} disconfirming_records={len(payload['disconfirming_records'])}"
    )
    lines.append(
        "maturity: "
        f"mature_recipe_count={payload['maturity_assessment']['mature_recipe_count']} "
        f"weak={payload['maturity_assessment']['weak_candidate_count']} "
        f"provisional={payload['maturity_assessment']['provisional_candidate_count']} "
        f"repeated_trace_supported={payload['maturity_assessment']['repeated_trace_supported_count']} "
        f"blocked={payload['maturity_assessment']['blocked_candidate_count']}"
    )
    if show_traces:
        for item in payload["lived_trace_records"]:
            lines.append(
                "trace: "
                f"trace_id={item['trace_id']} station_ref={item['public_station_ref']} "
                f"input_refs={item['public_input_refs']} effect_refs={item['public_effect_refs']}"
            )
    if show_candidates:
        for item in payload["precursor_candidates"]:
            lines.append(
                "precursor_candidate: "
                f"id={item['precursor_candidate_id']} support_status={item['support_status']} confidence={item['confidence']}"
            )
        for item in payload["recipe_candidates"]:
            lines.append(
                "recipe_candidate: "
                f"id={item['recipe_candidate_id']} maturity_status={item['maturity_status']} "
                f"maturity_score={item['maturity_score']} hidden_recipe_used={item['hidden_recipe_used']}"
            )
    if show_confounders:
        lines.append(f"confounder_records={payload['confounder_records']}")
    if show_maturity:
        lines.append(f"maturity_assessment={payload['maturity_assessment']}")
    if show_falsifiers:
        lines.append(f"falsifiers={payload['falsifier_results']}")
    lines.append(
        "claim boundary: P15 forms provisional recipe/precursor candidates from lived public traces only; "
        "no mature recipe guarantee, no automation, no consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for item in list_recipe_precursor_cases():
            print(item.scenario_id)
        return 0

    run = run_recipe_precursor_learning_case(args.scenario)
    payload = asdict(run)
    payload["ablation_summary"] = [asdict(item) for item in run_recipe_precursor_ablations()]

    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_traces=bool(args.show_traces),
                show_candidates=bool(args.show_candidates),
                show_confounders=bool(args.show_confounders),
                show_maturity=bool(args.show_maturity),
                show_falsifiers=bool(args.show_falsifiers),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
