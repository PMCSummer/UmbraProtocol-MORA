from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground import GridWorldBackend, list_grid_world_scenarios, make_published_action_envelope


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P2 Minimal GridWorld backend demo for embodied playground API.")
    parser.add_argument("--list-scenarios", action="store_true", help="List available grid scenarios")
    parser.add_argument("--scenario", default="empty_room_presence", help="Scenario id")
    parser.add_argument("--action", default="wait", help="Action kind")
    parser.add_argument("--target", default=None, help="Optional target ref")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument("--show-eval-only", action="store_true", help="Include eval-only snapshot")
    return parser.parse_args()


def run_demo(scenario_id: str, action_kind: str, target_ref: str | None = None) -> dict[str, object]:
    backend = GridWorldBackend(scenario_id=scenario_id)
    observation_before = backend.observe("subject_a")
    action_space = backend.action_space("subject_a")
    envelope = make_published_action_envelope(
        subject_id="subject_a",
        action_kind=action_kind,
        target_ref=target_ref,
        request_ref=f"ap01_request:{scenario_id}:{action_kind}",
    )
    effect = backend.submit_action(envelope)
    observation_after = backend.observe("subject_a")
    public_snapshot = backend.public_snapshot("subject_a")
    eval_snapshot = backend.eval_snapshot()

    return {
        "scenario_id": scenario_id,
        "action_kind": action_kind,
        "target_ref": target_ref,
        "observation_before": asdict(observation_before),
        "action_space": asdict(action_space),
        "published_envelope": asdict(envelope),
        "effect": asdict(effect),
        "observation_after": asdict(observation_after),
        "public_snapshot": asdict(public_snapshot),
        "eval_snapshot": asdict(eval_snapshot),
    }


def main() -> int:
    args = _parse_args()
    if args.list_scenarios:
        for scenario_id in list_grid_world_scenarios():
            print(scenario_id)
        return 0

    payload = run_demo(args.scenario, args.action, args.target)
    print("EMBODIED GRID WORLD DEMO (P2)")
    print(f"scenario={payload['scenario_id']}")
    print(f"action={payload['action_kind']}")
    print(f"target={payload['target_ref']}")
    effect_status = payload["effect"]["effect_status"]
    if hasattr(effect_status, "value"):
        effect_status = getattr(effect_status, "value")
    elif isinstance(effect_status, dict) and "value" in effect_status:
        effect_status = effect_status["value"]
    print(f"effect_status={effect_status}")
    print(f"blocked_reason={payload['effect']['blocked_reason']}")
    print(f"location_before={payload['observation_before']['body_state']['location_ref']}")
    print(f"location_after={payload['observation_after']['body_state']['location_ref']}")
    print(f"inventory_before={payload['observation_before']['inventory_state']['item_counts']}")
    print(f"inventory_after={payload['observation_after']['inventory_state']['item_counts']}")
    print("boundary_claims=request!=execution;request!=success;request!=completion;no_subject_tick_loop")

    if args.json:
        output = {
            "scenario_id": payload["scenario_id"],
            "action_kind": payload["action_kind"],
            "target_ref": payload["target_ref"],
            "observation_before": payload["observation_before"],
            "action_space": payload["action_space"],
            "published_envelope": payload["published_envelope"],
            "effect": payload["effect"],
            "observation_after": payload["observation_after"],
            "public_snapshot": payload["public_snapshot"],
        }
        if args.show_eval_only:
            output["eval_only"] = payload["eval_snapshot"]
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
