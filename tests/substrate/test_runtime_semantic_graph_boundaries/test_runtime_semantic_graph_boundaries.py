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
from substrate.grounded_semantic import build_grounded_semantic_substrate_legacy_compatibility
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import (
    RuntimeGraphBundle,
    RuntimeGraphResult,
    build_runtime_semantic_graph,
    evaluate_runtime_graph_downstream_gate,
)


def _grounded_input():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g02-bound", content="we do not track alpha"),
        SourceMetadata(
            source_id="user-g02-bound",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    return build_grounded_semantic_substrate_legacy_compatibility(dictum, utterance_surface=surface)


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "final_proposition",
        "world_truth",
        "self_applicability",
        "planner_action",
        "commitment_state",
        "policy_decision",
        "resolved_referent",
    }
    field_names = (
        {field_info.name for field_info in fields(RuntimeGraphBundle)}
        | {field_info.name for field_info in fields(RuntimeGraphResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_g02_requires_typed_g01_upstream_only() -> None:
    with pytest.raises(TypeError):
        build_runtime_semantic_graph("raw text")
    with pytest.raises(TypeError):
        evaluate_runtime_graph_downstream_gate("raw graph")


def test_insufficient_g01_basis_forces_abstain() -> None:
    grounded = _grounded_input()
    degraded = replace(
        grounded.bundle,
        phrase_scaffolds=(),
        dictum_carriers=(),
    )
    result = build_runtime_semantic_graph(degraded)
    gate = evaluate_runtime_graph_downstream_gate(result)
    assert result.abstain is True
    assert gate.accepted is False
    assert "no_usable_runtime_graph" in gate.restrictions
