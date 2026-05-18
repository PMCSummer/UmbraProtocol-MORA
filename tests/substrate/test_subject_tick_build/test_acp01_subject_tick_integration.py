from __future__ import annotations

from substrate.acp01_internal_action_candidate_production import (
    ACP01ActionSurfaceBasis,
    ACP01CandidateProductionInput,
    ACP01CapabilityBasis,
    ACP01CapabilityStatus,
    ACP01InternalDriveBasis,
    ACP01ObservationBasis,
    ACP01VisibleObjectBasis,
)
from substrate.ap01_subject_action_publication import (
    AP01ActionPublicationCandidate,
    AP01ActionPublicationCandidateSet,
    AP01CandidateOrigin,
)
from substrate.subject_tick import SubjectTickContext
from tests.substrate.subject_tick_testkit import build_subject_tick


def _acp_input(
    *,
    drive_kind: str = "water_need",
    drive_class: str = "pickup_intent",
    allowed_action_kinds: tuple[str, ...] = ("pickup",),
    target_object_refs: tuple[str, ...] = ("item:water_flask",),
) -> ACP01CandidateProductionInput:
    return ACP01CandidateProductionInput(
        tick_ref="subject_tick:acp01:1",
        observation_basis=ACP01ObservationBasis(
            observation_id="obs:1",
            body_ref="subject_a:body",
            location_ref="grid:2,2",
            orientation="north",
            inventory_ref="subject_a:inventory",
            visible_object_refs=("item:water_flask",),
            action_surface_refs=("surface:pickup", "surface:inspect"),
            previous_effect_refs=(),
        ),
        internal_drive_bases=(
            ACP01InternalDriveBasis(
                drive_ref="drive:water_need:1",
                drive_kind=drive_kind,
                resource_or_goal_ref="item:water_flask",
                urgency_level=0.7,
                source_ref="tests.subject_tick.acp01",
                drive_class=drive_class,
                target_object_refs=target_object_refs,
                target_resource_refs=target_object_refs,
                target_affordance_refs=allowed_action_kinds,
                allowed_action_kinds=allowed_action_kinds,
                required_capability_refs=("proximity", "inventory_capacity"),
                relevance_basis_refs=("drive_basis:typed:pickup",),
            ),
        ),
        visible_object_bases=(
            ACP01VisibleObjectBasis(
                object_ref="item:water_flask",
                object_kind="item",
                location_ref="grid:2,1",
                public_properties={},
                confidence=0.95,
            ),
        ),
        action_surface_bases=(
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
        ),
        capability_bases=(
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
                status=ACP01CapabilityStatus.AVAILABLE,
            ),
        ),
        effect_feedback_bases=(),
        private_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.subject_tick.acp01",
    )


def _ap01_candidate_set() -> AP01ActionPublicationCandidateSet:
    candidate = AP01ActionPublicationCandidate(
        candidate_id="explicit:ap01:1",
        action_kind="inspect",
        target_ref="item:water_flask",
        args={},
        intended_effect="inspect:item:water_flask",
        source_tick_ref="subject_tick:explicit:1",
        source_cycle_ref="cycle:explicit:1",
        source_phase_refs=("W04:permission", "W05:routing", "W06:revision"),
        affordance_binding_refs=(),
        permission_refs=("W04:permit",),
        evidence_refs=("W01:packet",),
        episode_refs=("P02:episode",),
        residue_refs=(),
        revalidation_refs=(),
        blocked_claim_refs=(),
        desired_refs=(),
        predicted_refs=(),
        observed_refs=(),
        permitted_refs=("W05:permitted",),
        candidate_origin=AP01CandidateOrigin.SUBJECT_TICK_CANDIDATE_BASIS,
        forbidden_basis_markers=(),
        no_hidden_truth_used=True,
        no_eval_only_used=True,
        no_scenario_label_used=True,
    )
    return AP01ActionPublicationCandidateSet(
        candidate_set_id="explicit:ap01:set",
        candidates=(candidate,),
    )


def _tick(context: SubjectTickContext | None = None):
    return build_subject_tick(
        case_id="acp01_subject_tick",
        energy=70.0,
        cognitive=60.0,
        safety=70.0,
        context=context,
    )


def test_subject_tick_exposes_acp01_result_and_counters() -> None:
    result = _tick(
        SubjectTickContext(
            acp01_candidate_production_input=_acp_input(),
        )
    )
    assert result.acp01_result.proposed_count >= 1
    assert result.state.acp01_candidate_input_present is True
    assert result.state.acp01_proposed_count >= 1


def test_acp01_candidate_set_passes_to_ap01_when_no_explicit_ap01_set() -> None:
    result = _tick(
        SubjectTickContext(
            acp01_candidate_production_input=_acp_input(),
        )
    )
    assert result.state.ap01_candidate_source == "acp01_internal"
    assert result.ap01_result.telemetry.candidate_count == 1
    assert result.ap01_result.telemetry.published_request_count == 1


def test_explicit_ap01_candidate_behavior_remains_compatible() -> None:
    result = _tick(
        SubjectTickContext(
            acp01_candidate_production_input=_acp_input(),
            ap01_action_publication_candidate_set=_ap01_candidate_set(),
        )
    )
    assert result.state.ap01_candidate_source == "external_context"
    assert result.ap01_result.telemetry.candidate_count == 1
    assert result.ap01_result.telemetry.published_request_count == 1


def test_no_acp01_input_means_no_acp01_candidate_and_no_ap01_request() -> None:
    result = _tick()
    assert result.acp01_result.proposed_count == 0
    assert result.ap01_result.telemetry.published_request_count == 0


def test_unsafe_acp01_basis_produces_zero_ap01_requests() -> None:
    result = _tick(
        SubjectTickContext(
            acp01_candidate_production_input=_acp_input(
                drive_kind="pickup_intent",
                drive_class="pickup_intent",
                allowed_action_kinds=("pickup",),
                target_object_refs=("scenario_id:pickup",),
            ),
        )
    )
    assert result.acp01_result.unsafe_basis_count >= 1
    assert result.ap01_result.telemetry.published_request_count == 0


def test_ap01_request_source_identified_as_acp01_internal() -> None:
    result = _tick(
        SubjectTickContext(
            acp01_candidate_production_input=_acp_input(),
        )
    )
    assert result.state.ap01_candidate_source == "acp01_internal"
