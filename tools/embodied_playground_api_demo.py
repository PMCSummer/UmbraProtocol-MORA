from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground import ContractOnlyWorldBackend, PublishedActionEnvelope


def run_demo(subject_id: str) -> dict[str, object]:
    backend = ContractOnlyWorldBackend()
    backend.reset(seed=7, scenario_config={"mode": "contract_only"})
    observation = backend.observe(subject_id)
    action_space = backend.action_space(subject_id)
    envelope = PublishedActionEnvelope(
        envelope_id=f"env:{subject_id}:1",
        subject_id=subject_id,
        ap01_request_ref=f"ap01_request:{subject_id}:1",
        action_kind="inspect",
        target_ref="object:aperture",
        args={"distance": 1},
        intended_effect="inspection",
        source_tick_ref="tick:demo:1",
        source_phase_refs=("W04:permit", "W05:route", "W06:revise"),
        permission_refs=("W04:permit",),
        evidence_refs=("W01:obs",),
        affordance_binding_refs=("A04:bind",),
    )
    effect = backend.submit_action(envelope)
    snapshot = backend.public_snapshot(subject_id)
    eval_snapshot = backend.eval_snapshot()
    return {
        "subject_id": subject_id,
        "observation_id": observation.observation_id,
        "action_space_frame_id": action_space.frame_id,
        "envelope_id": envelope.envelope_id,
        "effect_id": effect.effect_id,
        "effect_status": str(getattr(effect.effect_status, "value", effect.effect_status)),
        "correlation_status": str(getattr(effect.correlation_status, "value", effect.correlation_status)),
        "public_snapshot_id": snapshot.snapshot_id,
        "request_is_execution": False,
        "request_is_success": False,
        "request_is_completion": False,
        "eval_snapshot_present": bool(eval_snapshot.snapshot_id),
        "json_payload": {
            "observation": asdict(observation),
            "action_space": asdict(action_space),
            "published_envelope": asdict(envelope),
            "effect": asdict(effect),
            "public_snapshot": asdict(snapshot),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embodied Playground P1 API demo (contract-only, no world simulation).")
    parser.add_argument("--subject-id", default="subject_a")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = run_demo(args.subject_id)
    print("EMBODIED PLAYGROUND API DEMO")
    print(f"subject_id={payload['subject_id']}")
    print(f"observation_id={payload['observation_id']}")
    print(f"action_space_frame_id={payload['action_space_frame_id']}")
    print(f"envelope_id={payload['envelope_id']}")
    print(f"effect_id={payload['effect_id']}")
    print(f"effect_status={payload['effect_status']}")
    print(f"correlation_status={payload['correlation_status']}")
    print("boundary_claims=request!=execution;request!=success;request!=completion")
    if args.json:
        print(json.dumps(payload["json_payload"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
