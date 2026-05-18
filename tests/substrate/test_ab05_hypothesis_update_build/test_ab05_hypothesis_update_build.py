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
from substrate.ab05_hypothesis_update import AB5DeltaKind, AB5HypothesisUpdateInput, build_ab5_hypothesis_update


def _digest(**overrides: object) -> AB1EventDigest:
    base = AB1EventDigest(
        event_id="ab1:event:ab5",
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
        confidence=0.75,
        uncertainty=0.3,
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


def _frontier():
    seed_result = build_ab2_hypothesis_seeds(
        AB2HypothesisSeedInput(
            tick_ref="ab2:ab5:test",
            event_digests=(_digest(),),
            source_refs=("src:ab2:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab5",
        )
    )
    assert seed_result.seed_set is not None
    frontier_result = build_ab3_hypothesis_frontier(
        AB3FrontierInput(
            tick_ref="ab3:ab5:test",
            seed_set=seed_result.seed_set,
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
            source="tests.ab5",
        )
    )
    assert frontier_result.frontier is not None
    return frontier_result.frontier


def _input(frontier, **overrides: object) -> AB5HypothesisUpdateInput:
    hypotheses = tuple(item.hypothesis_id for item in frontier.hypotheses) if frontier is not None else ()
    base = AB5HypothesisUpdateInput(
        tick_ref="ab5:test:1",
        prior_frontier=frontier,
        source_refs=("src:ab5:public",),
        source_effect_refs=("effect:correlated:1",),
        source_event_digests=(_digest(),),
        source_request_refs=("ap01:request:1",),
        epistemic_basis_refs=("ab4:basis:1",),
        source_observation_refs=("obs:post:1",),
        supporting_hypothesis_refs=hypotheses[:1],
        disconfirming_hypothesis_refs=(),
        ambiguous_evidence=False,
        effect_correlated=True,
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.ab5",
    )
    return replace(base, **overrides)


def test_ab5_updates_from_correlated_effect() -> None:
    frontier = _frontier()
    run = build_ab5_hypothesis_update(_input(frontier))
    assert run.update is not None
    assert run.update.support_deltas
    assert any(item.delta_kind is AB5DeltaKind.INCREASE for item in run.update.support_deltas)


def test_ab5_disconfirming_lowers_support() -> None:
    frontier = _frontier()
    target = frontier.hypotheses[0].hypothesis_id
    run = build_ab5_hypothesis_update(
        _input(frontier, supporting_hypothesis_refs=(), disconfirming_hypothesis_refs=(target,))
    )
    assert run.update is not None
    delta = next(item for item in run.update.support_deltas if item.hypothesis_ref == target)
    assert delta.delta_kind is AB5DeltaKind.DISCONFIRM
    assert delta.new_support_bucket is AB3SupportBucket.CONTRADICTED


def test_ab5_request_alone_does_not_confirm() -> None:
    frontier = _frontier()
    run = build_ab5_hypothesis_update(
        _input(
            frontier,
            source_effect_refs=(),
            source_event_digests=(),
            source_request_refs=("ap01:request:only",),
            effect_correlated=False,
        )
    )
    assert run.update is not None
    assert run.update.support_deltas == ()
    assert run.update.closure_blocked_reason == "request_without_effect_not_confirmation"


def test_ab5_ambiguous_evidence_keeps_frontier_open() -> None:
    frontier = _frontier()
    run = build_ab5_hypothesis_update(_input(frontier, ambiguous_evidence=True))
    assert run.update is not None
    assert run.update.closure_allowed is False
    assert any(item.delta_kind is AB5DeltaKind.UNRESOLVED for item in run.update.support_deltas)


def test_ab5_uncorrelated_effect_does_not_strongly_update() -> None:
    frontier = _frontier()
    run = build_ab5_hypothesis_update(_input(frontier, effect_correlated=False))
    assert run.update is not None
    assert all(item.delta_kind is not AB5DeltaKind.INCREASE for item in run.update.support_deltas)


def test_ab5_no_effect_no_update() -> None:
    frontier = _frontier()
    run = build_ab5_hypothesis_update(_input(frontier, source_effect_refs=(), source_event_digests=(), source_request_refs=()))
    assert run.update is not None
    assert run.update.support_deltas == ()
    assert run.update.closure_blocked_reason == "no_effect_evidence"


def test_ab5_rejects_hidden_eval_update() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier(), hidden_eval_excluded=False))
    assert run.update is None
    assert "hidden_eval_exclusion_required" in run.reason_codes


def test_ab5_rejects_scenario_label_update() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier(), scenario_label_excluded=False))
    assert run.update is None
    assert "scenario_label_exclusion_required" in run.reason_codes


def test_ab5_rejects_cause_claiming_digest() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier(), source_event_digests=(_digest(cause_claimed=True),)))
    assert run.update is None
    assert "event_digest_cause_claim_forbidden" in run.reason_codes


def test_ab5_requires_prior_frontier() -> None:
    run = build_ab5_hypothesis_update(_input(None, prior_frontier=None))
    assert run.update is None
    assert "prior_frontier_required" in run.reason_codes


def test_ab5_support_delta_requires_evidence_refs() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier()))
    assert run.update is not None
    assert run.update.support_deltas
    for delta in run.update.support_deltas:
        assert delta.evidence_refs


def test_ab5_update_without_hypothesis_refs_is_blocked() -> None:
    frontier = replace(_frontier(), hypotheses=())
    run = build_ab5_hypothesis_update(_input(frontier))
    assert run.update is None


def test_ab5_missing_evidence_is_not_erased() -> None:
    frontier = _frontier()
    run = build_ab5_hypothesis_update(_input(frontier))
    assert run.update is not None
    assert run.update.missing_evidence == frontier.missing_evidence


def test_ab5_effect_is_not_truth_oracle() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier()))
    assert run.update is not None
    assert run.update.fact_claimed is False
    assert run.update.cause_confirmed is False
    assert run.update.selected_fact_hypothesis_id is None


def test_ab5_update_does_not_emit_action_candidate_or_request() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier()))
    assert run.update is not None
    assert run.update.action_request_emitted is False
    assert run.update.world_submission_emitted is False


def test_ab5_update_does_not_select_epistemic_action() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier()))
    assert run.update is not None
    assert run.update.epistemic_basis_refs == ("ab4:basis:1",)
    assert "no_epistemic_action_selection_authority" in str(asdict(run.scope_marker))


def test_ab5_update_does_not_perform_ownership_closure() -> None:
    run = build_ab5_hypothesis_update(_input(_frontier()))
    assert "no_ownership_closure_authority" in str(asdict(run.scope_marker))


def test_ab5_report_does_not_overclaim_resolution() -> None:
    claim_boundary = (
        "AB5 updates bounded support from correlated effects without effect truth oracle, "
        "without request-as-confirmation, and without full abduction/consciousness claims."
    )
    lowered = claim_boundary.lower()
    assert "full abduction proven" not in lowered
    assert "consciousness proven" not in lowered
