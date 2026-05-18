from __future__ import annotations

from dataclasses import dataclass, replace

from substrate.ab01_event_digest import (
    AB1CompressionQuality,
    AB1DigestStatus,
    AB1EventDigest,
    AB1EventDigestKind,
)
from substrate.ab05_hypothesis_update import (
    AB5HypothesisUpdateInput,
    AB5UpdateEnvelope,
    build_ab5_hypothesis_update,
)

from .ab3_hypothesis_frontier_probe import run_ab3_probe_case
from .ab4_epistemic_candidate_basis_probe import run_ab4_probe_case


@dataclass(frozen=True, slots=True)
class AB5ProbeCase:
    case_id: str
    description: str


def list_ab5_probe_cases() -> tuple[AB5ProbeCase, ...]:
    return (
        AB5ProbeCase("correlated_effect_support_increase", "correlated effect increases support for matching hypothesis"),
        AB5ProbeCase("disconfirming_effect_support_decrease", "disconfirming effect weakens/disconfirms hypothesis"),
        AB5ProbeCase("ambiguous_effect_no_closure", "ambiguous effect keeps update open and unresolved"),
        AB5ProbeCase("request_alone_no_confirmation", "request without effect cannot confirm"),
        AB5ProbeCase("uncorrelated_effect_weak_or_blocked_update", "uncorrelated effect cannot drive strong update"),
        AB5ProbeCase("hidden_eval_effect_rejected", "hidden/eval-only basis rejects update"),
        AB5ProbeCase("no_effect_no_update", "no effect evidence produces blocked/no update"),
    )


def run_ab5_probe_case(case_id: str) -> AB5UpdateEnvelope:
    if case_id == "correlated_effect_support_increase":
        return _run_with_frontier(
            case_id=case_id,
            frontier_case="blocked_movement_effect",
            ab4_case="open_frontier_inspect",
            correlated=True,
            disconfirm=False,
            ambiguous=False,
        )
    if case_id == "disconfirming_effect_support_decrease":
        return _run_with_frontier(
            case_id=case_id,
            frontier_case="effect_mismatch",
            ab4_case="ambiguous_frontier_wait",
            correlated=True,
            disconfirm=True,
            ambiguous=False,
        )
    if case_id == "ambiguous_effect_no_closure":
        return _run_with_frontier(
            case_id=case_id,
            frontier_case="ambiguous_evidence",
            ab4_case="ambiguous_frontier_wait",
            correlated=True,
            disconfirm=False,
            ambiguous=True,
        )
    if case_id == "request_alone_no_confirmation":
        frontier = run_ab3_probe_case("blocked_movement_effect").frontier
        assert frontier is not None
        return build_ab5_hypothesis_update(
            AB5HypothesisUpdateInput(
                tick_ref="ab5:probe:request_alone_no_confirmation",
                prior_frontier=frontier,
                source_refs=("probe:ab5:request_only",),
                source_effect_refs=(),
                source_event_digests=(),
                source_request_refs=("ap01:request:probe",),
                epistemic_basis_refs=("ab4:basis:probe",),
                source_observation_refs=("obs:probe:request_only",),
                supporting_hypothesis_refs=(frontier.hypotheses[0].hypothesis_id,),
                disconfirming_hypothesis_refs=(),
                ambiguous_evidence=False,
                effect_correlated=False,
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab5_probe.request_alone_no_confirmation",
            )
        )
    if case_id == "uncorrelated_effect_weak_or_blocked_update":
        return _run_with_frontier(
            case_id=case_id,
            frontier_case="blocked_movement_effect",
            ab4_case="open_frontier_inspect",
            correlated=False,
            disconfirm=False,
            ambiguous=False,
        )
    if case_id == "hidden_eval_effect_rejected":
        frontier = run_ab3_probe_case("blocked_movement_effect").frontier
        assert frontier is not None
        return build_ab5_hypothesis_update(
            AB5HypothesisUpdateInput(
                tick_ref="ab5:probe:hidden_eval_effect_rejected",
                prior_frontier=frontier,
                source_refs=("probe:ab5:hidden_eval",),
                source_effect_refs=("effect:hidden_eval",),
                source_event_digests=(_digest("ab5:probe:hidden_eval", AB1EventDigestKind.EFFECT_MISMATCH),),
                source_request_refs=("ap01:request:hidden_eval",),
                epistemic_basis_refs=("ab4:basis:hidden_eval",),
                source_observation_refs=("obs:hidden_eval",),
                supporting_hypothesis_refs=(frontier.hypotheses[0].hypothesis_id,),
                disconfirming_hypothesis_refs=(),
                ambiguous_evidence=False,
                effect_correlated=True,
                public_only=True,
                hidden_eval_excluded=False,
                scenario_label_excluded=True,
                source="ab5_probe.hidden_eval_effect_rejected",
            )
        )
    if case_id == "no_effect_no_update":
        frontier = run_ab3_probe_case("effect_mismatch").frontier
        assert frontier is not None
        return build_ab5_hypothesis_update(
            AB5HypothesisUpdateInput(
                tick_ref="ab5:probe:no_effect_no_update",
                prior_frontier=frontier,
                source_refs=("probe:ab5:no_effect",),
                source_effect_refs=(),
                source_event_digests=(),
                source_request_refs=(),
                epistemic_basis_refs=("ab4:basis:none",),
                source_observation_refs=("obs:no_effect",),
                supporting_hypothesis_refs=(frontier.hypotheses[0].hypothesis_id,),
                disconfirming_hypothesis_refs=(),
                ambiguous_evidence=False,
                effect_correlated=False,
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab5_probe.no_effect_no_update",
            )
        )
    raise ValueError(f"Unknown AB5 probe case: {case_id}")


def _run_with_frontier(
    *,
    case_id: str,
    frontier_case: str,
    ab4_case: str,
    correlated: bool,
    disconfirm: bool,
    ambiguous: bool,
) -> AB5UpdateEnvelope:
    frontier_result = run_ab3_probe_case(frontier_case)
    frontier = frontier_result.frontier
    assert frontier is not None
    ab4 = run_ab4_probe_case(ab4_case).result
    basis_refs = tuple(item.basis_id for item in ab4.bases)
    support_ref = frontier.hypotheses[0].hypothesis_id
    disconfirm_ref = frontier.hypotheses[1].hypothesis_id if len(frontier.hypotheses) > 1 else support_ref
    return build_ab5_hypothesis_update(
        AB5HypothesisUpdateInput(
            tick_ref=f"ab5:probe:{case_id}",
            prior_frontier=frontier,
            source_refs=(f"probe:ab3:{frontier_case}",),
            source_effect_refs=tuple(frontier.source_effect_refs) or ("effect:probe:default",),
            source_event_digests=(_digest(f"ab5:probe:{case_id}", AB1EventDigestKind.EFFECT_MISMATCH),),
            source_request_refs=("ap01:request:probe",),
            epistemic_basis_refs=basis_refs,
            source_observation_refs=tuple(frontier.source_effect_refs) or ("obs:probe:default",),
            supporting_hypothesis_refs=() if disconfirm else (support_ref,),
            disconfirming_hypothesis_refs=(disconfirm_ref,) if disconfirm else (),
            ambiguous_evidence=ambiguous,
            effect_correlated=correlated,
            public_only=True,
            hidden_eval_excluded=True,
            scenario_label_excluded=True,
            source=f"ab5_probe.{case_id}",
        )
    )


def _digest(event_id: str, event_kind: AB1EventDigestKind) -> AB1EventDigest:
    digest = AB1EventDigest(
        event_id=event_id,
        event_kind=event_kind,
        source_refs=("src:ab5:probe",),
        observation_refs=("obs:ab5:probe",),
        raw_window_refs=("raw:ab5:probe",),
        raw_window_missing_reason=None,
        effect_refs=("effect:ab5:probe",),
        residue_refs=("residue:ab5:probe",),
        expected_refs=("expected:ab5:probe",),
        observed_refs=("observed:ab5:probe",),
        magnitude=0.5,
        direction=None,
        confidence=0.7,
        uncertainty=0.3,
        compression_method="ab1_public_event_digest_v1",
        compression_quality=AB1CompressionQuality.LOSSY,
        digest_status=AB1DigestStatus.STRONG,
        lossiness=True,
        explicit_non_causal_closure=True,
        cause_claimed=False,
        hidden_eval_used=False,
        scenario_label_used=False,
        blocked_status=False,
        weak_status=False,
    )
    return replace(digest, event_id=event_id, event_kind=event_kind)
