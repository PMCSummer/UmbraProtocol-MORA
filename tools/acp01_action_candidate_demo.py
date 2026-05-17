from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from substrate.acp01_internal_action_candidate_production import (
    ACP01ActionSurfaceBasis,
    ACP01CandidateProductionInput,
    ACP01CapabilityBasis,
    ACP01CapabilityStatus,
    ACP01InternalDriveBasis,
    ACP01ObservationBasis,
    ACP01VisibleObjectBasis,
    build_acp01_internal_action_candidates,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ACP01 internal action candidate producer demo")
    parser.add_argument(
        "--case",
        required=True,
        choices=(
            "visible-item-no-drive",
            "water-drive-visible-flask",
            "capacity-blocked",
            "hidden-eval-object",
            "action-space-only",
        ),
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _build_case(case_id: str) -> ACP01CandidateProductionInput:
    drives: tuple[ACP01InternalDriveBasis, ...] = ()
    visible_objects: tuple[ACP01VisibleObjectBasis, ...] = ()
    action_surfaces: tuple[ACP01ActionSurfaceBasis, ...] = ()
    capabilities: tuple[ACP01CapabilityBasis, ...] = ()

    if case_id in {"visible-item-no-drive", "water-drive-visible-flask", "capacity-blocked", "hidden-eval-object"}:
        visible_objects = (
            ACP01VisibleObjectBasis(
                object_ref="item:water_flask",
                object_kind="item",
                location_ref="grid:2,1",
                public_properties={},
                confidence=0.95,
            ),
        )
        action_surfaces = (
            ACP01ActionSurfaceBasis(
                surface_ref="surface:pickup",
                surface_kind="pickup",
                target_ref="item:visible",
                action_kinds=("pickup",),
            ),
            ACP01ActionSurfaceBasis(
                surface_ref="surface:inspect",
                surface_kind="inspect",
                target_ref=None,
                action_kinds=("inspect",),
            ),
        )
        capacity_status = (
            ACP01CapabilityStatus.BLOCKED if case_id == "capacity-blocked" else ACP01CapabilityStatus.AVAILABLE
        )
        capabilities = (
            ACP01CapabilityBasis(
                capability_ref="capability:proximity:item:water_flask",
                capability_kind="proximity",
                target_ref="item:water_flask",
                status=ACP01CapabilityStatus.AVAILABLE,
            ),
            ACP01CapabilityBasis(
                capability_ref="capability:inventory_capacity",
                capability_kind="inventory_capacity",
                target_ref=None,
                status=capacity_status,
            ),
        )

    if case_id == "water-drive-visible-flask":
        drives = (
            ACP01InternalDriveBasis(
                drive_ref="drive:water_need",
                drive_kind="water_need",
                resource_or_goal_ref="item:water_flask",
                urgency_level=0.8,
                source_ref="acp01_demo",
            ),
        )
    elif case_id == "capacity-blocked":
        drives = (
            ACP01InternalDriveBasis(
                drive_ref="drive:water_need",
                drive_kind="water_need",
                resource_or_goal_ref="item:water_flask",
                urgency_level=0.8,
                source_ref="acp01_demo",
            ),
        )
    elif case_id == "hidden-eval-object":
        drives = (
            ACP01InternalDriveBasis(
                drive_ref="drive:hidden_truth_marker",
                drive_kind="eval_only:hidden_truth",
                resource_or_goal_ref="item:water_flask",
                urgency_level=0.8,
                source_ref="acp01_demo",
            ),
        )
    elif case_id == "action-space-only":
        action_surfaces = (
            ACP01ActionSurfaceBasis(
                surface_ref="surface:movement",
                surface_kind="movement",
                target_ref=None,
                action_kinds=("move_forward", "wait"),
            ),
        )

    return ACP01CandidateProductionInput(
        tick_ref=f"acp01_demo:{case_id}",
        observation_basis=ACP01ObservationBasis(
            observation_id=f"obs:{case_id}",
            body_ref="subject_a:body",
            location_ref="grid:2,2",
            orientation="north",
            inventory_ref="subject_a:inventory",
            visible_object_refs=tuple(item.object_ref for item in visible_objects),
            action_surface_refs=tuple(surface.surface_ref for surface in action_surfaces),
            previous_effect_refs=(),
        ),
        internal_drive_bases=drives,
        visible_object_bases=visible_objects,
        action_surface_bases=action_surfaces,
        capability_bases=capabilities,
        effect_feedback_bases=(),
        private_eval_excluded=True,
        scenario_label_excluded=True,
        source="acp01_demo",
    )


def main() -> int:
    args = _args()
    candidate_input = _build_case(args.case)
    result = build_acp01_internal_action_candidates(candidate_input)
    proposal = next((item.proposal for item in result.decisions if item.proposal is not None), None)

    print("ACP01 INTERNAL ACTION CANDIDATE DEMO")
    print(f"case={args.case}")
    print(f"decision_statuses={[item.status.value for item in result.decisions]}")
    print(f"candidate_count={result.proposal_count}")
    print(f"ap01_candidate_set_ready={result.candidate_set_for_ap01 is not None}")
    if proposal is not None:
        print(f"action_kind={proposal.action_kind}")
        print(f"basis_refs={proposal.basis_refs}")
        print(f"execution_boundary={proposal.execution_boundary.value}")
    print("world_execution=False")
    print("ap01_request_published=False")

    if args.json:
        payload = {
            "result": asdict(result),
            "proposal": None if proposal is None else asdict(proposal),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
