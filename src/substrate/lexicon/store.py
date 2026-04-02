from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.lexicon.models import (
    LexicalAcquisitionMode,
    DEFAULT_LEXICON_SCHEMA_VERSION,
    DEFAULT_LEXICON_TAXONOMY_VERSION,
    DEFAULT_LEXICON_VERSION,
    LexicalAcquisitionState,
    LexicalAcquisitionStatus,
    LexicalCoarseSemanticType,
    LexicalCompositionProfile,
    LexicalCompositionRole,
    LexicalConflictState,
    LexicalExampleRecord,
    LexicalExampleStatus,
    LexicalEntry,
    LexicalEntryProposal,
    LexicalEpisodeRecordContext,
    LexicalEpisodeRecordResult,
    LexicalEpisodeStatus,
    LexicalHypothesisConsolidationContext,
    LexicalHypothesisStatus,
    LexicalHypothesisUpdateResult,
    LexicalLearningGateDecision,
    LexicalReferenceProfile,
    LexicalSenseHypothesis,
    LexicalSenseRecord,
    LexicalSenseStatus,
    LexicalUsageEpisode,
    LexiconBlockedUpdate,
    LexiconGateDecision,
    LexiconQueryContext,
    LexiconQueryRecord,
    LexiconQueryRequest,
    LexiconQueryResult,
    LexiconState,
    LexiconUpdateContext,
    LexiconUpdateEvent,
    LexiconUpdateKind,
    LexiconUpdateResult,
    ProvisionalLexicalHypothesis,
    SurfaceFormRecord,
    UnknownLexicalItem,
    UnknownLexicalObservation,
)
from substrate.lexicon.policy import (
    build_lexicon_gate_decision,
    evaluate_lexical_learning_downstream_gate,
    evaluate_lexicon_downstream_gate,
)
from substrate.lexicon.telemetry import build_lexical_telemetry, lexicon_result_snapshot
from substrate.transition import execute_transition


ATTEMPTED_LEXICON_UPDATE_PATHS: tuple[str, ...] = (
    "lexicon.validate_typed_update_input",
    "lexicon.version_compatibility_guard",
    "lexicon.entry_create_or_update",
    "lexicon.conflict_and_unknown_registration",
    "lexicon.acquisition_state_update",
    "lexicon.decay_and_staleness_update",
    "lexicon.downstream_gate",
)

ATTEMPTED_LEXICON_QUERY_PATHS: tuple[str, ...] = (
    "lexicon.validate_typed_query_input",
    "lexicon.version_compatibility_guard",
    "lexicon.surface_variant_matching",
    "lexicon.ambiguity_and_unknown_exposure",
    "lexicon.downstream_gate",
)

ATTEMPTED_LEXICON_EPISODE_PATHS: tuple[str, ...] = (
    "lexicon.validate_typed_episode_input",
    "lexicon.version_compatibility_guard",
    "lexicon.episode_record",
    "lexicon.hypothesis_support_conflict_update",
    "lexicon.learning_downstream_gate",
)

ATTEMPTED_LEXICON_HYPOTHESIS_PATHS: tuple[str, ...] = (
    "lexicon.validate_typed_hypothesis_input",
    "lexicon.version_compatibility_guard",
    "lexicon.promotion_eligibility_check",
    "lexicon.promote_or_freeze_hypothesis",
    "lexicon.learning_downstream_gate",
)


def create_empty_lexicon_state(
    *,
    schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION,
    lexicon_version: str = DEFAULT_LEXICON_VERSION,
    taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION,
) -> LexiconState:
    return LexiconState(
        entries=(),
        unknown_items=(),
        usage_episodes=(),
        provisional_hypotheses=(),
        unresolved_updates=(),
        conflict_index=(),
        frozen_updates=(),
        schema_version=schema_version,
        lexicon_version=lexicon_version,
        taxonomy_version=taxonomy_version,
        last_updated_step=0,
    )


def create_seed_lexicon_state() -> LexiconState:
    return LexiconState(
        entries=_seed_entries(),
        unknown_items=(),
        usage_episodes=(),
        provisional_hypotheses=(),
        unresolved_updates=(),
        conflict_index=(),
        frozen_updates=(),
        schema_version=DEFAULT_LEXICON_SCHEMA_VERSION,
        lexicon_version=DEFAULT_LEXICON_VERSION,
        taxonomy_version=DEFAULT_LEXICON_TAXONOMY_VERSION,
        last_updated_step=0,
    )


def create_or_update_lexicon_state(
    *,
    lexicon_state: LexiconState | None = None,
    entry_proposals: tuple[LexicalEntryProposal, ...] | list[LexicalEntryProposal] = (),
    unknown_observations: tuple[UnknownLexicalObservation, ...] | list[UnknownLexicalObservation] = (),
    context: LexiconUpdateContext | None = None,
) -> LexiconUpdateResult:
    state = lexicon_state or create_seed_lexicon_state()
    if not isinstance(state, LexiconState):
        raise TypeError("lexicon_state must be LexiconState")
    if context is None:
        context = LexiconUpdateContext()
    if not isinstance(context, LexiconUpdateContext):
        raise TypeError("context must be LexiconUpdateContext")
    if not isinstance(entry_proposals, (tuple, list)):
        raise TypeError("entry_proposals must be tuple/list of LexicalEntryProposal")
    if not isinstance(unknown_observations, (tuple, list)):
        raise TypeError("unknown_observations must be tuple/list of UnknownLexicalObservation")

    proposals = tuple(entry_proposals)
    unknowns = tuple(unknown_observations)
    if not all(isinstance(proposal, LexicalEntryProposal) for proposal in proposals):
        raise TypeError("entry_proposals must contain only LexicalEntryProposal")
    if not all(isinstance(observation, UnknownLexicalObservation) for observation in unknowns):
        raise TypeError("unknown_observations must contain only UnknownLexicalObservation")

    compatibility_markers = _compatibility_markers(
        state=state,
        expected_schema_version=context.expected_schema_version,
        expected_lexicon_version=context.expected_lexicon_version,
        expected_taxonomy_version=context.expected_taxonomy_version,
    )
    if compatibility_markers:
        blocked = LexiconBlockedUpdate(
            surface_form="__lexicon__",
            reason="version compatibility mismatch blocked lexicon update",
            frozen=True,
            provenance="lexicon.compatibility_guard",
            compatibility_marker="|".join(compatibility_markers),
        )
        next_state = replace(
            state,
            usage_episodes=state.usage_episodes,
            provisional_hypotheses=state.provisional_hypotheses,
            unresolved_updates=state.unresolved_updates + (blocked,),
            frozen_updates=state.frozen_updates + (blocked,),
        )
        gate = evaluate_lexicon_downstream_gate(next_state)
        telemetry = build_lexical_telemetry(
            state=next_state,
            source_lineage=context.source_lineage,
            processed_entry_ids=(),
            new_entry_count=0,
            updated_entry_count=0,
            ambiguity_reasons=("compatibility_mismatch",),
            queried_forms=(),
            matched_entry_ids=(),
            no_match_count=0,
            compatibility_markers=compatibility_markers,
            attempted_paths=ATTEMPTED_LEXICON_UPDATE_PATHS,
            downstream_gate=gate,
            causal_basis="lexicon update blocked due to incompatible schema/version contract",
        )
        return LexiconUpdateResult(
            updated_state=next_state,
            update_events=(),
            blocked_updates=(blocked,),
            downstream_gate=gate,
            telemetry=telemetry,
            no_final_meaning_resolution_performed=True,
            abstain=True,
            abstain_reason="version compatibility mismatch",
        )

    decayed_entries, decay_events = _apply_decay(state.entries, context=context)
    compatible_entries, entry_compatibility_blocks, entry_compatibility_events = _freeze_incompatible_entries(
        entries=decayed_entries,
        state=state,
    )
    entry_map = {entry.entry_id: entry for entry in compatible_entries}
    blocked_updates: list[LexiconBlockedUpdate] = list(entry_compatibility_blocks)
    update_events: list[LexiconUpdateEvent] = list(decay_events) + list(entry_compatibility_events)
    processed_entry_ids: list[str] = []
    ambiguity_reasons: list[str] = [
        "entry_version_mismatch"
        for _ in entry_compatibility_blocks
    ]
    new_entry_count = 0
    updated_entry_count = 0

    for proposal in proposals:
        normalized_surface = _normalize(proposal.surface_form)
        if not normalized_surface or not proposal.sense_hypotheses:
            blocked = LexiconBlockedUpdate(
                surface_form=proposal.surface_form,
                reason="proposal missing normalized surface or sense hypotheses",
                frozen=False,
                provenance=proposal.evidence_ref or "lexicon.update_validation",
            )
            blocked_updates.append(blocked)
            ambiguity_reasons.append("proposal_missing_sense_hypotheses")
            update_events.append(
                LexiconUpdateEvent(
                    event_id=f"lexev-{uuid4().hex[:10]}",
                    entry_id=None,
                    update_kind=LexiconUpdateKind.NO_CLAIM,
                    reason_tags=("proposal_missing_sense_hypotheses",),
                    provenance=blocked.provenance,
                )
            )
            continue

        matching_entries = _find_matching_entries(
            state=tuple(entry_map.values()),
            proposal=proposal,
            expected_schema_version=context.expected_schema_version,
            expected_lexicon_version=context.expected_lexicon_version,
            expected_taxonomy_version=context.expected_taxonomy_version,
        )
        if matching_entries:
            ambiguous_targets = _ambiguous_update_targets(
                matches=matching_entries,
                proposal=proposal,
                score_margin=context.ambiguous_target_score_margin,
            )
            if ambiguous_targets and context.freeze_on_ambiguous_target:
                if context.allow_competing_entry_on_ambiguous_target:
                    created_entry, event = _create_entry(proposal=proposal, context=context)
                    entry_map[created_entry.entry_id] = created_entry
                    update_events.append(
                        replace(
                            event,
                            reason_tags=event.reason_tags + ("ambiguous_update_target_split",),
                        )
                    )
                    processed_entry_ids.append(created_entry.entry_id)
                    new_entry_count += 1
                    ambiguity_reasons.append("ambiguous_update_target_split")
                    continue
                blocked = LexiconBlockedUpdate(
                    surface_form=proposal.surface_form,
                    reason="ambiguous update target blocked to prevent forced winner collapse",
                    frozen=True,
                    provenance=proposal.evidence_ref or "lexicon.ambiguous_target_guard",
                )
                blocked_updates.append(blocked)
                ambiguity_reasons.append("ambiguous_update_target")
                update_events.append(
                    LexiconUpdateEvent(
                        event_id=f"lexev-{uuid4().hex[:10]}",
                        entry_id=None,
                        update_kind=LexiconUpdateKind.FREEZE_UPDATE,
                        reason_tags=("ambiguous_update_target",),
                        provenance=blocked.provenance,
                    )
                )
                continue
            target_entry = _select_update_target(matching_entries, proposal=proposal)
            updated_entry, event, block = _update_entry(
                existing=target_entry,
                proposal=proposal,
                context=context,
            )
            entry_map[updated_entry.entry_id] = updated_entry
            update_events.append(event)
            processed_entry_ids.append(updated_entry.entry_id)
            updated_entry_count += 1
            if block is not None:
                blocked_updates.append(block)
                ambiguity_reasons.append(block.reason)
        else:
            created_entry, event = _create_entry(proposal=proposal, context=context)
            entry_map[created_entry.entry_id] = created_entry
            update_events.append(event)
            processed_entry_ids.append(created_entry.entry_id)
            new_entry_count += 1

    unknown_items = list(state.unknown_items)
    for observation in unknowns:
        unknown_items.append(
            UnknownLexicalItem(
                unknown_id=f"unknown-{uuid4().hex[:10]}",
                surface_form=observation.surface_form,
                occurrence_ref=observation.occurrence_ref,
                partial_pos_hint=observation.partial_pos_hint,
                no_strong_meaning_claim=True,
                candidate_similarity_hints=observation.candidate_similarity_hints,
                confidence=_clamp(observation.confidence),
                provenance=observation.provenance or "lexicon.unknown_observation",
            )
        )
        update_events.append(
            LexiconUpdateEvent(
                event_id=f"lexev-{uuid4().hex[:10]}",
                entry_id=None,
                update_kind=LexiconUpdateKind.REGISTER_UNKNOWN,
                reason_tags=("unknown_lexical_item",),
                provenance=observation.provenance or "lexicon.unknown_observation",
            )
        )
        ambiguity_reasons.append("unknown_lexical_item")

    frozen_updates = tuple(block for block in blocked_updates if block.frozen)
    sorted_entries = tuple(sorted(entry_map.values(), key=lambda entry: entry.entry_id))
    conflict_index = tuple(
        sorted(
            entry.entry_id
            for entry in sorted_entries
            if entry.conflict_state != LexicalConflictState.NONE
        )
    )
    next_state = LexiconState(
        entries=sorted_entries,
        unknown_items=tuple(unknown_items),
        usage_episodes=state.usage_episodes,
        provisional_hypotheses=state.provisional_hypotheses,
        unresolved_updates=tuple(blocked_updates),
        conflict_index=conflict_index,
        frozen_updates=frozen_updates,
        schema_version=state.schema_version,
        lexicon_version=state.lexicon_version,
        taxonomy_version=state.taxonomy_version,
        last_updated_step=state.last_updated_step + context.step_delta,
    )
    gate = evaluate_lexicon_downstream_gate(next_state)
    compatibility_markers = tuple(
        dict.fromkeys(
            block.compatibility_marker
            for block in entry_compatibility_blocks
            if block.compatibility_marker
        )
    )
    telemetry = build_lexical_telemetry(
        state=next_state,
        source_lineage=context.source_lineage,
        processed_entry_ids=tuple(dict.fromkeys(processed_entry_ids)),
        new_entry_count=new_entry_count,
        updated_entry_count=updated_entry_count,
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        queried_forms=(),
        matched_entry_ids=(),
        no_match_count=0,
        compatibility_markers=compatibility_markers,
        attempted_paths=ATTEMPTED_LEXICON_UPDATE_PATHS,
        downstream_gate=gate,
        causal_basis="typed lexical entry updates with conflict/provisional/unknown discipline",
    )
    abstain = bool(not (new_entry_count or updated_entry_count or unknowns) and blocked_updates)
    abstain_reason = "all lexicon updates blocked" if abstain else None

    return LexiconUpdateResult(
        updated_state=next_state,
        update_events=tuple(update_events),
        blocked_updates=tuple(blocked_updates),
        downstream_gate=gate,
        telemetry=telemetry,
        no_final_meaning_resolution_performed=True,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def record_lexical_usage_episode(
    *,
    lexicon_state: LexiconState,
    episodes: LexicalUsageEpisode | tuple[LexicalUsageEpisode, ...] | list[LexicalUsageEpisode],
    context: LexicalEpisodeRecordContext | None = None,
) -> LexicalEpisodeRecordResult:
    if not isinstance(lexicon_state, LexiconState):
        raise TypeError("lexicon_state must be LexiconState")
    if context is None:
        context = LexicalEpisodeRecordContext()
    if not isinstance(context, LexicalEpisodeRecordContext):
        raise TypeError("context must be LexicalEpisodeRecordContext")
    if isinstance(episodes, LexicalUsageEpisode):
        normalized_episodes = (episodes,)
    elif isinstance(episodes, (tuple, list)):
        normalized_episodes = tuple(episodes)
    else:
        raise TypeError("episodes must be LexicalUsageEpisode or tuple/list of LexicalUsageEpisode")
    if not all(isinstance(episode, LexicalUsageEpisode) for episode in normalized_episodes):
        raise TypeError("episodes must contain only LexicalUsageEpisode")

    compatibility_markers = _compatibility_markers(
        state=lexicon_state,
        expected_schema_version=context.expected_schema_version,
        expected_lexicon_version=context.expected_lexicon_version,
        expected_taxonomy_version=context.expected_taxonomy_version,
    )
    if compatibility_markers:
        gate = LexicalLearningGateDecision(
            accepted=False,
            restrictions=("compatibility_mismatch", "no_strong_meaning_claim"),
            reason="lexical episode record blocked due to incompatible schema/version contract",
            accepted_hypothesis_ids=(),
            rejected_hypothesis_ids=(),
            state_ref=f"{lexicon_state.schema_version}|{lexicon_state.lexicon_version}|{lexicon_state.taxonomy_version}",
        )
        telemetry = build_lexical_telemetry(
            state=lexicon_state,
            source_lineage=context.source_lineage,
            processed_entry_ids=(),
            new_entry_count=0,
            updated_entry_count=0,
            ambiguity_reasons=("compatibility_mismatch",),
            queried_forms=(),
            matched_entry_ids=(),
            no_match_count=0,
            compatibility_markers=compatibility_markers,
            attempted_paths=ATTEMPTED_LEXICON_EPISODE_PATHS,
            downstream_gate=gate,
            causal_basis="lexical episode recording blocked due to incompatible schema/version contract",
        )
        return LexicalEpisodeRecordResult(
            updated_state=lexicon_state,
            recorded_episode_ids=(),
            blocked_episode_ids=tuple(episode.episode_id for episode in normalized_episodes),
            updated_hypothesis_ids=(),
            downstream_gate=gate,
            telemetry=telemetry,
            no_final_meaning_resolution_performed=True,
            abstain=True,
            abstain_reason="version compatibility mismatch",
        )

    episodes_out = list(lexicon_state.usage_episodes)
    hypotheses_map = {hypothesis.hypothesis_id: hypothesis for hypothesis in lexicon_state.provisional_hypotheses}
    recorded_episode_ids: list[str] = []
    blocked_episode_ids: list[str] = []
    updated_hypothesis_ids: list[str] = []
    ambiguity_reasons: list[str] = []
    compatibility_markers: list[str] = []
    insufficient_count = 0
    conflicted_count = 0
    frozen_count = 0

    for episode in normalized_episodes:
        episode_compatibility = _episode_compatibility_markers(
            episode=episode,
            expected_schema_version=context.expected_schema_version,
            expected_lexicon_version=context.expected_lexicon_version,
            expected_taxonomy_version=context.expected_taxonomy_version,
        )
        if episode_compatibility:
            compatibility_markers.extend(episode_compatibility)
            blocked_episode_ids.append(episode.episode_id)
            ambiguity_reasons.append("episode_version_mismatch")
            episodes_out.append(
                replace(
                    episode,
                    episode_status=LexicalEpisodeStatus.BLOCKED,
                    blocked_reason=f"compatibility_mismatch:{'|'.join(episode_compatibility)}",
                )
            )
            continue
        normalized_surface = _normalize(episode.observed_surface_form)
        hypothesis_index = _find_learning_hypothesis(
            hypotheses=tuple(hypotheses_map.values()),
            episode=episode,
        )
        if (
            not normalized_surface
            or not episode.proposed_sense_hypotheses
            or episode.confidence < context.min_episode_confidence
            or episode.evidence_quality < context.min_episode_evidence_quality
        ):
            insufficient_count += 1
            blocked_episode_ids.append(episode.episode_id)
            ambiguity_reasons.append("insufficient_episode_evidence")
            episodes_out.append(
                replace(
                    episode,
                    episode_status=LexicalEpisodeStatus.INSUFFICIENT_EVIDENCE,
                    blocked_reason="insufficient_episode_evidence",
                )
            )
            continue

        if hypothesis_index is None:
            new_hypothesis = _create_hypothesis_from_episode(
                episode=episode,
                context=context,
            )
            hypotheses_map[new_hypothesis.hypothesis_id] = new_hypothesis
            updated_hypothesis_ids.append(new_hypothesis.hypothesis_id)
            recorded_episode_ids.append(episode.episode_id)
            episodes_out.append(
                replace(
                    episode,
                    episode_status=LexicalEpisodeStatus.RECORDED,
                    blocked_reason=None,
                )
            )
            continue

        current_hypothesis = hypotheses_map[hypothesis_index]
        hypothesis_compatibility = _hypothesis_compatibility_markers(
            hypothesis=current_hypothesis,
            expected_schema_version=context.expected_schema_version,
            expected_lexicon_version=context.expected_lexicon_version,
            expected_taxonomy_version=context.expected_taxonomy_version,
        )
        if hypothesis_compatibility:
            compatibility_markers.extend(hypothesis_compatibility)
            frozen_count += 1
            ambiguity_reasons.append("hypothesis_version_mismatch")
            blocked_episode_ids.append(episode.episode_id)
            frozen_hypothesis = replace(
                current_hypothesis,
                status=LexicalHypothesisStatus.FROZEN,
                promotion_eligibility=False,
                blocked_reasons=tuple(
                    dict.fromkeys(
                        current_hypothesis.blocked_reasons
                        + tuple(f"compatibility:{marker}" for marker in hypothesis_compatibility)
                    )
                ),
            )
            hypotheses_map[frozen_hypothesis.hypothesis_id] = frozen_hypothesis
            episodes_out.append(
                replace(
                    episode,
                    episode_status=LexicalEpisodeStatus.BLOCKED,
                    blocked_reason=f"hypothesis_compatibility_mismatch:{'|'.join(hypothesis_compatibility)}",
                )
            )
            continue
        if current_hypothesis.status in {
            LexicalHypothesisStatus.FROZEN,
            LexicalHypothesisStatus.CONFLICTED,
            LexicalHypothesisStatus.STABLE_PROMOTED,
        }:
            blocked_episode_ids.append(episode.episode_id)
            ambiguity_reasons.append("hypothesis_not_updatable")
            episodes_out.append(
                replace(
                    episode,
                    episode_status=LexicalEpisodeStatus.BLOCKED,
                    blocked_reason=f"hypothesis_not_updatable:{current_hypothesis.status.value}",
                )
            )
            continue
        hypothesis_next, status_reason = _update_hypothesis_from_episode(
            hypothesis=current_hypothesis,
            episode=episode,
            context=context,
        )
        hypotheses_map[hypothesis_next.hypothesis_id] = hypothesis_next
        updated_hypothesis_ids.append(hypothesis_next.hypothesis_id)
        recorded_episode_ids.append(episode.episode_id)
        if hypothesis_next.status == LexicalHypothesisStatus.CONFLICTED:
            conflicted_count += 1
            ambiguity_reasons.append("episode_conflict_detected")
        if hypothesis_next.status == LexicalHypothesisStatus.FROZEN:
            frozen_count += 1
            ambiguity_reasons.append("episode_conflict_frozen")
        episodes_out.append(
            replace(
                episode,
                episode_status=(
                    LexicalEpisodeStatus.CONFLICTING
                    if status_reason.startswith("conflict")
                    else LexicalEpisodeStatus.RECORDED
                ),
                blocked_reason=status_reason if status_reason.startswith("conflict") else None,
            )
        )

    next_state = LexiconState(
        entries=lexicon_state.entries,
        unknown_items=lexicon_state.unknown_items,
        usage_episodes=tuple(episodes_out),
        provisional_hypotheses=tuple(sorted(hypotheses_map.values(), key=lambda item: item.hypothesis_id)),
        unresolved_updates=lexicon_state.unresolved_updates,
        conflict_index=lexicon_state.conflict_index,
        frozen_updates=lexicon_state.frozen_updates,
        schema_version=lexicon_state.schema_version,
        lexicon_version=lexicon_state.lexicon_version,
        taxonomy_version=lexicon_state.taxonomy_version,
        last_updated_step=lexicon_state.last_updated_step + context.step_delta,
    )
    gate = evaluate_lexical_learning_downstream_gate(next_state)
    telemetry = build_lexical_telemetry(
        state=next_state,
        source_lineage=context.source_lineage,
        processed_entry_ids=(),
        new_entry_count=0,
        updated_entry_count=0,
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        queried_forms=(),
        matched_entry_ids=(),
        no_match_count=0,
        compatibility_markers=tuple(dict.fromkeys(compatibility_markers)),
        attempted_paths=ATTEMPTED_LEXICON_EPISODE_PATHS,
        downstream_gate=gate,
        causal_basis="episode-backed provisional lexical hypothesis update",
        processed_episode_ids=tuple(dict.fromkeys(recorded_episode_ids + blocked_episode_ids)),
        processed_hypothesis_ids=tuple(dict.fromkeys(updated_hypothesis_ids)),
        recorded_episode_count=len(recorded_episode_ids),
        promoted_hypothesis_count=0,
        conflicted_hypothesis_count=conflicted_count,
        frozen_hypothesis_count=frozen_count,
        insufficient_episode_count=insufficient_count,
    )
    abstain = bool(not recorded_episode_ids and blocked_episode_ids)
    abstain_reason = "all lexical usage episodes blocked" if abstain else None
    return LexicalEpisodeRecordResult(
        updated_state=next_state,
        recorded_episode_ids=tuple(dict.fromkeys(recorded_episode_ids)),
        blocked_episode_ids=tuple(dict.fromkeys(blocked_episode_ids)),
        updated_hypothesis_ids=tuple(dict.fromkeys(updated_hypothesis_ids)),
        downstream_gate=gate,
        telemetry=telemetry,
        no_final_meaning_resolution_performed=True,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def consolidate_lexical_hypotheses(
    *,
    lexicon_state: LexiconState,
    context: LexicalHypothesisConsolidationContext | None = None,
) -> LexicalHypothesisUpdateResult:
    if not isinstance(lexicon_state, LexiconState):
        raise TypeError("lexicon_state must be LexiconState")
    if context is None:
        context = LexicalHypothesisConsolidationContext()
    if not isinstance(context, LexicalHypothesisConsolidationContext):
        raise TypeError("context must be LexicalHypothesisConsolidationContext")

    compatibility_markers = _compatibility_markers(
        state=lexicon_state,
        expected_schema_version=context.expected_schema_version,
        expected_lexicon_version=context.expected_lexicon_version,
        expected_taxonomy_version=context.expected_taxonomy_version,
    )
    if compatibility_markers:
        gate = LexicalLearningGateDecision(
            accepted=False,
            restrictions=("compatibility_mismatch", "no_strong_meaning_claim"),
            reason="lexical hypothesis consolidation blocked due to incompatible schema/version contract",
            accepted_hypothesis_ids=(),
            rejected_hypothesis_ids=(),
            state_ref=f"{lexicon_state.schema_version}|{lexicon_state.lexicon_version}|{lexicon_state.taxonomy_version}",
        )
        telemetry = build_lexical_telemetry(
            state=lexicon_state,
            source_lineage=context.source_lineage,
            processed_entry_ids=(),
            new_entry_count=0,
            updated_entry_count=0,
            ambiguity_reasons=("compatibility_mismatch",),
            queried_forms=(),
            matched_entry_ids=(),
            no_match_count=0,
            compatibility_markers=compatibility_markers,
            attempted_paths=ATTEMPTED_LEXICON_HYPOTHESIS_PATHS,
            downstream_gate=gate,
            causal_basis="lexical hypothesis consolidation blocked due to incompatible schema/version contract",
        )
        return LexicalHypothesisUpdateResult(
            updated_state=lexicon_state,
            promoted_hypothesis_ids=(),
            frozen_hypothesis_ids=(),
            conflicted_hypothesis_ids=(),
            downstream_gate=gate,
            telemetry=telemetry,
            no_final_meaning_resolution_performed=True,
            abstain=True,
            abstain_reason="version compatibility mismatch",
        )

    working_state = lexicon_state
    promoted_hypothesis_ids: list[str] = []
    frozen_hypothesis_ids: list[str] = []
    conflicted_hypothesis_ids: list[str] = []
    processed_hypothesis_ids: list[str] = []
    ambiguity_reasons: list[str] = []
    compatibility_markers: list[str] = []
    hypotheses_out: list[ProvisionalLexicalHypothesis] = []
    new_entry_count = 0
    updated_entry_count = 0

    for hypothesis in lexicon_state.provisional_hypotheses:
        processed_hypothesis_ids.append(hypothesis.hypothesis_id)
        hypothesis_compatibility = _hypothesis_compatibility_markers(
            hypothesis=hypothesis,
            expected_schema_version=context.expected_schema_version,
            expected_lexicon_version=context.expected_lexicon_version,
            expected_taxonomy_version=context.expected_taxonomy_version,
        )
        if hypothesis_compatibility:
            frozen_hypothesis_ids.append(hypothesis.hypothesis_id)
            ambiguity_reasons.append("hypothesis_version_mismatch")
            compatibility_markers.extend(hypothesis_compatibility)
            hypotheses_out.append(
                replace(
                    hypothesis,
                    status=LexicalHypothesisStatus.FROZEN,
                    promotion_eligibility=False,
                    blocked_reasons=tuple(
                        dict.fromkeys(
                            hypothesis.blocked_reasons
                            + tuple(f"compatibility:{marker}" for marker in hypothesis_compatibility)
                        )
                    ),
                )
            )
            continue
        if hypothesis.status == LexicalHypothesisStatus.FROZEN:
            frozen_hypothesis_ids.append(hypothesis.hypothesis_id)
            hypotheses_out.append(hypothesis)
            continue
        if hypothesis.status == LexicalHypothesisStatus.CONFLICTED:
            conflicted_hypothesis_ids.append(hypothesis.hypothesis_id)
            hypotheses_out.append(hypothesis)
            continue

        promotion_ready = (
            hypothesis.support_count
            >= _effective_min_support_for_promotion(context.min_support_for_promotion)
            and hypothesis.confidence >= context.promotion_confidence_threshold
            and hypothesis.status == LexicalHypothesisStatus.PROMOTION_ELIGIBLE
        )
        if not promotion_ready:
            hypotheses_out.append(
                replace(
                    hypothesis,
                    status=LexicalHypothesisStatus.PROVISIONAL,
                    promotion_eligibility=False,
                )
            )
            ambiguity_reasons.append("insufficient_hypothesis_support_for_promotion")
            continue

        proposal = _proposal_from_hypothesis(hypothesis)
        update_result = create_or_update_lexicon_state(
            lexicon_state=working_state,
            entry_proposals=(proposal,),
            context=LexiconUpdateContext(
                source_lineage=context.source_lineage,
                expected_schema_version=context.expected_schema_version,
                expected_lexicon_version=context.expected_lexicon_version,
                expected_taxonomy_version=context.expected_taxonomy_version,
                min_evidence_for_stable=1,
                stable_confidence_threshold=0.0,
            ),
        )
        working_state = update_result.updated_state
        event_entry_ids = tuple(event.entry_id for event in update_result.update_events if event.entry_id)
        promoted_entry_id = event_entry_ids[-1] if event_entry_ids else None
        promoted_hypothesis_ids.append(hypothesis.hypothesis_id)
        if update_result.telemetry.new_entry_count:
            new_entry_count += update_result.telemetry.new_entry_count
        if update_result.telemetry.updated_entry_count:
            updated_entry_count += update_result.telemetry.updated_entry_count
        hypotheses_out.append(
            replace(
                hypothesis,
                status=LexicalHypothesisStatus.STABLE_PROMOTED,
                promotion_eligibility=False,
                promoted_entry_id=promoted_entry_id,
            )
        )

    next_state = LexiconState(
        entries=working_state.entries,
        unknown_items=working_state.unknown_items,
        usage_episodes=working_state.usage_episodes,
        provisional_hypotheses=tuple(sorted(hypotheses_out, key=lambda item: item.hypothesis_id)),
        unresolved_updates=working_state.unresolved_updates,
        conflict_index=working_state.conflict_index,
        frozen_updates=working_state.frozen_updates,
        schema_version=working_state.schema_version,
        lexicon_version=working_state.lexicon_version,
        taxonomy_version=working_state.taxonomy_version,
        last_updated_step=working_state.last_updated_step + context.step_delta,
    )
    gate = evaluate_lexical_learning_downstream_gate(next_state)
    telemetry = build_lexical_telemetry(
        state=next_state,
        source_lineage=context.source_lineage,
        processed_entry_ids=(),
        new_entry_count=new_entry_count,
        updated_entry_count=updated_entry_count,
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        queried_forms=(),
        matched_entry_ids=(),
        no_match_count=0,
        compatibility_markers=tuple(dict.fromkeys(compatibility_markers)),
        attempted_paths=ATTEMPTED_LEXICON_HYPOTHESIS_PATHS,
        downstream_gate=gate,
        causal_basis="provisional lexical hypothesis consolidation via evidence threshold",
        processed_episode_ids=(),
        processed_hypothesis_ids=tuple(dict.fromkeys(processed_hypothesis_ids)),
        recorded_episode_count=0,
        promoted_hypothesis_count=len(promoted_hypothesis_ids),
        conflicted_hypothesis_count=len(conflicted_hypothesis_ids),
        frozen_hypothesis_count=len(frozen_hypothesis_ids),
        insufficient_episode_count=0,
    )
    abstain = bool(not promoted_hypothesis_ids and lexicon_state.provisional_hypotheses)
    abstain_reason = "no promotion-eligible lexical hypotheses" if abstain else None
    return LexicalHypothesisUpdateResult(
        updated_state=next_state,
        promoted_hypothesis_ids=tuple(dict.fromkeys(promoted_hypothesis_ids)),
        frozen_hypothesis_ids=tuple(dict.fromkeys(frozen_hypothesis_ids)),
        conflicted_hypothesis_ids=tuple(dict.fromkeys(conflicted_hypothesis_ids)),
        downstream_gate=gate,
        telemetry=telemetry,
        no_final_meaning_resolution_performed=True,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def query_lexical_entries(
    *,
    lexicon_state: LexiconState,
    queries: LexiconQueryRequest | tuple[LexiconQueryRequest, ...] | list[LexiconQueryRequest],
    context: LexiconQueryContext | None = None,
) -> LexiconQueryResult:
    if not isinstance(lexicon_state, LexiconState):
        raise TypeError("lexicon_state must be LexiconState")
    if context is None:
        context = LexiconQueryContext()
    if not isinstance(context, LexiconQueryContext):
        raise TypeError("context must be LexiconQueryContext")
    if isinstance(queries, LexiconQueryRequest):
        normalized_queries = (queries,)
    elif isinstance(queries, (tuple, list)):
        normalized_queries = tuple(queries)
    else:
        raise TypeError("queries must be LexiconQueryRequest or tuple/list of LexiconQueryRequest")
    if not all(isinstance(query, LexiconQueryRequest) for query in normalized_queries):
        raise TypeError("queries must contain only LexiconQueryRequest")

    compatibility_markers = _compatibility_markers(
        state=lexicon_state,
        expected_schema_version=context.expected_schema_version,
        expected_lexicon_version=context.expected_lexicon_version,
        expected_taxonomy_version=context.expected_taxonomy_version,
    )
    if compatibility_markers:
        gate = LexiconGateDecision(
            accepted=False,
            restrictions=("compatibility_mismatch", "no_strong_meaning_claim"),
            reason="lexicon query blocked due to incompatible schema/version contract",
            accepted_entry_ids=(),
            rejected_entry_ids=(),
            state_ref=f"{lexicon_state.schema_version}|{lexicon_state.lexicon_version}|{lexicon_state.taxonomy_version}",
        )
        telemetry = build_lexical_telemetry(
            state=lexicon_state,
            source_lineage=context.source_lineage,
            processed_entry_ids=(),
            new_entry_count=0,
            updated_entry_count=0,
            ambiguity_reasons=("compatibility_mismatch",),
            queried_forms=tuple(query.surface_form for query in normalized_queries),
            matched_entry_ids=(),
            no_match_count=len(normalized_queries),
            compatibility_markers=compatibility_markers,
            attempted_paths=ATTEMPTED_LEXICON_QUERY_PATHS,
            downstream_gate=gate,
            causal_basis="lexicon query blocked due to incompatible schema/version contract",
        )
        return LexiconQueryResult(
            query_records=(),
            state=lexicon_state,
            downstream_gate=gate,
            telemetry=telemetry,
            no_final_meaning_resolution_performed=True,
            abstain=True,
            abstain_reason="version compatibility mismatch",
        )

    records: list[LexiconQueryRecord] = []
    ambiguity_reasons: list[str] = []
    queried_forms: list[str] = []
    matched_entry_ids_all: list[str] = []
    no_match_count = 0

    for query in normalized_queries:
        queried_forms.append(query.surface_form)
        normalized_form = _normalize(query.surface_form)
        matches = _query_matches(lexicon_state, query=query, normalized_form=normalized_form)
        unknown_ids: tuple[str, ...]
        if query.include_unknown_items:
            unknown_ids = tuple(
                item.unknown_id
                for item in lexicon_state.unknown_items
                if _normalize(item.surface_form) == normalized_form
            )
        else:
            unknown_ids = ()

        matched_entry_ids = tuple(entry.entry_id for entry in matches)
        matched_sense_ids = tuple(
            dict.fromkeys(
                sense.sense_id
                for entry in matches
                for sense in entry.sense_records
            )
        )
        context_blocked_entry_ids: list[str] = []
        reference_context_blocked = False
        operator_scope_blocked = False
        for entry in matches:
            if entry.reference_profile.requires_context and not context.context_keys:
                context_blocked_entry_ids.append(entry.entry_id)
                reference_context_blocked = True
                continue
            if (
                entry.composition_profile.behaves_as_operator
                and entry.composition_profile.scope_sensitive
                and entry.composition_profile.remains_underspecified
                and "scope_anchor" not in context.context_keys
            ):
                context_blocked_entry_ids.append(entry.entry_id)
                operator_scope_blocked = True
        context_blocked_entry_ids_tuple = tuple(dict.fromkeys(context_blocked_entry_ids))
        local_ambiguity: list[str] = []
        if len(matches) > 1:
            local_ambiguity.append("multiple_entries_for_surface_form")
        if any(len(entry.sense_records) > 1 for entry in matches):
            local_ambiguity.append("multiple_senses_for_surface_form")
        if any(
            entry.acquisition_state.status != LexicalAcquisitionStatus.STABLE for entry in matches
        ):
            local_ambiguity.append("non_stable_entries_present")
        if not matches and unknown_ids:
            local_ambiguity.append("unknown_lexical_item")
        if not matches and not unknown_ids:
            local_ambiguity.append("no_match")
            no_match_count += 1
        if reference_context_blocked:
            local_ambiguity.append("context_required_for_reference_profile")
        if operator_scope_blocked:
            local_ambiguity.append("operator_scope_context_required")
        if any(_entry_compatibility_markers(entry=entry, state=lexicon_state) for entry in matches):
            local_ambiguity.append("entry_version_mismatch")
        learning_hypotheses = tuple(
            hypothesis
            for hypothesis in lexicon_state.provisional_hypotheses
            if _normalize(hypothesis.target_surface_form) == normalized_form
        )
        if learning_hypotheses:
            local_ambiguity.append("learning_hypotheses_present")
        if any(
            hypothesis.status == LexicalHypothesisStatus.PROVISIONAL
            for hypothesis in learning_hypotheses
        ):
            local_ambiguity.append("learning_hypothesis_provisional")
        if any(
            hypothesis.status == LexicalHypothesisStatus.CONFLICTED
            for hypothesis in learning_hypotheses
        ):
            local_ambiguity.append("learning_hypothesis_conflicted")
        if any(
            hypothesis.status == LexicalHypothesisStatus.FROZEN
            for hypothesis in learning_hypotheses
        ):
            local_ambiguity.append("learning_hypothesis_frozen")
        if any(
            hypothesis.status == LexicalHypothesisStatus.PROMOTION_ELIGIBLE
            for hypothesis in learning_hypotheses
        ):
            local_ambiguity.append("learning_hypothesis_promotion_eligible")

        ambiguity_reasons.extend(local_ambiguity)
        matched_entry_ids_all.extend(matched_entry_ids)
        records.append(
            LexiconQueryRecord(
                query_form=query.surface_form,
                matched_entry_ids=matched_entry_ids,
                matched_sense_ids=matched_sense_ids,
                unknown_item_ids=unknown_ids,
                context_blocked_entry_ids=context_blocked_entry_ids_tuple,
                ambiguity_reasons=tuple(dict.fromkeys(local_ambiguity)),
                no_final_meaning_resolution_performed=True,
            )
        )

    gate = _query_gate_from_records(
        records=tuple(records),
        state=lexicon_state,
    )
    query_compatibility_markers = (
        ("entry_version_mismatch",)
        if any("entry_version_mismatch" in record.ambiguity_reasons for record in records)
        else ()
    )
    telemetry = build_lexical_telemetry(
        state=lexicon_state,
        source_lineage=context.source_lineage,
        processed_entry_ids=(),
        new_entry_count=0,
        updated_entry_count=0,
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        queried_forms=tuple(queried_forms),
        matched_entry_ids=tuple(dict.fromkeys(matched_entry_ids_all)),
        no_match_count=no_match_count,
        compatibility_markers=query_compatibility_markers,
        attempted_paths=ATTEMPTED_LEXICON_QUERY_PATHS,
        downstream_gate=gate,
        causal_basis="typed lexical query over ambiguity-preserving lexicon substrate",
    )
    abstain = not bool(records)
    abstain_reason = "no valid lexical queries provided" if abstain else None
    return LexiconQueryResult(
        query_records=tuple(records),
        state=lexicon_state,
        downstream_gate=gate,
        telemetry=telemetry,
        no_final_meaning_resolution_performed=True,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def lexicon_result_to_payload(
    result: LexiconUpdateResult | LexiconQueryResult | LexicalEpisodeRecordResult | LexicalHypothesisUpdateResult,
) -> dict[str, object]:
    return lexicon_result_snapshot(result)


def reconstruct_lexicon_state_from_snapshot(snapshot: dict[str, object]) -> LexiconState:
    if not isinstance(snapshot, dict):
        raise TypeError("snapshot must be dict payload produced by lexicon_result_to_payload")
    state_payload = snapshot.get("state", snapshot)
    if not isinstance(state_payload, dict):
        raise TypeError("snapshot must contain dict 'state' payload")

    entries_payload = state_payload.get("entries", ())
    unknown_payload = state_payload.get("unknown_items", ())
    usage_episode_payload = state_payload.get("usage_episodes", ())
    provisional_hypothesis_payload = state_payload.get("provisional_hypotheses", ())
    unresolved_payload = state_payload.get("unresolved_updates", ())
    frozen_payload = state_payload.get("frozen_updates", ())
    conflict_index_payload = state_payload.get("conflict_index", ())

    if not isinstance(entries_payload, (tuple, list)):
        raise TypeError("state.entries must be tuple/list")
    if not isinstance(unknown_payload, (tuple, list)):
        raise TypeError("state.unknown_items must be tuple/list")
    if not isinstance(usage_episode_payload, (tuple, list)):
        raise TypeError("state.usage_episodes must be tuple/list")
    if not isinstance(provisional_hypothesis_payload, (tuple, list)):
        raise TypeError("state.provisional_hypotheses must be tuple/list")
    if not isinstance(unresolved_payload, (tuple, list)):
        raise TypeError("state.unresolved_updates must be tuple/list")
    if not isinstance(frozen_payload, (tuple, list)):
        raise TypeError("state.frozen_updates must be tuple/list")
    if not isinstance(conflict_index_payload, (tuple, list)):
        raise TypeError("state.conflict_index must be tuple/list")

    entries: list[LexicalEntry] = []
    for raw_entry in entries_payload:
        if not isinstance(raw_entry, dict):
            raise TypeError("state.entries must contain dict entry payloads")
        raw_variants = raw_entry.get("surface_variants", ())
        raw_senses = raw_entry.get("sense_records", ())
        if not isinstance(raw_variants, (tuple, list)):
            raise TypeError("entry.surface_variants must be tuple/list")
        if not isinstance(raw_senses, (tuple, list)):
            raise TypeError("entry.sense_records must be tuple/list")

        composition = raw_entry.get("composition_profile") or {}
        reference = raw_entry.get("reference_profile") or {}
        acquisition = raw_entry.get("acquisition_state") or {}
        if not isinstance(composition, dict):
            raise TypeError("entry.composition_profile must be dict")
        if not isinstance(reference, dict):
            raise TypeError("entry.reference_profile must be dict")
        if not isinstance(acquisition, dict):
            raise TypeError("entry.acquisition_state must be dict")

        role_hints_raw = composition.get("role_hints", ())
        if not isinstance(role_hints_raw, (tuple, list)):
            raise TypeError("entry.composition_profile.role_hints must be tuple/list")

        entries.append(
            LexicalEntry(
                entry_id=str(raw_entry["entry_id"]),
                canonical_form=str(raw_entry["canonical_form"]),
                surface_variants=tuple(
                    SurfaceFormRecord(
                        form=str(variant["form"]),
                        normalized_form=str(variant["normalized_form"]),
                        locale_hint=variant.get("locale_hint"),
                        variant_kind=str(variant["variant_kind"]),
                        confidence=_clamp(float(variant["confidence"])),
                        provenance=str(variant["provenance"]),
                    )
                    for variant in raw_variants
                ),
                language_code=str(raw_entry["language_code"]),
                part_of_speech_candidates=tuple(raw_entry.get("part_of_speech_candidates", ())),
                sense_records=tuple(
                    LexicalSenseRecord(
                        sense_id=str(sense["sense_id"]),
                        sense_family=str(sense["sense_family"]),
                        sense_label=str(sense["sense_label"]),
                        coarse_semantic_type=LexicalCoarseSemanticType(str(sense["coarse_semantic_type"])),
                        compatibility_cues=tuple(sense.get("compatibility_cues", ())),
                        anti_cues=tuple(sense.get("anti_cues", ())),
                        confidence=_clamp(float(sense["confidence"])),
                        provisional=bool(sense["provisional"]),
                        provenance=str(sense["provenance"]),
                        status=LexicalSenseStatus(str(sense.get("status", "provisional"))),
                        evidence_count=int(sense.get("evidence_count", 1)),
                        conflict_markers=tuple(sense.get("conflict_markers", ())),
                        example_ids=tuple(sense.get("example_ids", ())),
                    )
                    for sense in raw_senses
                ),
                examples=tuple(
                    LexicalExampleRecord(
                        example_id=str(example["example_id"]),
                        example_text=str(example["example_text"]),
                        linked_entry_id=str(example["linked_entry_id"]),
                        linked_sense_id=(
                            str(example["linked_sense_id"])
                            if example.get("linked_sense_id") is not None
                            else None
                        ),
                        status=LexicalExampleStatus(str(example.get("status", "illustrative"))),
                        illustrative_only=bool(example.get("illustrative_only", True)),
                        provenance=str(example.get("provenance", "lexicon.reconstruct")),
                    )
                    for example in raw_entry.get("examples", ())
                ),
                entry_status=LexicalAcquisitionStatus(
                    str(raw_entry.get("entry_status", acquisition.get("status", "unknown")))
                ),
                acquisition_mode=LexicalAcquisitionMode(
                    str(raw_entry.get("acquisition_mode", "unknown"))
                ),
                composition_profile=LexicalCompositionProfile(
                    role_hints=tuple(
                        LexicalCompositionRole(str(role))
                        for role in role_hints_raw
                    )
                    or (LexicalCompositionRole.UNKNOWN,),
                    argument_structure_hints=tuple(composition.get("argument_structure_hints", ())),
                    can_introduce_predicate_frame=bool(
                        composition.get("can_introduce_predicate_frame", False)
                    ),
                    behaves_as_modifier=bool(composition.get("behaves_as_modifier", False)),
                    behaves_as_operator=bool(composition.get("behaves_as_operator", False)),
                    behaves_as_participant=bool(composition.get("behaves_as_participant", False)),
                    behaves_as_referential_carrier=bool(
                        composition.get("behaves_as_referential_carrier", False)
                    ),
                    scope_sensitive=bool(composition.get("scope_sensitive", False)),
                    negation_sensitive=bool(composition.get("negation_sensitive", False)),
                    remains_underspecified=bool(composition.get("remains_underspecified", True)),
                ),
                reference_profile=LexicalReferenceProfile(
                    pronoun_like=bool(reference.get("pronoun_like", False)),
                    deictic=bool(reference.get("deictic", False)),
                    entity_introducing=bool(reference.get("entity_introducing", False)),
                    anaphora_prone=bool(reference.get("anaphora_prone", False)),
                    quote_sensitive=bool(reference.get("quote_sensitive", False)),
                    requires_context=bool(reference.get("requires_context", False)),
                    can_remain_unresolved=bool(reference.get("can_remain_unresolved", True)),
                ),
                acquisition_state=LexicalAcquisitionState(
                    status=LexicalAcquisitionStatus(str(acquisition.get("status", "unknown"))),
                    evidence_count=int(acquisition.get("evidence_count", 0)),
                    last_supporting_evidence_ref=acquisition.get("last_supporting_evidence_ref"),
                    revision_count=int(acquisition.get("revision_count", 0)),
                    frozen_update=bool(acquisition.get("frozen_update", False)),
                    staleness_steps=int(acquisition.get("staleness_steps", 0)),
                    decay_marker=_clamp(float(acquisition.get("decay_marker", 0.0))),
                    blocked_reason=acquisition.get("blocked_reason"),
                ),
                confidence=_clamp(float(raw_entry.get("confidence", 0.0))),
                conflict_state=LexicalConflictState(str(raw_entry.get("conflict_state", "none"))),
                provenance=str(raw_entry.get("provenance", "lexicon.reconstruct")),
                lemma=(
                    str(raw_entry["lemma"])
                    if raw_entry.get("lemma") is not None
                    else None
                ),
                aliases=tuple(raw_entry.get("aliases", ())),
                schema_version=str(raw_entry.get("schema_version", state_payload.get("schema_version", DEFAULT_LEXICON_SCHEMA_VERSION))),
                lexicon_version=str(raw_entry.get("lexicon_version", state_payload.get("lexicon_version", DEFAULT_LEXICON_VERSION))),
                taxonomy_version=str(raw_entry.get("taxonomy_version", state_payload.get("taxonomy_version", DEFAULT_LEXICON_TAXONOMY_VERSION))),
            )
        )

    unknown_items = tuple(
        UnknownLexicalItem(
            unknown_id=str(item["unknown_id"]),
            surface_form=str(item["surface_form"]),
            occurrence_ref=str(item["occurrence_ref"]),
            partial_pos_hint=item.get("partial_pos_hint"),
            no_strong_meaning_claim=bool(item.get("no_strong_meaning_claim", True)),
            candidate_similarity_hints=tuple(item.get("candidate_similarity_hints", ())),
            confidence=_clamp(float(item.get("confidence", 0.0))),
            provenance=str(item.get("provenance", "lexicon.reconstruct")),
        )
        for item in unknown_payload
    )
    usage_episodes = tuple(
        LexicalUsageEpisode(
            episode_id=str(episode["episode_id"]),
            observed_surface_form=str(episode["observed_surface_form"]),
            observed_lemma_hint=episode.get("observed_lemma_hint"),
            language_code=str(episode["language_code"]),
            observed_context_keys=tuple(episode.get("observed_context_keys", ())),
            source_kind=str(episode.get("source_kind", "unknown")),
            proposed_sense_hypotheses=tuple(
                LexicalSenseHypothesis(
                    sense_family=str(sense["sense_family"]),
                    sense_label=str(sense["sense_label"]),
                    coarse_semantic_type=LexicalCoarseSemanticType(str(sense["coarse_semantic_type"])),
                    compatibility_cues=tuple(sense.get("compatibility_cues", ())),
                    anti_cues=tuple(sense.get("anti_cues", ())),
                    confidence=_clamp(float(sense.get("confidence", 0.5))),
                    provisional=bool(sense.get("provisional", True)),
                    status_hint=(
                        LexicalSenseStatus(str(sense["status_hint"]))
                        if sense.get("status_hint") is not None
                        else None
                    ),
                    example_texts=tuple(sense.get("example_texts", ())),
                )
                for sense in episode.get("proposed_sense_hypotheses", ())
            ),
            proposed_role_hints=tuple(
                LexicalCompositionRole(str(role))
                for role in episode.get("proposed_role_hints", ())
            ),
            usage_span=episode.get("usage_span"),
            confidence=_clamp(float(episode.get("confidence", 0.0))),
            evidence_quality=_clamp(float(episode.get("evidence_quality", 0.0))),
            step_index=int(episode.get("step_index", 0)),
            episode_status=LexicalEpisodeStatus(str(episode.get("episode_status", "recorded"))),
            provenance=str(episode.get("provenance", "lexicon.reconstruct")),
            schema_version=str(episode.get("schema_version", state_payload.get("schema_version", DEFAULT_LEXICON_SCHEMA_VERSION))),
            lexicon_version=str(episode.get("lexicon_version", state_payload.get("lexicon_version", DEFAULT_LEXICON_VERSION))),
            taxonomy_version=str(episode.get("taxonomy_version", state_payload.get("taxonomy_version", DEFAULT_LEXICON_TAXONOMY_VERSION))),
            blocked_reason=episode.get("blocked_reason"),
        )
        for episode in usage_episode_payload
    )
    provisional_hypotheses = tuple(
        ProvisionalLexicalHypothesis(
            hypothesis_id=str(hypothesis["hypothesis_id"]),
            target_surface_form=str(hypothesis["target_surface_form"]),
            target_lemma=hypothesis.get("target_lemma"),
            language_code=str(hypothesis.get("language_code", "")),
            candidate_entry_id=hypothesis.get("candidate_entry_id"),
            candidate_sense_bundle=tuple(
                LexicalSenseHypothesis(
                    sense_family=str(sense["sense_family"]),
                    sense_label=str(sense["sense_label"]),
                    coarse_semantic_type=LexicalCoarseSemanticType(str(sense["coarse_semantic_type"])),
                    compatibility_cues=tuple(sense.get("compatibility_cues", ())),
                    anti_cues=tuple(sense.get("anti_cues", ())),
                    confidence=_clamp(float(sense.get("confidence", 0.5))),
                    provisional=bool(sense.get("provisional", True)),
                    status_hint=(
                        LexicalSenseStatus(str(sense["status_hint"]))
                        if sense.get("status_hint") is not None
                        else None
                    ),
                    example_texts=tuple(sense.get("example_texts", ())),
                )
                for sense in hypothesis.get("candidate_sense_bundle", ())
            ),
            candidate_role_hints=tuple(
                LexicalCompositionRole(str(role))
                for role in hypothesis.get("candidate_role_hints", ())
            )
            or (LexicalCompositionRole.UNKNOWN,),
            supporting_episode_ids=tuple(hypothesis.get("supporting_episode_ids", ())),
            conflicting_episode_ids=tuple(hypothesis.get("conflicting_episode_ids", ())),
            support_count=int(hypothesis.get("support_count", 0)),
            conflict_count=int(hypothesis.get("conflict_count", 0)),
            status=LexicalHypothesisStatus(str(hypothesis.get("status", "unknown"))),
            promotion_eligibility=bool(hypothesis.get("promotion_eligibility", False)),
            blocked_reasons=tuple(hypothesis.get("blocked_reasons", ())),
            confidence=_clamp(float(hypothesis.get("confidence", 0.0))),
            evidence_quality=_clamp(float(hypothesis.get("evidence_quality", 0.0))),
            provenance=str(hypothesis.get("provenance", "lexicon.reconstruct")),
            promoted_entry_id=hypothesis.get("promoted_entry_id"),
            schema_version=str(
                hypothesis.get(
                    "schema_version",
                    state_payload.get("schema_version", DEFAULT_LEXICON_SCHEMA_VERSION),
                )
            ),
            lexicon_version=str(
                hypothesis.get(
                    "lexicon_version",
                    state_payload.get("lexicon_version", DEFAULT_LEXICON_VERSION),
                )
            ),
            taxonomy_version=str(
                hypothesis.get(
                    "taxonomy_version",
                    state_payload.get("taxonomy_version", DEFAULT_LEXICON_TAXONOMY_VERSION),
                )
            ),
        )
        for hypothesis in provisional_hypothesis_payload
    )
    unresolved_updates = tuple(
        LexiconBlockedUpdate(
            surface_form=str(blocked.get("surface_form", "")),
            reason=str(blocked.get("reason", "blocked")),
            frozen=bool(blocked.get("frozen", False)),
            provenance=str(blocked.get("provenance", "lexicon.reconstruct")),
            compatibility_marker=blocked.get("compatibility_marker"),
        )
        for blocked in unresolved_payload
    )
    frozen_updates = tuple(
        LexiconBlockedUpdate(
            surface_form=str(blocked.get("surface_form", "")),
            reason=str(blocked.get("reason", "blocked")),
            frozen=bool(blocked.get("frozen", True)),
            provenance=str(blocked.get("provenance", "lexicon.reconstruct")),
            compatibility_marker=blocked.get("compatibility_marker"),
        )
        for blocked in frozen_payload
    )
    return LexiconState(
        entries=tuple(entries),
        unknown_items=unknown_items,
        usage_episodes=usage_episodes,
        provisional_hypotheses=provisional_hypotheses,
        unresolved_updates=unresolved_updates,
        conflict_index=tuple(str(entry_id) for entry_id in conflict_index_payload),
        frozen_updates=frozen_updates,
        schema_version=str(state_payload.get("schema_version", DEFAULT_LEXICON_SCHEMA_VERSION)),
        lexicon_version=str(state_payload.get("lexicon_version", DEFAULT_LEXICON_VERSION)),
        taxonomy_version=str(state_payload.get("taxonomy_version", DEFAULT_LEXICON_TAXONOMY_VERSION)),
        last_updated_step=int(state_payload.get("last_updated_step", 0)),
    )


def persist_lexicon_result_via_f01(
    *,
    result: LexiconUpdateResult | LexiconQueryResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("lexicon-substrate",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"lexicon-step-{transition_id}",
            "lexicon_snapshot": lexicon_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def persist_lexical_learning_result_via_f01(
    *,
    result: LexicalEpisodeRecordResult | LexicalHypothesisUpdateResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("lexicon-learning",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"lexicon-learning-step-{transition_id}",
            "lexicon_learning_snapshot": lexicon_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _normalize(value: str) -> str:
    return value.strip().lower()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _find_learning_hypothesis(
    *,
    hypotheses: tuple[ProvisionalLexicalHypothesis, ...],
    episode: LexicalUsageEpisode,
) -> str | None:
    normalized_surface = _normalize(episode.observed_surface_form)
    normalized_lemma = _normalize(episode.observed_lemma_hint or episode.observed_surface_form)
    for hypothesis in hypotheses:
        if hypothesis.language_code != episode.language_code:
            continue
        if _normalize(hypothesis.target_surface_form) == normalized_surface:
            return hypothesis.hypothesis_id
        if hypothesis.target_lemma and _normalize(hypothesis.target_lemma) == normalized_lemma:
            return hypothesis.hypothesis_id
    return None


def _merge_hypothesis_sense_bundle(
    *,
    existing: tuple[LexicalSenseHypothesis, ...],
    incoming: tuple[LexicalSenseHypothesis, ...],
) -> tuple[LexicalSenseHypothesis, ...]:
    merged: dict[tuple[str, str], LexicalSenseHypothesis] = {
        (sense.sense_family, sense.sense_label): sense
        for sense in existing
    }
    for sense in incoming:
        key = (sense.sense_family, sense.sense_label)
        if key not in merged:
            merged[key] = sense
            continue
        current = merged[key]
        merged[key] = LexicalSenseHypothesis(
            sense_family=current.sense_family,
            sense_label=current.sense_label,
            coarse_semantic_type=current.coarse_semantic_type,
            compatibility_cues=tuple(dict.fromkeys(current.compatibility_cues + sense.compatibility_cues)),
            anti_cues=tuple(dict.fromkeys(current.anti_cues + sense.anti_cues)),
            confidence=_clamp((current.confidence * 0.6) + (sense.confidence * 0.4)),
            provisional=current.provisional and sense.provisional,
            status_hint=current.status_hint or sense.status_hint,
            example_texts=tuple(dict.fromkeys(current.example_texts + sense.example_texts)),
        )
    return tuple(merged.values())


def _episode_conflicts_with_hypothesis(
    *,
    hypothesis: ProvisionalLexicalHypothesis,
    episode: LexicalUsageEpisode,
) -> bool:
    existing_labels = {(sense.sense_family, sense.sense_label) for sense in hypothesis.candidate_sense_bundle}
    incoming_labels = {(sense.sense_family, sense.sense_label) for sense in episode.proposed_sense_hypotheses}
    label_disjoint = bool(existing_labels and incoming_labels and existing_labels.isdisjoint(incoming_labels))
    if label_disjoint:
        return True
    existing_roles = {
        role for role in hypothesis.candidate_role_hints if role != LexicalCompositionRole.UNKNOWN
    }
    incoming_roles = {
        role for role in episode.proposed_role_hints if role != LexicalCompositionRole.UNKNOWN
    }
    if existing_roles and incoming_roles and existing_roles.isdisjoint(incoming_roles):
        return True
    existing_coarse = {
        (sense.sense_family, sense.sense_label): sense.coarse_semantic_type
        for sense in hypothesis.candidate_sense_bundle
    }
    incoming_coarse = {
        (sense.sense_family, sense.sense_label): sense.coarse_semantic_type
        for sense in episode.proposed_sense_hypotheses
    }
    if any(
        key in incoming_coarse and incoming_coarse[key] != existing_coarse[key]
        for key in existing_coarse
    ):
        return True
    for existing in hypothesis.candidate_sense_bundle:
        for incoming in episode.proposed_sense_hypotheses:
            if set(existing.compatibility_cues).intersection(set(incoming.anti_cues)):
                return True
            if set(existing.anti_cues).intersection(set(incoming.compatibility_cues)):
                return True
    return False


def _create_hypothesis_from_episode(
    *,
    episode: LexicalUsageEpisode,
    context: LexicalEpisodeRecordContext,
) -> ProvisionalLexicalHypothesis:
    confidence = _clamp((episode.confidence * 0.6) + (episode.evidence_quality * 0.4))
    min_support_for_promotion = _effective_min_support_for_promotion(
        context.min_support_for_promotion
    )
    promotion_eligibility = (
        1 >= min_support_for_promotion
        and confidence >= context.promotion_confidence_threshold
    )
    status = (
        LexicalHypothesisStatus.PROMOTION_ELIGIBLE
        if promotion_eligibility
        else LexicalHypothesisStatus.PROVISIONAL
    )
    return ProvisionalLexicalHypothesis(
        hypothesis_id=f"lexhyp-{uuid4().hex[:10]}",
        target_surface_form=episode.observed_surface_form,
        target_lemma=episode.observed_lemma_hint,
        language_code=episode.language_code,
        candidate_entry_id=None,
        candidate_sense_bundle=episode.proposed_sense_hypotheses,
        candidate_role_hints=episode.proposed_role_hints,
        supporting_episode_ids=(episode.episode_id,),
        conflicting_episode_ids=(),
        support_count=1,
        conflict_count=0,
        status=status,
        promotion_eligibility=promotion_eligibility,
        blocked_reasons=(),
        confidence=confidence,
        evidence_quality=_clamp(episode.evidence_quality),
        provenance=episode.provenance,
        schema_version=episode.schema_version,
        lexicon_version=episode.lexicon_version,
        taxonomy_version=episode.taxonomy_version,
    )


def _update_hypothesis_from_episode(
    *,
    hypothesis: ProvisionalLexicalHypothesis,
    episode: LexicalUsageEpisode,
    context: LexicalEpisodeRecordContext,
) -> tuple[ProvisionalLexicalHypothesis, str]:
    is_conflict = _episode_conflicts_with_hypothesis(hypothesis=hypothesis, episode=episode)
    merged_senses = _merge_hypothesis_sense_bundle(
        existing=hypothesis.candidate_sense_bundle,
        incoming=episode.proposed_sense_hypotheses,
    )
    support_count = hypothesis.support_count + (0 if is_conflict else 1)
    conflict_count = hypothesis.conflict_count + (1 if is_conflict else 0)
    confidence = _clamp((hypothesis.confidence * 0.65) + (episode.confidence * 0.35))
    evidence_quality = _clamp((hypothesis.evidence_quality * 0.65) + (episode.evidence_quality * 0.35))

    status = hypothesis.status
    promotion_eligibility = False
    blocked_reasons = list(hypothesis.blocked_reasons)
    status_reason = "support"
    if is_conflict:
        status = LexicalHypothesisStatus.FROZEN if context.freeze_on_conflict else LexicalHypothesisStatus.CONFLICTED
        promotion_eligibility = False
        blocked_reasons.append("conflicting_episode")
        status_reason = "conflict_frozen" if context.freeze_on_conflict else "conflict"
    elif (
        support_count >= _effective_min_support_for_promotion(context.min_support_for_promotion)
        and confidence >= context.promotion_confidence_threshold
    ):
        status = LexicalHypothesisStatus.PROMOTION_ELIGIBLE
        promotion_eligibility = True
        status_reason = "promotion_eligible"
    else:
        status = LexicalHypothesisStatus.PROVISIONAL
        promotion_eligibility = False
        status_reason = "support"

    return (
        replace(
            hypothesis,
            candidate_sense_bundle=merged_senses,
            candidate_role_hints=tuple(
                dict.fromkeys(hypothesis.candidate_role_hints + episode.proposed_role_hints)
            ),
            supporting_episode_ids=(
                hypothesis.supporting_episode_ids + (() if is_conflict else (episode.episode_id,))
            ),
            conflicting_episode_ids=(
                hypothesis.conflicting_episode_ids + ((episode.episode_id,) if is_conflict else ())
            ),
            support_count=support_count,
            conflict_count=conflict_count,
            status=status,
            promotion_eligibility=promotion_eligibility,
            blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
            confidence=confidence,
            evidence_quality=evidence_quality,
        ),
        status_reason,
    )


def _proposal_from_hypothesis(hypothesis: ProvisionalLexicalHypothesis) -> LexicalEntryProposal:
    return LexicalEntryProposal(
        surface_form=hypothesis.target_surface_form,
        canonical_form=hypothesis.target_lemma or hypothesis.target_surface_form,
        language_code=hypothesis.language_code,
        part_of_speech_candidates=(),
        sense_hypotheses=tuple(
            replace(
                sense,
                provisional=False,
                status_hint=LexicalSenseStatus.STABLE,
            )
            for sense in hypothesis.candidate_sense_bundle
        ),
        lemma=hypothesis.target_lemma or hypothesis.target_surface_form,
        aliases=(hypothesis.target_surface_form,),
        confidence=hypothesis.confidence,
        evidence_ref=f"lexicon.hypothesis_promotion:{hypothesis.hypothesis_id}",
    )


def _compatibility_markers(
    *,
    state: LexiconState,
    expected_schema_version: str,
    expected_lexicon_version: str,
    expected_taxonomy_version: str,
) -> tuple[str, ...]:
    markers: list[str] = []
    if state.schema_version != expected_schema_version:
        markers.append("schema_version_mismatch")
    if state.lexicon_version != expected_lexicon_version:
        markers.append("lexicon_version_mismatch")
    if state.taxonomy_version != expected_taxonomy_version:
        markers.append("taxonomy_version_mismatch")
    return tuple(markers)


def _entry_compatibility_markers(
    *,
    entry: LexicalEntry,
    state: LexiconState,
) -> tuple[str, ...]:
    markers: list[str] = []
    if entry.schema_version != state.schema_version:
        markers.append("entry_schema_version_mismatch")
    if entry.lexicon_version != state.lexicon_version:
        markers.append("entry_lexicon_version_mismatch")
    if entry.taxonomy_version != state.taxonomy_version:
        markers.append("entry_taxonomy_version_mismatch")
    return tuple(markers)


def _episode_compatibility_markers(
    *,
    episode: LexicalUsageEpisode,
    expected_schema_version: str,
    expected_lexicon_version: str,
    expected_taxonomy_version: str,
) -> tuple[str, ...]:
    markers: list[str] = []
    if episode.schema_version != expected_schema_version:
        markers.append("episode_schema_version_mismatch")
    if episode.lexicon_version != expected_lexicon_version:
        markers.append("episode_lexicon_version_mismatch")
    if episode.taxonomy_version != expected_taxonomy_version:
        markers.append("episode_taxonomy_version_mismatch")
    return tuple(markers)


def _hypothesis_compatibility_markers(
    *,
    hypothesis: ProvisionalLexicalHypothesis,
    expected_schema_version: str,
    expected_lexicon_version: str,
    expected_taxonomy_version: str,
) -> tuple[str, ...]:
    markers: list[str] = []
    if hypothesis.schema_version != expected_schema_version:
        markers.append("hypothesis_schema_version_mismatch")
    if hypothesis.lexicon_version != expected_lexicon_version:
        markers.append("hypothesis_lexicon_version_mismatch")
    if hypothesis.taxonomy_version != expected_taxonomy_version:
        markers.append("hypothesis_taxonomy_version_mismatch")
    return tuple(markers)


def _effective_min_support_for_promotion(min_support: int) -> int:
    # Ordinary episode learning must not stabilize after a single observation.
    return max(2, int(min_support))


def _freeze_incompatible_entries(
    *,
    entries: tuple[LexicalEntry, ...],
    state: LexiconState,
) -> tuple[tuple[LexicalEntry, ...], tuple[LexiconBlockedUpdate, ...], tuple[LexiconUpdateEvent, ...]]:
    adjusted_entries: list[LexicalEntry] = []
    blocked_updates: list[LexiconBlockedUpdate] = []
    update_events: list[LexiconUpdateEvent] = []
    for entry in entries:
        markers = _entry_compatibility_markers(entry=entry, state=state)
        if not markers:
            adjusted_entries.append(entry)
            continue
        marker_value = "|".join(markers)
        blocked = LexiconBlockedUpdate(
            surface_form=entry.canonical_form,
            reason="entry version mismatch frozen to avoid incompatible carry-forward",
            frozen=True,
            provenance=f"lexicon.entry_compatibility_guard:{entry.entry_id}",
            compatibility_marker=marker_value,
        )
        blocked_updates.append(blocked)
        update_events.append(
            LexiconUpdateEvent(
                event_id=f"lexev-{uuid4().hex[:10]}",
                entry_id=entry.entry_id,
                update_kind=LexiconUpdateKind.FREEZE_UPDATE,
                reason_tags=("entry_version_mismatch",),
                provenance=blocked.provenance,
            )
        )
        adjusted_entries.append(
            replace(
                entry,
                entry_status=LexicalAcquisitionStatus.FROZEN,
                acquisition_state=replace(
                    entry.acquisition_state,
                    status=LexicalAcquisitionStatus.FROZEN,
                    frozen_update=True,
                    blocked_reason=f"entry_version_mismatch:{marker_value}",
                ),
            )
        )
    return tuple(adjusted_entries), tuple(blocked_updates), tuple(update_events)


def _query_matches(
    state: LexiconState,
    *,
    query: LexiconQueryRequest,
    normalized_form: str,
) -> tuple[LexicalEntry, ...]:
    matches: list[LexicalEntry] = []
    for entry in state.entries:
        if query.language_code and entry.language_code != query.language_code:
            continue
        if not query.allow_provisional and entry.acquisition_state.status != LexicalAcquisitionStatus.STABLE:
            continue
        in_surface = any(variant.normalized_form == normalized_form for variant in entry.surface_variants)
        in_alias = any(_normalize(alias) == normalized_form for alias in entry.aliases)
        in_lemma = bool(entry.lemma and _normalize(entry.lemma) == normalized_form)
        if in_surface or in_alias or in_lemma or _normalize(entry.canonical_form) == normalized_form:
            matches.append(entry)
    return tuple(matches)


def _find_matching_entries(
    *,
    state: tuple[LexicalEntry, ...],
    proposal: LexicalEntryProposal,
    expected_schema_version: str,
    expected_lexicon_version: str,
    expected_taxonomy_version: str,
) -> tuple[LexicalEntry, ...]:
    normalized_surface = _normalize(proposal.surface_form)
    normalized_canonical = _normalize(proposal.canonical_form or proposal.surface_form)
    matches: list[LexicalEntry] = []
    for entry in state:
        if entry.schema_version != expected_schema_version:
            continue
        if entry.lexicon_version != expected_lexicon_version:
            continue
        if entry.taxonomy_version != expected_taxonomy_version:
            continue
        if entry.language_code != proposal.language_code:
            continue
        if _normalize(entry.canonical_form) == normalized_canonical:
            matches.append(entry)
            continue
        if entry.lemma and _normalize(entry.lemma) == normalized_canonical:
            matches.append(entry)
            continue
        if any(_normalize(alias) == normalized_surface for alias in entry.aliases):
            matches.append(entry)
            continue
        if any(variant.normalized_form == normalized_surface for variant in entry.surface_variants):
            matches.append(entry)
    return tuple(matches)


def _ambiguous_update_targets(
    *,
    matches: tuple[LexicalEntry, ...],
    proposal: LexicalEntryProposal,
    score_margin: float,
) -> tuple[LexicalEntry, ...]:
    if len(matches) < 2:
        return ()
    scored_matches = sorted(
        ((_entry_match_score(entry=entry, proposal=proposal), entry) for entry in matches),
        key=lambda item: item[0],
        reverse=True,
    )
    top_score = scored_matches[0][0]
    margin = max(0.0, float(score_margin))
    ambiguous = tuple(
        entry for score, entry in scored_matches if score >= (top_score - margin)
    )
    return ambiguous if len(ambiguous) > 1 else ()


def _entry_match_score(
    *,
    entry: LexicalEntry,
    proposal: LexicalEntryProposal,
) -> float:
    score = 0.0
    normalized_surface = _normalize(proposal.surface_form)
    normalized_canonical = _normalize(proposal.canonical_form or proposal.surface_form)
    if _normalize(entry.canonical_form) == normalized_canonical:
        score += 1.0
    if entry.lemma and _normalize(entry.lemma) == normalized_canonical:
        score += 0.5
    if any(_normalize(alias) == normalized_surface for alias in entry.aliases):
        score += 0.5
    if any(variant.normalized_form == normalized_surface for variant in entry.surface_variants):
        score += 1.0
    proposal_pos = set(proposal.part_of_speech_candidates)
    if proposal_pos:
        score += len(proposal_pos.intersection(set(entry.part_of_speech_candidates))) / len(proposal_pos)
    score += entry.confidence * 0.1
    return round(score, 4)


def _select_update_target(
    matches: tuple[LexicalEntry, ...],
    *,
    proposal: LexicalEntryProposal,
) -> LexicalEntry:
    if len(matches) == 1:
        return matches[0]
    sorted_matches = sorted(
        matches,
        key=lambda entry: _entry_match_score(entry=entry, proposal=proposal),
        reverse=True,
    )
    return sorted_matches[0]


def _update_entry(
    *,
    existing: LexicalEntry,
    proposal: LexicalEntryProposal,
    context: LexiconUpdateContext,
) -> tuple[LexicalEntry, LexiconUpdateEvent, LexiconBlockedUpdate | None]:
    merged_senses, has_conflict = _merge_senses(
        existing.sense_records,
        proposal.sense_hypotheses,
        context=context,
        provenance=proposal.evidence_ref or "lexicon.entry_update",
    )
    merged_examples = _merge_examples(
        existing.examples,
        entry_id=existing.entry_id,
        sense_records=merged_senses,
        proposal=proposal,
    )
    merged_senses = _attach_example_ids_to_senses(merged_senses, merged_examples)
    merged_surface = _merge_surface_variants(existing.surface_variants, proposal=proposal)
    merged_pos = tuple(dict.fromkeys(existing.part_of_speech_candidates + proposal.part_of_speech_candidates))
    evidence_count = existing.acquisition_state.evidence_count + 1
    revision_count = existing.acquisition_state.revision_count + 1
    merged_confidence = _clamp((existing.confidence * 0.6) + (_clamp(proposal.confidence) * 0.4))

    status = LexicalAcquisitionStatus.PROVISIONAL
    conflict_state = existing.conflict_state
    blocked: LexiconBlockedUpdate | None = None
    if proposal.conflict_hint or has_conflict:
        conflict_state = LexicalConflictState.EVIDENCE_CONFLICT
        status = LexicalAcquisitionStatus.CONFLICTED
        merged_senses = _apply_sense_conflict_state(
            merged_senses,
            freeze=context.freeze_on_conflict,
        )
        if context.freeze_on_conflict:
            status = LexicalAcquisitionStatus.FROZEN
            blocked = LexiconBlockedUpdate(
                surface_form=proposal.surface_form,
                reason="conflicting lexical evidence forced freeze path",
                frozen=True,
                provenance=proposal.evidence_ref or "lexicon.conflict_guard",
            )
    elif (
        evidence_count >= context.min_evidence_for_stable
        and merged_confidence >= context.stable_confidence_threshold
    ):
        status = LexicalAcquisitionStatus.STABLE

    updated = replace(
        existing,
        lemma=proposal.lemma or existing.lemma,
        aliases=tuple(dict.fromkeys(existing.aliases + proposal.aliases)),
        surface_variants=merged_surface,
        part_of_speech_candidates=merged_pos,
        sense_records=merged_senses,
        examples=merged_examples,
        entry_status=status,
        acquisition_mode=(
            LexicalAcquisitionMode.EPISODE_PROMOTION
            if _is_episode_promotion_proposal(proposal.evidence_ref)
            else (
                existing.acquisition_mode
                if existing.acquisition_mode != LexicalAcquisitionMode.UNKNOWN
                else LexicalAcquisitionMode.DIRECT_CURATION
            )
        ),
        composition_profile=proposal.composition_profile or existing.composition_profile,
        reference_profile=proposal.reference_profile or existing.reference_profile,
        acquisition_state=LexicalAcquisitionState(
            status=status,
            evidence_count=evidence_count,
            last_supporting_evidence_ref=proposal.evidence_ref or existing.acquisition_state.last_supporting_evidence_ref,
            revision_count=revision_count,
            frozen_update=status == LexicalAcquisitionStatus.FROZEN,
            staleness_steps=0,
            decay_marker=1.0,
            blocked_reason=blocked.reason if blocked is not None else None,
        ),
        confidence=merged_confidence,
        conflict_state=conflict_state,
        provenance=proposal.evidence_ref or existing.provenance,
        schema_version=existing.schema_version,
        lexicon_version=existing.lexicon_version,
        taxonomy_version=existing.taxonomy_version,
    )
    event_kind = LexiconUpdateKind.REGISTER_CONFLICT if blocked else LexiconUpdateKind.UPDATE_ENTRY
    event_tags = ("conflict",) if blocked else ("evidence_update",)
    event = LexiconUpdateEvent(
        event_id=f"lexev-{uuid4().hex[:10]}",
        entry_id=updated.entry_id,
        update_kind=event_kind,
        reason_tags=event_tags,
        provenance=proposal.evidence_ref or "lexicon.update",
    )
    return updated, event, blocked


def _create_entry(
    *,
    proposal: LexicalEntryProposal,
    context: LexiconUpdateContext,
) -> tuple[LexicalEntry, LexiconUpdateEvent]:
    entry_id = f"lex-{uuid4().hex[:10]}"
    normalized_surface = _normalize(proposal.surface_form)
    canonical_form = proposal.canonical_form or normalized_surface
    lemma = proposal.lemma or canonical_form
    aliases = tuple(dict.fromkeys((proposal.aliases or ()) + (canonical_form,)))
    provenance = proposal.evidence_ref or "lexicon.entry_proposal"
    sense_records = tuple(
        LexicalSenseRecord(
            sense_id=f"sense-{uuid4().hex[:10]}",
            sense_family=hypothesis.sense_family,
            sense_label=hypothesis.sense_label,
            coarse_semantic_type=hypothesis.coarse_semantic_type,
            compatibility_cues=hypothesis.compatibility_cues,
            anti_cues=hypothesis.anti_cues,
            confidence=_clamp(hypothesis.confidence),
            provisional=hypothesis.provisional,
            provenance=provenance,
            status=_sense_status_for_hypothesis(hypothesis),
            evidence_count=1,
            conflict_markers=(),
            example_ids=(),
        )
        for hypothesis in proposal.sense_hypotheses
    )
    entry_examples = _build_examples_for_new_entry(
        entry_id=entry_id,
        sense_records=sense_records,
        proposal=proposal,
        provenance=provenance,
    )
    sense_records = _attach_example_ids_to_senses(sense_records, entry_examples)
    status = LexicalAcquisitionStatus.PROVISIONAL
    confidence = _clamp(proposal.confidence)
    if (
        len(sense_records) == 1
        and confidence >= context.stable_confidence_threshold
        and context.min_evidence_for_stable <= 1
    ):
        status = LexicalAcquisitionStatus.STABLE

    entry = LexicalEntry(
        entry_id=entry_id,
        canonical_form=canonical_form,
        lemma=lemma,
        aliases=aliases,
        surface_variants=(
            SurfaceFormRecord(
                form=proposal.surface_form,
                normalized_form=normalized_surface,
                locale_hint=proposal.language_code,
                variant_kind="observed",
                confidence=confidence,
                provenance=provenance,
            ),
        ),
        language_code=proposal.language_code,
        part_of_speech_candidates=proposal.part_of_speech_candidates,
        sense_records=sense_records,
        examples=entry_examples,
        entry_status=status,
        acquisition_mode=(
            LexicalAcquisitionMode.EPISODE_PROMOTION
            if _is_episode_promotion_proposal(proposal.evidence_ref)
            else LexicalAcquisitionMode.DIRECT_CURATION
        ),
        composition_profile=proposal.composition_profile or _default_composition_profile(),
        reference_profile=proposal.reference_profile or _default_reference_profile(),
        acquisition_state=LexicalAcquisitionState(
            status=status,
            evidence_count=1,
            last_supporting_evidence_ref=proposal.evidence_ref or None,
            revision_count=1,
            frozen_update=False,
            staleness_steps=0,
            decay_marker=1.0,
            blocked_reason=None,
        ),
        confidence=confidence,
        conflict_state=LexicalConflictState.NONE,
        provenance=provenance,
        schema_version=DEFAULT_LEXICON_SCHEMA_VERSION,
        lexicon_version=DEFAULT_LEXICON_VERSION,
        taxonomy_version=DEFAULT_LEXICON_TAXONOMY_VERSION,
    )
    event = LexiconUpdateEvent(
        event_id=f"lexev-{uuid4().hex[:10]}",
        entry_id=entry.entry_id,
        update_kind=LexiconUpdateKind.CREATE_ENTRY,
        reason_tags=("create_entry",),
        provenance=entry.provenance,
    )
    return entry, event


def _is_episode_promotion_proposal(evidence_ref: str | None) -> bool:
    return bool(evidence_ref and evidence_ref.startswith("lexicon.hypothesis_promotion:"))


def _merge_senses(
    existing_senses: tuple[LexicalSenseRecord, ...],
    sense_hypotheses: tuple[LexicalSenseHypothesis, ...],
    *,
    context: LexiconUpdateContext,
    provenance: str,
) -> tuple[tuple[LexicalSenseRecord, ...], bool]:
    merged = list(existing_senses)
    conflict = False
    for hypothesis in sense_hypotheses:
        found_index = next(
            (
                index
                for index, record in enumerate(merged)
                if record.sense_family == hypothesis.sense_family
                and record.sense_label == hypothesis.sense_label
            ),
            None,
        )
        if found_index is None:
            merged.append(
                LexicalSenseRecord(
                    sense_id=f"sense-{uuid4().hex[:10]}",
                    sense_family=hypothesis.sense_family,
                    sense_label=hypothesis.sense_label,
                    coarse_semantic_type=hypothesis.coarse_semantic_type,
                    compatibility_cues=hypothesis.compatibility_cues,
                    anti_cues=hypothesis.anti_cues,
                    confidence=_clamp(hypothesis.confidence),
                    provisional=hypothesis.provisional,
                    provenance=provenance,
                    status=_sense_status_for_hypothesis(hypothesis),
                    evidence_count=1,
                    conflict_markers=(),
                    example_ids=(),
                )
            )
            continue
        record = merged[found_index]
        anti_cue_overlap = set(record.compatibility_cues).intersection(set(hypothesis.anti_cues))
        cue_anti_overlap = set(record.anti_cues).intersection(set(hypothesis.compatibility_cues))
        conflict_markers = set(record.conflict_markers)
        if anti_cue_overlap or cue_anti_overlap:
            conflict = True
            conflict_markers.add("cue_conflict")
        updated_confidence = _clamp((record.confidence * 0.6) + (_clamp(hypothesis.confidence) * 0.4))
        updated_evidence = record.evidence_count + 1
        next_status = record.status
        if conflict_markers:
            next_status = (
                LexicalSenseStatus.FROZEN
                if context.freeze_on_conflict
                else LexicalSenseStatus.CONFLICTED
            )
        elif (
            updated_evidence >= context.min_evidence_for_stable
            and updated_confidence >= context.stable_confidence_threshold
        ):
            next_status = LexicalSenseStatus.STABLE
        elif hypothesis.provisional:
            next_status = LexicalSenseStatus.PROVISIONAL
        else:
            next_status = LexicalSenseStatus.UNKNOWN
        merged[found_index] = replace(
            record,
            compatibility_cues=tuple(
                dict.fromkeys(record.compatibility_cues + hypothesis.compatibility_cues)
            ),
            anti_cues=tuple(dict.fromkeys(record.anti_cues + hypothesis.anti_cues)),
            confidence=updated_confidence,
            provisional=record.provisional and hypothesis.provisional,
            status=next_status,
            evidence_count=updated_evidence,
            conflict_markers=tuple(sorted(conflict_markers)),
        )
    return tuple(merged), conflict


def _apply_sense_conflict_state(
    sense_records: tuple[LexicalSenseRecord, ...],
    *,
    freeze: bool,
) -> tuple[LexicalSenseRecord, ...]:
    target = LexicalSenseStatus.FROZEN if freeze else LexicalSenseStatus.CONFLICTED
    updated: list[LexicalSenseRecord] = []
    for sense in sense_records:
        markers = tuple(dict.fromkeys(sense.conflict_markers + ("entry_level_conflict",)))
        updated.append(
            replace(
                sense,
                status=target,
                conflict_markers=markers,
            )
        )
    return tuple(updated)


def _sense_status_for_hypothesis(hypothesis: LexicalSenseHypothesis) -> LexicalSenseStatus:
    if hypothesis.status_hint is not None:
        return hypothesis.status_hint
    if hypothesis.provisional:
        return LexicalSenseStatus.PROVISIONAL
    return LexicalSenseStatus.UNKNOWN


def _build_examples_for_new_entry(
    *,
    entry_id: str,
    sense_records: tuple[LexicalSenseRecord, ...],
    proposal: LexicalEntryProposal,
    provenance: str,
) -> tuple[LexicalExampleRecord, ...]:
    examples: list[LexicalExampleRecord] = []
    for text in proposal.entry_example_texts:
        normalized = text.strip()
        if not normalized:
            continue
        examples.append(
            LexicalExampleRecord(
                example_id=f"lexex-{uuid4().hex[:10]}",
                example_text=normalized,
                linked_entry_id=entry_id,
                linked_sense_id=None,
                status=LexicalExampleStatus.ILLUSTRATIVE,
                illustrative_only=True,
                provenance=provenance,
            )
        )
    sense_by_label = {record.sense_label: record for record in sense_records}
    for hypothesis in proposal.sense_hypotheses:
        target_sense = sense_by_label.get(hypothesis.sense_label)
        if target_sense is None:
            continue
        for text in hypothesis.example_texts:
            normalized = text.strip()
            if not normalized:
                continue
            examples.append(
                LexicalExampleRecord(
                    example_id=f"lexex-{uuid4().hex[:10]}",
                    example_text=normalized,
                    linked_entry_id=entry_id,
                    linked_sense_id=target_sense.sense_id,
                    status=LexicalExampleStatus.PROVISIONAL,
                    illustrative_only=False,
                    provenance=provenance,
                )
            )
    unique: dict[tuple[str, str | None], LexicalExampleRecord] = {}
    for record in examples:
        key = (record.example_text.lower(), record.linked_sense_id)
        unique[key] = record
    return tuple(unique.values())


def _attach_example_ids_to_senses(
    sense_records: tuple[LexicalSenseRecord, ...],
    examples: tuple[LexicalExampleRecord, ...],
) -> tuple[LexicalSenseRecord, ...]:
    linked_example_ids: dict[str, list[str]] = {}
    for example in examples:
        if example.linked_sense_id is None:
            continue
        linked_example_ids.setdefault(example.linked_sense_id, []).append(example.example_id)
    updated: list[LexicalSenseRecord] = []
    for sense in sense_records:
        extra_ids = tuple(linked_example_ids.get(sense.sense_id, ()))
        if not extra_ids:
            updated.append(sense)
            continue
        updated.append(
            replace(
                sense,
                example_ids=tuple(dict.fromkeys(sense.example_ids + extra_ids)),
            )
        )
    return tuple(updated)


def _merge_examples(
    existing_examples: tuple[LexicalExampleRecord, ...],
    *,
    entry_id: str,
    sense_records: tuple[LexicalSenseRecord, ...],
    proposal: LexicalEntryProposal,
) -> tuple[LexicalExampleRecord, ...]:
    additions = _build_examples_for_new_entry(
        entry_id=entry_id,
        sense_records=sense_records,
        proposal=proposal,
        provenance=proposal.evidence_ref or "lexicon.entry_update",
    )
    merged: dict[tuple[str, str | None], LexicalExampleRecord] = {}
    for existing in existing_examples:
        merged[(existing.example_text.lower(), existing.linked_sense_id)] = existing
    for item in additions:
        key = (item.example_text.lower(), item.linked_sense_id)
        merged.setdefault(key, item)
    combined = tuple(merged.values())
    return combined


def _merge_surface_variants(
    existing_variants: tuple[SurfaceFormRecord, ...],
    *,
    proposal: LexicalEntryProposal,
) -> tuple[SurfaceFormRecord, ...]:
    normalized_surface = _normalize(proposal.surface_form)
    if any(variant.normalized_form == normalized_surface for variant in existing_variants):
        return existing_variants
    return existing_variants + (
        SurfaceFormRecord(
            form=proposal.surface_form,
            normalized_form=normalized_surface,
            locale_hint=proposal.language_code,
            variant_kind="observed",
            confidence=_clamp(proposal.confidence),
            provenance=proposal.evidence_ref or "lexicon.entry_update",
        ),
    )


def _apply_decay(
    entries: tuple[LexicalEntry, ...],
    *,
    context: LexiconUpdateContext,
) -> tuple[tuple[LexicalEntry, ...], tuple[LexiconUpdateEvent, ...]]:
    if context.step_delta <= 0:
        return entries, ()
    decayed_entries: list[LexicalEntry] = []
    decay_events: list[LexiconUpdateEvent] = []
    decay_factor = max(0.0, 1.0 - (context.decay_per_step * context.step_delta))
    for entry in entries:
        new_confidence = _clamp(entry.confidence * decay_factor)
        new_acquisition = replace(
            entry.acquisition_state,
            staleness_steps=entry.acquisition_state.staleness_steps + context.step_delta,
            decay_marker=decay_factor,
        )
        decayed_entry = replace(entry, confidence=new_confidence, acquisition_state=new_acquisition)
        decayed_entries.append(decayed_entry)
        if new_confidence != entry.confidence:
            decay_events.append(
                LexiconUpdateEvent(
                    event_id=f"lexev-{uuid4().hex[:10]}",
                    entry_id=entry.entry_id,
                    update_kind=LexiconUpdateKind.DECAY,
                    reason_tags=("decay",),
                    provenance=f"lexicon.decay:{entry.entry_id}",
                )
            )
    return tuple(decayed_entries), tuple(decay_events)


def _query_gate_from_records(
    *,
    records: tuple[LexiconQueryRecord, ...],
    state: LexiconState,
) -> LexiconGateDecision:
    return build_lexicon_gate_decision(
        state=state,
        query_records=records,
        abstain=False,
    )


def _default_composition_profile() -> LexicalCompositionProfile:
    return LexicalCompositionProfile(
        role_hints=(LexicalCompositionRole.UNKNOWN,),
        argument_structure_hints=(),
        can_introduce_predicate_frame=False,
        behaves_as_modifier=False,
        behaves_as_operator=False,
        behaves_as_participant=False,
        behaves_as_referential_carrier=False,
        scope_sensitive=False,
        negation_sensitive=False,
        remains_underspecified=True,
    )


def _default_reference_profile() -> LexicalReferenceProfile:
    return LexicalReferenceProfile(
        pronoun_like=False,
        deictic=False,
        entity_introducing=False,
        anaphora_prone=False,
        quote_sensitive=False,
        requires_context=False,
        can_remain_unresolved=True,
    )


def _seed_entries() -> tuple[LexicalEntry, ...]:
    def make_entry(
        *,
        entry_id: str,
        canonical_form: str,
        language: str,
        variants: tuple[str, ...],
        pos: tuple[str, ...],
        senses: tuple[tuple[str, str, LexicalCoarseSemanticType], ...],
        role_hints: tuple[LexicalCompositionRole, ...],
        reference_profile: LexicalReferenceProfile,
        confidence: float = 0.84,
    ) -> LexicalEntry:
        return LexicalEntry(
            entry_id=entry_id,
            canonical_form=canonical_form,
            surface_variants=tuple(
                SurfaceFormRecord(
                    form=variant,
                    normalized_form=_normalize(variant),
                    locale_hint=language,
                    variant_kind="seed",
                    confidence=confidence,
                    provenance="lexicon.seed",
                )
                for variant in variants
            ),
            language_code=language,
            part_of_speech_candidates=pos,
            sense_records=tuple(
                LexicalSenseRecord(
                    sense_id=f"{entry_id}:{index}",
                    sense_family=family,
                    sense_label=label,
                    coarse_semantic_type=coarse_type,
                    compatibility_cues=(),
                    anti_cues=(),
                    confidence=confidence,
                    provisional=False,
                    provenance="lexicon.seed",
                    status=LexicalSenseStatus.STABLE,
                    evidence_count=5,
                    conflict_markers=(),
                    example_ids=(),
                )
                for index, (family, label, coarse_type) in enumerate(senses, start=1)
            ),
            composition_profile=LexicalCompositionProfile(
                role_hints=role_hints,
                argument_structure_hints=(),
                can_introduce_predicate_frame=LexicalCompositionRole.CONTENT in role_hints,
                behaves_as_modifier=LexicalCompositionRole.MODIFIER in role_hints,
                behaves_as_operator=LexicalCompositionRole.OPERATOR in role_hints,
                behaves_as_participant=LexicalCompositionRole.PARTICIPANT in role_hints,
                behaves_as_referential_carrier=LexicalCompositionRole.REFERENTIAL_CARRIER in role_hints,
                scope_sensitive=LexicalCompositionRole.OPERATOR in role_hints,
                negation_sensitive=canonical_form in {"not", "не"},
                remains_underspecified=LexicalCompositionRole.OPERATOR in role_hints,
            ),
            reference_profile=reference_profile,
            acquisition_state=LexicalAcquisitionState(
                status=LexicalAcquisitionStatus.STABLE,
                evidence_count=5,
                last_supporting_evidence_ref="lexicon.seed",
                revision_count=1,
                frozen_update=False,
                staleness_steps=0,
                decay_marker=1.0,
            ),
            confidence=confidence,
            conflict_state=LexicalConflictState.NONE,
            provenance="lexicon.seed",
            lemma=canonical_form,
            aliases=(canonical_form,),
            examples=(),
            entry_status=LexicalAcquisitionStatus.STABLE,
            acquisition_mode=LexicalAcquisitionMode.SEED,
            schema_version=DEFAULT_LEXICON_SCHEMA_VERSION,
            lexicon_version=DEFAULT_LEXICON_VERSION,
            taxonomy_version=DEFAULT_LEXICON_TAXONOMY_VERSION,
        )

    pronoun_profile = LexicalReferenceProfile(
        pronoun_like=True,
        deictic=True,
        entity_introducing=False,
        anaphora_prone=True,
        quote_sensitive=True,
        requires_context=True,
        can_remain_unresolved=True,
    )
    deictic_profile = LexicalReferenceProfile(
        pronoun_like=False,
        deictic=True,
        entity_introducing=False,
        anaphora_prone=False,
        quote_sensitive=True,
        requires_context=True,
        can_remain_unresolved=True,
    )
    content_profile = LexicalReferenceProfile(
        pronoun_like=False,
        deictic=False,
        entity_introducing=True,
        anaphora_prone=True,
        quote_sensitive=False,
        requires_context=False,
        can_remain_unresolved=True,
    )
    operator_profile = LexicalReferenceProfile(
        pronoun_like=False,
        deictic=False,
        entity_introducing=False,
        anaphora_prone=False,
        quote_sensitive=False,
        requires_context=False,
        can_remain_unresolved=True,
    )

    return (
        make_entry(
            entry_id="seed-pron-i",
            canonical_form="i",
            language="en",
            variants=("i",),
            pos=("pronoun",),
            senses=(("person.deixis", "speaker", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-pron-you",
            canonical_form="you",
            language="en",
            variants=("you",),
            pos=("pronoun",),
            senses=(("person.deixis", "addressee", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-pron-he",
            canonical_form="he",
            language="en",
            variants=("he",),
            pos=("pronoun",),
            senses=(("anaphora.person", "third_person_masc", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-pron-she",
            canonical_form="she",
            language="en",
            variants=("she",),
            pos=("pronoun",),
            senses=(("anaphora.person", "third_person_fem", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-pron-it",
            canonical_form="it",
            language="en",
            variants=("it",),
            pos=("pronoun",),
            senses=(("anaphora.nonperson", "third_person_neutral", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-pron-ya",
            canonical_form="я",
            language="ru",
            variants=("я",),
            pos=("pronoun",),
            senses=(("person.deixis", "speaker", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-pron-ty",
            canonical_form="ты",
            language="ru",
            variants=("ты",),
            pos=("pronoun",),
            senses=(("person.deixis", "addressee", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-pron-on",
            canonical_form="он",
            language="ru",
            variants=("он",),
            pos=("pronoun",),
            senses=(("anaphora.person", "third_person_masc", LexicalCoarseSemanticType.PRONOMINAL),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=pronoun_profile,
        ),
        make_entry(
            entry_id="seed-deixis-here",
            canonical_form="here",
            language="en",
            variants=("here",),
            pos=("adverb",),
            senses=(("deixis.location", "near_speaker", LexicalCoarseSemanticType.DEICTIC),),
            role_hints=(LexicalCompositionRole.MODIFIER,),
            reference_profile=deictic_profile,
        ),
        make_entry(
            entry_id="seed-deixis-there",
            canonical_form="there",
            language="en",
            variants=("there",),
            pos=("adverb",),
            senses=(("deixis.location", "distal_location", LexicalCoarseSemanticType.DEICTIC),),
            role_hints=(LexicalCompositionRole.MODIFIER,),
            reference_profile=deictic_profile,
        ),
        make_entry(
            entry_id="seed-deixis-now",
            canonical_form="now",
            language="en",
            variants=("now",),
            pos=("adverb",),
            senses=(("deixis.time", "current_time", LexicalCoarseSemanticType.TEMPORAL),),
            role_hints=(LexicalCompositionRole.MODIFIER,),
            reference_profile=deictic_profile,
        ),
        make_entry(
            entry_id="seed-deixis-this",
            canonical_form="this",
            language="en",
            variants=("this",),
            pos=("determiner", "pronoun"),
            senses=(("deixis.object", "proximal_demonstrative", LexicalCoarseSemanticType.DEICTIC),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=deictic_profile,
        ),
        make_entry(
            entry_id="seed-deixis-that",
            canonical_form="that",
            language="en",
            variants=("that",),
            pos=("determiner", "pronoun"),
            senses=(("deixis.object", "distal_demonstrative", LexicalCoarseSemanticType.DEICTIC),),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=deictic_profile,
        ),
        make_entry(
            entry_id="seed-deixis-eto",
            canonical_form="это",
            language="ru",
            variants=("это",),
            pos=("pronoun", "particle"),
            senses=(
                ("deixis.object", "demonstrative", LexicalCoarseSemanticType.DEICTIC),
                ("discourse.placeholder", "placeholder_reference", LexicalCoarseSemanticType.PRONOMINAL),
            ),
            role_hints=(LexicalCompositionRole.REFERENTIAL_CARRIER,),
            reference_profile=deictic_profile,
        ),
        make_entry(
            entry_id="seed-neg-not",
            canonical_form="not",
            language="en",
            variants=("not",),
            pos=("particle",),
            senses=(("operator.negation", "negation", LexicalCoarseSemanticType.OPERATOR),),
            role_hints=(LexicalCompositionRole.OPERATOR,),
            reference_profile=operator_profile,
        ),
        make_entry(
            entry_id="seed-neg-ne",
            canonical_form="не",
            language="ru",
            variants=("не",),
            pos=("particle",),
            senses=(("operator.negation", "negation", LexicalCoarseSemanticType.OPERATOR),),
            role_hints=(LexicalCompositionRole.OPERATOR,),
            reference_profile=operator_profile,
        ),
        make_entry(
            entry_id="seed-temp-yesterday",
            canonical_form="yesterday",
            language="en",
            variants=("yesterday",),
            pos=("adverb",),
            senses=(("temporal.anchor", "past_day", LexicalCoarseSemanticType.TEMPORAL),),
            role_hints=(LexicalCompositionRole.MODIFIER,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-temp-tomorrow",
            canonical_form="tomorrow",
            language="en",
            variants=("tomorrow",),
            pos=("adverb",),
            senses=(("temporal.anchor", "future_day", LexicalCoarseSemanticType.TEMPORAL),),
            role_hints=(LexicalCompositionRole.MODIFIER,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-quant-all",
            canonical_form="all",
            language="en",
            variants=("all",),
            pos=("quantifier",),
            senses=(("quantifier.total", "universal", LexicalCoarseSemanticType.QUANTIFIER),),
            role_hints=(LexicalCompositionRole.OPERATOR,),
            reference_profile=operator_profile,
        ),
        make_entry(
            entry_id="seed-quant-some",
            canonical_form="some",
            language="en",
            variants=("some",),
            pos=("quantifier",),
            senses=(("quantifier.partial", "existential", LexicalCoarseSemanticType.QUANTIFIER),),
            role_hints=(LexicalCompositionRole.OPERATOR,),
            reference_profile=operator_profile,
        ),
        make_entry(
            entry_id="seed-quant-many",
            canonical_form="many",
            language="en",
            variants=("many",),
            pos=("quantifier",),
            senses=(("quantifier.amount", "high_count", LexicalCoarseSemanticType.QUANTIFIER),),
            role_hints=(LexicalCompositionRole.OPERATOR,),
            reference_profile=operator_profile,
        ),
        make_entry(
            entry_id="seed-verb-be",
            canonical_form="be",
            language="en",
            variants=("be", "is", "are", "was", "were"),
            pos=("verb",),
            senses=(("event.linking", "copula", LexicalCoarseSemanticType.EVENT),),
            role_hints=(LexicalCompositionRole.CONTENT,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-verb-have",
            canonical_form="have",
            language="en",
            variants=("have", "has", "had"),
            pos=("verb",),
            senses=(("event.possession", "possess", LexicalCoarseSemanticType.EVENT),),
            role_hints=(LexicalCompositionRole.CONTENT,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-verb-go",
            canonical_form="go",
            language="en",
            variants=("go", "goes", "went"),
            pos=("verb",),
            senses=(("event.motion", "move", LexicalCoarseSemanticType.EVENT),),
            role_hints=(LexicalCompositionRole.CONTENT,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-verb-say",
            canonical_form="say",
            language="en",
            variants=("say", "said"),
            pos=("verb",),
            senses=(("event.report", "quoted_report", LexicalCoarseSemanticType.EVENT),),
            role_hints=(LexicalCompositionRole.CONTENT,),
            reference_profile=LexicalReferenceProfile(
                pronoun_like=False,
                deictic=False,
                entity_introducing=False,
                anaphora_prone=False,
                quote_sensitive=True,
                requires_context=False,
                can_remain_unresolved=True,
            ),
        ),
        make_entry(
            entry_id="seed-noun-person",
            canonical_form="person",
            language="en",
            variants=("person", "people"),
            pos=("noun",),
            senses=(("entity.person", "human", LexicalCoarseSemanticType.ENTITY),),
            role_hints=(LexicalCompositionRole.PARTICIPANT,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-noun-thing",
            canonical_form="thing",
            language="en",
            variants=("thing", "things"),
            pos=("noun",),
            senses=(("entity.object", "generic_object", LexicalCoarseSemanticType.ENTITY),),
            role_hints=(LexicalCompositionRole.PARTICIPANT,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-noun-bank",
            canonical_form="bank",
            language="en",
            variants=("bank",),
            pos=("noun",),
            senses=(
                ("entity.institution", "financial_institution", LexicalCoarseSemanticType.ENTITY),
                ("entity.location", "river_edge", LexicalCoarseSemanticType.ENTITY),
            ),
            role_hints=(LexicalCompositionRole.PARTICIPANT,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-noun-key",
            canonical_form="key",
            language="en",
            variants=("key",),
            pos=("noun",),
            senses=(
                ("entity.tool", "key_tool", LexicalCoarseSemanticType.ENTITY),
                ("attribute.criticality", "important", LexicalCoarseSemanticType.ATTRIBUTE),
            ),
            role_hints=(LexicalCompositionRole.PARTICIPANT, LexicalCompositionRole.MODIFIER),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-can-modal",
            canonical_form="can",
            language="en",
            variants=("can",),
            pos=("modal", "verb"),
            senses=(("operator.modality", "ability_modal", LexicalCoarseSemanticType.OPERATOR),),
            role_hints=(LexicalCompositionRole.OPERATOR,),
            reference_profile=operator_profile,
        ),
        make_entry(
            entry_id="seed-can-noun",
            canonical_form="can",
            language="en",
            variants=("can",),
            pos=("noun",),
            senses=(("entity.container", "metal_container", LexicalCoarseSemanticType.ENTITY),),
            role_hints=(LexicalCompositionRole.PARTICIPANT,),
            reference_profile=content_profile,
        ),
        make_entry(
            entry_id="seed-ru-vremya",
            canonical_form="сейчас",
            language="ru",
            variants=("сейчас",),
            pos=("adverb",),
            senses=(("deixis.time", "current_time", LexicalCoarseSemanticType.TEMPORAL),),
            role_hints=(LexicalCompositionRole.MODIFIER,),
            reference_profile=deictic_profile,
        ),
        make_entry(
            entry_id="seed-ru-place",
            canonical_form="здесь",
            language="ru",
            variants=("здесь",),
            pos=("adverb",),
            senses=(("deixis.location", "speaker_location", LexicalCoarseSemanticType.DEICTIC),),
            role_hints=(LexicalCompositionRole.MODIFIER,),
            reference_profile=deictic_profile,
        ),
    )
