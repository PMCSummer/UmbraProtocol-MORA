import pytest

from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import (
    build_utterance_surface,
    evaluate_surface_downstream_gate,
)


def _epistemic_unit(text: str):
    result = ground_epistemic_input(
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return result.unit


def test_downstream_gate_rejects_raw_text_and_accepts_typed_surface() -> None:
    with pytest.raises(TypeError):
        evaluate_surface_downstream_gate("blarf zint")

    result = build_utterance_surface(_epistemic_unit("blarf zint."))
    gate = evaluate_surface_downstream_gate(result.surface)
    assert gate.accepted is True
    assert gate.surface_ref == result.surface.epistemic_unit_ref


def test_downstream_gate_restrictions_are_load_bearing() -> None:
    result = build_utterance_surface(_epistemic_unit('"blarf... zint", — сказал user'))
    gate = evaluate_surface_downstream_gate(result.surface)

    assert "surface_ambiguity_present" in gate.restrictions
    assert "quoted_spans_present" in gate.restrictions
    assert "normalization_log_present" in gate.restrictions


def test_l01_removal_breaks_critical_path_contract() -> None:
    # Without L01, downstream receives only raw text and must reject critical path input.
    raw = _epistemic_unit("blarf zint.").content
    with pytest.raises(TypeError):
        evaluate_surface_downstream_gate(raw)
