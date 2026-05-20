from __future__ import annotations

from dataclasses import asdict

from .models import (
    Micro1AuthorityFlags,
    MicroOperationBasis,
    MicroOperationBlockReason,
    MicroOperationCounters,
    MicroOperationFrame,
    MicroOperationGraph,
    MicroOperationGraphInput,
    MicroOperationGraphStatus,
    MicroOperationInput,
    MicroOperationKind,
    MicroOperationLineage,
    MicroOperationStatus,
    MicroOperationValidationResult,
    MicroValidationStatus,
)

_MACRO_ACTION_TOKENS: tuple[str, ...] = (
    "build_factory",
    "solve_quest",
    "complete_chain",
    "automate_line",
    "craft_machine",
    "build_base",
    "follow_route",
    "repair_system",
)
_COMMAND_TOKENS: tuple[str, ...] = (
    "selected_action",
    "command:",
    "execute_now",
    "ap01_request",
    "ap01_create",
    "world_submit",
    "world_submission",
    "submit_world_action",
    "if_then_policy",
    "behavior_tree",
    "route_plan",
)
_HIDDEN_TOKENS: tuple[str, ...] = (
    "hidden",
    "backend",
    "scenario",
    "eval",
    "private",
)
_PROVIDER_TRUTH_TOKENS: tuple[str, ...] = (
    "provider_truth",
    "oracle",
    "definitive",
    "confirmed",
    "true_recipe",
    "mature_skill",
    "mature_option",
    "automation_claim",
    "value_assigned",
    "assign_value",
)
_QUEST_PERMISSION_TOKENS: tuple[str, ...] = (
    "quest_permission",
    "goal_authority",
    "must_do",
)
_COST_PERMISSION_TOKENS: tuple[str, ...] = (
    "cost_winner",
    "winner_permission",
)
_RECIPE_SCRIPT_TOKENS: tuple[str, ...] = (
    "recipe_script",
    "factory_steps",
    "ordered_plan",
    "required_action_order",
)


def build_micro_operation_frame(operation_input: MicroOperationInput) -> MicroOperationValidationResult:
    blocked: list[MicroOperationBlockReason] = []
    warnings: list[str] = []
    trace: list[str] = ["micro1:build:start"]
    noop_candidate = _is_noop(operation_input)

    counters = MicroOperationCounters(operation_count=1)
    count_data = asdict(counters)

    if not operation_input.operation_id:
        blocked.append(MicroOperationBlockReason.MISSING_TARGET_AFFORDANCE)

    if not noop_candidate and not validate_public_basis(operation_input):
        blocked.append(MicroOperationBlockReason.MISSING_PUBLIC_PRESSURE_BASIS)
        count_data["missing_public_basis_count"] += 1

    if not noop_candidate and not validate_target_affordance(operation_input):
        blocked.append(MicroOperationBlockReason.MISSING_TARGET_AFFORDANCE)

    if not noop_candidate and not validate_expected_effect_basis(operation_input):
        blocked.append(MicroOperationBlockReason.MISSING_EXPECTED_EFFECT)

    if not validate_action_surface_is_not_command(operation_input):
        blocked.append(MicroOperationBlockReason.ACTION_SURFACE_IS_COMMAND)

    if operation_input.ap01_emission_attempt:
        blocked.append(MicroOperationBlockReason.AP01_EMISSION_ATTEMPTED)
        count_data["ap01_emission_attempt_count"] += 1

    if operation_input.world_submission_attempt:
        blocked.append(MicroOperationBlockReason.WORLD_SUBMISSION_ATTEMPTED)
        count_data["world_submission_attempt_count"] += 1

    if not validate_macro_action_decomposition(operation_input):
        blocked.append(MicroOperationBlockReason.MACRO_ACTION_REQUIRES_DECOMPOSITION)
        count_data["macro_action_block_count"] += 1

    if reject_hidden_preconditions(operation_input):
        blocked.append(MicroOperationBlockReason.HIDDEN_PRECONDITION_DETECTED)
        count_data["hidden_precondition_block_count"] += 1

    if reject_provider_hint_as_truth(operation_input):
        blocked.append(MicroOperationBlockReason.PROVIDER_HINT_AS_TRUTH_DETECTED)
        count_data["provider_truth_block_count"] += 1

    if reject_quest_objective_as_permission(operation_input):
        blocked.append(MicroOperationBlockReason.QUEST_OBJECTIVE_AS_PERMISSION_DETECTED)
        count_data["quest_permission_block_count"] += 1

    if reject_cost_winner_as_permission(operation_input):
        blocked.append(MicroOperationBlockReason.COST_WINNER_AS_PERMISSION_DETECTED)
        count_data["cost_permission_block_count"] += 1

    if reject_recipe_candidate_as_script(operation_input):
        blocked.append(MicroOperationBlockReason.RECIPE_CANDIDATE_AS_SCRIPT_DETECTED)
        count_data["recipe_script_block_count"] += 1

    lineage = operation_input.lineage
    if lineage is None:
        lineage = MicroOperationLineage(
            operation_id=operation_input.operation_id,
            pressure_ref=operation_input.basis.pressure_refs[0] if operation_input.basis.pressure_refs else None,
            target_affordance_ref=operation_input.target_affordance_refs[0] if operation_input.target_affordance_refs else None,
            action_surface_ref=operation_input.action_surface_refs[0] if operation_input.action_surface_refs else None,
        )

    if not validate_ap01_lineage_reference_only(lineage):
        blocked.append(MicroOperationBlockReason.AP01_EMISSION_ATTEMPTED)
        count_data["ap01_emission_attempt_count"] += 1

    effect_lineage_ok = validate_observed_effect_lineage(operation_input)
    if not effect_lineage_ok:
        blocked.append(MicroOperationBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER)
        count_data["effect_without_request_count"] += 1

    if not validate_operation_success_requires_effect(operation_input):
        blocked.append(MicroOperationBlockReason.SUCCESS_WITHOUT_EFFECT_REF)
        count_data["success_without_effect_count"] += 1

    blocked_unique = tuple(dict.fromkeys(blocked))
    status = _derive_operation_status(operation_input=operation_input, blocked_reasons=blocked_unique, effect_lineage_ok=effect_lineage_ok)
    if status in {MicroOperationStatus.BLOCKED, MicroOperationStatus.FAILED, MicroOperationStatus.RESIDUE_OPEN, MicroOperationStatus.UNRESOLVED}:
        if not _has_any_residue(operation_input):
            blocked.append(MicroOperationBlockReason.RESIDUE_MISSING_AFTER_FAILURE)
            count_data["residue_missing_after_failure_count"] += 1
            blocked_unique = tuple(dict.fromkeys(blocked))
            if status is not MicroOperationStatus.UNRESOLVED:
                status = _derive_operation_status(operation_input=operation_input, blocked_reasons=blocked_unique, effect_lineage_ok=effect_lineage_ok)

    residue_refs = tuple(
        dict.fromkeys(
            (*lineage.residue_refs, *(ref for frame in operation_input.residue_frames for ref in (frame.residue_id, *frame.next_pressure_refs)))
        )
    )
    count_data["residue_count"] = len(residue_refs)
    if status in {MicroOperationStatus.CANDIDATE_BASIS_READY, MicroOperationStatus.REQUEST_PUBLISHED_ELSEWHERE, MicroOperationStatus.EFFECT_OBSERVED, MicroOperationStatus.SUCCEEDED}:
        count_data["ready_operation_count"] = 1
    if status in {MicroOperationStatus.BLOCKED, MicroOperationStatus.BASIS_INCOMPLETE, MicroOperationStatus.UNRESOLVED, MicroOperationStatus.FAILED, MicroOperationStatus.RESIDUE_OPEN}:
        count_data["blocked_operation_count"] = 1

    trace.extend(
        (
            f"micro1:status:{status.value}",
            f"micro1:blocked_count:{len(blocked_unique)}",
            f"micro1:residue_count:{count_data['residue_count']}",
        )
    )

    frame = MicroOperationFrame(
        operation_id=operation_input.operation_id,
        operation_kind=operation_input.operation_kind,
        status=status,
        basis=operation_input.basis,
        target_affordance_refs=operation_input.target_affordance_refs,
        action_surface_refs=operation_input.action_surface_refs,
        constraints=operation_input.constraints,
        expected_effects=operation_input.expected_effects,
        lineage=lineage,
        residue_frame_refs=tuple(item.residue_id for item in operation_input.residue_frames),
        update_refs=lineage.update_refs,
        composition_parent_ref=operation_input.composition_parent_ref,
        composition_child_refs=operation_input.composition_child_refs,
        source_refs=tuple(dict.fromkeys((*operation_input.basis.source_refs, *lineage.trace_refs))),
        uncertainty_refs=tuple(dict.fromkeys((*operation_input.basis.uncertainty_refs, *operation_input.constraints.constraint_uncertainty_refs, *operation_input.expected_effects.uncertainty_refs))),
        blocked_reasons=blocked_unique,
        authority_flags=Micro1AuthorityFlags(),
        validation_trace=tuple(trace),
    )

    result_status = _derive_validation_status(status=status, blocked_reasons=blocked_unique)

    if noop_candidate and not blocked_unique:
        result_status = MicroValidationStatus.NOOP

    return MicroOperationValidationResult(
        status=result_status,
        operation_status=status,
        blocked_reasons=blocked_unique,
        warnings=tuple(dict.fromkeys(warnings)),
        counters=MicroOperationCounters(**count_data),
        operation=frame,
        graph=None,
        authority_flags=Micro1AuthorityFlags(),
        conformance_trace=tuple(trace),
    )


def validate_micro_operation_frame(frame: MicroOperationFrame) -> MicroOperationValidationResult:
    input_obj = MicroOperationInput(
        operation_id=frame.operation_id,
        operation_kind=frame.operation_kind,
        basis=frame.basis,
        target_affordance_refs=frame.target_affordance_refs,
        action_surface_refs=frame.action_surface_refs,
        constraints=frame.constraints,
        expected_effects=frame.expected_effects,
        lineage=frame.lineage,
        residue_frames=(),
        status_hint=frame.status,
        composition_parent_ref=frame.composition_parent_ref,
        composition_child_refs=frame.composition_child_refs,
    )
    return build_micro_operation_frame(input_obj)


def build_micro_operation_graph(graph_input: MicroOperationGraphInput) -> MicroOperationValidationResult:
    blocked: list[MicroOperationBlockReason] = []
    trace = ["micro1:graph:build:start"]
    count_data = asdict(MicroOperationCounters(operation_count=len(graph_input.operations)))
    count_data["composition_edge_count"] = len(graph_input.dependency_edges)

    operation_map = {item.operation_id: item for item in graph_input.operations}
    blocked_edges: list[tuple[str, str]] = []
    unresolved_refs: list[str] = []

    for parent, child in graph_input.dependency_edges:
        parent_op = operation_map.get(parent)
        child_op = operation_map.get(child)
        if parent_op is None or child_op is None:
            blocked_edges.append((parent, child))
            unresolved_refs.append(f"missing_node:{parent}->{child}")
            continue
        if parent_op.status not in {MicroOperationStatus.EFFECT_OBSERVED, MicroOperationStatus.SUCCEEDED}:
            blocked_edges.append((parent, child))
            unresolved_refs.append(f"unverified_intermediate:{parent}")

    if blocked_edges:
        count_data["unverified_intermediate_count"] = len(blocked_edges)

    if graph_input.macro_task_ref and (not graph_input.operations or len(graph_input.operations) < 2):
        blocked.append(MicroOperationBlockReason.MACRO_ACTION_REQUIRES_DECOMPOSITION)
        count_data["macro_action_block_count"] += 1

    if graph_input.macro_task_ref and _contains_any(graph_input.macro_task_ref.lower(), _MACRO_ACTION_TOKENS):
        if not graph_input.operations:
            blocked.append(MicroOperationBlockReason.MACRO_ACTION_REQUIRES_DECOMPOSITION)

    blocked_unique = tuple(dict.fromkeys(blocked))
    graph_status = (
        MicroOperationGraphStatus.BLOCKED
        if blocked_unique
        else (MicroOperationGraphStatus.PARTIAL if blocked_edges else MicroOperationGraphStatus.READY)
    )

    graph = MicroOperationGraph(
        graph_id=graph_input.graph_id,
        root_pressure_refs=graph_input.root_pressure_refs,
        operation_refs=tuple(item.operation_id for item in graph_input.operations),
        dependency_edges=graph_input.dependency_edges,
        verified_intermediate_refs=graph_input.verified_intermediate_refs,
        blocked_edges=tuple(blocked_edges),
        residue_refs=tuple(dict.fromkeys(ref for item in graph_input.operations for ref in item.residue_frame_refs)),
        unresolved_refs=tuple(dict.fromkeys(unresolved_refs)),
        macro_task_ref=graph_input.macro_task_ref,
        macro_task_decomposed=bool(graph_input.macro_task_ref and len(graph_input.operations) >= 2),
        graph_status=graph_status,
        authority_flags=Micro1AuthorityFlags(),
    )

    result_status = (
        MicroValidationStatus.BLOCKED
        if blocked_unique
        else (MicroValidationStatus.PARTIAL if blocked_edges else MicroValidationStatus.ACCEPTED)
    )

    trace.append(f"micro1:graph:status:{graph_status.value}")

    return MicroOperationValidationResult(
        status=result_status,
        operation_status=None,
        blocked_reasons=blocked_unique,
        warnings=(),
        counters=MicroOperationCounters(**count_data),
        operation=None,
        graph=graph,
        authority_flags=Micro1AuthorityFlags(),
        conformance_trace=tuple(trace),
    )


def validate_micro_operation_graph(graph: MicroOperationGraph) -> MicroOperationValidationResult:
    placeholder_ops = tuple(
        MicroOperationFrame(
            operation_id=op_id,
            operation_kind=MicroOperationKind.CUSTOM_PUBLIC_OPERATION,
            status=MicroOperationStatus.EFFECT_OBSERVED,
            basis=MicroOperationBasis(),
        )
        for op_id in graph.operation_refs
    )
    input_obj = MicroOperationGraphInput(
        graph_id=graph.graph_id,
        root_pressure_refs=graph.root_pressure_refs,
        operations=placeholder_ops,
        dependency_edges=graph.dependency_edges,
        verified_intermediate_refs=graph.verified_intermediate_refs,
        macro_task_ref=graph.macro_task_ref,
    )
    return build_micro_operation_graph(input_obj)


def validate_public_basis(operation_input: MicroOperationInput) -> bool:
    basis = operation_input.basis
    return bool(
        basis.pressure_refs
        or basis.need_refs
        or basis.body_pressure_refs
        or basis.public_observation_refs
        or basis.provider_hint_refs
        or basis.knowledge_hint_refs
        or basis.language_testimony_refs
        or basis.sensory_candidate_refs
    )


def validate_target_affordance(operation_input: MicroOperationInput) -> bool:
    return bool(operation_input.target_affordance_refs and operation_input.action_surface_refs)


def validate_action_surface_is_not_command(operation_input: MicroOperationInput) -> bool:
    hay = " ".join((*operation_input.action_surface_refs, *operation_input.metadata_refs)).lower()
    return not _contains_any(hay, _COMMAND_TOKENS)


def validate_expected_effect_basis(operation_input: MicroOperationInput) -> bool:
    return bool(operation_input.expected_effects.expected_effect_refs)


def validate_ap01_lineage_reference_only(lineage: MicroOperationLineage) -> bool:
    if lineage.ap01_request_ref is None:
        return True
    lowered = lineage.ap01_request_ref.lower()
    return lowered.startswith("ap01:req:") or lowered.startswith("request:published:")


def validate_observed_effect_lineage(operation_input: MicroOperationInput) -> bool:
    lineage = operation_input.lineage
    if lineage is None or not lineage.observed_effect_refs:
        return True
    if lineage.ap01_request_ref:
        return True
    return operation_input.expected_effects.passive_event_allowed


def validate_operation_success_requires_effect(operation_input: MicroOperationInput) -> bool:
    if operation_input.status_hint is not MicroOperationStatus.SUCCEEDED:
        return True
    lineage = operation_input.lineage
    return bool(lineage is not None and lineage.observed_effect_refs)


def validate_failure_preserves_residue(operation_input: MicroOperationInput) -> bool:
    if operation_input.status_hint not in {MicroOperationStatus.FAILED, MicroOperationStatus.BLOCKED, MicroOperationStatus.RESIDUE_OPEN}:
        return True
    lineage = operation_input.lineage
    has_lineage_residue = bool(lineage and (lineage.residue_refs or lineage.next_pressure_refs))
    has_residue_frames = bool(operation_input.residue_frames)
    return has_lineage_residue or has_residue_frames


def validate_macro_action_decomposition(operation_input: MicroOperationInput) -> bool:
    joined = " ".join(
        (
            operation_input.operation_kind.value,
            operation_input.macro_task_ref or "",
            *operation_input.target_affordance_refs,
            *operation_input.action_surface_refs,
            *operation_input.metadata_refs,
        )
    ).lower()
    if _contains_any(joined, _MACRO_ACTION_TOKENS):
        return bool(operation_input.composition_child_refs)
    return True


def reject_hidden_preconditions(operation_input: MicroOperationInput) -> bool:
    joined = " ".join(
        (
            *operation_input.constraints.precondition_refs,
            *operation_input.constraints.required_capability_refs,
            *operation_input.constraints.required_resource_refs,
            *operation_input.metadata_refs,
        )
    ).lower()
    return _contains_any(joined, _HIDDEN_TOKENS)


def reject_provider_hint_as_truth(operation_input: MicroOperationInput) -> bool:
    joined = " ".join(
        (
            *operation_input.basis.provider_hint_refs,
            *operation_input.basis.knowledge_hint_refs,
            *operation_input.metadata_refs,
            *operation_input.expected_effects.success_criteria_refs,
        )
    ).lower()
    return _contains_any(joined, _PROVIDER_TRUTH_TOKENS)


def reject_quest_objective_as_permission(operation_input: MicroOperationInput) -> bool:
    joined = " ".join(
        (
            *operation_input.basis.knowledge_hint_refs,
            *operation_input.basis.provider_hint_refs,
            *operation_input.constraints.precondition_refs,
            *operation_input.metadata_refs,
        )
    ).lower()
    return "quest" in joined and _contains_any(joined, _QUEST_PERMISSION_TOKENS)


def reject_cost_winner_as_permission(operation_input: MicroOperationInput) -> bool:
    joined = " ".join(
        (
            *operation_input.basis.provider_hint_refs,
            *operation_input.constraints.precondition_refs,
            *operation_input.metadata_refs,
        )
    ).lower()
    return _contains_any(joined, _COST_PERMISSION_TOKENS)


def reject_recipe_candidate_as_script(operation_input: MicroOperationInput) -> bool:
    lineage = operation_input.lineage
    joined = " ".join(
        (
            *operation_input.basis.knowledge_hint_refs,
            *operation_input.metadata_refs,
            *(lineage.trace_refs if lineage else ()),
        )
    ).lower()
    return _contains_any(joined, _RECIPE_SCRIPT_TOKENS)


def summarize_micro_operation_conformance(result: MicroOperationValidationResult) -> dict[str, object]:
    operation = result.operation
    graph = result.graph
    payload: dict[str, object] = {
        "status": result.status.value,
        "operation_status": result.operation_status.value if result.operation_status is not None else None,
        "blocked_reasons": tuple(item.value for item in result.blocked_reasons),
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "authority_flags": asdict(result.authority_flags),
    }
    if operation is not None:
        payload["operation"] = {
            "operation_id": operation.operation_id,
            "operation_kind": operation.operation_kind.value,
            "status": operation.status.value,
            "target_affordance_refs": operation.target_affordance_refs,
            "action_surface_refs": operation.action_surface_refs,
            "residue_frame_refs": operation.residue_frame_refs,
            "validation_trace": operation.validation_trace,
        }
    if graph is not None:
        payload["graph"] = {
            "graph_id": graph.graph_id,
            "graph_status": graph.graph_status.value,
            "operation_refs": graph.operation_refs,
            "dependency_edges": graph.dependency_edges,
            "blocked_edges": graph.blocked_edges,
            "unresolved_refs": graph.unresolved_refs,
        }
    return payload


def _derive_operation_status(
    *,
    operation_input: MicroOperationInput,
    blocked_reasons: tuple[MicroOperationBlockReason, ...],
    effect_lineage_ok: bool,
) -> MicroOperationStatus:
    if blocked_reasons:
        only_effect_lineage_gap = all(reason is MicroOperationBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER for reason in blocked_reasons)
        if only_effect_lineage_gap:
            return MicroOperationStatus.UNRESOLVED
        if MicroOperationBlockReason.MISSING_PUBLIC_PRESSURE_BASIS in blocked_reasons:
            return MicroOperationStatus.BASIS_INCOMPLETE
        return MicroOperationStatus.BLOCKED

    lineage = operation_input.lineage
    if operation_input.status_hint is MicroOperationStatus.SUCCEEDED:
        return MicroOperationStatus.SUCCEEDED
    if operation_input.status_hint in {MicroOperationStatus.FAILED, MicroOperationStatus.RESIDUE_OPEN}:
        return operation_input.status_hint
    if lineage is not None and lineage.ap01_request_ref is not None:
        if lineage.observed_effect_refs:
            return MicroOperationStatus.EFFECT_OBSERVED
        return MicroOperationStatus.REQUEST_PUBLISHED_ELSEWHERE
    if lineage is not None and lineage.observed_effect_refs and not effect_lineage_ok:
        return MicroOperationStatus.UNRESOLVED
    if operation_input.expected_effects.expected_effect_refs and validate_public_basis(operation_input):
        return MicroOperationStatus.CANDIDATE_BASIS_READY
    return MicroOperationStatus.PROPOSED


def _contains_any(haystack: str, tokens: tuple[str, ...]) -> bool:
    return any(token in haystack for token in tokens)


def _is_noop(operation_input: MicroOperationInput) -> bool:
    return (
        not validate_public_basis(operation_input)
        and not operation_input.target_affordance_refs
        and not operation_input.action_surface_refs
        and not operation_input.expected_effects.expected_effect_refs
        and operation_input.status_hint is MicroOperationStatus.PROPOSED
    )


def _derive_validation_status(
    *,
    status: MicroOperationStatus,
    blocked_reasons: tuple[MicroOperationBlockReason, ...],
) -> MicroValidationStatus:
    if not blocked_reasons:
        if status in {MicroOperationStatus.UNRESOLVED, MicroOperationStatus.RESIDUE_OPEN, MicroOperationStatus.FAILED, MicroOperationStatus.BASIS_INCOMPLETE}:
            return MicroValidationStatus.PARTIAL
        return MicroValidationStatus.ACCEPTED

    if status is MicroOperationStatus.UNRESOLVED and all(
        reason in {MicroOperationBlockReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER, MicroOperationBlockReason.RESIDUE_MISSING_AFTER_FAILURE}
        for reason in blocked_reasons
    ):
        return MicroValidationStatus.PARTIAL

    return MicroValidationStatus.BLOCKED


def _has_any_residue(operation_input: MicroOperationInput) -> bool:
    lineage = operation_input.lineage
    return bool(
        (lineage and (lineage.residue_refs or lineage.next_pressure_refs))
        or operation_input.residue_frames
    )
