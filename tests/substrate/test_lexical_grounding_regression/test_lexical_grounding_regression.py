import pytest

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


def _l03_result(text: str, material_id: str, context: LexicalDiscourseContext | None = None):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    return build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=context,
    )


@pytest.mark.parametrize(
    ("text", "case"),
    (
        ("he saw him", "pronoun_ambiguous"),
        ("здесь сейчас это", "deixis_without_anchor"),
        ('"alpha" alpha', "quoted_vs_current"),
        ("qzxv token", "unknown_word"),
        ("Bank bank", "common_vs_entity_like"),
        ("it it it", "repeated_reference_without_identity_basis"),
    ),
)
def test_adversarial_regression_corpus_keeps_contestable_outputs(text: str, case: str) -> None:
    result = _l03_result(text, material_id=f"m-l03-reg-{case}")

    assert result.bundle.no_final_resolution_performed is True
    assert result.no_final_resolution_performed is True
    assert result.bundle.mention_anchors or result.abstain

    if case == "pronoun_ambiguous":
        pronoun_refs = [
            hypothesis
            for hypothesis in result.bundle.reference_hypotheses
            if hypothesis.reference_kind.value == "pronoun"
        ]
        assert pronoun_refs
        assert any(hypothesis.unresolved for hypothesis in pronoun_refs)
    elif case == "deixis_without_anchor":
        assert result.bundle.deixis_candidates
        assert all(candidate.unresolved for candidate in result.bundle.deixis_candidates)
    elif case == "quoted_vs_current":
        assert len(result.bundle.mention_anchors) >= 2
        assert result.bundle.entity_candidates
    elif case == "unknown_word":
        assert result.bundle.unknown_states
    elif case == "common_vs_entity_like":
        assert any(candidate.entity_type == "named_entity" for candidate in result.bundle.entity_candidates)
        assert any(candidate.entity_type == "common_mention" for candidate in result.bundle.entity_candidates)
    elif case == "repeated_reference_without_identity_basis":
        pronoun_refs = [
            hypothesis
            for hypothesis in result.bundle.reference_hypotheses
            if hypothesis.reference_kind.value == "pronoun"
        ]
        assert pronoun_refs
        assert any(hypothesis.unresolved for hypothesis in pronoun_refs) or result.bundle.unknown_states


def test_entity_drift_risk_keeps_multiple_candidates_or_conflict() -> None:
    result = _l03_result(
        "Alpha alpha",
        material_id="m-l03-reg-drift",
        context=LexicalDiscourseContext(context_ref="ctx:drift"),
    )
    alpha_mentions = [anchor for anchor in result.bundle.mention_anchors if anchor.normalized_text.lower() == "alpha"]
    per_mention_candidates = [
        [candidate for candidate in result.bundle.entity_candidates if candidate.mention_id == anchor.mention_id]
        for anchor in alpha_mentions
    ]

    assert alpha_mentions
    assert any(len(candidates) > 1 for candidates in per_mention_candidates) or result.bundle.conflicts
