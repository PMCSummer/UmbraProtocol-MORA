from __future__ import annotations

from substrate.c06_surfacing_candidates import C06SurfacingResult
from substrate.p02_intervention_episode_layer_licensed_action_trace import (
    P02InterventionEpisodeRecord,
    P02InterventionEpisodeResult,
)
from substrate.p03_long_horizon_credit_assignment_intervention_learning.models import (
    P03AttributionClass,
    P03AttributionConflict,
    P03ConfounderKind,
    P03ConfounderSignal,
    P03ContributionMode,
    P03CreditAssignmentGateDecision,
    P03CreditAssignmentInput,
    P03CreditAssignmentRecordSet,
    P03CreditAssignmentResult,
    P03CreditRecord,
    P03LearningRecommendation,
    P03NoUpdateRecord,
    P03OutcomeObservation,
    P03OutcomeWindow,
    P03ScopeMarker,
    P03Telemetry,
    P03UpdateRecommendationKind,
    P03WindowEvidenceStatus,
)

_SIDE_EFFECT_DIMENSIONS = {"protective", "relational", "project_cost"}


def build_p03_long_horizon_credit_assignment_intervention_learning(
    *,
    tick_id: str,
    tick_index: int,
    p02_result: P02InterventionEpisodeResult,
    c06_result: C06SurfacingResult,
    credit_assignment_input: P03CreditAssignmentInput | None,
    source_lineage: tuple[str, ...],
    credit_assignment_enabled: bool = True,
) -> P03CreditAssignmentResult:
    if not credit_assignment_enabled:
        return _build_minimal_result(
            reason="p03 credit assignment disabled in ablation context",
            restrictions=("p03_disabled", "credit_assignment_not_evaluated"),
        )
    if not isinstance(p02_result, P02InterventionEpisodeResult):
        raise TypeError("p03 requires P02InterventionEpisodeResult")
    if not isinstance(c06_result, C06SurfacingResult):
        raise TypeError("p03 requires C06SurfacingResult")

    explicit_input = credit_assignment_input if isinstance(credit_assignment_input, P03CreditAssignmentInput) else None
    if explicit_input is None:
        return _build_minimal_result(
            reason=(
                "p03 frontier slice requires explicit credit-assignment input; "
                "raw impression reconstruction is intentionally forbidden"
            ),
            restrictions=("insufficient_p03_basis", "no_raw_outcome_impression_learning"),
        )

    episodes = p02_result.episodes
    if not episodes:
        return _build_minimal_result(
            reason="p03 received no p02 episode records and produced no attribution",
            restrictions=("no_p02_episode_records", "credit_assignment_not_evaluated"),
        )

    all_outcomes = explicit_input.outcome_observations
    all_windows = explicit_input.outcome_windows
    all_confounders = explicit_input.confounder_signals

    credit_records: list[P03CreditRecord] = []
    no_update_records: list[P03NoUpdateRecord] = []
    conflicts: list[P03AttributionConflict] = []

    for index, episode in enumerate(episodes, start=1):
        episode_outcomes = tuple(
            item for item in all_outcomes if item.episode_ref == episode.episode_id
        )
        episode_windows = tuple(
            item for item in all_windows if item.episode_ref == episode.episode_id
        )
        episode_confounders = _effective_confounders(
            episode=episode,
            confounders=all_confounders,
            continuity_resolution_refs=explicit_input.continuity_resolution_refs,
            c06_result=c06_result,
        )
        evaluated = _evaluate_episode(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=index,
            episode=episode,
            outcomes=episode_outcomes,
            windows=episode_windows,
            confounders=episode_confounders,
        )
        if evaluated.credit_record is not None:
            credit_records.append(evaluated.credit_record)
        if evaluated.no_update_record is not None:
            no_update_records.append(evaluated.no_update_record)
        if evaluated.conflict is not None:
            conflicts.append(evaluated.conflict)

    record_set = P03CreditAssignmentRecordSet(
        assignment_id=f"p03:{tick_id}:credit_assignment",
        evaluated_episode_refs=tuple(item.episode_id for item in episodes),
        credit_records=tuple(credit_records),
        no_update_records=tuple(no_update_records),
        conflicts=tuple(conflicts),
        continuity_resolution_refs=explicit_input.continuity_resolution_refs,
        confounder_bundle_ref=explicit_input.confounder_bundle_ref,
        reason=(
            "p03 consumed typed p02 episodes, delayed outcomes, continuity traces, and confounder bundle "
            "to emit explicit attribution records"
        ),
    )
    gate = _build_gate(record_set=record_set)
    telemetry = _build_telemetry(record_set=record_set, gate=gate)
    scope_marker = P03ScopeMarker(
        scope="rt01_hosted_p03_frontier_slice",
        rt01_hosted_only=True,
        p03_frontier_slice_only=True,
        no_policy_mutation_authority=True,
        no_scalar_reward_shortcut=True,
        no_raw_approval_shortcut=True,
        no_full_causal_discovery_claim=True,
        no_map_wide_rollout_claim=True,
        reason=(
            "p03 emits bounded attribution/recommendation artifacts only; "
            "it does not mutate policy and does not claim full causal truth"
        ),
    )
    return P03CreditAssignmentResult(
        record_set=record_set,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=(
            "p03 produced explicit attribution objects and first-class no-update/confounded states "
            "for downstream learning consumers"
        ),
    )


class _EpisodeEvaluation:
    __slots__ = ("credit_record", "no_update_record", "conflict")

    def __init__(
        self,
        *,
        credit_record: P03CreditRecord | None,
        no_update_record: P03NoUpdateRecord | None,
        conflict: P03AttributionConflict | None,
    ) -> None:
        self.credit_record = credit_record
        self.no_update_record = no_update_record
        self.conflict = conflict


def _evaluate_episode(
    *,
    tick_id: str,
    tick_index: int,
    ordinal: int,
    episode: P02InterventionEpisodeRecord,
    outcomes: tuple[P03OutcomeObservation, ...],
    windows: tuple[P03OutcomeWindow, ...],
    confounders: tuple[P03ConfounderSignal, ...],
) -> _EpisodeEvaluation:
    window_status = _resolve_window_status(
        episode=episode,
        outcomes=outcomes,
        windows=windows,
    )
    strong_confounding = _strong_confounding(confounders)
    moderate_confounding = _moderate_confounding(confounders)

    social_only = bool(outcomes) and all(item.is_social_approval_signal for item in outcomes)
    delayed = tuple(item for item in outcomes if item.horizon_class != "immediate")
    delayed_non_social = tuple(item for item in delayed if not item.is_social_approval_signal)

    positive_primary = _sum_outcomes(
        delayed_non_social,
        target_dimension="primary",
        effect_polarity="improved",
    )
    negative_primary = _sum_outcomes(
        delayed_non_social,
        target_dimension="primary",
        effect_polarity="degraded",
    )
    negative_side_effect = _sum_side_effect_outcomes(
        delayed_non_social,
        effect_polarity="degraded",
    )

    conflict = _build_conflict(
        tick_id=tick_id,
        tick_index=tick_index,
        ordinal=ordinal,
        episode=episode,
        outcomes=delayed_non_social,
        confounders=confounders,
    )
    conflict_present = conflict is not None or window_status is P03WindowEvidenceStatus.EVIDENCE_CONFLICTED

    if not outcomes:
        no_update = _make_no_update(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            window_status=window_status,
            reason_code="sparse_evidence",
            evidence_refs=(),
            confounders=confounders,
            reason="no delayed outcomes were provided for this episode",
        )
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            contribution_mode=P03ContributionMode.HYPOTHESIZED,
            window_status=window_status,
            outcomes=(),
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=False,
            recommendation=P03UpdateRecommendationKind.DO_NOT_UPDATE,
            guarded=False,
            confidence_band="weak",
            rationale_codes=("sparse_evidence",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=no_update, conflict=None)

    if social_only and not delayed_non_social:
        no_update = _make_no_update(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            window_status=window_status,
            reason_code="approval_signal_not_credit_basis",
            evidence_refs=tuple(item.observation_id for item in outcomes),
            confounders=confounders,
            reason="social approval/fluency signal was explicitly excluded as a success proxy",
        )
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            contribution_mode=P03ContributionMode.HYPOTHESIZED,
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=False,
            recommendation=P03UpdateRecommendationKind.DO_NOT_UPDATE,
            guarded=False,
            confidence_band="weak",
            rationale_codes=(
                "no_raw_approval_shortcut",
                "approval_signal_not_credit_basis",
            ),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=no_update, conflict=None)

    if window_status in {
        P03WindowEvidenceStatus.WINDOW_STILL_OPEN,
        P03WindowEvidenceStatus.OUTCOME_UNVERIFIED,
    }:
        no_update = _make_no_update(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            window_status=window_status,
            reason_code="window_or_verification_open",
            evidence_refs=tuple(item.observation_id for item in outcomes),
            confounders=confounders,
            reason="outcome window/verification remains open so p03 kept no-update",
        )
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            contribution_mode=P03ContributionMode.HYPOTHESIZED,
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=False,
            recommendation=P03UpdateRecommendationKind.DO_NOT_UPDATE,
            guarded=False,
            confidence_band="weak",
            rationale_codes=("window_or_verification_open",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=no_update, conflict=None)

    if window_status is P03WindowEvidenceStatus.OUT_OF_WINDOW:
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.NULL,
            contribution_mode=P03ContributionMode.NEUTRAL_ASSOCIATION,
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=False,
            recommendation=P03UpdateRecommendationKind.KEEP_UNCHANGED,
            guarded=False,
            confidence_band="weak",
            rationale_codes=("out_of_window",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=None, conflict=None)

    if conflict_present:
        no_update = _make_no_update(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            window_status=P03WindowEvidenceStatus.EVIDENCE_CONFLICTED,
            reason_code="evidence_conflicted",
            evidence_refs=tuple(item.observation_id for item in outcomes),
            confounders=confounders,
            reason="conflicting delayed evidence blocked confident update recommendation",
        )
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.UNRESOLVED,
            contribution_mode=P03ContributionMode.HYPOTHESIZED,
            window_status=P03WindowEvidenceStatus.EVIDENCE_CONFLICTED,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=() if conflict is None else (conflict,),
            side_effect_dominant=False,
            recommendation=P03UpdateRecommendationKind.DO_NOT_UPDATE,
            guarded=False,
            confidence_band="weak",
            rationale_codes=("evidence_conflicted",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=no_update, conflict=conflict)

    if strong_confounding:
        no_update = _make_no_update(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.CONFOUNDED_ASSOCIATION,
            window_status=window_status,
            reason_code="heavy_confounding",
            evidence_refs=tuple(item.observation_id for item in outcomes),
            confounders=confounders,
            reason="strong confounders prevented bounded attribution confidence",
        )
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.CONFOUNDED_ASSOCIATION,
            contribution_mode=P03ContributionMode.HYPOTHESIZED,
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=False,
            recommendation=P03UpdateRecommendationKind.DO_NOT_UPDATE,
            guarded=False,
            confidence_band="weak",
            rationale_codes=("heavy_confounding",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=no_update, conflict=None)

    side_effect_dominant = False
    if positive_primary > 0.0 and negative_primary <= 0.0 and negative_side_effect <= 0.0:
        recommendation = (
            P03UpdateRecommendationKind.ADD_VERIFICATION_REQUIREMENT
            if moderate_confounding
            else P03UpdateRecommendationKind.STRENGTHEN_GUARDED
        )
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.POSITIVE,
            contribution_mode=P03ContributionMode.DIRECT,
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=False,
            recommendation=recommendation,
            guarded=True,
            confidence_band="guarded",
            rationale_codes=("positive_primary_outcome",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=None, conflict=None)

    if negative_primary > 0.0 and positive_primary <= 0.0:
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.NEGATIVE,
            contribution_mode=P03ContributionMode.BLOCKING,
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=False,
            recommendation=P03UpdateRecommendationKind.WEAKEN_GUARDED,
            guarded=True,
            confidence_band="guarded",
            rationale_codes=("negative_primary_outcome",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=None, conflict=None)

    if positive_primary > 0.0 and (negative_primary > 0.0 or negative_side_effect > 0.0):
        side_effect_dominant = negative_side_effect >= positive_primary
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.MIXED,
            contribution_mode=(
                P03ContributionMode.ADVERSE_SIDE_EFFECT
                if side_effect_dominant
                else P03ContributionMode.ENABLING
            ),
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=side_effect_dominant,
            recommendation=(
                P03UpdateRecommendationKind.WEAKEN_GUARDED
                if side_effect_dominant
                else P03UpdateRecommendationKind.ADD_PRECONDITION
            ),
            guarded=True,
            confidence_band="guarded",
            rationale_codes=("mixed_primary_and_side_effect",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=None, conflict=None)

    if positive_primary <= 0.0 and negative_primary <= 0.0 and negative_side_effect > 0.0:
        credit = _make_credit(
            tick_id=tick_id,
            tick_index=tick_index,
            ordinal=ordinal,
            episode=episode,
            attribution_class=P03AttributionClass.NEGATIVE,
            contribution_mode=P03ContributionMode.ADVERSE_SIDE_EFFECT,
            window_status=window_status,
            outcomes=outcomes,
            confounders=confounders,
            conflicts=(),
            side_effect_dominant=True,
            recommendation=P03UpdateRecommendationKind.WEAKEN_GUARDED,
            guarded=True,
            confidence_band="guarded",
            rationale_codes=("negative_side_effect_without_primary_gain",),
        )
        return _EpisodeEvaluation(credit_record=credit, no_update_record=None, conflict=None)

    credit = _make_credit(
        tick_id=tick_id,
        tick_index=tick_index,
        ordinal=ordinal,
        episode=episode,
        attribution_class=P03AttributionClass.NULL,
        contribution_mode=P03ContributionMode.NEUTRAL_ASSOCIATION,
        window_status=window_status,
        outcomes=outcomes,
        confounders=confounders,
        conflicts=(),
        side_effect_dominant=side_effect_dominant,
        recommendation=P03UpdateRecommendationKind.KEEP_UNCHANGED,
        guarded=False,
        confidence_band="weak",
        rationale_codes=("neutral_outcome_association",),
    )
    return _EpisodeEvaluation(credit_record=credit, no_update_record=None, conflict=None)


def _effective_confounders(
    *,
    episode: P02InterventionEpisodeRecord,
    confounders: tuple[P03ConfounderSignal, ...],
    continuity_resolution_refs: tuple[str, ...],
    c06_result: C06SurfacingResult,
) -> tuple[P03ConfounderSignal, ...]:
    selected = [
        item
        for item in confounders
        if item.active and (item.episode_ref in {None, episode.episode_id})
    ]
    if (
        episode.residue
        and c06_result.candidate_set.metadata.commitment_carryover_count > 0
        and not continuity_resolution_refs
    ):
        selected.append(
            P03ConfounderSignal(
                confounder_id=f"{episode.episode_id}:synthetic:unresolved_residue",
                episode_ref=episode.episode_id,
                kind=P03ConfounderKind.UNRESOLVED_RESIDUE,
                strength=0.7,
                active=True,
                reason=(
                    "c06 commitment carryover remains open while p02 residue is unresolved "
                    "and no continuity resolution trace was supplied"
                ),
                provenance="p03.synthetic_confounder",
            )
        )
    return tuple(selected)


def _resolve_window_status(
    *,
    episode: P02InterventionEpisodeRecord,
    outcomes: tuple[P03OutcomeObservation, ...],
    windows: tuple[P03OutcomeWindow, ...],
) -> P03WindowEvidenceStatus:
    if windows:
        by_priority = (
            P03WindowEvidenceStatus.EVIDENCE_CONFLICTED,
            P03WindowEvidenceStatus.WINDOW_STILL_OPEN,
            P03WindowEvidenceStatus.OUTCOME_UNVERIFIED,
            P03WindowEvidenceStatus.OUT_OF_WINDOW,
            P03WindowEvidenceStatus.WITHIN_WINDOW,
        )
        statuses = {item.status for item in windows}
        for status in by_priority:
            if status in statuses:
                return status

    delayed = tuple(item for item in outcomes if item.horizon_class != "immediate")
    if delayed and any(not item.verified for item in delayed):
        return P03WindowEvidenceStatus.OUTCOME_UNVERIFIED
    if delayed:
        return P03WindowEvidenceStatus.WITHIN_WINDOW
    if episode.completion_and_verification.awaiting_verification or episode.residue:
        return P03WindowEvidenceStatus.WINDOW_STILL_OPEN
    return P03WindowEvidenceStatus.OUTCOME_UNVERIFIED


def _sum_outcomes(
    outcomes: tuple[P03OutcomeObservation, ...],
    *,
    target_dimension: str,
    effect_polarity: str,
) -> float:
    return float(
        sum(
            item.magnitude
            for item in outcomes
            if item.verified
            and item.target_dimension == target_dimension
            and item.effect_polarity == effect_polarity
        )
    )


def _sum_side_effect_outcomes(
    outcomes: tuple[P03OutcomeObservation, ...],
    *,
    effect_polarity: str,
) -> float:
    return float(
        sum(
            item.magnitude
            for item in outcomes
            if item.verified
            and item.target_dimension in _SIDE_EFFECT_DIMENSIONS
            and item.effect_polarity == effect_polarity
        )
    )


def _strong_confounding(confounders: tuple[P03ConfounderSignal, ...]) -> bool:
    if not confounders:
        return False
    if any(
        item.kind in {P03ConfounderKind.PARALLEL_INTERVENTION, P03ConfounderKind.EXTERNAL_CHANGE}
        and item.strength >= 0.6
        for item in confounders
    ):
        return True
    return sum(item.strength for item in confounders if item.active) >= 1.0


def _moderate_confounding(confounders: tuple[P03ConfounderSignal, ...]) -> bool:
    return sum(item.strength for item in confounders if item.active) >= 0.4


def _build_conflict(
    *,
    tick_id: str,
    tick_index: int,
    ordinal: int,
    episode: P02InterventionEpisodeRecord,
    outcomes: tuple[P03OutcomeObservation, ...],
    confounders: tuple[P03ConfounderSignal, ...],
) -> P03AttributionConflict | None:
    conflicted_flag = any(item.conflicted for item in outcomes)
    verified_outcomes = tuple(item for item in outcomes if item.verified)
    by_dimension: dict[str, set[str]] = {}
    for item in verified_outcomes:
        by_dimension.setdefault(item.target_dimension, set()).add(item.effect_polarity)
    conflicted_dimensions = {
        dimension
        for dimension, polarities in by_dimension.items()
        if {"improved", "degraded"}.issubset(polarities)
    }
    if not conflicted_flag and not conflicted_dimensions:
        return None
    conflicting_refs = tuple(
        sorted(
            item.observation_id
            for item in verified_outcomes
            if item.conflicted or item.target_dimension in conflicted_dimensions
        )
    )
    return P03AttributionConflict(
        conflict_id=f"p03:{tick_id}:{tick_index}:{ordinal}:conflict",
        episode_ref=episode.episode_id,
        reason_code="evidence_conflicted",
        conflicting_observation_refs=conflicting_refs,
        confounder_refs=tuple(item.confounder_id for item in confounders),
        unresolved=True,
        reason="verified delayed outcomes conflict within at least one target dimension",
        provenance="p03.credit_assignment.policy",
    )


def _make_credit(
    *,
    tick_id: str,
    tick_index: int,
    ordinal: int,
    episode: P02InterventionEpisodeRecord,
    attribution_class: P03AttributionClass,
    contribution_mode: P03ContributionMode,
    window_status: P03WindowEvidenceStatus,
    outcomes: tuple[P03OutcomeObservation, ...],
    confounders: tuple[P03ConfounderSignal, ...],
    conflicts: tuple[P03AttributionConflict, ...],
    side_effect_dominant: bool,
    recommendation: P03UpdateRecommendationKind,
    guarded: bool,
    confidence_band: str,
    rationale_codes: tuple[str, ...],
) -> P03CreditRecord:
    recommendation_payload = P03LearningRecommendation(
        recommendation_id=f"p03:{tick_id}:{tick_index}:{ordinal}:recommendation",
        episode_ref=episode.episode_id,
        recommendation=recommendation,
        guarded=guarded,
        rationale_codes=rationale_codes,
        reason="p03 recommendation is explicit and remains separate from policy mutation",
        provenance="p03.credit_assignment.policy",
    )
    return P03CreditRecord(
        record_id=f"p03:{tick_id}:{tick_index}:{ordinal}:credit",
        episode_ref=episode.episode_id,
        attribution_class=attribution_class,
        contribution_mode=contribution_mode,
        window_status=window_status,
        primary_outcome_refs=tuple(
            item.observation_id for item in outcomes if item.target_dimension == "primary"
        ),
        side_effect_outcome_refs=tuple(
            item.observation_id for item in outcomes if item.target_dimension in _SIDE_EFFECT_DIMENSIONS
        ),
        confounder_refs=tuple(item.confounder_id for item in confounders),
        side_effect_dominant=side_effect_dominant,
        conflicts=conflicts,
        recommendation=recommendation_payload,
        confidence_band=confidence_band,
        rationale_codes=rationale_codes,
        provenance="p03.credit_assignment.policy",
    )


def _make_no_update(
    *,
    tick_id: str,
    tick_index: int,
    ordinal: int,
    episode: P02InterventionEpisodeRecord,
    attribution_class: P03AttributionClass,
    window_status: P03WindowEvidenceStatus,
    reason_code: str,
    evidence_refs: tuple[str, ...],
    confounders: tuple[P03ConfounderSignal, ...],
    reason: str,
) -> P03NoUpdateRecord:
    recommendation_payload = P03LearningRecommendation(
        recommendation_id=f"p03:{tick_id}:{tick_index}:{ordinal}:no_update_recommendation",
        episode_ref=episode.episode_id,
        recommendation=P03UpdateRecommendationKind.DO_NOT_UPDATE,
        guarded=False,
        rationale_codes=(reason_code,),
        reason="p03 no-update branch remains explicit and first-class for downstream consumers",
        provenance="p03.credit_assignment.policy",
    )
    return P03NoUpdateRecord(
        record_id=f"p03:{tick_id}:{tick_index}:{ordinal}:no_update",
        episode_ref=episode.episode_id,
        attribution_class=attribution_class,
        window_status=window_status,
        reason_code=reason_code,
        confounder_refs=tuple(item.confounder_id for item in confounders),
        evidence_refs=evidence_refs,
        recommendation=recommendation_payload,
        reason=reason,
        provenance="p03.credit_assignment.policy",
    )


def _build_gate(
    *,
    record_set: P03CreditAssignmentRecordSet,
) -> P03CreditAssignmentGateDecision:
    credit_ready = bool(record_set.credit_records)
    no_update_ready = bool(record_set.no_update_records)
    update_ready = bool(record_set.credit_records or record_set.no_update_records)
    restrictions: list[str] = []
    if not credit_ready:
        restrictions.append("credit_record_consumer_not_ready")
    if not no_update_ready:
        restrictions.append("no_update_consumer_not_ready")
    if not update_ready:
        restrictions.append("update_recommendation_consumer_not_ready")
    return P03CreditAssignmentGateDecision(
        credit_record_consumer_ready=credit_ready,
        no_update_consumer_ready=no_update_ready,
        update_recommendation_consumer_ready=update_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "p03 gate exposes typed readiness for credit/no-update/recommendation consumers "
            "without mutating downstream policy state"
        ),
    )


def _build_telemetry(
    *,
    record_set: P03CreditAssignmentRecordSet,
    gate: P03CreditAssignmentGateDecision,
) -> P03Telemetry:
    credit_records = record_set.credit_records
    no_update_records = record_set.no_update_records
    guarded_update_count = sum(
        int(
            item.recommendation.guarded
            and item.recommendation.recommendation
            not in {
                P03UpdateRecommendationKind.KEEP_UNCHANGED,
                P03UpdateRecommendationKind.DO_NOT_UPDATE,
            }
        )
        for item in credit_records
    )
    window_open_count = sum(
        int(item.window_status is P03WindowEvidenceStatus.WINDOW_STILL_OPEN)
        for item in (*credit_records, *no_update_records)
    )
    return P03Telemetry(
        evaluated_episode_count=len(record_set.evaluated_episode_refs),
        credit_record_count=len(credit_records),
        no_update_count=len(no_update_records),
        positive_credit_count=sum(
            int(item.attribution_class is P03AttributionClass.POSITIVE) for item in credit_records
        ),
        negative_credit_count=sum(
            int(item.attribution_class is P03AttributionClass.NEGATIVE) for item in credit_records
        ),
        mixed_credit_count=sum(
            int(item.attribution_class is P03AttributionClass.MIXED) for item in credit_records
        ),
        unresolved_credit_count=sum(
            int(item.attribution_class is P03AttributionClass.UNRESOLVED) for item in credit_records
        ),
        confounded_credit_count=sum(
            int(item.attribution_class is P03AttributionClass.CONFOUNDED_ASSOCIATION)
            for item in credit_records
        ),
        guarded_update_count=guarded_update_count,
        side_effect_dominant_count=sum(int(item.side_effect_dominant) for item in credit_records),
        outcome_window_open_count=window_open_count,
        downstream_consumer_ready=(
            gate.credit_record_consumer_ready
            or gate.no_update_consumer_ready
            or gate.update_recommendation_consumer_ready
        ),
    )


def _build_minimal_result(
    *,
    reason: str,
    restrictions: tuple[str, ...],
) -> P03CreditAssignmentResult:
    record_set = P03CreditAssignmentRecordSet(
        assignment_id="p03:minimal",
        evaluated_episode_refs=(),
        credit_records=(),
        no_update_records=(),
        conflicts=(),
        continuity_resolution_refs=(),
        confounder_bundle_ref=None,
        reason=reason,
    )
    gate = P03CreditAssignmentGateDecision(
        credit_record_consumer_ready=False,
        no_update_consumer_ready=False,
        update_recommendation_consumer_ready=False,
        restrictions=restrictions,
        reason=reason,
    )
    telemetry = P03Telemetry(
        evaluated_episode_count=0,
        credit_record_count=0,
        no_update_count=0,
        positive_credit_count=0,
        negative_credit_count=0,
        mixed_credit_count=0,
        unresolved_credit_count=0,
        confounded_credit_count=0,
        guarded_update_count=0,
        side_effect_dominant_count=0,
        outcome_window_open_count=0,
        downstream_consumer_ready=False,
    )
    scope = P03ScopeMarker(
        scope="rt01_hosted_p03_frontier_slice",
        rt01_hosted_only=True,
        p03_frontier_slice_only=True,
        no_policy_mutation_authority=True,
        no_scalar_reward_shortcut=True,
        no_raw_approval_shortcut=True,
        no_full_causal_discovery_claim=True,
        no_map_wide_rollout_claim=True,
        reason="p03 minimal fallback scope",
    )
    return P03CreditAssignmentResult(
        record_set=record_set,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )
