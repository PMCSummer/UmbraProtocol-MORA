from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ab6_causal_attribution_probe import (
    list_ab6_probe_cases,
    run_ab6_probe_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AB6 Causal Attribution demo.")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="self_action_correlated_effect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-attribution", action="store_true")
    parser.add_argument("--show-source-refs", action="store_true")
    parser.add_argument("--show-missing-evidence", action="store_true")
    return parser.parse_args()


def _render_report(
    payload: dict[str, object],
    *,
    show_attribution: bool,
    show_source_refs: bool,
    show_missing_evidence: bool,
) -> str:
    lines: list[str] = []
    lines.append("AB6 CAUSAL ATTRIBUTION REPORT")
    lines.append(f"tick_ref={payload['tick_ref']}")
    lines.append(
        "candidate_count="
        f"{payload['telemetry']['candidate_count']} supported={payload['telemetry']['supported_count']} "
        f"blocked={payload['telemetry']['blocked_count']} unresolved={payload['telemetry']['unresolved_count']} "
        f"unsafe_basis={payload['telemetry']['unsafe_basis_count']}"
    )
    frame = payload["frame"]
    if frame is None:
        lines.append("frame=None fact_claimed=False cause_confirmed=False")
        lines.append(f"reason_codes={payload['reason_codes']}")
    else:
        lines.append(
            f"attribution_frame_id={frame['attribution_frame_id']} closure_status={frame['closure_status']} "
            f"supported_attribution_kinds={frame['supported_attribution_kinds']} "
            f"blocked_attribution_kinds={frame['blocked_attribution_kinds']} "
            f"unresolved_attribution_kinds={frame['unresolved_attribution_kinds']} "
            f"mixed_cause_preserved={frame['mixed_cause_preserved']} unknown_preserved={frame['unknown_preserved']} "
            f"fact_claimed={frame['fact_claimed']} cause_confirmed={frame['cause_confirmed']} "
            f"action_request_emitted={frame['action_request_emitted']}"
        )
        if show_source_refs:
            lines.append(f"source_effect_refs={frame['source_effect_refs']}")
            lines.append(f"source_request_refs={frame['source_request_refs']}")
            lines.append(f"source_event_digest_refs={frame['source_event_digest_refs']}")
            lines.append(f"source_frontier_refs={frame['source_frontier_refs']}")
        if show_missing_evidence:
            lines.append(f"missing_evidence={frame['missing_evidence']}")
        if show_attribution:
            for cand in frame["attribution_candidates"]:
                lines.append(
                    f"candidate: attribution_kind={cand['attribution_kind']} support_status={cand['support_status']} "
                    f"confidence={cand['confidence']} missing_evidence={cand['missing_evidence']}"
                )
    lines.append(
        "claim boundary: AB6 provides bounded attribution under uncertainty; no full self-model, no final cause truth, "
        "no consciousness claim."
    )
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_cases:
        for case in list_ab6_probe_cases():
            print(case.case_id)
        return 0

    result = run_ab6_probe_case(args.case)
    payload = asdict(result)
    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_attribution=bool(args.show_attribution),
                show_source_refs=bool(args.show_source_refs),
                show_missing_evidence=bool(args.show_missing_evidence),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
