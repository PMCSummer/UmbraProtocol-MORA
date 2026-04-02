import pytest

from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.morphosyntax import build_morphosyntax_candidate_space


def _surface_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-fuzz-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


@pytest.mark.parametrize(
    "text",
    (
        "",
        "   ",
        "!!! ... ??",
        "\"unterminated quote",
        "(open parenthetical",
        "```broken fence",
        "not not not ???",
        "не не не ???",
        "alpha\t\tbeta\r\ngamma",
        "blarf|||zint",
        "🙂🙂 ???",
        "qzxv nrmpt ???",
    ),
)
def test_fuzz_like_inputs_do_not_crash_and_keep_honest_uncertainty(text: str) -> None:
    result = build_morphosyntax_candidate_space(_surface_result(text))

    assert result is not None
    assert result.hypothesis_set.no_selected_winner is True
    assert result.partial_known or result.abstain or result.hypothesis_set.ambiguity_present
    assert result.confidence <= 0.95


def test_repeated_negation_markers_remain_structurally_visible_under_noise() -> None:
    result = build_morphosyntax_candidate_space(_surface_result("not not not alpha ???"))
    unresolved = result.hypothesis_set.hypotheses[0].unresolved_attachments if result.hypothesis_set.hypotheses else ()

    assert result.telemetry.negation_carrier_count > 0 or any(
        item.relation_hint == "negation_scope_ambiguous" for item in unresolved
    )
