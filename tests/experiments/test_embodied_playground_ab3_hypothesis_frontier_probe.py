from __future__ import annotations

from experiments.embodied_playground.ab3_hypothesis_frontier_probe import run_ab3_probe_case


def test_ab3_probe_uses_ab2_blocked_movement_seeds() -> None:
    result = run_ab3_probe_case("blocked_movement_effect")
    assert result.frontier is not None
    assert result.frontier.source_seed_set_refs


def test_ab3_probe_uses_ab2_effect_mismatch_seeds() -> None:
    result = run_ab3_probe_case("effect_mismatch")
    assert result.frontier is not None
    assert len(result.frontier.hypotheses) >= 2


def test_ab3_probe_no_hidden_eval_frontier() -> None:
    result = run_ab3_probe_case("hidden_eval_only")
    assert result.frontier is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab3_probe_frontier_feeds_no_ap01_request() -> None:
    result = run_ab3_probe_case("effect_mismatch")
    assert result.frontier is not None
    serialized = str(result.frontier).lower()
    assert "ap01_request" not in serialized


def test_ab3_probe_does_not_modify_world_or_subject_action() -> None:
    result = run_ab3_probe_case("blocked_movement_effect")
    assert result.scope_marker.no_action_candidate_authority is True
    assert result.scope_marker.no_ap01_request_authority is True
    assert result.scope_marker.no_execution_authority is True


def test_ab3_probe_preserves_ab2_no_fact_boundary() -> None:
    result = run_ab3_probe_case("effect_mismatch")
    assert result.frontier is not None
    assert result.frontier.fact_claimed is False
    assert result.frontier.selected_fact_hypothesis_id is None
