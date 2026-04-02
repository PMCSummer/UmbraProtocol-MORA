from __future__ import annotations

from dataclasses import dataclass

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.language_surface.models import (
    SegmentKind,
    TokenKind,
    UtteranceSurface,
    UtteranceSurfaceResult,
)
from substrate.morphosyntax.models import (
    AgreementStatus,
    ClauseBoundaryKind,
    ClauseGraph,
    ClauseNode,
    MorphAgreementCue,
    MorphNumber,
    MorphPos,
    MorphTokenFeatures,
    SyntaxDownstreamGateDecision,
    SyntaxEdge,
    SyntaxHypothesis,
    SyntaxHypothesisResult,
    SyntaxHypothesisSet,
    UnresolvedAttachment,
)
from substrate.morphosyntax.policy import evaluate_morphosyntax_downstream_gate
from substrate.morphosyntax.telemetry import build_syntax_telemetry, syntax_result_snapshot
from substrate.transition import execute_transition


NEGATION_FORMS = {"не", "ни", "no", "not", "n't"}
PRONOUN_SINGULAR = {"i", "he", "she", "it", "я", "он", "она", "оно", "ты"}
PRONOUN_PLURAL = {"we", "they", "мы", "они", "вы"}
CONJ_FORMS = {"and", "or", "but", "и", "или", "но"}
ATTEMPTED_MORPHOSYNTAX_PATHS: tuple[str, ...] = (
    "morphosyntax.validate_surface_input",
    "morphosyntax.morph_feature_derivation",
    "morphosyntax.clause_graph_derivation",
    "morphosyntax.dependency_candidate_generation",
    "morphosyntax.agreement_cue_derivation",
    "morphosyntax.unresolved_attachment_marking",
    "morphosyntax.nbest_hypothesis_emission",
    "morphosyntax.downstream_gate",
)


@dataclass(frozen=True, slots=True)
class MorphosyntaxBuildContext:
    source_lineage: tuple[str, ...] = ()
    require_multi_candidate_on_ambiguity: bool = True


def build_morphosyntax_candidate_space(
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult,
    context: MorphosyntaxBuildContext | None = None,
) -> SyntaxHypothesisResult:
    context = context or MorphosyntaxBuildContext()
    surface, upstream_lineage = _extract_surface_and_lineage(utterance_surface)
    valid_surface, invalid_reason = _validate_surface(surface)
    source_lineage = tuple(
        dict.fromkeys((surface.epistemic_unit_ref, *upstream_lineage, *context.source_lineage))
    )

    if not valid_surface:
        return _abstain_result(surface=surface, reason=invalid_reason, source_lineage=source_lineage)

    token_features = _derive_morph_token_features(surface)
    clause_graph = _derive_clause_graph(surface, token_features)
    base_edges = _derive_dependency_edges(surface, clause_graph, token_features)
    unresolved = _derive_unresolved_attachments(surface, token_features)
    agreement_cues = _derive_agreement_cues(clause_graph, token_features)

    ambiguity_reasons = tuple(
        dict.fromkeys(ambiguity.reason for ambiguity in surface.ambiguities)
    )
    base_conf = _estimate_hypothesis_confidence(
        unresolved_count=len(unresolved), ambiguity_count=len(surface.ambiguities)
    )
    base = SyntaxHypothesis(
        hypothesis_id="syn-h1",
        clause_graph=clause_graph,
        edges=base_edges,
        unresolved_attachments=unresolved,
        token_features=token_features,
        agreement_cues=agreement_cues,
        confidence=base_conf,
        reason="shallow dependency-like structure from L01 anchors",
    )

    hypotheses: list[SyntaxHypothesis] = [base]
    if context.require_multi_candidate_on_ambiguity and unresolved:
        alt = _derive_alternative_hypothesis(
            base=base,
            unresolved=unresolved,
        )
        hypotheses.append(alt)

    hypothesis_set = SyntaxHypothesisSet(
        source_surface_ref=surface.epistemic_unit_ref,
        hypotheses=tuple(hypotheses),
        ambiguity_present=bool(surface.ambiguities or unresolved),
        no_selected_winner=True,
        reason="candidate space emitted without hidden one-best selection",
    )
    _enforce_syntax_invariants(hypothesis_set)
    gate = evaluate_morphosyntax_downstream_gate(hypothesis_set)
    telemetry = build_syntax_telemetry(
        hypothesis_set=hypothesis_set,
        source_lineage=source_lineage,
        ambiguity_reasons=ambiguity_reasons,
        attempted_paths=ATTEMPTED_MORPHOSYNTAX_PATHS,
        downstream_gate=gate,
        causal_basis="L01 anchored surface -> inspectable morphosyntax candidate space",
    )

    confidence = round(
        max(hypothesis.confidence for hypothesis in hypothesis_set.hypotheses), 4
    )
    partial_known = bool(hypothesis_set.ambiguity_present or unresolved)
    partial_known_reason = (
        "; ".join(ambiguity_reasons)
        if ambiguity_reasons
        else ("unresolved attachments present" if unresolved else None)
    )
    abstain = not gate.accepted
    abstain_reason = None if gate.accepted else "empty or invalid morphosyntax candidate space"

    return SyntaxHypothesisResult(
        hypothesis_set=hypothesis_set,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
    )


def syntax_result_to_payload(result: SyntaxHypothesisResult) -> dict[str, object]:
    return syntax_result_snapshot(result)


def persist_syntax_result_via_f01(
    *,
    result: SyntaxHypothesisResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("l02-morphosyntax-build",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"morphosyntax-step-{transition_id}",
            "syntax_snapshot": syntax_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_surface_and_lineage(
    utterance_surface: UtteranceSurface | UtteranceSurfaceResult,
) -> tuple[UtteranceSurface, tuple[str, ...]]:
    if isinstance(utterance_surface, UtteranceSurface):
        return utterance_surface, ()
    if isinstance(utterance_surface, UtteranceSurfaceResult):
        return utterance_surface.surface, utterance_surface.telemetry.source_lineage
    raise TypeError(
        "build_morphosyntax_candidate_space requires UtteranceSurface or UtteranceSurfaceResult"
    )


def _validate_surface(surface: UtteranceSurface) -> tuple[bool, str]:
    if not surface.reversible_span_map_present:
        return False, "surface reversible span map is required for L02"
    if not surface.tokens:
        return False, "surface token anchors are required for L02"
    if not surface.segments:
        return False, "surface segment anchors are required for L02"
    if not surface.normalization_log:
        return False, "surface normalization log is required for L02"
    return True, ""


def _derive_morph_token_features(surface: UtteranceSurface) -> tuple[MorphTokenFeatures, ...]:
    features: list[MorphTokenFeatures] = []
    for token in surface.tokens:
        lower = token.normalized_text.lower()
        pos = _infer_pos(token_kind=token.token_kind, lower=lower)
        number = _infer_number(lower=lower, pos=pos)
        feature_map = (
            ("script", _script_kind(token.normalized_text)),
            ("is_upper", str(token.normalized_text.isupper())),
            ("has_hyphen", str("-" in token.normalized_text)),
            ("surface_token_kind", token.token_kind.value),
        )
        confidence = _feature_confidence(pos=pos, number=number, token_confidence=token.confidence)
        features.append(
            MorphTokenFeatures(
                token_id=token.token_id,
                raw_span=token.raw_span,
                coarse_pos=pos,
                number=number,
                feature_map=feature_map,
                confidence=confidence,
                provenance="derived from L01 token anchor and shallow form heuristics",
            )
        )
    return tuple(features)


def _derive_clause_graph(
    surface: UtteranceSurface, token_features: tuple[MorphTokenFeatures, ...]
) -> ClauseGraph:
    feature_map = {feature.token_id: feature for feature in token_features}
    clauses: list[ClauseNode] = []
    for index, segment in enumerate(surface.segments):
        negation_ids = tuple(
            token_id
            for token_id in segment.token_ids
            if token_id in feature_map
            and feature_map[token_id].coarse_pos == MorphPos.NEGATION_PARTICLE
        )
        clauses.append(
            ClauseNode(
                clause_id=f"clause-{index}",
                raw_span=segment.raw_span,
                token_ids=segment.token_ids,
                boundary_kind=_map_boundary_kind(segment.segment_kind),
                negation_carrier_ids=negation_ids,
                confidence=segment.confidence,
            )
        )
    inter_edges: list[tuple[str, str, str]] = []
    for idx in range(len(clauses) - 1):
        inter_edges.append((clauses[idx].clause_id, clauses[idx + 1].clause_id, "sequential"))
    confidence = round(sum(clause.confidence for clause in clauses) / max(1, len(clauses)), 4)
    return ClauseGraph(clauses=tuple(clauses), inter_clause_edges=tuple(inter_edges), confidence=confidence)


def _derive_dependency_edges(
    surface: UtteranceSurface,
    clause_graph: ClauseGraph,
    token_features: tuple[MorphTokenFeatures, ...],
) -> tuple[SyntaxEdge, ...]:
    feature_map = {feature.token_id: feature for feature in token_features}
    token_map = {token.token_id: token for token in surface.tokens}
    edges: list[SyntaxEdge] = []
    edge_index = 0

    for clause in clause_graph.clauses:
        lexical_ids = [
            token_id
            for token_id in clause.token_ids
            if token_id in feature_map
            and feature_map[token_id].coarse_pos
            in {
                MorphPos.WORD,
                MorphPos.VERB_LIKE,
                MorphPos.PRONOUN,
                MorphPos.NEGATION_PARTICLE,
                MorphPos.CODE,
            }
        ]
        for i in range(1, len(lexical_ids)):
            edge_index += 1
            head = lexical_ids[i - 1]
            dep = lexical_ids[i]
            relation = (
                "neg_modifier"
                if feature_map[head].coarse_pos == MorphPos.NEGATION_PARTICLE
                else "seq_attach"
            )
            confidence = 0.74 if relation == "neg_modifier" else 0.66
            edges.append(
                SyntaxEdge(
                    edge_id=f"edge-{edge_index}",
                    head_token_id=head,
                    dependent_token_id=dep,
                    relation=relation,
                    clause_id=clause.clause_id,
                    confidence=confidence,
                )
            )

        punctuation_ids = [
            token_id
            for token_id in clause.token_ids
            if token_id in token_map
            and token_map[token_id].token_kind in {TokenKind.PUNCTUATION, TokenKind.ELLIPSIS}
        ]
        attach_head = lexical_ids[-1] if lexical_ids else clause.token_ids[-1]
        for punct_id in punctuation_ids:
            edge_index += 1
            edges.append(
                SyntaxEdge(
                    edge_id=f"edge-{edge_index}",
                    head_token_id=attach_head,
                    dependent_token_id=punct_id,
                    relation="punct_attach",
                    clause_id=clause.clause_id,
                    confidence=0.83,
                )
            )
    return tuple(edges)


def _derive_unresolved_attachments(
    surface: UtteranceSurface,
    token_features: tuple[MorphTokenFeatures, ...],
) -> tuple[UnresolvedAttachment, ...]:
    feature_map = {feature.token_id: feature for feature in token_features}
    lexical_features = [
        feature
        for feature in token_features
        if feature.coarse_pos
        in {
            MorphPos.WORD,
            MorphPos.VERB_LIKE,
            MorphPos.PRONOUN,
            MorphPos.CODE,
            MorphPos.NEGATION_PARTICLE,
        }
    ]
    if len(lexical_features) < 3:
        return ()
    lexical_ids = [feature.token_id for feature in lexical_features]
    unresolved: list[UnresolvedAttachment] = []
    unresolved_index = 0
    seen: set[tuple[str, tuple[str, ...]]] = set()

    for ambiguity in surface.ambiguities:
        dependent = _first_lexical_after_span(
            lexical_features=lexical_features,
            span_start=ambiguity.affected_span.start,
        )
        if dependent is None:
            continue
        dep_index = lexical_ids.index(dependent.token_id)
        candidate_heads = tuple(lexical_ids[max(0, dep_index - 2) : dep_index])
        if len(candidate_heads) < 2:
            continue
        key = (dependent.token_id, candidate_heads)
        if key in seen:
            continue
        seen.add(key)
        unresolved_index += 1
        unresolved.append(
            UnresolvedAttachment(
                unresolved_id=f"unres-{unresolved_index}",
                dependent_token_id=dependent.token_id,
                candidate_head_ids=candidate_heads,
                relation_hint="attachment_ambiguous",
                confidence=0.58,
                reason=ambiguity.reason,
            )
        )

    for idx, feature in enumerate(lexical_features):
        if feature.coarse_pos != MorphPos.NEGATION_PARTICLE:
            continue
        if idx + 2 >= len(lexical_features):
            continue
        candidate_heads = (lexical_features[idx + 1].token_id, lexical_features[idx + 2].token_id)
        key = (lexical_features[idx + 2].token_id, candidate_heads)
        if key in seen:
            continue
        seen.add(key)
        unresolved_index += 1
        unresolved.append(
            UnresolvedAttachment(
                unresolved_id=f"unres-{unresolved_index}",
                dependent_token_id=lexical_features[idx + 2].token_id,
                candidate_head_ids=candidate_heads,
                relation_hint="negation_scope_ambiguous",
                confidence=0.54,
                reason="negation can scope over adjacent predicates/phrases",
            )
        )

    return tuple(unresolved)


def _derive_agreement_cues(
    clause_graph: ClauseGraph,
    token_features: tuple[MorphTokenFeatures, ...],
) -> tuple[MorphAgreementCue, ...]:
    feature_map = {feature.token_id: feature for feature in token_features}
    cues: list[MorphAgreementCue] = []
    cue_index = 0
    for clause in clause_graph.clauses:
        lexical_ids = [
            token_id
            for token_id in clause.token_ids
            if token_id in feature_map
            and feature_map[token_id].coarse_pos
            in {MorphPos.WORD, MorphPos.VERB_LIKE, MorphPos.PRONOUN}
        ]
        for i in range(1, len(lexical_ids)):
            controller = feature_map[lexical_ids[i - 1]]
            target = feature_map[lexical_ids[i]]
            status, reason, confidence = _agreement_status(controller.number, target.number)
            cue_index += 1
            cues.append(
                MorphAgreementCue(
                    cue_id=f"agr-{cue_index}",
                    controller_token_id=controller.token_id,
                    target_token_id=target.token_id,
                    feature_name="number",
                    status=status,
                    confidence=confidence,
                    reason=reason,
                )
            )
    return tuple(cues)


def _derive_alternative_hypothesis(
    *, base: SyntaxHypothesis, unresolved: tuple[UnresolvedAttachment, ...]
) -> SyntaxHypothesis:
    edges = list(base.edges)
    edge_index = len(edges)
    for unresolved_item in unresolved:
        if len(unresolved_item.candidate_head_ids) < 2:
            continue
        edge_index += 1
        edges.append(
            SyntaxEdge(
                edge_id=f"edge-alt-{edge_index}",
                head_token_id=unresolved_item.candidate_head_ids[1],
                dependent_token_id=unresolved_item.dependent_token_id,
                relation="alt_attach",
                clause_id=base.clause_graph.clauses[0].clause_id,
                confidence=0.52,
            )
        )
    return SyntaxHypothesis(
        hypothesis_id="syn-h2",
        clause_graph=base.clause_graph,
        edges=tuple(edges),
        unresolved_attachments=unresolved,
        token_features=base.token_features,
        agreement_cues=base.agreement_cues,
        confidence=max(0.1, round(base.confidence - 0.1, 4)),
        reason="alternative attachment hypothesis derived from unresolved edges",
    )


def _estimate_hypothesis_confidence(*, unresolved_count: int, ambiguity_count: int) -> float:
    score = 0.86
    score -= min(0.35, unresolved_count * 0.08)
    score -= min(0.3, ambiguity_count * 0.05)
    return max(0.2, min(0.95, round(score, 4)))


def _enforce_syntax_invariants(hypothesis_set: SyntaxHypothesisSet) -> None:
    if not hypothesis_set.hypotheses:
        return
    token_ids = {
        feature.token_id for feature in hypothesis_set.hypotheses[0].token_features
    }
    for hypothesis in hypothesis_set.hypotheses:
        for edge in hypothesis.edges:
            if edge.head_token_id not in token_ids or edge.dependent_token_id not in token_ids:
                raise ValueError("syntax edge refers to unknown token id")
        for unresolved in hypothesis.unresolved_attachments:
            if unresolved.dependent_token_id not in token_ids:
                raise ValueError("unresolved attachment refers to unknown dependent token id")
            if not unresolved.candidate_head_ids:
                raise ValueError("unresolved attachment requires candidate heads")
            if any(head_id not in token_ids for head_id in unresolved.candidate_head_ids):
                raise ValueError("unresolved attachment refers to unknown candidate head")
    if hypothesis_set.ambiguity_present and hypothesis_set.no_selected_winner is False:
        raise ValueError("ambiguous morphosyntax state must not select a hidden winner")


def _abstain_result(
    *, surface: UtteranceSurface, reason: str, source_lineage: tuple[str, ...]
) -> SyntaxHypothesisResult:
    hypothesis_set = SyntaxHypothesisSet(
        source_surface_ref=surface.epistemic_unit_ref,
        hypotheses=(),
        ambiguity_present=True,
        no_selected_winner=True,
        reason="no valid morphosyntax hypotheses due to invalid surface input",
    )
    gate = SyntaxDownstreamGateDecision(
        accepted=False,
        restrictions=("invalid_surface_input",),
        reason=reason,
        accepted_hypothesis_ids=(),
        rejected_hypothesis_ids=(),
        hypothesis_set_ref=surface.epistemic_unit_ref,
    )
    telemetry = build_syntax_telemetry(
        hypothesis_set=hypothesis_set,
        source_lineage=source_lineage,
        ambiguity_reasons=(reason,),
        attempted_paths=ATTEMPTED_MORPHOSYNTAX_PATHS,
        downstream_gate=gate,
        causal_basis="invalid L01 surface contract -> abstain",
    )
    return SyntaxHypothesisResult(
        hypothesis_set=hypothesis_set,
        telemetry=telemetry,
        confidence=0.1,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
    )


def _infer_pos(*, token_kind: TokenKind, lower: str) -> MorphPos:
    if token_kind in {TokenKind.PUNCTUATION, TokenKind.ELLIPSIS}:
        return MorphPos.PUNCTUATION
    if token_kind == TokenKind.QUOTE_MARK:
        return MorphPos.QUOTE
    if token_kind == TokenKind.CODE_LITERAL:
        return MorphPos.CODE
    if lower in NEGATION_FORMS:
        return MorphPos.NEGATION_PARTICLE
    if lower in CONJ_FORMS:
        return MorphPos.CONJUNCTION
    if lower in PRONOUN_SINGULAR or lower in PRONOUN_PLURAL:
        return MorphPos.PRONOUN
    if _looks_verb_like(lower):
        return MorphPos.VERB_LIKE
    if token_kind in {TokenKind.WORD, TokenKind.REPAIR_FRAGMENT}:
        return MorphPos.WORD
    return MorphPos.UNKNOWN


def _infer_number(*, lower: str, pos: MorphPos) -> MorphNumber:
    if lower in PRONOUN_SINGULAR:
        return MorphNumber.SINGULAR
    if lower in PRONOUN_PLURAL:
        return MorphNumber.PLURAL
    if lower in {"is", "was", "has", "does"}:
        return MorphNumber.SINGULAR
    if lower in {"are", "were", "have", "do"}:
        return MorphNumber.PLURAL
    if lower.endswith(("ют", "ут", "ем", "им")):
        return MorphNumber.PLURAL
    if lower.endswith(("ет", "ит", "ешь", "ишь")):
        return MorphNumber.SINGULAR
    if pos == MorphPos.WORD and lower.endswith(("s", "ы", "и")) and len(lower) > 2:
        return MorphNumber.PLURAL
    if pos == MorphPos.VERB_LIKE and lower.endswith("s") and len(lower) > 2:
        return MorphNumber.SINGULAR
    return MorphNumber.UNKNOWN


def _script_kind(token: str) -> str:
    has_cyr = any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in token)
    has_lat = any("a" <= ch.lower() <= "z" for ch in token)
    if has_cyr and has_lat:
        return "mixed"
    if has_cyr:
        return "cyrillic"
    if has_lat:
        return "latin"
    return "other"


def _feature_confidence(*, pos: MorphPos, number: MorphNumber, token_confidence: float) -> float:
    base = token_confidence
    if pos == MorphPos.UNKNOWN:
        base -= 0.25
    if number == MorphNumber.UNKNOWN:
        base -= 0.1
    return max(0.15, min(0.99, round(base, 4)))


def _map_boundary_kind(kind: SegmentKind) -> ClauseBoundaryKind:
    if kind == SegmentKind.SENTENCE:
        return ClauseBoundaryKind.SENTENCE
    if kind == SegmentKind.CLAUSE:
        return ClauseBoundaryKind.CLAUSE
    return ClauseBoundaryKind.UNKNOWN


def _first_lexical_after_span(
    *, lexical_features: list[MorphTokenFeatures], span_start: int
) -> MorphTokenFeatures | None:
    for feature in lexical_features:
        if feature.raw_span.start >= span_start:
            return feature
    return lexical_features[-1] if lexical_features else None


def _agreement_status(
    controller: MorphNumber, target: MorphNumber
) -> tuple[AgreementStatus, str, float]:
    if controller == MorphNumber.UNKNOWN or target == MorphNumber.UNKNOWN:
        return AgreementStatus.UNKNOWN, "insufficient number features for agreement decision", 0.45
    if controller == target:
        return AgreementStatus.MATCH, "number agreement cue match", 0.78
    return AgreementStatus.CONFLICT, "number agreement cue conflict", 0.76


def _looks_verb_like(lower: str) -> bool:
    if lower.endswith(("ed", "ing", "ть", "л", "ла", "ли", "ло")):
        return True
    if lower in {"is", "are", "was", "were", "be", "am", "have", "has", "do", "does"}:
        return True
    return False
