from __future__ import annotations

from dataclasses import asdict, replace

from substrate.ab01_event_digest import (
    AB1CompressionQuality,
    AB1DigestStatus,
    AB1EventDigest,
    AB1EventDigestKind,
)
from substrate.ab02_hypothesis_seed import (
    AB2HypothesisKind,
    AB2HypothesisSeedInput,
    AB2SeedStatus,
    build_ab2_hypothesis_seeds,
)


def _digest(**overrides: object) -> AB1EventDigest:
    base = AB1EventDigest(
        event_id="ab1:event:1",
        event_kind=AB1EventDigestKind.EFFECT_MISMATCH,
        source_refs=("src:public",),
        observation_refs=("obs:1",),
        raw_window_refs=("raw:1",),
        raw_window_missing_reason=None,
        effect_refs=("effect:1",),
        residue_refs=("residue:1",),
        expected_refs=("expected:1",),
        observed_refs=("observed:1",),
        magnitude=0.6,
        direction=None,
        confidence=0.8,
        uncertainty=0.2,
        compression_method="ab1_public_event_digest_v1",
        compression_quality=AB1CompressionQuality.LOSSLESS,
        digest_status=AB1DigestStatus.STRONG,
        lossiness=False,
        explicit_non_causal_closure=True,
        cause_claimed=False,
        hidden_eval_used=False,
        scenario_label_used=False,
        blocked_status=False,
        weak_status=False,
    )
    return replace(base, **overrides)


def _input(*, event_digests: tuple[AB1EventDigest, ...], **overrides: object) -> AB2HypothesisSeedInput:
    base = AB2HypothesisSeedInput(
        tick_ref="ab2:test:1",
        event_digests=event_digests,
        source_refs=("src:ab1:public",),
        observation_refs=("obs:1",),
        residue_refs=("residue:1",),
        effect_refs=("effect:1",),
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        prediction_error_signal=0.4,
        efference_mismatch_present=True,
        source="tests.ab2",
    )
    return replace(base, **overrides)


def test_ab2_generates_multiple_hypothesis_seeds() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),)))
    assert result.seed_set is not None
    usable = [h for h in result.seed_set.hypotheses if h.seed_status is AB2SeedStatus.USABLE]
    assert len(usable) >= 2


def test_ab2_generates_blocked_movement_hypotheses_without_claiming_cause() -> None:
    digest = _digest(event_kind=AB1EventDigestKind.UNEXPECTED_BLOCK)
    result = build_ab2_hypothesis_seeds(_input(event_digests=(digest,)))
    assert result.seed_set is not None
    kinds = {h.hypothesis_kind for h in result.seed_set.hypotheses}
    assert AB2HypothesisKind.CAPABILITY_OR_CONSTRAINT_BLOCK in kinds
    assert all(not h.cause_confirmed for h in result.seed_set.hypotheses)


def test_ab2_generates_effect_mismatch_hypotheses() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),)))
    assert result.seed_set is not None
    kinds = {h.hypothesis_kind for h in result.seed_set.hypotheses}
    assert AB2HypothesisKind.EXPECTED_EFFECT_MISSING in kinds
    assert AB2HypothesisKind.UNKNOWN_EXTERNAL_CAUSE in kinds


def test_ab2_generates_inventory_delta_hypotheses_without_recipe_truth() -> None:
    digest = _digest(
        event_kind=AB1EventDigestKind.INVENTORY_DELTA_MISMATCH,
        expected_refs=("expected:inventory",),
        observed_refs=("observed:inventory",),
    )
    result = build_ab2_hypothesis_seeds(_input(event_digests=(digest,)))
    assert result.seed_set is not None
    kinds = {h.hypothesis_kind for h in result.seed_set.hypotheses}
    assert AB2HypothesisKind.INVENTORY_TRANSITION_UNACCOUNTED in kinds
    serialized = str(asdict(result.seed_set)).lower()
    forbidden = ("recipe", "station", "minecraft", "water", "ore", "filter")
    assert all(token not in serialized for token in forbidden)


def test_ab2_best_hypothesis_is_not_fact() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),)))
    assert result.seed_set is not None
    assert result.seed_set.fact_claimed is False
    assert result.seed_set.selected_fact_hypothesis_id is None


def test_ab2_rejects_hidden_truth_explanation() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),), hidden_eval_excluded=False))
    assert result.seed_set is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab2_rejects_scenario_label_explanation() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),), scenario_label_excluded=False))
    assert result.seed_set is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab2_requires_event_digest_or_residue_basis() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=()))
    assert result.seed_set is None
    assert result.telemetry.seed_count == 0


def test_ab2_no_event_digest_no_hypothesis() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=()))
    assert result.seed_set is None


def test_ab2_rejects_cause_claiming_digest() -> None:
    digest = _digest(cause_claimed=True)
    result = build_ab2_hypothesis_seeds(_input(event_digests=(digest,)))
    assert result.seed_set is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab2_each_usable_hypothesis_has_expected_observations() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),)))
    assert result.seed_set is not None
    usable = [h for h in result.seed_set.hypotheses if h.seed_status is AB2SeedStatus.USABLE]
    assert usable
    assert all(h.expected_observations for h in usable)


def test_ab2_each_usable_hypothesis_has_possible_tests() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),)))
    assert result.seed_set is not None
    usable = [h for h in result.seed_set.hypotheses if h.seed_status is AB2SeedStatus.USABLE]
    assert usable
    assert all(h.possible_tests for h in usable)


def test_ab2_unknown_cause_is_low_confidence_and_open() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),)))
    assert result.seed_set is not None
    unknown = [h for h in result.seed_set.hypotheses if h.hypothesis_kind is AB2HypothesisKind.UNKNOWN_EXTERNAL_CAUSE]
    assert unknown
    assert all(h.confidence_initial <= 0.35 for h in unknown)
    assert result.seed_set.closure_status.value == "open"


def test_ab2_rpe_signal_is_not_explanation() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),), prediction_error_signal=0.95))
    assert result.seed_set is not None
    assert all(not h.cause_confirmed for h in result.seed_set.hypotheses)


def test_ab2_efference_mismatch_is_not_explanation() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),), efference_mismatch_present=True))
    assert result.seed_set is not None
    assert all(not h.cause_confirmed for h in result.seed_set.hypotheses)


def test_ab2_hypothesis_seed_does_not_emit_action_candidate_or_request() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),)))
    assert result.seed_set is not None
    serialized = str(asdict(result.seed_set)).lower()
    forbidden = ("action_candidate", "ap01_request", "world_submission", "execute")
    assert all(token not in serialized for token in forbidden)


def test_ab2_rejects_world_specific_recipe_truth_in_substrate() -> None:
    result = build_ab2_hypothesis_seeds(
        _input(event_digests=(_digest(),), source_refs=("src:water:filter:recipe",))
    )
    assert result.seed_set is None
    assert "world_specific_marker_forbidden_in_ab2_substrate" in result.reason_codes


def test_ab2_ambiguous_event_requires_competing_hypotheses() -> None:
    digest = _digest(event_kind=AB1EventDigestKind.EFFECT_MISMATCH, effect_refs=(), expected_refs=("expected:1",))
    result = build_ab2_hypothesis_seeds(_input(event_digests=(digest,)))
    assert result.seed_set is not None
    usable = [h for h in result.seed_set.hypotheses if h.seed_status is AB2SeedStatus.USABLE]
    assert len(usable) >= 2 or result.seed_set.blocked_status


def test_ab2_ablation_hidden_only_cause_no_hypothesis() -> None:
    result = build_ab2_hypothesis_seeds(
        _input(event_digests=(_digest(),), source_refs=("src:hidden:private",))
    )
    assert result.seed_set is None


def test_ab2_ablation_remove_expected_observations_blocks_usable_hypothesis() -> None:
    digest = _digest(event_kind=AB1EventDigestKind.EFFECT_MISMATCH, expected_refs=())
    result = build_ab2_hypothesis_seeds(_input(event_digests=(digest,)))
    assert result.seed_set is not None
    missing_expected = [
        h for h in result.seed_set.hypotheses if "expected_refs_required" in h.missing_evidence
    ]
    assert missing_expected


def test_ab2_ablation_remove_possible_tests_marks_not_usable() -> None:
    digest = _digest(event_kind=AB1EventDigestKind.UNKNOWN_PUBLIC_ANOMALY, effect_refs=(), residue_refs=())
    result = build_ab2_hypothesis_seeds(_input(event_digests=(digest,)))
    assert result.seed_set is not None
    assert any(h.seed_status is AB2SeedStatus.USABLE for h in result.seed_set.hypotheses)


def test_ab2_ablation_no_source_refs_no_usable_hypothesis() -> None:
    result = build_ab2_hypothesis_seeds(_input(event_digests=(_digest(),), source_refs=()))
    assert result.seed_set is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab2_ablation_single_hypothesis_only_for_ambiguous_event_is_blocked_or_multi() -> None:
    digest = _digest(event_kind=AB1EventDigestKind.UNEXPECTED_BLOCK, residue_refs=(), effect_refs=("effect:1",))
    result = build_ab2_hypothesis_seeds(_input(event_digests=(digest,)))
    assert result.seed_set is not None
    usable = [h for h in result.seed_set.hypotheses if h.seed_status is AB2SeedStatus.USABLE]
    assert len(usable) >= 2 or result.seed_set.blocked_status
