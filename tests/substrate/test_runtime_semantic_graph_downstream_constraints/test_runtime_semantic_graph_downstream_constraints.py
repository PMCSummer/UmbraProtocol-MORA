from __future__ import annotations

from dataclasses import replace

from substrate.dictum_candidates import build_dictum_candidates
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import (
    CertaintyClass,
    PolarityClass,
    build_runtime_semantic_graph,
    evaluate_runtime_graph_downstream_gate,
)


def _g01(text: str, material_id: str, *, with_surface: bool = True):
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
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    return build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface if with_surface else None,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )


def test_negation_quotation_modality_change_graph_topology() -> None:
    negated = build_runtime_semantic_graph(_g01("we do not track alpha", "m-g02-down-neg"))
    quoted = build_runtime_semantic_graph(_g01('"alpha moved"', "m-g02-down-quote"))
    modal = build_runtime_semantic_graph(_g01("maybe alpha can move?", "m-g02-down-modal"))

    assert any(candidate.polarity is PolarityClass.NEGATED for candidate in negated.bundle.proposition_candidates)
    assert any(candidate.certainty_class is CertaintyClass.QUOTED for candidate in quoted.bundle.proposition_candidates)
    assert any(
        candidate.certainty_class in {CertaintyClass.HYPOTHETICAL, CertaintyClass.INTERROGATIVE}
        for candidate in modal.bundle.proposition_candidates
    )
    assert len(negated.bundle.graph_edges) != len(modal.bundle.graph_edges) or any(
        edge.edge_kind.startswith("operator_scope")
        for edge in modal.bundle.graph_edges
    )


def test_dictum_modus_split_survives_to_graph() -> None:
    result = build_runtime_semantic_graph(_g01("maybe alpha can move?", "m-g02-down-dm"))
    assert any(unit.unit_kind.value == "modus_node" for unit in result.bundle.semantic_units)
    assert result.bundle.proposition_candidates
    assert any(edge.edge_kind == "modus_to_dictum" for edge in result.bundle.graph_edges)


def test_missing_arguments_stay_unresolved_no_role_hallucination() -> None:
    result = build_runtime_semantic_graph(_g01("because alpha", "m-g02-down-miss"))
    assert result.bundle.unresolved_role_slots
    assert any(candidate.unresolved for candidate in result.bundle.proposition_candidates)


def test_ambiguity_preserved_as_graph_alternatives() -> None:
    result = build_runtime_semantic_graph(_g01("alpha... beta??", "m-g02-down-amb"))
    assert result.bundle.graph_alternatives
    gate = evaluate_runtime_graph_downstream_gate(result)
    assert "ambiguity_preserved" in gate.restrictions


def test_g01_perturbations_cause_targeted_graph_degradation() -> None:
    grounded = _g01("operator said we do not track alpha?", "m-g02-down-ablate")
    base = build_runtime_semantic_graph(grounded)

    no_source = build_runtime_semantic_graph(replace(grounded.bundle, source_anchors=()))
    no_operator = build_runtime_semantic_graph(replace(grounded.bundle, operator_carriers=()))
    no_modus = build_runtime_semantic_graph(replace(grounded.bundle, modus_carriers=()))
    no_uncertainty = build_runtime_semantic_graph(replace(grounded.bundle, uncertainty_markers=()))
    no_surface = build_runtime_semantic_graph(_g01("operator said we do not track alpha?", "m-g02-down-nosurface", with_surface=False))
    minimal = build_runtime_semantic_graph(
        replace(
            grounded.bundle,
            source_anchors=(),
            operator_carriers=(),
            modus_carriers=(),
            uncertainty_markers=(),
            low_coverage_mode=False,
            low_coverage_reasons=(),
        )
    )

    assert any(c.certainty_class is CertaintyClass.REPORTED for c in base.bundle.proposition_candidates)
    assert not any(c.certainty_class is CertaintyClass.REPORTED for c in no_source.bundle.proposition_candidates)
    assert any(c.polarity is PolarityClass.NEGATED for c in base.bundle.proposition_candidates)
    assert not any(c.polarity is PolarityClass.NEGATED for c in no_operator.bundle.proposition_candidates)
    assert any(e.edge_kind == "modus_to_dictum" for e in base.bundle.graph_edges)
    assert not any(e.edge_kind == "modus_to_dictum" for e in no_modus.bundle.graph_edges)
    assert len(no_uncertainty.bundle.graph_alternatives) <= len(base.bundle.graph_alternatives)
    assert no_surface.bundle.low_coverage_mode is True

    base_gate = evaluate_runtime_graph_downstream_gate(base)
    minimal_gate = evaluate_runtime_graph_downstream_gate(minimal)
    assert base_gate.accepted is True
    assert minimal_gate.accepted in {True, False}
    assert "downstream_authority_degraded" in minimal_gate.restrictions
