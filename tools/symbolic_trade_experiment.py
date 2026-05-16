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
    run_stage25_reaction,
    run_stage3_response,
    stage25_result_to_dict,
    stage3_result_to_dict,
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
    parser.add_argument("--stage25-reaction", action="store_true", help="Run Stage 2.5 real-A reaction probe at highest executable surface.")
    parser.add_argument("--stage3-response", action="store_true", help="Run Stage 3 real-A response-candidate probe.")
    parser.add_argument("--include-response-candidates", action="store_true", help="Include full response candidate payload in Stage 3 JSON output.")
    parser.add_argument("--stage3-summary", action="store_true", help="Print concise Stage 3 summary in text mode.")
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


def _print_stage25_text(payload: dict[str, object]) -> None:
    falsifiers = payload.get("falsifier_results", [])
    passed = sum(1 for item in falsifiers if item.get("passed"))
    total = len(falsifiers)
    surface = payload.get("execution_surface", {})
    self_state = payload.get("self_state_probe", {})
    print("SYMBOLIC TRADE HARNESS STAGE2.5 REAL-A REACTION PROBE")
    print(f"scenario_id={payload['scenario_id']}")
    print(f"stage={payload['stage']}")
    print(f"execution_level={surface.get('execution_level')}")
    print(f"subject_tick_used={surface.get('subject_tick_used')}")
    print(f"owner_surface_used={surface.get('owner_surface_used')}")
    print(f"adapter_projection_used={surface.get('adapter_projection_used')}")
    print(f"fallback_reasons={surface.get('fallback_reasons', [])}")
    print(f"a_internal_state_summary={{'profile_id': {self_state.get('profile_id')}, 'deficit_markers': {self_state.get('deficit_markers', [])}, 'surplus_markers': {self_state.get('surplus_markers', [])}}}")
    print(f"b_visible_claim_summary={payload.get('b_visible_claim_summary', {})}")
    phase_coverage = sorted(
        {
            code
            for step in payload.get("steps", [])
            for code in step.get("phase_trace_summary", {}).get("phase_coverage", [])
        }
    )
    phase_coverage_verified = all(
        step.get("phase_trace_summary", {}).get("phase_coverage_verified", False)
        for step in payload.get("steps", [])
    )
    print(f"phase_coverage={phase_coverage}")
    print(f"phase_coverage_verified={phase_coverage_verified}")
    print(f"falsifier_summary={passed}/{total} passed")
    print("claim_boundary=['stage2.5 reaction probe only', 'no autonomous trade claim']")


def _print_stage3_text(payload: dict[str, object], *, summary_only: bool = False) -> None:
    falsifiers = payload.get("falsifier_summary", [])
    passed = sum(1 for item in falsifiers if item.get("passed"))
    total = len(falsifiers)
    print("SYMBOLIC TRADE HARNESS STAGE3 RESPONSE-CANDIDATE PROBE")
    print(f"scenario_id={payload['scenario_name']}")
    print(f"stage={payload['stage']}")
    print(f"execution_level={payload.get('execution_level')}")
    print(f"subject_tick_used={payload.get('subject_tick_used')}")
    print(f"owner_surface_used={payload.get('owner_surface_used')}")
    print(f"adapter_projection_used={payload.get('adapter_projection_used')}")
    print(f"fallback_reasons={payload.get('fallback_reasons', [])}")
    print(f"selected_response_kind={payload.get('selected_response_kind')}")
    print(f"response_verdict={payload.get('response_verdict')}")
    print(f"phase_coverage_verified={payload.get('phase_coverage_verified')}")
    print(f"phase_coverage_evidence={payload.get('phase_coverage_evidence', [])}")
    if not summary_only:
        print(f"response_candidates_count={len(payload.get('response_candidates', []))}")
    print(f"falsifier_summary={passed}/{total} passed")
    print("claim_boundary=['stage3 response-candidate probe only', 'no autonomous trade claim']")


def main() -> int:
    args = _parser().parse_args()

    if args.list_scenarios:
        for name in list_scenarios():
            print(name)
        return 0

    if not args.scenario:
        raise SystemExit("Provide --scenario or --list-scenarios")

    if args.stage3_response:
        result = run_stage3_response(args.scenario, include_falsifiers=args.run_falsifiers or args.json)
        payload = stage3_result_to_dict(
            result,
            include_eval_only=args.include_eval_only,
            include_response_candidates=args.include_response_candidates or not args.stage3_summary,
        )
    elif args.stage25_reaction:
        result = run_stage25_reaction(args.scenario, include_falsifiers=args.run_falsifiers or args.json)
        payload = stage25_result_to_dict(result, include_eval_only=args.include_eval_only)
    elif args.stage2_trace:
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
        elif args.stage3_response:
            _print_stage3_text(payload, summary_only=args.stage3_summary)
        elif args.stage25_reaction:
            _print_stage25_text(payload)
        else:
            _print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
