from __future__ import annotations

from dataclasses import fields, replace

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import build_grounded_semantic_substrate_legacy_compatibility
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import (
    SemanticAcquisitionBundle,
    SemanticAcquisitionResult,
    build_semantic_acquisition,
    evaluate_semantic_acquisition_downstream_gate,
)


def _g04_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g05-bound", content='he said "you are tired"'),
        SourceMetadata(
            source_id="user-g05-bound",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate_legacy_compatibility(dictum, utterance_surface=surface)
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


def _g03_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g05-bound-g03", content='he said "you are tired"'),
        SourceMetadata(
            source_id="user-g05-bound-g03",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate_legacy_compatibility(dictum, utterance_surface=surface)
    graph = build_runtime_semantic_graph(grounded)
    return build_scope_attribution(graph)


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "world_truth",
        "final_referent",
        "self_state_fact",
        "planner_decision",
        "narrative_commitment",
        "memory_policy_decision",
    }
    field_names = (
        {field_info.name for field_info in fields(SemanticAcquisitionBundle)}
        | {field_info.name for field_info in fields(SemanticAcquisitionResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_g05_requires_typed_g04_upstream_only() -> None:
    with pytest.raises(TypeError):
        build_semantic_acquisition("raw text")
    with pytest.raises(TypeError):
        build_semantic_acquisition(_g03_result())
    with pytest.raises(TypeError):
        evaluate_semantic_acquisition_downstream_gate("raw acquisition")


def test_insufficient_g04_basis_forces_abstain() -> None:
    g04 = _g04_result()
    degraded = replace(
        g04.bundle,
        wrapped_propositions=(),
        chain_records=(),
        commitment_lineages=(),
    )
    result = build_semantic_acquisition(degraded)
    gate = evaluate_semantic_acquisition_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_provisional_acquisitions" in gate.restrictions
