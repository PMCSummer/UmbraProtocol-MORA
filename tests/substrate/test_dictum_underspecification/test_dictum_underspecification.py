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
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    lexical_result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
    )
    return build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
    )


def test_unknown_and_unresolved_upstream_material_maps_to_underspecified_slots() -> None:
    result = _dictum_result("he qzxv here", "m-l04-under-1")
    assert result.bundle.dictum_candidates
    assert any(candidate.underspecified_slots for candidate in result.bundle.dictum_candidates)
    assert result.bundle.unknowns


def test_partial_construction_remains_valid_without_fake_completeness() -> None:
    result = _dictum_result("qzxv", "m-l04-under-2")
    assert result.no_final_resolution_performed is True
    assert result.partial_known is True or result.abstain is True


def test_lexical_ambiguity_creates_underspecified_slot_not_silent_resolution() -> None:
    result = _dictum_result("bank moved", "m-l04-under-3")
    assert result.bundle.dictum_candidates
    assert any(
        "multiple_lexical_candidates_for_slot" in (slot.unresolved_reason or "")
        or "predicate_lexical_ambiguity" in candidate.ambiguity_reasons
        for candidate in result.bundle.dictum_candidates
        for slot in candidate.argument_slots
    ) or any(
        slot.slot_id_or_field == "predicate_lexeme"
        for candidate in result.bundle.dictum_candidates
        for slot in candidate.underspecified_slots
    )
