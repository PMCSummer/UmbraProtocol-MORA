from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.delayed_credit_falsifiers import (
    attribution_as_learning_oracle,
    confounder_credit_leak,
    confounder_erased,
    correlation_as_cause,
    credit_learning_emits_action_request,
    delayed_effect_misattribution,
    delayed_window_without_timing_refs,
    disconfirming_trace_ignored,
    effect_as_learning_oracle,
    evaluate_delayed_credit_falsifiers,
    hidden_recipe_leak,
    mature_schema_without_repetition,
    one_shot_mature_schema,
    p13_overclaims_learning,
    request_as_learning_confirmation,
    scenario_label_learning,
    schema_without_effect_refs,
    schema_without_precursor_refs,
    support_precision_without_evidence,
)
from experiments.embodied_playground.delayed_credit_learning import (
    CandidateCreditLink,
    ConfounderRecord,
    DelayedCreditLearningRun,
    ProvisionalSchemaCandidate,
    run_delayed_credit_learning_case,
)


def _base_run() -> DelayedCreditLearningRun:
    return run_delayed_credit_learning_case("immediate_clear_effect")


def test_p13_falsifier_one_shot_mature_schema_negative_control() -> None:
    run = _base_run()
    schema = replace(run.provisional_schema_candidates[0], one_shot_mature=True)
    run = replace(run, provisional_schema_candidates=(schema,))
    assert one_shot_mature_schema(run=run)


def test_p13_falsifier_confounder_credit_leak_negative_control() -> None:
    run = run_delayed_credit_learning_case("confounded_effect_two_precursors")
    link = replace(run.candidate_credit_links[0], maturity_status="provisional_candidate", missing_evidence=())
    conf = replace(run.confounder_records[0], status="active")
    run = replace(run, candidate_credit_links=(link,), confounder_records=(conf,))
    assert confounder_credit_leak(run=run)


def test_p13_falsifier_delayed_effect_misattribution_negative_control() -> None:
    run = run_delayed_credit_learning_case("delayed_effect_correct_window")
    bad_delay = dict(run.delayed_effect_records[0])
    bad_delay["timing_refs"] = ()
    run = replace(run, delayed_effect_records=(bad_delay,))
    assert delayed_effect_misattribution(run=run)


def test_p13_falsifier_correlation_as_cause_negative_control() -> None:
    run = _base_run()
    link = replace(run.candidate_credit_links[0], fact_claimed=True)
    run = replace(run, candidate_credit_links=(link,))
    assert correlation_as_cause(run=run)


def test_p13_falsifier_hidden_recipe_leak_negative_control() -> None:
    run = _base_run()
    schema = replace(run.provisional_schema_candidates[0], hidden_recipe_used=True)
    run = replace(run, provisional_schema_candidates=(schema,))
    assert hidden_recipe_leak(run=run)


def test_p13_falsifier_scenario_label_learning_negative_control() -> None:
    run = _base_run()
    trace = replace(run.episode_traces[0], scenario_label_used=True)
    run = replace(run, episode_traces=(trace,))
    assert scenario_label_learning(run=run)


def test_p13_falsifier_schema_without_effect_refs_negative_control() -> None:
    run = _base_run()
    schema = replace(run.provisional_schema_candidates[0], effect_refs=())
    run = replace(run, provisional_schema_candidates=(schema,))
    assert schema_without_effect_refs(run=run)


def test_p13_falsifier_schema_without_precursor_refs_negative_control() -> None:
    run = _base_run()
    schema = replace(run.provisional_schema_candidates[0], precursor_refs=())
    run = replace(run, provisional_schema_candidates=(schema,))
    assert schema_without_precursor_refs(run=run)


def test_p13_falsifier_mature_schema_without_repetition_negative_control() -> None:
    run = _base_run()
    schema = replace(run.provisional_schema_candidates[0], maturity_status="mature_forbidden_in_P13", supporting_episode_refs=("ep1",))
    run = replace(run, provisional_schema_candidates=(schema,))
    assert mature_schema_without_repetition(run=run)


def test_p13_falsifier_disconfirming_trace_ignored_negative_control() -> None:
    run = _base_run()
    schema = replace(run.provisional_schema_candidates[0], disconfirming_episode_refs=("ep2",), maturity_status="provisional")
    run = replace(run, provisional_schema_candidates=(schema,))
    assert disconfirming_trace_ignored(run=run)


def test_p13_falsifier_confounder_erased_negative_control() -> None:
    run = run_delayed_credit_learning_case("confounded_effect_two_precursors")
    run = replace(run, confounder_records=())
    assert confounder_erased(run=run)


def test_p13_falsifier_delayed_window_without_timing_refs_negative_control() -> None:
    run = run_delayed_credit_learning_case("delayed_effect_correct_window")
    link = replace(run.candidate_credit_links[0], delay_window="")
    run = replace(run, candidate_credit_links=(link,))
    assert delayed_window_without_timing_refs(run=run)


def test_p13_falsifier_support_precision_without_evidence_negative_control() -> None:
    run = _base_run()
    link = replace(run.candidate_credit_links[0], confidence=0.85, evidence_refs=())
    run = replace(run, candidate_credit_links=(link,))
    assert support_precision_without_evidence(run=run)


def test_p13_falsifier_request_as_learning_confirmation_negative_control() -> None:
    run = _base_run()
    link = replace(run.candidate_credit_links[0], effect_ref="", maturity_status="provisional_candidate")
    run = replace(run, candidate_credit_links=(link,))
    assert request_as_learning_confirmation(run=run)


def test_p13_falsifier_effect_as_learning_oracle_negative_control() -> None:
    run = _base_run()
    link = replace(run.candidate_credit_links[0], precursor_ref="", effect_ref="effect:only", maturity_status="provisional_candidate")
    run = replace(run, candidate_credit_links=(link,))
    assert effect_as_learning_oracle(run=run)


def test_p13_falsifier_attribution_as_learning_oracle_negative_control() -> None:
    run = _base_run()
    link = replace(run.candidate_credit_links[0], attribution_kind_refs=("self_action",), evidence_refs=(), confidence=0.7)
    run = replace(run, candidate_credit_links=(link,))
    assert attribution_as_learning_oracle(run=run)


def test_p13_falsifier_credit_learning_emits_action_request_negative_control() -> None:
    run = _base_run()
    run = replace(run, action_request_emitted=True)
    assert credit_learning_emits_action_request(run=run)


def test_p13_falsifier_p13_overclaims_learning_negative_control() -> None:
    assert p13_overclaims_learning(claim_boundary="This proves mature recipe learning and consciousness.")


def test_p13_falsifier_suite_smoke_negative_control() -> None:
    run = _base_run()
    bad_link = CandidateCreditLink(
        link_id="bad:1",
        precursor_ref="",
        effect_ref="",
        delay_window="",
        correlation_status="delayed_possible",
        attribution_kind_refs=("self_action",),
        evidence_refs=(),
        missing_evidence=(),
        confidence=0.9,
        confidence_policy="evidence_bounded",
        maturity_status="provisional_candidate",
        fact_claimed=True,
        cause_confirmed=False,
    )
    bad_schema = ProvisionalSchemaCandidate(
        schema_candidate_id="bad:schema",
        precursor_refs=(),
        effect_refs=(),
        supporting_episode_refs=("ep1",),
        disconfirming_episode_refs=("ep2",),
        confounder_refs=(),
        delay_profile="delayed",
        maturity_score=0.95,
        maturity_policy="requires_repetition_and_disconfounder",
        maturity_status="mature_forbidden_in_P13",
        blocked_reasons=(),
        missing_evidence=(),
        hidden_recipe_used=True,
        one_shot_mature=True,
        fact_claimed=False,
        cause_confirmed=False,
    )
    bad_conf = ConfounderRecord(
        confounder_id="bad:conf",
        confounder_ref="confounder:parallel:ep1",
        overlaps_with=("bad:1",),
        could_explain_effect=True,
        discriminating_evidence_needed=("need",),
        credit_leak_risk="high",
        status="active",
        evidence_refs=("bad:1",),
    )
    run = replace(
        run,
        candidate_credit_links=(bad_link,),
        provisional_schema_candidates=(bad_schema,),
        confounder_records=(bad_conf,),
        action_request_emitted=True,
    )
    result = evaluate_delayed_credit_falsifiers(run=run, claim_boundary="mature recipe learning and consciousness")
    assert result["one_shot_mature_schema"] is True
    assert result["schema_without_effect_refs"] is True
    p13_overclaims_learning,
