from __future__ import annotations

from dataclasses import fields, replace

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import (
    PerspectiveChainBundle,
    PerspectiveChainResult,
    build_discourse_provenance_chain,
    evaluate_perspective_chain_downstream_gate,
)
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


def _g03_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g04-bound", content='he said "you are tired"'),
        SourceMetadata(
            source_id="user-g04-bound",
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


def _g02_result():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g04-bound-g02", content='he said "you are tired"'),
        SourceMetadata(
            source_id="user-g04-bound-g02",
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
        {field_info.name for field_info in fields(PerspectiveChainBundle)}
        | {field_info.name for field_info in fields(PerspectiveChainResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_g04_requires_typed_g03_upstream_only() -> None:
    with pytest.raises(TypeError):
        build_discourse_provenance_chain("raw text")
    with pytest.raises(TypeError):
        build_discourse_provenance_chain(_g02_result())
    with pytest.raises(TypeError):
        evaluate_perspective_chain_downstream_gate("raw provenance")


def test_insufficient_g03_basis_forces_abstain() -> None:
    g03 = _g03_result()
    degraded = replace(g03.bundle, records=(), permission_mappings=())
    result = build_discourse_provenance_chain(degraded)
    gate = evaluate_perspective_chain_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_perspective_chain_records" in gate.restrictions
