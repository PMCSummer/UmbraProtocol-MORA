from __future__ import annotations

from dataclasses import asdict, replace

from substrate.ab01_event_digest import (
    AB1CompressionQuality,
    AB1DigestStatus,
    AB1EventDigest,
    AB1EventDigestKind,
)
from substrate.ab02_hypothesis_seed import AB2HypothesisSeedInput, build_ab2_hypothesis_seeds
from substrate.ab03_hypothesis_frontier import AB3FrontierInput, build_ab3_hypothesis_frontier
from substrate.ab04_epistemic_candidate_basis import (
    AB4CandidateKind,
    AB4EIGLevel,
    AB4EpistemicBasisInput,
    build_ab4_epistemic_candidate_basis,
)


def _digest(**overrides: object) -> AB1EventDigest:
    base = AB1EventDigest(
        event_id="ab1:event:ab4",
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


def _frontier(*, ambiguous: bool = False):
    seed_result = build_ab2_hypothesis_seeds(
        AB2HypothesisSeedInput(
            tick_ref="ab2:ab4:test",
            event_digests=(_digest(),),
            source_refs=("src:ab2:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab4",
        )
    )
    assert seed_result.seed_set is not None
    frontier_result = build_ab3_hypothesis_frontier(
        AB3FrontierInput(
            tick_ref="ab3:ab4:test",
            seed_set=seed_result.seed_set,
            source_refs=("src:ab3:public",),
            observation_refs=("obs:1",),
            residue_refs=("residue:1",),
            effect_refs=("effect:1",),
            disconfirming_evidence_refs=(),
            ambiguous_evidence=ambiguous,
            require_competing_hypotheses=True,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source="tests.ab4",
        )
    )
    assert frontier_result.frontier is not None
    return frontier_result.frontier


def _input(frontier, **overrides: object) -> AB4EpistemicBasisInput:
    base = AB4EpistemicBasisInput(
        tick_ref="ab4:test:1",
        frontier=frontier,
        source_refs=("src:ab4:public",),
        observation_refs=("obs:1",),
        residue_refs=("residue:1",),
        effect_refs=("effect:1",),
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        allow_numeric_eig=False,
        source="tests.ab4",
    )
    return replace(base, **overrides)


def test_ab4_generates_inspect_basis_from_open_frontier() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier()))
    assert result.bases
    assert any(item.candidate_kind is AB4CandidateKind.INSPECT for item in result.bases)
    assert all(item.forbidden_execution for item in result.bases)


def test_ab4_generates_wait_or_reobserve_basis_from_ambiguous_frontier() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier(ambiguous=True)))
    kinds = {item.candidate_kind for item in result.bases}
    assert AB4CandidateKind.WAIT in kinds or AB4CandidateKind.REOBSERVE in kinds


def test_ab4_requires_frontier() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(None))
    assert result.bases == ()
    assert "frontier_required" in result.reason_codes


def test_ab4_requires_uncertainty_or_missing_evidence() -> None:
    frontier = _frontier()
    no_uncertainty = replace(frontier, unresolved_conflicts=(), missing_evidence=())
    result = build_ab4_epistemic_candidate_basis(_input(no_uncertainty))
    assert result.bases == ()


def test_ab4_requires_discriminating_tests() -> None:
    frontier = _frontier()
    no_tests = replace(frontier, discriminating_tests=())
    result = build_ab4_epistemic_candidate_basis(_input(no_tests))
    assert result.bases == ()


def test_ab4_rejects_hidden_truth_test_selection() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier(), hidden_eval_excluded=False))
    assert result.bases == ()
    assert "hidden_eval_exclusion_required" in result.reason_codes


def test_ab4_rejects_scenario_label_test_selection() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier(), scenario_label_excluded=False))
    assert result.bases == ()
    assert "scenario_label_exclusion_required" in result.reason_codes


def test_ab4_rejects_fact_claiming_frontier() -> None:
    frontier = replace(_frontier(), fact_claimed=True)
    result = build_ab4_epistemic_candidate_basis(_input(frontier))
    assert result.bases == ()
    assert "fact_claiming_frontier_forbidden" in result.reason_codes


def test_ab4_eig_requires_frontier_and_evidence_refs() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier()))
    assert result.bases
    for item in result.bases:
        assert item.expected_information_gain.scoring_refs
        assert item.frontier_ref


def test_ab4_fake_precision_eig_is_blocked() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier(), allow_numeric_eig=False))
    assert result.bases
    assert all(item.expected_information_gain.numeric is None for item in result.bases)
    assert all(item.expected_information_gain.level is not AB4EIGLevel.HIGH for item in result.bases)


def test_ab4_basis_has_public_basis_refs() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier()))
    assert result.bases
    assert all(item.public_basis_refs for item in result.bases)


def test_ab4_does_not_emit_action_candidate_or_request() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier()))
    assert result.bases
    for basis in result.bases:
        assert basis.action_request_emitted is False
        assert basis.ap01_request_ref is None
        assert basis.no_publication_authority is True
        assert basis.no_world_submission_authority is True
    assert all(item.action_request_emitted is False for item in result.bases)


def test_ab4_does_not_update_hypotheses() -> None:
    frontier = _frontier()
    before = asdict(frontier)
    _ = build_ab4_epistemic_candidate_basis(_input(frontier))
    after = asdict(frontier)
    assert before == after


def test_ab4_does_not_execute_world() -> None:
    result = build_ab4_epistemic_candidate_basis(_input(_frontier()))
    assert all(item.no_world_submission_authority is True for item in result.bases)
    serialized = str(asdict(result)).lower()
    assert "world_submission" not in serialized or "no_world_submission_authority': true" in serialized


def test_ab4_report_does_not_overclaim_active_inference() -> None:
    claim_boundary = (
        "AB4 emits bounded epistemic basis only; no full active inference, no cause confirmation, "
        "no consciousness claim."
    )
    lowered = claim_boundary.lower()
    assert "full active inference" in lowered
    assert "no full active inference" in lowered
