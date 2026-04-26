from __future__ import annotations

from dataclasses import dataclass

from substrate.c06_surfacing_candidates import (
    C06CandidateClass,
    C06CandidateSetMetadata,
    C06ContinuityHorizon,
    C06ScopeMarker,
    C06StrengthGrade,
    C06SuppressionReport,
    C06SurfacedCandidate,
    C06SurfacedCandidateSet,
    C06SurfacingGateDecision,
    C06SurfacingResult,
    C06SurfacingStatus,
    C06Telemetry,
    C06UncertaintyState,
)
from substrate.p02_intervention_episode_layer_licensed_action_trace import (
    P02CompletionAndVerificationState,
    P02EpisodeBoundaryReport,
    P02EpisodeGateDecision,
    P02EpisodeMetadata,
    P02EpisodeStatus,
    P02ExecutionStatus,
    P02InterventionEpisodeRecord,
    P02InterventionEpisodeResult,
    P02OutcomeVerificationStatus,
    P02ResidueItem,
    P02ResidueKind,
    P02ScopeMarker,
    P02Telemetry,
)
from substrate.p03_long_horizon_credit_assignment_intervention_learning import (
    P03AttributionClass,
    P03ConfounderKind,
    P03ConfounderSignal,
    P03CreditAssignmentInput,
    P03CreditAssignmentResult,
    P03OutcomeObservation,
    P03OutcomeWindow,
    P03UpdateRecommendationKind,
    P03WindowEvidenceStatus,
    build_p03_long_horizon_credit_assignment_intervention_learning,
)


def p03_outcome_observation(
    *,
    observation_id: str,
    episode_ref: str,
    horizon_class: str,
    target_dimension: str,
    effect_polarity: str,
    magnitude: float,
    verified: bool,
    is_social_approval_signal: bool = False,
    conflicted: bool = False,
    occurred_order: int | None = None,
) -> P03OutcomeObservation:
    return P03OutcomeObservation(
        observation_id=observation_id,
        episode_ref=episode_ref,
        horizon_class=horizon_class,
        target_dimension=target_dimension,
        effect_polarity=effect_polarity,
        magnitude=magnitude,
        verified=verified,
        is_social_approval_signal=is_social_approval_signal,
        conflicted=conflicted,
        occurred_order=occurred_order,
        provenance=f"tests.p03.outcome:{observation_id}",
    )


def p03_confounder_signal(
    *,
    confounder_id: str,
    kind: P03ConfounderKind,
    strength: float,
    episode_ref: str | None = None,
    active: bool = True,
    reason: str = "",
) -> P03ConfounderSignal:
    return P03ConfounderSignal(
        confounder_id=confounder_id,
        episode_ref=episode_ref,
        kind=kind,
        strength=strength,
        active=active,
        reason=reason or f"tests.p03.confounder:{confounder_id}",
        provenance=f"tests.p03.confounder:{confounder_id}",
    )


def p03_outcome_window(
    *,
    window_id: str,
    episode_ref: str,
    status: P03WindowEvidenceStatus,
    start_order: int | None = None,
    end_order: int | None = None,
    evaluation_order: int | None = None,
    reason: str | None = None,
) -> P03OutcomeWindow:
    return P03OutcomeWindow(
        window_id=window_id,
        episode_ref=episode_ref,
        start_order=start_order,
        end_order=end_order,
        evaluation_order=evaluation_order,
        status=status,
        reason=reason or f"tests.p03.window:{window_id}",
        provenance=f"tests.p03.window:{window_id}",
    )


def p03_credit_assignment_input(
    *,
    input_id: str,
    outcome_observations: tuple[P03OutcomeObservation, ...] = (),
    confounder_signals: tuple[P03ConfounderSignal, ...] = (),
    outcome_windows: tuple[P03OutcomeWindow, ...] = (),
    continuity_resolution_refs: tuple[str, ...] = (),
    delayed_outcome_refs: tuple[str, ...] = (),
    confounder_bundle_ref: str | None = None,
) -> P03CreditAssignmentInput:
    return P03CreditAssignmentInput(
        input_id=input_id,
        outcome_observations=outcome_observations,
        confounder_signals=confounder_signals,
        outcome_windows=outcome_windows,
        continuity_resolution_refs=continuity_resolution_refs,
        delayed_outcome_refs=delayed_outcome_refs,
        confounder_bundle_ref=confounder_bundle_ref,
        provenance=f"tests.p03.input:{input_id}",
    )


def p02_episode_record(
    *,
    episode_id: str,
    status: P02EpisodeStatus = P02EpisodeStatus.COMPLETED_AS_LICENSED,
    execution_status: P02ExecutionStatus = P02ExecutionStatus.EXECUTED,
    outcome_verification_status: P02OutcomeVerificationStatus = (
        P02OutcomeVerificationStatus.VERIFIED
    ),
    completion_verified: bool = True,
    awaiting_verification: bool = False,
    verification_conflicted: bool = False,
    outcome_unknown: bool = False,
    boundary_ambiguous: bool = False,
    license_link_missing: bool = False,
    overrun_detected: bool = False,
    possible_overrun: bool = False,
    side_effects: tuple[str, ...] = (),
    residue_count: int = 0,
) -> P02InterventionEpisodeRecord:
    action_ref = f"{episode_id}:ev:1"
    residue = tuple(
        P02ResidueItem(
            residue_id=f"{episode_id}:residue:{index + 1}",
            residue_kind=P02ResidueKind.PENDING_VERIFICATION,
            ref_id=f"{episode_id}:residue-ref:{index + 1}",
            unresolved=True,
            reason="tests.p03.synthetic_residue",
            provenance="tests.p03.synthetic_residue",
        )
        for index in range(residue_count)
    )
    return P02InterventionEpisodeRecord(
        episode_id=episode_id,
        source_license_refs=(f"{episode_id}:license",),
        project_refs=(f"{episode_id}:project",),
        action_trace_refs=(action_ref,),
        excluded_event_refs=(),
        boundary_window_start=1,
        boundary_window_end=3,
        boundary_report=P02EpisodeBoundaryReport(
            boundary_window_start=1,
            boundary_window_end=3,
            action_trace_refs=(action_ref,),
            included_event_refs=(action_ref,),
            excluded_event_refs=(),
            boundary_ambiguous=boundary_ambiguous,
            reason_codes=("tests_p03_boundary",),
            reason="tests.p03.synthetic_boundary",
        ),
        status=status,
        completion_and_verification=P02CompletionAndVerificationState(
            execution_status=execution_status,
            outcome_verification_status=outcome_verification_status,
            status=status,
            completion_verified=completion_verified,
            awaiting_verification=awaiting_verification,
            verification_conflicted=verification_conflicted,
            outcome_unknown=outcome_unknown,
            reason="tests.p03.synthetic_completion",
        ),
        execution_status=execution_status,
        outcome_verification_status=outcome_verification_status,
        license_link_missing=license_link_missing,
        overrun_detected=overrun_detected,
        possible_overrun=possible_overrun,
        side_effects=side_effects,
        residue=residue,
        uncertainty_markers=(),
        rationale_codes=("tests_p03_episode",),
        provenance="tests.p03.synthetic_episode",
    )


def build_p02_result(
    *,
    episodes: tuple[P02InterventionEpisodeRecord, ...],
    source_lineage: tuple[str, ...] = ("tests.p03.synthetic_p02",),
) -> P02InterventionEpisodeResult:
    episode_count = len(episodes)
    completed_as_licensed_count = sum(
        int(item.status is P02EpisodeStatus.COMPLETED_AS_LICENSED) for item in episodes
    )
    partial_episode_count = sum(int(item.status is P02EpisodeStatus.PARTIAL) for item in episodes)
    blocked_episode_count = sum(int(item.status is P02EpisodeStatus.BLOCKED) for item in episodes)
    awaiting_verification_count = sum(
        int(item.completion_and_verification.awaiting_verification) for item in episodes
    )
    completion_verified_count = sum(
        int(item.completion_and_verification.completion_verified) for item in episodes
    )
    overrun_detected_count = sum(int(item.overrun_detected) for item in episodes)
    boundary_ambiguous_count = sum(int(item.boundary_report.boundary_ambiguous) for item in episodes)
    license_link_missing_count = sum(int(item.license_link_missing) for item in episodes)
    residue_count = sum(len(item.residue) for item in episodes)
    side_effect_count = sum(len(item.side_effects) for item in episodes)
    metadata = P02EpisodeMetadata(
        episode_count=episode_count,
        completed_as_licensed_count=completed_as_licensed_count,
        partial_episode_count=partial_episode_count,
        blocked_episode_count=blocked_episode_count,
        awaiting_verification_count=awaiting_verification_count,
        completion_verified_count=completion_verified_count,
        overrun_detected_count=overrun_detected_count,
        boundary_ambiguous_count=boundary_ambiguous_count,
        license_link_missing_count=license_link_missing_count,
        residue_count=residue_count,
        side_effect_count=side_effect_count,
        source_lineage=source_lineage,
    )
    gate = P02EpisodeGateDecision(
        episode_consumer_ready=episode_count > 0,
        boundary_consumer_ready=boundary_ambiguous_count == 0,
        verification_consumer_ready=awaiting_verification_count == 0,
        restrictions=(),
        reason="tests.p03.synthetic_p02_gate",
    )
    scope = P02ScopeMarker(
        scope="rt01_hosted_p02_first_slice",
        rt01_hosted_only=True,
        p02_first_slice_only=True,
        no_project_formation_authority=True,
        no_action_licensing_authority=True,
        no_external_success_claim_without_evidence=True,
        no_memory_retention_authority=True,
        no_map_wide_rollout_claim=True,
        reason="tests.p03.synthetic_p02_scope",
    )
    telemetry = P02Telemetry(
        episode_count=episode_count,
        completed_as_licensed_count=completed_as_licensed_count,
        partial_episode_count=partial_episode_count,
        blocked_episode_count=blocked_episode_count,
        awaiting_verification_count=awaiting_verification_count,
        overrun_detected_count=overrun_detected_count,
        boundary_ambiguous_count=boundary_ambiguous_count,
        residue_count=residue_count,
        side_effect_count=side_effect_count,
        downstream_consumer_ready=(
            gate.episode_consumer_ready
            and gate.boundary_consumer_ready
            and gate.verification_consumer_ready
        ),
    )
    return P02InterventionEpisodeResult(
        episodes=episodes,
        metadata=metadata,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason="tests.p03.synthetic_p02_result",
    )


def build_c06_result(
    *,
    commitment_carryover_count: int = 0,
) -> C06SurfacingResult:
    candidates = tuple(
        C06SurfacedCandidate(
            candidate_id=f"tests.p03.c06.candidate:{index + 1}",
            candidate_class=C06CandidateClass.COMMITMENT_CARRYOVER,
            source_refs=(f"tests.p03.c06.source:{index + 1}",),
            identity_hint=f"tests.p03.c06.identity:{index + 1}",
            identity_stabilizer=f"tests.p03.c06.stabilizer:{index + 1}",
            continuity_horizon=C06ContinuityHorizon.SHORT_CHAIN,
            strength_grade=C06StrengthGrade.MODERATE,
            uncertainty_state=C06UncertaintyState.PROVISIONAL,
            relation_to_current_project="tests_p03_project",
            relation_to_discourse="tests_p03_discourse",
            suggested_next_layer_consumers=("P02", "P03"),
            dismissal_risk="moderate_if_dropped",
            rationale_codes=("tests_p03_c06",),
            provenance="tests.p03.synthetic_c06",
        )
        for index in range(commitment_carryover_count)
    )
    metadata = C06CandidateSetMetadata(
        candidate_count=len(candidates),
        ambiguous_candidate_count=0,
        commitment_carryover_count=commitment_carryover_count,
        repair_obligation_count=0,
        protective_monitor_count=0,
        closure_candidate_count=0,
        duplicate_merge_count=0,
        false_merge_detected=False,
        no_continuity_candidates=len(candidates) == 0,
        published_frontier_requirement=True,
        published_frontier_requirement_satisfied=True,
        unresolved_ambiguity_preserved=True,
        confidence_residue_preserved=True,
        source_lineage=("tests.p03.synthetic_c06",),
    )
    suppression = C06SuppressionReport(
        examined_item_count=len(candidates),
        suppressed_item_count=0,
        suppressed_items=(),
        reason="tests.p03.synthetic_c06",
    )
    candidate_set = C06SurfacedCandidateSet(
        candidate_set_id="tests.p03.c06.candidate_set",
        status=(
            C06SurfacingStatus.SURFACED
            if candidates
            else C06SurfacingStatus.NO_CONTINUITY_CANDIDATES
        ),
        surfaced_candidates=candidates,
        suppression_report=suppression,
        metadata=metadata,
        reason="tests.p03.synthetic_c06",
    )
    gate = C06SurfacingGateDecision(
        candidate_set_consumer_ready=True,
        suppression_report_consumer_ready=True,
        identity_merge_consumer_ready=True,
        restrictions=(),
        reason="tests.p03.synthetic_c06_gate",
    )
    scope = C06ScopeMarker(
        scope="rt01_hosted_c06_first_slice",
        rt01_hosted_only=True,
        c06_first_slice_only=True,
        c06_1_workspace_handoff_contract=True,
        no_retention_write_layer=True,
        no_project_reformation_layer=True,
        no_map_wide_rollout_claim=True,
        reason="tests.p03.synthetic_c06_scope",
    )
    telemetry = C06Telemetry(
        candidate_set_id=candidate_set.candidate_set_id,
        tick_index=1,
        status=candidate_set.status,
        surfaced_candidate_count=len(candidates),
        suppressed_item_count=0,
        commitment_carryover_count=commitment_carryover_count,
        repair_obligation_count=0,
        protective_monitor_count=0,
        closure_candidate_count=0,
        ambiguous_candidate_count=0,
        duplicate_merge_count=0,
        false_merge_detected=False,
        published_frontier_requirement=True,
        unresolved_ambiguity_preserved=True,
        confidence_residue_preserved=True,
        downstream_consumer_ready=True,
    )
    return C06SurfacingResult(
        candidate_set=candidate_set,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason="tests.p03.synthetic_c06_result",
    )


@dataclass(frozen=True, slots=True)
class P03HarnessCase:
    case_id: str
    episodes: tuple[P02InterventionEpisodeRecord, ...]
    credit_assignment_input: P03CreditAssignmentInput | None
    c06_commitment_carryover_count: int = 0
    credit_assignment_enabled: bool = True


@dataclass(frozen=True, slots=True)
class P03HarnessRun:
    p03_result: P03CreditAssignmentResult
    p02_result: P02InterventionEpisodeResult
    c06_result: C06SurfacingResult
    credit_assignment_input: P03CreditAssignmentInput | None


def build_p03_harness_case(case: P03HarnessCase) -> P03HarnessRun:
    p02_result = build_p02_result(episodes=case.episodes)
    c06_result = build_c06_result(
        commitment_carryover_count=case.c06_commitment_carryover_count
    )
    p03_result = build_p03_long_horizon_credit_assignment_intervention_learning(
        tick_id=f"tests.p03:{case.case_id}",
        tick_index=1,
        p02_result=p02_result,
        c06_result=c06_result,
        credit_assignment_input=case.credit_assignment_input,
        source_lineage=("tests.p03", case.case_id),
        credit_assignment_enabled=case.credit_assignment_enabled,
    )
    return P03HarnessRun(
        p03_result=p03_result,
        p02_result=p02_result,
        c06_result=c06_result,
        credit_assignment_input=case.credit_assignment_input,
    )


def harness_cases() -> dict[str, P03HarnessCase]:
    ep_bad = p02_episode_record(episode_id="ep:immediate-positive-later-degraded")
    ep_good = p02_episode_record(episode_id="ep:modest-immediate-later-success")
    ep_same_weak = p02_episode_record(episode_id="ep:same-outcome-weak")
    ep_same_strong = p02_episode_record(episode_id="ep:same-outcome-strong")
    ep_early = p02_episode_record(episode_id="ep:early-enabling")
    ep_late = p02_episode_record(episode_id="ep:late-salient")
    ep_side = p02_episode_record(episode_id="ep:side-effect-retention")
    ep_verify_yes = p02_episode_record(episode_id="ep:verification-present")
    ep_verify_no = p02_episode_record(episode_id="ep:verification-removed")
    ep_within = p02_episode_record(episode_id="ep:horizon-within")
    ep_out = p02_episode_record(episode_id="ep:horizon-out")
    ep_no_update = p02_episode_record(episode_id="ep:no-update-open-window")
    ep_social = p02_episode_record(episode_id="ep:social-only")
    ep_safe = p02_episode_record(episode_id="ep:checkpoint-safe")
    ep_risky = p02_episode_record(episode_id="ep:checkpoint-risky")

    cases: dict[str, P03HarnessCase] = {
        "immediate_positive_later_degraded": P03HarnessCase(
            case_id="immediate_positive_later_degraded",
            episodes=(ep_bad,),
            credit_assignment_input=p03_credit_assignment_input(
                input_id="input:immediate-positive-later-degraded",
                outcome_observations=(
                    p03_outcome_observation(
                        observation_id="obs:bad:immediate-social",
                        episode_ref=ep_bad.episode_id,
                        horizon_class="immediate",
                        target_dimension="primary",
                        effect_polarity="improved",
                        magnitude=0.9,
                        verified=True,
                        is_social_approval_signal=True,
                        occurred_order=1,
                    ),
                    p03_outcome_observation(
                        observation_id="obs:bad:delayed-degraded",
                        episode_ref=ep_bad.episode_id,
                        horizon_class="delayed",
                        target_dimension="primary",
                        effect_polarity="degraded",
                        magnitude=0.8,
                        verified=True,
                        occurred_order=3,
                    ),
                ),
                outcome_windows=(
                    p03_outcome_window(
                        window_id="win:bad",
                        episode_ref=ep_bad.episode_id,
                        status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                    ),
                ),
                delayed_outcome_refs=("obs:bad:delayed-degraded",),
            ),
        ),
        "modest_immediate_later_durable_success": P03HarnessCase(
            case_id="modest_immediate_later_durable_success",
            episodes=(ep_good,),
            credit_assignment_input=p03_credit_assignment_input(
                input_id="input:modest-immediate-later-success",
                outcome_observations=(
                    p03_outcome_observation(
                        observation_id="obs:good:immediate-social",
                        episode_ref=ep_good.episode_id,
                        horizon_class="immediate",
                        target_dimension="primary",
                        effect_polarity="improved",
                        magnitude=0.2,
                        verified=True,
                        is_social_approval_signal=True,
                        occurred_order=1,
                    ),
                    p03_outcome_observation(
                        observation_id="obs:good:delayed-improved",
                        episode_ref=ep_good.episode_id,
                        horizon_class="delayed",
                        target_dimension="primary",
                        effect_polarity="improved",
                        magnitude=0.9,
                        verified=True,
                        occurred_order=4,
                    ),
                ),
                outcome_windows=(
                    p03_outcome_window(
                        window_id="win:good",
                        episode_ref=ep_good.episode_id,
                        status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                    ),
                ),
                delayed_outcome_refs=("obs:good:delayed-improved",),
            ),
        ),
        "same_outcome_weak_confounders": P03HarnessCase(
            case_id="same_outcome_weak_confounders",
            episodes=(ep_same_weak,),
            credit_assignment_input=p03_credit_assignment_input(
                input_id="input:same-outcome-weak-confounders",
                outcome_observations=(
                    p03_outcome_observation(
                        observation_id="obs:weak:delayed-improved",
                        episode_ref=ep_same_weak.episode_id,
                        horizon_class="delayed",
                        target_dimension="primary",
                        effect_polarity="improved",
                        magnitude=0.8,
                        verified=True,
                    ),
                ),
                outcome_windows=(
                    p03_outcome_window(
                        window_id="win:weak",
                        episode_ref=ep_same_weak.episode_id,
                        status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                    ),
                ),
            ),
        ),
        "same_outcome_strong_parallel_confounder": P03HarnessCase(
            case_id="same_outcome_strong_parallel_confounder",
            episodes=(ep_same_strong,),
            credit_assignment_input=p03_credit_assignment_input(
                input_id="input:same-outcome-strong-confounders",
                outcome_observations=(
                    p03_outcome_observation(
                        observation_id="obs:strong:delayed-improved",
                        episode_ref=ep_same_strong.episode_id,
                        horizon_class="delayed",
                        target_dimension="primary",
                        effect_polarity="improved",
                        magnitude=0.8,
                        verified=True,
                    ),
                ),
                confounder_signals=(
                    p03_confounder_signal(
                        confounder_id="conf:strong:parallel",
                        episode_ref=ep_same_strong.episode_id,
                        kind=P03ConfounderKind.PARALLEL_INTERVENTION,
                        strength=0.9,
                    ),
                ),
                outcome_windows=(
                    p03_outcome_window(
                        window_id="win:strong",
                        episode_ref=ep_same_strong.episode_id,
                        status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                    ),
                ),
                confounder_bundle_ref="bundle:strong",
            ),
        ),
        "recency_bias_adversarial": P03HarnessCase(
            case_id="recency_bias_adversarial",
            episodes=(ep_early, ep_late),
            credit_assignment_input=p03_credit_assignment_input(
                input_id="input:recency-bias-adversarial",
                outcome_observations=(
                    p03_outcome_observation(
                        observation_id="obs:early:delayed-improved",
                        episode_ref=ep_early.episode_id,
                        horizon_class="delayed",
                        target_dimension="primary",
                        effect_polarity="improved",
                        magnitude=0.85,
                        verified=True,
                        occurred_order=2,
                    ),
                    p03_outcome_observation(
                        observation_id="obs:late:immediate-social",
                        episode_ref=ep_late.episode_id,
                        horizon_class="immediate",
                        target_dimension="primary",
                        effect_polarity="improved",
                        magnitude=1.0,
                        verified=True,
                        is_social_approval_signal=True,
                        occurred_order=4,
                    ),
                ),
                outcome_windows=(
                    p03_outcome_window(
                        window_id="win:early",
                        episode_ref=ep_early.episode_id,
                        status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                    ),
                    p03_outcome_window(
                        window_id="win:late",
                        episode_ref=ep_late.episode_id,
                        status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                    ),
                ),
            ),
        ),
    }
    cases.update(
        {
            "side_effect_retention": P03HarnessCase(
                case_id="side_effect_retention",
                episodes=(ep_side,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:side-effect-retention",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:side:primary-improved",
                            episode_ref=ep_side.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.6,
                            verified=True,
                        ),
                        p03_outcome_observation(
                            observation_id="obs:side:protective-degraded",
                            episode_ref=ep_side.episode_id,
                            horizon_class="delayed",
                            target_dimension="protective",
                            effect_polarity="degraded",
                            magnitude=0.9,
                            verified=True,
                        ),
                    ),
                    outcome_windows=(
                        p03_outcome_window(
                            window_id="win:side",
                            episode_ref=ep_side.episode_id,
                            status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                        ),
                    ),
                ),
            ),
            "verification_present": P03HarnessCase(
                case_id="verification_present",
                episodes=(ep_verify_yes,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:verification-present",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:verify:yes",
                            episode_ref=ep_verify_yes.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.7,
                            verified=True,
                        ),
                    ),
                    outcome_windows=(
                        p03_outcome_window(
                            window_id="win:verify:yes",
                            episode_ref=ep_verify_yes.episode_id,
                            status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                        ),
                    ),
                ),
            ),
            "verification_removed": P03HarnessCase(
                case_id="verification_removed",
                episodes=(ep_verify_no,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:verification-removed",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:verify:no",
                            episode_ref=ep_verify_no.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.7,
                            verified=False,
                        ),
                    ),
                ),
            ),
            "horizon_within_window": P03HarnessCase(
                case_id="horizon_within_window",
                episodes=(ep_within,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:horizon-within",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:horizon:within",
                            episode_ref=ep_within.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.7,
                            verified=True,
                        ),
                    ),
                    outcome_windows=(
                        p03_outcome_window(
                            window_id="win:horizon:within",
                            episode_ref=ep_within.episode_id,
                            status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                        ),
                    ),
                ),
            ),
            "horizon_out_of_window": P03HarnessCase(
                case_id="horizon_out_of_window",
                episodes=(ep_out,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:horizon-out",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:horizon:out",
                            episode_ref=ep_out.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.7,
                            verified=True,
                        ),
                    ),
                    outcome_windows=(
                        p03_outcome_window(
                            window_id="win:horizon:out",
                            episode_ref=ep_out.episode_id,
                            status=P03WindowEvidenceStatus.OUT_OF_WINDOW,
                        ),
                    ),
                ),
            ),
            "no_update_open_window": P03HarnessCase(
                case_id="no_update_open_window",
                episodes=(ep_no_update,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:no-update-open-window",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:no-update:open-window",
                            episode_ref=ep_no_update.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.8,
                            verified=True,
                        ),
                    ),
                    outcome_windows=(
                        p03_outcome_window(
                            window_id="win:no-update:open-window",
                            episode_ref=ep_no_update.episode_id,
                            status=P03WindowEvidenceStatus.WINDOW_STILL_OPEN,
                        ),
                    ),
                ),
            ),
            "social_approval_only": P03HarnessCase(
                case_id="social_approval_only",
                episodes=(ep_social,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:social-only",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:social:only",
                            episode_ref=ep_social.episode_id,
                            horizon_class="immediate",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=1.0,
                            verified=True,
                            is_social_approval_signal=True,
                        ),
                    ),
                ),
            ),
            "checkpoint_envelope_safe": P03HarnessCase(
                case_id="checkpoint_envelope_safe",
                episodes=(ep_safe,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:checkpoint-safe",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:checkpoint:safe",
                            episode_ref=ep_safe.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.8,
                            verified=True,
                        ),
                    ),
                    outcome_windows=(
                        p03_outcome_window(
                            window_id="win:checkpoint:safe",
                            episode_ref=ep_safe.episode_id,
                            status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                        ),
                    ),
                ),
            ),
            "checkpoint_envelope_risky_confounded": P03HarnessCase(
                case_id="checkpoint_envelope_risky_confounded",
                episodes=(ep_risky,),
                credit_assignment_input=p03_credit_assignment_input(
                    input_id="input:checkpoint-risky",
                    outcome_observations=(
                        p03_outcome_observation(
                            observation_id="obs:checkpoint:risky",
                            episode_ref=ep_risky.episode_id,
                            horizon_class="delayed",
                            target_dimension="primary",
                            effect_polarity="improved",
                            magnitude=0.8,
                            verified=True,
                        ),
                    ),
                    confounder_signals=(
                        p03_confounder_signal(
                            confounder_id="conf:checkpoint:risky",
                            episode_ref=ep_risky.episode_id,
                            kind=P03ConfounderKind.PARALLEL_INTERVENTION,
                            strength=0.95,
                        ),
                    ),
                    outcome_windows=(
                        p03_outcome_window(
                            window_id="win:checkpoint:risky",
                            episode_ref=ep_risky.episode_id,
                            status=P03WindowEvidenceStatus.WITHIN_WINDOW,
                        ),
                    ),
                    confounder_bundle_ref="bundle:checkpoint:risky",
                ),
            ),
        }
    )
    return cases


def first_credit(run: P03HarnessRun):
    return run.p03_result.record_set.credit_records[0]


def first_no_update(run: P03HarnessRun):
    return run.p03_result.record_set.no_update_records[0]


def assert_recommendation(
    run: P03HarnessRun,
    *,
    expected: P03UpdateRecommendationKind,
) -> None:
    credit_records = run.p03_result.record_set.credit_records
    if credit_records:
        assert credit_records[0].recommendation.recommendation is expected
        return
    assert run.p03_result.record_set.no_update_records
    assert run.p03_result.record_set.no_update_records[0].recommendation.recommendation is expected


def assert_credit_class(
    run: P03HarnessRun,
    *,
    expected: P03AttributionClass,
) -> None:
    assert run.p03_result.record_set.credit_records
    assert run.p03_result.record_set.credit_records[0].attribution_class is expected
