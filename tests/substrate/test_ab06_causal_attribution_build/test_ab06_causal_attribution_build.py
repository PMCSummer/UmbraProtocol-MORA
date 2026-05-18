from __future__ import annotations

from dataclasses import replace

from substrate.ab06_causal_attribution import (
    AB6CausalAttributionInput,
    AB6SupportStatus,
    build_ab6_causal_attribution,
)


def _input(**overrides: object) -> AB6CausalAttributionInput:
    base = AB6CausalAttributionInput(
        tick_ref="ab6:test:1",
        source_frontier_refs=("ab3:frontier:1",),
        source_update_refs=("ab5:update:1",),
        source_event_digest_refs=("ab1:event:1",),
        source_effect_refs=("effect:1",),
        source_request_refs=("ap01:request:1",),
        source_candidate_refs=("candidate:1",),
        source_observation_refs=("obs:1",),
        timing_refs=("tick:1",),
        external_event_refs=(),
        other_actor_refs=(),
        uncertainty_refs=("uncertain:1",),
        missing_evidence_refs=(),
        effect_correlated=True,
        blocked_action=False,
        delayed_marker=False,
        mixed_marker=False,
        unknown_marker=False,
        sensor_mismatch_marker=False,
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.ab6",
    )
    return replace(base, **overrides)


def _candidate(frame, kind: str):
    return next(item for item in frame.attribution_candidates if item.attribution_kind.value == kind)


def test_ab6_self_action_requires_ap01_and_correlation() -> None:
    run = build_ab6_causal_attribution(_input())
    assert run.frame is not None
    cand = _candidate(run.frame, "self_action")
    assert cand.support_status is AB6SupportStatus.SUPPORTED


def test_ab6_world_only_not_self() -> None:
    run = build_ab6_causal_attribution(
        _input(source_request_refs=(), effect_correlated=False, external_event_refs=("external:world",))
    )
    assert run.frame is not None
    self_cand = _candidate(run.frame, "self_action")
    assert self_cand.support_status is AB6SupportStatus.BLOCKED
    assert "world_process" in run.frame.supported_attribution_kinds


def test_ab6_other_actor_not_self() -> None:
    run = build_ab6_causal_attribution(
        _input(source_request_refs=(), effect_correlated=False, external_event_refs=("external:actor",), other_actor_refs=("other:1",))
    )
    assert run.frame is not None
    assert "other_actor" in run.frame.supported_attribution_kinds
    assert _candidate(run.frame, "self_action").support_status is AB6SupportStatus.BLOCKED


def test_ab6_unknown_preserved() -> None:
    run = build_ab6_causal_attribution(_input(source_request_refs=(), external_event_refs=(), other_actor_refs=(), unknown_marker=True))
    assert run.frame is not None
    assert run.frame.unknown_preserved is True
    assert "unknown_cause" in run.frame.supported_attribution_kinds


def test_ab6_mixed_cause_not_collapsed() -> None:
    run = build_ab6_causal_attribution(
        _input(external_event_refs=("external:world",), mixed_marker=True)
    )
    assert run.frame is not None
    assert run.frame.mixed_cause_preserved is True
    assert "mixed_cause" in run.frame.supported_attribution_kinds


def test_ab6_delayed_effect_not_immediate() -> None:
    run = build_ab6_causal_attribution(
        _input(delayed_marker=True, effect_correlated=False, timing_refs=("tick:1", "tick:2"))
    )
    assert run.frame is not None
    assert "delayed_self_effect" in run.frame.supported_attribution_kinds
    assert run.frame.fact_claimed is False


def test_ab6_sensor_mismatch_not_world_fact() -> None:
    run = build_ab6_causal_attribution(
        _input(source_request_refs=(), effect_correlated=False, sensor_mismatch_marker=True)
    )
    assert run.frame is not None
    assert "sensor_or_projection_error" in run.frame.supported_attribution_kinds
    assert run.frame.cause_confirmed is False


def test_ab6_blocked_action_not_success() -> None:
    run = build_ab6_causal_attribution(_input(blocked_action=True))
    assert run.frame is not None
    self_cand = _candidate(run.frame, "self_action")
    assert self_cand.support_status is AB6SupportStatus.BLOCKED


def test_ab6_hidden_eval_not_used() -> None:
    run = build_ab6_causal_attribution(_input(hidden_eval_excluded=False))
    assert run.frame is None
    assert "hidden_eval_exclusion_required" in run.reason_codes


def test_ab6_missing_ap01_ref_blocks_self_cause() -> None:
    run = build_ab6_causal_attribution(_input(source_request_refs=(), effect_correlated=True))
    assert run.frame is not None
    assert _candidate(run.frame, "self_action").support_status is AB6SupportStatus.BLOCKED


def test_ab6_request_alone_is_not_effect() -> None:
    run = build_ab6_causal_attribution(_input(source_effect_refs=(), source_event_digest_refs=()))
    assert run.frame is None


def test_ab6_uncorrelated_effect_not_self() -> None:
    run = build_ab6_causal_attribution(_input(effect_correlated=False))
    assert run.frame is not None
    assert _candidate(run.frame, "self_action").support_status is AB6SupportStatus.BLOCKED


def test_ab6_confidence_requires_evidence_refs() -> None:
    run = build_ab6_causal_attribution(_input())
    assert run.frame is not None
    for cand in run.frame.attribution_candidates:
        assert cand.evidence_refs


def test_ab6_does_not_update_hypotheses() -> None:
    run = build_ab6_causal_attribution(_input())
    assert run.frame is not None
    assert run.scope_marker.no_hypothesis_update_authority is True


def test_ab6_does_not_select_epistemic_action() -> None:
    run = build_ab6_causal_attribution(_input())
    assert run.scope_marker.no_epistemic_action_selection_authority is True


def test_ab6_does_not_emit_action_request() -> None:
    run = build_ab6_causal_attribution(_input())
    assert run.frame is not None
    assert run.frame.action_request_emitted is False
    assert run.frame.world_submission_emitted is False


def test_ab6_report_does_not_overclaim_self_model() -> None:
    claim_boundary = (
        "AB6 performs bounded attribution only; no full self-model, no final cause, no consciousness claim."
    )
    lowered = claim_boundary.lower()
    assert "full self-model proven" not in lowered
    assert "consciousness proven" not in lowered
