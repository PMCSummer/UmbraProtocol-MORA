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
    GraphUsabilityClass,
    PolarityClass,
    RuntimeCompletenessClass,
    RuntimeSourceMode,
    build_runtime_semantic_graph,
    derive_runtime_graph_contract_view,
    evaluate_runtime_graph_downstream_gate,
)


def _g02(text: str, material_id: str, *, with_surface: bool = True):
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
    grounded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface if with_surface else None,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )
    return build_runtime_semantic_graph(grounded)


def test_contract_view_distinguishes_source_negation_modality_and_completeness() -> None:
    asserted = derive_runtime_graph_contract_view(_g02("we track alpha", "m-g02-role-asserted"))
    quoted = derive_runtime_graph_contract_view(_g02('"alpha moved"', "m-g02-role-quoted"))
    reported = derive_runtime_graph_contract_view(_g02("operator said alpha moved", "m-g02-role-reported"))
    negated = derive_runtime_graph_contract_view(_g02("we do not track alpha", "m-g02-role-negated"))
    modal = derive_runtime_graph_contract_view(_g02("maybe alpha can move?", "m-g02-role-modal"))
    incomplete = derive_runtime_graph_contract_view(_g02("because alpha", "m-g02-role-incomplete"))

    assert asserted.source_mode is RuntimeSourceMode.ASSERTED
    assert quoted.source_mode in {RuntimeSourceMode.QUOTED, RuntimeSourceMode.MIXED}
    assert reported.source_mode is RuntimeSourceMode.REPORTED
    assert negated.negation_present is True
    assert modal.modality_or_interrogative_present is True
    assert incomplete.completeness_class is RuntimeCompletenessClass.INCOMPLETE


def test_contract_view_forces_restriction_reading_and_no_settlement_claim() -> None:
    view = derive_runtime_graph_contract_view(_g02("we do not track alpha", "m-g02-role-restrict"))
    assert view.requires_restriction_read is True
    assert view.strong_semantic_settlement_permitted is False
    assert "no_final_semantic_closure" in view.restrictions


def test_ablation_source_structure_breaks_source_distinction() -> None:
    base_result = _g02("operator said alpha moved", "m-g02-role-ablate-source")
    base_view = derive_runtime_graph_contract_view(base_result)
    ablated_candidates = tuple(
        replace(
            candidate,
            source_scope_refs=(),
            certainty_class=CertaintyClass.ASSERTED
            if candidate.certainty_class in {CertaintyClass.QUOTED, CertaintyClass.REPORTED}
            else candidate.certainty_class,
        )
        for candidate in base_result.bundle.proposition_candidates
    )
    ablated_bundle = replace(base_result.bundle, proposition_candidates=ablated_candidates)
    ablated_view = derive_runtime_graph_contract_view(ablated_bundle)
    assert base_view.source_mode is RuntimeSourceMode.REPORTED
    assert ablated_view.source_mode is RuntimeSourceMode.ASSERTED


def test_ablation_operator_propagation_breaks_negation_and_modality_distinction() -> None:
    base_result = _g02("we do not track alpha?", "m-g02-role-ablate-op")
    base_view = derive_runtime_graph_contract_view(base_result)
    ablated_candidates = tuple(
        replace(
            candidate,
            polarity=PolarityClass.AFFIRMATIVE,
            certainty_class=CertaintyClass.ASSERTED
            if candidate.certainty_class in {CertaintyClass.HYPOTHETICAL, CertaintyClass.INTERROGATIVE}
            else candidate.certainty_class,
        )
        for candidate in base_result.bundle.proposition_candidates
    )
    ablated_edges = tuple(edge for edge in base_result.bundle.graph_edges if not edge.edge_kind.startswith("operator_scope"))
    ablated_bundle = replace(
        base_result.bundle,
        proposition_candidates=ablated_candidates,
        graph_edges=ablated_edges,
    )
    ablated_view = derive_runtime_graph_contract_view(ablated_bundle)
    assert base_view.negation_present is True
    assert base_view.modality_or_interrogative_present is True
    assert ablated_view.negation_present is False
    assert ablated_view.modality_or_interrogative_present is False


def test_ablation_dictum_modus_links_breaks_modus_distinction() -> None:
    base_result = _g02("maybe alpha can move?", "m-g02-role-ablate-modus")
    base_view = derive_runtime_graph_contract_view(base_result)
    ablated_units = tuple(unit for unit in base_result.bundle.semantic_units if unit.unit_kind.value != "modus_node")
    ablated_edges = tuple(edge for edge in base_result.bundle.graph_edges if edge.edge_kind != "modus_to_dictum")
    ablated_bundle = replace(base_result.bundle, semantic_units=ablated_units, graph_edges=ablated_edges)
    ablated_view = derive_runtime_graph_contract_view(ablated_bundle)
    assert base_view.dictum_modus_linked is True
    assert ablated_view.dictum_modus_linked is False


def test_ablation_remove_alternatives_and_unresolved_masks_ambiguity_surface() -> None:
    base_result = _g02("alpha... beta??", "m-g02-role-ablate-amb")
    base_view = derive_runtime_graph_contract_view(base_result)
    cleaned_candidates = tuple(
        replace(candidate, unresolved=False, confidence=max(candidate.confidence, 0.6))
        for candidate in base_result.bundle.proposition_candidates
    )
    cleaned_bundle = replace(
        base_result.bundle,
        graph_alternatives=(),
        unresolved_role_slots=(),
        ambiguity_reasons=(),
        proposition_candidates=cleaned_candidates,
    )
    cleaned_view = derive_runtime_graph_contract_view(cleaned_bundle)
    assert base_view.ambiguity_preserved is True
    assert cleaned_view.ambiguity_preserved is False


def test_accepted_true_can_still_be_degraded_and_not_settled() -> None:
    result = _g02("we track alpha", "m-g02-role-degraded")
    degraded_bundle = replace(
        result.bundle,
        graph_alternatives=(),
        low_coverage_mode=True,
        low_coverage_reasons=("manual_degraded_case",),
    )
    gate = evaluate_runtime_graph_downstream_gate(degraded_bundle)
    view = derive_runtime_graph_contract_view(degraded_bundle)
    assert gate.accepted is True
    assert gate.usability_class is GraphUsabilityClass.DEGRADED_BOUNDED
    assert "downstream_authority_degraded" in gate.restrictions
    assert view.strong_semantic_settlement_permitted is False


def test_g01_source_operator_perturbation_changes_g02_structure() -> None:
    full = _g02("operator said we do not track alpha?", "m-g02-role-perturb-full")
    no_surface = _g02("operator said we do not track alpha?", "m-g02-role-perturb-nosurface", with_surface=False)
    assert len(full.bundle.graph_edges) != len(no_surface.bundle.graph_edges) or full.bundle.low_coverage_mode != no_surface.bundle.low_coverage_mode
    assert any(c.certainty_class is CertaintyClass.REPORTED for c in full.bundle.proposition_candidates)
    assert not any(c.certainty_class is CertaintyClass.REPORTED for c in no_surface.bundle.proposition_candidates)
