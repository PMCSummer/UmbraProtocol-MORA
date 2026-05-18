from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ab1_event_digest_probe import (
    list_ab1_probe_cases,
    run_ab1_probe_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AB1 Event Digest demo.")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="blocked_movement_effect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--include-weak", action="store_true")
    parser.add_argument("--show-source-refs", action="store_true")
    return parser.parse_args()


def _render_report(payload: dict[str, object], *, include_weak: bool, show_source_refs: bool) -> str:
    lines: list[str] = []
    lines.append("AB1 EVENT DIGEST REPORT")
    lines.append(f"tick_ref={payload['tick_ref']}")
    lines.append(f"digest_count={payload['telemetry']['digest_count']} unsafe_basis_count={payload['telemetry']['unsafe_basis_count']}")
    for digest in payload["digests"]:
        if not include_weak and digest["weak_status"]:
            continue
        event_kind = digest["event_kind"]
        if hasattr(event_kind, "value"):
            event_kind = event_kind.value
        lines.append(
            f"event_id={digest['event_id']} kind={event_kind} "
            f"confidence={digest['confidence']} uncertainty={digest['uncertainty']} "
            f"lossiness={digest['lossiness']} cause_claimed={digest['cause_claimed']}"
        )
        lines.append(
            f"  explicit_non_causal_closure={digest['explicit_non_causal_closure']} "
            f"hidden_eval_used={digest['hidden_eval_used']} scenario_label_used={digest['scenario_label_used']}"
        )
        lines.append(f"  effect_refs={digest['effect_refs']} residue_refs={digest['residue_refs']}")
        if show_source_refs:
            lines.append(f"  source_refs={digest['source_refs']} observation_refs={digest['observation_refs']}")
    lines.append("claim boundary: AB1 emits anomaly/event digest only, no cause explanation, no hypothesis, no action request.")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_cases:
        for case in list_ab1_probe_cases():
            print(case.case_id)
        return 0

    result = run_ab1_probe_case(args.case)
    payload = asdict(result)
    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                include_weak=bool(args.include_weak),
                show_source_refs=bool(args.show_source_refs),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
