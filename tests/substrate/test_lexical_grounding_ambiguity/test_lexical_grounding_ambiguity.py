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


def test_ambiguous_sense_bundle_is_explicit_not_silently_collapsed() -> None:
    result = build_lexical_grounding_hypotheses(_syntax_result("bank", "m-l03-amb-bank"))
    bank_senses = [
        candidate for candidate in result.bundle.sense_candidates if candidate.sense_key.startswith("sense:")
    ]

    assert len(bank_senses) >= 2
    assert result.bundle.conflicts
    assert result.bundle.no_final_resolution_performed is True


def test_pronoun_without_discourse_basis_yields_unresolved_reference() -> None:
    result = build_lexical_grounding_hypotheses(_syntax_result("he arrived", "m-l03-amb-pron"))
    pronoun_refs = [
        hypothesis
        for hypothesis in result.bundle.reference_hypotheses
        if hypothesis.reference_kind.value == "pronoun"
    ]
    assert pronoun_refs
    assert any(hypothesis.unresolved for hypothesis in pronoun_refs)
    assert result.bundle.unknown_states


def test_incompatible_weak_candidates_expose_conflict_state() -> None:
    result = build_lexical_grounding_hypotheses(_syntax_result("замок", "m-l03-amb-lock"))
    assert result.bundle.conflicts
    assert any("lexical senses" in conflict.reason for conflict in result.bundle.conflicts)
