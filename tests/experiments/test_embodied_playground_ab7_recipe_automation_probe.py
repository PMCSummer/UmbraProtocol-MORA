from __future__ import annotations

from experiments.embodied_playground.ab7_recipe_automation_probe import run_ab7_probe_case


def test_ab7_probe_uses_p15_candidate() -> None:
    run = run_ab7_probe_case("p15_candidate_bound_to_ab_frontier")
    assert run.frame is not None
    assert run.frame.recipe_candidate_refs


def test_ab7_probe_uses_p13_gate() -> None:
    run = run_ab7_probe_case("p15_candidate_requires_p13_gate")
    assert run.frame is not None
    assert "p13_maturity_gate_refs_required" in run.frame.blocked_reasons


def test_ab7_probe_uses_p14_affordance() -> None:
    run = run_ab7_probe_case("p15_candidate_bound_to_ab_frontier")
    assert run.frame is not None
    assert run.frame.p14_station_affordance_refs


def test_ab7_probe_blocks_without_ab_frontier() -> None:
    run = run_ab7_probe_case("blocks_without_ab_frontier")
    assert run.frame is not None
    assert "ab_frontier_refs_required" in run.frame.blocked_reasons


def test_ab7_probe_blocks_with_active_confounder() -> None:
    run = run_ab7_probe_case("active_confounder_blocks_recipe_maturity")
    assert run.frame is not None
    assert "active_confounder_requires_resolution" in run.frame.blocked_reasons


def test_ab7_probe_no_hidden_eval_rule() -> None:
    run = run_ab7_probe_case("protected_eval_only_rule_rejected")
    assert run.frame is None
    assert "protected_evaluator_only_rule_forbidden" in run.reason_codes


def test_ab7_probe_no_action_request_or_world_submission() -> None:
    run = run_ab7_probe_case("recipe_candidate_does_not_emit_action")
    assert run.frame is not None
    assert run.frame.action_request_emitted is False
    assert run.frame.world_submission_emitted is False


def test_ab7_probe_preserves_unresolved_recipe_frontier() -> None:
    run = run_ab7_probe_case("ambiguous_recipe_effect_preserves_frontier")
    assert run.frame is not None
    assert run.frame.bindings
    assert run.frame.bindings[0].unresolved_conflicts
