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
    LexicalGroundingResult,
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
    surface_result = build_utterance_surface(epistemic.unit)
    return build_morphosyntax_candidate_space(surface_result), surface_result


def test_generation_produces_typed_lexical_grounding_bundle_and_telemetry() -> None:
    syntax_result, surface_result = _syntax_result(
        "Bank alpha and qzxv", "m-l03-gen"
    )
    result = build_lexical_grounding_hypotheses(
        syntax_result, utterance_surface=surface_result
    )

    assert isinstance(result, LexicalGroundingResult)
    assert result.bundle.mention_anchors
    assert result.bundle.lexeme_candidates
    assert result.bundle.sense_candidates
    assert result.bundle.entity_candidates
    assert result.bundle.no_final_resolution_performed is True
    assert result.no_final_resolution_performed is True
    assert result.telemetry.candidate_count == (
        len(result.bundle.lexeme_candidates)
        + len(result.bundle.reference_hypotheses)
        + len(result.bundle.deixis_candidates)
    )
    assert result.telemetry.sense_candidate_count == len(result.bundle.sense_candidates)
    assert result.telemetry.entity_candidate_count == len(result.bundle.entity_candidates)
    assert result.telemetry.attempted_grounding_paths


def test_span_traceability_to_l01_l02_anchors_is_preserved() -> None:
    syntax_result, surface_result = _syntax_result("alpha beta", "m-l03-trace")
    result = build_lexical_grounding_hypotheses(
        syntax_result, utterance_surface=surface_result
    )

    token_ids = {feature.token_id for feature in syntax_result.hypothesis_set.hypotheses[0].token_features}
    for mention in result.bundle.mention_anchors:
        assert mention.token_id in token_ids
        assert mention.raw_span.start < mention.raw_span.end
    for candidate in result.bundle.lexeme_candidates:
        assert candidate.mention_id in {mention.mention_id for mention in result.bundle.mention_anchors}


def test_unknown_lexical_item_surfaces_unknown_state_not_forced_resolution() -> None:
    syntax_result, _ = _syntax_result("qzxv nrmpt", "m-l03-unknown")
    result = build_lexical_grounding_hypotheses(syntax_result)

    assert result.bundle.unknown_states
    assert result.partial_known is True
    assert any("unknown lexical item" in unknown.reason for unknown in result.bundle.unknown_states)
