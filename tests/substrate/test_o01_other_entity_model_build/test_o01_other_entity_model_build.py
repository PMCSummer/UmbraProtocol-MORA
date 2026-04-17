from __future__ import annotations

from substrate.o01_other_entity_model import O01EntitySignal, O01UpdateEventKind
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
    case = harness_sequences()["revision_correction"]
    full = build_o01_harness_case(case)
    summary_like = build_o01(
        case_id="summary_like_revision_blind",
        tick_index=case.tick_index,
        signals=tuple(
            signal for signal in case.signals if signal.relation_class.strip().lower() == "stable_claim"
        ),
    )
    full_user = _current_user(full)
    summary_user = _current_user(summary_like)
    assert "prefers_detailed_answers" not in full_user.stable_claims
    assert "prefers_detailed_answers" in summary_user.stable_claims


def test_adversarial_quoted_third_party_contamination_does_not_override_user() -> None:
    result = build_o01_harness_case(harness_sequences()["third_party_quoted"])
    user = _current_user(result)
    assert "prefers_verbose" not in user.stable_claims
    assert result.state.third_party_entity_ids


def test_metamorphic_removing_entity_individuation_exposes_conflation_risk() -> None:
    case = harness_sequences()["third_party_quoted"]
    trusted = build_o01_harness_case(case)
    mislabelled_quoted = build_o01(
        case_id="mislabelled_quoted_current_user_direct",
        tick_index=case.tick_index,
        signals=tuple(
            O01EntitySignal(
                signal_id=signal.signal_id,
                entity_id_hint=signal.entity_id_hint,
                referent_label=signal.referent_label,
                source_authority=(
                    "current_user_direct"
                    if signal.source_authority == "quoted_third_party"
                    else signal.source_authority
                ),
                relation_class=signal.relation_class,
                claim_value=signal.claim_value,
                confidence=signal.confidence,
                grounded=signal.grounded,
                quoted=signal.quoted,
                turn_index=signal.turn_index,
                provenance=signal.provenance,
                target_claim=signal.target_claim,
            )
            for signal in case.signals
        ),
    )
    trusted_user = _current_user(trusted)
    guarded_user = _current_user(mislabelled_quoted)
    assert "prefers_verbose" not in trusted_user.stable_claims
    assert "prefers_verbose" not in guarded_user.stable_claims
    assert mislabelled_quoted.state.projection_guard_triggered is False
    assert "authority_guard_triggered" in mislabelled_quoted.gate.restrictions


def test_metamorphic_removing_stable_temporary_split_degrades_model_honesty() -> None:
    one_turn_duplicate = build_o01(
        case_id="single_turn_duplicate",
        tick_index=1,
        signals=(
            O01EntitySignal(
                signal_id="dup1",
                entity_id_hint=None,
                referent_label="user",
                source_authority="current_user_direct",
                relation_class="stable_claim",
                claim_value="prefers_concise_answers",
                confidence=0.8,
                grounded=True,
                quoted=False,
                turn_index=1,
                provenance="tests.o01.dup.1",
                target_claim=None,
            ),
            O01EntitySignal(
                signal_id="dup2",
                entity_id_hint=None,
                referent_label="user",
                source_authority="current_user_direct",
                relation_class="stable_claim",
                claim_value="prefers_concise_answers",
                confidence=0.8,
                grounded=True,
                quoted=False,
                turn_index=1,
                provenance="tests.o01.dup.2",
                target_claim=None,
            ),
        ),
    )
    cross_turn_repeat = build_o01_harness_case(harness_sequences()["stable_preference_repeated"])
    one_turn_user = _current_user(one_turn_duplicate)
    repeated_user = _current_user(cross_turn_repeat)
    assert "prefers_concise_answers" not in one_turn_user.stable_claims
    assert "prefers_concise_answers" in repeated_user.stable_claims


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
