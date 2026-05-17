from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.ap01_subject_action_publication import (
    AP01ActionPublicationCandidate,
    AP01ActionPublicationCandidateSet,
    AP01CandidateOrigin,
    build_ap01_subject_action_publication,
)


def _candidate(case_id: str, **overrides: object) -> AP01ActionPublicationCandidate:
    payload: dict[str, object] = {
        "candidate_id": f"{case_id}:candidate",
        "action_kind": "inspect",
        "target_ref": "station:alpha",
        "args": {"mode": "inspection"},
        "intended_effect": "inspection",
        "source_tick_ref": f"subject-tick:{case_id}",
        "source_cycle_ref": f"cycle:{case_id}",
        "source_phase_refs": ("W04:permission", "W05:routing", "W06:revision"),
        "affordance_binding_refs": (),
        "permission_refs": ("W04:permit",),
        "evidence_refs": ("W01:packet",),
        "episode_refs": ("P02:episode",),
        "residue_refs": (),
        "revalidation_refs": (),
        "blocked_claim_refs": (),
        "desired_refs": (),
        "predicted_refs": (),
        "observed_refs": (),
        "permitted_refs": ("W05:permitted",),
        "candidate_origin": AP01CandidateOrigin.TEST_FIXTURE_CANDIDATE,
        "forbidden_basis_markers": (),
        "no_hidden_truth_used": True,
        "no_eval_only_used": True,
        "no_scenario_label_used": True,
    }
    payload.update(overrides)
    return AP01ActionPublicationCandidate(**payload)


def _scenario_candidate(scenario: str) -> AP01ActionPublicationCandidate:
    if scenario == "valid_move":
        return _candidate(
            scenario,
            action_kind="move_forward",
            target_ref=None,
            args={"steps": 1},
            intended_effect="approach_target",
        )
    if scenario == "valid_inspect":
        return _candidate(scenario, action_kind="inspect", target_ref="object:panel")
    if scenario == "valid_use_station":
        return _candidate(
            scenario,
            action_kind="use_station",
            target_ref="station:alpha",
            affordance_binding_refs=("A04:binding:station_alpha",),
        )
    if scenario == "desired_only_rejected":
        return _candidate(
            scenario,
            permission_refs=(),
            evidence_refs=(),
            permitted_refs=(),
            desired_refs=("desired:state",),
        )
    if scenario == "affordance_only_rejected":
        return _candidate(
            scenario,
            permission_refs=(),
            evidence_refs=(),
            permitted_refs=(),
            affordance_binding_refs=("A04:binding:only",),
        )
    if scenario == "scenario_hidden_eval_rejected":
        return _candidate(
            scenario,
            forbidden_basis_markers=("scenario_id:demo", "eval_only:label"),
            no_eval_only_used=False,
            no_scenario_label_used=False,
        )
    raise ValueError(scenario)


def run_demo(scenario: str) -> int:
    candidate = _scenario_candidate(scenario)
    result = build_ap01_subject_action_publication(
        tick_id=f"ap01-demo-{scenario}",
        tick_index=1,
        candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id=f"ap01-demo:{scenario}:set",
            candidates=(candidate,),
            source_lineage=("tools.ap01.demo", scenario),
        ),
        allow_test_fixture_candidates=True,
    )
    decision = result.decisions[0] if result.decisions else None
    request = result.published_requests[0] if result.published_requests else None

    print("AP01 ACTION PUBLICATION DEMO")
    print(f"scenario={scenario}")
    print(
        "telemetry="
        f"(candidates={result.telemetry.candidate_count}, published={result.telemetry.published_request_count}, "
        f"blocked={result.telemetry.blocked_count}, revalidate={result.telemetry.revalidation_required_count}, "
        f"unsafe={result.telemetry.unsafe_basis_count})"
    )
    if decision is not None:
        print(
            "decision="
            f"(status={decision.decision_status.value}, blocked_reason={decision.blocked_reason}, "
            f"reason_codes={decision.reason_codes}, missing={decision.missing_requirements})"
        )
    if request is not None:
        print(
            "request="
            f"(action_kind={request.action_kind}, target_ref={request.target_ref}, "
            f"execution_boundary={request.execution_boundary.value}, executed_by_subject={request.executed_by_subject}, "
            f"world_execution_status={request.world_execution_status.value}, must_wait_for_world_effect={request.must_wait_for_world_effect})"
        )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic AP01 action-publication scenarios.")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=(
            "valid_move",
            "valid_inspect",
            "valid_use_station",
            "desired_only_rejected",
            "affordance_only_rejected",
            "scenario_hidden_eval_rejected",
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_demo(args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
