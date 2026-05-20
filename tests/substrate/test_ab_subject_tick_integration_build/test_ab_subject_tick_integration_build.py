from __future__ import annotations

from dataclasses import replace

from substrate.ab01_event_digest import AB1EventDigestInput, build_ab1_event_digests
from substrate.ab02_hypothesis_seed import AB2HypothesisSeedInput, build_ab2_hypothesis_seeds
from substrate.ab03_hypothesis_frontier import AB3FrontierInput, build_ab3_hypothesis_frontier
from substrate.ab_subject_tick_integration import (
    ABLiveTickConfig,
    ABLiveTickInput,
    run_ab_live_subject_tick_contour,
)


def _frontier(*, ambiguous: bool = True):
    ab1 = build_ab1_event_digests(
        AB1EventDigestInput(
            tick_ref="ab-int:frontier:ab1",
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            raw_window_refs=("obs:1",),
            effect_refs=("effect:1",),
            residue_refs=("residue:1",),
            expected_refs=("expected:1",),
            observed_refs=("observed:1",),
            anomaly_markers=("uncertain:1",),
            effect_status="blocked" if ambiguous else "observed_success",
            magnitude=0.5,
            noise_level=0.1,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab_int",
        )
    )
    assert ab1.digests
    ab2 = build_ab2_hypothesis_seeds(
        AB2HypothesisSeedInput(
            tick_ref="ab-int:frontier:ab2",
            event_digests=ab1.digests,
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab_int",
        )
    )
    assert ab2.seed_set is not None
    ab3 = build_ab3_hypothesis_frontier(
        AB3FrontierInput(
            tick_ref="ab-int:frontier:ab3",
            seed_set=ab2.seed_set,
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            disconfirming_evidence_refs=("conflict:1",) if ambiguous else (),
            ambiguous_evidence=ambiguous,
            require_competing_hypotheses=True,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab_int",
        )
    )
    assert ab3.frontier is not None
    return ab3.frontier


def _input(**overrides: object) -> ABLiveTickInput:
    base = ABLiveTickInput(
        tick_id="ab-int:tick:1",
        public_observation_refs=("obs:1",),
        public_effect_refs=("effect:1",),
        residue_refs=("residue:1",),
        uncertainty_refs=("uncertain:1",),
        conflict_refs=(),
        ap01_request_refs=(),
        action_effect_refs=(),
        prior_frontier_refs=(),
        prior_ab_state_refs=(),
        recipe_candidate_refs=(),
        precursor_candidate_refs=(),
        value_chain_refs=(),
        factory_chain_refs=(),
        protected_eval_present=False,
        scenario_label_present=False,
    )
    return replace(base, **overrides)


def _enabled_config(**overrides: object) -> ABLiveTickConfig:
    base = ABLiveTickConfig(enable_ab_live_contour=True)
    return replace(base, **overrides)


def test_ab_int_no_public_basis_noop() -> None:
    run = run_ab_live_subject_tick_contour(
        _input(
            public_observation_refs=(),
            public_effect_refs=(),
            residue_refs=(),
            uncertainty_refs=(),
            conflict_refs=(),
            ap01_request_refs=(),
            action_effect_refs=(),
        ),
        _enabled_config(),
    )
    assert run.ab1_event_digest_refs == ()
    assert run.ab2_seed_set_refs == ()
    assert run.ab3_frontier_refs == ()
    assert run.ab5_update_refs == ()
    assert run.ab6_attribution_refs == ()
    assert run.ab7_constraint_refs == ()
    assert all(not stage.ran for stage in run.stage_traces)
    assert run.ab_live_counters.skipped_no_public_basis_count >= 1


def test_ab_int_public_effect_mismatch_creates_digest_seed_frontier() -> None:
    run = run_ab_live_subject_tick_contour(_input(), _enabled_config())
    assert run.ab1_event_digest_refs
    assert run.ab2_seed_set_refs
    assert run.ab3_frontier_refs
    assert run.fact_claimed is False
    assert run.cause_confirmed is False


def test_ab_int_prior_frontier_correlated_effect_updates_support() -> None:
    frontier = _frontier(ambiguous=False)
    run = run_ab_live_subject_tick_contour(
        _input(
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
            action_effect_refs=("action_effect:1",),
            ap01_request_refs=("ap01:req:1",),
        ),
        _enabled_config(),
    )
    assert run.ab5_update_refs


def test_ab_int_request_alone_does_not_confirm() -> None:
    frontier = _frontier(ambiguous=False)
    run = run_ab_live_subject_tick_contour(
        _input(
            public_effect_refs=(),
            ap01_request_refs=("ap01:req:1",),
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
        ),
        _enabled_config(),
    )
    assert run.ab5_update_refs == ()
    assert run.fact_claimed is False


def test_ab_int_ap01_effect_creates_bounded_attribution() -> None:
    frontier = _frontier(ambiguous=False)
    run = run_ab_live_subject_tick_contour(
        _input(
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
            ap01_request_refs=("ap01:req:1",),
            action_effect_refs=("action_effect:1",),
        ),
        _enabled_config(),
    )
    assert run.ab6_attribution_refs
    assert run.cause_confirmed is False


def test_ab_int_ab6_requires_ap01_or_correlation_basis() -> None:
    frontier = _frontier(ambiguous=False)
    run = run_ab_live_subject_tick_contour(
        _input(
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
            ap01_request_refs=(),
            action_effect_refs=(),
        ),
        _enabled_config(),
    )
    assert run.ab6_attribution_refs
    assert run.cause_confirmed is False


def test_ab_int_open_frontier_creates_epistemic_basis_without_publication() -> None:
    frontier = _frontier(ambiguous=True)
    run = run_ab_live_subject_tick_contour(
        _input(
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
        ),
        _enabled_config(),
    )
    assert run.ab4_epistemic_basis_refs
    assert run.action_request_emitted is False
    assert run.world_submission_emitted is False


def test_ab_int_recipe_candidate_creates_constraints_not_skill() -> None:
    frontier = _frontier(ambiguous=False)
    run = run_ab_live_subject_tick_contour(
        _input(
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
            ap01_request_refs=("ap01:req:1",),
            action_effect_refs=("action_effect:1",),
            recipe_candidate_refs=("recipe_candidate:r1",),
            precursor_candidate_refs=("precursor:p1",),
            value_chain_refs=("value_chain:1",),
            p13_credit_refs=("p13:credit:1",),
            p14_station_affordance_refs=("p14:affordance:1",),
        ),
        _enabled_config(),
    )
    assert run.ab7_constraint_refs
    assert run.automation_claimed is False
    assert run.mature_recipe_claimed is False


def test_ab_int_protected_eval_input_blocked() -> None:
    run = run_ab_live_subject_tick_contour(
        _input(protected_eval_present=True),
        _enabled_config(),
    )
    assert run.ab1_event_digest_refs == ()
    assert "protected_eval_present" in run.blocked_reasons
    assert run.hidden_eval_used is False


def test_ab_int_scenario_label_not_used() -> None:
    run = run_ab_live_subject_tick_contour(
        _input(scenario_label_present=True),
        _enabled_config(),
    )
    assert run.ab1_event_digest_refs == ()
    assert "scenario_label_present" in run.blocked_reasons
    assert run.scenario_label_used is False


def test_ab_int_ambiguous_evidence_keeps_frontier_open() -> None:
    run = run_ab_live_subject_tick_contour(
        _input(
            conflict_refs=("conflict:alt_hypothesis",),
            uncertainty_refs=("uncertain:ambiguous",),
            ap01_request_refs=("ap01:req:1",),
            action_effect_refs=("action_effect:1",),
        ),
        _enabled_config(),
    )
    assert run.ab3_frontier_refs
    assert run.fact_claimed is False
    assert run.cause_confirmed is False


def test_ab_int_disabled_preserves_noop_behavior() -> None:
    run = run_ab_live_subject_tick_contour(_input(), ABLiveTickConfig(enable_ab_live_contour=False))
    assert run.ab1_event_digest_refs == ()
    assert run.ab2_seed_set_refs == ()
    assert run.ab3_frontier_refs == ()
    assert run.skipped_reasons == ("ab_live_disabled",)


def test_ab_int_repeated_ticks_bounded_growth() -> None:
    run_one = run_ab_live_subject_tick_contour(
        _input(
            tick_id="ab-int:repeated:1",
            ap01_request_refs=("ap01:req:1",),
            action_effect_refs=("action_effect:1",),
        ),
        _enabled_config(),
    )
    for idx in range(2, 6):
        run_n = run_ab_live_subject_tick_contour(
            _input(
                tick_id=f"ab-int:repeated:{idx}",
                ap01_request_refs=("ap01:req:1",),
                action_effect_refs=("action_effect:1",),
            ),
            _enabled_config(),
        )
        assert run_n.ab_live_counters.performance_guard_triggered_count == 0
        assert run_n.ab_live_counters.ab1_digest_count == run_one.ab_live_counters.ab1_digest_count
        assert run_n.ab_live_counters.ab2_seed_count == run_one.ab_live_counters.ab2_seed_count
        assert run_n.ab_live_counters.ab3_frontier_count == run_one.ab_live_counters.ab3_frontier_count


def test_ab_int_outputs_keep_public_basis_refs_when_stages_run() -> None:
    run = run_ab_live_subject_tick_contour(
        _input(
            ap01_request_refs=("ap01:req:1",),
            action_effect_refs=("action_effect:1",),
        ),
        _enabled_config(),
    )
    assert run.public_basis_refs
    for stage in run.stage_traces:
        if stage.ran:
            assert stage.input_refs or stage.output_refs


def test_ab_int_ablation_disable_ab1_blocks_seed_and_frontier() -> None:
    run = run_ab_live_subject_tick_contour(
        _input(),
        _enabled_config(run_ab1=False),
    )
    assert run.ab1_event_digest_refs == ()
    assert run.ab2_seed_set_refs == ()
    assert run.ab3_frontier_refs == ()


def test_ab_int_ablation_remove_prior_frontier_blocks_ab5() -> None:
    run = run_ab_live_subject_tick_contour(
        _input(prior_frontier_refs=(), public_effect_refs=("effect:1",), action_effect_refs=("action_effect:1",)),
        _enabled_config(run_ab3=False),
    )
    assert run.ab5_update_refs == ()


def test_ab_int_ablation_remove_discriminating_tests_blocks_ab4() -> None:
    frontier = replace(_frontier(ambiguous=False), discriminating_tests=(), unresolved_conflicts=(), missing_evidence=())
    run = run_ab_live_subject_tick_contour(
        _input(
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
        ),
        _enabled_config(run_ab1=False, run_ab2=False, run_ab3=False),
    )
    assert run.ab4_epistemic_basis_refs == ()


def test_ab_int_ablation_remove_recipe_candidate_refs_blocks_ab7() -> None:
    frontier = _frontier(ambiguous=False)
    run = run_ab_live_subject_tick_contour(
        _input(
            prior_frontier_refs=(frontier.frontier_id,),
            prior_frontier_object=frontier,
            recipe_candidate_refs=(),
            precursor_candidate_refs=(),
        ),
        _enabled_config(),
    )
    assert run.ab7_constraint_refs == ()
