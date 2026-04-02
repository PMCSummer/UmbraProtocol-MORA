from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface, evaluate_surface_downstream_gate


def _surface(text: str):
    unit = ground_epistemic_input(
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="boundary-user",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    ).unit
    return build_utterance_surface(unit)


def test_l01_output_has_no_semantic_truth_intent_appraisal_claim_fields() -> None:
    result = _surface("blarf zint")
    forbidden = {
        "meaning",
        "selected_meaning",
        "final_interpretation",
        "world_truth",
        "intent",
        "illocution",
        "appraisal",
    }
    assert all(not hasattr(result, field) for field in forbidden)
    assert all(not hasattr(result.surface, field) for field in forbidden)


def test_nonce_strings_do_not_gain_hidden_interpretation() -> None:
    left = _surface("blarf zint")
    right = _surface("zint blarf")
    left_gate = evaluate_surface_downstream_gate(left.surface)
    right_gate = evaluate_surface_downstream_gate(right.surface)

    assert left_gate.accepted is True
    assert right_gate.accepted is True
    assert "normalization_log_present" in left_gate.restrictions
    assert "normalization_log_present" in right_gate.restrictions
    assert not hasattr(left, "semantic_label")
    assert not hasattr(right, "semantic_label")


def test_unmatched_quotes_and_parentheses_produce_honest_uncertainty() -> None:
    result = _surface('"blarf (zint')
    warning_set = set(result.telemetry.surface_warnings)
    assert result.partial_known is True
    assert {"quote_boundary_uncertain", "parenthetical_boundary_uncertain"} & warning_set
