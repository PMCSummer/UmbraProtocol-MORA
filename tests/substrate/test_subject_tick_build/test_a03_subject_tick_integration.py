from __future__ import annotations

from dataclasses import replace

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
    A01OwnershipRelevance,
)
from substrate.a03_internal_tool_affordances import (
    A03InternalOperationCandidate,
    A03InternalOperationCandidateSet,
    A03InvocationContract,
    A03ObservationHook,
    A03OperationBoundaryKind,
    A03OperationSourceProfile,
    A03ToolClass,
    A03ToolCostProfile,
    A03ToolFailureSignature,
    A03ToolInputSpec,
    A03ToolOutputSpec,
    A03ToolSideEffectProfile,
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


def _a03_checkpoint(result):
    return next(
        item
        for item in result.state.execution_checkpoints
        if item.checkpoint_id == "rt01.a03_internal_tool_affordances_checkpoint"
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
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance=f"tests.a03.integration:{case_id}:c1",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.9,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                ownership_relevance=A01OwnershipRelevance.SELF_RELEVANT,
                canonical_id_hint=f"a01:{case_id}:internal_diagnostic_scan",
            ),
        ),
    )


def _a03_candidate_set(
    case_id: str,
    *,
    legacy_direct_call: bool = False,
    incomplete_contract: bool = False,
    canonical_hint_matches: bool = True,
) -> A03InternalOperationCandidateSet:
    produced_outputs = () if incomplete_contract else (
        A03ToolOutputSpec(type_name="diagnostic_record", guaranteed=False, scope_hint="bounded"),
    )
    completion_criteria = () if incomplete_contract else ("diagnostic_record_ready",)
    failure_signatures = () if incomplete_contract else (
        A03ToolFailureSignature(
            signature_id=f"{case_id}:a03:fail",
            failure_mode="contract_guard_triggered",
            detectable=True,
        ),
    )
    canonical_tool_id_hint = (
        f"a01:{case_id}:internal_diagnostic_scan"
        if canonical_hint_matches
        else "a01:non_matching:internal_diagnostic_scan"
    )

    candidate = A03InternalOperationCandidate(
        operation_ref=f"{case_id}:op",
        local_label="internal_diagnostic_scan",
        tool_class=A03ToolClass.DIAGNOSTIC,
        source_profile=A03OperationSourceProfile(
            source_module="tests.a03.integration",
            source_surface="tests.surface",
            provenance_refs=("tests.a03.integration",),
            source_lineage=("tests.a03.integration", case_id),
        ),
        boundary_kind=A03OperationBoundaryKind.REUSABLE_TOOL,
        invocation_contract=A03InvocationContract(
            accepted_input_types=(A03ToolInputSpec(type_name="state_packet", required=True),),
            produced_output_types=produced_outputs,
            required_context=("mode:continue_stream",),
            preconditions=("requires_observation:internal_state",),
            abort_conditions=(),
            completion_criteria=completion_criteria,
        ),
        observation_hooks=(
            A03ObservationHook(
                hook_id=f"{case_id}:a03:obs",
                signal_ref="internal_state",
                verification_required=True,
            ),
        ),
        failure_signatures=failure_signatures,
        cost_profile=A03ToolCostProfile(latency_class="bounded_tick", cost_band="low"),
        side_effect_profile=A03ToolSideEffectProfile(side_effect_refs=(), risk_band="bounded"),
        controllability_hint=0.8,
        reliability_hint=0.8,
        reuse_scope="frontier_narrow",
        required_context=("mode:continue_stream",),
        canonical_tool_id_hint=canonical_tool_id_hint,
        legacy_module_only=False,
    )

    candidates: tuple[A03InternalOperationCandidate, ...] = (candidate,)
    if legacy_direct_call:
        legacy_helper = A03InternalOperationCandidate(
            operation_ref=f"{case_id}:legacy-helper",
            local_label="diagnostic_helper_module",
            tool_class=A03ToolClass.DIAGNOSTIC,
            source_profile=A03OperationSourceProfile(
                source_module="tests.a03.integration",
                source_surface="legacy.direct.call.path",
                provenance_refs=("tests.a03.integration", "legacy_direct_call"),
                source_lineage=("tests.a03.integration", case_id, "legacy_direct_call"),
            ),
            boundary_kind=A03OperationBoundaryKind.HIDDEN_PLUMBING,
            invocation_contract=A03InvocationContract(
                accepted_input_types=(A03ToolInputSpec(type_name="state_packet", required=True),),
                produced_output_types=produced_outputs,
                required_context=("mode:continue_stream",),
                preconditions=("requires_observation:internal_state",),
                abort_conditions=(),
                completion_criteria=completion_criteria,
            ),
            observation_hooks=(
                A03ObservationHook(
                    hook_id=f"{case_id}:legacy:obs",
                    signal_ref="internal_state",
                    verification_required=True,
                ),
            ),
            failure_signatures=failure_signatures,
            cost_profile=A03ToolCostProfile(latency_class="bounded_tick", cost_band="low"),
            side_effect_profile=A03ToolSideEffectProfile(side_effect_refs=(), risk_band="bounded"),
            controllability_hint=0.8,
            reliability_hint=0.8,
            reuse_scope="frontier_narrow",
            required_context=("mode:continue_stream",),
            canonical_tool_id_hint=canonical_tool_id_hint,
            legacy_module_only=True,
        )
        candidates = (candidate, legacy_helper)

    return A03InternalOperationCandidateSet(
        candidate_set_id=f"{case_id}:a03:set",
        candidates=candidates,
        source_lineage=("tests.a03.integration", case_id),
        active_mode="continue_stream",
        resource_pressure=False,
        available_observation_channels=("internal_state",),
        reason="a03 integration candidate set",
    )


def test_subject_tick_emits_a03_checkpoint_between_a02_and_a_line() -> None:
    case_id = "rt-a03-order"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a03_operation_candidate_set=_a03_candidate_set(case_id),
        ),
    )
    ids = [item.checkpoint_id for item in result.state.execution_checkpoints]
    assert "rt01.a02_capability_gap_detection_checkpoint" in ids
    assert "rt01.a03_internal_tool_affordances_checkpoint" in ids
    assert "rt01.a_line_normalization_checkpoint" in ids
    assert ids.index("rt01.a02_capability_gap_detection_checkpoint") < ids.index(
        "rt01.a03_internal_tool_affordances_checkpoint"
    )
    assert ids.index("rt01.a03_internal_tool_affordances_checkpoint") < ids.index(
        "rt01.a_line_normalization_checkpoint"
    )


def test_a03_require_path_is_deterministic_for_contract_consumer() -> None:
    case_id = "rt-a03-require"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a03_operation_candidate_set=_a03_candidate_set(case_id, incomplete_contract=True),
            require_a03_tool_contract_consumer=True,
        ),
    )
    checkpoint = _a03_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "require_a03_tool_contract_consumer" in checkpoint.required_action
    assert result.state.final_execution_outcome == SubjectTickOutcome.REVALIDATE


def test_same_checkpoint_envelope_can_diverge_by_typed_a03_shape() -> None:
    clean_case = "rt-a03-envelope-clean"
    unsafe_case = "rt-a03-envelope-unsafe"
    clean = _result(
        clean_case,
        context=replace(
            _base_context(),
            disable_a03_enforcement=True,
            require_a03_internal_tool_consumer=True,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(clean_case),
            a03_operation_candidate_set=_a03_candidate_set(clean_case),
        ),
    )
    unsafe = _result(
        unsafe_case,
        context=replace(
            _base_context(),
            disable_a03_enforcement=True,
            require_a03_internal_tool_consumer=True,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(unsafe_case),
            a03_operation_candidate_set=_a03_candidate_set(unsafe_case, legacy_direct_call=True),
        ),
    )

    clean_checkpoint = _a03_checkpoint(clean)
    unsafe_checkpoint = _a03_checkpoint(unsafe)
    assert clean_checkpoint.status.value == "allowed"
    assert unsafe_checkpoint.status.value == "allowed"
    assert "require_a03_internal_tool_consumer" in clean_checkpoint.required_action
    assert clean_checkpoint.required_action == unsafe_checkpoint.required_action
    assert clean.state.a03_legacy_direct_call_detected is False
    assert unsafe.state.a03_legacy_direct_call_detected is True
    assert clean.downstream_gate.accepted is True
    assert unsafe.downstream_gate.accepted is False


def test_legacy_direct_call_path_is_marked_unsafe_for_narrow_contract() -> None:
    case_id = "rt-a03-legacy-direct-call"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a03_operation_candidate_set=_a03_candidate_set(case_id, legacy_direct_call=True),
        ),
    )
    checkpoint = _a03_checkpoint(result)
    assert checkpoint.status.value == "enforced_detour"
    assert "default_a03_legacy_direct_call_detour" in checkpoint.required_action
    assert result.state.a03_legacy_direct_call_detected is True
    assert result.state.final_execution_outcome != SubjectTickOutcome.CONTINUE


def test_no_explicit_a03_basis_means_no_default_a03_detour_pressure() -> None:
    case_id = "rt-a03-no-basis"
    result = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a03_operation_candidate_set=None,
        ),
    )
    checkpoint = _a03_checkpoint(result)
    assert checkpoint.status.value == "allowed"
    assert checkpoint.required_action == "a03_optional"
    assert result.state.a03_explicit_basis_present is False


def test_a03_gate_disabled_in_test_fixture_changes_behavior_materially() -> None:
    case_id = "rt-a03-gate-disabled"
    enabled = _result(
        case_id,
        context=replace(
            _base_context(),
            a01_raw_affordance_candidate_set=_canonical_candidate_set(case_id),
            a03_operation_candidate_set=_a03_candidate_set(case_id, incomplete_contract=True),
        ),
    )
    disabled = _result(
        f"{case_id}-disabled",
        context=replace(
            _base_context(),
            disable_a03_enforcement=True,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(f"{case_id}-disabled"),
            a03_operation_candidate_set=_a03_candidate_set(f"{case_id}-disabled", incomplete_contract=True),
        ),
    )
    enabled_checkpoint = _a03_checkpoint(enabled)
    disabled_checkpoint = _a03_checkpoint(disabled)
    assert enabled_checkpoint.status.value == "enforced_detour"
    assert "default_a03_contract_incomplete_detour" in enabled_checkpoint.required_action
    assert disabled_checkpoint.status.value == "allowed"
    assert disabled_checkpoint.required_action == "a03_optional"
    assert disabled_checkpoint.reason == "A03 gate disabled in test fixture"
    assert enabled.state.final_execution_outcome != disabled.state.final_execution_outcome


def test_same_checkpoint_envelope_with_canonical_id_coverage_flip_changes_downstream_gate() -> None:
    complete_case = "rt-a03-canonical-coverage-complete"
    incomplete_case = "rt-a03-canonical-coverage-incomplete"
    common_context_flags = {
        "disable_a03_enforcement": True,
        "require_a03_internal_tool_consumer": True,
    }

    complete = _result(
        complete_case,
        context=replace(
            _base_context(),
            **common_context_flags,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(complete_case),
            a03_operation_candidate_set=_a03_candidate_set(
                complete_case,
                canonical_hint_matches=True,
            ),
        ),
    )
    incomplete = _result(
        incomplete_case,
        context=replace(
            _base_context(),
            **common_context_flags,
            a01_raw_affordance_candidate_set=_canonical_candidate_set(incomplete_case),
            a03_operation_candidate_set=_a03_candidate_set(
                incomplete_case,
                canonical_hint_matches=False,
            ),
        ),
    )

    complete_checkpoint = _a03_checkpoint(complete)
    incomplete_checkpoint = _a03_checkpoint(incomplete)
    assert complete_checkpoint.checkpoint_id == incomplete_checkpoint.checkpoint_id
    assert complete_checkpoint.required_action == incomplete_checkpoint.required_action
    assert complete_checkpoint.required_action == "require_a03_internal_tool_consumer"

    assert complete.state.a03_canonical_tool_id_coverage_complete is True
    assert incomplete.state.a03_canonical_tool_id_coverage_complete is False

    assert complete.downstream_gate.accepted is True
    assert incomplete.downstream_gate.accepted is False
