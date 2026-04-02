from substrate.dictum_candidates import DictumPolarity, build_dictum_candidates
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _dictum_result(text: str, material_id: str):
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
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    return build_dictum_candidates(lexical, syntax, utterance_surface=surface)


def test_cosmetic_whitespace_preserves_dictum_core_shape() -> None:
    compact = _dictum_result("we track alpha", "m-l04-meta-compact")
    spaced = _dictum_result("  we   track   alpha  ", "m-l04-meta-spaced")
    signature_compact = (
        len(compact.bundle.dictum_candidates),
        sum(len(candidate.argument_slots) for candidate in compact.bundle.dictum_candidates),
    )
    signature_spaced = (
        len(spaced.bundle.dictum_candidates),
        sum(len(candidate.argument_slots) for candidate in spaced.bundle.dictum_candidates),
    )
    assert signature_compact == signature_spaced


def test_negation_change_changes_polarity_predictably() -> None:
    plain = _dictum_result("we track alpha", "m-l04-meta-plain")
    negated = _dictum_result("we do not track alpha", "m-l04-meta-neg")
    plain_polarity = {candidate.polarity for candidate in plain.bundle.dictum_candidates}
    neg_polarity = {candidate.polarity for candidate in negated.bundle.dictum_candidates}
    assert DictumPolarity.NEGATED not in plain_polarity
    assert DictumPolarity.NEGATED in neg_polarity


def test_quote_marker_change_affects_quotation_sensitivity_not_hidden_semantics() -> None:
    quoted = _dictum_result('"alpha moved"', "m-l04-meta-quoted")
    plain = _dictum_result("alpha moved", "m-l04-meta-plain-quote")
    assert any(candidate.quotation_sensitive for candidate in quoted.bundle.dictum_candidates)
    assert any(not candidate.quotation_sensitive for candidate in plain.bundle.dictum_candidates)
