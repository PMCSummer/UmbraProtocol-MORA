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


def _l03_result(text: str, *, material_id: str, context: LexicalDiscourseContext | None = None):
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


def _pronoun_signature(result) -> tuple[int, int]:
    pronouns = [
        hypothesis
        for hypothesis in result.bundle.reference_hypotheses
        if hypothesis.reference_kind.value == "pronoun"
    ]
    unresolved = sum(1 for hypothesis in pronouns if hypothesis.unresolved)
    return len(pronouns), unresolved


def test_whitespace_and_casing_do_not_break_reference_structure() -> None:
    context = LexicalDiscourseContext(
        context_ref="ctx:meta-1",
        entity_bindings=(("alpha", "entity:alpha"),),
    )
    compact = _l03_result("alpha he arrived", material_id="m-l03-meta-compact", context=context)
    spaced = _l03_result("  alpha   he   arrived  ", material_id="m-l03-meta-spaced", context=context)

    assert len(compact.bundle.mention_anchors) == len(spaced.bundle.mention_anchors)
    assert _pronoun_signature(compact) == _pronoun_signature(spaced)
    assert compact.bundle.no_final_resolution_performed is True
    assert spaced.bundle.no_final_resolution_performed is True


def test_irrelevant_noise_permutation_does_not_create_fake_resolution() -> None:
    base = _l03_result("he arrived", material_id="m-l03-meta-base")
    noisy = _l03_result("!!! he ??? arrived ...", material_id="m-l03-meta-noisy")

    base_pronouns, base_unresolved = _pronoun_signature(base)
    noisy_pronouns, noisy_unresolved = _pronoun_signature(noisy)

    assert base_pronouns > 0
    assert noisy_pronouns > 0
    assert base_unresolved > 0
    assert noisy_unresolved > 0


def test_quote_marker_changes_keep_candidates_contestable_not_finalized() -> None:
    quoted = _l03_result('"alpha" he', material_id="m-l03-meta-quoted")
    plain = _l03_result("alpha he", material_id="m-l03-meta-plain")

    assert quoted.bundle.lexeme_candidates
    assert plain.bundle.lexeme_candidates
    assert quoted.bundle.no_final_resolution_performed is True
    assert plain.bundle.no_final_resolution_performed is True
    assert len(quoted.bundle.reference_hypotheses) >= 1
    assert len(plain.bundle.reference_hypotheses) >= 1
