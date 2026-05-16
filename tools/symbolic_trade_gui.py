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

from experiments.symbolic_trade.gui.viewmodel import (  # noqa: E402
    build_stage5_gui_view_model,
    list_stage5_gui_scenarios,
    run_stage5_gui_payload,
)
from experiments.symbolic_trade.gui_app import run_symbolic_trade_gui  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PySide6 GUI for Stage 5 symbolic trade affordance responsibility trace.")
    parser.add_argument("--scenario", choices=list_stage5_gui_scenarios(), help="Scenario id to run.")
    parser.add_argument("--execute-world-actuator", action="store_true", help="Allow world-side transfer actuator execution.")
    parser.add_argument("--dev-mode", action="store_true", help="Enable developer trace inspector mode.")
    parser.add_argument("--include-eval-only", action="store_true", help="Include eval-only payload in developer mode only.")
    parser.add_argument("--dry-run", action="store_true", help="Run Stage 5 trace and print GUI view-model summary without opening a window.")
    parser.add_argument("--timeline-dry-run", action="store_true", help="Print timeline steps in dry-run mode.")
    return parser


def _print_dry_run_summary(payload: dict[str, object], vm, *, include_timeline: bool = False) -> None:
    print("SYMBOLIC TRADE GUI DRY RUN")
    print(f"scenario_id={vm.scenario_id}")
    print(f"execute_world_actuator={vm.execute_world_actuator}")
    print(f"readiness_status={vm.readiness_status}")
    print(f"offer_candidate_emitted={vm.offer_candidate_emitted}")
    print(f"affordance_selection_status={vm.affordance_selection_status}")
    print(f"invocation_request_created={vm.invocation_request_created}")
    print(f"world_actuator_invoked={vm.world_actuator_invoked}")
    print(f"transfer_result={vm.transfer_result}")
    print(f"completion_claim={vm.completion_claim}")
    print(f"verification_status={vm.verification_status}")
    print(f"passive_packet_ref_count={vm.passive_packet_ref_count}")
    print(f"causal_post_invocation_ref_count={vm.causal_post_invocation_ref_count}")
    passed = sum(1 for item in payload.get("falsifier_summary", []) if item.get("passed"))
    total = len(payload.get("falsifier_summary", []))
    print(f"falsifier_summary={passed}/{total} passed")
    if "eval_only" in payload:
        print("eval_only=present")
    if include_timeline:
        print("timeline_steps=")
        for step, frame in zip(vm.timeline_state.steps, vm.playback_trace.frames):
            print(
                f"- {step.step_index}:{step.step_id}:status={step.status}:"
                f"frame={frame.event_kind}:public_status={frame.public_status}:"
                f"invoked={frame.chamber_state.actuator_invoked_visible}:"
                f"completion={frame.chamber_state.completion_claim}:"
                f"result={frame.chamber_state.transfer_result}:"
                f"passive={frame.chamber_state.passive_packet_ref_count}:"
                f"causal={frame.chamber_state.causal_post_invocation_ref_count}:"
                f"evidence={list(step.evidence_refs)}"
            )


def main() -> int:
    args = _parser().parse_args()
    scenario = args.scenario or list_stage5_gui_scenarios()[0]

    if args.dry_run or args.timeline_dry_run:
        payload = run_stage5_gui_payload(
            scenario,
            execute_world_actuator=args.execute_world_actuator,
            include_eval_only=args.dev_mode and args.include_eval_only,
            include_ledger=True,
            include_records=True,
        )
        vm = build_stage5_gui_view_model(
            payload,
            dev_mode=args.dev_mode,
            include_eval_only=args.dev_mode and args.include_eval_only,
        )
        _print_dry_run_summary(payload, vm, include_timeline=args.timeline_dry_run)
        if args.dev_mode:
            print("developer_payload_json=")
            print(json.dumps(vm.developer_payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    return run_symbolic_trade_gui(
        scenario=scenario,
        execute_world_actuator=args.execute_world_actuator,
        dev_mode=args.dev_mode,
    )


if __name__ == "__main__":
    raise SystemExit(main())
