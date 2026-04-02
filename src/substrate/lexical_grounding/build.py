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
from substrate.language_surface.models import UtteranceSurface, UtteranceSurfaceResult
from substrate.lexical_grounding.models import (
    DeixisCandidate,
    DeixisKind,
    EntityCandidate,
    GroundingConflict,
    GroundingUnknownState,
    LexemeCandidate,
    LexicalCandidateType,
    LexicalDiscourseContext,
    LexicalGroundingBundle,
    LexicalGroundingResult,
    MentionAnchor,
    ReferenceHypothesis,
    ReferenceKind,
    SenseCandidate,
)
from substrate.lexical_grounding.policy import evaluate_lexical_grounding_downstream_gate
from substrate.lexical_grounding.telemetry import (
    build_lexical_grounding_telemetry,
    lexical_grounding_result_snapshot,
)
from substrate.morphosyntax.models import (
    MorphPos,
    SyntaxHypothesisResult,
    SyntaxHypothesisSet,
)
from substrate.transition import execute_transition


AMBIGUOUS_SENSES: dict[str, tuple[str, str]] = {
    "bank": ("sense:financial_institution", "sense:river_edge"),
    "замок": ("sense:castle", "sense:lock_device"),
    "ключ": ("sense:key_tool", "sense:spring_source"),
    "light": ("sense:illumination", "sense:low_weight"),
    "charge": ("sense:electrical_charge", "sense:accusation"),
    "это": ("sense:demonstrative", "sense:placeholder_reference"),
}

PRONOUN_FORMS = {
    "i",
    "you",
    "he",
    "she",
    "it",
    "we",
    "they",
    "я",
    "ты",
    "он",
    "она",
    "оно",
    "мы",
    "вы",
    "они",
}

DEIXIS_FORMS: dict[str, DeixisKind] = {
    "i": DeixisKind.SPEAKER,
    "я": DeixisKind.SPEAKER,
    "you": DeixisKind.ADDRESSEE,
    "ты": DeixisKind.ADDRESSEE,
    "вы": DeixisKind.ADDRESSEE,
    "here": DeixisKind.LOCATION,
    "there": DeixisKind.LOCATION,
    "здесь": DeixisKind.LOCATION,
    "тут": DeixisKind.LOCATION,
    "now": DeixisKind.TIME,
    "сейчас": DeixisKind.TIME,
    "this": DeixisKind.OBJECT,
    "that": DeixisKind.OBJECT,
    "это": DeixisKind.OBJECT,
}

ATTEMPTED_GROUNDING_PATHS: tuple[str, ...] = (
    "lexical_grounding.validate_typed_input",
    "lexical_grounding.mention_anchor_derivation",
    "lexical_grounding.sense_candidate_generation",
    "lexical_grounding.entity_candidate_generation",
    "lexical_grounding.reference_hypothesis_generation",
    "lexical_grounding.deixis_candidate_generation",
    "lexical_grounding.unknown_and_conflict_marking",
    "lexical_grounding.downstream_gate",
)


def build_lexical_grounding_hypotheses(
    syntax_hypothesis_result_or_set: SyntaxHypothesisResult | SyntaxHypothesisSet,
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult | None = None,
    discourse_context: LexicalDiscourseContext | None = None,
) -> LexicalGroundingResult:
    hypothesis_set, syntax_lineage = _extract_syntax_input(syntax_hypothesis_result_or_set)
    surface = _extract_optional_surface(utterance_surface)
    context = discourse_context or LexicalDiscourseContext()
    if discourse_context is not None and not isinstance(discourse_context, LexicalDiscourseContext):
        raise TypeError("discourse_context must be LexicalDiscourseContext")

    if not hypothesis_set.hypotheses:
        return _abstain_result(
            syntax_ref=hypothesis_set.source_surface_ref,
            surface_ref=surface.epistemic_unit_ref if surface else None,
            source_lineage=syntax_lineage,
            reason="syntax hypothesis set is empty",
        )

    primary_hypothesis = hypothesis_set.hypotheses[0]
    mentions = _derive_mentions(primary_hypothesis, surface_ref=surface.epistemic_unit_ref if surface else None)
    if not mentions:
        return _abstain_result(
            syntax_ref=hypothesis_set.source_surface_ref,
            surface_ref=surface.epistemic_unit_ref if surface else None,
            source_lineage=syntax_lineage,
            reason="no lexical mention anchors derived from syntax",
        )

    context_entity_map = {key.lower(): ref for key, ref in context.entity_bindings}
    indexical_map = {key.lower(): ref for key, ref in context.indexical_bindings}
    discourse_context_keys_used: set[str] = set()

    candidate_counter = 0
    reference_counter = 0
    unknown_counter = 0
    conflict_counter = 0

    lexeme_candidates: list[LexemeCandidate] = []
    sense_candidates: list[SenseCandidate] = []
    entity_candidates: list[EntityCandidate] = []
    reference_hypotheses: list[ReferenceHypothesis] = []
    deixis_candidates: list[DeixisCandidate] = []
    unknown_states: list[GroundingUnknownState] = []
    conflicts: list[GroundingConflict] = []
    blocked_reasons: list[str] = []
    ambiguity_reasons: list[str] = []

    prior_entity_refs: list[str] = []
    mention_text_by_id: dict[str, str] = {}
    entity_candidates_by_mention: dict[str, list[EntityCandidate]] = defaultdict(list)

    for mention in mentions:
        token_lower = mention.normalized_text.lower()
        mention_text_by_id[mention.mention_id] = token_lower
        prior_entity_refs_before_mention = tuple(prior_entity_refs)

        candidate_counter, local_sense_candidates, local_unknown = _sense_candidates_for_mention(
            mention=mention,
            token_lower=token_lower,
            candidate_counter=candidate_counter,
        )
        sense_candidates.extend(local_sense_candidates)
        if local_unknown is not None:
            unknown_counter += 1
            unknown_states.append(
                GroundingUnknownState(
                    unknown_id=f"unknown-{unknown_counter}",
                    mention_id=mention.mention_id,
                    token_id=mention.token_id,
                    reason=local_unknown,
                    confidence=0.2,
                )
            )
            ambiguity_reasons.append(local_unknown)
            blocked_reasons.append(local_unknown)

        for candidate in local_sense_candidates:
            lexeme_candidates.append(
                LexemeCandidate(
                    candidate_id=candidate.candidate_id,
                    mention_id=candidate.mention_id,
                    token_id=candidate.token_id,
                    candidate_type=LexicalCandidateType.SENSE,
                    label=candidate.sense_key,
                    confidence=candidate.confidence,
                    entropy=candidate.entropy,
                    evidence=candidate.evidence,
                    discourse_context_ref=context.context_ref if context.context_ref else None,
                )
            )

        candidate_counter, local_entity_candidates = _entity_candidates_for_mention(
            mention=mention,
            token_lower=token_lower,
            context_entity_map=context_entity_map,
            candidate_counter=candidate_counter,
            context_ref=context.context_ref,
        )
        entity_candidates.extend(local_entity_candidates)
        entity_candidates_by_mention[mention.mention_id].extend(local_entity_candidates)
        for candidate in local_entity_candidates:
            lexeme_candidates.append(
                LexemeCandidate(
                    candidate_id=candidate.candidate_id,
                    mention_id=candidate.mention_id,
                    token_id=candidate.token_id,
                    candidate_type=LexicalCandidateType.ENTITY,
                    label=candidate.entity_ref,
                    confidence=candidate.confidence,
                    entropy=0.25 if candidate.confidence >= 0.75 else 0.45,
                    evidence=candidate.evidence,
                    discourse_context_ref=candidate.discourse_context_ref,
                )
            )
            prior_entity_refs.append(candidate.entity_ref)
            if candidate.discourse_context_ref:
                discourse_context_keys_used.add(candidate.discourse_context_ref)

        reference_counter, local_reference, reference_blocked = _reference_hypotheses_for_mention(
            mention=mention,
            token_lower=token_lower,
            context_entity_map=context_entity_map,
            prior_entity_refs=prior_entity_refs_before_mention,
            reference_counter=reference_counter,
            context_ref=context.context_ref,
        )
        reference_hypotheses.extend(local_reference)
        if reference_blocked:
            blocked_reasons.append(reference_blocked)
            ambiguity_reasons.append(reference_blocked)

        reference_counter, local_deixis, deixis_blocked = _deixis_candidates_for_mention(
            mention=mention,
            token_lower=token_lower,
            indexical_map=indexical_map,
            reference_counter=reference_counter,
            context_ref=context.context_ref,
        )
        deixis_candidates.extend(local_deixis)
        if deixis_blocked:
            blocked_reasons.append(deixis_blocked)
            ambiguity_reasons.append(deixis_blocked)
        if local_deixis and context.context_ref:
            discourse_context_keys_used.add(context.context_ref)

    for mention in mentions:
        sense_for_mention = [
            candidate for candidate in sense_candidates if candidate.mention_id == mention.mention_id
        ]
        if len(sense_for_mention) >= 2 and abs(sense_for_mention[0].confidence - sense_for_mention[1].confidence) <= 0.1:
            conflict_counter += 1
            conflicts.append(
                GroundingConflict(
                    conflict_id=f"conflict-{conflict_counter}",
                    mention_id=mention.mention_id,
                    candidate_ids=tuple(candidate.candidate_id for candidate in sense_for_mention[:2]),
                    reason="multiple near-equal lexical senses",
                    confidence=0.58,
                )
            )
            ambiguity_reasons.append("multiple near-equal lexical senses")

        refs_for_mention = [
            hypothesis
            for hypothesis in reference_hypotheses
            if hypothesis.mention_id == mention.mention_id
        ]
        if any(hypothesis.unresolved for hypothesis in refs_for_mention):
            ambiguity_reasons.append("reference unresolved")

    for hypothesis in reference_hypotheses:
        if hypothesis.reference_kind == ReferenceKind.DISCOURSE_LINK:
            continue
        if hypothesis.unresolved and not any(
            unknown.mention_id == hypothesis.mention_id for unknown in unknown_states
        ):
            unknown_counter += 1
            unknown_states.append(
                GroundingUnknownState(
                    unknown_id=f"unknown-{unknown_counter}",
                    mention_id=hypothesis.mention_id,
                    token_id=hypothesis.token_id,
                    reason="reference hypothesis unresolved under weak discourse evidence",
                    confidence=0.25,
                )
            )

    bundle = LexicalGroundingBundle(
        source_syntax_ref=hypothesis_set.source_surface_ref,
        source_surface_ref=surface.epistemic_unit_ref if surface else None,
        linked_hypothesis_ids=tuple(hypothesis.hypothesis_id for hypothesis in hypothesis_set.hypotheses),
        mention_anchors=mentions,
        lexeme_candidates=tuple(lexeme_candidates),
        sense_candidates=tuple(sense_candidates),
        entity_candidates=tuple(entity_candidates),
        reference_hypotheses=tuple(reference_hypotheses),
        deixis_candidates=tuple(deixis_candidates),
        unknown_states=tuple(unknown_states),
        conflicts=tuple(conflicts),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        no_final_resolution_performed=True,
        reason="candidate lexical and referential grounding generated without final discourse acceptance",
    )
    gate = evaluate_lexical_grounding_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                *syntax_lineage,
                bundle.source_syntax_ref,
                *(tuple(mention.surface_text for mention in mentions[:1]) if mentions else ()),
            )
        )
    )
    telemetry = build_lexical_grounding_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        discourse_context_keys_used=tuple(sorted(discourse_context_keys_used)),
        attempted_grounding_paths=ATTEMPTED_GROUNDING_PATHS,
        blocked_grounding_reasons=tuple(dict.fromkeys(blocked_reasons)),
        downstream_gate=gate,
        causal_basis="L02 morphosyntax anchors transformed into lexical/reference candidate hypotheses",
    )
    confidence = _estimate_result_confidence(bundle)
    partial_known = bool(bundle.unknown_states or bundle.conflicts or any(h.unresolved for h in bundle.reference_hypotheses))
    partial_known_reason = (
        "; ".join(bundle.ambiguity_reasons)
        if bundle.ambiguity_reasons
        else None
    )
    abstain = not gate.accepted
    abstain_reason = None if gate.accepted else gate.reason

    return LexicalGroundingResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_final_resolution_performed=True,
    )


def lexical_grounding_result_to_payload(result: LexicalGroundingResult) -> dict[str, object]:
    return lexical_grounding_result_snapshot(result)


def persist_lexical_grounding_result_via_f01(
    *,
    result: LexicalGroundingResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("l03-lexical-grounding",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"lexical-grounding-step-{transition_id}",
            "lexical_grounding_snapshot": lexical_grounding_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_syntax_input(
    syntax_hypothesis_result_or_set: SyntaxHypothesisResult | SyntaxHypothesisSet,
) -> tuple[SyntaxHypothesisSet, tuple[str, ...]]:
    if isinstance(syntax_hypothesis_result_or_set, SyntaxHypothesisResult):
        return (
            syntax_hypothesis_result_or_set.hypothesis_set,
            syntax_hypothesis_result_or_set.telemetry.source_lineage,
        )
    if isinstance(syntax_hypothesis_result_or_set, SyntaxHypothesisSet):
        return syntax_hypothesis_result_or_set, ()
    raise TypeError(
        "build_lexical_grounding_hypotheses requires SyntaxHypothesisResult or SyntaxHypothesisSet"
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


def _derive_mentions(primary_hypothesis, *, surface_ref: str | None) -> tuple[MentionAnchor, ...]:
    mention_anchors: list[MentionAnchor] = []
    mention_index = 0
    for token_feature in primary_hypothesis.token_features:
        if token_feature.coarse_pos in {MorphPos.PUNCTUATION, MorphPos.QUOTE}:
            continue
        mention_index += 1
        mention_anchors.append(
            MentionAnchor(
                mention_id=f"mention-{mention_index}",
                token_id=token_feature.token_id,
                raw_span=token_feature.raw_span,
                surface_text=token_feature.raw_span.raw_text,
                normalized_text=token_feature.raw_span.raw_text.strip(),
                syntax_hypothesis_ref=primary_hypothesis.hypothesis_id,
                confidence=token_feature.confidence,
            )
        )
    _ = surface_ref
    return tuple(mention_anchors)


def _sense_candidates_for_mention(
    *,
    mention: MentionAnchor,
    token_lower: str,
    candidate_counter: int,
) -> tuple[int, list[SenseCandidate], str | None]:
    candidates: list[SenseCandidate] = []
    unknown_reason: str | None = None
    if token_lower in AMBIGUOUS_SENSES:
        first, second = AMBIGUOUS_SENSES[token_lower]
        candidate_counter += 1
        candidates.append(
            SenseCandidate(
                candidate_id=f"sense-{candidate_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                sense_key=first,
                confidence=0.52,
                entropy=0.91,
                evidence="lexeme appears in predefined ambiguity bundle",
            )
        )
        candidate_counter += 1
        candidates.append(
            SenseCandidate(
                candidate_id=f"sense-{candidate_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                sense_key=second,
                confidence=0.48,
                entropy=0.91,
                evidence="lexeme appears in predefined ambiguity bundle",
            )
        )
        return candidate_counter, candidates, None

    if _looks_unknown_lexeme(token_lower):
        candidate_counter += 1
        candidates.append(
            SenseCandidate(
                candidate_id=f"sense-{candidate_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                sense_key="sense:unknown_lexeme",
                confidence=0.2,
                entropy=0.99,
                evidence="nonce or unsupported lexical form",
            )
        )
        unknown_reason = "unknown lexical item without stable sense grounding"
        return candidate_counter, candidates, unknown_reason

    candidate_counter += 1
    candidates.append(
        SenseCandidate(
            candidate_id=f"sense-{candidate_counter}",
            mention_id=mention.mention_id,
            token_id=mention.token_id,
            sense_key=f"sense:surface::{token_lower}",
            confidence=0.74,
            entropy=0.24,
            evidence="single shallow lexical reading from normalized form",
        )
    )
    return candidate_counter, candidates, None


def _entity_candidates_for_mention(
    *,
    mention: MentionAnchor,
    token_lower: str,
    context_entity_map: dict[str, str],
    candidate_counter: int,
    context_ref: str,
) -> tuple[int, list[EntityCandidate]]:
    candidates: list[EntityCandidate] = []

    if token_lower in context_entity_map:
        candidate_counter += 1
        candidates.append(
            EntityCandidate(
                candidate_id=f"entity-{candidate_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                entity_ref=context_entity_map[token_lower],
                entity_type="discourse_bound_entity",
                confidence=0.82,
                evidence="matched discourse context binding by normalized mention text",
                discourse_context_ref=context_ref,
            )
        )
        return candidate_counter, candidates

    looks_capitalized = bool(mention.surface_text[:1]) and mention.surface_text[:1].isupper()
    if looks_capitalized:
        candidate_counter += 1
        candidates.append(
            EntityCandidate(
                candidate_id=f"entity-{candidate_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                entity_ref=f"entity:named::{mention.surface_text}",
                entity_type="named_entity",
                confidence=0.58,
                evidence="surface capitalization supports possible named entity grounding",
                discourse_context_ref=context_ref,
            )
        )
        candidate_counter += 1
        candidates.append(
            EntityCandidate(
                candidate_id=f"entity-{candidate_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                entity_ref=f"entity:common::{token_lower}",
                entity_type="common_mention",
                confidence=0.46,
                evidence="capitalization alone is insufficient for final named-entity commitment",
                discourse_context_ref=context_ref,
            )
        )
        return candidate_counter, candidates

    candidate_counter += 1
    candidates.append(
        EntityCandidate(
            candidate_id=f"entity-{candidate_counter}",
            mention_id=mention.mention_id,
            token_id=mention.token_id,
            entity_ref=f"entity:surface::{token_lower}",
            entity_type="surface_linked_mention",
            confidence=0.44,
            evidence="fallback mention-level entity candidate without discourse confirmation",
            discourse_context_ref=context_ref,
        )
    )
    return candidate_counter, candidates


def _reference_hypotheses_for_mention(
    *,
    mention: MentionAnchor,
    token_lower: str,
    context_entity_map: dict[str, str],
    prior_entity_refs: tuple[str, ...],
    reference_counter: int,
    context_ref: str,
) -> tuple[int, list[ReferenceHypothesis], str | None]:
    hypotheses: list[ReferenceHypothesis] = []
    blocked_reason: str | None = None

    if token_lower in PRONOUN_FORMS:
        candidate_refs: list[str] = []
        if token_lower in context_entity_map:
            candidate_refs.append(context_entity_map[token_lower])
        candidate_refs.extend(ref for ref in prior_entity_refs[-2:] if ref not in candidate_refs)
        unresolved = len(candidate_refs) == 0
        reference_counter += 1
        hypotheses.append(
            ReferenceHypothesis(
                reference_id=f"ref-{reference_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                reference_kind=ReferenceKind.PRONOUN,
                candidate_ref_ids=tuple(candidate_refs),
                confidence=0.6 if len(candidate_refs) == 1 else (0.45 if candidate_refs else 0.2),
                unresolved=unresolved,
                evidence="pronoun reference candidates from discourse binding and local antecedent window",
                discourse_context_ref=context_ref,
            )
        )
        if unresolved:
            blocked_reason = "pronoun reference unresolved due to missing discourse antecedent"
        return reference_counter, hypotheses, blocked_reason

    if token_lower in context_entity_map:
        reference_counter += 1
        hypotheses.append(
            ReferenceHypothesis(
                reference_id=f"ref-{reference_counter}",
                mention_id=mention.mention_id,
                token_id=mention.token_id,
                reference_kind=ReferenceKind.DISCOURSE_LINK,
                candidate_ref_ids=(context_entity_map[token_lower],),
                confidence=0.8,
                unresolved=False,
                evidence="direct discourse link candidate from context mention map",
                discourse_context_ref=context_ref,
            )
        )
    return reference_counter, hypotheses, blocked_reason


def _deixis_candidates_for_mention(
    *,
    mention: MentionAnchor,
    token_lower: str,
    indexical_map: dict[str, str],
    reference_counter: int,
    context_ref: str,
) -> tuple[int, list[DeixisCandidate], str | None]:
    candidates: list[DeixisCandidate] = []
    blocked_reason: str | None = None
    if token_lower not in DEIXIS_FORMS:
        return reference_counter, candidates, blocked_reason

    kind = DEIXIS_FORMS[token_lower]
    key = {
        DeixisKind.SPEAKER: "speaker",
        DeixisKind.ADDRESSEE: "addressee",
        DeixisKind.LOCATION: "location",
        DeixisKind.TIME: "time",
        DeixisKind.OBJECT: "object",
        DeixisKind.UNKNOWN: "unknown",
    }[kind]
    target_ref = indexical_map.get(key)
    unresolved = target_ref is None
    reference_counter += 1
    candidates.append(
        DeixisCandidate(
            candidate_id=f"deixis-{reference_counter}",
            mention_id=mention.mention_id,
            token_id=mention.token_id,
            deixis_kind=kind,
            target_ref=target_ref,
            confidence=0.78 if target_ref else 0.26,
            unresolved=unresolved,
            evidence="deixis candidate from indexical form and discourse indexical bindings",
            discourse_context_ref=context_ref,
        )
    )
    if unresolved:
        blocked_reason = "indexical/deictic target unresolved due to missing discourse context key"
    return reference_counter, candidates, blocked_reason


def _estimate_result_confidence(bundle: LexicalGroundingBundle) -> float:
    if not bundle.mention_anchors:
        return 0.1
    confidence_values = [
        candidate.confidence for candidate in bundle.lexeme_candidates
    ] + [hypothesis.confidence for hypothesis in bundle.reference_hypotheses]
    if not confidence_values:
        return 0.2
    score = sum(confidence_values) / len(confidence_values)
    score -= min(0.4, len(bundle.unknown_states) * 0.07)
    score -= min(0.25, len(bundle.conflicts) * 0.06)
    return max(0.1, min(0.95, round(score, 4)))


def _looks_unknown_lexeme(token_lower: str) -> bool:
    if not token_lower:
        return True
    if re.fullmatch(r"[a-z]{4,}", token_lower) and not re.search(r"[aeiouy]", token_lower):
        return True
    has_cyr = any("а" <= ch <= "я" or ch == "ё" for ch in token_lower)
    has_lat = any("a" <= ch <= "z" for ch in token_lower)
    if has_cyr and has_lat:
        return True
    if re.fullmatch(r"[a-z]{6,}", token_lower) and token_lower in {"qzxv", "nrmpt", "blarf", "zint", "glorf", "wint"}:
        return True
    return False


def _abstain_result(
    *,
    syntax_ref: str,
    surface_ref: str | None,
    source_lineage: tuple[str, ...],
    reason: str,
) -> LexicalGroundingResult:
    bundle = LexicalGroundingBundle(
        source_syntax_ref=syntax_ref,
        source_surface_ref=surface_ref,
        linked_hypothesis_ids=(),
        mention_anchors=(),
        lexeme_candidates=(),
        sense_candidates=(),
        entity_candidates=(),
        reference_hypotheses=(),
        deixis_candidates=(),
        unknown_states=(),
        conflicts=(),
        ambiguity_reasons=(reason,),
        no_final_resolution_performed=True,
        reason="lexical grounding abstained due to invalid or empty upstream contract",
    )
    gate = evaluate_lexical_grounding_downstream_gate(bundle)
    telemetry = build_lexical_grounding_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        discourse_context_keys_used=(),
        attempted_grounding_paths=ATTEMPTED_GROUNDING_PATHS,
        blocked_grounding_reasons=(reason,),
        downstream_gate=gate,
        causal_basis="invalid or empty L02 input -> abstain",
    )
    return LexicalGroundingResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.1,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_resolution_performed=True,
    )
