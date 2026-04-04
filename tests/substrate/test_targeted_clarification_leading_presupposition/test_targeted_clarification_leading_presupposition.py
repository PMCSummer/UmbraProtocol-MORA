from __future__ import annotations

from substrate.targeted_clarification import InterventionStatus


def test_minimal_question_spec_blocks_leading_answer_injection(g07_factory) -> None:
    result = g07_factory('he said "you are dangerous"', "g07-leading").intervention
    for record in result.bundle.intervention_records:
        assert record.minimal_question_spec.preferred_answer_forbidden is True
        assert record.minimal_question_spec.realization_contract_marker == "clarification_not_equal_realized_question"
        assert record.minimal_question_spec.forbidden_assumptions


def test_forbidden_presuppositions_explicit_for_ask_paths(g07_factory) -> None:
    result = g07_factory("you are dangerous?", "g07-presupposition").intervention
    ask_records = [
        record for record in result.bundle.intervention_records if record.intervention_status is InterventionStatus.ASK_NOW
    ]
    if ask_records:
        assert all("do_not_assume_resolution_without_answer" in record.forbidden_presuppositions for record in ask_records)
        assert all("do_not_force_target_identity" in record.forbidden_presuppositions for record in ask_records)
