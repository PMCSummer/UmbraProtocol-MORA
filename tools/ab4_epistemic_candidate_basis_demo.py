from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ab4_epistemic_candidate_basis_probe import (
    list_ab4_probe_cases,
    run_ab4_probe_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AB4 epistemic candidate basis demo.")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="open_frontier_inspect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-basis", action="store_true")
    parser.add_argument("--show-source-refs", action="store_true")
    parser.add_argument("--route-through-acp01", action="store_true")
    parser.add_argument("--suppress-ap01", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_basis: bool,
    show_source_refs: bool,
) -> str:
    lines: list[str] = []
    lines.append("AB4 EPISTEMIC CANDIDATE BASIS REPORT")
    lines.append(f"case_id={payload['case_id']}")
    result = payload["result"]
    lines.append(
        f"frontier_ref={result['frontier_ref']} basis_count={result['telemetry']['basis_count']} "
        f"unsafe_basis_count={result['telemetry']['unsafe_basis_count']} no_basis_count={result['telemetry']['no_basis_count']}"
    )
    if result["bases"]:
        for basis in result["bases"]:
            lines.append(
                "basis: "
                f"basis_id={basis['basis_id']} candidate_kind={basis['candidate_kind']} "
                f"frontier_ref={basis['frontier_ref']} hypothesis_refs={basis['hypothesis_refs']} "
                f"discriminates_between={basis['discriminates_between']} "
                f"expected_information_gain={basis['expected_information_gain']['level']} "
                f"uncertainty_basis_refs={basis['uncertainty_basis_refs']} "
                f"public_basis_refs={basis['public_basis_refs']} "
                f"forbidden_execution={basis['forbidden_execution']} "
                f"no_publication_authority={basis['no_publication_authority']} "
                f"no_world_submission_authority={basis['no_world_submission_authority']} "
                f"action_request_emitted={basis['action_request_emitted']} "
                f"hidden_eval_used={basis['hidden_eval_used']} scenario_label_used={basis['scenario_label_used']}"
            )
            if show_basis:
                lines.append(
                    f"  tests={basis['discriminating_test_refs']} missing={basis['missing_evidence_refs']} "
                    f"allowed_action_kinds={basis['allowed_action_kinds']}"
                )
            if show_source_refs:
                lines.append(f"  source_refs={basis['public_basis_refs']}")
    else:
        lines.append(f"reason_codes={result['reason_codes']}")
    lines.append(
        "routing: "
        f"route_supported={payload['route_supported']} "
        f"routed_ap01_publication_count={payload['routed_ap01_publication_count']} "
        f"routed_world_submission_count={payload['routed_world_submission_count']}"
    )
    lines.append(
        "claim boundary: AB4 emits bounded epistemic basis only; no full active inference, "
        "no fact/cause closure, no consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_cases:
        for case in list_ab4_probe_cases():
            print(case.case_id)
        return 0

    run = run_ab4_probe_case(
        args.case,
        route_through_acp01=bool(args.route_through_acp01),
        suppress_ap01=bool(args.suppress_ap01),
    )
    payload = asdict(run)
    report = _render_report(payload, show_basis=bool(args.show_basis), show_source_refs=bool(args.show_source_refs))
    if args.report or (not args.report and not args.json):
        print(report)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
