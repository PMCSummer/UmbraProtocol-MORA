from __future__ import annotations

from .models import (
    MicroOperationBasis,
    MicroOperationConstraintSet,
    MicroOperationExpectedEffectSet,
    MicroOperationGraphInput,
    MicroOperationInput,
    MicroOperationKind,
    MicroOperationLineage,
    MicroOperationResidueFrame,
    MicroOperationStatus,
)


def inspect_unknown_resource_fixture() -> MicroOperationInput:
    return MicroOperationInput(
        operation_id="micro1:inspect:unknown_resource",
        operation_kind=MicroOperationKind.INSPECT,
        basis=MicroOperationBasis(
            pressure_refs=("pressure:unknown_resource_nearby",),
            need_refs=("need:resource_identification",),
            source_refs=("source:public:vision",),
            uncertainty_refs=("uncertain:identity_unknown",),
            channel_refs={"symbolic_world": ("obs:node:17",)},
            public_observation_refs=("obs:node:17",),
        ),
        target_affordance_refs=("affordance:inspect_resource",),
        action_surface_refs=("surface:inspect",),
        constraints=MicroOperationConstraintSet(required_tool_refs=("tool:scanner_basic",)),
        expected_effects=MicroOperationExpectedEffectSet(
            expected_effect_refs=("effect:identity_candidate_updated",),
            success_criteria_refs=("criterion:public_identity_candidate_present",),
            request_correlation_required=False,
        ),
        lineage=MicroOperationLineage(
            operation_id="micro1:inspect:unknown_resource",
            pressure_ref="pressure:unknown_resource_nearby",
            target_affordance_ref="affordance:inspect_resource",
            action_surface_ref="surface:inspect",
            trace_refs=("trace:pressure_to_inspect",),
        ),
    )


def move_toward_resource_fixture() -> MicroOperationInput:
    return MicroOperationInput(
        operation_id="micro1:move_toward:resource",
        operation_kind=MicroOperationKind.MOVE_TOWARD,
        basis=MicroOperationBasis(
            pressure_refs=("pressure:resource_out_of_reach",),
            source_refs=("source:public:distance_probe",),
            channel_refs={"symbolic_world": ("obs:distance:far",), "body_internal": ("body:range_limit",)},
            public_observation_refs=("obs:distance:far",),
        ),
        target_affordance_refs=("affordance:approach_target",),
        action_surface_refs=("surface:move_toward",),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:distance_delta:decrease",), request_correlation_required=False),
        lineage=MicroOperationLineage(
            operation_id="micro1:move_toward:resource",
            pressure_ref="pressure:resource_out_of_reach",
            target_affordance_ref="affordance:approach_target",
            action_surface_ref="surface:move_toward",
            trace_refs=("trace:range_delta_expected",),
        ),
    )


def use_station_candidate_fixture() -> MicroOperationInput:
    return MicroOperationInput(
        operation_id="micro1:use_station:candidate",
        operation_kind=MicroOperationKind.USE_STATION,
        basis=MicroOperationBasis(
            pressure_refs=("pressure:transform_resource_needed",),
            source_refs=("source:public:station_visible",),
            channel_refs={"symbolic_world": ("station:smelter",), "knowledge_affordance": ("hint:station_capability",)},
            provider_hint_refs=("hint:station_capability",),
            public_observation_refs=("obs:station:smelter",),
        ),
        target_affordance_refs=("affordance:use_station_candidate",),
        action_surface_refs=("surface:use_station",),
        constraints=MicroOperationConstraintSet(
            required_capability_refs=("cap:station_interaction",),
            required_resource_refs=("resource:ore",),
            required_station_refs=("station:smelter",),
        ),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:station_state_delta",)),
        lineage=MicroOperationLineage(
            operation_id="micro1:use_station:candidate",
            pressure_ref="pressure:transform_resource_needed",
            target_affordance_ref="affordance:use_station_candidate",
            action_surface_ref="surface:use_station",
            trace_refs=("trace:station_candidate_only",),
        ),
    )


def store_resource_fixture() -> MicroOperationInput:
    return MicroOperationInput(
        operation_id="micro1:store:resource",
        operation_kind=MicroOperationKind.STORE,
        basis=MicroOperationBasis(
            pressure_refs=("pressure:inventory_overflow",),
            source_refs=("source:public:inventory_state",),
            channel_refs={"symbolic_world": ("inventory:full",)},
            public_observation_refs=("inventory:full",),
        ),
        target_affordance_refs=("affordance:store_resource",),
        action_surface_refs=("surface:store",),
        constraints=MicroOperationConstraintSet(required_resource_refs=("resource:ore",), required_station_refs=("storage:chest",)),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:inventory_storage_delta",)),
        lineage=MicroOperationLineage(
            operation_id="micro1:store:resource",
            pressure_ref="pressure:inventory_overflow",
            target_affordance_ref="affordance:store_resource",
            action_surface_ref="surface:store",
        ),
    )


def repair_check_fixture() -> MicroOperationInput:
    return MicroOperationInput(
        operation_id="micro1:repair_check:machine",
        operation_kind=MicroOperationKind.REPAIR_CHECK,
        basis=MicroOperationBasis(
            pressure_refs=("pressure:machine_stalled",),
            source_refs=("source:machine_ui:panel",),
            provider_hint_refs=("hint:machine_status_stalled",),
            channel_refs={"knowledge_affordance": ("hint:machine_status_stalled",), "system_status": ("status:stalled",)},
            public_observation_refs=("status:stalled",),
        ),
        target_affordance_refs=("affordance:repair_check",),
        action_surface_refs=("surface:repair_check",),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:machine_status_delta",)),
        lineage=MicroOperationLineage(
            operation_id="micro1:repair_check:machine",
            pressure_ref="pressure:machine_stalled",
            target_affordance_ref="affordance:repair_check",
            action_surface_ref="surface:repair_check",
        ),
    )


def provider_hint_basis_fixture() -> MicroOperationInput:
    src = inspect_unknown_resource_fixture()
    return MicroOperationInput(
        operation_id="micro1:inspect:provider_hint_basis",
        operation_kind=MicroOperationKind.INSPECT,
        basis=MicroOperationBasis(
            pressure_refs=src.basis.pressure_refs,
            need_refs=src.basis.need_refs,
            source_refs=src.basis.source_refs,
            uncertainty_refs=src.basis.uncertainty_refs,
            channel_refs={"knowledge_affordance": ("hint:manual:resource_maybe_iron",), "symbolic_world": ("obs:node:17",)},
            provider_hint_refs=("hint:manual:resource_maybe_iron",),
            knowledge_hint_refs=("hint:manual:resource_maybe_iron",),
            public_observation_refs=src.basis.public_observation_refs,
        ),
        target_affordance_refs=src.target_affordance_refs,
        action_surface_refs=src.action_surface_refs,
        expected_effects=src.expected_effects,
        lineage=src.lineage,
    )


def quest_objective_blocked_fixture() -> MicroOperationInput:
    src = provider_hint_basis_fixture()
    return MicroOperationInput(
        operation_id="micro1:quest:block",
        operation_kind=MicroOperationKind.CUSTOM_PUBLIC_OPERATION,
        basis=MicroOperationBasis(
            pressure_refs=src.basis.pressure_refs,
            source_refs=src.basis.source_refs,
            knowledge_hint_refs=("quest:collect_ore:quest_permission",),
            provider_hint_refs=("quest:collect_ore:quest_permission",),
            channel_refs={"knowledge_affordance": ("quest:collect_ore:quest_permission",)},
            public_observation_refs=src.basis.public_observation_refs,
        ),
        target_affordance_refs=("affordance:quest_objective",),
        action_surface_refs=("surface:ask",),
        constraints=MicroOperationConstraintSet(precondition_refs=("quest_permission:must_do",)),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:quest_progress_delta",)),
        lineage=MicroOperationLineage(
            operation_id="micro1:quest:block",
            pressure_ref="pressure:quest_text",
            target_affordance_ref="affordance:quest_objective",
            action_surface_ref="surface:ask",
        ),
    )


def macro_factory_action_blocked_fixture() -> MicroOperationInput:
    return MicroOperationInput(
        operation_id="micro1:macro:factory",
        operation_kind=MicroOperationKind.CUSTOM_PUBLIC_OPERATION,
        basis=MicroOperationBasis(
            pressure_refs=("pressure:complete_factory",),
            source_refs=("source:public:factory_context",),
            public_observation_refs=("obs:factory_context",),
        ),
        target_affordance_refs=("affordance:build_factory",),
        action_surface_refs=("surface:build_factory",),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:factory_complete",)),
        macro_task_ref="build_factory",
        metadata_refs=("build_factory", "ordered_plan"),
    )


def ap01_lineage_reference_fixture() -> MicroOperationInput:
    src = inspect_unknown_resource_fixture()
    return MicroOperationInput(
        operation_id="micro1:lineage:ap01_reference",
        operation_kind=MicroOperationKind.INSPECT,
        basis=src.basis,
        target_affordance_refs=src.target_affordance_refs,
        action_surface_refs=src.action_surface_refs,
        expected_effects=src.expected_effects,
        lineage=MicroOperationLineage(
            operation_id="micro1:lineage:ap01_reference",
            pressure_ref="pressure:unknown_resource_nearby",
            target_affordance_ref="affordance:inspect_resource",
            action_surface_ref="surface:inspect",
            ap01_request_ref="ap01:req:123",
            observed_effect_refs=(),
        ),
        status_hint=MicroOperationStatus.REQUEST_PUBLISHED_ELSEWHERE,
    )


def failed_operation_residue_fixture() -> MicroOperationInput:
    residue = MicroOperationResidueFrame(
        residue_id="residue:inspect_failed",
        operation_ref="micro1:failed:inspect",
        failure_or_block_reason="missing_signal",
        failed_precondition_refs=("precondition:visibility",),
        missing_evidence_refs=("missing:effect_ref",),
        next_pressure_refs=("pressure:reinspect",),
        uncertainty_refs=("uncertain:missing_effect",),
    )
    return MicroOperationInput(
        operation_id="micro1:failed:inspect",
        operation_kind=MicroOperationKind.INSPECT,
        basis=MicroOperationBasis(
            pressure_refs=("pressure:inspect_again",),
            source_refs=("source:public:vision",),
            public_observation_refs=("obs:node:17",),
        ),
        target_affordance_refs=("affordance:inspect_resource",),
        action_surface_refs=("surface:inspect",),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:identity_candidate_updated",)),
        lineage=MicroOperationLineage(
            operation_id="micro1:failed:inspect",
            pressure_ref="pressure:inspect_again",
            target_affordance_ref="affordance:inspect_resource",
            action_surface_ref="surface:inspect",
            residue_refs=("residue:inspect_failed",),
            next_pressure_refs=("pressure:reinspect",),
        ),
        residue_frames=(residue,),
        status_hint=MicroOperationStatus.FAILED,
    )


def effect_without_request_unresolved_fixture() -> MicroOperationInput:
    src = inspect_unknown_resource_fixture()
    return MicroOperationInput(
        operation_id="micro1:unresolved:effect_no_request",
        operation_kind=MicroOperationKind.INSPECT,
        basis=src.basis,
        target_affordance_refs=src.target_affordance_refs,
        action_surface_refs=src.action_surface_refs,
        expected_effects=MicroOperationExpectedEffectSet(
            expected_effect_refs=("effect:identity_candidate_updated",),
            passive_event_allowed=False,
            request_correlation_required=True,
        ),
        lineage=MicroOperationLineage(
            operation_id="micro1:unresolved:effect_no_request",
            pressure_ref="pressure:unknown_resource_nearby",
            target_affordance_ref="affordance:inspect_resource",
            action_surface_ref="surface:inspect",
            observed_effect_refs=("effect:identity_candidate_updated",),
        ),
        status_hint=MicroOperationStatus.EFFECT_OBSERVED,
    )


def bounded_graph_fixture() -> MicroOperationGraphInput:
    step1 = MicroOperationInput(
        operation_id="micro1:g:inspect",
        operation_kind=MicroOperationKind.INSPECT,
        basis=MicroOperationBasis(pressure_refs=("pressure:unknown_resource",), source_refs=("source:public:vision",), public_observation_refs=("obs:node:17",)),
        target_affordance_refs=("affordance:inspect",),
        action_surface_refs=("surface:inspect",),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:identity_candidate",), request_correlation_required=False),
        lineage=MicroOperationLineage(
            operation_id="micro1:g:inspect",
            pressure_ref="pressure:unknown_resource",
            target_affordance_ref="affordance:inspect",
            action_surface_ref="surface:inspect",
            observed_effect_refs=("effect:identity_candidate",),
        ),
        status_hint=MicroOperationStatus.EFFECT_OBSERVED,
    )
    step2 = MicroOperationInput(
        operation_id="micro1:g:move",
        operation_kind=MicroOperationKind.MOVE_TOWARD,
        basis=MicroOperationBasis(pressure_refs=("pressure:approach",), source_refs=("source:public:distance",), public_observation_refs=("obs:distance:far",)),
        target_affordance_refs=("affordance:move",),
        action_surface_refs=("surface:move_toward",),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:distance_delta",), request_correlation_required=False),
        lineage=MicroOperationLineage(
            operation_id="micro1:g:move",
            pressure_ref="pressure:approach",
            target_affordance_ref="affordance:move",
            action_surface_ref="surface:move_toward",
        ),
        status_hint=MicroOperationStatus.CANDIDATE_BASIS_READY,
    )
    step3 = MicroOperationInput(
        operation_id="micro1:g:pickup",
        operation_kind=MicroOperationKind.PICKUP,
        basis=MicroOperationBasis(pressure_refs=("pressure:pickup",), source_refs=("source:public:item",), public_observation_refs=("obs:item:on_ground",)),
        target_affordance_refs=("affordance:pickup",),
        action_surface_refs=("surface:pickup",),
        expected_effects=MicroOperationExpectedEffectSet(expected_effect_refs=("effect:inventory_delta",), request_correlation_required=False),
        lineage=MicroOperationLineage(
            operation_id="micro1:g:pickup",
            pressure_ref="pressure:pickup",
            target_affordance_ref="affordance:pickup",
            action_surface_ref="surface:pickup",
        ),
        status_hint=MicroOperationStatus.PROPOSED,
    )
    from .policy import build_micro_operation_frame

    op1 = build_micro_operation_frame(step1).operation
    op2 = build_micro_operation_frame(step2).operation
    op3 = build_micro_operation_frame(step3).operation
    assert op1 is not None and op2 is not None and op3 is not None

    return MicroOperationGraphInput(
        graph_id="micro1:graph:bounded",
        root_pressure_refs=("pressure:unknown_resource",),
        operations=(op1, op2, op3),
        dependency_edges=((op1.operation_id, op2.operation_id), (op2.operation_id, op3.operation_id)),
        verified_intermediate_refs=("effect:identity_candidate",),
        macro_task_ref="macro:bounded_collection",
    )


def hidden_precondition_rejected_fixture() -> MicroOperationInput:
    src = inspect_unknown_resource_fixture()
    return MicroOperationInput(
        operation_id="micro1:hidden_precondition",
        operation_kind=MicroOperationKind.INSPECT,
        basis=src.basis,
        target_affordance_refs=src.target_affordance_refs,
        action_surface_refs=src.action_surface_refs,
        constraints=MicroOperationConstraintSet(precondition_refs=("hidden_backend_precondition:secret_flag",)),
        expected_effects=src.expected_effects,
        lineage=src.lineage,
    )
