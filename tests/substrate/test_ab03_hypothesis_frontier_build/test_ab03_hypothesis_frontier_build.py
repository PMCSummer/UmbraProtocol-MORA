from __future__ import annotations

from dataclasses import asdict, replace

from substrate.ab01_event_digest import (
    AB1CompressionQuality,
    AB1DigestStatus,
    AB1EventDigest,
    AB1EventDigestKind,
)
from substrate.ab02_hypothesis_seed import AB2HypothesisSeedInput, build_ab2_hypothesis_seeds
from substrate.ab03_hypothesis_frontier import AB3FrontierInput, AB3SupportBucket, build_ab3_hypothesis_frontier


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


def _ab2_seed_set_from_digest(digest: AB1EventDigest):
    seed_result = build_ab2_hypothesis_seeds(
        AB2HypothesisSeedInput(
            tick_ref="ab2:test:1",
            event_digests=(digest,),
            source_refs=("src:ab2:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab3",
        )
    )
    assert seed_result.seed_set is not None
    return seed_result.seed_set


def _frontier_input(seed_set, **overrides: object) -> AB3FrontierInput:
    base = AB3FrontierInput(
        tick_ref="ab3:test:1",
        seed_set=seed_set,
        source_refs=("src:ab3:public",),
        observation_refs=("obs:1",),
        residue_refs=("residue:1",),
        effect_refs=("effect:1",),
        disconfirming_evidence_refs=(),
        ambiguous_evidence=False,
        require_competing_hypotheses=True,
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.ab3",
    )
    return replace(base, **overrides)


def test_ab3_frontier_preserves_multiple_hypotheses() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    assert len(result.frontier.hypotheses) >= 2


def test_ab3_builds_frontier_from_ab2_blocked_movement_seeds() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest(event_kind=AB1EventDigestKind.UNEXPECTED_BLOCK))
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    assert result.frontier.closure_status.value in {"open", "provisionally_ranked"}


def test_ab3_builds_frontier_from_ab2_effect_mismatch_seeds() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest(event_kind=AB1EventDigestKind.EFFECT_MISMATCH))
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    assert result.frontier.source_event_refs


def test_ab3_builds_frontier_from_ab2_inventory_delta_seeds() -> None:
    seed_set = _ab2_seed_set_from_digest(
        _digest(event_kind=AB1EventDigestKind.INVENTORY_DELTA_MISMATCH, expected_refs=("expected:inventory",))
    )
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    assert len(result.frontier.hypotheses) >= 2


def test_ab3_leader_is_not_fact() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    assert result.frontier.fact_claimed is False
    assert result.frontier.selected_fact_hypothesis_id is None
    assert result.frontier.cause_confirmed is False


def test_ab3_ambiguous_evidence_keeps_open() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set, ambiguous_evidence=True))
    assert result.frontier is not None
    assert result.frontier.closure_status.value == "open"


def test_ab3_confidence_requires_evidence_refs() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    seed = seed_set.hypotheses[0]
    weakened = replace(seed, event_refs=(), residue_refs=(), effect_refs=(), source_refs=())
    modified = replace(seed_set, hypotheses=(weakened,))
    result = build_ab3_hypothesis_frontier(_frontier_input(modified, require_competing_hypotheses=False))
    assert result.frontier is not None
    record = result.frontier.hypotheses[0]
    assert record.evidence_refs == ()
    assert record.support_score is None


def test_ab3_missing_evidence_blocks_resolution() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    first = seed_set.hypotheses[0]
    first_with_missing = replace(first, missing_evidence=("expected_refs_required",))
    seed_set = replace(seed_set, hypotheses=(first_with_missing, *seed_set.hypotheses[1:]))
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    assert result.frontier.missing_evidence
    assert result.frontier.closure_status.value in {"open", "blocked"}


def test_ab3_discriminating_tests_present_for_competing_hypotheses() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    assert result.frontier.discriminating_tests


def test_ab3_rejects_hidden_eval_frontier_basis() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set, hidden_eval_excluded=False))
    assert result.frontier is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab3_rejects_scenario_label_frontier_basis() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set, scenario_label_excluded=False))
    assert result.frontier is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab3_rejects_cause_claiming_seed_set() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    forced = replace(seed_set, fact_claimed=True)
    result = build_ab3_hypothesis_frontier(_frontier_input(forced))
    assert result.frontier is None
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab3_frontier_does_not_emit_action_candidate_or_request() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    serialized = str(asdict(result.frontier)).lower()
    assert "action_candidate" not in serialized
    assert "ap01_request" not in serialized


def test_ab3_frontier_does_not_select_epistemic_action() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    assert result.frontier is not None
    serialized = str(asdict(result.frontier)).lower()
    assert "selected_epistemic_action" not in serialized
    assert "expected_information_gain" not in serialized


def test_ab3_single_hypothesis_for_ambiguous_event_blocks_frontier() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    modified = replace(seed_set, hypotheses=(seed_set.hypotheses[0],))
    result = build_ab3_hypothesis_frontier(_frontier_input(modified, ambiguous_evidence=True))
    assert result.frontier is not None
    assert result.frontier.closure_status.value == "blocked"


def test_ab3_disconfirming_evidence_lowers_support() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    baseline = build_ab3_hypothesis_frontier(_frontier_input(seed_set))
    disconfirm = build_ab3_hypothesis_frontier(
        _frontier_input(seed_set, disconfirming_evidence_refs=tuple(seed_set.source_event_refs))
    )
    assert baseline.frontier is not None and disconfirm.frontier is not None
    base_supported = sum(1 for h in baseline.frontier.hypotheses if h.support_bucket is AB3SupportBucket.SUPPORTED)
    disconfirmed = sum(1 for h in disconfirm.frontier.hypotheses if h.support_bucket is AB3SupportBucket.CONTRADICTED)
    assert disconfirmed >= 1
    assert disconfirmed >= base_supported


def test_ab3_unresolved_conflicts_are_preserved() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set, ambiguous_evidence=True))
    assert result.frontier is not None
    assert result.frontier.unresolved_conflicts


def test_ab3_rejects_world_specific_recipe_truth_in_substrate() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    result = build_ab3_hypothesis_frontier(_frontier_input(seed_set, source_refs=("src:water:filter:recipe",)))
    assert result.frontier is None
    assert "world_specific_marker_forbidden_in_ab3_substrate" in result.reason_codes


def test_ab3_confidence_precision_degrades_without_support() -> None:
    seed_set = _ab2_seed_set_from_digest(_digest())
    seed = seed_set.hypotheses[0]
    weakened = replace(seed, confidence_initial=0.95, event_refs=(), residue_refs=(), effect_refs=(), source_refs=())
    modified = replace(seed_set, hypotheses=(weakened,))
    result = build_ab3_hypothesis_frontier(_frontier_input(modified, require_competing_hypotheses=False))
    assert result.frontier is not None
    assert result.frontier.hypotheses[0].confidence <= 0.2
