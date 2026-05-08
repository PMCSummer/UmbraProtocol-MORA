from __future__ import annotations

from dataclasses import replace

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickOutcome
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    a01_candidate,
    a01_candidate_set,
)
from tests.substrate.subject_tick_testkit import build_subject_tick


def _result(case_id: str, *, context: SubjectTickContext | None = None):
    return build_subject_tick(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        context=context,
    )


def _a01_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a01_affordance_ontology_cleanup_checkpoint"
    )


def _base_context() -> SubjectTickContext:
    return SubjectTickContext()


def _canonical_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:canonical",
        reason="canonical input",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:c1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:c1",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:pause_and_recover",
            ),
        ),
    )


def _granularity_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:granularity",
        reason="coarse fine relation",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:g1",
                local_label="repair_sequence",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:g1",
                preconditions=("rupture_detected",),
                primary_outcomes=("repair_progress",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("repair_open",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:repair_sequence",
                granularity_level=1,
            ),
            a01_candidate(
                candidate_id=f"{case_id}:g2",
                local_label="repair_sequence",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:g2",
                preconditions=("rupture_detected",),
                primary_outcomes=("repair_progress",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("clarify_then_repair",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:repair_sequence.step",
                granularity_level=3,
            ),
        ),
    )


def _legacy_only_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:legacy",
        reason="legacy bypass adversarial",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:l1",
                local_label="legacy_pause",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:l1",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=None,
                legacy_local_label_only=True,
            ),
        ),
    )


def _contested_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:contested",
        reason="same label precondition conflict",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:x1",
                local_label="safety_recheck",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:x1",
                preconditions=("world_signal_present",),
                primary_outcomes=("safety_verification",),
                target_channels=("world",),
                controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
                controllability_confidence=0.7,
                observation_signals=("verified_signal",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:safety_recheck.world",
            ),
            a01_candidate(
                candidate_id=f"{case_id}:x2",
                local_label="safety_recheck",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:x2",
                preconditions=("internal_alarm",),
                primary_outcomes=("safety_verification",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.7,
                observation_signals=("alarm_settled",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:safety_recheck.internal",
            ),
        ),
    )


def _deprecated_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:deprecated",
        reason="invalid assumption should downgrade validity",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:d1",
                local_label="send_update",
                affordance_class=A01AffordanceClass.COMMUNICATION_OUTPUT,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:d1",
                preconditions=("invalid_assumption",),
                primary_outcomes=("update_sent",),
                target_channels=("world",),
                controllability_class=A01ControllabilityClass.WORLD_DEPENDENT,
                controllability_confidence=0.5,
                observation_signals=("sent",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.WORLD_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:send_update",
            ),
        ),
    )


def _canonical_missing_id_hint_candidate_set(case_id: str):
    return a01_candidate_set(
        set_id=f"{case_id}:a01:set:canonical-no-hint",
        reason="canonical shape with generated ids only",
        candidates=(
            a01_candidate(
                candidate_id=f"{case_id}:z1",
                local_label="pause_and_recover",
                affordance_class=A01AffordanceClass.REPAIR_RECOVERY,
                aliases=(),
                provenance=f"tests.a01.integration:{case_id}:z1",
                preconditions=("energy_low",),
                primary_outcomes=("reduce_overload",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("calmer_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=None,
                legacy_local_label_only=False,
            ),
        ),
    )


def test_subject_tick_emits_a01_checkpoint_between_s_minimal_and_a_line() -> None:
    case_id = "rt-a01-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.s_minimal_contour_checkpoint" in ids
    assert "rt01.a01_affordance_ontology_cleanup_checkpoint" in ids
    assert "rt01.a_line_normalization_checkpoint" in ids
    assert ids.index("rt01.s_minimal_contour_checkpoint") < ids.index(
        "rt01.a01_affordance_ontology_cleanup_checkpoint"
    )
    assert ids.index("rt01.a01_affordance_ontology_cleanup_checkpoint") < ids.index(
        "rt01.a_line_normalization_checkpoint"
    )


def test_a01_require_paths_are_deterministic() -> None:
    case_id = "rt-a01-require"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=None,
            require_a01_canonical_affordance_consumer=True,
            require_a01_contested_affordance_consumer=True,
            require_a01_deprecated_affordance_consumer=True,
        ),
    )
    checkpoint = _a01_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_a01_canonical_affordance_consumer" in checkpoint.required_action
    assert "require_a01_contested_affordance_consumer" in checkpoint.required_action
    assert "require_a01_deprecated_affordance_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_same_checkpoint_envelope_can_diverge_by_typed_a01_shape() -> None:
    clean_case = "rt-a01-envelope-clean"
    granular_case = "rt-a01-envelope-granular"
    clean = _result(
        clean_case,
        context=replace(
            _base_context(),
            require_a01_canonical_affordance_consumer=True,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(clean_case),
        ),
    )
    granular = _result(
        granular_case,
        context=replace(
            _base_context(),
            require_a01_canonical_affordance_consumer=True,
            a01_raw_affordance_candidate_set=_granularity_candidate_set(granular_case),
        ),
    )
    clean_checkpoint = _a01_checkpoint(clean)
    granular_checkpoint = _a01_checkpoint(granular)
    assert clean_checkpoint.status.value == "allowed"
    assert granular_checkpoint.status.value == "allowed"
    assert clean_checkpoint.required_action == "require_a01_canonical_affordance_consumer"
    assert clean_checkpoint.required_action == granular_checkpoint.required_action
    assert clean.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert granular.state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    assert clean.downstream_gate.accepted is True
    assert granular.downstream_gate.accepted is False
    assert clean.downstream_gate.usability_class.value != granular.downstream_gate.usability_class.value


def test_a01_downstream_canonical_id_migration_blocks_legacy_only_path() -> None:
    legacy_case = "rt-a01-legacy-path"
    canonical_case = "rt-a01-canonical-path"
    legacy = _result(
        legacy_case,
        context=replace(
            _base_context(),
            require_a01_canonical_affordance_consumer=True,
            a01_raw_affordance_candidate_set=_legacy_only_candidate_set(legacy_case),
        ),
    )
    canonical = _result(
        canonical_case,
        context=replace(
            _base_context(),
            require_a01_canonical_affordance_consumer=True,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(canonical_case),
        ),
    )
    legacy_checkpoint = _a01_checkpoint(legacy)
    canonical_checkpoint = _a01_checkpoint(canonical)
    assert legacy_checkpoint.status.value == "enforced_detour"
    assert "default_a01_legacy_label_bypass_forbidden" in legacy_checkpoint.required_action
    assert canonical_checkpoint.status.value == "allowed"
    assert canonical_checkpoint.required_action == "require_a01_canonical_affordance_consumer"
    assert legacy.state.final_execution_outcome != canonical.state.final_execution_outcome


def test_disable_a01_enforcement_materially_changes_downstream_behavior() -> None:
    case_id = "rt-a01-no-bypass"
    enabled = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_legacy_only_candidate_set(case_id),
        ),
    )
    disabled_case = f"{case_id}-disabled"
    disabled = _result(
        disabled_case,
        context=replace(
            _base_context(),
            disable_a01_enforcement=True,
            a01_raw_affordance_candidate_set=_legacy_only_candidate_set(disabled_case),
        ),
    )
    enabled_checkpoint = _a01_checkpoint(enabled)
    disabled_checkpoint = _a01_checkpoint(disabled)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_a01_legacy_label_bypass_forbidden" in enabled_checkpoint.required_action
    assert disabled_checkpoint.status.value == "allowed"
    assert disabled_checkpoint.required_action == "a01_optional"
    assert enabled.state.final_execution_outcome != disabled.state.final_execution_outcome


def test_a01_contested_default_detour_is_load_bearing() -> None:
    case_id = "rt-a01-contested-default"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_contested_candidate_set(case_id),
        ),
    )
    checkpoint = _a01_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_a01_contested_canonicalization_detour" in checkpoint.required_action
    assert result.state.a01_contested_entry_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_a01_deprecated_default_detour_is_load_bearing() -> None:
    case_id = "rt-a01-deprecated-default"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_deprecated_candidate_set(case_id),
        ),
    )
    checkpoint = _a01_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_a01_deprecated_affordance_detour" in checkpoint.required_action
    assert result.state.a01_deprecated_entry_count > 0
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_same_checkpoint_action_but_canonical_id_coverage_changes_downstream_gate() -> None:
    hinted_case = "rt-a01-canonical-id-hinted"
    generated_case = "rt-a01-canonical-id-generated"
    hinted = _result(
        hinted_case,
        context=replace(
            _base_context(),
            require_a01_canonical_affordance_consumer=True,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(hinted_case),
        ),
    )
    generated = _result(
        generated_case,
        context=replace(
            _base_context(),
            require_a01_canonical_affordance_consumer=True,
            a01_raw_affordance_candidate_set=_canonical_missing_id_hint_candidate_set(
                generated_case
            ),
        ),
    )
    hinted_checkpoint = _a01_checkpoint(hinted)
    generated_checkpoint = _a01_checkpoint(generated)
    assert hinted_checkpoint.status.value == "allowed"
    assert generated_checkpoint.status.value == "allowed"
    assert hinted_checkpoint.required_action == "require_a01_canonical_affordance_consumer"
    assert generated_checkpoint.required_action == "require_a01_canonical_affordance_consumer"
    assert hinted.state.a01_canonical_id_coverage_complete is True
    assert generated.state.a01_canonical_id_coverage_complete is False
    assert hinted.downstream_gate.accepted is True
    assert generated.downstream_gate.accepted is False
