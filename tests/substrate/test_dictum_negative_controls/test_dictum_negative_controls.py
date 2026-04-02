from dataclasses import replace

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


def _result(text: str, material_id: str):
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


def test_ablation_without_candidate_bundle_degrades_downstream_contract() -> None:
    result = _result("we do not track alpha", "m-l04-neg-ablation")
    assert evaluate_dictum_downstream_gate(result).accepted is True
    ablated_bundle = replace(
        result.bundle,
        dictum_candidates=(),
        ambiguities=(),
        conflicts=(),
        unknowns=(),
        blocked_candidate_reasons=("ablated",),
    )
    gate = evaluate_dictum_downstream_gate(ablated_bundle)
    assert gate.accepted is False
    assert "no_dictum_candidates" in gate.restrictions


def test_post_hoc_text_report_is_not_valid_typed_dictum_artifact() -> None:
    with pytest.raises(TypeError):
        evaluate_dictum_downstream_gate(
            {"report": "final proposition accepted", "confidence": 0.99}
        )


def test_adversarial_case_requires_underspecification_or_unknown_markers() -> None:
    result = _result("he qzxv not", "m-l04-neg-adv")
    has_uncertainty = (
        bool(result.bundle.unknowns)
        or bool(result.bundle.conflicts)
        or any(candidate.underspecified_slots for candidate in result.bundle.dictum_candidates)
    )
    assert has_uncertainty is True


def test_forced_top1_style_collapse_changes_gate_contract_signal() -> None:
    result = _result("he qzxv not", "m-l04-neg-collapse")
    original_gate = evaluate_dictum_downstream_gate(result)
    original_signal = set(original_gate.restrictions)
    assert "no_final_resolution_performed" in original_signal

    if not result.bundle.dictum_candidates:
        return

    first = result.bundle.dictum_candidates[0]
    collapsed_slots = tuple(
        replace(
            slot,
            unresolved=False,
            unresolved_reason=None,
            lexical_candidate_ids=slot.lexical_candidate_ids[:1],
            reference_candidate_ids=slot.reference_candidate_ids[:1],
        )
        for slot in first.argument_slots
    )
    collapsed_first = replace(
        first,
        argument_slots=collapsed_slots,
        underspecified_slots=(),
        ambiguity_reasons=(),
    )
    collapsed_bundle = replace(
        result.bundle,
        dictum_candidates=(collapsed_first,),
        ambiguities=(),
        conflicts=(),
        unknowns=(),
    )
    collapsed_gate = evaluate_dictum_downstream_gate(collapsed_bundle)
    collapsed_signal = set(collapsed_gate.restrictions)

    assert original_signal != collapsed_signal
