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
    LexicalReferenceProfile,
    LexicalSenseHypothesis,
    LexicalSenseRecord,
    LexicalSenseStatus,
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
    SurfaceFormRecord,
    UnknownLexicalItem,
    UnknownLexicalObservation,
)
from substrate.lexicon.policy import (
    build_lexicon_gate_decision,
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


def create_empty_lexicon_state(
    *,
    schema_version: str = DEFAULT_LEXICON_SCHEMA_VERSION,
    lexicon_version: str = DEFAULT_LEXICON_VERSION,
    taxonomy_version: str = DEFAULT_LEXICON_TAXONOMY_VERSION,
) -> LexiconState:
    return LexiconState(
        entries=(),
        unknown_items=(),
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


def lexicon_result_to_payload(result: LexiconUpdateResult | LexiconQueryResult) -> dict[str, object]:
    return lexicon_result_snapshot(result)


def reconstruct_lexicon_state_from_snapshot(snapshot: dict[str, object]) -> LexiconState:
    if not isinstance(snapshot, dict):
        raise TypeError("snapshot must be dict payload produced by lexicon_result_to_payload")
    state_payload = snapshot.get("state", snapshot)
    if not isinstance(state_payload, dict):
        raise TypeError("snapshot must contain dict 'state' payload")

    entries_payload = state_payload.get("entries", ())
    unknown_payload = state_payload.get("unknown_items", ())
    unresolved_payload = state_payload.get("unresolved_updates", ())
    frozen_payload = state_payload.get("frozen_updates", ())
    conflict_index_payload = state_payload.get("conflict_index", ())

    if not isinstance(entries_payload, (tuple, list)):
        raise TypeError("state.entries must be tuple/list")
    if not isinstance(unknown_payload, (tuple, list)):
        raise TypeError("state.unknown_items must be tuple/list")
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


def _normalize(value: str) -> str:
    return value.strip().lower()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


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
