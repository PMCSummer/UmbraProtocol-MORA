from __future__ import annotations

from dataclasses import replace

from substrate.a_line_normalization import ALineNormalizationResult
from substrate.m_minimal import MMinimalResult
from substrate.n_minimal import NMinimalResult
from substrate.self_contour import SMinimalContourResult
from substrate.t01_semantic_field.models import T01ActiveFieldResult, T01SceneStatus
from substrate.t02_relation_binding.models import (
    ForbiddenT02Shortcut,
    T02AssemblyMode,
    T02BindingStatus,
    T02ConflictRecord,
    T02ConstrainedSceneResult,
    T02ConstrainedSceneState,
    T02ConstrainedSceneStatus,
    T02ConstraintObject,
    T02ConstraintPolarity,
    T02GateDecision,
    T02Operation,
    T02PropagationEffectType,
    T02PropagationRecord,
    T02PropagationStatus,
    T02RelationBinding,
    T02ScopeMarker,
    T02Telemetry,
)
from substrate.world_entry_contract import WorldEntryContractResult

_REVALIDATE_ACTIONS = {
    "run_selective_revalidation",
    "run_bounded_revalidation",
    "suspend_until_revalidation_basis",
    "halt_reuse_and_rebuild_scope",
}


def build_t02_constrained_scene(
    *,
    tick_id: str,
    t01_result: T01ActiveFieldResult,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    c05_validity_action: str,
    assembly_mode: T02AssemblyMode = T02AssemblyMode.BOUNDED_CONSTRAINT_PROPAGATION,
    preserve_conflicts: bool = True,
    enforce_stop_conditions: bool = True,
    source_lineage: tuple[str, ...] = (),
) -> T02ConstrainedSceneResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if not isinstance(t01_result, T01ActiveFieldResult):
        raise TypeError("t01_result must be T01ActiveFieldResult")
    if not isinstance(world_entry_result, WorldEntryContractResult):
        raise TypeError("world_entry_result must be WorldEntryContractResult")
    if not isinstance(s_minimal_result, SMinimalContourResult):
        raise TypeError("s_minimal_result must be SMinimalContourResult")
    if not isinstance(a_line_result, ALineNormalizationResult):
        raise TypeError("a_line_result must be ALineNormalizationResult")
    if not isinstance(m_minimal_result, MMinimalResult):
        raise TypeError("m_minimal_result must be MMinimalResult")
    if not isinstance(n_minimal_result, NMinimalResult):
        raise TypeError("n_minimal_result must be NMinimalResult")

    raw_scene_nodes = tuple(entity.entity_id for entity in t01_result.state.active_entities)
    raw_relation_candidates = tuple(
        (edge.source_entity_id, edge.relation_type, edge.target_entity_id)
        for edge in t01_result.state.relation_edges
    )
    authority_floor = _authority_floor(
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
    )
    bindings = _build_relation_bindings(
        raw_relation_candidates=raw_relation_candidates,
        authority_floor=authority_floor,
        t01_result=t01_result,
        world_entry_result=world_entry_result,
        a_line_result=a_line_result,
        n_minimal_result=n_minimal_result,
        assembly_mode=assembly_mode,
    )
    constraints = _build_constraint_objects(
        t01_result=t01_result,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        c05_validity_action=c05_validity_action,
        enforce_stop_conditions=enforce_stop_conditions,
    )
    propagations = _build_propagation_records(
        bindings=bindings,
        constraints=constraints,
        authority_floor=authority_floor,
        t01_result=t01_result,
        c05_validity_action=c05_validity_action,
        assembly_mode=assembly_mode,
        enforce_stop_conditions=enforce_stop_conditions,
    )
    conflicts = _build_conflict_records(
        bindings=bindings,
        t01_result=t01_result,
        preserve_conflicts=preserve_conflicts,
    )
    narrowed_roles = _build_narrowed_role_candidates(
        t01_result=t01_result,
        bindings=bindings,
        propagations=propagations,
    )
    scene_status = _derive_constrained_scene_status(
        raw_scene_nodes=raw_scene_nodes,
        bindings=bindings,
        conflicts=conflicts,
        propagations=propagations,
        authority_floor=authority_floor,
        c05_validity_action=c05_validity_action,
        t01_scene_status=t01_result.state.scene_status,
    )
    operations = _derive_operations(
        bindings=bindings,
        constraints=constraints,
        propagations=propagations,
        conflicts=conflicts,
        preserve_conflicts=preserve_conflicts,
        enforce_stop_conditions=enforce_stop_conditions,
    )
    state = T02ConstrainedSceneState(
        constrained_scene_id=f"t02-constrained-scene:{tick_id}",
        source_t01_scene_id=t01_result.state.scene_id,
        source_t01_scene_status=t01_result.state.scene_status.value,
        raw_scene_nodes=raw_scene_nodes,
        raw_relation_candidates=raw_relation_candidates,
        relation_bindings=bindings,
        constraint_objects=constraints,
        propagation_records=propagations,
        conflict_records=conflicts,
        narrowed_role_candidates=narrowed_roles,
        scene_status=scene_status,
        operations_applied=operations,
        source_authority_tags=tuple(
            dict.fromkeys(
                (
                    *t01_result.state.source_authority_tags,
                    f"T02:authority_floor={authority_floor:.3f}",
                    f"C05:validity_action={c05_validity_action}",
                )
            )
        ),
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *t01_result.state.source_lineage,
                    *world_entry_result.episode.source_lineage,
                    *s_minimal_result.state.source_lineage,
                    *a_line_result.state.source_lineage,
                    *m_minimal_result.state.source_lineage,
                    *n_minimal_result.state.source_lineage,
                )
            )
        ),
        provenance="t02.relation_binding.constraint_propagation",
    )
    gate = _build_gate(
        state=state,
        assembly_mode=assembly_mode,
        preserve_conflicts=preserve_conflicts,
        enforce_stop_conditions=enforce_stop_conditions,
        authority_floor=authority_floor,
    )
    scope_marker = _build_scope_marker()
    telemetry = T02Telemetry(
        constrained_scene_id=state.constrained_scene_id,
        source_t01_scene_id=state.source_t01_scene_id,
        scene_status=state.scene_status,
        relation_bindings_count=len(state.relation_bindings),
        confirmed_bindings_count=sum(
            1 for item in state.relation_bindings if item.status is T02BindingStatus.CONFIRMED
        ),
        provisional_bindings_count=sum(
            1 for item in state.relation_bindings if item.status is T02BindingStatus.PROVISIONAL
        ),
        blocked_bindings_count=sum(
            1 for item in state.relation_bindings if item.status is T02BindingStatus.BLOCKED
        ),
        conflicted_bindings_count=sum(
            1
            for item in state.relation_bindings
            if item.status in {T02BindingStatus.CONFLICTED, T02BindingStatus.INCOMPATIBLE}
        ),
        constraint_objects_count=len(state.constraint_objects),
        propagation_records_count=len(state.propagation_records),
        stopped_propagation_count=sum(
            1 for item in state.propagation_records if item.status is T02PropagationStatus.STOPPED
        ),
        conflict_records_count=len(state.conflict_records),
        pre_verbal_constraint_consumer_ready=gate.pre_verbal_constraint_consumer_ready,
        no_clean_binding_commit=gate.no_clean_binding_commit,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return T02ConstrainedSceneResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="t02.first_bounded_relation_binding_constraint_propagation_slice",
    )


def evolve_t02_constrained_scene(
    *,
    result: T02ConstrainedSceneResult,
    operation: T02Operation,
    binding_id: str | None = None,
    role_id: str | None = None,
    candidate_id: str | None = None,
) -> T02ConstrainedSceneResult:
    if not isinstance(result, T02ConstrainedSceneResult):
        raise TypeError("result must be T02ConstrainedSceneResult")
    if not isinstance(operation, T02Operation):
        raise TypeError("operation must be T02Operation")

    state = result.state
    bindings = list(state.relation_bindings)
    narrowed = list(state.narrowed_role_candidates)
    scene_status = state.scene_status

    if operation is T02Operation.CONFIRM_BINDING and binding_id:
        bindings = [
            replace(item, status=T02BindingStatus.CONFIRMED)
            if item.binding_id == binding_id
            else item
            for item in bindings
        ]
    elif operation is T02Operation.KEEP_PROVISIONAL and binding_id:
        bindings = [
            replace(item, status=T02BindingStatus.PROVISIONAL)
            if item.binding_id == binding_id
            else item
            for item in bindings
        ]
    elif operation is T02Operation.BLOCK_BINDING and binding_id:
        bindings = [
            replace(item, status=T02BindingStatus.BLOCKED)
            if item.binding_id == binding_id
            else item
            for item in bindings
        ]
        scene_status = T02ConstrainedSceneStatus.LOCAL_CONSTRAINT_ONLY
    elif operation is T02Operation.MARK_INCOMPATIBLE and binding_id:
        bindings = [
            replace(item, status=T02BindingStatus.INCOMPATIBLE)
            if item.binding_id == binding_id
            else item
            for item in bindings
        ]
        scene_status = T02ConstrainedSceneStatus.CONFLICT_PRESERVED
    elif operation is T02Operation.RETRACT_PROVISIONAL_BINDING and binding_id:
        bindings = [
            replace(item, status=T02BindingStatus.RETRACTED)
            if item.binding_id == binding_id
            else item
            for item in bindings
        ]
    elif operation is T02Operation.NARROW_ROLE_CANDIDATES and role_id and candidate_id:
        narrowed = [
            (item_role, (candidate_id,))
            if item_role == role_id and candidate_id in candidates
            else (item_role, candidates)
            for item_role, candidates in narrowed
        ]

    operations = tuple(dict.fromkeys((*state.operations_applied, operation.value)))
    state = replace(
        state,
        relation_bindings=tuple(bindings),
        narrowed_role_candidates=tuple(narrowed),
        scene_status=scene_status,
        operations_applied=operations,
    )
    no_clean = state.scene_status in {
        T02ConstrainedSceneStatus.NO_CLEAN_BINDING_COMMIT,
        T02ConstrainedSceneStatus.CONFLICT_PRESERVED,
        T02ConstrainedSceneStatus.AUTHORITY_INSUFFICIENT_FOR_PROPAGATION,
        T02ConstrainedSceneStatus.PROPAGATION_SCOPE_UNCERTAIN,
        T02ConstrainedSceneStatus.FRAGMENT_ONLY,
    }
    ready = bool(
        not no_clean
        and any(
            item.status in {T02BindingStatus.CONFIRMED, T02BindingStatus.PROVISIONAL}
            for item in state.relation_bindings
        )
    )
    gate = replace(
        result.gate,
        pre_verbal_constraint_consumer_ready=ready,
        no_clean_binding_commit=no_clean,
    )
    telemetry = replace(
        result.telemetry,
        scene_status=state.scene_status,
        relation_bindings_count=len(state.relation_bindings),
        confirmed_bindings_count=sum(
            1 for item in state.relation_bindings if item.status is T02BindingStatus.CONFIRMED
        ),
        provisional_bindings_count=sum(
            1 for item in state.relation_bindings if item.status is T02BindingStatus.PROVISIONAL
        ),
        blocked_bindings_count=sum(
            1 for item in state.relation_bindings if item.status is T02BindingStatus.BLOCKED
        ),
        conflicted_bindings_count=sum(
            1
            for item in state.relation_bindings
            if item.status in {T02BindingStatus.CONFLICTED, T02BindingStatus.INCOMPATIBLE}
        ),
        pre_verbal_constraint_consumer_ready=gate.pre_verbal_constraint_consumer_ready,
        no_clean_binding_commit=gate.no_clean_binding_commit,
    )
    return replace(result, state=state, gate=gate, telemetry=telemetry)


def _authority_floor(
    *,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
) -> float:
    return min(
        world_entry_result.episode.confidence,
        s_minimal_result.state.attribution_confidence,
        a_line_result.state.confidence,
        m_minimal_result.state.confidence,
        n_minimal_result.state.confidence,
    )


def _build_relation_bindings(
    *,
    raw_relation_candidates: tuple[tuple[str, str, str], ...],
    authority_floor: float,
    t01_result: T01ActiveFieldResult,
    world_entry_result: WorldEntryContractResult,
    a_line_result: ALineNormalizationResult,
    n_minimal_result: NMinimalResult,
    assembly_mode: T02AssemblyMode,
) -> tuple[T02RelationBinding, ...]:
    bindings: list[T02RelationBinding] = []
    edge_map = {
        (item.source_entity_id, item.relation_type, item.target_entity_id): item
        for item in t01_result.state.relation_edges
    }
    for index, candidate in enumerate(raw_relation_candidates, start=1):
        source_id, relation_type, target_id = candidate
        edge = edge_map[candidate]
        status = T02BindingStatus.CANDIDATE
        confidence = max(0.1, min(0.95, edge.weight))
        role_constraints = ("scene_actor_requires_self_anchor", "scene_environment_requires_world_anchor")
        if assembly_mode is T02AssemblyMode.GRAPH_EDGE_HEURISTIC_ABLATION:
            status = T02BindingStatus.CONFIRMED
            confidence = max(confidence, 0.8)
        elif assembly_mode is T02AssemblyMode.HIDDEN_LOGIC_ABLATION:
            status = T02BindingStatus.CONFIRMED
            confidence = 0.95
        else:
            if edge.contested:
                status = T02BindingStatus.CONFLICTED
            elif authority_floor < 0.45:
                status = T02BindingStatus.BLOCKED
            elif edge.provisional or authority_floor < 0.67:
                status = T02BindingStatus.PROVISIONAL
            else:
                status = T02BindingStatus.CONFIRMED
            if (
                relation_type == "can_execute_affordance"
                and not a_line_result.gate.available_capability_claim_allowed
            ):
                status = T02BindingStatus.BLOCKED
            if relation_type == "bounded_commitment_link" and n_minimal_result.state.underconstrained:
                status = T02BindingStatus.PROVISIONAL
            if (
                relation_type == "engages_world_surface"
                and world_entry_result.episode.action_trace_present
                and not world_entry_result.episode.effect_feedback_correlated
            ):
                status = T02BindingStatus.PROVISIONAL
        downstream_effects = ()
        if status in {T02BindingStatus.CONFIRMED, T02BindingStatus.PROVISIONAL}:
            downstream_effects = ("narrow:scene_actor", "narrow:scene_environment")
        elif status in {T02BindingStatus.CONFLICTED, T02BindingStatus.INCOMPATIBLE}:
            downstream_effects = ("preserve_conflict",)
        bindings.append(
            T02RelationBinding(
                binding_id=f"t02-binding:{index}:{relation_type}",
                source_nodes=(source_id, target_id),
                relation_type=relation_type,
                role_constraints=role_constraints,
                authority_basis=t01_result.state.source_authority_tags,
                confidence=round(confidence, 3),
                status=status,
                downstream_effects=downstream_effects,
                provenance="t02.binding.from_t01_relation_candidate",
            )
        )
    for slot in t01_result.state.unresolved_slots:
        bindings.append(
            T02RelationBinding(
                binding_id=f"t02-binding:unresolved:{slot.slot_id}",
                source_nodes=slot.candidate_entity_ids,
                relation_type=f"unresolved:{slot.slot_kind}",
                role_constraints=("slot_requires_resolution",),
                authority_basis=t01_result.state.source_authority_tags,
                confidence=0.32,
                status=T02BindingStatus.CANDIDATE,
                downstream_effects=("await_slot_fill",),
                provenance="t02.binding.from_t01_unresolved_slot",
            )
        )
    return tuple(bindings)


def _build_constraint_objects(
    *,
    t01_result: T01ActiveFieldResult,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    c05_validity_action: str,
    enforce_stop_conditions: bool,
) -> tuple[T02ConstraintObject, ...]:
    constraints: list[T02ConstraintObject] = []
    for index, slot in enumerate(t01_result.state.unresolved_slots, start=1):
        constraints.append(
            T02ConstraintObject(
                constraint_id=f"t02-constraint:slot:{index}:{slot.slot_id}",
                origin=f"t01_unresolved:{slot.slot_id}",
                scope="local_scene",
                polarity=(
                    T02ConstraintPolarity.FORBID
                    if slot.contested
                    else T02ConstraintPolarity.REQUIRE
                ),
                authority_basis=t01_result.state.source_authority_tags,
                applicability_limits=(slot.slot_kind, "no_global_propagation"),
                propagation_status=(
                    T02PropagationStatus.STOPPED
                    if slot.contested and enforce_stop_conditions
                    else T02PropagationStatus.ACTIVE
                ),
                provenance="t02.constraint.from_t01_unresolved_slot",
            )
        )
    if c05_validity_action in _REVALIDATE_ACTIONS:
        constraints.append(
            T02ConstraintObject(
                constraint_id="t02-constraint:c05-revalidation",
                origin="c05.temporal_validity",
                scope="local_scene",
                polarity=T02ConstraintPolarity.REQUIRE,
                authority_basis=("C05:validity",),
                applicability_limits=("revalidate_before_wide_propagation",),
                propagation_status=(
                    T02PropagationStatus.STOPPED
                    if enforce_stop_conditions
                    else T02PropagationStatus.ACTIVE
                ),
                provenance="t02.constraint.from_c05_validity_action",
            )
        )
    if not world_entry_result.episode.effect_feedback_correlated and world_entry_result.episode.action_trace_present:
        constraints.append(
            T02ConstraintObject(
                constraint_id="t02-constraint:world-effect-link",
                origin="world_entry.effect_feedback",
                scope="local_scene",
                polarity=T02ConstraintPolarity.FORBID,
                authority_basis=("WORLD_ENTRY:effect_feedback_uncorrelated",),
                applicability_limits=("do_not_confirm_world_effect_binding",),
                propagation_status=(
                    T02PropagationStatus.STOPPED
                    if enforce_stop_conditions
                    else T02PropagationStatus.ACTIVE
                ),
                provenance="t02.constraint.from_world_entry_feedback_link",
            )
        )
    if s_minimal_result.state.underconstrained:
        constraints.append(
            T02ConstraintObject(
                constraint_id="t02-constraint:self-world-underconstrained",
                origin="s_minimal.attribution",
                scope="local_scene",
                polarity=T02ConstraintPolarity.PREFER,
                authority_basis=("S_MINIMAL:underconstrained",),
                applicability_limits=("preserve_mixed_attribution", "no_clean_commit"),
                propagation_status=(
                    T02PropagationStatus.STOPPED
                    if enforce_stop_conditions
                    else T02PropagationStatus.ACTIVE
                ),
                provenance="t02.constraint.from_s_minimal_attribution",
            )
        )
    return tuple(constraints)


def _build_propagation_records(
    *,
    bindings: tuple[T02RelationBinding, ...],
    constraints: tuple[T02ConstraintObject, ...],
    authority_floor: float,
    t01_result: T01ActiveFieldResult,
    c05_validity_action: str,
    assembly_mode: T02AssemblyMode,
    enforce_stop_conditions: bool,
) -> tuple[T02PropagationRecord, ...]:
    records: list[T02PropagationRecord] = []
    revalidation_pressure = c05_validity_action in _REVALIDATE_ACTIONS
    for index, binding in enumerate(bindings, start=1):
        scope = "local_scene"
        effect_type = T02PropagationEffectType.NARROW_ROLE_CANDIDATES
        status = T02PropagationStatus.ACTIVE
        stop_reason: str | None = None
        if assembly_mode is T02AssemblyMode.SPREADING_ACTIVATION_ABLATION:
            scope = "diffuse_scene"
            effect_type = T02PropagationEffectType.NO_EFFECT
        if binding.status in {
            T02BindingStatus.BLOCKED,
            T02BindingStatus.INCOMPATIBLE,
            T02BindingStatus.CONFLICTED,
        }:
            effect_type = T02PropagationEffectType.PRESERVE_CONFLICT
            status = T02PropagationStatus.BLOCKED
            stop_reason = "binding_not_propagable"
        elif enforce_stop_conditions and (
            binding.status is T02BindingStatus.PROVISIONAL
            or authority_floor < 0.65
            or revalidation_pressure
            or t01_result.state.scene_status
            in {
                T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
                T01SceneStatus.UNRESOLVED_RELATION_CLUSTER,
                T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
                T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
            }
        ):
            status = T02PropagationStatus.STOPPED
            stop_reason = "scope_or_authority_stop_condition"
            effect_type = T02PropagationEffectType.RESTRICT_SCOPE
        records.append(
            T02PropagationRecord(
                propagation_id=f"t02-propagation:binding:{index}",
                trigger_binding_or_constraint=binding.binding_id,
                affected_nodes_or_roles=binding.source_nodes,
                effect_type=effect_type,
                scope=scope,
                stop_reason_or_none=stop_reason,
                status=status,
                provenance="t02.propagation.from_binding",
            )
        )
    for index, constraint in enumerate(constraints, start=1):
        status = (
            T02PropagationStatus.STOPPED
            if constraint.propagation_status is T02PropagationStatus.STOPPED
            else T02PropagationStatus.ACTIVE
        )
        records.append(
            T02PropagationRecord(
                propagation_id=f"t02-propagation:constraint:{index}",
                trigger_binding_or_constraint=constraint.constraint_id,
                affected_nodes_or_roles=constraint.applicability_limits,
                effect_type=T02PropagationEffectType.RESTRICT_SCOPE,
                scope=constraint.scope,
                stop_reason_or_none=(
                    "constraint_stop_condition"
                    if status is T02PropagationStatus.STOPPED
                    else None
                ),
                status=status,
                provenance="t02.propagation.from_constraint",
            )
        )
    return tuple(records)


def _build_conflict_records(
    *,
    bindings: tuple[T02RelationBinding, ...],
    t01_result: T01ActiveFieldResult,
    preserve_conflicts: bool,
) -> tuple[T02ConflictRecord, ...]:
    conflict_groups: list[tuple[str, ...]] = []
    conflicted_binding_ids = tuple(
        item.binding_id
        for item in bindings
        if item.status in {T02BindingStatus.CONFLICTED, T02BindingStatus.INCOMPATIBLE}
    )
    if conflicted_binding_ids:
        conflict_groups.append(conflicted_binding_ids)
    contested_relation_ids = tuple(
        item.edge_id for item in t01_result.state.relation_edges if item.contested
    )
    if contested_relation_ids:
        conflict_groups.append(contested_relation_ids)
    if not conflict_groups or not preserve_conflicts:
        return ()
    return tuple(
        T02ConflictRecord(
            conflict_id=f"t02-conflict:{index}",
            conflicting_bindings_or_constraints=group,
            conflict_class="binding_constraint_conflict",
            preserved_status=True,
            overwrite_forbidden=True,
            downstream_visibility=True,
            provenance="t02.conflict.preserved",
        )
        for index, group in enumerate(conflict_groups, start=1)
    )


def _build_narrowed_role_candidates(
    *,
    t01_result: T01ActiveFieldResult,
    bindings: tuple[T02RelationBinding, ...],
    propagations: tuple[T02PropagationRecord, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    all_nodes = tuple(entity.entity_id for entity in t01_result.state.active_entities)
    narrowed: dict[str, tuple[str, ...]] = {}
    for role_binding in t01_result.state.role_bindings:
        if role_binding.entity_id is not None:
            narrowed[role_binding.role_id] = (role_binding.entity_id,)
        else:
            narrowed[role_binding.role_id] = all_nodes
    binding_map = {item.binding_id: item for item in bindings}
    for record in propagations:
        if record.effect_type is not T02PropagationEffectType.NARROW_ROLE_CANDIDATES:
            continue
        if record.status is not T02PropagationStatus.ACTIVE:
            continue
        binding = binding_map.get(record.trigger_binding_or_constraint)
        if binding is None:
            continue
        if "self" in binding.relation_type and "scene_actor" in narrowed:
            actor_candidates = tuple(node for node in binding.source_nodes if node == "entity:self")
            if actor_candidates:
                narrowed["scene_actor"] = actor_candidates
        if "world" in binding.relation_type and "scene_environment" in narrowed:
            world_candidates = tuple(node for node in binding.source_nodes if node == "entity:world")
            if world_candidates:
                narrowed["scene_environment"] = world_candidates
    return tuple((role_id, candidates) for role_id, candidates in narrowed.items())


def _derive_constrained_scene_status(
    *,
    raw_scene_nodes: tuple[str, ...],
    bindings: tuple[T02RelationBinding, ...],
    conflicts: tuple[T02ConflictRecord, ...],
    propagations: tuple[T02PropagationRecord, ...],
    authority_floor: float,
    c05_validity_action: str,
    t01_scene_status: T01SceneStatus,
) -> T02ConstrainedSceneStatus:
    if not raw_scene_nodes or not bindings:
        return T02ConstrainedSceneStatus.FRAGMENT_ONLY
    if authority_floor < 0.4:
        return T02ConstrainedSceneStatus.AUTHORITY_INSUFFICIENT_FOR_PROPAGATION
    if conflicts:
        return T02ConstrainedSceneStatus.CONFLICT_PRESERVED
    if any(item.stop_reason_or_none == "scope_or_authority_stop_condition" for item in propagations):
        return T02ConstrainedSceneStatus.PROPAGATION_SCOPE_UNCERTAIN
    if c05_validity_action in _REVALIDATE_ACTIONS:
        return T02ConstrainedSceneStatus.LOCAL_CONSTRAINT_ONLY
    if t01_scene_status in {
        T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
        T01SceneStatus.UNRESOLVED_RELATION_CLUSTER,
        T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
    }:
        return T02ConstrainedSceneStatus.NO_CLEAN_BINDING_COMMIT
    if not any(item.status is T02BindingStatus.CONFIRMED for item in bindings):
        return T02ConstrainedSceneStatus.NO_CLEAN_BINDING_COMMIT
    if any(item.status is T02BindingStatus.BLOCKED for item in bindings):
        return T02ConstrainedSceneStatus.LOCAL_CONSTRAINT_ONLY
    return T02ConstrainedSceneStatus.CONSTRAINED_SCENE_ASSEMBLED


def _derive_operations(
    *,
    bindings: tuple[T02RelationBinding, ...],
    constraints: tuple[T02ConstraintObject, ...],
    propagations: tuple[T02PropagationRecord, ...],
    conflicts: tuple[T02ConflictRecord, ...],
    preserve_conflicts: bool,
    enforce_stop_conditions: bool,
) -> tuple[str, ...]:
    operations: list[str] = [T02Operation.SELECT_BINDING.value]
    if any(item.status is T02BindingStatus.CONFIRMED for item in bindings):
        operations.append(T02Operation.CONFIRM_BINDING.value)
    if any(item.status is T02BindingStatus.PROVISIONAL for item in bindings):
        operations.append(T02Operation.KEEP_PROVISIONAL.value)
    if any(item.status is T02BindingStatus.BLOCKED for item in bindings):
        operations.append(T02Operation.BLOCK_BINDING.value)
    if any(item.status is T02BindingStatus.INCOMPATIBLE for item in bindings):
        operations.append(T02Operation.MARK_INCOMPATIBLE.value)
    if constraints:
        operations.append(T02Operation.PROPAGATE_CONSTRAINT.value)
    if enforce_stop_conditions and any(
        item.status is T02PropagationStatus.STOPPED for item in propagations
    ):
        operations.append(T02Operation.STOP_PROPAGATION.value)
    if preserve_conflicts and conflicts:
        operations.append(T02Operation.PRESERVE_CONFLICT.value)
    if any(item.status is T02BindingStatus.RETRACTED for item in bindings):
        operations.append(T02Operation.RETRACT_PROVISIONAL_BINDING.value)
    if any(item.effect_type is T02PropagationEffectType.NARROW_ROLE_CANDIDATES for item in propagations):
        operations.append(T02Operation.NARROW_ROLE_CANDIDATES.value)
    return tuple(dict.fromkeys(operations))


def _build_gate(
    *,
    state: T02ConstrainedSceneState,
    assembly_mode: T02AssemblyMode,
    preserve_conflicts: bool,
    enforce_stop_conditions: bool,
    authority_floor: float,
) -> T02GateDecision:
    no_clean_binding_commit = state.scene_status in {
        T02ConstrainedSceneStatus.NO_CLEAN_BINDING_COMMIT,
        T02ConstrainedSceneStatus.CONFLICT_PRESERVED,
        T02ConstrainedSceneStatus.AUTHORITY_INSUFFICIENT_FOR_PROPAGATION,
        T02ConstrainedSceneStatus.PROPAGATION_SCOPE_UNCERTAIN,
        T02ConstrainedSceneStatus.FRAGMENT_ONLY,
    }
    pre_verbal_ready = bool(
        not no_clean_binding_commit
        and any(
            item.status in {T02BindingStatus.CONFIRMED, T02BindingStatus.PROVISIONAL}
            for item in state.relation_bindings
        )
        and any(
            item.effect_type is T02PropagationEffectType.NARROW_ROLE_CANDIDATES
            and item.status is T02PropagationStatus.ACTIVE
            for item in state.propagation_records
        )
    )
    forbidden: list[str] = []
    if assembly_mode is T02AssemblyMode.GRAPH_EDGE_HEURISTIC_ABLATION:
        forbidden.append(ForbiddenT02Shortcut.GRAPH_EDGE_HEURISTIC_REBRANDING.value)
    if assembly_mode is T02AssemblyMode.SPREADING_ACTIVATION_ABLATION:
        forbidden.append(ForbiddenT02Shortcut.SPREADING_ACTIVATION_REBRANDING.value)
    if assembly_mode is T02AssemblyMode.HIDDEN_LOGIC_ABLATION:
        forbidden.append(ForbiddenT02Shortcut.HIDDEN_LOGIC_SHORTCUT.value)
    if authority_floor < 0.5 and any(
        item.status is T02BindingStatus.CONFIRMED for item in state.relation_bindings
    ):
        forbidden.append(ForbiddenT02Shortcut.AUTHORITY_LEAK_PROPAGATION.value)
    if not enforce_stop_conditions and any(
        item.status is T02BindingStatus.PROVISIONAL for item in state.relation_bindings
    ):
        forbidden.append(ForbiddenT02Shortcut.SCOPE_LEAK_PROPAGATION.value)
    if not preserve_conflicts and any(
        item.status in {T02BindingStatus.CONFLICTED, T02BindingStatus.INCOMPATIBLE}
        for item in state.relation_bindings
    ):
        forbidden.append(ForbiddenT02Shortcut.SILENT_CONFLICT_OVERWRITE.value)

    restrictions: list[str] = [
        "t02_relation_binding_contract_must_be_read",
        "t02_constraint_objects_must_be_read",
        "t02_propagation_scope_must_be_read",
        "t02_conflict_preservation_must_be_read",
        "t02_raw_vs_propagated_distinction_must_be_read",
    ]
    if no_clean_binding_commit:
        restrictions.append("t02_no_clean_binding_commit_requires_revalidate_or_clarification")
    if not pre_verbal_ready:
        restrictions.append("t02_preverbal_constraint_consumer_not_ready")
    if ForbiddenT02Shortcut.SILENT_CONFLICT_OVERWRITE.value in forbidden:
        restrictions.append("t02_conflict_overwrite_shortcut_detected")
    if ForbiddenT02Shortcut.SCOPE_LEAK_PROPAGATION.value in forbidden:
        restrictions.append("t02_scope_leak_propagation_detected")
    return T02GateDecision(
        pre_verbal_constraint_consumer_ready=pre_verbal_ready,
        no_clean_binding_commit=no_clean_binding_commit,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="t02 produced bounded relation bindings and scoped propagation over t01 scene",
    )


def _build_scope_marker() -> T02ScopeMarker:
    return T02ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        t02_first_slice_only=True,
        t03_implemented=False,
        t04_implemented=False,
        o01_implemented=False,
        full_silent_thought_line_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "first bounded t02 slice only; t03/t04/o01 and full silent-thought line remain out of scope"
        ),
    )
