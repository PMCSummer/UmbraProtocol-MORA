from __future__ import annotations

from experiments.embodied_playground.ab6_causal_attribution_probe import run_ab6_probe_case


def test_ab6_probe_uses_p11_self_caused_move() -> None:
    run = run_ab6_probe_case("self_action_correlated_effect")
    assert run.frame is not None
    assert "self_action" in run.frame.supported_attribution_kinds


def test_ab6_probe_uses_p11_world_only_change() -> None:
    run = run_ab6_probe_case("world_only_change")
    assert run.frame is not None
    assert "self_action" in run.frame.blocked_attribution_kinds


def test_ab6_probe_uses_p11_other_actor_change() -> None:
    run = run_ab6_probe_case("other_actor_change")
    assert run.frame is not None
    assert "other_actor" in run.frame.supported_attribution_kinds


def test_ab6_probe_uses_p11_mixed_cause() -> None:
    run = run_ab6_probe_case("mixed_self_world_effect")
    assert run.frame is not None
    assert run.frame.mixed_cause_preserved is True


def test_ab6_probe_uses_p11_unknown_effect() -> None:
    run = run_ab6_probe_case("unknown_unexplained_effect")
    assert run.frame is not None
    assert run.frame.unknown_preserved is True


def test_ab6_probe_no_hidden_eval_attribution() -> None:
    run = run_ab6_probe_case("hidden_eval_only_cause")
    assert run.frame is None
    assert "hidden_eval_exclusion_required" in run.reason_codes


def test_ab6_probe_preserves_ab5_no_fact_boundary() -> None:
    run = run_ab6_probe_case("self_action_correlated_effect")
    assert run.frame is not None
    assert run.frame.fact_claimed is False
    assert run.frame.cause_confirmed is False


def test_ab6_probe_no_action_request_emitted() -> None:
    run = run_ab6_probe_case("self_action_correlated_effect")
    assert run.frame is not None
    assert run.frame.action_request_emitted is False
