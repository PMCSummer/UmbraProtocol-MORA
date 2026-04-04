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
from substrate.grounded_semantic import build_grounded_semantic_substrate_legacy_compatibility
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import CertaintyClass, PolarityClass, build_runtime_semantic_graph
from substrate.scope_attribution import (
    ApplicabilityUsabilityClass,
    SourceScopeClass,
    build_scope_attribution,
    derive_applicability_contract_view,
    evaluate_applicability_downstream_gate,
)


def _g03(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    return build_scope_attribution(graph)


def _runtime_graph(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )
    return build_runtime_semantic_graph(grounded)


def test_lexically_similar_inputs_yield_different_permissions() -> None:
    direct = _g03("you are tired", "m-g03-diff-direct")
    quoted = _g03('"you are tired"', "m-g03-diff-quoted")
    hypothetical = _g03("if you are tired", "m-g03-diff-hypo")
    denied = _g03("you are not tired", "m-g03-diff-denied")
    questioned = _g03("you are tired?", "m-g03-diff-questioned")

    def _perm_set(result):
        return {perm for record in result.bundle.records for perm in record.downstream_permissions}

    assert _perm_set(direct) != _perm_set(quoted) or any(
        record.source_scope_class is SourceScopeClass.QUOTED for record in quoted.bundle.records
    )
    assert _perm_set(hypothetical) != _perm_set(direct)
    assert _perm_set(denied) != _perm_set(direct)
    assert _perm_set(questioned) != _perm_set(direct)


def test_about_self_not_equal_self_applicable_for_adversarial_cases() -> None:
    direct_self = _g03("i am tired", "m-g03-self-direct")
    quoted_self = _g03('"i am tired"', "m-g03-self-quoted")
    reported_self = _g03("he said i am tired", "m-g03-self-reported")
    hypothetical_self = _g03("if i am tired", "m-g03-self-hypo")
    denied_self = _g03("i am not tired", "m-g03-self-denied")

    assert any("allow_self_appraisal" in record.downstream_permissions for record in direct_self.bundle.records)
    assert all("allow_self_appraisal" not in record.downstream_permissions for record in quoted_self.bundle.records)
    assert all("allow_self_appraisal" not in record.downstream_permissions for record in reported_self.bundle.records)
    assert all("allow_self_appraisal" not in record.downstream_permissions for record in hypothetical_self.bundle.records)
    assert all("allow_self_appraisal" not in record.downstream_permissions for record in denied_self.bundle.records)


def test_mixed_unresolved_cases_preserve_conservative_permissions() -> None:
    mixed_case = _g03("you and i are tired", "m-g03-mixed")
    unresolved_case = _g03("там это устало", "m-g03-unresolved")
    assert mixed_case.bundle.ambiguity_reasons or any(
        "recommend_clarification" in record.downstream_permissions for record in mixed_case.bundle.records
    )
    assert unresolved_case.bundle.ambiguity_reasons or any(
        "recommend_clarification" in record.downstream_permissions for record in unresolved_case.bundle.records
    )
    assert any("block_self_state_update" in record.downstream_permissions for record in mixed_case.bundle.records) or any(
        "block_self_state_update" in record.downstream_permissions for record in unresolved_case.bundle.records
    )
    assert not all("allow_self_appraisal" in record.downstream_permissions for record in unresolved_case.bundle.records)


def test_downstream_contract_obedience_uses_only_g03_output() -> None:
    result = _g03("he said you are tired", "m-g03-contract")
    view = derive_applicability_contract_view(result)
    assert view.self_update_allowed is False
    assert view.self_update_blocked is True
    assert view.external_only_routing is True
    assert view.requires_permission_read is True
    assert view.requires_restriction_read is True
    assert "permissions_must_be_read" in view.restrictions
    assert view.strong_self_state_commitment_permitted is False


def test_context_only_outputs_are_explicitly_degraded_not_normalized() -> None:
    result = _g03("if you are tired", "m-g03-context-only")
    gate = evaluate_applicability_downstream_gate(result)
    view = derive_applicability_contract_view(result)

    assert gate.accepted is True
    assert gate.usability_class is ApplicabilityUsabilityClass.DEGRADED_BOUNDED
    assert "bounded_context_only_output" in gate.restrictions
    assert "downstream_authority_degraded" in gate.restrictions
    assert view.context_only_mode is True
    assert view.degraded_handling_required is True
    assert view.self_update_allowed is False
    assert view.self_update_blocked is True


def test_legitimate_direct_self_signal_not_systemically_overblocked() -> None:
    direct_self = _g03("i am tired", "m-g03-legit-self")
    view = derive_applicability_contract_view(direct_self)
    assert any("allow_self_appraisal" in record.downstream_permissions for record in direct_self.bundle.records)
    assert view.self_update_allowed is True
    assert view.context_only_mode is False
    assert view.strong_self_state_commitment_permitted is False


def test_generic_second_person_stays_bounded_and_never_shortcuts_to_self_update() -> None:
    generic = _g03("when you are tired you rest", "m-g03-generic-second-person")
    rhetorical = _g03("you are tired, right?", "m-g03-rhetorical-question")
    vocative_like = _g03("you, listen, are tired?", "m-g03-vocative-like")

    for result in (generic, rhetorical, vocative_like):
        gate = evaluate_applicability_downstream_gate(result)
        view = derive_applicability_contract_view(result)
        assert view.self_update_allowed is False
        assert view.self_update_blocked is True
        assert "no_truth_upgrade" in gate.restrictions
        assert "permissions_must_be_read" in gate.restrictions


def test_ablation_from_g02_structure_causes_targeted_g03_degradation() -> None:
    base = _g03("he said you are not tired?", "m-g03-ablate-base")
    raw_runtime = _runtime_graph("he said you are not tired?", "m-g03-ablate-runtime")
    no_source_tags = replace(
        raw_runtime.bundle,
        proposition_candidates=tuple(
            replace(
                candidate,
                certainty_class=CertaintyClass.ASSERTED
                if candidate.certainty_class in {CertaintyClass.REPORTED, CertaintyClass.QUOTED}
                else candidate.certainty_class,
                source_scope_refs=(),
            )
            for candidate in raw_runtime.bundle.proposition_candidates
        ),
    )
    no_operator_tags = replace(
        no_source_tags,
        proposition_candidates=tuple(
            replace(
                candidate,
                polarity=PolarityClass.AFFIRMATIVE,
                certainty_class=CertaintyClass.ASSERTED
                if candidate.certainty_class in {CertaintyClass.INTERROGATIVE, CertaintyClass.HYPOTHETICAL}
                else candidate.certainty_class,
            )
            for candidate in no_source_tags.proposition_candidates
        ),
    )
    no_target_cues = replace(
        no_operator_tags,
        role_bindings=tuple(
            replace(binding, target_lexeme_hint=None)
            for binding in no_operator_tags.role_bindings
        ),
    )
    degraded = build_scope_attribution(no_target_cues)
    gate = evaluate_applicability_downstream_gate(degraded)

    assert any("allow_external_model_update" in record.downstream_permissions for record in base.bundle.records)
    assert gate.usability_class in {
        ApplicabilityUsabilityClass.DEGRADED_BOUNDED,
        ApplicabilityUsabilityClass.BLOCKED,
    }
    assert "downstream_authority_degraded" in gate.restrictions
    assert "self_state_update_blocked" in gate.restrictions
    assert "permissions_must_be_read" in gate.restrictions


def test_shortcut_falsifier_simple_pronoun_heuristic_not_equivalent_to_g03() -> None:
    cases = [
        "i am tired",
        '"i am tired"',
        "he said i am tired",
        "if i am tired",
        "i am not tired",
        "you are tired",
    ]

    def naive_self_update(text: str) -> bool:
        lower = text.lower()
        return (" i " in f" {lower} " or " я " in f" {lower} ")

    mismatches = 0
    for idx, text in enumerate(cases):
        result = _g03(text, f"m-g03-shortcut-{idx}")
        g03_allows = any("allow_self_appraisal" in record.downstream_permissions for record in result.bundle.records)
        if g03_allows != naive_self_update(text):
            mismatches += 1

    assert mismatches >= 2
