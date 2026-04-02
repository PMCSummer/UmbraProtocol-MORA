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
        InputMaterial(material_id=f"m-reg-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


@pytest.mark.parametrize(
    ("text", "check"),
    (
        ("we do not track alpha beta", "negation"),
        ("alpha beta ... gamma delta", "attachment_ambiguity"),
        ("alpha beta; gamma delta.", "clause_split"),
        ("blarf... zint", "ellipsis_noise"),
        ("qzxv nrmpt.", "pseudo_lexical"),
        ("!!! ... ??", "short_noisy"),
    ),
)
def test_regression_corpus_keeps_load_bearing_structure(text: str, check: str) -> None:
    result = build_morphosyntax_candidate_space(_surface_result(text))
    hypotheses = result.hypothesis_set.hypotheses

    assert result.hypothesis_set.no_selected_winner is True
    if not hypotheses:
        assert result.abstain is True
        return

    first = hypotheses[0]
    assert first.token_features
    assert first.clause_graph.clauses

    if check == "negation":
        assert result.telemetry.negation_carrier_count > 0
        assert any(item.relation_hint == "negation_scope_ambiguous" for item in first.unresolved_attachments)
    elif check == "attachment_ambiguity":
        assert result.hypothesis_set.ambiguity_present is True
        assert len(hypotheses) > 1 or len(first.unresolved_attachments) > 0
    elif check == "clause_split":
        assert len(first.clause_graph.clauses) >= 2
    elif check == "ellipsis_noise":
        assert result.partial_known is True or len(first.unresolved_attachments) > 0
    elif check == "pseudo_lexical":
        assert result.telemetry.morphology_feature_count >= 2
    elif check == "short_noisy":
        assert result.partial_known is True or result.abstain is True


def test_regression_agreement_sensitive_contrast_remains_observable() -> None:
    matched = build_morphosyntax_candidate_space(_surface_result("we are ready."))
    mismatch = build_morphosyntax_candidate_space(_surface_result("we is ready."))

    matched_conflicts = sum(
        1
        for cue in matched.hypothesis_set.hypotheses[0].agreement_cues
        if cue.status.value == "conflict"
    )
    mismatch_conflicts = sum(
        1
        for cue in mismatch.hypothesis_set.hypotheses[0].agreement_cues
        if cue.status.value == "conflict"
    )
    assert mismatch_conflicts > matched_conflicts
