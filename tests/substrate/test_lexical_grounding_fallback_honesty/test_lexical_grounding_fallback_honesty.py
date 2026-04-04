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
    build_lexical_grounding_hypotheses,
    evaluate_lexical_grounding_downstream_gate,
)
from substrate.lexicon import create_seed_lexicon_state
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


def _mention_id_for_surface(result, surface: str) -> str:
    normalized = surface.lower()
    return next(
        anchor.mention_id
        for anchor in result.bundle.mention_anchors
        if anchor.normalized_text.lower() == normalized
    )


def test_fallback_is_explicit_and_gate_is_capped() -> None:
    syntax_result, surface_result = _syntax_result("bank", "m-l03-fallback-explicit")
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )
    mention_id = _mention_id_for_surface(result, "bank")

    fallback_candidates = [
        candidate
        for candidate in result.bundle.sense_candidates
        if candidate.mention_id == mention_id and "heuristic_fallback:" in candidate.evidence
    ]
    assert fallback_candidates
    assert result.bundle.heuristic_fallback_used is True
    assert result.bundle.no_strong_lexical_claim_from_fallback is True
    assert "heuristic_fallback_used" in result.bundle.ambiguity_reasons
    gate = evaluate_lexical_grounding_downstream_gate(result)
    assert "no_strong_lexical_claim_from_fallback" in gate.restrictions


def test_lexicon_unknown_is_not_erased_by_fallback() -> None:
    syntax_result, surface_result = _syntax_result("bank", "m-l03-unknown-survives")
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )

    assert any(
        "lexicon unknown state: known_lexeme_unknown_sense_in_context" in unknown.reason
        for unknown in result.bundle.unknown_states
    )
    assert "lexicon_known_lexeme_unknown_sense_in_context" in result.bundle.ambiguity_reasons
    assert result.bundle.no_final_resolution_performed is True


def test_queried_but_capped_lexicon_is_not_reported_as_usable_basis() -> None:
    syntax_result, surface_result = _syntax_result("bank", "m-l03-queried-capped")
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )
    gate = evaluate_lexical_grounding_downstream_gate(result)

    assert result.lexicon_handoff_present is True
    assert result.lexicon_query_attempted is True
    assert result.lexicon_primary_used is True  # compatibility marker
    assert result.lexicon_usable_basis_present is False
    assert result.lexicon_backed_mentions_count == 0
    assert result.telemetry.lexicon_query_attempted is True
    assert result.telemetry.lexicon_usable_basis_present is False
    assert result.telemetry.lexicon_backed_mentions_count == 0
    assert "lexicon_query_attempted" in gate.restrictions
    assert "lexicon_query_attempted_without_usable_basis" in gate.restrictions
    assert "no_strong_lexical_claim_from_fallback" in gate.restrictions


def test_missing_lexicon_handoff_enters_explicit_degraded_mode() -> None:
    syntax_result, surface_result = _syntax_result("thing", "m-l03-missing-lexicon-handoff")
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=None,
    )
    gate = evaluate_lexical_grounding_downstream_gate(result)

    assert result.lexicon_handoff_missing is True
    assert result.lexical_basis_degraded is True
    assert result.no_strong_lexical_claim_without_lexicon is True
    assert result.bundle.lexicon_handoff_missing is True
    assert result.bundle.no_strong_lexical_claim_without_lexicon is True
    assert "lexicon_handoff_missing" in gate.restrictions
    assert "no_strong_lexical_claim_without_lexicon" in gate.restrictions
