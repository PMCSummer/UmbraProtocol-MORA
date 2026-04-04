from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import LexicalBasisClass, build_lexical_grounding_hypotheses
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


def _basis_by_surface(result) -> dict[str, object]:
    anchors = {anchor.mention_id: anchor.normalized_text.lower() for anchor in result.bundle.mention_anchors}
    return {
        anchors[basis.mention_id]: basis
        for basis in result.bundle.lexical_basis_records
        if basis.mention_id in anchors
    }


def test_l03_uses_lexicon_as_primary_basis_when_usable() -> None:
    syntax_result, surface_result = _syntax_result("thing arrived", "m-l03-lexicon-primary")
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )
    basis = _basis_by_surface(result)["thing"]

    assert basis.basis_class == LexicalBasisClass.LEXICON_BACKED
    assert basis.lexicon_used is True
    assert basis.lexicon_usable is True
    assert basis.heuristic_fallback_used is False
    assert basis.no_strong_lexical_claim_from_fallback is False
    assert result.lexicon_primary_used is True
    assert result.lexicon_handoff_present is True
    assert result.lexicon_query_attempted is True
    assert result.lexicon_usable_basis_present is True
    assert result.lexicon_backed_mentions_count >= 1
    thing_senses = [
        candidate
        for candidate in result.bundle.sense_candidates
        if candidate.mention_id == basis.mention_id
    ]
    assert thing_senses
    assert all(candidate.sense_key.startswith("lexicon:") for candidate in thing_senses)


def test_heuristic_fallback_only_when_lexicon_is_capped_or_unknown() -> None:
    syntax_result, surface_result = _syntax_result("bank qzxv", "m-l03-lexicon-fallback")
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )
    basis = _basis_by_surface(result)

    assert basis["bank"].basis_class == LexicalBasisClass.LEXICON_CAPPED_UNKNOWN
    assert basis["bank"].heuristic_fallback_used is True
    assert basis["bank"].no_strong_lexical_claim_from_fallback is True

    assert basis["qzxv"].basis_class == LexicalBasisClass.LEXICON_CAPPED_UNKNOWN
    assert basis["qzxv"].heuristic_fallback_used is True
    assert basis["qzxv"].no_strong_lexical_claim_from_fallback is True

    assert result.heuristic_fallback_used is True
    assert result.lexicon_handoff_present is True
    assert result.lexicon_query_attempted is True
    assert result.lexicon_usable_basis_present is False
    assert result.lexicon_backed_mentions_count == 0
    assert result.bundle.no_strong_lexical_claim_from_fallback is True
