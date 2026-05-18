from __future__ import annotations

from .models import (
    AB4BasisStatus,
    AB4CandidateKind,
    AB4EIGLevel,
    AB4EpistemicBasisInput,
    AB4EpistemicBasisResult,
    AB4EpistemicCandidateBasis,
    AB4ExpectedInformationGain,
    AB4ScopeMarker,
)
from .telemetry import build_ab4_telemetry

_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "test_label",
    "hidden",
    "eval",
    "private",
)
_WORLD_SPECIFIC_TOKENS: tuple[str, ...] = (
    "water",
    "flask",
    "ore",
    "filter",
    "station",
    "recipe",
    "minecraft",
)


def build_ab4_epistemic_candidate_basis(candidate_input: AB4EpistemicBasisInput) -> AB4EpistemicBasisResult:
    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    bases: tuple[AB4EpistemicCandidateBasis, ...] = ()
    frontier = candidate_input.frontier
    if not unsafe_reasons and frontier is not None:
        bases = _build_bases(candidate_input)

    telemetry = build_ab4_telemetry(
        candidate_input=candidate_input,
        bases=bases,
        unsafe_basis_count=len(unsafe_reasons),
    )
    scope_marker = AB4ScopeMarker(
        scope="ab04_evidence_seeking_candidate_basis",
        epistemic_basis_only=True,
        no_action_candidate_authority=True,
        no_ap01_request_authority=True,
        no_execution_authority=True,
        no_world_submission_authority=True,
        no_hypothesis_update_authority=True,
        reason="ab4 emits bounded epistemic basis only; no action/publication/execution authority",
    )
    if unsafe_reasons:
        reason_codes = tuple(unsafe_reasons)
    elif not bases:
        reason_codes = ("no_epistemic_basis_emitted",)
    else:
        reason_codes = ("epistemic_basis_emitted",)
    return AB4EpistemicBasisResult(
        tick_ref=candidate_input.tick_ref,
        frontier_ref=frontier.frontier_id if frontier is not None else None,
        bases=bases,
        telemetry=telemetry,
        scope_marker=scope_marker,
        reason_codes=reason_codes,
        source_lineage=("ab04_epistemic_candidate_basis.policy",),
    )


def _build_bases(candidate_input: AB4EpistemicBasisInput) -> tuple[AB4EpistemicCandidateBasis, ...]:
    frontier = candidate_input.frontier
    assert frontier is not None
    if not frontier.hypotheses:
        return ()

    uncertainty_refs = tuple(dict.fromkeys((*frontier.unresolved_conflicts, *frontier.missing_evidence)))
    if not uncertainty_refs:
        return ()
    if not frontier.discriminating_tests:
        return ()
    if frontier.closure_status.value == "blocked":
        return ()

    kinds: list[AB4CandidateKind] = [AB4CandidateKind.INSPECT]
    if frontier.unresolved_conflicts:
        kinds.extend((AB4CandidateKind.WAIT, AB4CandidateKind.REOBSERVE))
    if frontier.missing_evidence:
        kinds.append(AB4CandidateKind.CHECK_CONSISTENCY)

    public_basis_refs = tuple(
        dict.fromkeys(
            (
                *candidate_input.source_refs,
                *candidate_input.observation_refs,
                *candidate_input.residue_refs,
                *candidate_input.effect_refs,
                *frontier.source_event_refs,
                *frontier.source_residue_refs,
                *frontier.source_effect_refs,
            )
        )
    )
    if not public_basis_refs:
        return ()

    hypothesis_refs = tuple(item.hypothesis_id for item in frontier.hypotheses)
    discriminates_between = tuple(item for item in frontier.competitive_neighborhood if item in hypothesis_refs)
    if len(discriminates_between) < 2 and len(hypothesis_refs) >= 2:
        discriminates_between = hypothesis_refs[:2]
    if len(discriminates_between) < 2:
        return ()

    bases: list[AB4EpistemicCandidateBasis] = []
    for index, kind in enumerate(kinds, start=1):
        eig = _expected_information_gain(
            kind=kind,
            unresolved_conflict_count=len(frontier.unresolved_conflicts),
            missing_evidence_count=len(frontier.missing_evidence),
            scoring_refs=tuple(frontier.discriminating_tests),
            allow_numeric=candidate_input.allow_numeric_eig,
        )
        confidence = _confidence_for_basis(eig.level, uncertainty_refs_count=len(uncertainty_refs))
        bases.append(
            AB4EpistemicCandidateBasis(
                basis_id=f"ab4:{candidate_input.tick_ref}:{frontier.frontier_id}:{kind.value}:{index}",
                frontier_ref=frontier.frontier_id,
                hypothesis_refs=hypothesis_refs,
                candidate_kind=kind,
                discriminates_between=discriminates_between,
                expected_information_gain=eig,
                expected_information_gain_policy="ab4_evidence_bounded_eig_v1",
                uncertainty_basis_refs=uncertainty_refs,
                missing_evidence_refs=tuple(frontier.missing_evidence),
                discriminating_test_refs=tuple(frontier.discriminating_tests),
                public_basis_refs=public_basis_refs,
                allowed_action_kinds=(kind.value,),
                target_refs=tuple(frontier.competitive_neighborhood),
                risk=_risk_for_kind(kind),
                cost=_cost_for_kind(kind),
                confidence=confidence,
                confidence_policy="bounded",
                forbidden_execution=True,
                no_publication_authority=True,
                no_world_submission_authority=True,
                hidden_eval_used=False,
                scenario_label_used=False,
                action_request_emitted=False,
                ap01_request_ref=None,
                fact_claimed=False,
                cause_confirmed=False,
                basis_status=AB4BasisStatus.USABLE,
            )
        )
    return tuple(bases)


def _expected_information_gain(
    *,
    kind: AB4CandidateKind,
    unresolved_conflict_count: int,
    missing_evidence_count: int,
    scoring_refs: tuple[str, ...],
    allow_numeric: bool,
) -> AB4ExpectedInformationGain:
    if unresolved_conflict_count <= 0 and missing_evidence_count <= 0:
        level = AB4EIGLevel.NONE
    elif kind in {AB4CandidateKind.WAIT, AB4CandidateKind.REOBSERVE} and unresolved_conflict_count > 0:
        level = AB4EIGLevel.MEDIUM
    elif kind is AB4CandidateKind.INSPECT:
        level = AB4EIGLevel.MEDIUM
    elif missing_evidence_count > 0:
        level = AB4EIGLevel.LOW
    else:
        level = AB4EIGLevel.LOW

    numeric: float | None = None
    if allow_numeric and scoring_refs:
        numeric = {
            AB4EIGLevel.NONE: 0.0,
            AB4EIGLevel.LOW: 0.3,
            AB4EIGLevel.MEDIUM: 0.55,
            AB4EIGLevel.HIGH: 0.75,
        }[level]
    return AB4ExpectedInformationGain(
        level=level,
        numeric=numeric,
        scoring_refs=scoring_refs,
        scoring_policy="qualitative_evidence_bounded" if not allow_numeric else "bounded_numeric_with_scoring_refs",
    )


def _confidence_for_basis(level: AB4EIGLevel, *, uncertainty_refs_count: int) -> float:
    base = {
        AB4EIGLevel.NONE: 0.1,
        AB4EIGLevel.LOW: 0.35,
        AB4EIGLevel.MEDIUM: 0.55,
        AB4EIGLevel.HIGH: 0.7,
    }[level]
    penalty = min(0.2, float(max(0, uncertainty_refs_count - 1)) * 0.03)
    return round(max(0.1, min(0.8, base - penalty)), 3)


def _risk_for_kind(kind: AB4CandidateKind) -> float:
    if kind in {AB4CandidateKind.WAIT, AB4CandidateKind.REOBSERVE}:
        return 0.1
    if kind is AB4CandidateKind.CHECK_CONSISTENCY:
        return 0.2
    return 0.25


def _cost_for_kind(kind: AB4CandidateKind) -> float:
    if kind is AB4CandidateKind.WAIT:
        return 0.15
    if kind in {AB4CandidateKind.REOBSERVE, AB4CandidateKind.CHECK_CONSISTENCY}:
        return 0.25
    return 0.3


def _unsafe_basis_reasons(candidate_input: AB4EpistemicBasisInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.public_only:
        reasons.append("public_only_required")
    if not candidate_input.hidden_eval_excluded:
        reasons.append("hidden_eval_exclusion_required")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_exclusion_required")
    if not candidate_input.source_refs:
        reasons.append("source_refs_required")

    frontier = candidate_input.frontier
    if frontier is None:
        reasons.append("frontier_required")
    else:
        if frontier.fact_claimed or frontier.selected_fact_hypothesis_id is not None or frontier.cause_confirmed:
            reasons.append("fact_claiming_frontier_forbidden")
        if frontier.hidden_eval_used:
            reasons.append("hidden_eval_frontier_forbidden")
        if frontier.scenario_label_used:
            reasons.append("scenario_label_frontier_forbidden")
        if len(frontier.hypotheses) < 2:
            reasons.append("competing_hypotheses_required")

    values = (
        tuple(candidate_input.source_refs)
        + tuple(candidate_input.observation_refs)
        + tuple(candidate_input.residue_refs)
        + tuple(candidate_input.effect_refs)
    )
    lowered = " ".join(str(item).lower() for item in values)
    for marker in _FORBIDDEN_MARKERS:
        if marker in lowered:
            if marker in {"hidden", "eval", "private"}:
                reasons.append("hidden_eval_marker_in_basis")
            else:
                reasons.append("scenario_marker_in_basis")
            break
    for token in _WORLD_SPECIFIC_TOKENS:
        if token in lowered:
            reasons.append("world_specific_marker_forbidden_in_ab4_substrate")
            break
    return list(dict.fromkeys(reasons))
