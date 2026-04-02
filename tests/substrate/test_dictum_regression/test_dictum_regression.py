import pytest

from substrate.dictum_candidates import build_dictum_candidates
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


def _dictum_result(text: str, material_id: str, context: LexicalDiscourseContext | None = None):
    context = context or LexicalDiscourseContext(context_ref=f"ctx:{material_id}")
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
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(
        syntax,
        utterance_surface=surface,
        discourse_context=context,
    )
    return build_dictum_candidates(
        lexical,
        syntax,
        utterance_surface=surface,
        discourse_context=context,
    )


@pytest.mark.parametrize(
    ("text", "case"),
    (
        ("we do not track alpha beta", "negation_scope"),
        ("he saw him", "partial_pronoun"),
        ('"alpha" moved', "quoted_content"),
        ("if alpha then", "conditional_fragment"),
        ("do this now", "temporal_anchor"),
        ("qzxv moved", "unknown_word_shell"),
        ("can you close the door", "pragmatic_temptation"),
    ),
)
def test_regression_corpus_keeps_dictum_candidate_contract(text: str, case: str) -> None:
    result = _dictum_result(text, material_id=f"m-l04-reg-{case}")
    assert result.no_final_resolution_performed is True
    assert result.bundle.reason
    if not result.bundle.dictum_candidates:
        assert result.bundle.unknowns
        return

    if case == "negation_scope":
        assert any(candidate.negation_markers for candidate in result.bundle.dictum_candidates)
        assert any(marker.ambiguous for candidate in result.bundle.dictum_candidates for marker in candidate.scope_markers)
    elif case == "partial_pronoun":
        assert any(candidate.underspecified_slots for candidate in result.bundle.dictum_candidates)
    elif case == "quoted_content":
        assert any(candidate.quotation_sensitive for candidate in result.bundle.dictum_candidates)
    elif case == "conditional_fragment":
        assert result.bundle.blocked_candidate_reasons or result.partial_known
    elif case == "temporal_anchor":
        assert any(candidate.temporal_markers for candidate in result.bundle.dictum_candidates)
    elif case == "unknown_word_shell":
        assert result.bundle.unknowns or any(candidate.underspecified_slots for candidate in result.bundle.dictum_candidates)
    elif case == "pragmatic_temptation":
        assert not hasattr(result.bundle, "illocution")


def test_context_shift_changes_dictum_candidate_distribution_or_marks_conflict() -> None:
    a = _dictum_result(
        "he moved here",
        material_id="m-l04-reg-shift-a",
        context=LexicalDiscourseContext(
            context_ref="ctx:a",
            entity_bindings=(("he", "entity:alpha"),),
        ),
    )
    b = _dictum_result(
        "he moved here",
        material_id="m-l04-reg-shift-b",
        context=LexicalDiscourseContext(
            context_ref="ctx:b",
            entity_bindings=(("he", "entity:beta"),),
        ),
    )
    sig_a = tuple(
        tuple(slot.reference_candidate_ids for slot in candidate.argument_slots)
        for candidate in a.bundle.dictum_candidates
    )
    sig_b = tuple(
        tuple(slot.reference_candidate_ids for slot in candidate.argument_slots)
        for candidate in b.bundle.dictum_candidates
    )
    assert sig_a != sig_b or a.bundle.conflicts or b.bundle.conflicts
