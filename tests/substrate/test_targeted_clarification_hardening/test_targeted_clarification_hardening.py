from __future__ import annotations

from dataclasses import replace

from substrate.targeted_clarification import (
    InterventionStatus,
    evaluate_targeted_clarification_downstream_gate,
)


def test_contract_break_target_drift_and_missing_presuppositions_becomes_blocked(g07_factory) -> None:
    result = g07_factory('he said "you are tired?"', "g07-hardening-contract-break").intervention
    record = result.bundle.intervention_records[0]
    broken = replace(
        result.bundle,
        intervention_records=(
            replace(
                record,
                minimal_question_spec=replace(
                    record.minimal_question_spec,
                    clarification_intent=replace(
                        record.minimal_question_spec.clarification_intent,
                        allowed_semantic_scope=("frame_family:descriptive_literal",),
                    ),
                    forbidden_assumptions=(),
                ),
                forbidden_presuppositions=(),
            ),
        ),
    )
    gate = evaluate_targeted_clarification_downstream_gate(broken)
    assert gate.accepted is False
    assert "target_drift_risk_detected" in gate.restrictions
    assert "forbidden_presuppositions_missing_or_unreadable" in gate.restrictions
    assert "intervention_record_contract_broken" in gate.restrictions


def test_ask_now_without_answer_binding_ready_is_forbidden(g07_factory) -> None:
    result = g07_factory("you are tired", "g07-hardening-ask-binding").intervention
    record = result.bundle.intervention_records[0]
    forced_ask = replace(
        result.bundle,
        answer_binding_ready=False,
        intervention_records=(
            replace(
                record,
                intervention_status=InterventionStatus.ASK_NOW,
                ask_policy=replace(record.ask_policy, should_ask=True),
                expected_evidence_gain=replace(record.expected_evidence_gain, worth_cost=True),
            ),
        ),
    )
    gate = evaluate_targeted_clarification_downstream_gate(forced_ask)
    assert "ask_now_without_answer_binding_forbidden" in gate.restrictions
    assert "answer_binding_not_ready" in gate.restrictions
    assert "intervention_record_contract_broken" in gate.restrictions


def test_nonblocking_uncertainty_does_not_inflate_into_question_spam(g07_factory) -> None:
    result = g07_factory("it is cold", "g07-hardening-nonblocking").intervention
    statuses = [record.intervention_status for record in result.bundle.intervention_records]
    ask_count = sum(1 for status in statuses if status is InterventionStatus.ASK_NOW)
    assert ask_count <= 1
    if ask_count == 1:
        assert any(
            record.uncertainty_class.value in {"high_impact_binding_risk", "frame_competition", "owner_scope_ambiguity"}
            for record in result.bundle.intervention_records
            if record.intervention_status is InterventionStatus.ASK_NOW
        )


def test_high_impact_uncertainty_requires_high_impact_lockouts(g07_factory) -> None:
    result = g07_factory("you are dangerous", "g07-hardening-lockout-gap").intervention
    record = result.bundle.intervention_records[0]
    broken = replace(
        result.bundle,
        intervention_records=(
            replace(
                record,
                uncertainty_class=record.uncertainty_class.__class__.HIGH_IMPACT_BINDING_RISK,
                downstream_lockouts=tuple(
                    item
                    for item in record.downstream_lockouts
                    if item not in {"planning_forbidden_on_current_frame", "safety_escalation_not_authorized_from_current_evidence"}
                ),
            ),
        ),
    )
    gate = evaluate_targeted_clarification_downstream_gate(broken)
    assert "high_impact_lockout_gap_detected" in gate.restrictions


def test_source_ref_relabeling_gap_degrades_intervention_authority(g07_factory) -> None:
    result = g07_factory("you are tired", "g07-hardening-source-gap").intervention
    malformed = replace(
        result.bundle,
        source_acquisition_ref=result.bundle.source_acquisition_lineage_ref,
        source_acquisition_ref_kind="upstream_lineage_ref",
    )
    gate = evaluate_targeted_clarification_downstream_gate(malformed)
    assert gate.accepted is False
    assert "source_ref_relabeling_without_notice" in gate.restrictions
    assert "lineage_identity_collapse_risk" in gate.restrictions
