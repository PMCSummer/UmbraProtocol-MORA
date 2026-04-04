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
    build_grounded_semantic_substrate_legacy_compatibility,
    evaluate_grounded_semantic_downstream_gate,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space


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
        build_grounded_semantic_substrate_legacy_compatibility("raw dictum payload")
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate("raw dictum payload")
    with pytest.raises(TypeError):
        evaluate_grounded_semantic_downstream_gate("raw grounded payload")


def test_normative_g01_route_requires_typed_l05_and_l06_or_explicit_compat_mode() -> None:
    surface, dictum_result = _typed_inputs()
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate(
            dictum_result,
            utterance_surface=surface,
            memory_anchor_ref="m03:g01-bound-norm",
            cooperation_anchor_ref="o03:g01-bound-norm",
        )
    compat = build_grounded_semantic_substrate_legacy_compatibility(
        dictum_result,
        utterance_surface=surface,
        memory_anchor_ref="m03:g01-bound-compat",
        cooperation_anchor_ref="o03:g01-bound-compat",
    )
    assert compat.bundle.legacy_surface_cue_fallback_used is True
    assert compat.bundle.normative_l05_l06_route_active is False


def test_empty_l04_bundle_forces_g01_abstain_instead_of_forced_success() -> None:
    _, dictum_result = _typed_inputs()
    empty_bundle = replace(
        dictum_result.bundle,
        dictum_candidates=(),
    )
    result = build_grounded_semantic_substrate_legacy_compatibility(empty_bundle)
    gate = evaluate_grounded_semantic_downstream_gate(result)
    assert result.abstain is True
    assert result.partial_known is True
    assert result.no_final_semantic_resolution is True
    assert gate.accepted is False
    assert "no_usable_scaffold" in gate.restrictions
