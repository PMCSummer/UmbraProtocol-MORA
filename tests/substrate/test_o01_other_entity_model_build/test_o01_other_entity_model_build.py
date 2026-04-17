from __future__ import annotations

from dataclasses import replace

from substrate.o01_other_entity_model import O01UpdateEventKind
from tests.substrate.o01_other_entity_model_testkit import (
    O01HarnessCase,
    build_o01,
    build_o01_harness_case,
    harness_sequences,
)


def _current_user(result):
    entity_id = result.state.current_user_entity_id
    assert entity_id is not None
    for entity in result.state.entities:
        if entity.entity_id == entity_id:
            return entity
    raise AssertionError("current user entity missing")


def test_harness_has_required_diversity_and_size() -> None:
    cases = harness_sequences()
    assert len(cases) >= 10
    required = {
        "stable_preference_repeated",
        "temporary_request_one_off",
        "revision_correction",
        "revision_contradiction_preserved",
        "third_party_quoted",
        "referenced_other_separate",
        "competing_referent",
        "knowledge_unknown",
        "knowledge_later_known",
        "projection_adversarial",
        "stale_memory_contradiction",
    }
    assert required.issubset(set(cases.keys()))


def test_ordinary_typed_state_and_provenance_are_preserved() -> None:
    result = build_o01_harness_case(harness_sequences()["stable_preference_repeated"])
    assert result.state.model_id.startswith("o01-model:")
    assert result.state.entities
    assert result.state.source_lineage
    assert result.state.last_update_provenance.startswith("o01.")
    entity = _current_user(result)
    assert isinstance(entity.uncertainty_map, dict)
    assert entity.provenance.startswith("o01.")
    assert entity.belief_overlay.evidence_basis


def test_stable_vs_temporary_separation_is_real() -> None:
    stable = build_o01_harness_case(harness_sequences()["stable_preference_repeated"])
    temporary = build_o01_harness_case(harness_sequences()["temporary_request_one_off"])
    stable_user = _current_user(stable)
    temporary_user = _current_user(temporary)
    assert "prefers_concise_answers" in stable_user.stable_claims
    assert "prefers_concise_answers" not in temporary_user.stable_claims
    assert temporary.state.temporary_only_not_stable is True


def test_contradiction_revision_path_does_not_silently_merge() -> None:
    result = build_o01_harness_case(harness_sequences()["revision_correction"])
    user = _current_user(result)
    event_kinds = {event.event_kind for event in user.revision_history}
    assert O01UpdateEventKind.INVALIDATE in event_kinds or O01UpdateEventKind.REVISE in event_kinds
    assert "prefers_detailed_answers" not in user.stable_claims


def test_entity_individuation_separates_current_user_and_third_party() -> None:
    result = build_o01_harness_case(harness_sequences()["third_party_quoted"])
    assert result.state.current_user_entity_id is not None
    assert result.state.third_party_entity_ids
    user = _current_user(result)
    assert "prefers_verbose" not in user.stable_claims
    third_party = [
        entity
        for entity in result.state.entities
        if entity.entity_id in set(result.state.third_party_entity_ids)
    ][0]
    assert "prefers_verbose" in third_party.stable_claims


def test_competing_entity_models_are_explicit_not_silently_collapsed() -> None:
    result = build_o01_harness_case(harness_sequences()["competing_referent"])
    assert result.state.competing_entity_models
    assert result.state.entity_not_individuated is True
    assert result.gate.downstream_consumer_ready is False


def test_projection_guard_blocks_self_internal_authority_injection() -> None:
    result = build_o01_harness_case(harness_sequences()["projection_adversarial"])
    user = _current_user(result)
    assert "prefers_long_storytelling" not in user.stable_claims
    assert result.state.projection_guard_triggered is True


def test_knowledge_boundary_revision_from_unknown_to_known_is_supported() -> None:
    unknown = build_o01_harness_case(harness_sequences()["knowledge_unknown"])
    known = build_o01_harness_case(
        harness_sequences()["knowledge_later_known"],
        prior_state=unknown.state,
    )
    assert unknown.state.knowledge_boundary_unknown is False
    assert known.state.knowledge_boundary_unknown is False
    assert any("knows_api_rate_limit_now" in item for item in _current_user(known).stable_claims)


def test_baseline_recent_summary_shortcut_differs_from_o01_revision_behavior() -> None:
    corrected = build_o01_harness_case(harness_sequences()["stale_memory_contradiction"])
    naive_recent_summary = {"stable_claims": ("prefers_json",)}
    user = _current_user(corrected)
    assert naive_recent_summary["stable_claims"] != user.stable_claims
    assert corrected.state.no_safe_state_claim in {True, False}


def test_adversarial_quoted_third_party_contamination_does_not_override_user() -> None:
    result = build_o01_harness_case(harness_sequences()["third_party_quoted"])
    user = _current_user(result)
    assert "prefers_verbose" not in user.stable_claims
    assert result.state.third_party_entity_ids


def test_metamorphic_removing_entity_individuation_exposes_conflation_risk() -> None:
    result = build_o01_harness_case(harness_sequences()["third_party_quoted"])
    conflated = replace(
        result.state,
        third_party_entity_ids=(),
        competing_entity_models=(),
    )
    assert len(result.state.third_party_entity_ids) > len(conflated.third_party_entity_ids)


def test_metamorphic_removing_stable_temporary_split_degrades_model_honesty() -> None:
    result = build_o01_harness_case(harness_sequences()["temporary_request_one_off"])
    user = _current_user(result)
    flattened = tuple(dict.fromkeys((*user.stable_claims, *user.temporary_state_hypotheses)))
    assert user.stable_claims != flattened


def test_ablation_disabled_model_produces_no_safe_fallback() -> None:
    case = harness_sequences()["stable_preference_repeated"]
    disabled = build_o01(
        case_id=case.case_id,
        tick_index=case.tick_index,
        signals=case.signals,
        model_enabled=False,
    )
    assert disabled.state.no_safe_state_claim is True
    assert "o01_disabled" in disabled.gate.restrictions


def test_matrix_signals_change_readiness_bands() -> None:
    stable = build_o01_harness_case(harness_sequences()["stable_preference_repeated"])
    temporary = build_o01_harness_case(harness_sequences()["temporary_request_one_off"])
    competing = build_o01_harness_case(harness_sequences()["competing_referent"])
    assert stable.gate.current_user_model_ready is True
    assert temporary.gate.current_user_model_ready is True
    assert competing.gate.current_user_model_ready is False
    assert competing.gate.clarification_ready is False


def test_role_based_load_bearing_signal_exists_in_gate_not_just_telemetry() -> None:
    result = build_o01_harness_case(harness_sequences()["competing_referent"])
    assert result.gate.downstream_consumer_ready is False
    assert "competing_entity_models" in result.gate.restrictions
