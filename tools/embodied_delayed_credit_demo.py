from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.delayed_credit_learning import (  # noqa: E402
    list_delayed_credit_cases,
    run_delayed_credit_ablation_checks,
    run_delayed_credit_learning_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P13 delayed-credit/confounder learning demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="immediate_clear_effect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-credit-links", action="store_true")
    parser.add_argument("--show-confounders", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    parser.add_argument("--show-maturity", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_credit_links: bool,
    show_confounders: bool,
    show_falsifiers: bool,
    show_maturity: bool,
) -> str:
    lines: list[str] = []
    lines.append("DELAYED CREDIT LEARNING REPORT (P13)")
    lines.append(f"scenario_id={payload['scenario_id']} episode_count={len(payload['episode_traces'])}")
    lines.append(
        f"credit_links={len(payload['candidate_credit_links'])} confounder_records={len(payload['confounder_records'])} "
        f"delayed_records={len(payload['delayed_effect_records'])} schema_candidates={len(payload['provisional_schema_candidates'])}"
    )
    lines.append(
        "maturity: "
        f"candidate_count={payload['maturity_assessment']['candidate_count']} "
        f"weak={payload['maturity_assessment']['weak_candidate_count']} "
        f"provisional={payload['maturity_assessment']['provisional_candidate_count']} "
        f"blocked={payload['maturity_assessment']['blocked_candidate_count']} "
        f"mature_schema_count={payload['maturity_assessment']['mature_schema_count']}"
    )
    if show_credit_links:
        for item in payload["candidate_credit_links"]:
            lines.append(
                "credit_link: "
                f"link_id={item['link_id']} correlation_status={item['correlation_status']} "
                f"delay_window={item['delay_window']} maturity_status={item['maturity_status']} confidence={item['confidence']}"
            )
    if show_confounders:
        for item in payload["confounder_records"]:
            lines.append(
                "confounder: "
                f"confounder_id={item['confounder_id']} status={item['status']} "
                f"credit_leak_risk={item['credit_leak_risk']}"
            )
    if show_maturity:
        for item in payload["provisional_schema_candidates"]:
            lines.append(
                "schema: "
                f"schema_candidate_id={item['schema_candidate_id']} maturity_status={item['maturity_status']} "
                f"maturity_score={item['maturity_score']} one_shot_mature={item['one_shot_mature']}"
            )
    if show_falsifiers:
        lines.append(f"falsifiers={payload['falsifier_results']}")
    lines.append(
        "claim boundary: P13 provides provisional delayed-credit/confounder-aware candidates only; "
        "no mature recipe, no true-cause closure, no consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for item in list_delayed_credit_cases():
            print(item.scenario_id)
        return 0

    run = run_delayed_credit_learning_case(args.scenario)
    payload = asdict(run)
    payload["ablation_summary"] = [asdict(item) for item in run_delayed_credit_ablation_checks()]
    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_credit_links=bool(args.show_credit_links),
                show_confounders=bool(args.show_confounders),
                show_falsifiers=bool(args.show_falsifiers),
                show_maturity=bool(args.show_maturity),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
