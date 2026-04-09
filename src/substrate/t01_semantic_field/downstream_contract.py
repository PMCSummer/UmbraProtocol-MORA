from __future__ import annotations

from dataclasses import dataclass

from substrate.t01_semantic_field.models import T01ActiveFieldResult, T01SceneStatus


@dataclass(frozen=True, slots=True)
class T01FieldContractView:
    scene_id: str
    scene_status: str
    stability_state: str
    active_entities: tuple[str, ...]
    relation_edges: tuple[tuple[str, str, str], ...]
    role_bindings: tuple[tuple[str, str | None], ...]
    active_predicates: tuple[str, ...]
    unresolved_slots: tuple[str, ...]
    contested_relations: tuple[str, ...]
    attention_weights: tuple[tuple[str, float], ...]
    salience_weights: tuple[tuple[str, float], ...]
    expectation_links: tuple[tuple[str, str, str], ...]
    source_authority_tags: tuple[str, ...]
    pre_verbal_consumer_ready: bool
    no_clean_scene_commit: bool
    forbidden_shortcuts: tuple[str, ...]
    restrictions: tuple[str, ...]
    scope: str
    scope_rt01_contour_only: bool
    scope_t01_first_slice_only: bool
    scope_t02_implemented: bool
    scope_t03_implemented: bool
    scope_t04_implemented: bool
    scope_o01_implemented: bool
    scope_full_silent_thought_line_implemented: bool
    scope_repo_wide_adoption: bool
    scope_reason: str
    reason: str


@dataclass(frozen=True, slots=True)
class T01PreverbalConsumerView:
    scene_id: str
    scene_status: str
    clarification_required: bool
    comparison_ready: bool
    can_continue_preverbal: bool
    unresolved_slots: tuple[str, ...]
    contested_relations: tuple[str, ...]
    restrictions: tuple[str, ...]
    reason: str


def derive_t01_field_contract_view(result: T01ActiveFieldResult) -> T01FieldContractView:
    if not isinstance(result, T01ActiveFieldResult):
        raise TypeError("derive_t01_field_contract_view requires T01ActiveFieldResult")
    return T01FieldContractView(
        scene_id=result.state.scene_id,
        scene_status=result.state.scene_status.value,
        stability_state=result.state.stability_state.value,
        active_entities=tuple(item.entity_id for item in result.state.active_entities),
        relation_edges=tuple(
            (edge.source_entity_id, edge.relation_type, edge.target_entity_id)
            for edge in result.state.relation_edges
        ),
        role_bindings=tuple(
            (binding.role_id, binding.entity_id) for binding in result.state.role_bindings
        ),
        active_predicates=result.state.active_predicates,
        unresolved_slots=tuple(slot.slot_id for slot in result.state.unresolved_slots),
        contested_relations=tuple(
            edge.edge_id for edge in result.state.relation_edges if edge.contested
        ),
        attention_weights=result.state.attention_weights,
        salience_weights=result.state.salience_weights,
        expectation_links=tuple(
            (link.source_entity_id, link.predicate, link.target_entity_id)
            for link in result.state.expectation_links
        ),
        source_authority_tags=result.state.source_authority_tags,
        pre_verbal_consumer_ready=result.gate.pre_verbal_consumer_ready,
        no_clean_scene_commit=result.gate.no_clean_scene_commit,
        forbidden_shortcuts=result.gate.forbidden_shortcuts,
        restrictions=result.gate.restrictions,
        scope=result.scope_marker.scope,
        scope_rt01_contour_only=result.scope_marker.rt01_contour_only,
        scope_t01_first_slice_only=result.scope_marker.t01_first_slice_only,
        scope_t02_implemented=result.scope_marker.t02_implemented,
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


def derive_t01_preverbal_consumer_view(
    result_or_view: T01ActiveFieldResult | T01FieldContractView,
) -> T01PreverbalConsumerView:
    view = (
        derive_t01_field_contract_view(result_or_view)
        if isinstance(result_or_view, T01ActiveFieldResult)
        else result_or_view
    )
    if not isinstance(view, T01FieldContractView):
        raise TypeError(
            "derive_t01_preverbal_consumer_view requires T01ActiveFieldResult/T01FieldContractView"
        )
    clarification_required = bool(
        view.unresolved_slots
        or view.contested_relations
        or view.scene_status
        in {
            T01SceneStatus.UNRESOLVED_RELATION_CLUSTER.value,
            T01SceneStatus.COMPETING_SCENE_HYPOTHESES.value,
            T01SceneStatus.NO_CLEAN_SCENE_COMMIT.value,
        }
    )
    comparison_ready = view.scene_status in {
        T01SceneStatus.SCENE_ASSEMBLED.value,
        T01SceneStatus.PROVISIONAL_SCENE_ONLY.value,
        T01SceneStatus.UNRESOLVED_RELATION_CLUSTER.value,
    }
    can_continue_preverbal = view.pre_verbal_consumer_ready and not view.no_clean_scene_commit
    return T01PreverbalConsumerView(
        scene_id=view.scene_id,
        scene_status=view.scene_status,
        clarification_required=clarification_required,
        comparison_ready=comparison_ready,
        can_continue_preverbal=can_continue_preverbal,
        unresolved_slots=view.unresolved_slots,
        contested_relations=view.contested_relations,
        restrictions=view.restrictions,
        reason="t01 preverbal consumer contract derived from active semantic field",
    )


def require_t01_preverbal_consumer_ready(
    result_or_view: T01ActiveFieldResult | T01FieldContractView,
) -> T01PreverbalConsumerView:
    consumer_view = derive_t01_preverbal_consumer_view(result_or_view)
    if not consumer_view.can_continue_preverbal:
        raise PermissionError(
            "t01 semantic field cannot be consumed as clean pre-verbal scene; clarification/revalidate path required"
        )
    return consumer_view


def derive_t01_scene_signature(
    result_or_view: T01ActiveFieldResult | T01FieldContractView,
) -> tuple[object, ...]:
    view = (
        derive_t01_field_contract_view(result_or_view)
        if isinstance(result_or_view, T01ActiveFieldResult)
        else result_or_view
    )
    if not isinstance(view, T01FieldContractView):
        raise TypeError("derive_t01_scene_signature requires T01ActiveFieldResult/T01FieldContractView")
    return (
        tuple(sorted(_normalize_entity_token(entity_id) for entity_id in view.active_entities)),
        tuple(
            sorted(
                (
                    _normalize_entity_token(source),
                    relation,
                    _normalize_entity_token(target),
                )
                for source, relation, target in view.relation_edges
            )
        ),
        tuple(
            sorted(
                (role_id, None if entity_id is None else _normalize_entity_token(entity_id))
                for role_id, entity_id in view.role_bindings
            )
        ),
        tuple(sorted(view.unresolved_slots)),
        view.scene_status,
    )


def _normalize_entity_token(entity_id: str) -> str:
    if entity_id.startswith("entity:memory:"):
        return "entity:memory:*"
    if entity_id.startswith("entity:narrative:"):
        return "entity:narrative:*"
    return entity_id
