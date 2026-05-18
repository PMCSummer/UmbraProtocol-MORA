from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.inner_state_calibration import (  # noqa: E402
    list_inner_state_calibration_cases,
    run_inner_state_calibration_ablation_checks,
    run_inner_state_calibration_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P12 Inner-State Report Calibration demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="clear_self_caused_effect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-hidden-evaluator-summary", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    parser.add_argument("--show-metrics", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_hidden_summary: bool,
    show_falsifiers: bool,
    show_metrics: bool,
) -> str:
    lines: list[str] = []
    lines.append("INNER-STATE CALIBRATION REPORT (P12)")
    lines.append(f"scenario_id={payload['scenario_id']} sealed_condition_id={payload['sealed_condition_id']}")
    report = payload["public_report"]
    lines.append(
        f"public_report: confidence={report['confidence_reported']} uncertainty={report['uncertainty_reported']} "
        f"residue_reported={report['residue_reported']} conflict_reported={report['conflict_reported']} "
        f"closure_status={report['closure_status']} fact_claimed={report['fact_claimed']} cause_confirmed={report['cause_confirmed']}"
    )
    lines.append(
        f"calibration: report_calibration_score={payload['calibration_metrics']['report_calibration_score']} "
        f"hidden_leak_detected={payload['hidden_leak_detected']} claim_safe_verdict={payload['claim_safe_verdict']}"
    )
    if show_metrics:
        metrics = payload["calibration_metrics"]
        lines.append(
            "metrics: uncertainty_alignment="
            f"{metrics['uncertainty_alignment']} residue_preservation_score={metrics['residue_preservation_score']} "
            f"conflict_preservation_score={metrics['conflict_preservation_score']} "
            f"confidence_evidence_alignment={metrics['confidence_evidence_alignment']} "
            f"overconfidence_count={metrics['overconfidence_count']} underconfidence_count={metrics['underconfidence_count']} "
            f"hidden_leak_count={metrics['hidden_leak_count']} forced_closure_count={metrics['forced_closure_count']}"
        )
    if show_hidden_summary:
        lines.append(f"evaluator_hidden_condition_summary={payload['evaluator_hidden_condition_summary']}")
    if show_falsifiers:
        lines.append(f"falsifiers={payload['falsifier_results']}")
    lines.append(
        "claim boundary: P12 is evaluator-side calibration only; no hidden-truth injection into subject report, "
        "no consciousness/full-causality claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for item in list_inner_state_calibration_cases():
            print(item.scenario_id)
        return 0

    run = run_inner_state_calibration_case(args.scenario)
    payload = asdict(run)
    payload["ablation_summary"] = [asdict(item) for item in run_inner_state_calibration_ablation_checks()]
    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_hidden_summary=bool(args.show_hidden_evaluator_summary),
                show_falsifiers=bool(args.show_falsifiers),
                show_metrics=bool(args.show_metrics),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
