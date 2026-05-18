from __future__ import annotations

from dataclasses import replace

from experiments.embodied_playground.recipe_precursor_falsifiers import (
    ab5_update_as_recipe_oracle,
    ab6_attribution_as_recipe_oracle,
    confounder_bypasses_recipe_maturity,
    delayed_effect_as_immediate_recipe,
    disconfirming_trace_ignored,
    evaluate_recipe_precursor_falsifiers,
    hidden_recipe_leak,
    mature_schema_without_p13_gate,
    one_shot_recipe_maturity,
    output_as_truth_oracle,
    p15_overclaims_recipe_learning,
    protected_eval_output_used,
    recipe_candidate_emits_action_request,
    recipe_candidate_executes_world,
    recipe_without_effect_refs,
    recipe_without_input_refs,
    recipe_without_lived_trace,
    repeated_trace_without_public_refs,
    scenario_label_recipe_learning,
    station_affordance_as_recipe_truth,
    station_visible_as_recipe_basis,
)
from experiments.embodied_playground.recipe_precursor_learning import (
    LivedRecipeTrace,
    RecipeCandidate,
    RecipePrecursorLearningRun,
    run_recipe_precursor_learning_case,
)


def _base_run() -> RecipePrecursorLearningRun:
    return run_recipe_precursor_learning_case("one_success_trace_provisional_only")


def test_p15_falsifier_hidden_recipe_leak_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], hidden_recipe_used=True)
    run = replace(run, recipe_candidates=(candidate,))
    assert hidden_recipe_leak(run=run)


def test_p15_falsifier_one_shot_recipe_maturity_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], one_shot_mature=True)
    run = replace(run, recipe_candidates=(candidate,))
    assert one_shot_recipe_maturity(run=run)


def test_p15_falsifier_recipe_without_lived_trace_negative_control() -> None:
    run = _base_run()
    run = replace(run, lived_trace_records=())
    assert recipe_without_lived_trace(run=run)


def test_p15_falsifier_recipe_without_effect_refs_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], effect_refs=())
    run = replace(run, recipe_candidates=(candidate,))
    assert recipe_without_effect_refs(run=run)


def test_p15_falsifier_recipe_without_input_refs_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], input_refs=())
    run = replace(run, recipe_candidates=(candidate,))
    assert recipe_without_input_refs(run=run)


def test_p15_falsifier_station_visible_as_recipe_basis_negative_control() -> None:
    run = _base_run()
    candidate = replace(
        run.recipe_candidates[0],
        input_refs=(),
        effect_refs=(),
        maturity_status="provisional_candidate",
    )
    run = replace(run, recipe_candidates=(candidate,))
    assert station_visible_as_recipe_basis(run=run)


def test_p15_falsifier_station_affordance_as_recipe_truth_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], maturity_status="repeated_trace_supported", p13_schema_candidate_refs=())
    run = replace(run, recipe_candidates=(candidate,))
    assert station_affordance_as_recipe_truth(run=run)


def test_p15_falsifier_confounder_bypasses_recipe_maturity_negative_control() -> None:
    run = run_recipe_precursor_learning_case("confounded_station_effect")
    candidate = replace(run.recipe_candidates[0], maturity_status="repeated_trace_supported", confounder_refs=())
    run = replace(run, recipe_candidates=(candidate,))
    assert confounder_bypasses_recipe_maturity(run=run)


def test_p15_falsifier_disconfirming_trace_ignored_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], disconfirming_trace_refs=("trace:2",), maturity_status="provisional_candidate")
    run = replace(run, recipe_candidates=(candidate,))
    assert disconfirming_trace_ignored(run=run)


def test_p15_falsifier_repeated_trace_without_public_refs_negative_control() -> None:
    run = run_recipe_precursor_learning_case("repeated_consistent_traces_candidate_strengthens")
    trace = replace(run.lived_trace_records[0], evidence_refs=())
    candidate = replace(run.recipe_candidates[0], maturity_status="repeated_trace_supported")
    traces = (trace, *run.lived_trace_records[1:])
    run = replace(run, lived_trace_records=traces, recipe_candidates=(candidate,))
    assert repeated_trace_without_public_refs(run=run)


def test_p15_falsifier_delayed_effect_as_immediate_recipe_negative_control() -> None:
    run = run_recipe_precursor_learning_case("delayed_station_effect")
    candidate = replace(run.recipe_candidates[0], maturity_score=0.81)
    run = replace(run, recipe_candidates=(candidate,))
    assert delayed_effect_as_immediate_recipe(run=run)


def test_p15_falsifier_output_as_truth_oracle_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], output_refs=("output:item_b",), input_refs=(), maturity_status="provisional_candidate")
    run = replace(run, recipe_candidates=(candidate,))
    assert output_as_truth_oracle(run=run)


def test_p15_falsifier_ab5_update_as_recipe_oracle_negative_control() -> None:
    run = _base_run()
    trace = replace(run.lived_trace_records[0], evidence_refs=("ab5:update:1",))
    run = replace(run, lived_trace_records=(trace, *run.lived_trace_records[1:]))
    assert ab5_update_as_recipe_oracle(run=run)


def test_p15_falsifier_ab6_attribution_as_recipe_oracle_negative_control() -> None:
    run = _base_run()
    trace = replace(run.lived_trace_records[0], evidence_refs=("ab6:frame:1",), public_effect_refs=())
    run = replace(run, lived_trace_records=(trace, *run.lived_trace_records[1:]))
    assert ab6_attribution_as_recipe_oracle(run=run)


def test_p15_falsifier_scenario_label_recipe_learning_negative_control() -> None:
    run = _base_run()
    trace = replace(run.lived_trace_records[0], scenario_label_used=True)
    run = replace(run, lived_trace_records=(trace, *run.lived_trace_records[1:]))
    assert scenario_label_recipe_learning(run=run)


def test_p15_falsifier_protected_eval_output_used_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], protected_eval_used=True)
    run = replace(run, recipe_candidates=(candidate,))
    assert protected_eval_output_used(run=run)


def test_p15_falsifier_recipe_candidate_emits_action_request_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], action_request_emitted=True)
    run = replace(run, recipe_candidates=(candidate,))
    assert recipe_candidate_emits_action_request(run=run)


def test_p15_falsifier_recipe_candidate_executes_world_negative_control() -> None:
    run = _base_run()
    candidate = replace(run.recipe_candidates[0], world_submission_emitted=True)
    run = replace(run, recipe_candidates=(candidate,))
    assert recipe_candidate_executes_world(run=run)


def test_p15_falsifier_mature_schema_without_p13_gate_negative_control() -> None:
    run = _base_run()
    candidate = replace(
        run.recipe_candidates[0],
        maturity_status="repeated_trace_supported",
        p13_schema_candidate_refs=(),
        supporting_trace_refs=("trace:1",),
    )
    run = replace(run, recipe_candidates=(candidate,))
    assert mature_schema_without_p13_gate(run=run)


def test_p15_falsifier_p15_overclaims_recipe_learning_negative_control() -> None:
    assert p15_overclaims_recipe_learning(claim_boundary="This proves mature recipe learning, automation, and consciousness.")


def test_p15_falsifier_suite_smoke_negative_control() -> None:
    run = _base_run()
    bad_trace = LivedRecipeTrace(
        trace_id="bad:trace",
        public_station_ref="station:alpha",
        public_input_refs=(),
        public_output_refs=("output:item_b",),
        public_effect_refs=(),
        ap01_request_refs=(),
        station_attempt_refs=(),
        action_effect_refs=(),
        p13_credit_link_refs=(),
        p13_schema_candidate_refs=(),
        confounder_refs=(),
        timing_refs=("timing:delayed",),
        evidence_refs=(),
        hidden_eval_used=True,
        scenario_label_used=True,
    )
    bad_candidate = RecipeCandidate(
        recipe_candidate_id="bad:candidate",
        station_ref="station:alpha",
        input_refs=(),
        output_refs=("output:item_b",),
        effect_refs=(),
        supporting_trace_refs=("bad:trace",),
        disconfirming_trace_refs=("bad:trace",),
        p13_schema_candidate_refs=(),
        confounder_refs=(),
        required_public_evidence=("station_ref",),
        missing_evidence=(),
        maturity_status="mature_forbidden_or_not_reached",
        maturity_score=0.95,
        maturity_policy="requires_repeated_public_traces_confounded_checked_disconfirmation_aware",
        one_shot_mature=True,
        hidden_recipe_used=True,
        protected_eval_used=True,
        fact_claimed=False,
        cause_confirmed=False,
        action_request_emitted=True,
        world_submission_emitted=True,
    )
    run = replace(
        run,
        lived_trace_records=(bad_trace,),
        recipe_candidates=(bad_candidate,),
        confounder_records=({"confounder_ref": "conf:1", "status": "active"},),
        action_request_emitted=True,
        world_submission_emitted=True,
    )
    result = evaluate_recipe_precursor_falsifiers(run=run, claim_boundary="mature recipe learning and consciousness")
    assert result["hidden_recipe_leak"] is True
    assert result["one_shot_recipe_maturity"] is True
    assert result["recipe_candidate_emits_action_request"] is True
    assert result["recipe_candidate_executes_world"] is True
    assert result["P15_overclaims_recipe_learning"] is True
