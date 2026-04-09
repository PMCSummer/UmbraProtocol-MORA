from __future__ import annotations

from dataclasses import dataclass

from substrate.t02_relation_binding.models import T02ConstrainedSceneResult, T02ConstrainedSceneStatus


@dataclass(frozen=True, slots=True)
class T02ConstrainedSceneContractView:
    constrained_scene_id: str
    source_t01_scene_id: str
    source_t01_scene_status: str
    scene_status: str
    raw_scene_nodes: tuple[str, ...]
    raw_relation_candidates: tuple[tuple[str, str, str], ...]
    confirmed_bindings: tuple[str, ...]
    provisional_bindings: tuple[str, ...]
    blocked_bindings: tuple[str, ...]
    incompatible_bindings: tuple[str, ...]
    conflicted_bindings: tuple[str, ...]
    propagated_consequences: tuple[str, ...]
    blocked_or_conflicted_consequences: tuple[str, ...]
    narrowed_role_candidates: tuple[tuple[str, tuple[str, ...]], ...]
    pre_verbal_constraint_consumer_ready: bool
    no_clean_binding_commit: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_t02_first_slice_only: bool
    scope_t03_implemented: bool
    scope_t04_implemented: bool
    scope_o01_implemented: bool
    scope_full_silent_thought_line_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class T02PreverbalConstraintConsumerView:
    constrained_scene_id: str
    scene_status: str
    can_consume_constrained_scene: bool
    clarification_required: bool
    role_narrowing_ready: bool
    raw_vs_propagated_distinct: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_t02_constrained_scene_contract_view(
    result: T02ConstrainedSceneResult,
) -> T02ConstrainedSceneContractView:
    if not isinstance(result, T02ConstrainedSceneResult):
        raise TypeError("derive_t02_constrained_scene_contract_view requires T02ConstrainedSceneResult")
    return T02ConstrainedSceneContractView(
        constrained_scene_id=result.state.constrained_scene_id,
        source_t01_scene_id=result.state.source_t01_scene_id,
        source_t01_scene_status=result.state.source_t01_scene_status,
        scene_status=result.state.scene_status.value,
        raw_scene_nodes=result.state.raw_scene_nodes,
        raw_relation_candidates=result.state.raw_relation_candidates,
        confirmed_bindings=tuple(
            item.binding_id
            for item in result.state.relation_bindings
            if item.status.value == "confirmed"
        ),
        provisional_bindings=tuple(
            item.binding_id
            for item in result.state.relation_bindings
            if item.status.value == "provisional"
        ),
        blocked_bindings=tuple(
            item.binding_id
            for item in result.state.relation_bindings
            if item.status.value == "blocked"
        ),
        incompatible_bindings=tuple(
            item.binding_id
            for item in result.state.relation_bindings
            if item.status.value == "incompatible"
        ),
        conflicted_bindings=tuple(
            item.binding_id
            for item in result.state.relation_bindings
            if item.status.value == "conflicted"
        ),
        propagated_consequences=tuple(
            item.propagation_id
            for item in result.state.propagation_records
            if item.effect_type.value != "no_effect" and item.status.value == "active"
        ),
        blocked_or_conflicted_consequences=tuple(
            item.propagation_id
            for item in result.state.propagation_records
            if item.status.value in {"blocked", "stopped"}
        ),
        narrowed_role_candidates=result.state.narrowed_role_candidates,
        pre_verbal_constraint_consumer_ready=result.gate.pre_verbal_constraint_consumer_ready,
        no_clean_binding_commit=result.gate.no_clean_binding_commit,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_t02_first_slice_only=result.scope_marker.t02_first_slice_only,
        scope_t03_implemented=result.scope_marker.t03_implemented,
        scope_t04_implemented=result.scope_marker.t04_implemented,
        scope_o01_implemented=result.scope_marker.o01_implemented,
        scope_full_silent_thought_line_implemented=(
            result.scope_marker.full_silent_thought_line_implemented
        ),
        scope_repo_wide_adoption=result.scope_marker.repo_wide_adoption,
        scope_reason=result.scope_marker.reason,
        reason=result.reason,
    )


def derive_t02_preverbal_constraint_consumer_view(
    result_or_view: T02ConstrainedSceneResult | T02ConstrainedSceneContractView,
) -> T02PreverbalConstraintConsumerView:
    view = (
        derive_t02_constrained_scene_contract_view(result_or_view)
        if isinstance(result_or_view, T02ConstrainedSceneResult)
        else result_or_view
    )
    if not isinstance(view, T02ConstrainedSceneContractView):
        raise TypeError(
            "derive_t02_preverbal_constraint_consumer_view requires T02ConstrainedSceneResult/T02ConstrainedSceneContractView"
        )
    clarification_required = bool(
        view.no_clean_binding_commit
        or view.blocked_bindings
        or view.incompatible_bindings
        or view.conflicted_bindings
        or view.scene_status
        in {
            T02ConstrainedSceneStatus.NO_CLEAN_BINDING_COMMIT.value,
            T02ConstrainedSceneStatus.CONFLICT_PRESERVED.value,
            T02ConstrainedSceneStatus.PROPAGATION_SCOPE_UNCERTAIN.value,
        }
    )
    role_narrowing_ready = bool(
        view.narrowed_role_candidates
        and any(len(candidates) == 1 for _, candidates in view.narrowed_role_candidates)
    )
    raw_vs_propagated_distinct = bool(
        view.raw_relation_candidates
        and (view.propagated_consequences or view.blocked_or_conflicted_consequences)
    )
    can_consume = bool(
        view.pre_verbal_constraint_consumer_ready
        and not clarification_required
        and raw_vs_propagated_distinct
    )
    return T02PreverbalConstraintConsumerView(
        constrained_scene_id=view.constrained_scene_id,
        scene_status=view.scene_status,
        can_consume_constrained_scene=can_consume,
        clarification_required=clarification_required,
        role_narrowing_ready=role_narrowing_ready,
        raw_vs_propagated_distinct=raw_vs_propagated_distinct,
        restrictions=view.restrictions,
        reason="t02 pre-verbal constrained-scene consumer view derived from binding/propagation contract",
    )


def require_t02_preverbal_constraint_consumer_ready(
    result_or_view: T02ConstrainedSceneResult | T02ConstrainedSceneContractView,
) -> T02PreverbalConstraintConsumerView:
    consumer_view = derive_t02_preverbal_constraint_consumer_view(result_or_view)
    if not consumer_view.can_consume_constrained_scene:
        raise PermissionError(
            "t02 constrained scene cannot be consumed as clean pre-verbal relation binding basis; clarification/revalidate path required"
        )
    return consumer_view


def derive_t02_relation_signature(
    result_or_view: T02ConstrainedSceneResult | T02ConstrainedSceneContractView,
) -> tuple[object, ...]:
    view = (
        derive_t02_constrained_scene_contract_view(result_or_view)
        if isinstance(result_or_view, T02ConstrainedSceneResult)
        else result_or_view
    )
    if not isinstance(view, T02ConstrainedSceneContractView):
        raise TypeError("derive_t02_relation_signature requires T02ConstrainedSceneResult/T02ConstrainedSceneContractView")
    return (
        tuple(sorted(_normalize_entity_token(entity_id) for entity_id in view.raw_scene_nodes)),
        tuple(
            sorted(
                (
                    _normalize_entity_token(source),
                    relation,
                    _normalize_entity_token(target),
                )
                for source, relation, target in view.raw_relation_candidates
            )
        ),
        tuple(sorted(view.confirmed_bindings)),
        tuple(sorted(view.provisional_bindings)),
        tuple(sorted(view.blocked_bindings)),
        tuple(sorted(view.conflicted_bindings)),
        view.scene_status,
    )


def _normalize_entity_token(entity_id: str) -> str:
    if entity_id.startswith("entity:memory:"):
        return "entity:memory:*"
    if entity_id.startswith("entity:narrative:"):
        return "entity:narrative:*"
    if entity_id.startswith("entity:capability:"):
        return "entity:capability:*"
    return entity_id
