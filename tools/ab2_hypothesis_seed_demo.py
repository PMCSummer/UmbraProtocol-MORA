from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ab2_hypothesis_seed_probe import (
    list_ab2_probe_cases,
    run_ab2_probe_case,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AB2 Hypothesis Seed demo.")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--case", default="blocked_movement_effect")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--show-hypotheses", action="store_true")
    parser.add_argument("--show-source-refs", action="store_true")
    return parser.parse_args()


def _render_report(payload: dict[str, object], *, show_hypotheses: bool, show_source_refs: bool) -> str:
    lines: list[str] = []
    lines.append("AB2 HYPOTHESIS SEED REPORT")
    lines.append(f"tick_ref={payload['tick_ref']}")
    lines.append(
        "seed_count="
        f"{payload['telemetry']['seed_count']} usable={payload['telemetry']['usable_seed_count']} "
        f"blocked={payload['telemetry']['blocked_seed_count']} unsafe_basis={payload['telemetry']['unsafe_basis_count']}"
    )
    seed_set = payload["seed_set"]
    if seed_set is None:
        lines.append("seed_set=None closure_status=blocked fact_claimed=False")
    else:
        lines.append(
            f"seed_set_id={seed_set['seed_set_id']} hypothesis_count={len(seed_set['hypotheses'])} "
            f"closure_status={seed_set['closure_status']} fact_claimed={seed_set['fact_claimed']} "
            f"selected_fact_hypothesis_id={seed_set['selected_fact_hypothesis_id']}"
        )
        if show_source_refs:
            lines.append(f"  source_event_refs={seed_set['source_event_refs']}")
            lines.append(f"  source_residue_refs={seed_set['source_residue_refs']}")
            lines.append(f"  source_effect_refs={seed_set['source_effect_refs']}")
        if show_hypotheses:
            for hypothesis in seed_set["hypotheses"]:
                kind = hypothesis["hypothesis_kind"]
                if hasattr(kind, "value"):
                    kind = kind.value
                lines.append(
                    f"hypothesis_id={hypothesis['hypothesis_id']} kind={kind} status={hypothesis['seed_status']} "
                    f"confidence_initial={hypothesis['confidence_initial']} policy={hypothesis['confidence_policy']} "
                    f"cause_confirmed={hypothesis['cause_confirmed']}"
                )
                lines.append(f"  explains_what={hypothesis['explains_what']}")
                lines.append(f"  does_not_explain={hypothesis['does_not_explain']}")
                lines.append(f"  expected_observations={hypothesis['expected_observations']}")
                lines.append(f"  possible_tests={hypothesis['possible_tests']}")
                lines.append(f"  missing_evidence={hypothesis['missing_evidence']}")
    lines.append("claim boundary: AB2 emits bounded hypothesis seeds only; no fact closure, no action request, no consciousness/general abduction claim.")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.list_cases:
        for case in list_ab2_probe_cases():
            print(case.case_id)
        return 0

    result = run_ab2_probe_case(args.case)
    payload = asdict(result)
    if args.report or (not args.report and not args.json):
        print(
            _render_report(
                payload,
                show_hypotheses=bool(args.show_hypotheses),
                show_source_refs=bool(args.show_source_refs),
            )
        )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
