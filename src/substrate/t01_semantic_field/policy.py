from __future__ import annotations

from dataclasses import replace

from substrate.a_line_normalization import ALineNormalizationResult
from substrate.m_minimal import MMinimalResult, RiskLevel
from substrate.n_minimal import NMinimalResult, NarrativeRiskLevel
from substrate.self_contour import SMinimalContourResult
from substrate.t01_semantic_field.models import (
    ForbiddenT01Shortcut,
    T01ActiveFieldResult,
    T01ActiveSemanticFieldState,
    T01AssemblyMode,
    T01Entity,
    T01ExpectationLink,
    T01FieldGateDecision,
    T01FieldOperation,
    T01RelationEdge,
    T01RoleBinding,
    T01SceneStatus,
    T01ScopeMarker,
    T01StabilityState,
    T01Telemetry,
    T01TemporalLink,
    T01UnresolvedSlot,
)
from substrate.world_entry_contract import WorldEntryContractResult


def build_t01_active_semantic_field(
    *,
    tick_id: str,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
    prior_state: T01ActiveSemanticFieldState | None = None,
    assembly_mode: T01AssemblyMode = T01AssemblyMode.SEMANTIC_FIELD,
    maintain_unresolved_slots: bool = True,
    retain_provenance_tags: bool = True,
    enable_preverbal_consumer: bool = True,
    allow_immediate_verbalization_shortcut: bool = False,
    wording_surface_ref: str | None = None,
    source_lineage: tuple[str, ...] = (),
) -> T01ActiveFieldResult:
    if not tick_id:
        raise ValueError("tick_id is required")
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

    authority_tags = _build_source_authority_tags(
        c04_execution_mode_claim=c04_execution_mode_claim,
        c05_validity_action=c05_validity_action,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        retain_provenance_tags=retain_provenance_tags,
    )
    entities = _build_entities(
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        authority_tags=authority_tags,
        assembly_mode=assembly_mode,
    )
    relations = _build_relations(
        entities=entities,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        assembly_mode=assembly_mode,
    )
    role_bindings = _build_role_bindings(
        entities=entities,
        s_minimal_result=s_minimal_result,
    )
    unresolved_slots = _build_unresolved_slots(
        entities=entities,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        maintain_unresolved_slots=maintain_unresolved_slots,
    )
    unresolved_basis_expected = _has_unresolved_basis_expectation(
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        a_line_result=a_line_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
        c05_validity_action=c05_validity_action,
    )
    temporal_links = _build_temporal_links(entities=entities, m_minimal_result=m_minimal_result)
    expectation_links = _build_expectation_links(
        entities=entities,
        world_entry_result=world_entry_result,
        a_line_result=a_line_result,
    )
    active_predicates = tuple(
        dict.fromkeys(
            (
                f"mode:{c04_execution_mode_claim}",
                f"validity:{c05_validity_action}",
                f"world_presence:{world_entry_result.episode.world_presence_mode.value}",
                f"self_attribution:{s_minimal_result.state.attribution_class.value}",
                f"capability_status:{a_line_result.state.capability_status.value}",
                f"memory_lifecycle:{m_minimal_result.state.lifecycle_status.value}",
                f"narrative_status:{n_minimal_result.state.commitment_status.value}",
            )
        )
    )
    attention_weights, salience_weights = _build_attention_and_salience(entities=entities)
    scene_status = _derive_scene_status(
        entities=entities,
        relations=relations,
        unresolved_slots=unresolved_slots,
        world_entry_result=world_entry_result,
        s_minimal_result=s_minimal_result,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
    )
    stability_state = _derive_stability_state(
        scene_status=scene_status,
        m_minimal_result=m_minimal_result,
        n_minimal_result=n_minimal_result,
    )
    operations = _derive_operations(
        prior_state=prior_state,
        scene_status=scene_status,
        unresolved_slots=unresolved_slots,
        relations=relations,
    )
    scene_id = f"t01-scene:{tick_id}"
    source_lineage = tuple(
        dict.fromkeys(
            (
                *source_lineage,
                *world_entry_result.episode.source_lineage,
                *s_minimal_result.state.source_lineage,
                *a_line_result.state.source_lineage,
                *m_minimal_result.state.source_lineage,
                *n_minimal_result.state.source_lineage,
            )
        )
    )
    state = T01ActiveSemanticFieldState(
        scene_id=scene_id,
        scene_status=scene_status,
        active_entities=entities,
        relation_edges=relations,
        role_bindings=role_bindings,
        active_predicates=active_predicates,
        unresolved_slots=unresolved_slots,
        attention_weights=attention_weights,
        salience_weights=salience_weights,
        temporal_links=temporal_links,
        expectation_links=expectation_links,
        source_authority_tags=authority_tags,
        stability_state=stability_state,
        operations_applied=operations,
        wording_surface_ref=wording_surface_ref,
        source_lineage=source_lineage,
        provenance="t01.semantic_field.active_non_verbal_scene",
    )
    gate = _build_gate(
        state=state,
        assembly_mode=assembly_mode,
        maintain_unresolved_slots=maintain_unresolved_slots,
        unresolved_basis_expected=unresolved_basis_expected,
        retain_provenance_tags=retain_provenance_tags,
        enable_preverbal_consumer=enable_preverbal_consumer,
        allow_immediate_verbalization_shortcut=allow_immediate_verbalization_shortcut,
        m_minimal_result=m_minimal_result,
    )
    scope_marker = _build_scope_marker()
    telemetry = T01Telemetry(
        scene_id=state.scene_id,
        scene_status=state.scene_status,
        stability_state=state.stability_state,
        active_entities_count=len(state.active_entities),
        relation_edges_count=len(state.relation_edges),
        unresolved_slots_count=len(state.unresolved_slots),
        contested_relations_count=sum(1 for edge in state.relation_edges if edge.contested),
        pre_verbal_consumer_ready=gate.pre_verbal_consumer_ready,
        no_clean_scene_commit=gate.no_clean_scene_commit,
        forbidden_shortcuts=gate.forbidden_shortcuts,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return T01ActiveFieldResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason="t01.first_bounded_active_semantic_field_slice",
    )


def evolve_t01_field(
    *,
    result: T01ActiveFieldResult,
    operation: T01FieldOperation,
    focus_target: str | None = None,
    slot_id: str | None = None,
    relation_id: str | None = None,
    relation_weight_delta: float = 0.0,
    decay_factor: float = 0.1,
) -> T01ActiveFieldResult:
    if not isinstance(result, T01ActiveFieldResult):
        raise TypeError("result must be T01ActiveFieldResult")
    if not isinstance(operation, T01FieldOperation):
        raise TypeError("operation must be T01FieldOperation")
    state = result.state

    if operation is T01FieldOperation.DECAY:
        attention = tuple((key, max(0.0, value * (1.0 - decay_factor))) for key, value in state.attention_weights)
        salience = tuple((key, max(0.0, value * (1.0 - decay_factor))) for key, value in state.salience_weights)
        relations = tuple(
            replace(edge, weight=max(0.0, edge.weight * (1.0 - decay_factor)))
            for edge in state.relation_edges
        )
        state = replace(
            state,
            attention_weights=attention,
            salience_weights=salience,
            relation_edges=relations,
            stability_state=T01StabilityState.DEGRADED,
        )
    elif operation is T01FieldOperation.RECENTER and focus_target:
        attention = []
        for key, value in state.attention_weights:
            if key == focus_target:
                attention.append((key, min(1.0, value + 0.2)))
            else:
                attention.append((key, max(0.0, value - 0.05)))
        state = replace(state, attention_weights=tuple(attention))
    elif operation is T01FieldOperation.SLOT_FILL and slot_id:
        state = replace(
            state,
            unresolved_slots=tuple(slot for slot in state.unresolved_slots if slot.slot_id != slot_id),
        )
    elif operation is T01FieldOperation.RELATION_REWEIGHT and relation_id:
        state = replace(
            state,
            relation_edges=tuple(
                replace(edge, weight=max(0.0, min(1.0, edge.weight + relation_weight_delta)))
                if edge.edge_id == relation_id
                else edge
                for edge in state.relation_edges
            ),
        )
    elif operation is T01FieldOperation.SPLIT:
        state = replace(
            state,
            scene_status=T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
            stability_state=T01StabilityState.CONTESTED,
        )
    elif operation is T01FieldOperation.MERGE:
        state = replace(
            state,
            scene_status=T01SceneStatus.PROVISIONAL_SCENE_ONLY,
            stability_state=T01StabilityState.PROVISIONAL,
        )

    operations = tuple(dict.fromkeys((*state.operations_applied, operation.value)))
    state = replace(state, operations_applied=operations)
    no_clean = state.scene_status in {
        T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
        T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
        T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
        T01SceneStatus.SCENE_FRAGMENT_ONLY,
    }
    pre_verbal_ready = state.scene_status not in {
        T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
        T01SceneStatus.SCENE_FRAGMENT_ONLY,
    } and len(state.active_entities) >= 2
    gate = replace(
        result.gate,
        pre_verbal_consumer_ready=pre_verbal_ready,
        no_clean_scene_commit=no_clean,
    )
    telemetry = replace(
        result.telemetry,
        scene_status=state.scene_status,
        stability_state=state.stability_state,
        unresolved_slots_count=len(state.unresolved_slots),
        contested_relations_count=sum(1 for edge in state.relation_edges if edge.contested),
        pre_verbal_consumer_ready=gate.pre_verbal_consumer_ready,
        no_clean_scene_commit=gate.no_clean_scene_commit,
    )
    return replace(result, state=state, gate=gate, telemetry=telemetry)


def _build_source_authority_tags(
    *,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    retain_provenance_tags: bool,
) -> tuple[str, ...]:
    if not retain_provenance_tags:
        return ()
    return tuple(
        dict.fromkeys(
            (
                f"C04:mode={c04_execution_mode_claim}",
                f"C05:validity={c05_validity_action}",
                f"W_ENTRY:scope={world_entry_result.scope_marker.scope}",
                f"S_MINIMAL:attr={s_minimal_result.state.attribution_class.value}",
                f"A_LINE:status={a_line_result.state.capability_status.value}",
                f"M_MINIMAL:lifecycle={m_minimal_result.state.lifecycle_status.value}",
                f"N_MINIMAL:status={n_minimal_result.state.commitment_status.value}",
            )
        )
    )


def _build_entities(
    *,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    authority_tags: tuple[str, ...],
    assembly_mode: T01AssemblyMode,
) -> tuple[T01Entity, ...]:
    if assembly_mode is T01AssemblyMode.HIDDEN_TEXT_ABLATION:
        return ()
    entities: list[T01Entity] = []
    tag = authority_tags[0] if authority_tags else "no_authority_tag"
    if s_minimal_result.state.self_attribution_basis_present:
        entities.append(
            T01Entity(
                entity_id="entity:self",
                label="self_agent",
                entity_type="self_anchor",
                provisional=s_minimal_result.state.underconstrained,
                source_authority_tag=tag,
            )
        )
    if world_entry_result.episode.observation_basis_present:
        entities.append(
            T01Entity(
                entity_id="entity:world",
                label="external_world",
                entity_type="world_anchor",
                provisional=world_entry_result.episode.incomplete,
                source_authority_tag="W_ENTRY",
            )
        )
    if a_line_result.state.availability_basis_present:
        entities.append(
            T01Entity(
                entity_id=f"entity:capability:{a_line_result.state.capability_status.value}",
                label="capability_anchor",
                entity_type="capability_anchor",
                provisional=a_line_result.state.underconstrained,
                source_authority_tag="A_LINE",
            )
        )
    if m_minimal_result.state.bounded_persistence_allowed:
        entities.append(
            T01Entity(
                entity_id=f"entity:memory:{m_minimal_result.state.memory_item_id}",
                label="memory_anchor",
                entity_type="memory_anchor",
                provisional=m_minimal_result.state.review_required,
                source_authority_tag="M_MINIMAL",
            )
        )
    if n_minimal_result.state.narrative_basis_present:
        entities.append(
            T01Entity(
                entity_id=f"entity:narrative:{n_minimal_result.state.commitment_status.value}",
                label="narrative_anchor",
                entity_type="narrative_anchor",
                provisional=n_minimal_result.state.underconstrained,
                source_authority_tag="N_MINIMAL",
            )
        )
    if assembly_mode is T01AssemblyMode.FLAT_TAG_ABLATION:
        return tuple(
            T01Entity(
                entity_id=entity.entity_id,
                label=entity.label,
                entity_type="flat_tag",
                provisional=True,
                source_authority_tag=entity.source_authority_tag,
            )
            for entity in entities
        )
    return tuple(entities)


def _build_relations(
    *,
    entities: tuple[T01Entity, ...],
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    assembly_mode: T01AssemblyMode,
) -> tuple[T01RelationEdge, ...]:
    if assembly_mode is T01AssemblyMode.FLAT_TAG_ABLATION:
        return ()
    if assembly_mode is T01AssemblyMode.HIDDEN_TEXT_ABLATION:
        return ()
    if assembly_mode is T01AssemblyMode.TOKEN_GRAPH_ABLATION:
        return tuple(
            T01RelationEdge(
                edge_id=f"edge:token_graph:{index}",
                source_entity_id=entity.entity_id,
                target_entity_id=entity.entity_id,
                relation_type="co_occurs_with_token",
                weight=0.2,
                provisional=True,
                contested=False,
                source_authority_tag="token_graph_only",
            )
            for index, entity in enumerate(entities, start=1)
        )
    by_id = {item.entity_id: item for item in entities}
    edges: list[T01RelationEdge] = []
    if "entity:self" in by_id and "entity:world" in by_id:
        edges.append(
            T01RelationEdge(
                edge_id="edge:self_world_engagement",
                source_entity_id="entity:self",
                target_entity_id="entity:world",
                relation_type="engages_world_surface",
                weight=0.72 if world_entry_result.world_grounded_transition_admissible else 0.45,
                provisional=world_entry_result.episode.incomplete,
                contested=False,
                source_authority_tag="W_ENTRY+S_MINIMAL",
            )
        )
    capability_entity = next(
        (key for key in by_id if key.startswith("entity:capability:")),
        None,
    )
    if capability_entity and "entity:self" in by_id:
        edges.append(
            T01RelationEdge(
                edge_id="edge:self_capability_binding",
                source_entity_id="entity:self",
                target_entity_id=capability_entity,
                relation_type="can_execute_affordance",
                weight=0.74 if a_line_result.gate.available_capability_claim_allowed else 0.35,
                provisional=(
                    a_line_result.state.underconstrained
                    or a_line_result.gate.policy_conditioned_capability_present
                ),
                contested=False,
                source_authority_tag="A_LINE",
            )
        )
    memory_entity = next(
        (key for key in by_id if key.startswith("entity:memory:")),
        None,
    )
    if memory_entity and "entity:self" in by_id:
        edges.append(
            T01RelationEdge(
                edge_id="edge:memory_self_support",
                source_entity_id=memory_entity,
                target_entity_id="entity:self",
                relation_type="supports_current_scene",
                weight=0.7 if not m_minimal_result.state.review_required else 0.42,
                provisional=m_minimal_result.state.review_required,
                contested=m_minimal_result.state.conflict_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH},
                source_authority_tag="M_MINIMAL",
            )
        )
    narrative_entity = next(
        (key for key in by_id if key.startswith("entity:narrative:")),
        None,
    )
    if narrative_entity and "entity:self" in by_id:
        edges.append(
            T01RelationEdge(
                edge_id="edge:narrative_binding",
                source_entity_id="entity:self",
                target_entity_id=narrative_entity,
                relation_type="bounded_commitment_link",
                weight=0.68 if n_minimal_result.gate.safe_narrative_commitment_allowed else 0.36,
                provisional=n_minimal_result.state.underconstrained,
                contested=n_minimal_result.state.contradiction_risk in {
                    NarrativeRiskLevel.MEDIUM,
                    NarrativeRiskLevel.HIGH,
                },
                source_authority_tag="N_MINIMAL",
            )
        )
    if (
        s_minimal_result.state.attribution_class.value
        == "mixed_or_underconstrained_attribution"
        and edges
    ):
        first = edges[0]
        edges[0] = replace(first, contested=True, provisional=True, weight=max(0.2, first.weight - 0.2))
    return tuple(edges)


def _build_role_bindings(
    *,
    entities: tuple[T01Entity, ...],
    s_minimal_result: SMinimalContourResult,
) -> tuple[T01RoleBinding, ...]:
    entity_ids = {entity.entity_id for entity in entities}
    return (
        T01RoleBinding(
            role_id="scene_actor",
            entity_id="entity:self" if "entity:self" in entity_ids else None,
            binding_confidence=s_minimal_result.state.attribution_confidence,
            provisional=s_minimal_result.state.underconstrained,
            unresolved="entity:self" not in entity_ids,
            source_authority_tag="S_MINIMAL",
        ),
        T01RoleBinding(
            role_id="scene_environment",
            entity_id="entity:world" if "entity:world" in entity_ids else None,
            binding_confidence=0.8 if "entity:world" in entity_ids else 0.0,
            provisional="entity:world" not in entity_ids,
            unresolved="entity:world" not in entity_ids,
            source_authority_tag="W_ENTRY",
        ),
    )


def _build_unresolved_slots(
    *,
    entities: tuple[T01Entity, ...],
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    maintain_unresolved_slots: bool,
) -> tuple[T01UnresolvedSlot, ...]:
    if not maintain_unresolved_slots:
        return ()
    entity_ids = tuple(entity.entity_id for entity in entities)
    slots: list[T01UnresolvedSlot] = []
    if s_minimal_result.state.underconstrained:
        slots.append(
            T01UnresolvedSlot(
                slot_id="slot:self_world_attribution",
                slot_kind="attribution",
                candidate_entity_ids=entity_ids,
                contested=True,
                reason="self/world attribution remains underconstrained",
            )
        )
    if (
        world_entry_result.episode.action_trace_present
        and not world_entry_result.episode.effect_basis_present
    ):
        slots.append(
            T01UnresolvedSlot(
                slot_id="slot:world_effect_feedback",
                slot_kind="effect_feedback",
                candidate_entity_ids=("entity:world",),
                contested=False,
                reason="world action trace exists without effect observation",
            )
        )
    if m_minimal_result.state.review_required or m_minimal_result.gate.no_safe_memory_claim:
        slots.append(
            T01UnresolvedSlot(
                slot_id="slot:memory_reuse_legitimacy",
                slot_kind="memory_reuse",
                candidate_entity_ids=tuple(
                    entity.entity_id
                    for entity in entities
                    if entity.entity_type in {"memory_anchor", "self_anchor"}
                ),
                contested=m_minimal_result.state.conflict_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH},
                reason="memory lifecycle requires review/conflict resolution before strong reuse",
            )
        )
    if (
        a_line_result.gate.policy_conditioned_capability_present
        or a_line_result.state.underconstrained
    ):
        slots.append(
            T01UnresolvedSlot(
                slot_id="slot:capability_legitimacy",
                slot_kind="capability_legitimacy",
                candidate_entity_ids=tuple(
                    entity.entity_id for entity in entities if entity.entity_type == "capability_anchor"
                ),
                contested=True,
                reason="capability remains policy-conditioned or underconstrained",
            )
        )
    if n_minimal_result.state.ambiguity_residue:
        slots.append(
            T01UnresolvedSlot(
                slot_id="slot:narrative_commitment_scope",
                slot_kind="narrative_scope",
                candidate_entity_ids=tuple(
                    entity.entity_id for entity in entities if entity.entity_type == "narrative_anchor"
                ),
                contested=n_minimal_result.state.contradiction_risk in {
                    NarrativeRiskLevel.MEDIUM,
                    NarrativeRiskLevel.HIGH,
                },
                reason="narrative basis retains ambiguity/contradiction residue",
            )
        )
    return tuple(slots)


def _build_temporal_links(
    *,
    entities: tuple[T01Entity, ...],
    m_minimal_result: MMinimalResult,
) -> tuple[T01TemporalLink, ...]:
    if not entities:
        return ()
    if not any(entity.entity_type == "memory_anchor" for entity in entities):
        return ()
    return (
        T01TemporalLink(
            link_id="temporal:memory_to_scene",
            source_entity_id=next(
                entity.entity_id
                for entity in entities
                if entity.entity_type == "memory_anchor"
            ),
            target_entity_id="entity:self" if any(e.entity_id == "entity:self" for e in entities) else entities[0].entity_id,
            temporal_relation=m_minimal_result.state.lifecycle_status.value,
            provisional=m_minimal_result.state.review_required,
        ),
    )


def _build_expectation_links(
    *,
    entities: tuple[T01Entity, ...],
    world_entry_result: WorldEntryContractResult,
    a_line_result: ALineNormalizationResult,
) -> tuple[T01ExpectationLink, ...]:
    if not entities:
        return ()
    source_id = "entity:self" if any(item.entity_id == "entity:self" for item in entities) else entities[0].entity_id
    target_id = "entity:world" if any(item.entity_id == "entity:world" for item in entities) else entities[0].entity_id
    return (
        T01ExpectationLink(
            link_id="expectation:scene_effect_followup",
            source_entity_id=source_id,
            target_entity_id=target_id,
            predicate="effect_feedback_expected_after_action",
            confidence=(
                0.76
                if (
                    world_entry_result.episode.action_trace_present
                    and a_line_result.gate.available_capability_claim_allowed
                )
                else 0.42
            ),
            provisional=not world_entry_result.episode.effect_basis_present,
        ),
    )


def _build_attention_and_salience(
    *,
    entities: tuple[T01Entity, ...],
) -> tuple[tuple[tuple[str, float], ...], tuple[tuple[str, float], ...]]:
    if not entities:
        return (), ()
    count = max(1, len(entities))
    attention = []
    salience = []
    for index, entity in enumerate(entities, start=1):
        attention.append((entity.entity_id, round(max(0.15, 1.0 - (index - 1) / (count + 1)), 3)))
        salience.append((entity.entity_id, round(max(0.2, 0.95 - (index - 1) / (count + 0.5)), 3)))
    return tuple(attention), tuple(salience)


def _derive_scene_status(
    *,
    entities: tuple[T01Entity, ...],
    relations: tuple[T01RelationEdge, ...],
    unresolved_slots: tuple[T01UnresolvedSlot, ...],
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
) -> T01SceneStatus:
    authority_insufficient = bool(
        not world_entry_result.episode.observation_basis_present
        and not s_minimal_result.state.self_attribution_basis_present
    )
    if authority_insufficient:
        return T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING
    if not entities or not relations:
        return T01SceneStatus.SCENE_FRAGMENT_ONLY
    if any(slot.contested for slot in unresolved_slots) and len(unresolved_slots) >= 2:
        return T01SceneStatus.COMPETING_SCENE_HYPOTHESES
    if len(unresolved_slots) >= 2:
        return T01SceneStatus.UNRESOLVED_RELATION_CLUSTER
    no_clean = bool(
        unresolved_slots
        and (
            n_minimal_result.state.underconstrained
            or n_minimal_result.state.contradiction_risk in {
                NarrativeRiskLevel.MEDIUM,
                NarrativeRiskLevel.HIGH,
            }
            or m_minimal_result.state.conflict_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}
        )
    )
    if no_clean:
        return T01SceneStatus.NO_CLEAN_SCENE_COMMIT
    if unresolved_slots:
        return T01SceneStatus.PROVISIONAL_SCENE_ONLY
    return T01SceneStatus.SCENE_ASSEMBLED


def _derive_stability_state(
    *,
    scene_status: T01SceneStatus,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
) -> T01StabilityState:
    if scene_status is T01SceneStatus.SCENE_ASSEMBLED:
        return T01StabilityState.STABLE
    if scene_status in {
        T01SceneStatus.PROVISIONAL_SCENE_ONLY,
        T01SceneStatus.UNRESOLVED_RELATION_CLUSTER,
    }:
        return T01StabilityState.PROVISIONAL
    if scene_status in {
        T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
        T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
    }:
        return T01StabilityState.CONTESTED
    if scene_status is T01SceneStatus.SCENE_FRAGMENT_ONLY:
        return T01StabilityState.FRAGMENTARY
    if (
        m_minimal_result.state.degraded
        or n_minimal_result.state.degraded
        or scene_status is T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING
    ):
        return T01StabilityState.DEGRADED
    return T01StabilityState.PROVISIONAL


def _derive_operations(
    *,
    prior_state: T01ActiveSemanticFieldState | None,
    scene_status: T01SceneStatus,
    unresolved_slots: tuple[T01UnresolvedSlot, ...],
    relations: tuple[T01RelationEdge, ...],
) -> tuple[str, ...]:
    operations: list[str] = [T01FieldOperation.ASSEMBLE.value]
    if prior_state is not None:
        operations.append(T01FieldOperation.UPDATE.value)
        if len(unresolved_slots) < len(prior_state.unresolved_slots):
            operations.append(T01FieldOperation.SLOT_FILL.value)
        if scene_status != prior_state.scene_status:
            operations.append(T01FieldOperation.RECENTER.value)
        if any(edge.contested for edge in relations):
            operations.append(T01FieldOperation.RELATION_REWEIGHT.value)
        if scene_status is T01SceneStatus.COMPETING_SCENE_HYPOTHESES:
            operations.append(T01FieldOperation.SPLIT.value)
        if (
            prior_state.scene_status is T01SceneStatus.COMPETING_SCENE_HYPOTHESES
            and scene_status is T01SceneStatus.PROVISIONAL_SCENE_ONLY
        ):
            operations.append(T01FieldOperation.MERGE.value)
    if scene_status in {
        T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
        T01SceneStatus.SCENE_FRAGMENT_ONLY,
    }:
        operations.append(T01FieldOperation.DECAY.value)
    return tuple(dict.fromkeys(operations))


def _build_gate(
    *,
    state: T01ActiveSemanticFieldState,
    assembly_mode: T01AssemblyMode,
    maintain_unresolved_slots: bool,
    unresolved_basis_expected: bool,
    retain_provenance_tags: bool,
    enable_preverbal_consumer: bool,
    allow_immediate_verbalization_shortcut: bool,
    m_minimal_result: MMinimalResult,
) -> T01FieldGateDecision:
    no_clean = state.scene_status in {
        T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
        T01SceneStatus.AUTHORITY_INSUFFICIENT_FOR_BINDING,
        T01SceneStatus.SCENE_FRAGMENT_ONLY,
        T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
    }
    pre_verbal_consumer_ready = bool(
        enable_preverbal_consumer
        and not no_clean
        and len(state.active_entities) >= 2
        and len(state.relation_edges) >= 1
    )
    forbidden: list[str] = []
    if assembly_mode is T01AssemblyMode.HIDDEN_TEXT_ABLATION:
        forbidden.append(ForbiddenT01Shortcut.HIDDEN_TEXT_BUFFER_SURROGATE.value)
    if assembly_mode is T01AssemblyMode.FLAT_TAG_ABLATION:
        forbidden.append(ForbiddenT01Shortcut.BAG_OF_TAGS_REBRANDING.value)
    if assembly_mode is T01AssemblyMode.TOKEN_GRAPH_ABLATION:
        forbidden.append(ForbiddenT01Shortcut.TOKEN_GRAPH_REBRANDING.value)
    provisional_structure_present = bool(
        any(item.provisional for item in state.active_entities)
        or any(item.provisional or item.contested for item in state.relation_edges)
        or any(item.provisional or item.unresolved for item in state.role_bindings)
        or any(item.provisional for item in state.temporal_links)
        or any(item.provisional for item in state.expectation_links)
    )
    weak_unresolved_risk = bool(
        unresolved_basis_expected
        or provisional_structure_present
        or state.scene_status
        in {
            T01SceneStatus.PROVISIONAL_SCENE_ONLY,
            T01SceneStatus.UNRESOLVED_RELATION_CLUSTER,
            T01SceneStatus.COMPETING_SCENE_HYPOTHESES,
            T01SceneStatus.NO_CLEAN_SCENE_COMMIT,
        }
    )
    if weak_unresolved_risk and not maintain_unresolved_slots:
        forbidden.append(ForbiddenT01Shortcut.PREMATURE_SCENE_CLOSURE.value)
    if (
        m_minimal_result.state.conflict_risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}
        and state.scene_status is T01SceneStatus.SCENE_ASSEMBLED
    ):
        forbidden.append(ForbiddenT01Shortcut.MEMORY_POLLUTION_REFRAMED_AS_SCENE_FACT.value)
    if allow_immediate_verbalization_shortcut:
        forbidden.append(ForbiddenT01Shortcut.IMMEDIATE_VERBALIZATION_SHORTCUT.value)
    restrictions: list[str] = [
        "t01_semantic_field_contract_must_be_read",
        "t01_scene_status_must_be_read",
        "t01_unresolved_slots_must_be_preserved",
        "t01_scene_must_be_consumed_preverbal",
    ]
    if not retain_provenance_tags:
        restrictions.append("t01_source_authority_tags_missing")
    if no_clean:
        restrictions.append("no_clean_scene_commit_requires_revalidate_or_clarification")
    if not pre_verbal_consumer_ready:
        restrictions.append("t01_preverbal_consumer_not_ready")
    if ForbiddenT01Shortcut.PREMATURE_SCENE_CLOSURE.value in forbidden:
        restrictions.append("t01_unresolved_laundering_risk_detected")
    return T01FieldGateDecision(
        pre_verbal_consumer_ready=pre_verbal_consumer_ready,
        no_clean_scene_commit=no_clean,
        forbidden_shortcuts=tuple(dict.fromkeys(forbidden)),
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="t01 active semantic field produced bounded non-verbal scene for downstream pre-verbal use",
    )


def _has_unresolved_basis_expectation(
    *,
    world_entry_result: WorldEntryContractResult,
    s_minimal_result: SMinimalContourResult,
    a_line_result: ALineNormalizationResult,
    m_minimal_result: MMinimalResult,
    n_minimal_result: NMinimalResult,
    c05_validity_action: str,
) -> bool:
    return bool(
        s_minimal_result.state.underconstrained
        or s_minimal_result.state.attribution_confidence < 0.7
        or world_entry_result.episode.incomplete
        or world_entry_result.episode.confidence < 0.7
        or (
            world_entry_result.episode.action_trace_present
            and not world_entry_result.episode.effect_basis_present
        )
        or (
            world_entry_result.episode.action_trace_present
            and not world_entry_result.episode.effect_feedback_correlated
        )
        or c05_validity_action
        in {
            "run_selective_revalidation",
            "run_bounded_revalidation",
            "suspend_until_revalidation_basis",
            "halt_reuse_and_rebuild_scope",
        }
        or m_minimal_result.state.review_required
        or m_minimal_result.state.reactivation_eligible
        or m_minimal_result.gate.no_safe_memory_claim
        or a_line_result.gate.policy_conditioned_capability_present
        or a_line_result.state.underconstrained
        or a_line_result.state.confidence < 0.7
        or n_minimal_result.state.ambiguity_residue
        or n_minimal_result.state.underconstrained
        or n_minimal_result.state.confidence < 0.7
        or n_minimal_result.state.contradiction_risk in {
            NarrativeRiskLevel.MEDIUM,
            NarrativeRiskLevel.HIGH,
        }
        or m_minimal_result.state.confidence < 0.7
    )


def _build_scope_marker() -> T01ScopeMarker:
    return T01ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        t01_first_slice_only=True,
        t02_implemented=False,
        t03_implemented=False,
        t04_implemented=False,
        o01_implemented=False,
        full_silent_thought_line_implemented=False,
        repo_wide_adoption=False,
        reason=(
            "first bounded t01 slice only; t02/t03/t04/o01 and full silent-thought line remain out of scope"
        ),
    )
