from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from substrate.affordances.models import AffordanceResult
from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.regulation.models import NeedAxis, RegulationConfidence, RegulationState
from substrate.regulatory_preferences.models import (
    BlockedPreferenceUpdate,
    OutcomeTrace,
    PreferenceConflictState,
    PreferenceContext,
    PreferenceEntry,
    PreferenceSign,
    PreferenceState,
    PreferenceTimeHorizon,
    PreferenceUncertainty,
    PreferenceUpdateEvent,
    PreferenceUpdateKind,
    PreferenceUpdateResult,
    PreferenceUpdateStatus,
)
from substrate.regulatory_preferences.policy import evaluate_preference_downstream_gate
from substrate.regulatory_preferences.telemetry import (
    build_preference_telemetry,
    preference_result_snapshot,
)
from substrate.transition import execute_transition


ATTEMPTED_PREFERENCE_PATHS: tuple[str, ...] = (
    "preferences.validate_input_shape",
    "preferences.validate_affordance_identity",
    "preferences.credit_assignment",
    "preferences.short_long_horizon_update",
    "preferences.context_conditioning",
    "preferences.conflict_registration",
    "preferences.freeze_or_no_claim",
    "preferences.decay_update",
    "preferences.downstream_gate",
)


def create_empty_preference_state() -> PreferenceState:
    return PreferenceState(entries=(), unresolved_updates=(), conflict_index=(), frozen_updates=())


def update_regulatory_preferences(
    regulation_state: RegulationState,
    affordance_result: AffordanceResult,
    outcome_traces: tuple[OutcomeTrace, ...] | list[OutcomeTrace],
    preference_state: PreferenceState | None = None,
    context: PreferenceContext | None = None,
) -> PreferenceUpdateResult:
    context = context or PreferenceContext()
    prior_state = preference_state or create_empty_preference_state()

    is_valid, reason, normalized_outcomes = validate_preference_inputs(
        regulation_state=regulation_state,
        affordance_result=affordance_result,
        outcome_traces=outcome_traces,
        preference_state=prior_state,
        context=context,
    )
    if not is_valid:
        return _abstain_result(
            regulation_state=regulation_state,
            affordance_result=affordance_result if isinstance(affordance_result, AffordanceResult) else None,
            prior_state=prior_state,
            source_lineage=context.source_lineage,
            reason=reason,
        )

    decayed_entries, decay_events, decay_ids = _apply_decay(prior_state.entries, context=context)
    entry_map: dict[tuple[object, tuple[str, ...]], PreferenceEntry] = {
        _entry_key(entry.option_class_id, entry.context_scope): entry for entry in decayed_entries
    }

    available_options = {candidate.option_class for candidate in affordance_result.candidates}
    affordance_ids = {candidate.affordance_id for candidate in affordance_result.candidates}
    source_lineage = tuple(
        dict.fromkeys(
            (
                *context.source_lineage,
                *affordance_result.telemetry.source_lineage,
            )
        )
    )
    processed_episode_ids: list[str] = []
    updated_entry_ids: list[str] = []
    blocked_updates: list[BlockedPreferenceUpdate] = []
    update_events: list[PreferenceUpdateEvent] = list(decay_events)
    blocked_reasons: list[str] = []
    short_term_signal_count = 0
    long_term_signal_count = 0
    context_keys_used: set[str] = set()

    for outcome in normalized_outcomes:
        processed_episode_ids.append(outcome.episode_id)
        context_scope = outcome.context_scope if outcome.context_scope else ("global",)
        for context_key in context_scope:
            context_keys_used.add(context_key)

        block = _blocked_update_if_any(
            outcome=outcome,
            available_options=available_options,
            affordance_ids=affordance_ids,
            context=context,
        )
        if block is not None:
            blocked_updates.append(block)
            if block.uncertainty == PreferenceUncertainty.ATTRIBUTION_BLOCKED:
                blocked_reasons.append(block.reason)
            update_events.append(
                PreferenceUpdateEvent(
                    event_id=f"pref-ev-{uuid4().hex[:10]}",
                    entry_id=None,
                    prior_entry_ref=None,
                    observed_episode_ref=outcome.episode_id,
                    update_kind=PreferenceUpdateKind.FREEZE if block.frozen else PreferenceUpdateKind.NO_CLAIM,
                    reason_tags=(block.uncertainty.value,),
                    provenance=block.provenance,
                    delta_strength=0.0,
                    short_term_delta=outcome.observed_short_term_delta,
                    long_term_delta=outcome.observed_long_term_delta,
                )
            )
            continue

        short_term_signal_count += 1
        has_long = outcome.observed_long_term_delta is not None
        if has_long:
            long_term_signal_count += 1
        weighted_signal = _weighted_signal(
            short_term=outcome.observed_short_term_delta,
            long_term=outcome.observed_long_term_delta,
        )

        key = _entry_key(outcome.option_class_id, context_scope)
        existing = entry_map.get(key)
        if existing is None:
            created, event = _create_entry_from_outcome(
                outcome=outcome,
                context_scope=context_scope,
                weighted_signal=weighted_signal,
                context=context,
            )
            entry_map[key] = created
            update_events.append(event)
            updated_entry_ids.append(created.entry_id)
            continue

        updated, event, optional_block = _update_existing_entry(
            existing=existing,
            outcome=outcome,
            context_scope=context_scope,
            weighted_signal=weighted_signal,
            context=context,
        )
        entry_map[key] = updated
        update_events.append(event)
        updated_entry_ids.append(updated.entry_id)
        if optional_block is not None:
            blocked_updates.append(optional_block)
            if optional_block.uncertainty == PreferenceUncertainty.ATTRIBUTION_BLOCKED:
                blocked_reasons.append(optional_block.reason)

    final_entries = tuple(sorted(entry_map.values(), key=lambda item: item.entry_id))
    frozen_updates = tuple(block for block in blocked_updates if block.frozen)
    conflict_index = tuple(
        entry.entry_id for entry in final_entries if entry.conflict_state == PreferenceConflictState.CONFLICTING
    )
    next_state = PreferenceState(
        entries=final_entries,
        unresolved_updates=tuple(blocked_updates),
        conflict_index=conflict_index,
        frozen_updates=frozen_updates,
        schema_version=prior_state.schema_version,
        last_updated_step=prior_state.last_updated_step + context.step_delta,
    )
    gate = evaluate_preference_downstream_gate(next_state)
    telemetry = build_preference_telemetry(
        state=next_state,
        source_lineage=source_lineage,
        input_regulation_snapshot_ref=f"regulation-step-{regulation_state.last_updated_step}",
        input_affordance_ids=tuple(sorted(affordance_ids)),
        processed_episode_ids=tuple(processed_episode_ids),
        updated_entry_ids=tuple(sorted(set(updated_entry_ids))),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        short_term_signal_count=short_term_signal_count,
        long_term_signal_count=long_term_signal_count,
        context_keys_used=tuple(sorted(context_keys_used)),
        decay_events=tuple(decay_ids),
        downstream_gate=gate,
        causal_basis=(
            "typed R02 outcome traces with credit assignment over short/long regulation deltas"
        ),
        attempted_update_paths=ATTEMPTED_PREFERENCE_PATHS,
    )
    abstain = bool(not next_state.entries and blocked_updates)
    abstain_reason = "all updates blocked by attribution/uncertainty constraints" if abstain else None

    return PreferenceUpdateResult(
        updated_preference_state=next_state,
        update_events=tuple(update_events),
        blocked_updates=tuple(blocked_updates),
        downstream_gate=gate,
        telemetry=telemetry,
        regulation_state_ref=regulation_state,
        no_final_selection_performed=True,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def validate_preference_inputs(
    *,
    regulation_state: object,
    affordance_result: object,
    outcome_traces: object,
    preference_state: object,
    context: object,
) -> tuple[bool, str, tuple[OutcomeTrace, ...]]:
    if not isinstance(regulation_state, RegulationState):
        return False, "regulation_state must be RegulationState", ()
    if not isinstance(affordance_result, AffordanceResult):
        return False, "affordance_result must be AffordanceResult", ()
    if not isinstance(preference_state, PreferenceState):
        return False, "preference_state must be PreferenceState", ()
    if not isinstance(context, PreferenceContext):
        return False, "context must be PreferenceContext", ()
    if not isinstance(outcome_traces, (tuple, list)):
        return False, "outcome_traces must be tuple/list of OutcomeTrace", ()
    normalized: list[OutcomeTrace] = []
    for trace in outcome_traces:
        if not isinstance(trace, OutcomeTrace):
            return False, "outcome_traces must contain only OutcomeTrace objects", ()
        normalized.append(trace)
    return True, "", tuple(normalized)


def preference_result_to_payload(result: PreferenceUpdateResult) -> dict[str, object]:
    return preference_result_snapshot(result)


def persist_preference_result_via_f01(
    *,
    result: PreferenceUpdateResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("r03-preference-update",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"preferences-step-{result.updated_preference_state.last_updated_step}",
            "preference_snapshot": preference_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _entry_key(option_class_id: object, context_scope: tuple[str, ...]) -> tuple[object, tuple[str, ...]]:
    return option_class_id, tuple(context_scope)


def _weighted_signal(*, short_term: float, long_term: float | None) -> float:
    if long_term is None:
        return round(short_term * 0.35, 4)
    return round((short_term * 0.45) + (long_term * 0.55), 4)


def _blocked_update_if_any(
    *,
    outcome: OutcomeTrace,
    available_options: set[object],
    affordance_ids: set[str],
    context: PreferenceContext,
) -> BlockedPreferenceUpdate | None:
    if outcome.option_class_id not in available_options:
        return BlockedPreferenceUpdate(
            episode_id=outcome.episode_id,
            option_class_id=outcome.option_class_id,
            uncertainty=PreferenceUncertainty.ATTRIBUTION_BLOCKED,
            reason="option_class absent in upstream R02 affordance landscape",
            frozen=True,
            provenance=outcome.provenance or "r03.credit_assignment",
        )
    if outcome.affordance_id is not None and outcome.affordance_id not in affordance_ids:
        return BlockedPreferenceUpdate(
            episode_id=outcome.episode_id,
            option_class_id=outcome.option_class_id,
            uncertainty=PreferenceUncertainty.ATTRIBUTION_BLOCKED,
            reason="affordance_id not traceable to upstream R02 candidates",
            frozen=True,
            provenance=outcome.provenance or "r03.credit_assignment",
        )
    if context.freeze_on_mixed_causes and outcome.mixed_causes:
        return BlockedPreferenceUpdate(
            episode_id=outcome.episode_id,
            option_class_id=outcome.option_class_id,
            uncertainty=PreferenceUncertainty.ATTRIBUTION_BLOCKED,
            reason="mixed causes prevent reliable credit assignment",
            frozen=True,
            provenance=outcome.provenance or "r03.credit_assignment",
        )
    if outcome.observed_long_term_delta is None and not outcome.delayed_window_complete:
        return BlockedPreferenceUpdate(
            episode_id=outcome.episode_id,
            option_class_id=outcome.option_class_id,
            uncertainty=PreferenceUncertainty.DELAYED_EFFECT_UNRESOLVED,
            reason="long-term effect unresolved for delayed credit assignment",
            frozen=True,
            provenance=outcome.provenance or "r03.temporal_credit",
        )
    if context.require_long_term_signal and outcome.observed_long_term_delta is None:
        return BlockedPreferenceUpdate(
            episode_id=outcome.episode_id,
            option_class_id=outcome.option_class_id,
            uncertainty=PreferenceUncertainty.INSUFFICIENT_EVIDENCE,
            reason="long-term signal required by context but absent",
            frozen=True,
            provenance=outcome.provenance or "r03.temporal_credit",
        )
    return None


def _create_entry_from_outcome(
    *,
    outcome: OutcomeTrace,
    context_scope: tuple[str, ...],
    weighted_signal: float,
    context: PreferenceContext,
) -> tuple[PreferenceEntry, PreferenceUpdateEvent]:
    sign = _sign_from_value(weighted_signal)
    has_long = outcome.observed_long_term_delta is not None
    short_sign = _sign_from_value(outcome.observed_short_term_delta)
    long_sign = _sign_from_value(outcome.observed_long_term_delta or 0.0)
    conflict = (
        has_long
        and short_sign not in {PreferenceSign.NEUTRAL, PreferenceSign.UNKNOWN}
        and long_sign not in {PreferenceSign.NEUTRAL, PreferenceSign.UNKNOWN}
        and short_sign != long_sign
    )
    confidence = _derive_confidence(
        base=outcome.attribution_confidence,
        support_count=1,
        has_long=has_long,
        conflict=conflict,
    )
    status = (
        PreferenceUpdateStatus.PROVISIONAL
        if confidence != RegulationConfidence.HIGH or not has_long
        else PreferenceUpdateStatus.ACTIVE
    )
    conflict_state = PreferenceConflictState.CONFLICTING if conflict else PreferenceConflictState.NONE
    strength = round(min(1.0, max(0.05, abs(weighted_signal) * context.learning_rate)), 4)
    entry = PreferenceEntry(
        entry_id=f"pref-{uuid4().hex[:10]}",
        option_class_id=outcome.option_class_id,
        target_need_or_set=outcome.target_need_or_set,
        preference_sign=sign,
        preference_strength=strength,
        expected_short_term_delta=round(outcome.observed_short_term_delta, 4),
        expected_long_term_delta=round(outcome.observed_long_term_delta or 0.0, 4),
        confidence=confidence,
        context_scope=context_scope,
        time_horizon=_derive_horizon(
            short_delta=outcome.observed_short_term_delta,
            long_delta=outcome.observed_long_term_delta,
        ),
        conflict_state=conflict_state,
        episode_support=1,
        staleness_steps=0,
        decay_marker=1.0,
        last_update_provenance=_build_provenance(outcome),
        update_status=status,
    )
    if conflict:
        kind = PreferenceUpdateKind.CONFLICT_REGISTER
        reason_tags = ("provisional_cold_start", "short_long_conflict")
    elif sign == PreferenceSign.POSITIVE:
        kind = PreferenceUpdateKind.STRENGTHEN
        reason_tags = ("provisional_cold_start", "positive_delta")
    elif sign == PreferenceSign.NEGATIVE:
        kind = PreferenceUpdateKind.WEAKEN
        reason_tags = ("provisional_cold_start", "negative_delta")
    else:
        kind = PreferenceUpdateKind.NO_CLAIM
        reason_tags = ("provisional_cold_start", "neutral_delta")

    event = PreferenceUpdateEvent(
        event_id=f"pref-ev-{uuid4().hex[:10]}",
        entry_id=entry.entry_id,
        prior_entry_ref=None,
        observed_episode_ref=outcome.episode_id,
        update_kind=kind,
        reason_tags=reason_tags,
        provenance=entry.last_update_provenance,
        delta_strength=entry.preference_strength,
        short_term_delta=outcome.observed_short_term_delta,
        long_term_delta=outcome.observed_long_term_delta,
    )
    return entry, event


def _update_existing_entry(
    *,
    existing: PreferenceEntry,
    outcome: OutcomeTrace,
    context_scope: tuple[str, ...],
    weighted_signal: float,
    context: PreferenceContext,
) -> tuple[PreferenceEntry, PreferenceUpdateEvent, BlockedPreferenceUpdate | None]:
    prior_score = _signed_score(existing.preference_sign, existing.preference_strength)
    combined = round(
        ((1.0 - context.learning_rate) * prior_score) + (context.learning_rate * weighted_signal),
        4,
    )
    new_sign = _sign_from_value(combined)
    new_strength = round(min(1.0, abs(combined)), 4)
    has_long = outcome.observed_long_term_delta is not None
    support_count = existing.episode_support + 1
    short_avg = round(
        ((existing.expected_short_term_delta * existing.episode_support) + outcome.observed_short_term_delta)
        / support_count,
        4,
    )
    long_for_avg = outcome.observed_long_term_delta if has_long else existing.expected_long_term_delta
    long_avg = round(
        ((existing.expected_long_term_delta * existing.episode_support) + long_for_avg) / support_count,
        4,
    )
    evidence_sign = _sign_from_value(weighted_signal)
    has_conflicting_evidence = (
        existing.preference_sign not in {PreferenceSign.UNKNOWN, PreferenceSign.NEUTRAL}
        and evidence_sign not in {PreferenceSign.UNKNOWN, PreferenceSign.NEUTRAL}
        and existing.preference_sign != evidence_sign
    )
    conflict_state = (
        PreferenceConflictState.CONFLICTING if has_conflicting_evidence else existing.conflict_state
    )
    confidence = _derive_confidence(
        base=min(existing.confidence, outcome.attribution_confidence, key=_confidence_rank),
        support_count=support_count,
        has_long=has_long,
        conflict=has_conflicting_evidence,
    )
    update_status = (
        PreferenceUpdateStatus.PROVISIONAL
        if confidence == RegulationConfidence.LOW or not has_long
        else PreferenceUpdateStatus.ACTIVE
    )

    blocked: BlockedPreferenceUpdate | None = None
    if has_conflicting_evidence and abs(prior_score) >= context.conflict_threshold and abs(weighted_signal) >= context.conflict_threshold and abs(combined) < context.conflict_threshold:
        update_status = PreferenceUpdateStatus.FROZEN
        blocked = BlockedPreferenceUpdate(
            episode_id=outcome.episode_id,
            option_class_id=outcome.option_class_id,
            uncertainty=PreferenceUncertainty.CONFLICTING_EVIDENCE,
            reason="conflicting evidence froze update before forced sign collapse",
            frozen=True,
            provenance=outcome.provenance or "r03.conflict_handling",
        )

    updated = replace(
        existing,
        target_need_or_set=outcome.target_need_or_set or existing.target_need_or_set,
        preference_sign=new_sign,
        preference_strength=new_strength,
        expected_short_term_delta=short_avg,
        expected_long_term_delta=long_avg,
        confidence=confidence,
        context_scope=context_scope,
        time_horizon=_merge_horizon(
            existing.time_horizon,
            _derive_horizon(
                short_delta=outcome.observed_short_term_delta,
                long_delta=outcome.observed_long_term_delta,
            ),
        ),
        conflict_state=conflict_state,
        episode_support=support_count,
        staleness_steps=0,
        decay_marker=1.0,
        last_update_provenance=_build_provenance(outcome),
        update_status=update_status,
    )

    if blocked is not None:
        kind = PreferenceUpdateKind.FREEZE
        reason_tags = ("conflicting_evidence",)
    elif has_conflicting_evidence and new_sign != existing.preference_sign:
        kind = PreferenceUpdateKind.INVERT
        reason_tags = ("conflicting_evidence", "sign_inverted")
    elif has_conflicting_evidence:
        kind = PreferenceUpdateKind.CONFLICT_REGISTER
        reason_tags = ("conflicting_evidence",)
    elif updated.preference_strength > existing.preference_strength:
        kind = PreferenceUpdateKind.STRENGTHEN
        reason_tags = ("consistent_evidence",)
    elif updated.preference_strength < existing.preference_strength:
        kind = PreferenceUpdateKind.WEAKEN
        reason_tags = ("counter_evidence",)
    else:
        kind = PreferenceUpdateKind.NO_CLAIM
        reason_tags = ("no_material_change",)

    event = PreferenceUpdateEvent(
        event_id=f"pref-ev-{uuid4().hex[:10]}",
        entry_id=updated.entry_id,
        prior_entry_ref=existing.entry_id,
        observed_episode_ref=outcome.episode_id,
        update_kind=kind,
        reason_tags=reason_tags,
        provenance=updated.last_update_provenance,
        delta_strength=round(updated.preference_strength - existing.preference_strength, 4),
        short_term_delta=outcome.observed_short_term_delta,
        long_term_delta=outcome.observed_long_term_delta,
    )
    return updated, event, blocked


def _apply_decay(
    entries: tuple[PreferenceEntry, ...], *, context: PreferenceContext
) -> tuple[tuple[PreferenceEntry, ...], tuple[PreferenceUpdateEvent, ...], tuple[str, ...]]:
    decayed: list[PreferenceEntry] = []
    events: list[PreferenceUpdateEvent] = []
    decay_ids: list[str] = []
    decay_factor = max(0.0, 1.0 - (context.decay_per_step * context.step_delta))
    for entry in entries:
        new_strength = round(entry.preference_strength * decay_factor, 4)
        new_staleness = entry.staleness_steps + context.step_delta
        new_status = entry.update_status
        if new_staleness > 0 and entry.update_status != PreferenceUpdateStatus.FROZEN:
            new_status = PreferenceUpdateStatus.STALE
        updated = replace(
            entry,
            preference_strength=new_strength,
            staleness_steps=new_staleness,
            decay_marker=decay_factor,
            update_status=new_status,
        )
        decayed.append(updated)
        if new_strength != entry.preference_strength:
            decay_event_id = f"pref-decay-{uuid4().hex[:10]}"
            decay_ids.append(decay_event_id)
            events.append(
                PreferenceUpdateEvent(
                    event_id=decay_event_id,
                    entry_id=updated.entry_id,
                    prior_entry_ref=entry.entry_id,
                    observed_episode_ref="__decay__",
                    update_kind=PreferenceUpdateKind.DECAY,
                    reason_tags=("temporal_decay",),
                    provenance=f"r03.decay:{updated.entry_id}",
                    delta_strength=round(updated.preference_strength - entry.preference_strength, 4),
                    short_term_delta=None,
                    long_term_delta=None,
                )
            )
    return tuple(decayed), tuple(events), tuple(decay_ids)


def _sign_from_value(value: float) -> PreferenceSign:
    if value > 0.05:
        return PreferenceSign.POSITIVE
    if value < -0.05:
        return PreferenceSign.NEGATIVE
    return PreferenceSign.NEUTRAL


def _signed_score(sign: PreferenceSign, strength: float) -> float:
    if sign == PreferenceSign.POSITIVE:
        return strength
    if sign == PreferenceSign.NEGATIVE:
        return -strength
    return 0.0


def _derive_horizon(*, short_delta: float, long_delta: float | None) -> PreferenceTimeHorizon:
    if long_delta is None:
        return PreferenceTimeHorizon.SHORT_TERM
    short_sign = _sign_from_value(short_delta)
    long_sign = _sign_from_value(long_delta)
    if short_sign != long_sign and short_sign != PreferenceSign.NEUTRAL and long_sign != PreferenceSign.NEUTRAL:
        return PreferenceTimeHorizon.MIXED
    if abs(long_delta) >= abs(short_delta):
        return PreferenceTimeHorizon.LONG_TERM
    return PreferenceTimeHorizon.SHORT_TERM


def _merge_horizon(
    existing: PreferenceTimeHorizon, current: PreferenceTimeHorizon
) -> PreferenceTimeHorizon:
    if existing == current:
        return existing
    if PreferenceTimeHorizon.MIXED in {existing, current}:
        return PreferenceTimeHorizon.MIXED
    if existing == PreferenceTimeHorizon.UNKNOWN:
        return current
    if current == PreferenceTimeHorizon.UNKNOWN:
        return existing
    return PreferenceTimeHorizon.MIXED


def _derive_confidence(
    *,
    base: RegulationConfidence,
    support_count: int,
    has_long: bool,
    conflict: bool,
) -> RegulationConfidence:
    if conflict:
        return RegulationConfidence.LOW
    if support_count >= 3 and has_long and base != RegulationConfidence.LOW:
        return RegulationConfidence.HIGH
    if support_count >= 2 and base == RegulationConfidence.HIGH:
        return RegulationConfidence.MEDIUM if not has_long else RegulationConfidence.HIGH
    return RegulationConfidence.MEDIUM if has_long else RegulationConfidence.LOW


def _confidence_rank(level: RegulationConfidence) -> int:
    if level == RegulationConfidence.HIGH:
        return 3
    if level == RegulationConfidence.MEDIUM:
        return 2
    return 1


def _build_provenance(outcome: OutcomeTrace) -> str:
    parts = [
        f"episode:{outcome.episode_id}",
        f"option:{outcome.option_class_id.value}",
    ]
    if outcome.affordance_id:
        parts.append(f"affordance:{outcome.affordance_id}")
    if outcome.source_ref:
        parts.append(f"source:{outcome.source_ref}")
    if outcome.provenance:
        parts.append(f"trace:{outcome.provenance}")
    return "|".join(parts)


def _abstain_result(
    *,
    regulation_state: object,
    affordance_result: AffordanceResult | None,
    prior_state: PreferenceState,
    source_lineage: tuple[str, ...],
    reason: str,
) -> PreferenceUpdateResult:
    next_state = PreferenceState(
        entries=prior_state.entries,
        unresolved_updates=prior_state.unresolved_updates,
        conflict_index=prior_state.conflict_index,
        frozen_updates=prior_state.frozen_updates,
        schema_version=prior_state.schema_version,
        last_updated_step=prior_state.last_updated_step,
    )
    gate = evaluate_preference_downstream_gate(next_state)
    telemetry = build_preference_telemetry(
        state=next_state,
        source_lineage=source_lineage,
        input_regulation_snapshot_ref="invalid-input",
        input_affordance_ids=tuple(
            candidate.affordance_id for candidate in (affordance_result.candidates if affordance_result else ())
        ),
        processed_episode_ids=(),
        updated_entry_ids=(),
        blocked_reasons=(reason,),
        short_term_signal_count=0,
        long_term_signal_count=0,
        context_keys_used=(),
        decay_events=(),
        downstream_gate=gate,
        causal_basis="invalid R03 typed input -> abstain",
        attempted_update_paths=ATTEMPTED_PREFERENCE_PATHS,
    )
    return PreferenceUpdateResult(
        updated_preference_state=next_state,
        update_events=(),
        blocked_updates=(),
        downstream_gate=gate,
        telemetry=telemetry,
        regulation_state_ref=regulation_state if isinstance(regulation_state, RegulationState) else RegulationState(needs=(), confidence=RegulationConfidence.LOW),
        no_final_selection_performed=True,
        abstain=True,
        abstain_reason=reason,
    )
