from __future__ import annotations

from substrate.a01_internal_affordance_ontology_cleanup import (
    A01AffordanceClass,
    A01ControllabilityClass,
)
from substrate.a02_capability_gap_detection import A02DemandClass
from substrate.a03_internal_tool_affordances import (
    A03AvailabilityStatus,
    A03CapabilityGapLinkageKind,
    A03ContractStatus,
    A03NormalizationDecisionType,
    A03ObservationHook,
    A03OperationBoundaryKind,
    A03RejectionReason,
    A03ToolClass,
    A03ToolFailureSignature,
    A03ToolInputSpec,
    A03ToolOutputSpec,
    derive_a03_tool_contract_view,
)
from tests.substrate.a01_internal_affordance_ontology_cleanup_testkit import (
    A01HarnessCase,
    a01_candidate,
    a01_candidate_set,
    build_a01_harness_case,
)
from tests.substrate.a02_capability_gap_detection_testkit import (
    A02HarnessCase,
    a02_demand,
    a02_demand_set,
    build_a02_harness_case,
)
from tests.substrate.a03_internal_tool_affordances_testkit import (
    A03HarnessCase,
    a03_candidate_set,
    a03_operation_candidate,
    build_a03_harness_case,
)


def _a01_result(case_id: str, candidates: tuple) -> object:
    return build_a01_harness_case(
        A01HarnessCase(
            case_id=f"{case_id}:a01",
            raw_candidate_set=a01_candidate_set(
                set_id=f"{case_id}:a01:set",
                reason=f"{case_id}:seed",
                candidates=candidates,
            ),
        )
    ).a01_result


def _typed_candidate(
    *,
    operation_ref: str,
    local_label: str,
    tool_class: A03ToolClass,
    boundary_kind: A03OperationBoundaryKind = A03OperationBoundaryKind.REUSABLE_TOOL,
    canonical_tool_id_hint: str | None = None,
    produced_output_type: str = "diagnostic_record",
    preconditions: tuple[str, ...] = ("requires_observation:internal_state",),
    required_context: tuple[str, ...] = ("mode:continue_stream",),
    completion_criteria: tuple[str, ...] = ("diagnostic_record_ready",),
    observation_signal: str = "internal_state",
    validity_hint: str = "valid",
    reliability_hint: float = 0.8,
    controllability_hint: float = 0.8,
    legacy_module_only: bool = False,
) -> object:
    return a03_operation_candidate(
        operation_ref=operation_ref,
        local_label=local_label,
        tool_class=tool_class,
        boundary_kind=boundary_kind,
        accepted_input_types=(
            A03ToolInputSpec(type_name="state_packet", required=True, shape_hint="typed_state"),
        ),
        produced_output_types=(
            A03ToolOutputSpec(type_name=produced_output_type, guaranteed=False, scope_hint="bounded"),
        ),
        required_context=required_context,
        preconditions=preconditions,
        abort_conditions=("contract_guard_triggered",),
        completion_criteria=completion_criteria,
        observation_hooks=(
            A03ObservationHook(
                hook_id=f"{operation_ref}:obs",
                signal_ref=observation_signal,
                verification_required=True,
            ),
        ),
        failure_signatures=(
            A03ToolFailureSignature(
                signature_id=f"{operation_ref}:fail",
                failure_mode="contract_guard_triggered",
                detectable=True,
            ),
        ),
        canonical_tool_id_hint=canonical_tool_id_hint,
        validity_hint=validity_hint,
        reliability_hint=reliability_hint,
        controllability_hint=controllability_hint,
        legacy_module_only=legacy_module_only,
    )


def test_owner_import_surface_and_init_integrity() -> None:
    from substrate.a03_internal_tool_affordances import (
        A03InternalOperationCandidateSet,
        A03ToolContractView,
        a03_internal_tool_affordances_snapshot,
        build_a03_internal_tool_affordances,
    )

    assert A03InternalOperationCandidateSet is not None
    assert A03ToolContractView is not None
    assert callable(a03_internal_tool_affordances_snapshot)
    assert callable(build_a03_internal_tool_affordances)


def test_reusable_tool_is_canonicalized_and_mode_helper_are_rejected() -> None:
    seed = _a01_result(
        "a03-boundary",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="internal_diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.boundary",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:internal_diagnostic_scan",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="boundary",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="boundary:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="op:tool",
                        local_label="internal_diagnostic_scan",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        canonical_tool_id_hint="a01:test:internal_diagnostic_scan",
                    ),
                    _typed_candidate(
                        operation_ref="op:mode",
                        local_label="safe_idle",
                        tool_class=A03ToolClass.ATTENTION_REDIRECTION,
                        boundary_kind=A03OperationBoundaryKind.INTERNAL_MODE,
                    ),
                    _typed_candidate(
                        operation_ref="op:helper",
                        local_label="render_internal_buffer",
                        tool_class=A03ToolClass.INSPECTION,
                        boundary_kind=A03OperationBoundaryKind.HELPER_ROUTINE,
                    ),
                ),
                reason="boundary split",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    rejected = {item.rejection_reason for item in result.cleanup_ledger.rejected_operations}
    assert result.telemetry.canonical_tool_count == 1
    assert result.telemetry.rejected_operation_count == 2
    assert rejected == {
        A03RejectionReason.MODE_NOT_TOOL,
        A03RejectionReason.HELPER_NOT_AFFORDANCE,
    }


def test_same_name_with_different_contract_remains_split() -> None:
    seed = _a01_result(
        "a03-split",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="inspect_state",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.split",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("inspection",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:inspect_state",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="split",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="split:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="split:1",
                        local_label="inspect_state",
                        tool_class=A03ToolClass.INSPECTION,
                        produced_output_type="inspection_record",
                        canonical_tool_id_hint="a01:test:inspect_state",
                    ),
                    _typed_candidate(
                        operation_ref="split:2",
                        local_label="inspect_state",
                        tool_class=A03ToolClass.INSPECTION,
                        produced_output_type="constraint_report",
                        canonical_tool_id_hint="a01:test:inspect_state",
                    ),
                ),
                reason="split by contract",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    decision_types = {item.decision_type for item in result.cleanup_ledger.normalization_decisions}
    assert result.telemetry.canonical_tool_count == 2
    assert result.telemetry.contested_tool_count == 1
    assert A03NormalizationDecisionType.SPLIT_BY_CONTRACT in decision_types


def test_true_aliases_merge_to_single_canonical_tool() -> None:
    seed = _a01_result(
        "a03-alias",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=("diag_scan",),
                provenance="tests.a03.alias",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="alias",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="alias:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="alias:1",
                        local_label="diagnostic_scan",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        canonical_tool_id_hint="a01:test:diagnostic_scan",
                    ),
                    _typed_candidate(
                        operation_ref="alias:2",
                        local_label="diag_scan",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        canonical_tool_id_hint="a01:test:diagnostic_scan",
                    ),
                ),
                reason="true alias",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    decision_types = {item.decision_type for item in result.cleanup_ledger.normalization_decisions}
    assert result.telemetry.canonical_tool_count == 1
    assert len(result.canonical_registry.aliases) == 1
    assert A03NormalizationDecisionType.MERGED_AS_ALIAS in decision_types


def test_overbroad_generic_operation_and_narrative_slogan_are_rejected() -> None:
    seed = _a01_result(
        "a03-overbroad",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.overbroad",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="overbroad",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="overbroad:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="overbroad:1",
                        local_label="reason_about_anything",
                        tool_class=A03ToolClass.ROUTE_BUILDING,
                        boundary_kind=A03OperationBoundaryKind.PSEUDO_TOOL,
                    ),
                    _typed_candidate(
                        operation_ref="overbroad:2",
                        local_label="think harder",
                        tool_class=A03ToolClass.SELF_QUERY,
                        boundary_kind=A03OperationBoundaryKind.REUSABLE_TOOL,
                    ),
                ),
                reason="overbroad rejection",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    rejected = {item.rejection_reason for item in result.cleanup_ledger.rejected_operations}
    assert A03RejectionReason.OVERBROAD_GENERIC_OPERATION in rejected
    assert A03RejectionReason.NARRATIVE_SLOGAN_WITHOUT_CONTRACT in rejected
    assert result.telemetry.overbroad_generic_operation_rejected is True


def test_incomplete_contract_does_not_become_fully_available_tool() -> None:
    seed = _a01_result(
        "a03-contract-incomplete",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.contract",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    incomplete = build_a03_harness_case(
        A03HarnessCase(
            case_id="contract-incomplete",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="contract-incomplete:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="contract:1",
                        local_label="diagnostic_scan",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        completion_criteria=(),
                    ),
                ),
                reason="contract incomplete",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    tool = incomplete.canonical_registry.canonical_tools[0]
    assert incomplete.telemetry.contract_incomplete_count == 1
    assert tool.contract_status is A03ContractStatus.CONTRACT_INCOMPLETE
    assert tool.availability_profile.status is A03AvailabilityStatus.AVAILABLE_BUT_UNVERIFIED


def test_context_resource_and_observation_shift_availability_deterministically() -> None:
    seed = _a01_result(
        "a03-availability",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.availability",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    blocked_observation = build_a03_harness_case(
        A03HarnessCase(
            case_id="availability-observation",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="availability:obs",
                candidates=(
                    _typed_candidate(
                        operation_ref="availability:obs",
                        local_label="diagnostic_scan",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        canonical_tool_id_hint="a01:test:diagnostic_scan",
                    ),
                ),
                reason="missing observation",
                available_observation_channels=(),
            ),
        )
    ).a03_result

    blocked_resource = build_a03_harness_case(
        A03HarnessCase(
            case_id="availability-resource",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="availability:resource",
                candidates=(
                    _typed_candidate(
                        operation_ref="availability:resource",
                        local_label="diagnostic_scan",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        canonical_tool_id_hint="a01:test:diagnostic_scan",
                        preconditions=("resource_available",),
                    ),
                ),
                reason="resource pressure",
                available_observation_channels=("internal_state",),
                resource_pressure=True,
            ),
        )
    ).a03_result

    degraded_reliability = build_a03_harness_case(
        A03HarnessCase(
            case_id="availability-degraded",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="availability:degraded",
                candidates=(
                    _typed_candidate(
                        operation_ref="availability:degraded",
                        local_label="diagnostic_scan",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        canonical_tool_id_hint="a01:test:diagnostic_scan",
                        reliability_hint=0.2,
                    ),
                ),
                reason="low reliability",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    assert (
        blocked_observation.canonical_registry.canonical_tools[0].availability_profile.status
        is A03AvailabilityStatus.BLOCKED_BY_MISSING_OBSERVATION
    )
    assert (
        blocked_resource.canonical_registry.canonical_tools[0].availability_profile.status
        is A03AvailabilityStatus.BLOCKED_BY_RESOURCE
    )
    assert (
        degraded_reliability.canonical_registry.canonical_tools[0].availability_profile.status
        is A03AvailabilityStatus.DEGRADED
    )


def test_a02_internal_tool_gap_linkage_differs_from_world_action_gap() -> None:
    a01_seed = _a01_result(
        "a03-a02-link",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.link",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    internal_gap = build_a02_harness_case(
        A02HarnessCase(
            case_id="a03-internal-gap",
            a01_result=a01_seed,
            demand_set=a02_demand_set(
                set_id="a03-internal-gap:set",
                demands=(
                    a02_demand(
                        demand_id="d-internal",
                        demanded_change_class=A02DemandClass.INTERNAL_TOOL,
                        demanded_scope=("simulation",),
                        target_channels=("internal",),
                    ),
                ),
                reason="internal tool missing",
            ),
        )
    ).a02_result

    world_gap = build_a02_harness_case(
        A02HarnessCase(
            case_id="a03-world-gap",
            a01_result=a01_seed,
            demand_set=a02_demand_set(
                set_id="a03-world-gap:set",
                demands=(
                    a02_demand(
                        demand_id="d-world",
                        demanded_change_class=A02DemandClass.WORLD_FACING,
                        demanded_scope=("external_delivery",),
                        target_channels=("world",),
                    ),
                ),
                reason="world action missing",
            ),
        )
    ).a02_result

    tool_set = a03_candidate_set(
        set_id="link:set",
        candidates=(
            _typed_candidate(
                operation_ref="link:tool",
                local_label="diagnostic_scan",
                tool_class=A03ToolClass.DIAGNOSTIC,
                canonical_tool_id_hint="a01:test:diagnostic_scan",
            ),
        ),
        reason="linkage",
        available_observation_channels=("internal_state",),
    )

    internal = build_a03_harness_case(
        A03HarnessCase(
            case_id="link-internal",
            a01_result=a01_seed,
            a02_result=internal_gap,
            operation_candidate_set=tool_set,
        )
    ).a03_result

    world = build_a03_harness_case(
        A03HarnessCase(
            case_id="link-world",
            a01_result=a01_seed,
            a02_result=world_gap,
            operation_candidate_set=tool_set,
        )
    ).a03_result

    assert internal.gap_linkage.linkage_kind is A03CapabilityGapLinkageKind.MISSING_INTERNAL_TOOL
    assert world.gap_linkage.linkage_kind is A03CapabilityGapLinkageKind.MISSING_WORLD_ACTION_NOT_TOOL


def test_module_name_baseline_differs_and_no_tool_inflation_occurs() -> None:
    seed = _a01_result(
        "a03-wrapper",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="inspect_state",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.wrapper",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("inspection",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:inspect_state",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="wrapper",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="wrapper:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="wrapper:tool",
                        local_label="inspect_state",
                        tool_class=A03ToolClass.INSPECTION,
                        canonical_tool_id_hint="a01:test:inspect_state",
                    ),
                    _typed_candidate(
                        operation_ref="wrapper:helper",
                        local_label="inspect_state_helper_module",
                        tool_class=A03ToolClass.INSPECTION,
                        boundary_kind=A03OperationBoundaryKind.HIDDEN_PLUMBING,
                        legacy_module_only=True,
                    ),
                    _typed_candidate(
                        operation_ref="wrapper:overbroad",
                        local_label="fix_problem",
                        tool_class=A03ToolClass.ROUTE_BUILDING,
                        boundary_kind=A03OperationBoundaryKind.PSEUDO_TOOL,
                    ),
                ),
                reason="no tool inflation",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    rejected_refs = {item.operation_ref for item in result.cleanup_ledger.rejected_operations}
    view = derive_a03_tool_contract_view(result)

    assert result.telemetry.canonical_tool_count == 1
    assert result.telemetry.rejected_operation_count == 2
    assert rejected_refs == {"wrapper:helper", "wrapper:overbroad"}
    assert view.legacy_direct_call_detected is True


def test_strategy_boundary_candidate_is_not_promoted_to_canonical_tool() -> None:
    seed = _a01_result(
        "a03-strategy-boundary",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.strategy",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="strategy-boundary",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="strategy-boundary:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="strategy:1",
                        local_label="prefer safer reasoning route",
                        tool_class=A03ToolClass.ROUTE_BUILDING,
                        boundary_kind=A03OperationBoundaryKind.STRATEGY,
                    ),
                ),
                reason="strategy boundary classification",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    assert result.telemetry.canonical_tool_count == 0
    assert result.telemetry.rejected_operation_count == 1
    assert result.cleanup_ledger.rejected_operations[0].rejection_reason is A03RejectionReason.NO_REUSABLE_OPERATION
    assert result.gate.internal_tool_consumer_ready is False


def test_latent_state_boundary_candidate_is_not_canonicalized_as_tool() -> None:
    seed = _a01_result(
        "a03-latent-state",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.latent",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="latent-state-boundary",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="latent-state-boundary:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="latent:1",
                        local_label="active uncertainty buffer",
                        tool_class=A03ToolClass.SELF_QUERY,
                        boundary_kind=A03OperationBoundaryKind.LATENT_STATE,
                    ),
                ),
                reason="latent-state boundary classification",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    assert result.telemetry.canonical_tool_count == 0
    assert result.telemetry.rejected_operation_count == 1
    assert result.cleanup_ledger.rejected_operations[0].rejection_reason is A03RejectionReason.STORED_CONTENT_NOT_TOOL
    assert result.gate.internal_tool_consumer_ready is False


def test_unknown_boundary_candidate_is_contested_and_not_fully_canonicalized() -> None:
    seed = _a01_result(
        "a03-unknown-boundary",
        (
            a01_candidate(
                candidate_id="c1",
                local_label="diagnostic_scan",
                affordance_class=A01AffordanceClass.SENSING_MONITORING,
                aliases=(),
                provenance="tests.a03.unknown",
                preconditions=("requires_observation:internal_state",),
                primary_outcomes=("diagnostic",),
                target_channels=("internal",),
                controllability_class=A01ControllabilityClass.SELF_CONTROLLED,
                controllability_confidence=0.8,
                observation_signals=("internal_state",),
                observation_verification_required=True,
                canonical_id_hint="a01:test:diagnostic_scan",
            ),
        ),
    )

    result = build_a03_harness_case(
        A03HarnessCase(
            case_id="unknown-boundary",
            a01_result=seed,
            a02_result=None,
            operation_candidate_set=a03_candidate_set(
                set_id="unknown-boundary:set",
                candidates=(
                    _typed_candidate(
                        operation_ref="unknown:1",
                        local_label="unknown internal operation marker",
                        tool_class=A03ToolClass.DIAGNOSTIC,
                        boundary_kind=A03OperationBoundaryKind.UNKNOWN_BOUNDARY,
                    ),
                ),
                reason="unknown-boundary classification",
                available_observation_channels=("internal_state",),
            ),
        )
    ).a03_result

    contested_decisions = [
        item
        for item in result.cleanup_ledger.normalization_decisions
        if item.decision_type is A03NormalizationDecisionType.CONTESTED_PENDING_CONTRACT
    ]
    assert result.telemetry.canonical_tool_count == 0
    assert result.telemetry.contested_tool_count == 1
    assert result.cleanup_ledger.rejected_operations[0].rejection_reason is A03RejectionReason.NO_REUSABLE_OPERATION
    assert len(contested_decisions) == 1
    assert result.gate.internal_tool_consumer_ready is False
