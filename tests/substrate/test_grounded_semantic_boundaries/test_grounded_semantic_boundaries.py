from __future__ import annotations

from dataclasses import fields, replace

import pytest

from substrate.dictum_candidates import DictumCandidateBundle, build_dictum_candidates
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    GroundedSemanticBundle,
    GroundedSemanticResult,
    build_grounded_semantic_substrate,
    evaluate_grounded_semantic_downstream_gate,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative


def _typed_inputs():
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g01-bound", content="we do not track alpha"),
        SourceMetadata(
            source_id="user-g01-bound",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    return surface, dictum


def test_public_models_exclude_overreach_fields() -> None:
    forbidden = {
        "final_proposition",
        "world_truth",
        "intent",
        "policy_decision",
        "resolved_reference",
        "resolved_scope",
        "communicative_intent",
        "self_significance",
    }
    field_names = (
        {field_info.name for field_info in fields(GroundedSemanticBundle)}
        | {field_info.name for field_info in fields(GroundedSemanticResult)}
    )
    assert forbidden.isdisjoint(field_names)


def test_typed_only_input_required_on_g01_critical_path() -> None:
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate_normative("raw dictum payload")
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate("raw dictum payload")
    with pytest.raises(TypeError):
        evaluate_grounded_semantic_downstream_gate("raw grounded payload")


def test_normative_g01_route_requires_typed_l05_and_l06_without_legacy_fallback() -> None:
    surface, dictum_result = _typed_inputs()
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate(
            dictum_result,
            utterance_surface=surface,
            memory_anchor_ref="m03:g01-bound-norm",
            cooperation_anchor_ref="o03:g01-bound-norm",
        )
    normative = build_grounded_semantic_substrate_normative(
        dictum_result,
        utterance_surface=surface,  # type: ignore[arg-type]
        memory_anchor_ref="m03:g01-bound-normative",
        cooperation_anchor_ref="o03:g01-bound-normative",
    )
    assert normative.bundle.legacy_surface_cue_fallback_used is False
    assert normative.bundle.normative_l05_l06_route_active is True


def test_empty_l04_bundle_forces_g01_abstain_instead_of_forced_success() -> None:
    _, dictum_result = _typed_inputs()
    empty_bundle = replace(
        dictum_result.bundle,
        dictum_candidates=(),
    )
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate_normative(empty_bundle)
