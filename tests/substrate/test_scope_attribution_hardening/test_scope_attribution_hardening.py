from __future__ import annotations

from dataclasses import replace

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
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import CertaintyClass, PolarityClass, RuntimeGraphResult, build_runtime_semantic_graph
from substrate.scope_attribution import (
    ApplicabilityUsabilityClass,
    build_scope_attribution,
    derive_applicability_contract_view,
    evaluate_applicability_downstream_gate,
)


def _runtime_graph(text: str, material_id: str) -> RuntimeGraphResult:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"{material_id}-epi", content=text),
        SourceMetadata(
            source_id=f"user-{material_id}-epi",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )
    return build_runtime_semantic_graph(grounded)


def _scope_from_text(text: str, material_id: str):
    return build_scope_attribution(_runtime_graph(text, material_id))


def _signature(result) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    source = tuple(sorted({record.source_scope_class.value for record in result.bundle.records}))
    target = tuple(sorted({record.target_scope_class.value for record in result.bundle.records}))
    applicability = tuple(sorted({record.applicability_class.value for record in result.bundle.records}))
    commitment = tuple(sorted({record.commitment_level.value for record in result.bundle.records}))
    return source, target, applicability, commitment


def test_contrastive_self_leak_vs_overblocking_balance_matrix() -> None:
    cases = (
        ("ru-self-direct", "я устал", None),
        ("ru-user-direct", "ты устал", False),
        ("ru-reported", "он сказал, что ты устал", False),
        ("ru-hypothetical", "если бы ты устал", False),
        ("ru-questioned", "ты устал?", False),
        ("ru-denial-report", "я не думаю, что ты устал", False),
        ("ru-quoted", '"я устал"', False),
    )
    for case_id, text, expected_self_allowed in cases:
        result = _scope_from_text(text, case_id)
        view = derive_applicability_contract_view(result)
        if expected_self_allowed is not None:
            assert view.self_update_allowed is expected_self_allowed
        if expected_self_allowed is False:
            assert view.self_update_blocked is True


def test_permissions_present_can_still_require_degraded_handling() -> None:
    runtime = _runtime_graph("he said you are tired", "g03-hard-perm-degraded")
    forced_low_coverage = replace(
        runtime.bundle,
        low_coverage_mode=True,
        low_coverage_reasons=tuple(dict.fromkeys((*runtime.bundle.low_coverage_reasons, "forced_low_coverage_for_hardening_test"))),
    )
    result = build_scope_attribution(forced_low_coverage)
    gate = evaluate_applicability_downstream_gate(result)
    view = derive_applicability_contract_view(result)

    assert any(record.downstream_permissions for record in result.bundle.records)
    assert gate.accepted is True
    assert gate.usability_class is ApplicabilityUsabilityClass.DEGRADED_BOUNDED
    assert "downstream_authority_degraded" in gate.restrictions
    assert view.degraded_handling_required is True


@pytest.mark.parametrize(
    ("ablation_id", "ablate"),
    (
        (
            "drop_source_scope_markers",
            lambda bundle: replace(
                bundle,
                proposition_candidates=tuple(
                    replace(
                        candidate,
                        certainty_class=(
                            CertaintyClass.ASSERTED
                            if candidate.certainty_class in {CertaintyClass.REPORTED, CertaintyClass.QUOTED}
                            else candidate.certainty_class
                        ),
                        source_scope_refs=(),
                    )
                    for candidate in bundle.proposition_candidates
                ),
            ),
        ),
        (
            "drop_commitment_markers",
            lambda bundle: replace(
                bundle,
                proposition_candidates=tuple(
                    replace(
                        candidate,
                        certainty_class=CertaintyClass.ASSERTED,
                        polarity=PolarityClass.AFFIRMATIVE,
                    )
                    for candidate in bundle.proposition_candidates
                ),
                graph_edges=tuple(
                    edge
                    for edge in bundle.graph_edges
                    if edge.edge_kind not in {"operator_scope:conditional", "operator_scope:interrogation"}
                ),
            ),
        ),
        (
            "drop_target_cues",
            lambda bundle: replace(
                bundle,
                role_bindings=tuple(
                    replace(binding, target_lexeme_hint=None)
                    for binding in bundle.role_bindings
                ),
            ),
        ),
        (
            "drop_unresolved_and_alternatives",
            lambda bundle: replace(
                bundle,
                graph_alternatives=(),
                unresolved_role_slots=(),
                ambiguity_reasons=(),
            ),
        ),
        (
            "sparse_role_graph",
            lambda bundle: replace(
                bundle,
                role_bindings=tuple(
                    replace(
                        binding,
                        target_ref=None,
                        target_lexeme_hint=None,
                        unresolved=True,
                        unresolved_reason="ablation_sparse_role_graph",
                        confidence=min(binding.confidence, 0.12),
                    )
                    for binding in bundle.role_bindings
                ),
                proposition_candidates=tuple(
                    replace(
                        candidate,
                        unresolved=True,
                        confidence=min(candidate.confidence, 0.22),
                    )
                    for candidate in bundle.proposition_candidates
                ),
                low_coverage_mode=True,
                low_coverage_reasons=tuple(dict.fromkeys((*bundle.low_coverage_reasons, "ablation_sparse_role_graph"))),
            ),
        ),
    ),
)
def test_ablation_matrix_forces_targeted_degradation(ablation_id: str, ablate) -> None:
    base_runtime = _runtime_graph('he said "you are not tired?"', f"g03-hard-ablation-base-{ablation_id}")
    base_result = build_scope_attribution(base_runtime)
    ablated_bundle = ablate(base_runtime.bundle)
    ablated_result = build_scope_attribution(ablated_bundle)
    gate = evaluate_applicability_downstream_gate(ablated_result)
    view = derive_applicability_contract_view(ablated_result)

    assert _signature(base_result) != _signature(ablated_result) or base_result.bundle.ambiguity_reasons != ablated_result.bundle.ambiguity_reasons
    assert "permissions_must_be_read" in gate.restrictions
    assert view.requires_permission_read is True
    assert view.requires_restriction_read is True

    if ablation_id == "drop_source_scope_markers":
        assert not any(record.source_scope_class.value in {"quoted", "reported"} for record in ablated_result.bundle.records)
    elif ablation_id == "drop_commitment_markers":
        assert not any(
            record.commitment_level.value in {"hypothetical", "questioned", "denied"}
            for record in ablated_result.bundle.records
        )
    elif ablation_id == "drop_target_cues":
        assert all(
            record.target_scope_class.value in {"world_directed", "unresolved"}
            for record in ablated_result.bundle.records
        )
        assert view.self_update_allowed is False
    elif ablation_id == "drop_unresolved_and_alternatives":
        assert len(ablated_result.bundle.ambiguity_reasons) <= len(base_result.bundle.ambiguity_reasons)
    elif ablation_id == "sparse_role_graph":
        assert gate.usability_class in {
            ApplicabilityUsabilityClass.DEGRADED_BOUNDED,
            ApplicabilityUsabilityClass.BLOCKED,
        }
        assert "downstream_authority_degraded" in gate.restrictions
        assert view.self_update_allowed is False


def test_shortcut_resistance_stronger_contrastive_matrix() -> None:
    cases = [
        "ты устал",
        "он сказал, что ты устал",
        "если бы ты устал",
        "ты устал?",
        "я не думаю, что ты устал",
        "я устал",
        '"я устал"',
        "he said you are tired",
        "if you are tired",
    ]

    def naive_contract_signature(text: str) -> tuple[bool, bool, bool]:
        lower = text.lower()
        has_self = any(token in f" {lower} " for token in (" i ", " я ", " me ", " myself ", " мой ", " себя "))
        has_other = any(token in f" {lower} " for token in (" you ", " ты ", " he ", " он ", " she ", " она "))
        has_uncertain = ("?" in lower) or ("if " in lower) or ("если" in lower)
        return has_self, (has_other and not has_self), has_uncertain

    mismatches = 0
    for idx, text in enumerate(cases):
        result = _scope_from_text(text, f"g03-hard-shortcut-{idx}")
        view = derive_applicability_contract_view(result)
        g03_signature = (
            view.self_update_allowed,
            view.external_only_routing,
            view.clarification_recommended,
        )
        if g03_signature != naive_contract_signature(text):
            mismatches += 1

    assert mismatches >= 3
