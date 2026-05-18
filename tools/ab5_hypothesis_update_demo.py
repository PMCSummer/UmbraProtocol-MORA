from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ab5_hypothesis_update_probe import (
    list_ab5_probe_cases,
    run_ab5_probe_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AB5 Hypothesis Update demo.")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="correlated_effect_support_increase")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-update", action="store_true")
    parser.add_argument("--show-source-refs", action="store_true")
    parser.add_argument("--show-deltas", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_update: bool,
    show_source_refs: bool,
    show_deltas: bool,
) -> str:
    lines: list[str] = []
    lines.append("AB5 HYPOTHESIS UPDATE REPORT")
    lines.append(f"tick_ref={payload['tick_ref']}")
    lines.append(
        "support_delta_count="
        f"{payload['telemetry']['support_delta_count']} strengthened={payload['telemetry']['strengthened_count']} "
        f"weakened={payload['telemetry']['weakened_count']} disconfirmed={payload['telemetry']['disconfirmed_count']} "
        f"unresolved={payload['telemetry']['unresolved_count']} unsafe_basis={payload['telemetry']['unsafe_basis_count']}"
    )
    update = payload["update"]
    if update is None:
        lines.append("update=None fact_claimed=False cause_confirmed=False")
        lines.append(f"reason_codes={payload['reason_codes']}")
    else:
        lines.append(
            f"update_id={update['update_id']} prior_frontier_ref={update['prior_frontier_ref']} "
            f"closure_allowed={update['closure_allowed']} closure_blocked_reason={update['closure_blocked_reason']} "
            f"fact_claimed={update['fact_claimed']} cause_confirmed={update['cause_confirmed']} "
            f"action_request_emitted={update['action_request_emitted']}"
        )
        lines.append(f"strengthened_hypothesis_refs={update['strengthened_hypothesis_refs']}")
        lines.append(f"weakened_hypothesis_refs={update['weakened_hypothesis_refs']}")
        lines.append(f"disconfirmed_hypothesis_refs={update['disconfirmed_hypothesis_refs']}")
        lines.append(f"unresolved_hypothesis_refs={update['unresolved_hypothesis_refs']}")
        if show_source_refs:
            lines.append(f"source_effect_refs={update['source_effect_refs']}")
            lines.append(f"source_event_digest_refs={update['source_event_digest_refs']}")
            lines.append(f"source_request_refs={update['source_request_refs']}")
            lines.append(f"epistemic_basis_refs={update['epistemic_basis_refs']}")
        if show_deltas:
            for delta in update["support_deltas"]:
                lines.append(
                    f"delta: hypothesis_ref={delta['hypothesis_ref']} delta_kind={delta['delta_kind']} "
                    f"{delta['previous_support_bucket']}->{delta['new_support_bucket']} confidence_delta={delta['confidence_delta']}"
                )
        if show_update:
            lines.append(f"missing_evidence={update['missing_evidence']}")
            lines.append(f"ambiguous_evidence_refs={update['ambiguous_evidence_refs']}")
    lines.append(
        "claim boundary: AB5 updates bounded support only; no effect truth oracle, no request-as-confirmation, "
        "no final cause/fact closure, no full abduction/consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_cases:
        for case in list_ab5_probe_cases():
            print(case.case_id)
        return 0

    run = run_ab5_probe_case(args.case)
    payload = asdict(run)
    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_update=bool(args.show_update),
                show_source_refs=bool(args.show_source_refs),
                show_deltas=bool(args.show_deltas),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
