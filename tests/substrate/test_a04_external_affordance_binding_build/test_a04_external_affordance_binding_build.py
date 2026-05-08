from __future__ import annotations

from substrate.a04_external_affordance_binding import (
    A04AdmissionStatus,
    A04BindingStatus,
    A04NormalizationDecision,
    A04ObjectMaturityStatus,
    derive_a04_external_affordance_contract_view,
)
from tests.substrate.a04_external_affordance_binding_testkit import (
    A04HarnessCase,
    a04_candidate,
    a04_candidate_set,
    a04_scaffold,
    build_a04_harness_case,
)


def test_owner_import_surface_and_init_integrity() -> None:
    from substrate.a04_external_affordance_binding import (
        A04ExternalAffordanceBindingResult,
        A04ExternalAffordanceCandidateSet,
        a04_external_affordance_binding_snapshot,
        build_a04_external_affordance_binding,
    )

    assert A04ExternalAffordanceBindingResult is not None
    assert A04ExternalAffordanceCandidateSet is not None
    assert callable(a04_external_affordance_binding_snapshot)
    assert callable(build_a04_external_affordance_binding)


def test_entity_centric_binding_without_object_maturity_claim() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="entity-centric",
            candidate_set=a04_candidate_set(
                set_id="entity-centric:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:cup",
                        object_ref=None,
                        affordance_class="world_directed_action",
                        candidate_label="lift_cup",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:cup",
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="entity-centric admission",
            ),
        )
    ).a04_result
    binding = result.bindings[0]
    assert binding.binding_status is A04BindingStatus.ADMITTED
    assert binding.downstream_scope == "admitted_entity_scoped_binding"
    assert binding.object_maturity_claim_blocked is False
    assert binding.authority_preserved is True


def test_object_scaffold_intake_does_not_become_mature_object_claim() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="object-scaffold",
            candidate_set=a04_candidate_set(
                set_id="object-scaffold:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:handle",
                        object_ref="object:handle",
                        affordance_class="world_directed_action",
                        candidate_label="turn_handle",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:handle",
                        object_ref="object:handle",
                        object_maturity_status=A04ObjectMaturityStatus.SCAFFOLD_ONLY,
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="object scaffold only",
            ),
        )
    ).a04_result
    binding = result.bindings[0]
    assert binding.binding_status is A04BindingStatus.ADMITTED
    assert binding.downstream_scope == "admitted_object_scaffold_binding"
    assert binding.object_maturity_claim_blocked is True


def test_absent_scaffold_blocks_candidate() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="absent-scaffold",
            candidate_set=a04_candidate_set(
                set_id="absent-scaffold:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:unknown",
                        affordance_class="world_directed_action",
                        candidate_label="push_unknown",
                    ),
                ),
                world_scaffolds=(),
                reason="missing scaffold",
            ),
        )
    ).a04_result
    assert result.telemetry.a04_blocked_count == 1
    assert result.blocked_candidates[0].decision is A04NormalizationDecision.BLOCKED_ABSENT_SCAFFOLD


def test_authority_dropout_blocks_candidate() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="authority-dropout",
            candidate_set=a04_candidate_set(
                set_id="authority-dropout:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:door",
                        affordance_class="world_directed_action",
                        candidate_label="open_door",
                        source_authority="",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:door",
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="authority missing",
            ),
        )
    ).a04_result
    assert result.telemetry.a04_authority_missing_count == 1
    assert result.blocked_candidates[0].decision is A04NormalizationDecision.BLOCKED_NO_AUTHORITY


def test_noisy_scaffold_produces_contested_status() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="noisy-scaffold",
            candidate_set=a04_candidate_set(
                set_id="noisy-scaffold:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:panel",
                        affordance_class="world_directed_action",
                        candidate_label="press_panel",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:panel",
                        admission_status=A04AdmissionStatus.CONTESTED,
                        confidence=0.3,
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="noisy scaffold",
            ),
        )
    ).a04_result
    assert result.telemetry.a04_contested_count == 1
    assert result.contested_candidates[0].decision is A04NormalizationDecision.CONTESTED_NOISY_SCAFFOLD


def test_contradictory_world_packets_do_not_auto_promote() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="contradictory",
            candidate_set=a04_candidate_set(
                set_id="contradictory:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:lever",
                        affordance_class="world_directed_action",
                        candidate_label="pull_lever",
                        contradiction_refs=("conflict:packet",),
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:lever",
                        admission_status=A04AdmissionStatus.ADMITTED,
                        supported_affordance_classes=("world_directed_action",),
                        provenance=("packet:admit",),
                    ),
                    a04_scaffold(
                        entity_ref="entity:lever",
                        admission_status=A04AdmissionStatus.REVOKED,
                        revocation_status=True,
                        supported_affordance_classes=("world_directed_action",),
                        provenance=("packet:revoke",),
                    ),
                ),
                reason="contradictory packets",
            ),
        )
    ).a04_result
    assert result.telemetry.a04_contested_count == 1
    assert result.ledger.contradiction_count == 1
    assert (
        result.contested_candidates[0].decision
        is A04NormalizationDecision.BLOCKED_CONTRADICTORY_WORLD_PACKETS
    )


def test_unsupported_candidate_cannot_bind() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="unsupported",
            candidate_set=a04_candidate_set(
                set_id="unsupported:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:switch",
                        affordance_class="external_delivery",
                        candidate_label="deliver_package",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:switch",
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="unsupported affordance class",
            ),
        )
    ).a04_result
    assert result.telemetry.a04_blocked_count == 1
    assert result.blocked_candidates[0].decision is A04NormalizationDecision.BLOCKED_UNSUPPORTED_CANDIDATE


def test_revocation_invalidates_binding() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="revoked",
            candidate_set=a04_candidate_set(
                set_id="revoked:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:gate",
                        affordance_class="world_directed_action",
                        candidate_label="close_gate",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:gate",
                        admission_status=A04AdmissionStatus.REVOKED,
                        revocation_status=True,
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="revocation path",
            ),
        )
    ).a04_result
    assert result.telemetry.a04_revoked_count == 1
    assert result.bindings[0].binding_status is A04BindingStatus.REVOKED
    assert result.blocked_candidates[0].decision is A04NormalizationDecision.REVOKED_BINDING


def test_baseline_contrast_with_naive_string_matching() -> None:
    candidate = a04_candidate(
        candidate_id="c1",
        entity_ref="entity:panel",
        affordance_class="world_directed_action",
        candidate_label="press_panel",
        source_authority="",
    )
    naive_baseline_admits = "panel" in candidate.candidate_label
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="baseline-contrast",
            candidate_set=a04_candidate_set(
                set_id="baseline-contrast:set",
                candidates=(candidate,),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:panel",
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="baseline contrast",
            ),
        )
    ).a04_result
    assert naive_baseline_admits is True
    assert result.telemetry.a04_binding_count == 0
    assert result.blocked_candidates[0].decision is A04NormalizationDecision.BLOCKED_NO_AUTHORITY


def test_removing_authority_and_admission_degrades_result() -> None:
    admitted = build_a04_harness_case(
        A04HarnessCase(
            case_id="ablation-admitted",
            candidate_set=a04_candidate_set(
                set_id="ablation-admitted:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:drawer",
                        affordance_class="world_directed_action",
                        candidate_label="open_drawer",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:drawer",
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="authority present",
            ),
        )
    ).a04_result
    removed = build_a04_harness_case(
        A04HarnessCase(
            case_id="ablation-removed",
            candidate_set=a04_candidate_set(
                set_id="ablation-removed:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:drawer",
                        affordance_class="world_directed_action",
                        candidate_label="open_drawer",
                        source_authority="",
                    ),
                ),
                world_scaffolds=(),
                reason="authority removed",
            ),
        )
    ).a04_result
    assert admitted.telemetry.a04_binding_count == 1
    assert removed.telemetry.a04_binding_count == 0
    assert removed.telemetry.a04_consumer_ready is False


def test_contract_view_preserves_scope_and_authority_counts() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="contract-view",
            candidate_set=a04_candidate_set(
                set_id="contract-view:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:knob",
                        object_ref="object:knob",
                        affordance_class="world_directed_action",
                        candidate_label="turn_knob",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:knob",
                        object_ref="object:knob",
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="view coverage",
            ),
        )
    ).a04_result
    view = derive_a04_external_affordance_contract_view(result)
    assert view.a04_binding_count == 1
    assert view.scope_staged_scaffold_only is True
    assert view.scope_entity_binding_not_object_perception is True


def test_unknown_admission_status_is_not_promoted_to_clean_binding() -> None:
    result = build_a04_harness_case(
        A04HarnessCase(
            case_id="unknown-admission",
            candidate_set=a04_candidate_set(
                set_id="unknown-admission:set",
                candidates=(
                    a04_candidate(
                        candidate_id="c1",
                        entity_ref="entity:hinge",
                        object_ref="object:hinge",
                        affordance_class="world_directed_action",
                        candidate_label="move_hinge",
                    ),
                ),
                world_scaffolds=(
                    a04_scaffold(
                        entity_ref="entity:hinge",
                        object_ref="object:hinge",
                        admission_status=A04AdmissionStatus.UNKNOWN,
                        confidence=0.9,
                        supported_affordance_classes=("world_directed_action",),
                    ),
                ),
                reason="unknown admission should remain non-clean",
            ),
        )
    ).a04_result

    assert result.telemetry.a04_binding_count == 0
    assert result.telemetry.a04_contested_count == 1
    assert result.telemetry.a04_consumer_ready is False
    assert result.gate.consumer_ready is False
    assert result.gate.binding_packet_consumer_ready is False
    assert result.gate.authority_path_consumer_ready is True
    assert result.contested_candidates[0].decision is A04NormalizationDecision.NO_CLEAN_EXTERNAL_AFFORDANCE_CLAIM
    assert result.ledger.entries[0].decision is A04NormalizationDecision.NO_CLEAN_EXTERNAL_AFFORDANCE_CLAIM
    assert result.ledger.entries[0].status is A04BindingStatus.CONTESTED
    assert not result.bindings
