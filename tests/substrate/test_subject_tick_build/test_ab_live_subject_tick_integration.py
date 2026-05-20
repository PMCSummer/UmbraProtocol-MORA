from __future__ import annotations

from substrate.ab_subject_tick_integration import ABLiveTickConfig, ABLiveTickInput
from substrate.ab01_event_digest import AB1EventDigestInput, build_ab1_event_digests
from substrate.ab02_hypothesis_seed import AB2HypothesisSeedInput, build_ab2_hypothesis_seeds
from substrate.ab03_hypothesis_frontier import AB3FrontierInput, build_ab3_hypothesis_frontier
from substrate.acp01_internal_action_candidate_production import (
    ACP01ActionSurfaceBasis,
    ACP01CandidateProductionInput,
    ACP01CapabilityBasis,
    ACP01CapabilityStatus,
    ACP01InternalDriveBasis,
    ACP01ObservationBasis,
    ACP01VisibleObjectBasis,
)
from substrate.subject_tick import SubjectTickContext
from tests.substrate.subject_tick_testkit import build_subject_tick
from tests.substrate.test_subject_tick_build import test_v03_subject_tick_integration as v03_cases


def _frontier():
    ab1 = build_ab1_event_digests(
        AB1EventDigestInput(
            tick_ref="ab-int:st-frontier:ab1",
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            raw_window_refs=("obs:1",),
            effect_refs=("effect:1",),
            residue_refs=("residue:1",),
            expected_refs=("expected:1",),
            observed_refs=("observed:1",),
            anomaly_markers=("uncertain:1",),
            effect_status="blocked",
            magnitude=0.6,
            noise_level=0.1,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab_int",
        )
    )
    ab2 = build_ab2_hypothesis_seeds(
        AB2HypothesisSeedInput(
            tick_ref="ab-int:st-frontier:ab2",
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
    ab3 = build_ab3_hypothesis_frontier(
        AB3FrontierInput(
            tick_ref="ab-int:st-frontier:ab3",
            seed_set=ab2.seed_set,
            source_refs=("src:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            disconfirming_evidence_refs=("conflict:1",),
            ambiguous_evidence=True,
            require_competing_hypotheses=True,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab_int",
        )
    )
    return ab3.frontier


def _acp_input() -> ACP01CandidateProductionInput:
    return ACP01CandidateProductionInput(
        tick_ref="subject_tick:ab_int:acp01",
        observation_basis=ACP01ObservationBasis(
            observation_id="obs:acp:1",
            body_ref="subject_a:body",
            location_ref="loc:1",
            orientation="north",
            inventory_ref="subject_a:inventory",
            visible_object_refs=("item:a",),
            action_surface_refs=("surface:pickup",),
            previous_effect_refs=(),
        ),
        internal_drive_bases=(
            ACP01InternalDriveBasis(
                drive_ref="drive:1",
                drive_kind="need_item",
                resource_or_goal_ref="item:a",
                urgency_level=0.6,
                source_ref="tests.ab_int",
                drive_class="pickup_intent",
                target_object_refs=("item:a",),
                target_resource_refs=("item:a",),
                target_affordance_refs=("pickup",),
                allowed_action_kinds=("pickup",),
                required_capability_refs=("proximity", "inventory_capacity"),
                relevance_basis_refs=("basis:initial",),
            ),
        ),
        visible_object_bases=(
            ACP01VisibleObjectBasis(
                object_ref="item:a",
                object_kind="item",
                location_ref="loc:1",
                public_properties={},
                confidence=0.9,
            ),
        ),
        action_surface_bases=(
            ACP01ActionSurfaceBasis(
                surface_ref="surface:pickup",
                surface_kind="pickup",
                target_ref="item:a",
                action_kinds=("pickup",),
            ),
        ),
        capability_bases=(
            ACP01CapabilityBasis(
                capability_ref="cap:proximity:item:a",
                capability_kind="proximity",
                target_ref="item:a",
                status=ACP01CapabilityStatus.AVAILABLE,
            ),
            ACP01CapabilityBasis(
                capability_ref="cap:inventory",
                capability_kind="inventory_capacity",
                target_ref=None,
                status=ACP01CapabilityStatus.AVAILABLE,
            ),
        ),
        effect_feedback_bases=(),
        private_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.ab_int",
    )


def _tick(case_id: str, context: SubjectTickContext | None = None):
    return build_subject_tick(
        case_id=case_id,
        energy=72.0,
        cognitive=58.0,
        safety=67.0,
        unresolved_preference=False,
        context=context,
    )


def test_subject_tick_runs_ab_live_contour_when_enabled() -> None:
    run = _tick(
        "ab-int:enabled",
        SubjectTickContext(
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=True),
            ab_live_input=ABLiveTickInput(
                tick_id="ab-int:enabled",
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
            ),
        ),
    )
    assert run.ab_live_result is not None
    assert run.ab_live_result.ab1_event_digest_refs


def test_subject_tick_exposes_ab_live_result_and_counters() -> None:
    run = _tick(
        "ab-int:counters",
        SubjectTickContext(
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=True),
            ab_live_input=ABLiveTickInput(
                tick_id="ab-int:counters",
                public_observation_refs=("obs:1",),
                public_effect_refs=("effect:1",),
                residue_refs=("residue:1",),
                uncertainty_refs=("uncertain:1",),
                conflict_refs=(),
                ap01_request_refs=("ap01:req:1",),
                action_effect_refs=("action_effect:1",),
                prior_frontier_refs=(),
                prior_ab_state_refs=(),
                recipe_candidate_refs=(),
                precursor_candidate_refs=(),
                value_chain_refs=(),
                factory_chain_refs=(),
            ),
        ),
    )
    assert run.ab_live_result is not None
    assert run.ab_live_counters["ab1_digest_count"] >= 1
    assert run.state.ab1_digest_count >= 1


def test_subject_tick_ab4_basis_is_available_before_acp01() -> None:
    frontier = _frontier()
    run = _tick(
        "ab-int:ab4-before-acp01",
        SubjectTickContext(
            acp01_candidate_production_input=_acp_input(),
            ab_live_attach_ab4_basis_to_acp01=True,
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=True),
            ab_live_input=ABLiveTickInput(
                tick_id="ab-int:ab4-before-acp01",
                public_observation_refs=("obs:1",),
                public_effect_refs=("effect:1",),
                residue_refs=("residue:1",),
                uncertainty_refs=("uncertain:1",),
                conflict_refs=("conflict:1",),
                ap01_request_refs=("ap01:req:1",),
                action_effect_refs=("action_effect:1",),
                prior_frontier_refs=(frontier.frontier_id,),
                prior_ab_state_refs=(),
                recipe_candidate_refs=(),
                precursor_candidate_refs=(),
                value_chain_refs=(),
                factory_chain_refs=(),
                prior_frontier_object=frontier,
            ),
        ),
    )
    assert run.ab_epistemic_basis_for_acp01
    assert run.state.ab_epistemic_basis_for_acp01


def test_subject_tick_ab_live_does_not_emit_ap01_request() -> None:
    run = _tick(
        "ab-int:no-ap01",
        SubjectTickContext(
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=True),
            ab_live_input=ABLiveTickInput(
                tick_id="ab-int:no-ap01",
                public_observation_refs=("obs:1",),
                public_effect_refs=("effect:1",),
                residue_refs=("residue:1",),
                uncertainty_refs=("uncertain:1",),
                conflict_refs=(),
                ap01_request_refs=("ap01:req:1",),
                action_effect_refs=("action_effect:1",),
                prior_frontier_refs=(),
                prior_ab_state_refs=(),
                recipe_candidate_refs=(),
                precursor_candidate_refs=(),
                value_chain_refs=(),
                factory_chain_refs=(),
            ),
        ),
    )
    assert run.ab_live_result is not None
    assert run.ab_live_result.action_request_emitted is False
    assert run.ab_live_result.world_submission_emitted is False


def test_subject_tick_ab_live_preserves_acp01_ap01_ordering() -> None:
    source = __import__("pathlib").Path("src/substrate/subject_tick/update.py").read_text(encoding="utf-8")
    lines = source.splitlines()

    def _first_runtime_call_line(token: str) -> int:
        for idx, line in enumerate(lines, start=1):
            lowered = line.lower()
            if token.lower() in lowered and "(" in lowered and "import " not in lowered:
                return idx
        raise AssertionError(f"runtime call not found for token={token}")

    acp_line = _first_runtime_call_line("build_acp01_internal_action_candidates")
    ap_line = _first_runtime_call_line("build_ap01_subject_action_publication")
    assert acp_line < ap_line


def test_subject_tick_ab_live_default_compatibility() -> None:
    baseline = _tick("ab-int:default-compat-baseline")
    disabled = _tick(
        "ab-int:default-compat-disabled",
        SubjectTickContext(
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=False),
        ),
    )
    assert baseline.state.final_execution_outcome == disabled.state.final_execution_outcome
    assert baseline.state.ap01_published_request_count == disabled.state.ap01_published_request_count
    assert disabled.state.ab_live_enabled is False


def test_subject_tick_ab_live_rejects_protected_eval_basis() -> None:
    run = _tick(
        "ab-int:protected-eval",
        SubjectTickContext(
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=True),
            ab_live_input=ABLiveTickInput(
                tick_id="ab-int:protected-eval",
                public_observation_refs=("obs:1",),
                public_effect_refs=("effect:1",),
                residue_refs=("residue:1",),
                uncertainty_refs=(),
                conflict_refs=(),
                ap01_request_refs=(),
                action_effect_refs=(),
                prior_frontier_refs=(),
                prior_ab_state_refs=(),
                recipe_candidate_refs=(),
                precursor_candidate_refs=(),
                value_chain_refs=(),
                factory_chain_refs=(),
                protected_eval_present=True,
            ),
        ),
    )
    assert run.ab_live_result is not None
    assert "protected_eval_present" in run.ab_live_result.blocked_reasons
    assert run.ab_live_result.ab1_event_digest_refs == ()


def test_subject_tick_ab_live_state_drift_limited_to_ab_fields() -> None:
    baseline = _tick("ab-int:drift-baseline")
    with_ab = _tick(
        "ab-int:drift-with-ab",
        SubjectTickContext(
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=True),
            ab_live_input=ABLiveTickInput(
                tick_id="ab-int:drift-with-ab",
                public_observation_refs=(),
                public_effect_refs=(),
                residue_refs=(),
                uncertainty_refs=(),
                conflict_refs=(),
                ap01_request_refs=(),
                action_effect_refs=(),
                prior_frontier_refs=(),
                prior_ab_state_refs=(),
                recipe_candidate_refs=(),
                precursor_candidate_refs=(),
                value_chain_refs=(),
                factory_chain_refs=(),
            ),
        ),
    )
    assert baseline.state.final_execution_outcome == with_ab.state.final_execution_outcome
    assert baseline.state.active_execution_mode == with_ab.state.active_execution_mode
    assert baseline.state.execution_stance == with_ab.state.execution_stance
    assert baseline.state.acp01_proposed_count == with_ab.state.acp01_proposed_count
    assert baseline.state.ap01_published_request_count == with_ab.state.ap01_published_request_count
    assert with_ab.state.ab_live_enabled is True


def test_subject_tick_ab_live_disabled_preserves_v03_protected_omission_path() -> None:
    baseline = v03_cases._result(
        "ab-int:v03-protected-baseline",
        context=v03_cases.replace(
            v03_cases._base_context("ab-int:v03-protected-baseline"),
            v01_act_candidates=(
                v03_cases._candidate(
                    act_id="assertion-ab-int-v03",
                    act_type=v03_cases.V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
                v03_cases._candidate(
                    act_id="promise-ab-int-v03",
                    act_type=v03_cases.V01ActType.PROMISE,
                    evidence_strength=0.62,
                ),
            ),
            v03_realization_input=v03_cases.V03RealizationInput(
                input_id="ab-int:v03-protected-input",
                inject_protected_omission_token="omit:promise-ab-int-v03",
            ),
        ),
    )
    with_disabled_ab_live = v03_cases._result(
        "ab-int:v03-protected-disabled-ab-live",
        context=v03_cases.replace(
            v03_cases._base_context("ab-int:v03-protected-disabled-ab-live"),
            ab_live_config=ABLiveTickConfig(enable_ab_live_contour=False),
            v01_act_candidates=(
                v03_cases._candidate(
                    act_id="assertion-ab-int-v03-disabled",
                    act_type=v03_cases.V01ActType.ASSERTION,
                    evidence_strength=0.97,
                ),
                v03_cases._candidate(
                    act_id="promise-ab-int-v03-disabled",
                    act_type=v03_cases.V01ActType.PROMISE,
                    evidence_strength=0.62,
                ),
            ),
            v03_realization_input=v03_cases.V03RealizationInput(
                input_id="ab-int:v03-protected-input-disabled",
                inject_protected_omission_token="omit:promise-ab-int-v03-disabled",
            ),
        ),
    )
    assert baseline.state.final_execution_outcome == with_disabled_ab_live.state.final_execution_outcome
    assert baseline.state.active_execution_mode == with_disabled_ab_live.state.active_execution_mode


def test_subject_tick_ab_live_repeated_ticks_without_new_evidence_stay_bounded() -> None:
    seen_trace_lengths: set[int] = set()
    for idx in range(1, 6):
        run = _tick(
            f"ab-int:bounded:{idx}",
            SubjectTickContext(
                ab_live_config=ABLiveTickConfig(enable_ab_live_contour=True),
                ab_live_input=ABLiveTickInput(
                    tick_id=f"ab-int:bounded:{idx}",
                    public_observation_refs=(),
                    public_effect_refs=(),
                    residue_refs=(),
                    uncertainty_refs=(),
                    conflict_refs=(),
                    ap01_request_refs=(),
                    action_effect_refs=(),
                    prior_frontier_refs=(),
                    prior_ab_state_refs=(),
                    recipe_candidate_refs=(),
                    precursor_candidate_refs=(),
                    value_chain_refs=(),
                    factory_chain_refs=(),
                ),
            ),
        )
        assert run.ab_live_result is not None
        assert run.ab_live_result.ab_live_counters.performance_guard_triggered_count == 0
        seen_trace_lengths.add(len(run.ab_live_result.stage_traces))
    assert seen_trace_lengths == {7}
