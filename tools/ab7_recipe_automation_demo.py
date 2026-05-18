from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ab7_recipe_automation_probe import (  # noqa: E402
    list_ab7_probe_cases,
    run_ab7_probe_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AB7 Recipe-Automation Abductive Integration demo.")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="p15_candidate_bound_to_ab_frontier")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-frame", action="store_true")
    parser.add_argument("--show-constraints", action="store_true")
    parser.add_argument("--show-bindings", action="store_true")
    parser.add_argument("--show-readiness", action="store_true")
    parser.add_argument("--show-falsifiers", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_frame: bool,
    show_constraints: bool,
    show_bindings: bool,
    show_readiness: bool,
    show_falsifiers: bool,
) -> str:
    lines: list[str] = []
    lines.append("AB7 RECIPE-AUTOMATION INTEGRATION REPORT")
    lines.append(f"tick_ref={payload['tick_ref']}")
    lines.append(
        "telemetry: "
        f"recipe_candidates={payload['telemetry']['recipe_candidate_count']} "
        f"constraints={payload['telemetry']['constraint_count']} "
        f"bindings={payload['telemetry']['binding_count']} "
        f"unsafe_basis={payload['telemetry']['unsafe_basis_count']}"
    )
    frame = payload["frame"]
    if frame is None:
        lines.append("frame=None")
        lines.append(f"reason_codes={payload['reason_codes']}")
    else:
        lines.append(
            f"frame_id={frame['frame_id']} recipe_candidate_refs={frame['recipe_candidate_refs']} "
            f"precursor_candidate_refs={frame['precursor_candidate_refs']}"
        )
        lines.append(
            f"maturity_gate_status={frame['maturity_gate_status']} automation_readiness={frame['automation_readiness']}"
        )
        lines.append(
            f"blocked_reasons={frame['blocked_reasons']} hidden_eval_used={frame['hidden_eval_used']} "
            f"mature_recipe_claimed={frame['mature_recipe_claimed']} automation_claimed={frame['automation_claimed']} "
            f"action_request_emitted={frame['action_request_emitted']} world_submission_emitted={frame['world_submission_emitted']}"
        )
        if show_frame:
            lines.append(f"frame={frame}")
        if show_constraints:
            lines.append(f"constraints={frame['abductive_constraints']}")
        if show_bindings:
            lines.append(f"bindings={frame['bindings']}")
        if show_readiness:
            lines.append(f"readiness={frame['automation_readiness']}")
        if show_falsifiers:
            blocked_reasons = tuple(frame["blocked_reasons"])
            missing_evidence_requirements = tuple(frame["missing_evidence_requirements"])
            missing_evidence_expected = any("missing" in reason for reason in blocked_reasons)
            falsifier_summary = {
                "recipe_candidate_bypasses_ab_frontier": not bool(frame["ab_frontier_refs"]),
                "automation_from_recipe_candidate": bool(frame["automation_claimed"]),
                "mature_recipe_from_ab7": bool(frame["mature_recipe_claimed"]),
                "p13_gate_bypassed": "p13_maturity_gate_refs_required" not in frame["blocked_reasons"] and "p13_credit_refs" not in str(frame),
                "p14_affordance_bypassed": not bool(frame["p14_station_affordance_refs"]),
                "ab5_support_as_recipe_oracle": bool(frame["mature_recipe_claimed"]),
                "ab6_attribution_as_recipe_oracle": bool(frame["mature_recipe_claimed"]),
                "one_trace_to_automation": any(item.get("readiness_status") in {"not_ready"} for item in frame["automation_readiness"]) and len(frame["lived_trace_refs"]) <= 1,
                "active_confounder_ignored": False if "active_confounder_requires_resolution" in frame["blocked_reasons"] else ("confounder" in str(frame["confounder_requirements"])),
                "disconfirming_trace_ignored": False if "disconfirming_trace_present" in frame["blocked_reasons"] else ("disconfirming" in str(frame["disconfirmation_requirements"]) and not frame["blocked_reasons"]),
                "hidden_eval_rule_used": bool(frame["hidden_eval_used"]),
                "scenario_label_recipe_integration": bool(frame["scenario_label_used"]),
                "unresolved_frontier_erased": not bool(frame["bindings"][0]["unresolved_conflicts"]) if frame["bindings"] else True,
                "missing_evidence_erased": missing_evidence_expected and not bool(missing_evidence_requirements),
                "recipe_integration_emits_action_request": bool(frame["action_request_emitted"]),
                "recipe_integration_executes_world": bool(frame["world_submission_emitted"]),
                "AB7_overclaims_automation": bool(frame["automation_claimed"] or frame["mature_recipe_claimed"]),
            }
            lines.append(f"falsifier_summary={falsifier_summary}")
    lines.append(
        "claim boundary: AB7 keeps recipe/precursor candidates as constrained explanatory objects only; "
        "no mature recipe knowledge, no executable automation, no consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_cases:
        for case in list_ab7_probe_cases():
            print(case.case_id)
        return 0

    run = run_ab7_probe_case(args.case)
    payload = asdict(run)

    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_frame=bool(args.show_frame),
                show_constraints=bool(args.show_constraints),
                show_bindings=bool(args.show_bindings),
                show_readiness=bool(args.show_readiness),
                show_falsifiers=bool(args.show_falsifiers),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
