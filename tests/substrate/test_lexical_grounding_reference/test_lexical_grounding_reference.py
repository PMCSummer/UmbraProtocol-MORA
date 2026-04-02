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
    return build_morphosyntax_candidate_space(build_utterance_surface(epistemic.unit))


def test_deixis_candidates_generated_and_context_bound_when_available() -> None:
    context = LexicalDiscourseContext(
        context_ref="ctx:dialogue-1",
        indexical_bindings=(
            ("speaker", "agent:self"),
            ("location", "loc:room-7"),
            ("time", "time:now"),
            ("object", "obj:focus-1"),
        ),
    )
    result = build_lexical_grounding_hypotheses(
        _syntax_result("я здесь сейчас это", "m-l03-deixis"),
        discourse_context=context,
    )
    assert result.bundle.deixis_candidates
    assert all(candidate.discourse_context_ref == "ctx:dialogue-1" for candidate in result.bundle.deixis_candidates)
    assert any(candidate.target_ref is not None for candidate in result.bundle.deixis_candidates)


def test_discourse_context_shifts_reference_candidates_without_forced_resolution() -> None:
    syntax_result = _syntax_result("he arrived", "m-l03-ref-shift")
    context_a = LexicalDiscourseContext(
        context_ref="ctx:A",
        entity_bindings=(("he", "entity:alice"),),
    )
    context_b = LexicalDiscourseContext(
        context_ref="ctx:B",
        entity_bindings=(("he", "entity:bob"),),
    )
    a = build_lexical_grounding_hypotheses(syntax_result, discourse_context=context_a)
    b = build_lexical_grounding_hypotheses(syntax_result, discourse_context=context_b)

    refs_a = tuple(
        hypothesis.candidate_ref_ids
        for hypothesis in a.bundle.reference_hypotheses
        if hypothesis.reference_kind.value == "pronoun"
    )
    refs_b = tuple(
        hypothesis.candidate_ref_ids
        for hypothesis in b.bundle.reference_hypotheses
        if hypothesis.reference_kind.value == "pronoun"
    )
    assert refs_a
    assert refs_b
    assert refs_a != refs_b
    assert a.bundle.no_final_resolution_performed is True
    assert b.bundle.no_final_resolution_performed is True


def test_discourse_linked_mentions_emit_entity_candidates() -> None:
    context = LexicalDiscourseContext(
        context_ref="ctx:entities",
        entity_bindings=(("alpha", "entity:alpha-root"),),
    )
    result = build_lexical_grounding_hypotheses(
        _syntax_result("alpha arrives", "m-l03-entity-link"),
        discourse_context=context,
    )
    linked = [candidate for candidate in result.bundle.entity_candidates if candidate.entity_ref == "entity:alpha-root"]
    assert linked
    assert linked[0].discourse_context_ref == "ctx:entities"
