from __future__ import annotations

from experiments.embodied_playground.ab1_event_digest_probe import run_ab1_probe_case
from substrate.ab01_event_digest import AB1EventDigestKind


def test_ab1_probe_uses_p10_blocked_movement_effect() -> None:
    result = run_ab1_probe_case("blocked_movement_effect")
    assert len(result.digests) == 1
    digest = result.digests[0]
    assert digest.event_kind is AB1EventDigestKind.UNEXPECTED_BLOCK
    assert digest.effect_refs


def test_ab1_probe_uses_p10_pickup_inventory_delta_effect() -> None:
    result = run_ab1_probe_case("pickup_inventory_delta")
    assert len(result.digests) == 1
    assert result.digests[0].event_kind is AB1EventDigestKind.INVENTORY_DELTA_MISMATCH


def test_ab1_probe_no_hidden_eval_digest() -> None:
    result = run_ab1_probe_case("hidden_eval_only")
    assert result.digests == ()
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab1_probe_event_digest_feeds_no_ap01_request() -> None:
    result = run_ab1_probe_case("effect_mismatch")
    assert len(result.digests) == 1
    serialized = str(result.digests[0]).lower()
    assert "ap01_request" not in serialized
    assert "action_candidate" not in serialized


def test_ab1_probe_strict_no_auto_builder_compatible() -> None:
    result = run_ab1_probe_case("blocked_movement_effect")
    digest = result.digests[0]
    assert digest.source_refs
    assert digest.observation_refs
    assert digest.effect_refs
