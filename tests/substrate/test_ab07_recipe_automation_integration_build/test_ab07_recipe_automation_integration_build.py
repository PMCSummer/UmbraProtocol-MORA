from __future__ import annotations

from dataclasses import replace

from substrate.ab07_recipe_automation_integration import (
    AB7PrecursorCandidateRecord,
    AB7RecipeAutomationInput,
    AB7RecipeCandidateRecord,
    build_ab7_recipe_automation_integration,
)


def _recipe(**overrides: object) -> AB7RecipeCandidateRecord:
    base = AB7RecipeCandidateRecord(
        recipe_candidate_ref="candidate:recipe_a",
        station_ref="station:generic_station",
        input_refs=("input:item_a",),
        output_refs=("output:item_b",),
        effect_refs=("effect:output_appeared",),
        supporting_trace_refs=("trace:1", "trace:2"),
        disconfirming_trace_refs=(),
        p13_schema_candidate_refs=("p13:schema:1",),
        confounder_refs=(),
        missing_evidence=(),
        maturity_status="provisional_candidate",
        maturity_score=0.6,
        hidden_recipe_used=False,
        protected_eval_used=False,
    )
    return replace(base, **overrides)


def _precursor() -> AB7PrecursorCandidateRecord:
    return AB7PrecursorCandidateRecord(
        precursor_candidate_ref="candidate:precursor_a",
        precursor_refs=("input:item_a",),
        effect_refs=("effect:output_appeared",),
        support_status="provisional",
        missing_evidence=(),
    )


def _input(**overrides: object) -> AB7RecipeAutomationInput:
    base = AB7RecipeAutomationInput(
        tick_ref="ab7:test:1",
        recipe_candidates=(_recipe(),),
        precursor_candidates=(_precursor(),),
        lived_trace_refs=("trace:1", "trace:2"),
        p13_credit_refs=("p13:credit:1",),
        p14_station_affordance_refs=("p14:affordance:1",),
        ab_event_digest_refs=("ab1:event:1",),
        ab_hypothesis_seed_refs=("ab2:seed:1",),
        ab_frontier_refs=("ab3:frontier:1",),
        ab_update_refs=("ab5:update:1",),
        ab_attribution_refs=("ab6:frame:1",),
        unresolved_frontier_refs=("ab3:conflict:1",),
        missing_evidence_refs=(),
        disconfirming_evidence_refs=(),
        active_confounder_refs=(),
        public_effect_refs=("effect:output_appeared",),
        public_input_refs=("input:item_a",),
        protected_eval_only_rule=False,
        ambiguous_frontier=False,
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.ab7",
    )
    return replace(base, **overrides)


def test_ab7_binds_p15_candidate_to_ab_frontier_without_fact_claim() -> None:
    run = build_ab7_recipe_automation_integration(_input())
    assert run.frame is not None
    assert run.frame.bindings
    assert run.frame.fact_claimed is False
    assert run.frame.cause_confirmed is False
    assert run.frame.bindings[0].unresolved_conflicts == ("ab3:conflict:1",)


def test_ab7_requires_p13_maturity_gate_refs() -> None:
    candidate = _recipe(p13_schema_candidate_refs=())
    run = build_ab7_recipe_automation_integration(_input(recipe_candidates=(candidate,), p13_credit_refs=()))
    assert run.frame is not None
    assert "maturity_blocked" in run.frame.blocked_reasons
    assert run.frame.automation_readiness[0].readiness_status.value in {"blocked", "automation_forbidden_in_ab7"}


def test_ab7_repeated_trace_with_ab_support_remains_provisional() -> None:
    run = build_ab7_recipe_automation_integration(_input())
    assert run.frame is not None
    readiness = run.frame.automation_readiness[0].readiness_status.value
    assert readiness in {"evidence_required", "provisional_only", "not_ready"}
    assert run.frame.mature_recipe_claimed is False


def test_ab7_disconfirming_effect_blocks_recipe_integration() -> None:
    candidate = _recipe(disconfirming_trace_refs=("trace:disconfirm",))
    run = build_ab7_recipe_automation_integration(_input(recipe_candidates=(candidate,)))
    assert run.frame is not None
    assert "disconfirming_trace_present" in run.frame.blocked_reasons


def test_ab7_active_confounder_blocks_maturity() -> None:
    candidate = _recipe(confounder_refs=("confounder:c1",))
    run = build_ab7_recipe_automation_integration(
        _input(recipe_candidates=(candidate,), active_confounder_refs=("confounder:c1",))
    )
    assert run.frame is not None
    assert "active_confounder_requires_resolution" in run.frame.blocked_reasons


def test_ab7_requires_p14_station_affordance_refs() -> None:
    run = build_ab7_recipe_automation_integration(_input(p14_station_affordance_refs=()))
    assert run.frame is not None
    assert "p14_station_affordance_refs_required" in run.frame.blocked_reasons


def test_ab7_rejects_protected_eval_only_rule() -> None:
    run = build_ab7_recipe_automation_integration(_input(protected_eval_only_rule=True))
    assert run.frame is None
    assert "protected_evaluator_only_rule_forbidden" in run.reason_codes


def test_ab7_one_success_trace_not_automation() -> None:
    candidate = _recipe(supporting_trace_refs=("trace:1",))
    run = build_ab7_recipe_automation_integration(_input(recipe_candidates=(candidate,), lived_trace_refs=("trace:1",)))
    assert run.frame is not None
    assert run.frame.automation_claimed is False
    assert run.frame.automation_readiness[0].readiness_status.value in {"blocked", "provisional_only"}


def test_ab7_ambiguous_recipe_effect_preserves_frontier() -> None:
    run = build_ab7_recipe_automation_integration(
        _input(ambiguous_frontier=True, unresolved_frontier_refs=("ab3:conflict:1", "ab3:conflict:2"))
    )
    assert run.frame is not None
    assert run.frame.bindings[0].unresolved_conflicts
    assert run.frame.fact_claimed is False


def test_ab7_does_not_emit_action_request() -> None:
    run = build_ab7_recipe_automation_integration(_input())
    assert run.frame is not None
    assert run.frame.action_request_emitted is False
    assert run.frame.world_submission_emitted is False


def test_ab7_ab6_attribution_is_not_recipe_oracle() -> None:
    run = build_ab7_recipe_automation_integration(_input(ab_attribution_refs=("ab6:frame:1",)))
    assert run.frame is not None
    assert run.frame.bindings[0].fact_status == "not_fact"


def test_ab7_ab5_update_is_not_recipe_oracle() -> None:
    run = build_ab7_recipe_automation_integration(_input(ab_update_refs=("ab5:update:1",)))
    assert run.frame is not None
    assert run.frame.mature_recipe_claimed is False


def test_ab7_missing_evidence_is_preserved() -> None:
    candidate = _recipe(missing_evidence=("input_quality_unknown",))
    run = build_ab7_recipe_automation_integration(_input(recipe_candidates=(candidate,), missing_evidence_refs=("trace_gap",)))
    assert run.frame is not None
    assert "input_quality_unknown" in run.frame.missing_evidence_requirements
    assert "trace_gap" in run.frame.missing_evidence_requirements


def test_ab7_report_does_not_overclaim_automation() -> None:
    run = build_ab7_recipe_automation_integration(_input())
    assert run.frame is not None
    lowered = run.frame.claim_boundary.lower()
    assert "automation achieved" not in lowered
    assert "mature recipe learned" not in lowered
    assert "consciousness proven" not in lowered
