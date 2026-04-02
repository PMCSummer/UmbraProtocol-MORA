from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _syntax_result(text: str, material_id: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    return build_morphosyntax_candidate_space(surface), surface


def test_l02_ambiguity_is_load_bearing_for_l03_output() -> None:
    syntax_result, surface = _syntax_result(
        "alpha beta ... gamma delta",
        "m-l03-syntax-prop",
    )
    assert len(syntax_result.hypothesis_set.hypotheses) >= 2

    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface,
    )
    assert result.bundle.linked_hypothesis_ids
    assert len(result.bundle.linked_hypothesis_ids) >= 2
    assert result.bundle.syntax_instability_present is True
    assert "unstable_across_syntax_hypotheses" in result.bundle.ambiguity_reasons
    assert any(
        len(mention.supporting_syntax_hypothesis_refs) >= 2
        for mention in result.bundle.mention_anchors
    )
    assert result.telemetry.syntax_hypothesis_count >= 2
    assert result.telemetry.syntax_instability_mention_count > 0


def test_pronoun_with_competing_candidates_stays_unresolved_not_forced_top1() -> None:
    syntax_result, surface = _syntax_result("alpha he", "m-l03-syntax-pron")
    context = LexicalDiscourseContext(
        context_ref="ctx:l03-pron",
        entity_bindings=(("he", "entity:ctx-he"),),
        recent_mentions=("entity:recent-he",),
    )
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface,
        discourse_context=context,
    )
    pronoun_refs = [
        hypothesis
        for hypothesis in result.bundle.reference_hypotheses
        if hypothesis.reference_kind.value == "pronoun"
    ]

    assert pronoun_refs
    assert any(len(hypothesis.candidate_ref_ids) > 1 for hypothesis in pronoun_refs)
    assert any(hypothesis.unresolved for hypothesis in pronoun_refs)
