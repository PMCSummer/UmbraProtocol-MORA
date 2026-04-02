from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.morphosyntax import (
    AgreementStatus,
    build_morphosyntax_candidate_space,
)


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


def test_generation_produces_typed_candidate_space_and_telemetry() -> None:
    surface_result = _surface_result("blarf zint; glorf wint.")
    result = build_morphosyntax_candidate_space(surface_result)

    assert result.abstain is False
    assert result.hypothesis_set.hypotheses
    assert result.hypothesis_set.no_selected_winner is True
    first = result.hypothesis_set.hypotheses[0]
    assert first.token_features
    assert first.clause_graph.clauses
    assert result.telemetry.hypothesis_count == len(result.hypothesis_set.hypotheses)
    assert result.telemetry.clause_count >= len(first.clause_graph.clauses)
    assert result.telemetry.morphology_feature_count >= len(first.token_features)
    assert result.telemetry.attempted_paths


def test_clause_boundary_perturbation_changes_clause_graph_shape() -> None:
    single = build_morphosyntax_candidate_space(_surface_result("alpha beta gamma."))
    split = build_morphosyntax_candidate_space(_surface_result("alpha beta; gamma delta."))

    single_clause_count = len(single.hypothesis_set.hypotheses[0].clause_graph.clauses)
    split_clause_count = len(split.hypothesis_set.hypotheses[0].clause_graph.clauses)
    assert split_clause_count >= single_clause_count


def test_agreement_cues_are_inspectable_and_reflect_perturbation() -> None:
    matched = build_morphosyntax_candidate_space(_surface_result("we are ready."))
    mismatched = build_morphosyntax_candidate_space(_surface_result("we is ready."))

    matched_statuses = {
        cue.status for cue in matched.hypothesis_set.hypotheses[0].agreement_cues
    }
    mismatched_statuses = {
        cue.status for cue in mismatched.hypothesis_set.hypotheses[0].agreement_cues
    }
    assert matched_statuses
    assert mismatched_statuses
    assert AgreementStatus.CONFLICT in mismatched_statuses
