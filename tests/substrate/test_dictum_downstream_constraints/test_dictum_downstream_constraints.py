import pytest

from substrate.dictum_candidates import (
    build_dictum_candidates,
    evaluate_dictum_downstream_gate,
)
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


def _dictum_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l04-gate", content="he qzxv here"),
        SourceMetadata(
            source_id="user-l04-gate",
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


def test_gate_rejects_raw_input_and_accepts_typed_result_or_bundle() -> None:
    with pytest.raises(TypeError):
        evaluate_dictum_downstream_gate("raw dictum")
    with pytest.raises(TypeError):
        evaluate_dictum_downstream_gate({"dictum": "raw"})

    result = _dictum_result()
    from_result = evaluate_dictum_downstream_gate(result)
    from_bundle = evaluate_dictum_downstream_gate(result.bundle)
    assert from_result.accepted is True
    assert from_bundle.accepted is True


def test_gate_restrictions_expose_uncertainty_and_no_final_resolution() -> None:
    result = _dictum_result()
    gate = evaluate_dictum_downstream_gate(result)
    assert "no_final_resolution_performed" in gate.restrictions
    assert (
        "underspecified_slots_present" in gate.restrictions
        or "dictum_unknown_present" in gate.restrictions
        or "scope_ambiguity_present" in gate.restrictions
    )
