from substrate.dictum_candidates import DictumCandidateResult, build_dictum_candidates
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


def _pipeline(text: str, material_id: str, context: LexicalDiscourseContext | None = None):
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
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    lexical_result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=context,
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=context,
    )
    return surface_result, syntax_result, lexical_result, dictum_result


def test_dictum_candidates_are_built_from_typed_l03_l02_inputs() -> None:
    _, _, _, result = _pipeline(
        "we do not track alpha tomorrow very 3",
        material_id="m-l04-gen",
    )
    assert isinstance(result, DictumCandidateResult)
    assert result.bundle.dictum_candidates
    assert result.bundle.no_final_resolution_performed is True
    assert result.no_final_resolution_performed is True
    assert result.telemetry.dictum_candidate_count == len(result.bundle.dictum_candidates)
    assert result.telemetry.magnitude_marker_count >= 0


def test_dictum_candidate_structure_is_traceable_to_syntax_and_spans() -> None:
    _, syntax_result, lexical_result, dictum_result = _pipeline(
        "alpha moved here",
        material_id="m-l04-trace",
    )
    syntax_ids = {hypothesis.hypothesis_id for hypothesis in syntax_result.hypothesis_set.hypotheses}
    lexical_ref = lexical_result.bundle.source_syntax_ref
    for candidate in dictum_result.bundle.dictum_candidates:
        assert candidate.source_syntax_hypothesis_ref in syntax_ids
        assert candidate.source_lexical_grounding_ref == lexical_ref
        assert candidate.predicate_frame.predicate_span.start < candidate.predicate_frame.predicate_span.end
        for slot in candidate.argument_slots:
            assert slot.token_span.start < slot.token_span.end


def test_l02_syntax_ambiguity_propagates_into_l04_candidate_bundle() -> None:
    _, syntax_result, lexical_result, dictum_result = _pipeline(
        "alpha beta ... gamma delta",
        material_id="m-l04-syntax-prop",
    )
    assert len(syntax_result.hypothesis_set.hypotheses) >= 2
    assert len(dictum_result.bundle.linked_syntax_hypothesis_ids) >= 2
    assert dictum_result.bundle.dictum_candidates
    covered_syntax_refs = {
        candidate.source_syntax_hypothesis_ref
        for candidate in dictum_result.bundle.dictum_candidates
    }
    assert len(covered_syntax_refs) >= 2 or any(
        "lexical_instability_from_upstream_syntax" in candidate.ambiguity_reasons
        for candidate in dictum_result.bundle.dictum_candidates
    )
    assert dictum_result.partial_known is True
    assert dictum_result.bundle.ambiguities or dictum_result.bundle.conflicts
