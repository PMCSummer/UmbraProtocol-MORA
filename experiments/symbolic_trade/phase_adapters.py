from __future__ import annotations

from dataclasses import dataclass

from .models import CounterpartSignalKind, SignalAuthority, SubjectVisiblePacket
from .packets import packet_to_w01_world_packet
from .subject_trace import PhaseAdapterInput, PhaseAdapterOutput


@dataclass(slots=True)
class AdapterState:
    seen_claim_counts: dict[tuple[str, str], int]


def _claim_key(packet: SubjectVisiblePacket) -> tuple[str, str] | None:
    if packet.resource_kind is None or packet.reported_level is None:
        return None
    return packet.resource_kind.value, packet.reported_level.value


def adapt_w01(packet: SubjectVisiblePacket, *, trace_id: str, step_index: int) -> tuple[PhaseAdapterInput, PhaseAdapterOutput]:
    adapter_source = "adapter_projection"
    reason_codes: list[str] = []
    limitations: list[str] = []
    try:
        packet_to_w01_world_packet(packet, sequence=step_index)
        reason_codes.append("w01_packet_shape_compatible")
        adapter_source = "real_surface_compatible_projection"
    except Exception:
        limitations.append("w01_shape_projection_fallback")

    uncertainty = ["claim_not_fact"] if packet.claim_not_fact_marker else []
    if not packet.hidden_truth_excluded:
        reason_codes.append("hidden_truth_leak_detected")
        status = "rejected"
        uncertainty.append("visibility_violation")
    elif packet.source_authority is SignalAuthority.COUNTERPART_CLAIM:
        status = "admitted_with_uncertainty"
        reason_codes.append("counterpart_claim_admitted_as_scaffold")
    elif packet.signal_kind is CounterpartSignalKind.CONTRADICTION:
        status = "contested"
        reason_codes.append("contradictory_signal_detected")
    else:
        status = "admitted"
        reason_codes.append("observed_event_admitted")

    input_obj = PhaseAdapterInput(
        trace_id=trace_id,
        phase_code="W01",
        input_refs=(f"packet:{packet.packet_id}",),
        source_packet_ids=(packet.packet_id,),
        adapter_source=adapter_source,
    )
    output_obj = PhaseAdapterOutput(
        trace_id=trace_id,
        phase_code="W01",
        output_refs=(f"w01_admission:{status}",),
        decision_status=status,
        reason_codes=tuple(reason_codes),
        uncertainty_markers=tuple(uncertainty),
        prohibited_claims=("no_counterpart_inventory_fact", "no_trade_intent_fact"),
        downstream_permission_delta=("may_use_world_scaffold", "must_preserve_claim_boundary"),
        execution_prohibited=True,
        adapter_limitations=tuple(limitations),
    )
    return input_obj, output_obj


def adapt_w02(packet: SubjectVisiblePacket, *, trace_id: str, state: AdapterState) -> tuple[PhaseAdapterInput, PhaseAdapterOutput]:
    key = _claim_key(packet)
    support = 0
    if key is not None and packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM:
        state.seen_claim_counts[key] = state.seen_claim_counts.get(key, 0) + 1
        support = state.seen_claim_counts[key]

    if support >= 2:
        status = "provisional_repeated_pattern"
        reasons = ("repeated_visible_claim_pattern",)
        uncertainty = ("still_unverified_counterpart_truth",)
    elif support == 1:
        status = "single_claim_scaffold_only"
        reasons = ("one_shot_not_regularized",)
        uncertainty = ("insufficient_support_for_regularity",)
    else:
        status = "no_candidate"
        reasons = ("no_regular_pattern_signal",)
        uncertainty = ("limited_observability",)

    input_obj = PhaseAdapterInput(
        trace_id=trace_id,
        phase_code="W02",
        input_refs=(f"packet:{packet.packet_id}",),
        source_packet_ids=(packet.packet_id,),
        adapter_source="adapter_projection",
    )
    output_obj = PhaseAdapterOutput(
        trace_id=trace_id,
        phase_code="W02",
        output_refs=(f"w02_pattern:{status}",),
        decision_status=status,
        reason_codes=reasons,
        uncertainty_markers=uncertainty,
        prohibited_claims=("no_one_shot_mature_regularity",),
        downstream_permission_delta=("bounded_regularity_candidate_only",),
        execution_prohibited=True,
        adapter_limitations=("no_full_subject_tick_execution",),
    )
    return input_obj, output_obj


def adapt_w03(packet: SubjectVisiblePacket, *, trace_id: str, state: AdapterState) -> tuple[PhaseAdapterInput, PhaseAdapterOutput]:
    key = _claim_key(packet)
    support = state.seen_claim_counts.get(key, 0) if key else 0
    if support >= 2:
        status = "bounded_prior_candidate"
        reasons = ("w02_support_threshold_met",)
        uncertainty = ("counterpart_claim_not_world_truth",)
    else:
        status = "insufficient_support"
        reasons = ("no_schema_from_single_claim",)
        uncertainty = ("support_not_sufficient",)

    input_obj = PhaseAdapterInput(
        trace_id=trace_id,
        phase_code="W03",
        input_refs=(f"w02_support:{support}",),
        source_packet_ids=(packet.packet_id,),
        adapter_source="adapter_projection",
    )
    output_obj = PhaseAdapterOutput(
        trace_id=trace_id,
        phase_code="W03",
        output_refs=(f"w03_candidate:{status}",),
        decision_status=status,
        reason_codes=reasons,
        uncertainty_markers=uncertainty,
        prohibited_claims=("no_trade_schema_from_language_prior_alone", "no_mutual_benefit_claim"),
        downstream_permission_delta=("bounded_prior_only",),
        execution_prohibited=True,
        adapter_limitations=("support_proxied_from_visible_packets",),
    )
    return input_obj, output_obj


def adapt_w04(packet: SubjectVisiblePacket, *, trace_id: str) -> tuple[PhaseAdapterInput, PhaseAdapterOutput]:
    reasons: list[str] = []
    uncertainty: list[str] = []
    permissions: list[str] = ["action_authorization_granted:false"]
    if packet.aperture_state.value == "blocked" or packet.signal_kind is CounterpartSignalKind.BLOCKED:
        status = "blocked"
        reasons.extend(("aperture_blocked", "must_revalidate_before_use"))
        permissions.extend(("may_deploy_candidate:false", "must_revalidate:true"))
    elif packet.signal_kind is CounterpartSignalKind.CONTRADICTION:
        status = "revalidate_required"
        reasons.append("contradictory_signal_requires_revalidation")
        uncertainty.append("contested_signal")
        permissions.extend(("may_deploy_candidate:false", "must_revalidate:true"))
    elif packet.signal_kind is CounterpartSignalKind.RESOURCE_STATUS_CLAIM:
        status = "hint_only"
        reasons.append("counterpart_claim_hint_only")
        uncertainty.append("claim_not_fact")
        permissions.extend(("may_deploy_candidate:false", "may_use_as_hint_only:true"))
    else:
        status = "bounded_applicability_candidate"
        reasons.append("observed_event_bounded_applicability")
        permissions.extend(("may_deploy_candidate:true", "must_preserve_hard_constraints:true"))

    input_obj = PhaseAdapterInput(
        trace_id=trace_id,
        phase_code="W04",
        input_refs=(f"signal:{packet.signal_kind.value}", f"aperture:{packet.aperture_state.value}"),
        source_packet_ids=(packet.packet_id,),
        adapter_source="adapter_projection",
    )
    output_obj = PhaseAdapterOutput(
        trace_id=trace_id,
        phase_code="W04",
        output_refs=(f"w04_decision:{status}",),
        decision_status=status,
        reason_codes=tuple(reasons),
        uncertainty_markers=tuple(uncertainty),
        prohibited_claims=("no_action_selection", "no_usefulness_as_permission"),
        downstream_permission_delta=tuple(permissions),
        execution_prohibited=True,
        adapter_limitations=("no_policy_execution",),
    )
    return input_obj, output_obj


def adapt_w05(packet: SubjectVisiblePacket, *, trace_id: str, w04_status: str) -> tuple[PhaseAdapterInput, PhaseAdapterOutput]:
    base_reasons = ("desired_predicted_observed_permitted_separated",)
    base_delta = ("must_not_execute_update:true", "execution_authorization_granted:false")
    if w04_status in {"blocked", "revalidate_required"}:
        status = "permitted_channel_blocked"
        reasons = base_reasons + ("w04_boundary_blocks_clean_injection",)
        uncertainty = ("permission_block",)
        delta = base_delta + ("may_consider_update:false",)
    elif packet.signal_kind is CounterpartSignalKind.CONTRADICTION:
        status = "mismatch_routed"
        reasons = base_reasons + ("predicted_vs_observed_mismatch",)
        uncertainty = ("contested_observation",)
        delta = base_delta + ("may_consider_update:true",)
    else:
        status = "bounded_injection"
        reasons = base_reasons + ("bounded_prior_injection_candidate",)
        uncertainty = ()
        delta = base_delta + ("may_consider_update:true",)

    input_obj = PhaseAdapterInput(
        trace_id=trace_id,
        phase_code="W05",
        input_refs=(f"w04_status:{w04_status}", f"signal:{packet.signal_kind.value}"),
        source_packet_ids=(packet.packet_id,),
        adapter_source="adapter_projection",
    )
    output_obj = PhaseAdapterOutput(
        trace_id=trace_id,
        phase_code="W05",
        output_refs=(f"w05_route:{status}",),
        decision_status=status,
        reason_codes=reasons,
        uncertainty_markers=uncertainty,
        prohibited_claims=("desired_not_evidence", "predicted_utility_not_permission"),
        downstream_permission_delta=delta,
        execution_prohibited=True,
        adapter_limitations=("no_learning_execution",),
    )
    return input_obj, output_obj


def adapt_w06(packet: SubjectVisiblePacket, *, trace_id: str, w05_status: str) -> tuple[PhaseAdapterInput, PhaseAdapterOutput]:
    reasons: list[str] = []
    uncertainty: list[str] = []
    delta: list[str] = [
        "must_not_execute_correction:true",
        "correction_candidate_created:true" if w05_status in {"mismatch_routed", "permitted_channel_blocked"} else "correction_candidate_created:false",
        "execution_prohibited:true",
        "correction_executed:false",
    ]

    if packet.signal_kind is CounterpartSignalKind.CONTRADICTION:
        status = "retain_unresolved_with_revalidation"
        reasons.extend(("contradiction_operationalized", "residual_uncertainty_retained"))
        uncertainty.extend(("residue_present", "revalidate_required"))
        delta.append("must_revalidate:true")
    elif w05_status == "permitted_channel_blocked":
        status = "claim_blocked"
        reasons.extend(("upstream_permission_block_preserved", "blocked_claim_propagated"))
        uncertainty.append("blocked_claim_residue")
        delta.extend(("must_block_claim:true", "may_continue_narrowly:false"))
    else:
        status = "narrow_continuation_with_residue"
        reasons.extend(("bounded_revision_route", "no_clean_global_truth_claim"))
        uncertainty.append("residue_present")
        delta.extend(("may_continue_narrowly:true", "must_revalidate:false"))

    input_obj = PhaseAdapterInput(
        trace_id=trace_id,
        phase_code="W06",
        input_refs=(f"w05_status:{w05_status}", f"signal:{packet.signal_kind.value}"),
        source_packet_ids=(packet.packet_id,),
        adapter_source="adapter_projection",
    )
    output_obj = PhaseAdapterOutput(
        trace_id=trace_id,
        phase_code="W06",
        output_refs=(f"w06_consequence:{status}",),
        decision_status=status,
        reason_codes=tuple(reasons),
        uncertainty_markers=tuple(uncertainty),
        prohibited_claims=("no_correction_execution", "no_upstream_state_rewrite"),
        downstream_permission_delta=tuple(delta),
        execution_prohibited=True,
        adapter_limitations=("revision_projection_no_core_mutation",),
    )
    return input_obj, output_obj
