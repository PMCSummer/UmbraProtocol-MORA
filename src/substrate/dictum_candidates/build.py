from __future__ import annotations

import re
from collections import defaultdict

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.dictum_candidates.models import (
    ArgumentSlot,
    DictumAmbiguity,
    DictumCandidate,
    DictumCandidateBundle,
    DictumCandidateResult,
    DictumConflict,
    DictumPolarity,
    DictumUnknown,
    MagnitudeMarker,
    NegationMarker,
    PredicateFrame,
    ScopeMarker,
    TemporalAnchorKind,
    TemporalMarker,
    UnderspecifiedSlot,
)
from substrate.dictum_candidates.policy import evaluate_dictum_downstream_gate
from substrate.dictum_candidates.telemetry import (
    build_dictum_telemetry,
    dictum_result_snapshot,
)
from substrate.language_surface.models import UtteranceSurface, UtteranceSurfaceResult
from substrate.lexical_grounding.models import (
    DeixisKind,
    LexicalDiscourseContext,
    LexicalGroundingBundle,
    LexicalGroundingResult,
)
from substrate.morphosyntax.models import (
    MorphPos,
    SyntaxHypothesisResult,
    SyntaxHypothesisSet,
)
from substrate.transition import execute_transition


TEMPORAL_PAST = {"yesterday", "before", "previously", "вчера", "раньше"}
TEMPORAL_PRESENT = {"now", "today", "currently", "сейчас", "сегодня"}
TEMPORAL_FUTURE = {"tomorrow", "later", "soon", "завтра", "позже", "скоро"}

MAGNITUDE_HIGH = {"very", "much", "many", "очень", "сильно", "много"}
MAGNITUDE_LOW = {"little", "few", "slightly", "немного", "слегка", "мало"}

ATTEMPTED_CONSTRUCTION_PATHS: tuple[str, ...] = (
    "dictum.validate_typed_inputs",
    "dictum.syntax_lexical_alignment",
    "dictum.predicate_frame_generation",
    "dictum.argument_slot_generation",
    "dictum.negation_scope_marker_generation",
    "dictum.temporal_marker_generation",
    "dictum.magnitude_marker_generation",
    "dictum.underspecification_marking",
    "dictum.conflict_and_unknown_registration",
    "dictum.downstream_gate",
)


def build_dictum_candidates(
    lexical_grounding_result_or_bundle: LexicalGroundingResult | LexicalGroundingBundle,
    syntax_hypothesis_result_or_set: SyntaxHypothesisResult | SyntaxHypothesisSet,
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult | None = None,
    discourse_context: LexicalDiscourseContext | None = None,
) -> DictumCandidateResult:
    lexical_bundle, lexical_lineage = _extract_lexical_input(lexical_grounding_result_or_bundle)
    syntax_set, syntax_lineage = _extract_syntax_input(syntax_hypothesis_result_or_set)
    surface = _extract_optional_surface(utterance_surface)
    if discourse_context is not None and not isinstance(discourse_context, LexicalDiscourseContext):
        raise TypeError("discourse_context must be LexicalDiscourseContext when provided")
    context = discourse_context or LexicalDiscourseContext()

    if not syntax_set.hypotheses:
        return _abstain_result(
            lexical_bundle=lexical_bundle,
            syntax_set=syntax_set,
            source_lineage=tuple(dict.fromkeys((*lexical_lineage, *syntax_lineage))),
            reason="syntax hypothesis set is empty",
        )

    mention_by_token = {mention.token_id: mention for mention in lexical_bundle.mention_anchors}
    lexeme_by_token: dict[str, list[str]] = defaultdict(list)
    for candidate in lexical_bundle.lexeme_candidates:
        lexeme_by_token[candidate.token_id].append(candidate.candidate_id)

    reference_by_token: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    for hypothesis in lexical_bundle.reference_hypotheses:
        for ref in hypothesis.candidate_ref_ids:
            reference_by_token[hypothesis.token_id].append((ref, hypothesis.unresolved))

    deixis_by_token: dict[str, list[tuple[str | None, bool, DeixisKind]]] = defaultdict(list)
    for candidate in lexical_bundle.deixis_candidates:
        deixis_by_token[candidate.token_id].append(
            (candidate.target_ref, candidate.unresolved, candidate.deixis_kind)
        )

    unknown_mention_ids = {unknown.mention_id for unknown in lexical_bundle.unknown_states}
    syntax_ids = {hypothesis.hypothesis_id for hypothesis in syntax_set.hypotheses}
    lexical_syntax_ids = set(lexical_bundle.linked_hypothesis_ids)
    syntax_alignment_mismatch = bool(lexical_syntax_ids and lexical_syntax_ids - syntax_ids)

    candidate_index = 0
    ambiguity_index = 0
    unknown_index = 0
    blocked_reasons: list[str] = []
    dictum_candidates: list[DictumCandidate] = []
    ambiguities: list[DictumAmbiguity] = []
    unknowns: list[DictumUnknown] = []

    for hypothesis in syntax_set.hypotheses:
        token_feature_by_id = {feature.token_id: feature for feature in hypothesis.token_features}
        unresolved_scope = tuple(
            item for item in hypothesis.unresolved_attachments
            if item.relation_hint in {"negation_scope_ambiguous", "attachment_ambiguous"}
        )

        for clause in hypothesis.clause_graph.clauses:
            clause_tokens = [
                token_feature_by_id[token_id]
                for token_id in clause.token_ids
                if token_id in token_feature_by_id
                and token_feature_by_id[token_id].coarse_pos
                not in {MorphPos.PUNCTUATION, MorphPos.QUOTE, MorphPos.CONJUNCTION}
            ]
            if not clause_tokens:
                blocked_reasons.append(
                    f"clause:{clause.clause_id}:no_lexical_tokens_for_predicate_shell"
                )
                continue

            predicate_tokens = [
                feature for feature in clause_tokens if feature.coarse_pos == MorphPos.VERB_LIKE
            ]
            predicate_fallback = False
            if not predicate_tokens:
                predicate_tokens = [clause_tokens[0]]
                predicate_fallback = True
                blocked_reasons.append(
                    f"clause:{clause.clause_id}:no_explicit_verb_like_predicate_shell_used"
                )

            for predicate in predicate_tokens:
                candidate_index += 1
                candidate_id = f"dictum-{candidate_index}"
                local_ambiguity_reasons: list[str] = []
                quotation_sensitive = bool(
                    mention_by_token.get(predicate.token_id) and mention_by_token[predicate.token_id].inside_quote
                )
                if quotation_sensitive:
                    local_ambiguity_reasons.append("quotation_sensitive_content")
                if predicate_fallback:
                    local_ambiguity_reasons.append("predicate_shell_fallback")

                predicate_lexeme_ids = tuple(lexeme_by_token.get(predicate.token_id, ()))
                predicate_frame = PredicateFrame(
                    frame_id=f"frame-{candidate_id}",
                    predicate_token_id=predicate.token_id,
                    predicate_span=predicate.raw_span,
                    predicate_lexeme_candidate_ids=predicate_lexeme_ids,
                    clause_id=clause.clause_id,
                    quotation_sensitive=quotation_sensitive,
                    confidence=0.52 if predicate_fallback else 0.68,
                    provenance="predicate frame from L02 clause token + L03 lexical candidates",
                )
                argument_token_ids = _argument_tokens_for_predicate(
                    hypothesis=hypothesis,
                    clause_token_ids=clause.token_ids,
                    predicate_token_id=predicate.token_id,
                    token_feature_by_id=token_feature_by_id,
                )
                argument_slots: list[ArgumentSlot] = []
                underspecified: list[UnderspecifiedSlot] = []

                for slot_idx, token_id in enumerate(argument_token_ids, start=1):
                    feature = token_feature_by_id[token_id]
                    role = _role_label(feature.raw_span.start, predicate.raw_span.start, slot_idx)
                    lexical_ids = tuple(lexeme_by_token.get(token_id, ()))
                    reference_rows = reference_by_token.get(token_id, [])
                    reference_ids = tuple(dict.fromkeys(ref for ref, _ in reference_rows))
                    if token_id in deixis_by_token:
                        reference_ids = tuple(
                            dict.fromkeys(
                                [
                                    *reference_ids,
                                    *[
                                        target_ref
                                        for target_ref, _, _ in deixis_by_token[token_id]
                                        if target_ref is not None
                                    ],
                                ]
                            )
                        )
                    mention = mention_by_token.get(token_id)
                    slot_quotation_sensitive = bool(mention and mention.inside_quote)
                    quotation_sensitive = quotation_sensitive or slot_quotation_sensitive

                    unresolved_reasons: list[str] = []
                    if not lexical_ids:
                        unresolved_reasons.append("missing_lexical_candidate_for_slot")
                    elif len(lexical_ids) > 1:
                        unresolved_reasons.append("multiple_lexical_candidates_for_slot")
                    if mention and mention.mention_id in unknown_mention_ids:
                        unresolved_reasons.append("upstream_unknown_lexical_grounding")
                    if any(is_unresolved for _, is_unresolved in reference_rows):
                        unresolved_reasons.append("upstream_reference_unresolved")
                    if token_id in deixis_by_token and any(
                        unresolved for _, unresolved, _ in deixis_by_token[token_id]
                    ):
                        unresolved_reasons.append("upstream_deixis_unresolved")
                    if not reference_ids and reference_rows:
                        unresolved_reasons.append("reference_candidates_empty_after_filter")

                    unresolved = bool(unresolved_reasons)
                    slot = ArgumentSlot(
                        slot_id=f"{candidate_id}-slot-{slot_idx}",
                        role_label=role,
                        token_id=token_id,
                        token_span=feature.raw_span,
                        lexical_candidate_ids=lexical_ids,
                        reference_candidate_ids=reference_ids,
                        unresolved=unresolved,
                        unresolved_reason="; ".join(unresolved_reasons) if unresolved_reasons else None,
                        confidence=0.42 if unresolved else 0.72,
                        provenance="argument slot from L02 token role and L03 lexical/reference candidates",
                    )
                    argument_slots.append(slot)
                    if unresolved:
                        underspecified.append(
                            UnderspecifiedSlot(
                                underspecified_id=f"under-{candidate_id}-{slot.slot_id}",
                                slot_id_or_field=slot.slot_id,
                                reason=slot.unresolved_reason or "slot unresolved",
                                source_ref_ids=(token_id,),
                                confidence=0.33,
                            )
                        )

                if len(predicate_lexeme_ids) > 1:
                    local_ambiguity_reasons.append("predicate_lexical_ambiguity")
                    underspecified.append(
                        UnderspecifiedSlot(
                            underspecified_id=f"under-{candidate_id}-predicate-lexical",
                            slot_id_or_field="predicate_lexeme",
                            reason="multiple lexical candidates available for predicate shell",
                            source_ref_ids=(predicate.token_id,),
                            confidence=0.39,
                        )
                    )

                slot_ids = tuple(slot.slot_id for slot in argument_slots)
                scope_markers: list[ScopeMarker] = []
                for unresolved in unresolved_scope:
                    if unresolved.dependent_token_id not in clause.token_ids:
                        continue
                    affected_slot_ids = tuple(
                        slot.slot_id
                        for slot in argument_slots
                        if slot.token_id in unresolved.candidate_head_ids
                        or slot.token_id == unresolved.dependent_token_id
                    )
                    scope_markers.append(
                        ScopeMarker(
                            scope_marker_id=f"scope-{candidate_id}-{unresolved.unresolved_id}",
                            marker_kind=unresolved.relation_hint,
                            affected_slot_ids=affected_slot_ids,
                            ambiguous=True,
                            reason=unresolved.reason,
                            confidence=unresolved.confidence,
                        )
                    )
                    local_ambiguity_reasons.append("scope_ambiguous")

                negation_scope_ambiguous = any(
                    marker.marker_kind == "negation_scope_ambiguous" for marker in scope_markers
                )
                negation_markers: list[NegationMarker] = []
                if clause.negation_carrier_ids:
                    negation_markers.append(
                        NegationMarker(
                            negation_marker_id=f"neg-{candidate_id}",
                            carrier_token_ids=clause.negation_carrier_ids,
                            scope_target_slot_ids=slot_ids,
                            scope_ambiguous=negation_scope_ambiguous,
                            confidence=0.61 if not negation_scope_ambiguous else 0.49,
                            reason=(
                                "negation carriers from clause graph"
                                if not negation_scope_ambiguous
                                else "negation carriers with unresolved scope"
                            ),
                        )
                    )
                polarity = DictumPolarity.NEGATED if negation_markers else DictumPolarity.AFFIRMATIVE

                temporal_markers = _temporal_markers_for_clause(
                    candidate_id=candidate_id,
                    clause_token_ids=clause.token_ids,
                    token_feature_by_id=token_feature_by_id,
                    deixis_by_token=deixis_by_token,
                    context_ref=context.context_ref,
                )
                magnitude_markers = _magnitude_markers_for_clause(
                    candidate_id=candidate_id,
                    clause_token_ids=clause.token_ids,
                    token_feature_by_id=token_feature_by_id,
                )

                if lexical_bundle.syntax_instability_present:
                    local_ambiguity_reasons.append("lexical_instability_from_upstream_syntax")
                    underspecified.append(
                        UnderspecifiedSlot(
                            underspecified_id=f"under-{candidate_id}-syntax-instability",
                            slot_id_or_field="syntax_instability",
                            reason="upstream lexical grounding marked unstable across syntax hypotheses",
                            source_ref_ids=(hypothesis.hypothesis_id,),
                            confidence=0.37,
                        )
                    )

                if syntax_alignment_mismatch:
                    local_ambiguity_reasons.append("syntax_lexical_reference_mismatch")
                    underspecified.append(
                        UnderspecifiedSlot(
                            underspecified_id=f"under-{candidate_id}-syntax-mismatch",
                            slot_id_or_field="source_alignment",
                            reason="lexical bundle references syntax hypothesis absent in provided syntax set",
                            source_ref_ids=(hypothesis.hypothesis_id,),
                            confidence=0.29,
                        )
                    )

                confidence = _estimate_candidate_confidence(
                    predicate_fallback=predicate_fallback,
                    underspecified_count=len(underspecified),
                    scope_ambiguity_count=sum(1 for marker in scope_markers if marker.ambiguous),
                    quotation_sensitive=quotation_sensitive,
                )
                candidate = DictumCandidate(
                    dictum_candidate_id=candidate_id,
                    source_syntax_hypothesis_ref=hypothesis.hypothesis_id,
                    source_lexical_grounding_ref=lexical_bundle.source_syntax_ref,
                    source_surface_ref=surface.epistemic_unit_ref if surface else lexical_bundle.source_surface_ref,
                    predicate_frame=predicate_frame,
                    argument_slots=tuple(argument_slots),
                    scope_markers=tuple(scope_markers),
                    negation_markers=tuple(negation_markers),
                    temporal_markers=tuple(temporal_markers),
                    magnitude_markers=tuple(magnitude_markers),
                    polarity=polarity,
                    underspecified_slots=tuple(underspecified),
                    ambiguity_reasons=tuple(dict.fromkeys(local_ambiguity_reasons)),
                    quotation_sensitive=quotation_sensitive,
                    confidence=confidence,
                    provenance="L04 dictum skeleton from L03 lexical/reference candidates + L02 syntax frame",
                    no_final_resolution_performed=True,
                )
                dictum_candidates.append(candidate)

                if candidate.ambiguity_reasons:
                    ambiguity_index += 1
                    ambiguities.append(
                        DictumAmbiguity(
                            ambiguity_id=f"d-amb-{ambiguity_index}",
                            dictum_candidate_id=candidate_id,
                            reason="; ".join(candidate.ambiguity_reasons),
                            related_slot_ids=tuple(
                                slot.slot_id for slot in candidate.argument_slots if slot.unresolved
                            ),
                            confidence=0.43,
                        )
                    )

    if not dictum_candidates:
        unknown_index += 1
        unknowns.append(
            DictumUnknown(
                unknown_id=f"d-unknown-{unknown_index}",
                dictum_candidate_ref=None,
                reason="no dictum predicate frames produced from syntax and lexical inputs",
                source_ref_ids=(lexical_bundle.source_syntax_ref, syntax_set.source_surface_ref),
                confidence=0.2,
            )
        )

    candidate_groups: dict[str, list[DictumCandidate]] = defaultdict(list)
    for candidate in dictum_candidates:
        candidate_groups[candidate.predicate_frame.predicate_token_id].append(candidate)

    conflicts: list[DictumConflict] = []
    conflict_index = 0
    for predicate_token_id, group in candidate_groups.items():
        signatures = {
            (
                candidate.source_syntax_hypothesis_ref,
                tuple(slot.token_id for slot in candidate.argument_slots),
                candidate.polarity.value,
            )
            for candidate in group
        }
        if len(signatures) > 1:
            conflict_index += 1
            conflicts.append(
                DictumConflict(
                    conflict_id=f"d-conflict-{conflict_index}",
                    dictum_candidate_ids=tuple(candidate.dictum_candidate_id for candidate in group),
                    reason=f"competing dictum structures for predicate token {predicate_token_id}",
                    confidence=0.51,
                )
            )

    for unknown in lexical_bundle.unknown_states:
        unknown_index += 1
        unknowns.append(
            DictumUnknown(
                unknown_id=f"d-unknown-{unknown_index}",
                dictum_candidate_ref=None,
                reason=f"upstream lexical unknown preserved: {unknown.reason}",
                source_ref_ids=(unknown.mention_id, unknown.token_id),
                confidence=unknown.confidence,
            )
        )

    input_lexical_basis_classes = tuple(
        dict.fromkeys(
            basis.basis_class.value for basis in lexical_bundle.lexical_basis_records
        )
    )
    fallback_basis_present = lexical_bundle.heuristic_fallback_used
    lexicon_basis_missing_or_capped = lexical_bundle.lexicon_handoff_missing or any(
        basis.basis_class.value in {"lexicon_capped_unknown", "no_usable_lexical_basis"}
        for basis in lexical_bundle.lexical_basis_records
    )
    no_strong_lexical_basis_from_upstream = (
        lexical_bundle.no_strong_lexical_claim_from_fallback
        or lexical_bundle.no_strong_lexical_claim_without_lexicon
    )
    lexicon_handoff_missing_upstream = lexical_bundle.lexicon_handoff_missing
    if lexicon_handoff_missing_upstream:
        blocked_reasons.append("upstream_lexicon_handoff_missing")
    if lexicon_basis_missing_or_capped:
        blocked_reasons.append("upstream_lexicon_basis_missing_or_capped")
    if no_strong_lexical_basis_from_upstream:
        blocked_reasons.append("upstream_no_strong_lexical_basis")

    bundle = DictumCandidateBundle(
        source_lexical_grounding_ref=lexical_bundle.source_syntax_ref,
        source_syntax_ref=syntax_set.source_surface_ref,
        source_surface_ref=surface.epistemic_unit_ref if surface else lexical_bundle.source_surface_ref,
        linked_syntax_hypothesis_ids=tuple(hypothesis.hypothesis_id for hypothesis in syntax_set.hypotheses),
        linked_lexical_candidate_ids=tuple(
            dict.fromkeys(candidate.candidate_id for candidate in lexical_bundle.lexeme_candidates)
        ),
        dictum_candidates=tuple(dictum_candidates),
        ambiguities=tuple(ambiguities),
        conflicts=tuple(conflicts),
        unknowns=tuple(unknowns),
        blocked_candidate_reasons=tuple(dict.fromkeys(blocked_reasons)),
        no_final_resolution_performed=True,
        reason="dictum candidates built from typed lexical and syntax hypotheses without modus commitment",
        input_lexical_basis_classes=input_lexical_basis_classes,
        fallback_basis_present=fallback_basis_present,
        lexicon_basis_missing_or_capped=lexicon_basis_missing_or_capped,
        no_strong_lexical_basis_from_upstream=no_strong_lexical_basis_from_upstream,
        lexicon_handoff_missing_upstream=lexicon_handoff_missing_upstream,
    )
    gate = evaluate_dictum_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                lexical_bundle.source_syntax_ref,
                syntax_set.source_surface_ref,
                *lexical_lineage,
                *syntax_lineage,
            )
        )
    )
    telemetry = build_dictum_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_construction_paths=ATTEMPTED_CONSTRUCTION_PATHS,
        downstream_gate=gate,
        causal_basis="L03 lexical/reference candidates + L02 syntax hypotheses -> proposition-like dictum skeletons",
    )
    confidence = _estimate_result_confidence(bundle)
    partial_known = bool(
        bundle.ambiguities
        or bundle.conflicts
        or bundle.unknowns
        or any(candidate.underspecified_slots for candidate in bundle.dictum_candidates)
    )
    partial_known_reason = (
        "; ".join(telemetry.ambiguity_reasons)
        if telemetry.ambiguity_reasons
        else None
    )
    abstain = not gate.accepted
    abstain_reason = None if gate.accepted else gate.reason

    return DictumCandidateResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_final_resolution_performed=True,
    )


def dictum_result_to_payload(result: DictumCandidateResult) -> dict[str, object]:
    return dictum_result_snapshot(result)


def persist_dictum_result_via_f01(
    *,
    result: DictumCandidateResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("l04-dictum-candidates",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"dictum-step-{transition_id}",
            "dictum_snapshot": dictum_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_lexical_input(
    lexical_grounding_result_or_bundle: LexicalGroundingResult | LexicalGroundingBundle,
) -> tuple[LexicalGroundingBundle, tuple[str, ...]]:
    if isinstance(lexical_grounding_result_or_bundle, LexicalGroundingResult):
        return lexical_grounding_result_or_bundle.bundle, lexical_grounding_result_or_bundle.telemetry.source_lineage
    if isinstance(lexical_grounding_result_or_bundle, LexicalGroundingBundle):
        return lexical_grounding_result_or_bundle, ()
    raise TypeError(
        "build_dictum_candidates requires LexicalGroundingResult or LexicalGroundingBundle"
    )


def _extract_syntax_input(
    syntax_hypothesis_result_or_set: SyntaxHypothesisResult | SyntaxHypothesisSet,
) -> tuple[SyntaxHypothesisSet, tuple[str, ...]]:
    if isinstance(syntax_hypothesis_result_or_set, SyntaxHypothesisResult):
        return syntax_hypothesis_result_or_set.hypothesis_set, syntax_hypothesis_result_or_set.telemetry.source_lineage
    if isinstance(syntax_hypothesis_result_or_set, SyntaxHypothesisSet):
        return syntax_hypothesis_result_or_set, ()
    raise TypeError(
        "build_dictum_candidates requires SyntaxHypothesisResult or SyntaxHypothesisSet"
    )


def _extract_optional_surface(
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult | None,
) -> UtteranceSurface | None:
    if utterance_surface is None:
        return None
    if isinstance(utterance_surface, UtteranceSurface):
        return utterance_surface
    if isinstance(utterance_surface, UtteranceSurfaceResult):
        return utterance_surface.surface
    raise TypeError("utterance_surface must be UtteranceSurface or UtteranceSurfaceResult when provided")


def _argument_tokens_for_predicate(
    *,
    hypothesis,
    clause_token_ids: tuple[str, ...],
    predicate_token_id: str,
    token_feature_by_id,
) -> tuple[str, ...]:
    tokens: list[str] = []
    for edge in hypothesis.edges:
        if edge.head_token_id == predicate_token_id and edge.dependent_token_id in clause_token_ids:
            if edge.dependent_token_id != predicate_token_id:
                tokens.append(edge.dependent_token_id)
        if edge.dependent_token_id == predicate_token_id and edge.head_token_id in clause_token_ids:
            if edge.head_token_id != predicate_token_id:
                tokens.append(edge.head_token_id)

    if not tokens:
        clause_lexical = [
            token_id
            for token_id in clause_token_ids
            if token_id in token_feature_by_id
            and token_feature_by_id[token_id].coarse_pos
            not in {MorphPos.PUNCTUATION, MorphPos.QUOTE, MorphPos.CONJUNCTION}
            and token_id != predicate_token_id
        ]
        tokens.extend(clause_lexical[:2])

    unique = []
    seen = set()
    for token_id in tokens:
        if token_id in seen:
            continue
        seen.add(token_id)
        unique.append(token_id)
    unique.sort(key=lambda token_id: token_feature_by_id[token_id].raw_span.start)
    return tuple(unique)


def _role_label(token_start: int, predicate_start: int, slot_idx: int) -> str:
    if token_start < predicate_start:
        return "agent_like"
    if slot_idx == 1:
        return "patient_like"
    return f"arg_{slot_idx}"


def _temporal_markers_for_clause(
    *,
    candidate_id: str,
    clause_token_ids: tuple[str, ...],
    token_feature_by_id,
    deixis_by_token,
    context_ref: str,
) -> tuple[TemporalMarker, ...]:
    kinds: list[TemporalAnchorKind] = []
    token_ids: list[str] = []
    for token_id in clause_token_ids:
        if token_id not in token_feature_by_id:
            continue
        lower = token_feature_by_id[token_id].raw_span.raw_text.lower()
        if lower in TEMPORAL_PAST:
            kinds.append(TemporalAnchorKind.PAST)
            token_ids.append(token_id)
        elif lower in TEMPORAL_PRESENT:
            kinds.append(TemporalAnchorKind.PRESENT)
            token_ids.append(token_id)
        elif lower in TEMPORAL_FUTURE:
            kinds.append(TemporalAnchorKind.FUTURE)
            token_ids.append(token_id)

    if kinds:
        unique_kinds = tuple(dict.fromkeys(kinds))
        markers = []
        for idx, kind in enumerate(unique_kinds, start=1):
            markers.append(
                TemporalMarker(
                    temporal_marker_id=f"temp-{candidate_id}-{idx}",
                    anchor_kind=kind,
                    token_ids=tuple(token_ids),
                    unresolved=False,
                    confidence=0.62,
                    reason="temporal anchor derived from lexical temporal cue",
                )
            )
        return tuple(markers)

    for token_id in clause_token_ids:
        rows = deixis_by_token.get(token_id, [])
        for _, unresolved, kind in rows:
            if kind != DeixisKind.TIME:
                continue
            return (
                TemporalMarker(
                    temporal_marker_id=f"temp-{candidate_id}-ctx",
                    anchor_kind=TemporalAnchorKind.UNRESOLVED if unresolved else TemporalAnchorKind.CONTEXTUAL,
                    token_ids=(token_id,),
                    unresolved=unresolved,
                    confidence=0.39 if unresolved else 0.56,
                    reason=(
                        "temporal anchor unresolved from deictic time carrier"
                        if unresolved
                        else f"contextual temporal anchor from deictic carrier ({context_ref})"
                    ),
                ),
            )

    return (
        TemporalMarker(
            temporal_marker_id=f"temp-{candidate_id}-unspecified",
            anchor_kind=TemporalAnchorKind.UNSPECIFIED,
            token_ids=(),
            unresolved=False,
            confidence=0.31,
            reason="no explicit temporal anchor detected",
        ),
    )


def _magnitude_markers_for_clause(
    *,
    candidate_id: str,
    clause_token_ids: tuple[str, ...],
    token_feature_by_id,
) -> tuple[MagnitudeMarker, ...]:
    markers: list[MagnitudeMarker] = []
    idx = 0
    for token_id in clause_token_ids:
        if token_id not in token_feature_by_id:
            continue
        lower = token_feature_by_id[token_id].raw_span.raw_text.lower()
        if lower in MAGNITUDE_HIGH:
            idx += 1
            markers.append(
                MagnitudeMarker(
                    magnitude_marker_id=f"mag-{candidate_id}-{idx}",
                    marker_kind="intensity_high",
                    token_ids=(token_id,),
                    value_hint="high",
                    unresolved=False,
                    confidence=0.57,
                    reason="intensity cue from lexical marker",
                )
            )
        elif lower in MAGNITUDE_LOW:
            idx += 1
            markers.append(
                MagnitudeMarker(
                    magnitude_marker_id=f"mag-{candidate_id}-{idx}",
                    marker_kind="intensity_low",
                    token_ids=(token_id,),
                    value_hint="low",
                    unresolved=False,
                    confidence=0.57,
                    reason="intensity cue from lexical marker",
                )
            )
        elif re.fullmatch(r"\d+", lower):
            idx += 1
            markers.append(
                MagnitudeMarker(
                    magnitude_marker_id=f"mag-{candidate_id}-{idx}",
                    marker_kind="quantifier_numeric",
                    token_ids=(token_id,),
                    value_hint=lower,
                    unresolved=False,
                    confidence=0.68,
                    reason="numeric quantity cue from token surface",
                )
            )
    return tuple(markers)


def _estimate_candidate_confidence(
    *,
    predicate_fallback: bool,
    underspecified_count: int,
    scope_ambiguity_count: int,
    quotation_sensitive: bool,
) -> float:
    score = 0.82
    if predicate_fallback:
        score -= 0.13
    score -= min(0.38, underspecified_count * 0.08)
    score -= min(0.22, scope_ambiguity_count * 0.09)
    if quotation_sensitive:
        score -= 0.05
    return max(0.1, min(0.94, round(score, 4)))


def _estimate_result_confidence(bundle: DictumCandidateBundle) -> float:
    if not bundle.dictum_candidates:
        return 0.1
    scores = [candidate.confidence for candidate in bundle.dictum_candidates]
    value = sum(scores) / len(scores)
    value -= min(0.25, len(bundle.conflicts) * 0.06)
    value -= min(0.2, len(bundle.unknowns) * 0.04)
    return max(0.1, min(0.95, round(value, 4)))


def _abstain_result(
    *,
    lexical_bundle: LexicalGroundingBundle,
    syntax_set: SyntaxHypothesisSet,
    source_lineage: tuple[str, ...],
    reason: str,
) -> DictumCandidateResult:
    bundle = DictumCandidateBundle(
        source_lexical_grounding_ref=lexical_bundle.source_syntax_ref,
        source_syntax_ref=syntax_set.source_surface_ref,
        source_surface_ref=lexical_bundle.source_surface_ref,
        linked_syntax_hypothesis_ids=tuple(hypothesis.hypothesis_id for hypothesis in syntax_set.hypotheses),
        linked_lexical_candidate_ids=tuple(
            dict.fromkeys(candidate.candidate_id for candidate in lexical_bundle.lexeme_candidates)
        ),
        dictum_candidates=(),
        ambiguities=(),
        conflicts=(),
        unknowns=(
            DictumUnknown(
                unknown_id="d-unknown-abstain",
                dictum_candidate_ref=None,
                reason=reason,
                source_ref_ids=(lexical_bundle.source_syntax_ref, syntax_set.source_surface_ref),
                confidence=0.2,
            ),
        ),
        blocked_candidate_reasons=(reason,),
        no_final_resolution_performed=True,
        reason="dictum construction abstained due to invalid or empty upstream contract",
        input_lexical_basis_classes=tuple(
            dict.fromkeys(
                basis.basis_class.value for basis in lexical_bundle.lexical_basis_records
            )
        ),
        fallback_basis_present=lexical_bundle.heuristic_fallback_used,
        lexicon_basis_missing_or_capped=(
            lexical_bundle.lexicon_handoff_missing
            or any(
                basis.basis_class.value in {"lexicon_capped_unknown", "no_usable_lexical_basis"}
                for basis in lexical_bundle.lexical_basis_records
            )
        ),
        no_strong_lexical_basis_from_upstream=(
            lexical_bundle.no_strong_lexical_claim_from_fallback
            or lexical_bundle.no_strong_lexical_claim_without_lexicon
        ),
        lexicon_handoff_missing_upstream=lexical_bundle.lexicon_handoff_missing,
    )
    gate = evaluate_dictum_downstream_gate(bundle)
    telemetry = build_dictum_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_construction_paths=ATTEMPTED_CONSTRUCTION_PATHS,
        downstream_gate=gate,
        causal_basis="invalid upstream typed contract -> abstain",
    )
    return DictumCandidateResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.1,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_resolution_performed=True,
    )
