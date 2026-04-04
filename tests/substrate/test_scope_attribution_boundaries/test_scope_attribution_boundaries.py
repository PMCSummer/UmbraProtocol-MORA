from __future__ import annotations

from dataclasses import fields, replace

import pytest

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
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import (
    ApplicabilityBundle,
    ApplicabilityResult,
    build_scope_attribution,
    evaluate_applicability_downstream_gate,
)


def _runtime_graph():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g03-bound", content="you are tired"),
        SourceMetadata(
            source_id="user-g03-bound",
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
    return build_runtime_semantic_graph(grounded)


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "world_truth",
        "final_referent",
        "self_state_fact",
        "appraisal_score",
        "planner_decision",
        "narrative_commitment",
    }
    field_names = (
        {field_info.name for field_info in fields(ApplicabilityBundle)}
        | {field_info.name for field_info in fields(ApplicabilityResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_g03_requires_typed_g02_upstream_only() -> None:
    with pytest.raises(TypeError):
        build_scope_attribution("raw text")
    with pytest.raises(TypeError):
        evaluate_applicability_downstream_gate("raw applicability")


def test_insufficient_g02_basis_forces_abstain() -> None:
    runtime_graph = _runtime_graph()
    degraded_bundle = replace(runtime_graph.bundle, proposition_candidates=())
    result = build_scope_attribution(degraded_bundle)
    gate = evaluate_applicability_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_applicability_records" in gate.restrictions
