from __future__ import annotations

from substrate.n03_autobiographical_relevance import (
    N03AutobiographicalTraceKind,
    N03CurrentTargetKind,
    N03LimitingReason,
    N03RelevanceKind,
    N03StructuralDimension,
    N03TransferDecision,
    N03TransferScope,
    derive_n03_consumer_packets,
)
from tests.substrate.n03_autobiographical_relevance_testkit import (
    N03HarnessCase,
    build_n03_harness_case,
    n03_bundle,
    n03_target,
    n03_trace,
)


def _run(case_id: str, *, traces=(), targets=()):
    bundle = n03_bundle(
        bundle_id=f"{case_id}:bundle",
        traces=traces,
        targets=targets,
        source_lineage=("tests.n03.owner", case_id),
        reason=case_id,
    )
    return build_n03_harness_case(N03HarnessCase(case_id=case_id, input_bundle=bundle)).n03_result


def _first_entry(result):
    return result.relevance_entries[0]


def test_no_typed_basis_yields_no_safe_transfer() -> None:
    result = build_n03_harness_case(N03HarnessCase(case_id="no-basis", input_bundle=None)).n03_result
    assert result.relevance_entries == ()
    assert result.gate.consumer_ready is False
    assert "n03_no_safe_transfer" in result.gate.required_restrictions


def test_semantic_similarity_only_does_not_create_autobiographical_relevance() -> None:
    result = _run(
        "semantic-only",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=(), identity_region_refs=()),),
        targets=(n03_target(current_target_id="g1", active_commitment_refs=(), active_identity_region_refs=()),),
    )
    entry = _first_entry(result)
    assert entry.transfer_decision in {
        N03TransferDecision.DO_NOT_TRANSFER,
        N03TransferDecision.NO_SAFE_AUTOBIOGRAPHICAL_TRANSFER,
    }
    assert N03LimitingReason.SEMANTIC_SIMILARITY_ONLY in entry.limiting_reasons


def test_recency_only_does_not_create_autobiographical_relevance() -> None:
    result = _run(
        "recency-only",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=(), identity_region_refs=(), recency_hint=0.92),),
        targets=(n03_target(current_target_id="g1", active_commitment_refs=(), active_identity_region_refs=()),),
    )
    assert N03LimitingReason.RECENCY_ONLY in _first_entry(result).limiting_reasons
    assert _first_entry(result).transfer_decision is N03TransferDecision.DO_NOT_TRANSFER


def test_vividness_only_does_not_override_structural_basis() -> None:
    result = _run(
        "vivid-only",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=(), identity_region_refs=(), vividness_hint=0.95),),
        targets=(n03_target(current_target_id="g1", active_commitment_refs=(), active_identity_region_refs=()),),
    )
    entry = _first_entry(result)
    assert N03LimitingReason.VIVIDNESS_NOT_SUFFICIENT in entry.limiting_reasons
    assert entry.transfer_decision is N03TransferDecision.DO_NOT_TRANSFER


def test_structural_commitment_match_creates_bounded_relevance() -> None:
    result = _run(
        "commitment-match",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=("c:1",), trace_kind=N03AutobiographicalTraceKind.PRIOR_COMMITMENT_KEPT),),
        targets=(n03_target(current_target_id="g1", target_kind=N03CurrentTargetKind.COMMITMENT_UNDER_LOAD, active_commitment_refs=("c:1",)),),
    )
    entry = _first_entry(result)
    assert N03StructuralDimension.COMMITMENT_MATCH in entry.supported_by_dimensions
    assert entry.transfer_scope in {N03TransferScope.SAME_COMMITMENT_REGION_ONLY, N03TransferScope.CURRENT_CONTEXT_ONLY}


def test_capability_gap_match_creates_capability_boundary_relevance() -> None:
    result = _run(
        "cap-gap-match",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=(), capability_gap_refs=("gap:a",), trace_kind=N03AutobiographicalTraceKind.CAPABILITY_BOUNDARY_TRACE),),
        targets=(n03_target(current_target_id="g1", target_kind=N03CurrentTargetKind.CAPABILITY_GAP_DEMAND, active_commitment_refs=(), active_capability_gap_refs=("gap:a",)),),
    )
    entry = _first_entry(result)
    assert entry.relevance_kind is N03RelevanceKind.CAPABILITY_BOUNDARY_RELEVANCE
    assert entry.transfer_decision in {N03TransferDecision.USE_AS_PLAN_CONSTRAINT, N03TransferDecision.PROVISIONAL_TRANSFER_ONLY}


def test_recovery_pattern_match_creates_recovery_template_with_scope() -> None:
    result = _run(
        "recovery-match",
        traces=(n03_trace(source_trace_id="t1", trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY, failure_or_recovery_signature="sig:recovery", recurrence_count=3),),
        targets=(n03_target(current_target_id="g1", target_kind=N03CurrentTargetKind.RECOVERY_NEED),),
    )
    entry = _first_entry(result)
    assert entry.relevance_kind is N03RelevanceKind.RECOVERY_PATTERN_RELEVANCE
    assert entry.transfer_scope in {N03TransferScope.SAME_RECOVERY_PATTERN_ONLY, N03TransferScope.CURRENT_CONTEXT_ONLY}


def test_repeated_recovery_pattern_strengthens_but_keeps_limits() -> None:
    result = _run(
        "recovery-repeated",
        traces=(n03_trace(source_trace_id="t1", trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY, recurrence_count=5),),
        targets=(n03_target(current_target_id="g1", target_kind=N03CurrentTargetKind.RECOVERY_NEED),),
    )
    entry = _first_entry(result)
    assert entry.relevance_strength > 0.4
    assert "must_not_generalize_single_episode" in entry.anti_generalization_limits


def test_single_episode_does_not_generalize_globally() -> None:
    result = _run(
        "single-episode",
        traces=(n03_trace(source_trace_id="t1", recurrence_count=1),),
        targets=(n03_target(current_target_id="g1"),),
    )
    entry = _first_entry(result)
    assert N03LimitingReason.SINGLE_EPISODE_OVERGENERALIZATION_RISK in entry.limiting_reasons
    assert entry.transfer_scope is not N03TransferScope.BROAD_TRANSFER_BLOCKED


def test_identity_drift_downweights_or_blocks_old_transfer() -> None:
    result = _run(
        "drift-block",
        traces=(n03_trace(source_trace_id="t1"),),
        targets=(n03_target(current_target_id="g1", active_drift_markers=("drift_contested",)),),
    )
    entry = _first_entry(result)
    assert N03LimitingReason.IDENTITY_DRIFT_REDUCES_TRANSFER in entry.limiting_reasons
    assert entry.transfer_decision in {N03TransferDecision.PROVISIONAL_TRANSFER_ONLY, N03TransferDecision.DO_NOT_TRANSFER}


def test_n02_drift_markers_change_transfer_decision_and_gate_readiness_on_same_trace_target() -> None:
    trace = n03_trace(
        source_trace_id="t-drift-contrast",
        trace_kind=N03AutobiographicalTraceKind.PRIOR_FAILURE,
        commitment_refs=("c:drift",),
        recurrence_count=4,
        confidence=0.88,
    )
    clean = _run(
        "drift-contrast-clean",
        traces=(trace,),
        targets=(
            n03_target(
                current_target_id="g-drift",
                target_kind=N03CurrentTargetKind.COMMITMENT_UNDER_LOAD,
                active_commitment_refs=("c:drift",),
                active_drift_markers=(),
                regulation_or_planning_pressure=0.8,
            ),
        ),
    )
    drifted = _run(
        "drift-contrast-drifted",
        traces=(trace,),
        targets=(
            n03_target(
                current_target_id="g-drift",
                target_kind=N03CurrentTargetKind.COMMITMENT_UNDER_LOAD,
                active_commitment_refs=("c:drift",),
                active_drift_markers=("drift_fracture",),
                regulation_or_planning_pressure=0.8,
            ),
        ),
    )
    clean_entry = _first_entry(clean)
    drifted_entry = _first_entry(drifted)
    assert clean_entry.transfer_decision in {
        N03TransferDecision.USE_AS_REGULATORY_WARNING,
        N03TransferDecision.USE_AS_COMMITMENT_ANCHOR,
        N03TransferDecision.USE_AS_SUPPORTING_PATTERN,
    }
    assert drifted_entry.transfer_decision in {
        N03TransferDecision.PROVISIONAL_TRANSFER_ONLY,
        N03TransferDecision.DO_NOT_TRANSFER,
    }
    assert N03LimitingReason.IDENTITY_DRIFT_REDUCES_TRANSFER in drifted_entry.limiting_reasons
    assert clean.gate.consumer_ready is True
    assert drifted.gate.consumer_ready is False
    assert clean.gate.required_restrictions != drifted.gate.required_restrictions


def test_affordance_change_blocks_old_recovery_template_transfer() -> None:
    result = _run(
        "affordance-change",
        traces=(n03_trace(source_trace_id="t1", trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY, affordance_refs=("aff:a",)),),
        targets=(n03_target(current_target_id="g1", active_affordance_refs=("aff:a",), active_drift_markers=("affordance_changed",)),),
    )
    entry = _first_entry(result)
    assert N03LimitingReason.AFFORDANCE_SPACE_CHANGED in entry.limiting_reasons
    assert entry.transfer_decision is N03TransferDecision.USE_AS_CAUTION


def test_current_evidence_can_block_past_trace_transfer() -> None:
    result = _run(
        "current-overrides",
        traces=(n03_trace(source_trace_id="t1", failure_or_recovery_signature="sig:failure"),),
        targets=(n03_target(current_target_id="g1", current_evidence_signature="contradicts:sig:failure"),),
    )
    entry = _first_entry(result)
    assert N03LimitingReason.CURRENT_EVIDENCE_CONTRADICTS_PAST_TRACE in entry.limiting_reasons
    assert entry.transfer_decision is N03TransferDecision.DO_NOT_TRANSFER


def test_conflicting_autobiographical_traces_are_preserved() -> None:
    result = _run(
        "conflict-set",
        traces=(
            n03_trace(source_trace_id="t1", trace_kind=N03AutobiographicalTraceKind.PRIOR_FAILURE, recurrence_count=3),
            n03_trace(source_trace_id="t2", trace_kind=N03AutobiographicalTraceKind.PRIOR_RECOVERY, recurrence_count=3),
        ),
        targets=(n03_target(current_target_id="g1"),),
    )
    decisions = {item.transfer_decision for item in result.relevance_entries}
    assert N03TransferDecision.CONFLICTING_AUTOBIOGRAPHICAL_GUIDANCE in decisions
    assert result.gate.conflict_count > 0


def test_conflicting_plan_constraint_and_commitment_anchor_are_preserved() -> None:
    result = _run(
        "conflict-plan-constraint-vs-anchor",
        traces=(
            n03_trace(
                source_trace_id="t1",
                trace_kind=N03AutobiographicalTraceKind.PRIOR_COMMITMENT_KEPT,
                commitment_refs=("commitment:alpha",),
                capability_gap_refs=(),
                recurrence_count=3,
            ),
            n03_trace(
                source_trace_id="t2",
                trace_kind=N03AutobiographicalTraceKind.CAPABILITY_BOUNDARY_TRACE,
                commitment_refs=(),
                capability_gap_refs=("gap:alpha",),
                recurrence_count=3,
            ),
        ),
        targets=(
            n03_target(
                current_target_id="g1",
                target_kind=N03CurrentTargetKind.PLANNING_DEMAND,
                active_commitment_refs=("commitment:alpha",),
                active_capability_gap_refs=("gap:alpha",),
            ),
        ),
    )
    decisions = {item.transfer_decision for item in result.relevance_entries}
    assert N03TransferDecision.CONFLICTING_AUTOBIOGRAPHICAL_GUIDANCE in decisions
    assert result.gate.conflict_count > 0
    assert result.gate.consumer_ready is False


def test_generic_world_fact_memory_is_not_autobiographical_trace() -> None:
    result = _run(
        "generic-memory",
        traces=(n03_trace(source_trace_id="t1", trace_kind=N03AutobiographicalTraceKind.GENERIC_MEMORY_ONLY),),
        targets=(n03_target(current_target_id="g1"),),
    )
    entry = _first_entry(result)
    assert N03LimitingReason.GENERIC_MEMORY_NOT_SELF_LINE in entry.limiting_reasons
    assert entry.transfer_decision is N03TransferDecision.DO_NOT_TRANSFER


def test_provisional_transfer_only_when_basis_partial() -> None:
    result = _run(
        "provisional-partial",
        traces=(n03_trace(source_trace_id="t1", attribution_profile="mixed", recurrence_count=2),),
        targets=(n03_target(current_target_id="g1", attribution_profile="mixed"),),
    )
    assert _first_entry(result).transfer_decision is N03TransferDecision.PROVISIONAL_TRANSFER_ONLY


def test_do_not_transfer_packet_is_downstream_visible() -> None:
    result = _run(
        "do-not-transfer-visible",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=(), identity_region_refs=(), recency_hint=0.95),),
        targets=(n03_target(current_target_id="g1", active_commitment_refs=(), active_identity_region_refs=()),),
    )
    packet = derive_n03_consumer_packets(result)[0]
    assert packet.transfer_decision == N03TransferDecision.DO_NOT_TRANSFER.value
    assert packet.routing_signal == "no_downstream_transfer"


def test_anti_generalization_limits_are_required_for_consumer_ready() -> None:
    result = _run(
        "limits-ready",
        traces=(n03_trace(source_trace_id="t1", recurrence_count=3),),
        targets=(n03_target(current_target_id="g1"),),
    )
    entry = _first_entry(result)
    assert bool(entry.anti_generalization_limits)


def test_downstream_packet_exposes_transfer_scope_and_reason() -> None:
    result = _run(
        "packet-scope-reason",
        traces=(n03_trace(source_trace_id="t1", recency_hint=0.95, commitment_refs=(), identity_region_refs=()),),
        targets=(n03_target(current_target_id="g1", active_commitment_refs=(), active_identity_region_refs=()),),
    )
    packet = derive_n03_consumer_packets(result)[0]
    assert packet.transfer_scope
    assert packet.caution_markers


def test_ablation_commitment_history_degrades_to_weaker_transfer() -> None:
    strong = _run(
        "ablate-commit-strong",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=("c:1",), recurrence_count=3),),
        targets=(n03_target(current_target_id="g1", active_commitment_refs=("c:1",)),),
    )
    weak = _run(
        "ablate-commit-weak",
        traces=(n03_trace(source_trace_id="t1", commitment_refs=(), recurrence_count=3),),
        targets=(n03_target(current_target_id="g1", active_commitment_refs=("c:1",)),),
    )
    assert _first_entry(strong).relevance_strength >= _first_entry(weak).relevance_strength


def test_ablation_capability_or_self_binding_degrades_to_weaker_transfer() -> None:
    strong = _run(
        "ablate-cap-sb-strong",
        traces=(n03_trace(source_trace_id="t1", capability_gap_refs=("gap:a",), self_binding_refs=("sb:a",), recurrence_count=3),),
        targets=(n03_target(current_target_id="g1", active_capability_gap_refs=("gap:a",), active_self_binding_refs=("sb:a",)),),
    )
    weak = _run(
        "ablate-cap-sb-weak",
        traces=(n03_trace(source_trace_id="t1", capability_gap_refs=(), self_binding_refs=(), recurrence_count=3),),
        targets=(n03_target(current_target_id="g1", active_capability_gap_refs=("gap:a",), active_self_binding_refs=("sb:a",)),),
    )
    assert _first_entry(strong).relevance_strength >= _first_entry(weak).relevance_strength
