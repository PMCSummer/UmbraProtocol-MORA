from __future__ import annotations

from dataclasses import replace

from substrate.micro1_micro_operation_frame import (
    MicroOperationBasis,
    MicroOperationBlockReason,
    MicroOperationExpectedEffectSet,
    MicroOperationGraphInput,
    MicroOperationInput,
    MicroOperationKind,
    MicroOperationLineage,
    MicroOperationStatus,
    MicroValidationStatus,
    ap01_lineage_reference_fixture,
    bounded_graph_fixture,
    build_micro_operation_frame,
    build_micro_operation_graph,
    effect_without_request_unresolved_fixture,
    failed_operation_residue_fixture,
    hidden_precondition_rejected_fixture,
    inspect_unknown_resource_fixture,
    macro_factory_action_blocked_fixture,
    move_toward_resource_fixture,
    provider_hint_basis_fixture,
    quest_objective_blocked_fixture,
    store_resource_fixture,
    use_station_candidate_fixture,
)


def test_micro1_creates_operation_from_public_pressure_and_affordance() -> None:
    run = build_micro_operation_frame(inspect_unknown_resource_fixture())
    assert run.status is MicroValidationStatus.ACCEPTED
    assert run.operation is not None
    assert run.operation.status is MicroOperationStatus.CANDIDATE_BASIS_READY


def test_micro1_blocks_operation_without_public_basis() -> None:
    src = inspect_unknown_resource_fixture()
    run = build_micro_operation_frame(replace(src, basis=MicroOperationBasis()))
    assert run.status is MicroValidationStatus.BLOCKED
    assert MicroOperationBlockReason.MISSING_PUBLIC_PRESSURE_BASIS in run.blocked_reasons


def test_micro1_action_surface_is_basis_not_command() -> None:
    run = build_micro_operation_frame(move_toward_resource_fixture())
    assert run.operation is not None
    assert run.operation.action_surface_refs == ("surface:move_toward",)
    assert MicroOperationBlockReason.ACTION_SURFACE_IS_COMMAND not in run.blocked_reasons
    assert run.operation.authority_flags.can_select_action is False


def test_micro1_does_not_emit_ap01_request() -> None:
    run = build_micro_operation_frame(store_resource_fixture())
    assert run.operation is not None
    assert run.operation.authority_flags.can_publish_ap01 is False
    assert MicroOperationBlockReason.AP01_EMISSION_ATTEMPTED not in run.blocked_reasons


def test_micro1_operation_references_ap01_request_only_after_publication() -> None:
    run = build_micro_operation_frame(ap01_lineage_reference_fixture())
    assert run.status is MicroValidationStatus.ACCEPTED
    assert run.operation is not None
    assert run.operation.status is MicroOperationStatus.REQUEST_PUBLISHED_ELSEWHERE
    assert run.operation.lineage is not None
    assert run.operation.lineage.ap01_request_ref == "ap01:req:123"

    bad = replace(ap01_lineage_reference_fixture(), lineage=replace(ap01_lineage_reference_fixture().lineage, ap01_request_ref="internal:new_request"))  # type: ignore[arg-type]
    blocked = build_micro_operation_frame(bad)
    assert MicroOperationBlockReason.AP01_EMISSION_ATTEMPTED in blocked.blocked_reasons


def test_micro1_success_requires_observed_effect_ref() -> None:
    src = inspect_unknown_resource_fixture()
    run = build_micro_operation_frame(replace(src, status_hint=MicroOperationStatus.SUCCEEDED))
    assert MicroOperationBlockReason.SUCCESS_WITHOUT_EFFECT_REF in run.blocked_reasons


def test_micro1_effect_without_request_ref_stays_unresolved() -> None:
    run = build_micro_operation_frame(effect_without_request_unresolved_fixture())
    assert run.operation is not None
    assert run.operation.status is MicroOperationStatus.UNRESOLVED
    assert MicroOperationBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER in run.blocked_reasons
    assert run.status is MicroValidationStatus.PARTIAL


def test_micro1_failure_preserves_residue() -> None:
    run = build_micro_operation_frame(failed_operation_residue_fixture())
    assert run.operation is not None
    assert run.operation.status in {MicroOperationStatus.FAILED, MicroOperationStatus.RESIDUE_OPEN}
    assert run.operation.residue_frame_refs
    assert MicroOperationBlockReason.RESIDUE_MISSING_AFTER_FAILURE not in run.blocked_reasons

    src = failed_operation_residue_fixture()
    missing = build_micro_operation_frame(
        replace(
            src,
            residue_frames=(),
            lineage=replace(src.lineage, residue_refs=(), next_pressure_refs=()),  # type: ignore[arg-type]
        )
    )
    assert MicroOperationBlockReason.RESIDUE_MISSING_AFTER_FAILURE in missing.blocked_reasons


def test_micro1_macro_action_requires_decomposition() -> None:
    run = build_micro_operation_frame(macro_factory_action_blocked_fixture())
    assert MicroOperationBlockReason.MACRO_ACTION_REQUIRES_DECOMPOSITION in run.blocked_reasons


def test_micro1_knowledge_hint_not_operation_truth() -> None:
    run = build_micro_operation_frame(provider_hint_basis_fixture())
    assert run.operation is not None
    assert run.operation.basis.knowledge_hint_refs
    assert run.operation.status is not MicroOperationStatus.SUCCEEDED


def test_micro1_quest_objective_not_operation_permission() -> None:
    run = build_micro_operation_frame(quest_objective_blocked_fixture())
    assert MicroOperationBlockReason.QUEST_OBJECTIVE_AS_PERMISSION_DETECTED in run.blocked_reasons


def test_micro1_cost_winner_not_action_permission() -> None:
    src = provider_hint_basis_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("cost_winner:best",)))
    assert MicroOperationBlockReason.COST_WINNER_AS_PERMISSION_DETECTED in run.blocked_reasons


def test_micro1_recipe_candidate_not_operation_script() -> None:
    src = provider_hint_basis_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("ordered_plan", "recipe_script")))
    assert MicroOperationBlockReason.RECIPE_CANDIDATE_AS_SCRIPT_DETECTED in run.blocked_reasons


def test_micro1_hidden_precondition_rejected() -> None:
    run = build_micro_operation_frame(hidden_precondition_rejected_fixture())
    assert MicroOperationBlockReason.HIDDEN_PRECONDITION_DETECTED in run.blocked_reasons


def test_micro1_operation_status_lattice_transitions() -> None:
    proposed = build_micro_operation_frame(replace(inspect_unknown_resource_fixture(), expected_effects=MicroOperationExpectedEffectSet()))
    assert proposed.operation is not None
    assert proposed.operation.status is MicroOperationStatus.BLOCKED

    ready = build_micro_operation_frame(inspect_unknown_resource_fixture())
    assert ready.operation is not None
    assert ready.operation.status is MicroOperationStatus.CANDIDATE_BASIS_READY

    req = build_micro_operation_frame(ap01_lineage_reference_fixture())
    assert req.operation is not None
    assert req.operation.status is MicroOperationStatus.REQUEST_PUBLISHED_ELSEWHERE

    observed_src = ap01_lineage_reference_fixture()
    observed = build_micro_operation_frame(
        replace(
            observed_src,
            lineage=replace(observed_src.lineage, observed_effect_refs=("effect:identity_candidate_updated",)),  # type: ignore[arg-type]
        )
    )
    assert observed.operation is not None
    assert observed.operation.status is MicroOperationStatus.EFFECT_OBSERVED

    succeeded_src = observed_src
    succeeded = build_micro_operation_frame(
        replace(
            succeeded_src,
            lineage=replace(succeeded_src.lineage, observed_effect_refs=("effect:identity_candidate_updated",)),  # type: ignore[arg-type]
            status_hint=MicroOperationStatus.SUCCEEDED,
        )
    )
    assert succeeded.operation is not None
    assert succeeded.operation.status is MicroOperationStatus.SUCCEEDED

    failed = build_micro_operation_frame(failed_operation_residue_fixture())
    assert failed.operation is not None
    assert failed.operation.status is MicroOperationStatus.FAILED


def test_micro1_multichannel_basis_preserved() -> None:
    src = provider_hint_basis_fixture()
    run = build_micro_operation_frame(
        replace(
            src,
            basis=replace(
                src.basis,
                channel_refs={
                    "symbolic_world": ("obs:node:17",),
                    "knowledge_affordance": ("hint:manual:resource_maybe_iron",),
                    "language_contact": ("lang:testimony:maybe_iron",),
                    "sensory_candidate": ("sensory:visual:candidate:ore",),
                    "body_internal": ("body:pressure:hunger",),
                    "system_status": ("status:net:ok",),
                },
                language_testimony_refs=("lang:testimony:maybe_iron",),
                sensory_candidate_refs=("sensory:visual:candidate:ore",),
                body_pressure_refs=("body:pressure:hunger",),
            ),
        )
    )
    assert run.operation is not None
    assert "language_contact" in run.operation.basis.channel_refs
    assert "sensory_candidate" in run.operation.basis.channel_refs


def test_micro1_no_skill_maturity_or_automation_claim() -> None:
    first = build_micro_operation_frame(ap01_lineage_reference_fixture())
    second = build_micro_operation_frame(ap01_lineage_reference_fixture())
    for result in (first, second):
        assert result.operation is not None
        flags = result.operation.authority_flags
        assert flags.can_mature_skill is False
        assert flags.can_claim_automation is False
        assert flags.can_mature_recipe is False


def test_micro1_operation_trace_preserves_pressure_to_effect_lineage() -> None:
    src = ap01_lineage_reference_fixture()
    run = build_micro_operation_frame(
        replace(
            src,
            lineage=replace(src.lineage, observed_effect_refs=("effect:identity_candidate_updated",), trace_refs=("trace:pressure_to_effect",)),  # type: ignore[arg-type]
        )
    )
    assert run.operation is not None
    assert run.operation.lineage is not None
    assert run.operation.lineage.pressure_ref is not None
    assert run.operation.lineage.observed_effect_refs
    assert "trace:pressure_to_effect" in run.operation.lineage.trace_refs


def test_micro1_bounded_operation_graph_blocks_unverified_intermediate() -> None:
    run = build_micro_operation_graph(bounded_graph_fixture())
    assert run.status is MicroValidationStatus.PARTIAL
    assert run.graph is not None
    assert run.graph.blocked_edges
    assert run.counters.unverified_intermediate_count >= 1


def test_micro1_macro_task_decomposes_into_micro_graph_not_atomic_command() -> None:
    graph_input = bounded_graph_fixture()
    run = build_micro_operation_graph(replace(graph_input, macro_task_ref="build_factory"))
    assert run.graph is not None
    assert run.graph.macro_task_decomposed is True
    assert MicroOperationBlockReason.MACRO_ACTION_REQUIRES_DECOMPOSITION not in run.blocked_reasons


def test_micro1_passive_event_effect_allowed_only_when_marked() -> None:
    src = inspect_unknown_resource_fixture()
    base_lineage = replace(src.lineage, observed_effect_refs=("effect:identity_candidate_updated",))  # type: ignore[arg-type]
    blocked = build_micro_operation_frame(
        replace(
            src,
            expected_effects=replace(src.expected_effects, passive_event_allowed=False),
            lineage=base_lineage,
        )
    )
    assert blocked.operation is not None
    assert blocked.operation.status is MicroOperationStatus.UNRESOLVED

    accepted = build_micro_operation_frame(
        replace(
            src,
            expected_effects=replace(src.expected_effects, passive_event_allowed=True),
            lineage=base_lineage,
        )
    )
    assert accepted.operation is not None
    assert accepted.operation.status is MicroOperationStatus.CANDIDATE_BASIS_READY


def test_micro1_failed_precondition_becomes_next_pressure() -> None:
    run = build_micro_operation_frame(failed_operation_residue_fixture())
    assert run.operation is not None
    assert run.operation.lineage is not None
    assert run.operation.lineage.next_pressure_refs


def test_micro1_operation_as_planner_step_rejected() -> None:
    src = use_station_candidate_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("route_plan", "if_then_policy")))
    assert MicroOperationBlockReason.ACTION_SURFACE_IS_COMMAND in run.blocked_reasons


def test_micro1_provider_hint_action_truth_metadata_rejected() -> None:
    src = provider_hint_basis_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("provider_truth", "selected_action")))
    assert MicroOperationBlockReason.PROVIDER_HINT_AS_TRUTH_DETECTED in run.blocked_reasons
    assert MicroOperationBlockReason.ACTION_SURFACE_IS_COMMAND in run.blocked_reasons


def test_micro1_world_submission_attempt_rejected() -> None:
    src = inspect_unknown_resource_fixture()
    run = build_micro_operation_frame(replace(src, world_submission_attempt=True))
    assert MicroOperationBlockReason.WORLD_SUBMISSION_ATTEMPTED in run.blocked_reasons
    assert run.operation is not None
    assert run.operation.authority_flags.can_execute_world_action is False


def test_micro1_rejects_fake_ap01_request_ref_created_locally() -> None:
    src = ap01_lineage_reference_fixture()
    run = build_micro_operation_frame(
        replace(src, lineage=replace(src.lineage, ap01_request_ref="ap01:local:tmp-1"))  # type: ignore[arg-type]
    )
    assert MicroOperationBlockReason.AP01_EMISSION_ATTEMPTED in run.blocked_reasons


def test_micro1_expected_effect_is_not_observed_effect() -> None:
    run = build_micro_operation_frame(inspect_unknown_resource_fixture())
    assert run.operation is not None
    assert run.operation.expected_effects.expected_effect_refs
    assert run.operation.lineage is not None
    assert run.operation.lineage.observed_effect_refs == ()
    assert run.operation.status is not MicroOperationStatus.EFFECT_OBSERVED
    assert run.operation.status is not MicroOperationStatus.SUCCEEDED


def test_micro1_status_succeeded_cannot_be_forced_without_effect() -> None:
    src = inspect_unknown_resource_fixture()
    run = build_micro_operation_frame(replace(src, status_hint=MicroOperationStatus.SUCCEEDED))
    assert MicroOperationBlockReason.SUCCESS_WITHOUT_EFFECT_REF in run.blocked_reasons
    assert run.status is MicroValidationStatus.BLOCKED


def test_micro1_blocked_operation_requires_residue_or_explicit_noop() -> None:
    src = inspect_unknown_resource_fixture()
    blocked = build_micro_operation_frame(replace(src, metadata_refs=("selected_action",)))
    assert blocked.operation is not None
    assert blocked.operation.status is MicroOperationStatus.BLOCKED
    assert MicroOperationBlockReason.RESIDUE_MISSING_AFTER_FAILURE in blocked.blocked_reasons

    noop = build_micro_operation_frame(
        MicroOperationInput(
            operation_id="micro1:noop",
            operation_kind=MicroOperationKind.CUSTOM_PUBLIC_OPERATION,
        )
    )
    assert noop.status is MicroValidationStatus.NOOP


def test_micro1_macro_task_ref_requires_child_operations() -> None:
    base = build_micro_operation_frame(inspect_unknown_resource_fixture()).operation
    assert base is not None
    run = build_micro_operation_graph(
        MicroOperationGraphInput(
            graph_id="micro1:graph:macro_single",
            root_pressure_refs=("pressure:test",),
            operations=(base,),
            dependency_edges=(),
            macro_task_ref="build_factory",
        )
    )
    assert run.status is MicroValidationStatus.BLOCKED
    assert MicroOperationBlockReason.MACRO_ACTION_REQUIRES_DECOMPOSITION in run.blocked_reasons


def test_micro1_graph_does_not_advance_past_unverified_dependency() -> None:
    run = build_micro_operation_graph(bounded_graph_fixture())
    assert run.graph is not None
    assert run.graph.graph_status.value == "partial"
    assert run.graph.blocked_edges


def test_micro1_cost_winner_metadata_cannot_authorize_operation() -> None:
    src = provider_hint_basis_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("cost_winner:best_path", "winner_permission:go")))
    assert MicroOperationBlockReason.COST_WINNER_AS_PERMISSION_DETECTED in run.blocked_reasons


def test_micro1_recipe_candidate_metadata_cannot_encode_script() -> None:
    src = provider_hint_basis_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("factory_steps", "required_action_order")))
    assert MicroOperationBlockReason.RECIPE_CANDIDATE_AS_SCRIPT_DETECTED in run.blocked_reasons


def test_micro1_repeated_success_does_not_mature_option_or_skill() -> None:
    src = ap01_lineage_reference_fixture()
    succeeded = build_micro_operation_frame(
        replace(
            src,
            lineage=replace(src.lineage, observed_effect_refs=("effect:identity_candidate_updated",)),  # type: ignore[arg-type]
            status_hint=MicroOperationStatus.SUCCEEDED,
        )
    )
    repeated = build_micro_operation_frame(
        replace(
            src,
            lineage=replace(src.lineage, observed_effect_refs=("effect:identity_candidate_updated",)),  # type: ignore[arg-type]
            status_hint=MicroOperationStatus.SUCCEEDED,
        )
    )
    for item in (succeeded, repeated):
        assert item.operation is not None
        flags = item.operation.authority_flags
        assert flags.can_mature_skill is False
        assert flags.can_claim_automation is False


def test_micro1_world_submission_payload_rejected_in_nested_metadata() -> None:
    src = inspect_unknown_resource_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("payload:{'world_submission':true}",)))
    assert MicroOperationBlockReason.ACTION_SURFACE_IS_COMMAND in run.blocked_reasons


def test_micro1_hidden_backend_precondition_payload_rejected_in_metadata() -> None:
    src = inspect_unknown_resource_fixture()
    run = build_micro_operation_frame(replace(src, metadata_refs=("payload:{'backend_hidden_precondition':'x'}",)))
    assert MicroOperationBlockReason.HIDDEN_PRECONDITION_DETECTED in run.blocked_reasons


def test_micro1_passive_event_marker_required_for_uncorrelated_effect() -> None:
    src = inspect_unknown_resource_fixture()
    with_effect = replace(src, lineage=replace(src.lineage, observed_effect_refs=("effect:identity_candidate_updated",)))  # type: ignore[arg-type]
    blocked = build_micro_operation_frame(replace(with_effect, expected_effects=replace(src.expected_effects, passive_event_allowed=False)))
    assert MicroOperationBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER in blocked.blocked_reasons
    allowed = build_micro_operation_frame(replace(with_effect, expected_effects=replace(src.expected_effects, passive_event_allowed=True)))
    assert MicroOperationBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER not in allowed.blocked_reasons


def test_micro1_operation_graph_preserves_blocked_edge_residue() -> None:
    failed = build_micro_operation_frame(failed_operation_residue_fixture()).operation
    next_op = build_micro_operation_frame(move_toward_resource_fixture()).operation
    assert failed is not None and next_op is not None
    run = build_micro_operation_graph(
        MicroOperationGraphInput(
            graph_id="micro1:graph:residue_blocked_edge",
            root_pressure_refs=("pressure:inspect_again",),
            operations=(failed, next_op),
            dependency_edges=((failed.operation_id, next_op.operation_id),),
            macro_task_ref="macro:repair_chain",
        )
    )
    assert run.graph is not None
    assert run.graph.blocked_edges
    assert "residue:inspect_failed" in run.graph.residue_refs


def test_micro1_language_testimony_basis_not_operation_truth() -> None:
    src = inspect_unknown_resource_fixture()
    run = build_micro_operation_frame(
        replace(
            src,
            basis=replace(
                src.basis,
                language_testimony_refs=("language:testimony:maybe_ore",),
                channel_refs={"language_contact": ("language:testimony:maybe_ore",)},
            ),
        )
    )
    assert run.operation is not None
    assert run.operation.basis.language_testimony_refs
    assert run.operation.status is not MicroOperationStatus.SUCCEEDED
