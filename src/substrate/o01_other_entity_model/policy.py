from __future__ import annotations

from collections import Counter, defaultdict

from substrate.o01_other_entity_model.models import (
    O01AttributionStatus,
    O01BeliefOverlay,
    O01EntityKind,
    O01EntityRevisionEvent,
    O01EntitySignal,
    O01EntityState,
    O01ModelScope,
    O01OtherEntityModelGateDecision,
    O01OtherEntityModelResult,
    O01OtherEntityModelState,
    O01ScopeMarker,
    O01Telemetry,
    O01UpdateEventKind,
)

_ALLOWED_AUTHORITIES = {
    "current_user_direct",
    "interaction_grounded",
    "referenced_other",
    "quoted_third_party",
}
_CURRENT_USER_REFERENT_LABELS = {"", "user", "current_user"}


def build_o01_other_entity_model(
    *,
    tick_id: str,
    tick_index: int,
    signals: tuple[O01EntitySignal, ...] = (),
    prior_state: O01OtherEntityModelState | None = None,
    source_lineage: tuple[str, ...] = (),
    model_enabled: bool = True,
) -> O01OtherEntityModelResult:
    if not model_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    filtered: list[O01EntitySignal] = []
    projection_guard_triggered = False
    authority_guard_triggered = False
    for raw in signals:
        if not isinstance(raw, O01EntitySignal):
            continue
        authority = raw.source_authority.strip().lower()
        if authority.startswith("self_"):
            projection_guard_triggered = True
            continue
        if authority == "current_user_direct":
            referent = str(raw.referent_label or "").strip().lower()
            if raw.quoted:
                authority_guard_triggered = True
                continue
            if referent not in _CURRENT_USER_REFERENT_LABELS:
                authority_guard_triggered = True
                continue
        if authority not in _ALLOWED_AUTHORITIES or not raw.grounded:
            continue
        filtered.append(raw)

    buckets: dict[str, list[O01EntitySignal]] = defaultdict(list)
    entity_kinds: dict[str, O01EntityKind] = {}
    for signal in filtered:
        entity_id, kind = _resolve_entity_id_and_kind(signal)
        buckets[entity_id].append(signal)
        entity_kinds[entity_id] = kind

    entities: list[O01EntityState] = []
    contradiction_count = 0
    competing_entity_models: list[str] = []
    current_user_entity_id: str | None = None
    referenced_other_entity_ids: list[str] = []
    third_party_entity_ids: list[str] = []
    minimal_other_entity_ids: list[str] = []

    prior_by_entity = (
        {entity.entity_id: entity for entity in prior_state.entities}
        if isinstance(prior_state, O01OtherEntityModelState)
        else {}
    )

    referent_to_entity: dict[str, set[str]] = defaultdict(set)
    for entity_id, signals_for_entity in buckets.items():
        referent_labels = {
            str(item.referent_label or "").strip().lower()
            for item in signals_for_entity
            if str(item.referent_label or "").strip()
        }
        for label in referent_labels:
            referent_to_entity[label].add(entity_id)

    for referent_label, entity_ids in referent_to_entity.items():
        if len(entity_ids) > 1 and referent_label not in {"user", "current_user"}:
            competing_entity_models.extend(sorted(entity_ids))

    for entity_id, signals_for_entity in sorted(buckets.items(), key=lambda item: item[0]):
        kind = entity_kinds[entity_id]
        prior_entity = prior_by_entity.get(entity_id)
        entity_state, entity_contradictions = _build_entity_state(
            entity_id=entity_id,
            kind=kind,
            signals=tuple(signals_for_entity),
            prior=prior_entity,
            competing=entity_id in competing_entity_models,
        )
        entities.append(entity_state)
        contradiction_count += entity_contradictions
        if kind is O01EntityKind.CURRENT_USER_MODEL:
            current_user_entity_id = entity_id
        elif kind is O01EntityKind.REFERENCED_OTHER_MODEL:
            referenced_other_entity_ids.append(entity_id)
        elif kind is O01EntityKind.THIRD_PARTY_STUB:
            third_party_entity_ids.append(entity_id)
        elif kind is O01EntityKind.MINIMAL_OTHER_STUB:
            minimal_other_entity_ids.append(entity_id)

    if not entities:
        minimal_entity = _build_minimal_other_entity(
            entity_id="other:minimal",
            reason="no_grounded_o01_signals",
        )
        entities = [minimal_entity]
        minimal_other_entity_ids = [minimal_entity.entity_id]

    stable_claim_count = sum(len(entity.stable_claims) for entity in entities)
    temporary_hypothesis_count = sum(len(entity.temporary_state_hypotheses) for entity in entities)
    knowledge_boundary_known_count = sum(
        len(entity.knowledge_boundary_estimates) for entity in entities
    )

    temporary_only_not_stable = stable_claim_count == 0 and temporary_hypothesis_count > 0
    knowledge_boundary_unknown = knowledge_boundary_known_count == 0
    entity_not_individuated = current_user_entity_id is None
    belief_overlay_underconstrained = _belief_overlay_underconstrained(
        entities=tuple(entities),
        current_user_entity_id=current_user_entity_id,
    )
    perspective_underconstrained = bool(
        entity_not_individuated
        or temporary_only_not_stable
        or knowledge_boundary_unknown
        or belief_overlay_underconstrained
        or not filtered
    )
    no_safe_state_claim = bool(stable_claim_count == 0 and not current_user_entity_id)

    restrictions: list[str] = []
    if entity_not_individuated:
        restrictions.append("entity_not_individuated")
    if perspective_underconstrained:
        restrictions.append("perspective_underconstrained")
    if no_safe_state_claim:
        restrictions.append("no_safe_state_claim")
    if temporary_only_not_stable:
        restrictions.append("temporary_only_not_stable")
    if knowledge_boundary_unknown:
        restrictions.append("knowledge_boundary_unknown")
    if belief_overlay_underconstrained:
        restrictions.append("belief_overlay_underconstrained")
    if projection_guard_triggered:
        restrictions.append("projection_guard_triggered")
    if authority_guard_triggered:
        restrictions.append("authority_guard_triggered")
    if competing_entity_models:
        restrictions.append("competing_entity_models")

    current_user_model_ready = bool(
        current_user_entity_id is not None
        and any(
            entity.entity_id == current_user_entity_id and entity.identity_confidence >= 0.45
            for entity in entities
        )
    )
    entity_individuation_ready = not entity_not_individuated and not competing_entity_models
    clarification_ready = bool(
        entity_individuation_ready and not perspective_underconstrained and not no_safe_state_claim
    )
    downstream_consumer_ready = bool(current_user_model_ready and clarification_ready)

    attribution_status = (
        O01AttributionStatus.NO_SAFE_STATE_CLAIM
        if no_safe_state_claim
        else O01AttributionStatus.ENTITY_NOT_INDIVIDUATED
        if entity_not_individuated
        else O01AttributionStatus.PERSPECTIVE_UNDERCONSTRAINED
        if perspective_underconstrained
        else O01AttributionStatus.READY
    )
    reason = (
        "o01 produced bounded other-entity model with explicit uncertainty partition"
        if attribution_status is O01AttributionStatus.READY
        else "o01 kept bounded fallback due underconstrained perspective/entity basis"
    )

    state = O01OtherEntityModelState(
        model_id=f"o01-model:{tick_id}",
        tick_index=tick_index,
        entities=tuple(entities),
        current_user_entity_id=current_user_entity_id,
        referenced_other_entity_ids=tuple(referenced_other_entity_ids),
        third_party_entity_ids=tuple(third_party_entity_ids),
        minimal_other_entity_ids=tuple(minimal_other_entity_ids),
        competing_entity_models=tuple(dict.fromkeys(competing_entity_models)),
        entity_not_individuated=entity_not_individuated,
        perspective_underconstrained=perspective_underconstrained,
        no_safe_state_claim=no_safe_state_claim,
        temporary_only_not_stable=temporary_only_not_stable,
        knowledge_boundary_unknown=knowledge_boundary_unknown,
        contradiction_count=contradiction_count,
        projection_guard_triggered=projection_guard_triggered,
        source_lineage=source_lineage,
        last_update_provenance="o01.other_entity_model.policy",
    )
    gate = O01OtherEntityModelGateDecision(
        current_user_model_ready=current_user_model_ready,
        entity_individuation_ready=entity_individuation_ready,
        clarification_ready=clarification_ready,
        downstream_consumer_ready=downstream_consumer_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
    )
    scope_marker = O01ScopeMarker(
        scope="rt01_hosted_o01_first_slice",
        rt01_hosted_only=True,
        o01_first_slice_only=True,
        o02_o03_not_implemented=True,
        repo_wide_adoption=False,
        reason="first bounded o01 slice; o02/o03 and broad social stack remain out of scope",
    )
    telemetry = O01Telemetry(
        model_id=state.model_id,
        tick_index=tick_index,
        entity_count=len(state.entities),
        current_user_model_ready=gate.current_user_model_ready,
        third_party_models_active=len(state.third_party_entity_ids),
        stable_claim_count=stable_claim_count,
        temporary_hypothesis_count=temporary_hypothesis_count,
        contradiction_count=state.contradiction_count,
        knowledge_boundary_known_count=knowledge_boundary_known_count,
        projection_guard_triggered=state.projection_guard_triggered,
        no_safe_state_claim=state.no_safe_state_claim,
        downstream_consumer_ready=gate.downstream_consumer_ready,
    )
    return O01OtherEntityModelResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        attribution_status=attribution_status,
        reason=reason,
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> O01OtherEntityModelResult:
    entity = _build_minimal_other_entity(
        entity_id="other:minimal",
        reason="o01_disabled",
    )
    state = O01OtherEntityModelState(
        model_id=f"o01-model:{tick_id}",
        tick_index=tick_index,
        entities=(entity,),
        current_user_entity_id=None,
        referenced_other_entity_ids=(),
        third_party_entity_ids=(),
        minimal_other_entity_ids=(entity.entity_id,),
        competing_entity_models=(),
        entity_not_individuated=True,
        perspective_underconstrained=True,
        no_safe_state_claim=True,
        temporary_only_not_stable=False,
        knowledge_boundary_unknown=True,
        contradiction_count=0,
        projection_guard_triggered=False,
        source_lineage=source_lineage,
        last_update_provenance="o01.other_entity_model.disabled",
    )
    gate = O01OtherEntityModelGateDecision(
        current_user_model_ready=False,
        entity_individuation_ready=False,
        clarification_ready=False,
        downstream_consumer_ready=False,
        restrictions=("o01_disabled", "no_safe_state_claim"),
        reason="o01 other-entity modeling disabled in ablation context",
    )
    scope_marker = O01ScopeMarker(
        scope="rt01_hosted_o01_first_slice",
        rt01_hosted_only=True,
        o01_first_slice_only=True,
        o02_o03_not_implemented=True,
        repo_wide_adoption=False,
        reason="o01 disabled path",
    )
    telemetry = O01Telemetry(
        model_id=state.model_id,
        tick_index=tick_index,
        entity_count=1,
        current_user_model_ready=False,
        third_party_models_active=0,
        stable_claim_count=0,
        temporary_hypothesis_count=0,
        contradiction_count=0,
        knowledge_boundary_known_count=0,
        projection_guard_triggered=False,
        no_safe_state_claim=True,
        downstream_consumer_ready=False,
    )
    return O01OtherEntityModelResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        attribution_status=O01AttributionStatus.NO_SAFE_STATE_CLAIM,
        reason=gate.reason,
    )


def _resolve_entity_id_and_kind(signal: O01EntitySignal) -> tuple[str, O01EntityKind]:
    authority = signal.source_authority.strip().lower()
    raw_hint = str(signal.entity_id_hint or "").strip()
    label = str(signal.referent_label or "").strip().lower()
    if authority == "current_user_direct":
        return ("current_user", O01EntityKind.CURRENT_USER_MODEL)
    if authority == "quoted_third_party" or signal.quoted:
        entity_id = raw_hint or f"third_party:{label or 'unknown'}"
        return (entity_id, O01EntityKind.THIRD_PARTY_STUB)
    if authority == "referenced_other":
        entity_id = raw_hint or f"referenced_other:{label or 'unknown'}"
        return (entity_id, O01EntityKind.REFERENCED_OTHER_MODEL)
    entity_id = raw_hint or f"other:{label or 'minimal'}"
    return (entity_id, O01EntityKind.MINIMAL_OTHER_STUB)


def _build_entity_state(
    *,
    entity_id: str,
    kind: O01EntityKind,
    signals: tuple[O01EntitySignal, ...],
    prior: O01EntityState | None,
    competing: bool,
) -> tuple[O01EntityState, int]:
    claims_by_value: Counter[str] = Counter()
    goal_counter: Counter[str] = Counter()
    temporary_counter: Counter[str] = Counter()
    knowledge_counter: Counter[str] = Counter()
    attention_counter: Counter[str] = Counter()
    trust_counter: Counter[str] = Counter()
    belief_counter: Counter[str] = Counter()
    ignorance_counter: Counter[str] = Counter()
    evidence_ids: list[str] = []
    revision_triggers: list[str] = []
    revision_events: list[O01EntityRevisionEvent] = []
    correction_targets: set[str] = set()
    contradiction_count = 0
    stable_claim_turns: dict[str, set[int]] = defaultdict(set)

    confidences: list[float] = []
    for signal in signals:
        value = signal.claim_value.strip()
        if not value:
            continue
        evidence_ids.append(signal.signal_id)
        confidences.append(max(0.0, min(1.0, float(signal.confidence))))
        relation = signal.relation_class.strip().lower()
        if relation == "stable_claim":
            claims_by_value[value] += 1
            stable_claim_turns[value].add(int(signal.turn_index))
        elif relation in {"temporary_state", "state_hypothesis"}:
            temporary_counter[value] += 1
        elif relation in {"goal_hint", "probable_goal"}:
            goal_counter[value] += 1
        elif relation in {"knowledge_boundary", "knowledge_limit"}:
            knowledge_counter[value] += 1
        elif relation == "ignorance":
            ignorance_counter[value] += 1
            knowledge_counter[f"unknown:{value}"] += 1
        elif relation == "attention_target":
            attention_counter[value] += 1
        elif relation in {"trust_marker", "reliability_marker"}:
            trust_counter[value] += 1
        elif relation == "belief_candidate":
            belief_counter[value] += 1
        elif relation == "correction":
            revision_triggers.append(value)
            if signal.target_claim:
                correction_targets.add(signal.target_claim.strip())

    stable_claims: list[str] = []
    temporary_state_hypotheses: list[str] = []
    for claim, count in claims_by_value.items():
        has_multi_turn_repetition = len(stable_claim_turns.get(claim, set())) >= 2
        if count >= 2 and has_multi_turn_repetition and claim not in correction_targets:
            stable_claims.append(claim)
        else:
            temporary_state_hypotheses.append(claim)
    temporary_state_hypotheses.extend(
        value for value, _ in temporary_counter.most_common()
    )

    prior_stable = set(() if prior is None else prior.stable_claims)
    current_stable = set(stable_claims)
    for claim in sorted(current_stable & prior_stable):
        revision_events.append(
            O01EntityRevisionEvent(
                event_kind=O01UpdateEventKind.REINFORCE,
                field_name="stable_claims",
                detail=claim,
                provenance="o01.other_entity_model.reinforce",
            )
        )
    for claim in sorted(prior_stable - current_stable):
        revision_events.append(
            O01EntityRevisionEvent(
                event_kind=O01UpdateEventKind.REVISE,
                field_name="stable_claims",
                detail=claim,
                provenance="o01.other_entity_model.revise",
            )
        )
    for target in sorted(correction_targets & prior_stable):
        revision_events.append(
            O01EntityRevisionEvent(
                event_kind=O01UpdateEventKind.INVALIDATE,
                field_name="stable_claims",
                detail=target,
                provenance="o01.other_entity_model.invalidate",
            )
        )
    for target in sorted(correction_targets - prior_stable):
        revision_events.append(
            O01EntityRevisionEvent(
                event_kind=O01UpdateEventKind.REVISE,
                field_name="stable_claims",
                detail=target,
                provenance="o01.other_entity_model.revise_without_prior_anchor",
            )
        )
    for claim in sorted(current_stable):
        opposite = _invert_claim(claim)
        if opposite in current_stable:
            contradiction_count += 1
            revision_events.append(
                O01EntityRevisionEvent(
                    event_kind=O01UpdateEventKind.CONTRADICTION_PRESERVED,
                    field_name="stable_claims",
                    detail=f"{claim}<->{opposite}",
                    provenance="o01.other_entity_model.contradiction",
                )
            )
    if competing:
        revision_events.append(
            O01EntityRevisionEvent(
                event_kind=O01UpdateEventKind.ENTITY_SPLIT_REQUIRED,
                field_name="entity_id",
                detail=entity_id,
                provenance="o01.other_entity_model.entity_split",
            )
        )
    if not stable_claims and not temporary_state_hypotheses:
        revision_events.append(
            O01EntityRevisionEvent(
                event_kind=O01UpdateEventKind.NO_SAFE_STATE_CLAIM,
                field_name="claims",
                detail="no_grounded_claims",
                provenance="o01.other_entity_model.no_safe_state_claim",
            )
        )

    confidence = max(confidences) if confidences else 0.0
    identity_confidence = max(
        0.05,
        min(
            1.0,
            confidence
            + (0.2 if kind is O01EntityKind.CURRENT_USER_MODEL else 0.0)
            + (0.1 if len(signals) >= 2 else 0.0)
            - (0.2 if competing else 0.0),
        ),
    )
    uncertainty_map = {
        "stable_claims": max(0.0, 1.0 - min(1.0, len(stable_claims) * 0.4)),
        "temporary_state_hypotheses": max(
            0.0, 1.0 - min(1.0, len(temporary_state_hypotheses) * 0.2)
        ),
        "goals": max(0.0, 1.0 - min(1.0, len(goal_counter) * 0.3)),
        "knowledge_boundary": max(0.0, 1.0 - min(1.0, len(knowledge_counter) * 0.3)),
    }
    belief_overlay = O01BeliefOverlay(
        belief_candidates=tuple(item for item, _ in belief_counter.most_common(4)),
        ignorance_candidates=tuple(item for item, _ in ignorance_counter.most_common(4)),
        belief_attribution_uncertainty=max(0.0, min(1.0, uncertainty_map["stable_claims"])),
        evidence_basis=tuple(dict.fromkeys(evidence_ids)),
        revision_triggers=tuple(dict.fromkeys(revision_triggers)),
    )
    entity_state = O01EntityState(
        entity_id=entity_id,
        entity_kind=kind,
        model_scope=O01ModelScope.BOUNDED_RUNTIME,
        identity_confidence=identity_confidence,
        stable_claims=tuple(sorted(dict.fromkeys(stable_claims))),
        temporary_state_hypotheses=tuple(sorted(dict.fromkeys(temporary_state_hypotheses))),
        probable_goals=tuple(item for item, _ in goal_counter.most_common(4)),
        knowledge_boundary_estimates=tuple(item for item, _ in knowledge_counter.most_common(4)),
        attention_targets=tuple(item for item, _ in attention_counter.most_common(4)),
        trust_or_reliability_markers=tuple(item for item, _ in trust_counter.most_common(4)),
        uncertainty_map=uncertainty_map,
        interaction_history_links=tuple(dict.fromkeys(evidence_ids)),
        revision_history=tuple(revision_events),
        belief_overlay=belief_overlay,
        provenance="o01.other_entity_model.entity_state",
    )
    return entity_state, contradiction_count


def _build_minimal_other_entity(*, entity_id: str, reason: str) -> O01EntityState:
    return O01EntityState(
        entity_id=entity_id,
        entity_kind=O01EntityKind.MINIMAL_OTHER_STUB,
        model_scope=O01ModelScope.INTERACTION_LOCAL,
        identity_confidence=0.05,
        stable_claims=(),
        temporary_state_hypotheses=("minimal_other_stub",),
        probable_goals=(),
        knowledge_boundary_estimates=(),
        attention_targets=(),
        trust_or_reliability_markers=(),
        uncertainty_map={
            "stable_claims": 1.0,
            "temporary_state_hypotheses": 1.0,
            "goals": 1.0,
            "knowledge_boundary": 1.0,
        },
        interaction_history_links=(),
        revision_history=(
            O01EntityRevisionEvent(
                event_kind=O01UpdateEventKind.NO_SAFE_STATE_CLAIM,
                field_name="claims",
                detail=reason,
                provenance="o01.other_entity_model.minimal_stub",
            ),
        ),
        belief_overlay=O01BeliefOverlay(
            belief_candidates=(),
            ignorance_candidates=(),
            belief_attribution_uncertainty=1.0,
            evidence_basis=(),
            revision_triggers=(reason,),
        ),
        provenance="o01.other_entity_model.minimal_stub",
    )


def _belief_overlay_underconstrained(
    *,
    entities: tuple[O01EntityState, ...],
    current_user_entity_id: str | None,
) -> bool:
    if not current_user_entity_id:
        return False
    for entity in entities:
        if entity.entity_id != current_user_entity_id:
            continue
        if (
            entity.belief_overlay.ignorance_candidates
            and entity.belief_overlay.belief_attribution_uncertainty >= 0.8
        ):
            return True
    return False


def _invert_claim(claim: str) -> str:
    token = claim.strip()
    if token.startswith("not:"):
        return token.removeprefix("not:")
    return f"not:{token}"
