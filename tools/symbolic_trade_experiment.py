from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from experiments.symbolic_trade import (
    list_scenarios,
    result_to_dict,
    run_stage1_scenario,
    run_stage2_trace,
    stage2_result_to_dict,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run symbolic trade-through-wall Stage 0/1 harness scenarios.")
    parser.add_argument("--list-scenarios", action="store_true", help="List available deterministic scenarios.")
    parser.add_argument("--scenario", choices=list_scenarios(), help="Run a single scenario.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--run-falsifiers", action="store_true", help="Include falsifier checks in output.")
    parser.add_argument("--include-eval-only", action="store_true", help="Include eval-only harness truth in JSON output.")
    parser.add_argument("--stage2-trace", action="store_true", help="Run Stage 2 subject-adapter W01->W06 trace-through.")
    return parser


def _print_text(payload: dict[str, object]) -> None:
    falsifiers = payload.get("falsifier_results", [])
    passed = sum(1 for item in falsifiers if item.get("passed"))
    total = len(falsifiers)
    print("SYMBOLIC TRADE HARNESS")
    print(f"scenario_id={payload['scenario_id']}")
    print(f"stage={payload['stage']}")
    print(f"packet_count={payload['packet_count']}")
    print(f"falsifier_summary={passed}/{total} passed")
    print(f"claim_discipline_markers={payload['claim_discipline_markers']}")


def _print_stage2_text(payload: dict[str, object]) -> None:
    falsifiers = payload.get("falsifier_results", [])
    passed = sum(1 for item in falsifiers if item.get("passed"))
    total = len(falsifiers)
    verdict = payload.get("stage2_trace_verdict", {})
    print("SYMBOLIC TRADE HARNESS STAGE2 TRACE")
    print(f"scenario_id={payload['scenario_id']}")
    print(f"stage={payload['stage']}")
    print(f"packet_count={payload['packet_count']}")
    print(f"phase_coverage={payload.get('phase_coverage', [])}")
    print(f"stage2_trace_verdict={verdict.get('status')}")
    print(f"falsifier_summary={passed}/{total} passed")
    print("claim_boundary=['stage2 trace-through only', 'no autonomous trade claim']")


def main() -> int:
    args = _parser().parse_args()

    if args.list_scenarios:
        for name in list_scenarios():
            print(name)
        return 0

    if not args.scenario:
        raise SystemExit("Provide --scenario or --list-scenarios")

    if args.stage2_trace:
        result = run_stage2_trace(args.scenario, include_falsifiers=args.run_falsifiers or args.json)
        payload = stage2_result_to_dict(result, include_eval_only=args.include_eval_only)
    else:
        result = run_stage1_scenario(args.scenario, include_falsifiers=args.run_falsifiers or args.json)
        payload = result_to_dict(result, include_eval_only=args.include_eval_only)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if args.stage2_trace:
            _print_stage2_text(payload)
        else:
            _print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
