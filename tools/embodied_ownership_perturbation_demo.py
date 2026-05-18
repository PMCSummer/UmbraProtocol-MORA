from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ownership_perturbation import (
    list_ownership_perturbation_scenarios,
    run_ownership_ablation_checks,
    run_ownership_perturbation_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P11 self/world ownership perturbation demo.")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="self_caused_move_effect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-evidence", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_evidence: bool,
    show_falsifiers: bool,
) -> str:
    lines: list[str] = []
    lines.append("OWNERSHIP PERTURBATION REPORT (P11)")
    lines.append(
        f"scenario_id={payload['scenario_id']} perturbation_kind={payload['perturbation_kind']} "
        f"tick_count={payload['tick_count']}"
    )
    lines.append(
        f"observed_effect_refs={payload['effect_refs']} ap01_request_refs={payload['ap01_request_refs']} "
        f"external_event_refs={payload['external_event_refs']}"
    )
    assessment = payload["ownership_assessment"]
    lines.append(
        "ownership_assessment: "
        f"self={assessment['self_cause_status']} world={assessment['world_cause_status']} "
        f"other={assessment['other_cause_status']} mixed={assessment['mixed_cause_status']} "
        f"unknown={assessment['unknown_cause_status']}"
    )
    lines.append(
        "safety: "
        f"fact_claimed={assessment['fact_claimed']} cause_confirmed={assessment['cause_confirmed']} "
        f"self_overclaim={assessment['self_overclaim']} mixed_preserved={assessment['mixed_cause_preserved']} "
        f"unknown_preserved={assessment['unknown_preserved']}"
    )
    lines.append(f"missing_evidence={assessment['missing_evidence']} uncertainty={assessment['uncertainty']}")
    lines.append(f"claim_safe_verdict={payload['claim_safe_verdict']} boundary_violations={payload['boundary_violations']}")
    if show_evidence:
        lines.append(f"event_digest_refs={payload['event_digest_refs']}")
        lines.append(f"hypothesis_seed_refs={payload['hypothesis_seed_refs']}")
        lines.append(f"frontier_refs={payload['frontier_refs']}")
        lines.append("candidate_attributions:")
        for item in assessment["candidate_attributions"]:
            lines.append(
                f"  kind={item['attribution_kind']} confidence={item['confidence']} "
                f"required={item['required_evidence']} present={item['present_evidence']} missing={item['missing_evidence']}"
            )
    if show_falsifiers:
        lines.append("falsifier_summary:")
        for name, fired in sorted(payload["falsifier_results"].items()):
            lines.append(f"  {name}={fired}")
    lines.append(
        "claim boundary: P11 supports bounded ownership distinctions only; no full self-model, "
        "no complete causal attribution, no consciousness/general agency claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for spec in list_ownership_perturbation_scenarios():
            print(spec.scenario_id)
        return 0

    run = run_ownership_perturbation_case(args.scenario)
    payload = asdict(run)
    payload["ablation_summary"] = [asdict(item) for item in run_ownership_ablation_checks()]
    report_text = _render_report(
        payload,
        show_evidence=bool(args.show_evidence),
        show_falsifiers=bool(args.show_falsifiers),
    )
    if args.report or (not args.report and not args.json):
        print(report_text)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
