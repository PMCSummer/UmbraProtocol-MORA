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


def test_negation_carriers_stay_structurally_visible() -> None:
    result = build_morphosyntax_candidate_space(_surface_result("я не вижу цель и выход"))

    clause_nodes = result.hypothesis_set.hypotheses[0].clause_graph.clauses
    assert any(clause.negation_carrier_ids for clause in clause_nodes)
    assert result.telemetry.negation_carrier_count > 0


def test_negation_scope_ambiguity_emits_unresolved_attachment() -> None:
    result = build_morphosyntax_candidate_space(_surface_result("we do not track alpha beta"))
    unresolved = result.hypothesis_set.hypotheses[0].unresolved_attachments

    assert any(item.relation_hint == "negation_scope_ambiguous" for item in unresolved)
