from __future__ import annotations

from experiments.embodied_playground.ab2_hypothesis_seed_probe import run_ab2_probe_case
from substrate.ab02_hypothesis_seed import AB2SeedStatus


def test_ab2_probe_uses_ab1_blocked_movement_digest() -> None:
    result = run_ab2_probe_case("blocked_movement_effect")
    assert result.seed_set is not None
    assert result.seed_set.source_event_refs
    assert any("unexpected_block" in ref for ref in result.seed_set.source_event_refs)


def test_ab2_probe_uses_ab1_pickup_inventory_delta_digest() -> None:
    result = run_ab2_probe_case("pickup_inventory_delta")
    assert result.seed_set is not None
    assert any("inventory_delta_mismatch" in ref for ref in result.seed_set.source_event_refs)


def test_ab2_probe_no_hidden_eval_hypothesis() -> None:
    result = run_ab2_probe_case("hidden_eval_only")
    assert result.seed_set is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab2_probe_hypotheses_feed_no_ap01_request() -> None:
    result = run_ab2_probe_case("effect_mismatch")
    assert result.seed_set is not None
    serialized = str(result.seed_set).lower()
    assert "ap01_request" not in serialized


def test_ab2_probe_does_not_modify_world_or_subject_action() -> None:
    result = run_ab2_probe_case("blocked_movement_effect")
    assert result.scope_marker.no_action_candidate_authority is True
    assert result.scope_marker.no_ap01_request_authority is True
    assert result.scope_marker.no_execution_authority is True


def test_ab2_probe_preserves_ab1_non_causal_boundary() -> None:
    result = run_ab2_probe_case("effect_mismatch")
    assert result.seed_set is not None
    assert result.seed_set.fact_claimed is False
    assert all(item.seed_status in {AB2SeedStatus.USABLE, AB2SeedStatus.BLOCKED} for item in result.seed_set.hypotheses)
