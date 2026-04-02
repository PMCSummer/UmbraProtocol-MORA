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


def _basis_class_for_surface(result, surface: str) -> LexicalBasisClass:
    mention_id = next(
        anchor.mention_id
        for anchor in result.bundle.mention_anchors
        if anchor.normalized_text.lower() == surface.lower()
    )
    return next(
        basis.basis_class
        for basis in result.bundle.lexical_basis_records
        if basis.mention_id == mention_id
    )


def test_lexicon_ablation_changes_l03_lexical_basis_mode() -> None:
    syntax_result, surface_result = _syntax_result("thing", "m-l03-neg-lex-ablate")
    with_lexicon = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )
    without_lexicon = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=None,
    )

    assert _basis_class_for_surface(with_lexicon, "thing") == LexicalBasisClass.LEXICON_BACKED
    assert _basis_class_for_surface(without_lexicon, "thing") == LexicalBasisClass.HEURISTIC_FALLBACK
    assert with_lexicon.bundle.heuristic_fallback_used is False
    assert without_lexicon.bundle.heuristic_fallback_used is True


def test_forced_heuristic_only_path_is_more_capped_than_lexicon_backed() -> None:
    syntax_result, surface_result = _syntax_result("thing", "m-l03-neg-heuristic-only")
    with_lexicon = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )
    without_lexicon = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=None,
    )

    assert with_lexicon.bundle.no_strong_lexical_claim_from_fallback is False
    assert without_lexicon.bundle.no_strong_lexical_claim_from_fallback is True
    with_conf = max(candidate.confidence for candidate in with_lexicon.bundle.sense_candidates)
    without_conf = max(candidate.confidence for candidate in without_lexicon.bundle.sense_candidates)
    assert with_conf > without_conf
