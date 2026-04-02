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
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


def test_ambiguous_attachment_emits_candidates_or_unresolved_edges() -> None:
    result = build_morphosyntax_candidate_space(_surface_result("alpha beta ... gamma delta"))
    hypotheses = result.hypothesis_set.hypotheses
    unresolved_total = sum(len(h.unresolved_attachments) for h in hypotheses)

    assert result.hypothesis_set.ambiguity_present is True
    assert result.hypothesis_set.no_selected_winner is True
    assert len(hypotheses) > 1 or unresolved_total > 0
    assert "no_selected_winner" in result.telemetry.downstream_gate.restrictions


def test_noisy_input_keeps_honest_partial_known_without_fake_precision() -> None:
    result = build_morphosyntax_candidate_space(_surface_result("!!! ... ??"))

    assert result.partial_known is True or result.abstain is True
    assert result.hypothesis_set.no_selected_winner is True
    assert result.telemetry.ambiguity_reasons or result.partial_known_reason
