from __future__ import annotations

from dataclasses import replace

from substrate.stream_kernel import (
    StreamInterruptionStatus,
    StreamKernelContext,
    StreamLinkDecision,
    build_stream_kernel,
    choose_stream_execution_mode,
    derive_stream_kernel_contract_view,
)
from tests.substrate.c01_testkit import build_c01_upstream


def test_c01_generates_typed_stream_state_and_gate() -> None:
    upstream = build_c01_upstream(
        case_id="c01-gen",
        energy=18.0,
        cognitive=92.0,
        safety=38.0,
    )
    result = build_stream_kernel(
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )

    assert result.state.stream_id
    assert result.state.sequence_index == 0
    assert result.state.carryover_items
    assert result.state.unresolved_anchors
    assert result.state.pending_operations
    assert result.state.link_decision in {
        StreamLinkDecision.STARTED_NEW_STREAM,
        StreamLinkDecision.FORCED_NEW_STREAM,
    }
    assert result.state.continuity_confidence >= 0.0
    assert result.telemetry.ledger_events
    assert result.no_transcript_replay_dependency is True
    assert result.no_memory_retrieval_dependency is True
    assert result.no_planner_hidden_flag_dependency is True


def test_c01_typed_only_boundary_rejects_raw_bypass() -> None:
    try:
        build_stream_kernel("raw", "raw", "raw", "raw")  # type: ignore[arg-type]
    except TypeError:
        return
    assert False, "build_stream_kernel must reject raw/non-typed bypass"


def test_contrast_true_continuation_vs_false_similarity_requires_anchor_bridge() -> None:
    prior_bundle = build_c01_upstream(
        case_id="c01-bridge-prior",
        energy=14.0,
        cognitive=94.0,
        safety=36.0,
    )
    prior = build_stream_kernel(
        prior_bundle.regulation,
        prior_bundle.affordances,
        prior_bundle.preferences,
        prior_bundle.viability,
    )
    true_bundle = build_c01_upstream(
        case_id="c01-bridge-true",
        energy=15.0,
        cognitive=92.0,
        safety=37.0,
    )
    continued = build_stream_kernel(
        true_bundle.regulation,
        true_bundle.affordances,
        true_bundle.preferences,
        true_bundle.viability,
        context=StreamKernelContext(prior_stream_state=prior.state),
    )
    false_prior_bundle = build_c01_upstream(
        case_id="c01-bridge-false-prior",
        energy=56.0,
        cognitive=42.0,
        safety=82.0,
    )
    false_prior = build_stream_kernel(
        false_prior_bundle.regulation,
        false_prior_bundle.affordances,
        false_prior_bundle.preferences,
        false_prior_bundle.viability,
    )
    false_continuation = build_stream_kernel(
        true_bundle.regulation,
        true_bundle.affordances,
        true_bundle.preferences,
        true_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=false_prior.state,
            require_strong_link=True,
        ),
    )

    assert continued.state.link_decision in {
        StreamLinkDecision.CONTINUED_EXISTING_STREAM,
        StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
        StreamLinkDecision.OPENED_BRANCH,
    }
    assert false_continuation.state.link_decision in {
        StreamLinkDecision.AMBIGUOUS_LINK,
        StreamLinkDecision.FORCED_NEW_STREAM,
        StreamLinkDecision.STARTED_NEW_STREAM,
    }
    assert continued.state.link_decision != false_continuation.state.link_decision


def test_interruption_and_resume_are_explicit_not_silent() -> None:
    first_bundle = build_c01_upstream(
        case_id="c01-interrupt-first",
        energy=16.0,
        cognitive=91.0,
        safety=39.0,
    )
    first = build_stream_kernel(
        first_bundle.regulation,
        first_bundle.affordances,
        first_bundle.preferences,
        first_bundle.viability,
    )
    interrupted = build_stream_kernel(
        first_bundle.regulation,
        first_bundle.affordances,
        first_bundle.preferences,
        first_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=first.state,
            interruption_signal=True,
        ),
    )
    resumed = build_stream_kernel(
        first_bundle.regulation,
        first_bundle.affordances,
        first_bundle.preferences,
        first_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=interrupted.state,
            resume_signal=True,
        ),
    )

    assert interrupted.state.interruption_status.value == "interrupted"
    assert any(
        item.carryover_class.value == "interruption_marker"
        for item in interrupted.state.carryover_items
    )
    assert resumed.state.interruption_status.value == "resumed"
    assert resumed.state.link_decision in {
        StreamLinkDecision.RESUMED_INTERRUPTED_STREAM,
        StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
    }


def test_release_and_stale_cleanup_after_closure() -> None:
    active_bundle = build_c01_upstream(
        case_id="c01-release-active",
        energy=15.0,
        cognitive=93.0,
        safety=37.0,
    )
    active = build_stream_kernel(
        active_bundle.regulation,
        active_bundle.affordances,
        active_bundle.preferences,
        active_bundle.viability,
    )
    resolved_bundle = build_c01_upstream(
        case_id="c01-release-resolved",
        energy=54.0,
        cognitive=46.0,
        safety=69.0,
    )
    stale_step = build_stream_kernel(
        resolved_bundle.regulation,
        resolved_bundle.affordances,
        resolved_bundle.preferences,
        resolved_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=active.state,
            stale_after_steps=1,
            release_after_steps=2,
        ),
    )
    released_step = build_stream_kernel(
        resolved_bundle.regulation,
        resolved_bundle.affordances,
        resolved_bundle.preferences,
        resolved_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=stale_step.state,
            stale_after_steps=1,
            release_after_steps=2,
        ),
    )

    assert stale_step.state.stale_markers
    assert released_step.state.link_decision in {
        StreamLinkDecision.FORCED_RELEASE,
        StreamLinkDecision.STARTED_NEW_STREAM,
        StreamLinkDecision.FORCED_NEW_STREAM,
        StreamLinkDecision.AMBIGUOUS_LINK,
    }
    if released_step.state.link_decision == StreamLinkDecision.FORCED_RELEASE:
        assert not released_step.state.carryover_items


def test_ambiguity_falls_back_to_honest_ambiguous_or_forced_new() -> None:
    prior_bundle = build_c01_upstream(
        case_id="c01-amb-prior",
        energy=12.0,
        cognitive=95.0,
        safety=35.0,
    )
    prior = build_stream_kernel(
        prior_bundle.regulation,
        prior_bundle.affordances,
        prior_bundle.preferences,
        prior_bundle.viability,
    )
    shifted_bundle = build_c01_upstream(
        case_id="c01-amb-shifted",
        energy=66.0,
        cognitive=30.0,
        safety=88.0,
    )
    shifted = build_stream_kernel(
        shifted_bundle.regulation,
        shifted_bundle.affordances,
        shifted_bundle.preferences,
        shifted_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=prior.state,
            require_strong_link=True,
        ),
    )

    assert shifted.state.link_decision in {
        StreamLinkDecision.AMBIGUOUS_LINK,
        StreamLinkDecision.FORCED_NEW_STREAM,
    }
    assert shifted.state.continuity_confidence <= 0.45


def test_metamorphic_minor_perturbation_keeps_continuity_topology() -> None:
    first_bundle = build_c01_upstream(
        case_id="c01-meta-first",
        energy=17.0,
        cognitive=90.0,
        safety=38.0,
    )
    first = build_stream_kernel(
        first_bundle.regulation,
        first_bundle.affordances,
        first_bundle.preferences,
        first_bundle.viability,
    )
    second_bundle = build_c01_upstream(
        case_id="c01-meta-second",
        energy=17.2,
        cognitive=89.6,
        safety=38.1,
    )
    a = build_stream_kernel(
        second_bundle.regulation,
        second_bundle.affordances,
        second_bundle.preferences,
        second_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=first.state,
            source_lineage=("meta-a", "meta-b"),
        ),
    )
    b = build_stream_kernel(
        second_bundle.regulation,
        second_bundle.affordances,
        second_bundle.preferences,
        second_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=first.state,
            source_lineage=("meta-b", "meta-a"),
            step_delta=2,
        ),
    )

    assert a.state.link_decision == b.state.link_decision
    assert a.state.stream_id == b.state.stream_id


def test_ablation_of_anchor_linking_degrades_continuation() -> None:
    first_bundle = build_c01_upstream(
        case_id="c01-abl-first",
        energy=15.0,
        cognitive=92.0,
        safety=37.0,
    )
    first = build_stream_kernel(
        first_bundle.regulation,
        first_bundle.affordances,
        first_bundle.preferences,
        first_bundle.viability,
    )
    second_bundle = build_c01_upstream(
        case_id="c01-abl-second",
        energy=15.4,
        cognitive=90.8,
        safety=37.2,
    )
    baseline = build_stream_kernel(
        second_bundle.regulation,
        second_bundle.affordances,
        second_bundle.preferences,
        second_bundle.viability,
        context=StreamKernelContext(prior_stream_state=first.state),
    )
    ablated = build_stream_kernel(
        second_bundle.regulation,
        second_bundle.affordances,
        second_bundle.preferences,
        second_bundle.viability,
        context=StreamKernelContext(
            prior_stream_state=first.state,
            disable_anchor_linking=True,
        ),
    )

    assert baseline.state.link_decision != ablated.state.link_decision
    assert baseline.state.stream_id != ablated.state.stream_id


def test_downstream_obedience_changes_mode_when_active_anchor_exists() -> None:
    active_bundle = build_c01_upstream(
        case_id="c01-consumer-active",
        energy=15.0,
        cognitive=94.0,
        safety=37.0,
    )
    active = build_stream_kernel(
        active_bundle.regulation,
        active_bundle.affordances,
        active_bundle.preferences,
        active_bundle.viability,
    )
    resolved_bundle = build_c01_upstream(
        case_id="c01-consumer-resolved",
        energy=58.0,
        cognitive=42.0,
        safety=70.0,
    )
    resolved = build_stream_kernel(
        resolved_bundle.regulation,
        resolved_bundle.affordances,
        resolved_bundle.preferences,
        resolved_bundle.viability,
        context=StreamKernelContext(prior_stream_state=active.state),
    )

    active_mode = choose_stream_execution_mode(active)
    resolved_mode = choose_stream_execution_mode(resolved)
    active_contract = derive_stream_kernel_contract_view(active)
    resolved_contract = derive_stream_kernel_contract_view(resolved)

    assert active_contract.active_carryover_present is True
    assert active_mode in {"continue_existing_stream", "continue_with_limits", "start_new_stream"}
    assert resolved_mode in {"start_new_stream", "resume_or_hold", "hold_or_repair", "idle"}
    assert active_mode != resolved_mode or (
        active_contract.link_decision != resolved_contract.link_decision
    )


def test_narrow_contour_role_preserves_relevant_anchor_but_not_irrelevant_recall() -> None:
    pressure = build_c01_upstream(
        case_id="c01-contour-pressure",
        energy=16.0,
        cognitive=94.0,
        safety=36.0,
        unresolved_preference=True,
    )
    step1 = build_stream_kernel(
        pressure.regulation,
        pressure.affordances,
        pressure.preferences,
        pressure.viability,
    )
    step2 = build_stream_kernel(
        pressure.regulation,
        pressure.affordances,
        pressure.preferences,
        pressure.viability,
        context=StreamKernelContext(prior_stream_state=step1.state),
    )
    settled = build_c01_upstream(
        case_id="c01-contour-settled",
        energy=57.0,
        cognitive=45.0,
        safety=72.0,
        unresolved_preference=False,
    )
    step3 = build_stream_kernel(
        settled.regulation,
        settled.affordances,
        settled.preferences,
        settled.viability,
        context=StreamKernelContext(
            prior_stream_state=step2.state,
            source_lineage=("memory-recall-only",),
            require_strong_link=True,
        ),
    )
    view = derive_stream_kernel_contract_view(step3)

    assert step2.state.carryover_items
    assert view.link_decision in {
        StreamLinkDecision.AMBIGUOUS_LINK,
        StreamLinkDecision.FORCED_NEW_STREAM,
        StreamLinkDecision.FORCED_RELEASE,
    }
    assert "memory-recall-only" in step3.state.source_lineage
    assert view.continuation_expected is False or view.active_carryover_present is False


def test_blocked_branch_conflict_cannot_return_strong_continue_mode() -> None:
    a = build_c01_upstream(
        case_id="c01-hard-branch-a",
        energy=16.0,
        cognitive=94.0,
        safety=36.0,
        unresolved_preference=True,
    )
    s1 = build_stream_kernel(a.regulation, a.affordances, a.preferences, a.viability)
    b = build_c01_upstream(
        case_id="c01-hard-branch-b",
        energy=94.0,
        cognitive=40.0,
        safety=36.0,
        unresolved_preference=True,
    )
    s2 = build_stream_kernel(
        b.regulation,
        b.affordances,
        b.preferences,
        b.viability,
        context=StreamKernelContext(prior_stream_state=s1.state),
    )
    c = build_c01_upstream(
        case_id="c01-hard-branch-c",
        energy=40.0,
        cognitive=40.0,
        safety=94.0,
        unresolved_preference=True,
    )
    s3 = build_stream_kernel(
        c.regulation,
        c.affordances,
        c.preferences,
        c.viability,
        context=StreamKernelContext(prior_stream_state=s2.state),
    )
    mode = choose_stream_execution_mode(s3)

    assert s3.state.branch_status.value == "branch_conflict"
    assert s3.downstream_gate.accepted is False
    assert s3.downstream_gate.usability_class.value == "blocked"
    assert mode != "continue_existing_stream"
    assert mode == "hold_or_repair"


def test_confidence_changes_consumer_mode_for_same_topology() -> None:
    base_bundle = build_c01_upstream(
        case_id="c01-hard-confidence",
        energy=16.0,
        cognitive=94.0,
        safety=36.0,
        unresolved_preference=True,
    )
    base = build_stream_kernel(
        base_bundle.regulation,
        base_bundle.affordances,
        base_bundle.preferences,
        base_bundle.viability,
    )
    continued = build_stream_kernel(
        base_bundle.regulation,
        base_bundle.affordances,
        base_bundle.preferences,
        base_bundle.viability,
        context=StreamKernelContext(prior_stream_state=base.state),
    )
    low_conf_state = replace(continued.state, continuity_confidence=0.52)
    high_conf_state = replace(continued.state, continuity_confidence=0.9)

    low_mode = choose_stream_execution_mode(low_conf_state)
    high_mode = choose_stream_execution_mode(high_conf_state)
    assert high_mode == "continue_existing_stream"
    assert low_mode in {"continue_with_limits", "resume_or_hold"}
    assert low_mode != high_mode


def test_weak_focus_only_seed_cannot_claim_strong_continuation() -> None:
    weak_a = build_c01_upstream(
        case_id="c01-hard-focus-a",
        energy=66.0,
        cognitive=50.0,
        safety=60.0,
        unresolved_preference=False,
    )
    s1 = build_stream_kernel(
        weak_a.regulation,
        weak_a.affordances,
        weak_a.preferences,
        weak_a.viability,
    )
    weak_b = build_c01_upstream(
        case_id="c01-hard-focus-b",
        energy=67.0,
        cognitive=49.0,
        safety=61.0,
        unresolved_preference=False,
    )
    s2 = build_stream_kernel(
        weak_b.regulation,
        weak_b.affordances,
        weak_b.preferences,
        weak_b.viability,
        context=StreamKernelContext(prior_stream_state=s1.state),
    )
    mode = choose_stream_execution_mode(s2)

    assert any(item.carryover_class.value == "held_focus_anchor" for item in s2.state.carryover_items)
    assert s2.state.link_decision != StreamLinkDecision.CONTINUED_EXISTING_STREAM
    assert s2.state.continuity_confidence <= 0.52
    assert mode != "continue_existing_stream"


def test_interrupted_without_resume_remains_degraded() -> None:
    upstream = build_c01_upstream(
        case_id="c01-hard-interrupt",
        energy=16.0,
        cognitive=94.0,
        safety=36.0,
        unresolved_preference=True,
    )
    s1 = build_stream_kernel(
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
    )
    interrupted = build_stream_kernel(
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamKernelContext(prior_stream_state=s1.state, interruption_signal=True),
    )
    without_resume = build_stream_kernel(
        upstream.regulation,
        upstream.affordances,
        upstream.preferences,
        upstream.viability,
        context=StreamKernelContext(prior_stream_state=interrupted.state),
    )
    mode = choose_stream_execution_mode(without_resume)

    assert interrupted.state.interruption_status == StreamInterruptionStatus.INTERRUPTED
    assert without_resume.state.interruption_status == StreamInterruptionStatus.INTERRUPTED
    assert without_resume.state.link_decision in {
        StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
        StreamLinkDecision.AMBIGUOUS_LINK,
    }
    assert mode in {"resume_or_hold", "start_new_stream", "hold_or_repair"}


def test_stale_topology_weakens_mode_vs_fresh_continuation() -> None:
    active = build_c01_upstream(
        case_id="c01-hard-stale-active",
        energy=16.0,
        cognitive=94.0,
        safety=36.0,
        unresolved_preference=True,
    )
    s1 = build_stream_kernel(active.regulation, active.affordances, active.preferences, active.viability)
    fresh = build_stream_kernel(
        active.regulation,
        active.affordances,
        active.preferences,
        active.viability,
        context=StreamKernelContext(prior_stream_state=s1.state),
    )
    settled = build_c01_upstream(
        case_id="c01-hard-stale-settled",
        energy=57.0,
        cognitive=46.0,
        safety=71.0,
        unresolved_preference=False,
    )
    stale = build_stream_kernel(
        settled.regulation,
        settled.affordances,
        settled.preferences,
        settled.viability,
        context=StreamKernelContext(
            prior_stream_state=s1.state,
            stale_after_steps=1,
            release_after_steps=10,
        ),
    )
    fresh_mode = choose_stream_execution_mode(fresh)
    stale_mode = choose_stream_execution_mode(stale)

    assert fresh_mode in {"continue_existing_stream", "continue_with_limits", "start_new_stream"}
    assert stale.state.stale_markers or stale.state.decay_state.value in {"stale", "released", "decaying"}
    assert stale_mode in {"resume_or_hold", "start_new_stream", "hold_or_repair"}
    assert stale_mode != "continue_existing_stream"


def test_mixed_survival_anchor_chain_does_not_force_strong_continue_forever() -> None:
    a = build_c01_upstream(
        case_id="c01-hard-lock-a",
        energy=16.0,
        cognitive=96.0,
        safety=36.0,
        unresolved_preference=False,
    )
    s1 = build_stream_kernel(a.regulation, a.affordances, a.preferences, a.viability)
    b = build_c01_upstream(
        case_id="c01-hard-lock-b",
        energy=96.0,
        cognitive=40.0,
        safety=36.0,
        unresolved_preference=False,
    )
    s2 = build_stream_kernel(
        b.regulation,
        b.affordances,
        b.preferences,
        b.viability,
        context=StreamKernelContext(
            prior_stream_state=s1.state,
            stale_after_steps=1,
            require_strong_link=True,
        ),
    )
    c = build_c01_upstream(
        case_id="c01-hard-lock-c",
        energy=40.0,
        cognitive=40.0,
        safety=96.0,
        unresolved_preference=False,
    )
    s3 = build_stream_kernel(
        c.regulation,
        c.affordances,
        c.preferences,
        c.viability,
        context=StreamKernelContext(
            prior_stream_state=s2.state,
            stale_after_steps=1,
            require_strong_link=True,
        ),
    )
    mode = choose_stream_execution_mode(s3)

    assert s3.state.link_decision in {
        StreamLinkDecision.AMBIGUOUS_LINK,
        StreamLinkDecision.LOW_CONFIDENCE_CONTINUATION,
        StreamLinkDecision.FORCED_NEW_STREAM,
        StreamLinkDecision.FORCED_RELEASE,
    } or s3.state.branch_status.value == "branch_conflict"
    assert mode != "continue_existing_stream"
