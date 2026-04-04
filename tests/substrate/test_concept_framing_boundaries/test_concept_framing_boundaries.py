from __future__ import annotations

from dataclasses import fields, replace

import pytest

from substrate.concept_framing import (
    ConceptFramingBundle,
    ConceptFramingResult,
    build_concept_framing,
    evaluate_concept_framing_downstream_gate,
)
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
from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import build_semantic_acquisition


def _g05_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g06-bound", content='he said "you are tired"'),
        SourceMetadata(
            source_id="user-g06-bound",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate(dictum, utterance_surface=surface)
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    perspective = build_discourse_provenance_chain(applicability)
    return build_semantic_acquisition(perspective)


def _g04_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g06-bound-g04", content='he said "you are tired"'),
        SourceMetadata(
            source_id="user-g06-bound-g04",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate(dictum, utterance_surface=surface)
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "world_truth",
        "final_referent",
        "self_state_fact",
        "planner_decision",
        "policy_decision",
        "appraisal_commitment",
    }
    field_names = (
        {field_info.name for field_info in fields(ConceptFramingBundle)}
        | {field_info.name for field_info in fields(ConceptFramingResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_g06_requires_typed_g05_upstream_only() -> None:
    with pytest.raises(TypeError):
        build_concept_framing("raw text")
    with pytest.raises(TypeError):
        build_concept_framing(_g04_result())
    with pytest.raises(TypeError):
        evaluate_concept_framing_downstream_gate("raw framing")


def test_insufficient_g05_basis_forces_abstain() -> None:
    g05 = _g05_result()
    degraded = replace(g05.bundle, acquisition_records=(), cluster_links=())
    result = build_concept_framing(degraded)
    gate = evaluate_concept_framing_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_framing_records" in gate.restrictions
