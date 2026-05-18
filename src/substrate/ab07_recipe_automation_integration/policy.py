from __future__ import annotations

from .models import (
    AB7AutomationReadinessAssessment,
    AB7AutomationReadinessStatus,
    AB7ConstraintKind,
    AB7ConstraintStatus,
    AB7IntegrationEnvelope,
    AB7MaturityGateStatus,
    AB7RecipeAutomationAbductiveFrame,
    AB7RecipeAutomationInput,
    AB7RecipeCandidateRecord,
    AB7RecipeHypothesisBinding,
    AB7RecipeLearningConstraint,
    AB7ScopeMarker,
)
from .telemetry import build_ab7_telemetry

_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "test_label",
    "hidden",
    "eval",
    "private",
)
_WORLD_SPECIFIC_FORBIDDEN: tuple[str, ...] = (
    "minecraft",
    "crafting_table",
    "water",
    "ore",
    "flask",
    "filter",
)
_CLAIM_BOUNDARY = (
    "AB7 constrains provisional recipe/precursor candidates through abductive evidence, support updates, attribution "
    "frames, and maturity gates, without converting them into executable automation."
)


def build_ab7_recipe_automation_integration(candidate_input: AB7RecipeAutomationInput) -> AB7IntegrationEnvelope:
    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    frame: AB7RecipeAutomationAbductiveFrame | None = None
    reason_codes: tuple[str, ...]

    if not unsafe_reasons and candidate_input.recipe_candidates:
        frame = _build_frame(candidate_input)
        reason_codes = ("ab7_integration_frame_emitted",) if frame is not None else ("ab7_frame_blocked",)
    elif unsafe_reasons:
        reason_codes = tuple(unsafe_reasons)
    else:
        reason_codes = ("no_recipe_candidates_for_integration",)

    telemetry = build_ab7_telemetry(
        candidate_input=candidate_input,
        frame=frame,
        unsafe_basis_count=len(unsafe_reasons),
    )
    scope_marker = AB7ScopeMarker(
        scope="ab07_recipe_automation_abductive_integration",
        recipe_automation_integration_only=True,
        no_recipe_candidate_generation_authority=True,
        no_recipe_execution_authority=True,
        no_automation_execution_authority=True,
        no_action_candidate_authority=True,
        no_ap01_request_authority=True,
        no_world_submission_authority=True,
        reason="ab7 emits bounded integration constraints only; no mature recipe or automation execution authority",
    )
    return AB7IntegrationEnvelope(
        tick_ref=candidate_input.tick_ref,
        frame=frame,
        telemetry=telemetry,
        scope_marker=scope_marker,
        reason_codes=reason_codes,
        source_lineage=("ab07_recipe_automation_integration.policy",),
    )


def _build_frame(candidate_input: AB7RecipeAutomationInput) -> AB7RecipeAutomationAbductiveFrame:
    constraints: list[AB7RecipeLearningConstraint] = []
    bindings: list[AB7RecipeHypothesisBinding] = []
    readiness: list[AB7AutomationReadinessAssessment] = []
    maturity_map: dict[str, str] = {}
    blocked_reasons: list[str] = []

    for candidate in candidate_input.recipe_candidates:
        candidate_constraints = _constraints_for_candidate(candidate_input, candidate)
        constraints.extend(candidate_constraints)

        per_candidate_blockers = tuple(
            code
            for item in candidate_constraints
            if item.status in {AB7ConstraintStatus.BLOCKED, AB7ConstraintStatus.UNSATISFIED}
            and item.constraint_kind is not AB7ConstraintKind.BLOCKS_AUTOMATION
            for code in item.reason_codes
        )
        blocked_reasons.extend(per_candidate_blockers)

        maturity_status = _maturity_status(candidate=candidate, blockers=per_candidate_blockers)
        maturity_map[candidate.recipe_candidate_ref] = maturity_status.value

        readiness_status = _readiness_status(
            maturity_status=maturity_status,
            has_blockers=bool(per_candidate_blockers),
            trace_count=len(candidate.supporting_trace_refs),
        )
        readiness.append(
            AB7AutomationReadinessAssessment(
                candidate_ref=candidate.recipe_candidate_ref,
                readiness_status=readiness_status,
                missing_requirements=tuple(
                    dict.fromkeys(
                        (*candidate.missing_evidence, *candidate_input.missing_evidence_refs, *candidate_input.disconfirming_evidence_refs)
                    )
                ),
                blocked_reasons=tuple(dict.fromkeys(per_candidate_blockers)),
                action_request_emitted=False,
                world_submission_emitted=False,
                automation_plan_created=False,
            )
        )

        bindings.append(
            AB7RecipeHypothesisBinding(
                binding_id=f"ab7:{candidate_input.tick_ref}:{candidate.recipe_candidate_ref}:binding",
                recipe_candidate_ref=candidate.recipe_candidate_ref,
                hypothesis_refs=tuple(candidate_input.ab_hypothesis_seed_refs),
                frontier_refs=tuple(candidate_input.ab_frontier_refs),
                update_refs=tuple(candidate_input.ab_update_refs),
                attribution_refs=tuple(candidate_input.ab_attribution_refs),
                explains_what=("public_station_effect_pattern", "provisional_input_output_link"),
                does_not_explain=("final_recipe_truth", "automation_execution"),
                unresolved_conflicts=tuple(candidate_input.unresolved_frontier_refs),
                disconfirming_evidence_refs=tuple(
                    dict.fromkeys((*candidate.disconfirming_trace_refs, *candidate_input.disconfirming_evidence_refs))
                ),
                confidence=_binding_confidence(maturity_status),
                confidence_policy="evidence_bounded",
                fact_status="not_fact",
            )
        )

    disconfirmation_requirements = tuple(
        dict.fromkeys(
            item
            for candidate in candidate_input.recipe_candidates
            for item in (*candidate.disconfirming_trace_refs, *candidate_input.disconfirming_evidence_refs)
        )
    )
    missing_requirements = tuple(
        dict.fromkeys(
            item
            for candidate in candidate_input.recipe_candidates
            for item in (*candidate.missing_evidence, *candidate_input.missing_evidence_refs)
        )
    )
    confounder_requirements = tuple(
        dict.fromkeys((*candidate_input.active_confounder_refs, *(ref for c in candidate_input.recipe_candidates for ref in c.confounder_refs)))
    )

    if candidate_input.protected_eval_only_rule:
        blocked_reasons.append("protected_evaluator_only_rule_forbidden")

    return AB7RecipeAutomationAbductiveFrame(
        frame_id=f"ab7:{candidate_input.tick_ref}:frame",
        recipe_candidate_refs=tuple(item.recipe_candidate_ref for item in candidate_input.recipe_candidates),
        precursor_candidate_refs=tuple(item.precursor_candidate_ref for item in candidate_input.precursor_candidates),
        lived_trace_refs=tuple(candidate_input.lived_trace_refs),
        p13_credit_refs=tuple(candidate_input.p13_credit_refs),
        p14_station_affordance_refs=tuple(candidate_input.p14_station_affordance_refs),
        ab_event_digest_refs=tuple(candidate_input.ab_event_digest_refs),
        ab_hypothesis_seed_refs=tuple(candidate_input.ab_hypothesis_seed_refs),
        ab_frontier_refs=tuple(candidate_input.ab_frontier_refs),
        ab_update_refs=tuple(candidate_input.ab_update_refs),
        ab_attribution_refs=tuple(candidate_input.ab_attribution_refs),
        abductive_constraints=tuple(constraints),
        bindings=tuple(bindings),
        disconfirmation_requirements=disconfirmation_requirements,
        missing_evidence_requirements=missing_requirements,
        confounder_requirements=confounder_requirements,
        maturity_gate_status=maturity_map,
        automation_readiness=tuple(readiness),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        claim_boundary=_CLAIM_BOUNDARY,
        fact_claimed=False,
        cause_confirmed=False,
        mature_recipe_claimed=False,
        automation_claimed=False,
        action_request_emitted=False,
        world_submission_emitted=False,
        hidden_eval_used=False,
        scenario_label_used=False,
    )


def _constraints_for_candidate(
    candidate_input: AB7RecipeAutomationInput,
    candidate: AB7RecipeCandidateRecord,
) -> tuple[AB7RecipeLearningConstraint, ...]:
    refs = tuple(
        dict.fromkeys(
            (
                *candidate.supporting_trace_refs,
                *candidate.effect_refs,
                *candidate.input_refs,
                *candidate_input.p14_station_affordance_refs,
                *candidate_input.ab_frontier_refs,
                *candidate_input.ab_update_refs,
                *candidate_input.ab_attribution_refs,
            )
        )
    )

    repeated_ok = len(candidate.supporting_trace_refs) >= 2
    effect_ok = bool(candidate.effect_refs)
    input_ok = bool(candidate.input_refs)
    affordance_ok = bool(candidate_input.p14_station_affordance_refs)
    frontier_ok = bool(candidate_input.ab_frontier_refs)
    p13_gate_ok = bool(candidate.p13_schema_candidate_refs or candidate_input.p13_credit_refs)
    update_ok = bool(candidate_input.ab_update_refs)
    attribution_ok = bool(candidate_input.ab_attribution_refs)
    confounder_blocked = bool(set(candidate.confounder_refs).intersection(set(candidate_input.active_confounder_refs)))
    disconfirming_blocked = bool(candidate.disconfirming_trace_refs or candidate_input.disconfirming_evidence_refs)
    missing_blocked = bool(candidate.missing_evidence or candidate_input.missing_evidence_refs)

    rep_missing = () if repeated_ok else ("repeated_trace_required",)
    eff_missing = () if effect_ok else ("effect_refs_required",)
    inp_missing = () if input_ok else ("input_refs_required",)
    aff_missing = () if affordance_ok else ("p14_station_affordance_refs_required",)
    fr_missing = () if frontier_ok else ("ab_frontier_refs_required",)
    p13_missing = () if p13_gate_ok else ("p13_maturity_gate_refs_required",)
    upd_missing = () if update_ok else ("ab_update_refs_missing",)
    att_missing = () if attribution_ok else ("ab_attribution_refs_missing",)
    conf_missing = () if not confounder_blocked else ("active_confounder_requires_resolution",)
    dis_missing = () if not disconfirming_blocked else ("disconfirming_trace_present",)
    miss_missing = () if not missing_blocked else tuple(dict.fromkeys((*candidate.missing_evidence, *candidate_input.missing_evidence_refs)))

    out: list[AB7RecipeLearningConstraint] = []
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_REPEATED_TRACE, refs, rep_missing, AB7ConstraintStatus.SATISFIED if repeated_ok else AB7ConstraintStatus.UNSATISFIED, rep_missing or ("repeated_trace_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_EFFECT_CORRELATION, refs, eff_missing, AB7ConstraintStatus.SATISFIED if effect_ok else AB7ConstraintStatus.BLOCKED, eff_missing or ("effect_correlation_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_INPUT_REFS, refs, inp_missing, AB7ConstraintStatus.SATISFIED if input_ok else AB7ConstraintStatus.BLOCKED, inp_missing or ("input_refs_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_STATION_AFFORDANCE, refs, aff_missing, AB7ConstraintStatus.SATISFIED if affordance_ok else AB7ConstraintStatus.BLOCKED, aff_missing or ("station_affordance_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_FRONTIER_SUPPORT, refs, fr_missing, AB7ConstraintStatus.SATISFIED if frontier_ok else AB7ConstraintStatus.BLOCKED, fr_missing or ("ab_frontier_support_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_CONFOUNDER_RESOLUTION, refs, p13_missing, AB7ConstraintStatus.SATISFIED if p13_gate_ok else AB7ConstraintStatus.BLOCKED, p13_missing or ("p13_gate_refs_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_UPDATE_SUPPORT, refs, upd_missing, AB7ConstraintStatus.SATISFIED if update_ok else AB7ConstraintStatus.PARTIALLY_SATISFIED, upd_missing or ("ab_update_support_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_ATTRIBUTION_SUPPORT, refs, att_missing, AB7ConstraintStatus.SATISFIED if attribution_ok else AB7ConstraintStatus.PARTIALLY_SATISFIED, att_missing or ("ab_attribution_support_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_CONFOUNDER_RESOLUTION, refs, conf_missing, AB7ConstraintStatus.SATISFIED if not confounder_blocked else AB7ConstraintStatus.BLOCKED, conf_missing or ("confounder_resolved",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_DISCONFIRMATION_CHECK, refs, dis_missing, AB7ConstraintStatus.SATISFIED if not disconfirming_blocked else AB7ConstraintStatus.BLOCKED, dis_missing or ("disconfirmation_check_satisfied",)))
    out.append(_constraint(candidate, AB7ConstraintKind.REQUIRES_MISSING_EVIDENCE_RESOLUTION, refs, miss_missing, AB7ConstraintStatus.SATISFIED if not missing_blocked else AB7ConstraintStatus.UNRESOLVED, miss_missing or ("missing_evidence_resolved",)))

    maturity_blocked = (
        (not repeated_ok)
        or (not effect_ok)
        or (not input_ok)
        or (not affordance_ok)
        or (not frontier_ok)
        or (not p13_gate_ok)
        or confounder_blocked
        or disconfirming_blocked
        or missing_blocked
    )
    out.append(
        _constraint(
            candidate,
            AB7ConstraintKind.BLOCKS_MATURITY,
            refs,
            ("maturity_blocked",) if maturity_blocked else (),
            AB7ConstraintStatus.BLOCKED if maturity_blocked else AB7ConstraintStatus.SATISFIED,
            ("maturity_blocked",) if maturity_blocked else ("maturity_gate_satisfied",),
        )
    )
    out.append(
        _constraint(
            candidate,
            AB7ConstraintKind.BLOCKS_AUTOMATION,
            refs,
            ("automation_forbidden_in_ab7",),
            AB7ConstraintStatus.BLOCKED,
            ("ab7_no_automation_execution",),
        )
    )
    return tuple(out)


def _constraint(
    candidate: AB7RecipeCandidateRecord,
    kind: AB7ConstraintKind,
    evidence_refs: tuple[str, ...],
    missing_evidence: tuple[str, ...],
    status: AB7ConstraintStatus,
    reason_codes: tuple[str, ...],
) -> AB7RecipeLearningConstraint:
    return AB7RecipeLearningConstraint(
        constraint_id=f"{candidate.recipe_candidate_ref}:{kind.value}",
        constraint_kind=kind,
        applies_to_candidate_refs=(candidate.recipe_candidate_ref,),
        evidence_refs=evidence_refs if evidence_refs else ("insufficient_evidence_refs",),
        missing_evidence=missing_evidence,
        status=status,
        reason_codes=reason_codes,
    )


def _maturity_status(*, candidate: AB7RecipeCandidateRecord, blockers: tuple[str, ...]) -> AB7MaturityGateStatus:
    if blockers:
        return AB7MaturityGateStatus.BLOCKED
    trace_count = len(candidate.supporting_trace_refs)
    if trace_count >= 2:
        return AB7MaturityGateStatus.REPEATED_TRACE_SUPPORTED
    if trace_count == 1:
        return AB7MaturityGateStatus.PROVISIONAL
    return AB7MaturityGateStatus.WEAK


def _readiness_status(
    *,
    maturity_status: AB7MaturityGateStatus,
    has_blockers: bool,
    trace_count: int,
) -> AB7AutomationReadinessStatus:
    if has_blockers:
        return AB7AutomationReadinessStatus.BLOCKED
    if trace_count <= 1:
        return AB7AutomationReadinessStatus.PROVISIONAL_ONLY
    if maturity_status is AB7MaturityGateStatus.REPEATED_TRACE_SUPPORTED:
        return AB7AutomationReadinessStatus.EVIDENCE_REQUIRED
    return AB7AutomationReadinessStatus.NOT_READY


def _binding_confidence(status: AB7MaturityGateStatus) -> float:
    if status is AB7MaturityGateStatus.BLOCKED:
        return 0.2
    if status is AB7MaturityGateStatus.WEAK:
        return 0.33
    if status is AB7MaturityGateStatus.PROVISIONAL:
        return 0.45
    return 0.58


def _unsafe_basis_reasons(candidate_input: AB7RecipeAutomationInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.public_only:
        reasons.append("public_only_required")
    if not candidate_input.hidden_eval_excluded:
        reasons.append("hidden_eval_exclusion_required")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_exclusion_required")
    if candidate_input.protected_eval_only_rule:
        reasons.append("protected_evaluator_only_rule_forbidden")

    values: list[str] = []
    for candidate in candidate_input.recipe_candidates:
        values.extend(
            (
                candidate.recipe_candidate_ref,
                *(candidate.input_refs),
                *(candidate.output_refs),
                *(candidate.effect_refs),
                *(candidate.supporting_trace_refs),
                *(candidate.disconfirming_trace_refs),
                *(candidate.p13_schema_candidate_refs),
                *(candidate.confounder_refs),
                *(candidate.missing_evidence),
            )
        )
    for precursor in candidate_input.precursor_candidates:
        values.extend(
            (
                precursor.precursor_candidate_ref,
                *(precursor.precursor_refs),
                *(precursor.effect_refs),
                *(precursor.missing_evidence),
            )
        )
    values.extend(
        (
            *candidate_input.lived_trace_refs,
            *candidate_input.p13_credit_refs,
            *candidate_input.p14_station_affordance_refs,
            *candidate_input.ab_event_digest_refs,
            *candidate_input.ab_hypothesis_seed_refs,
            *candidate_input.ab_frontier_refs,
            *candidate_input.ab_update_refs,
            *candidate_input.ab_attribution_refs,
            *candidate_input.unresolved_frontier_refs,
            *candidate_input.missing_evidence_refs,
            *candidate_input.disconfirming_evidence_refs,
            *candidate_input.active_confounder_refs,
            *candidate_input.public_effect_refs,
            *candidate_input.public_input_refs,
        )
    )
    joined = " ".join(str(item).lower() for item in values)
    for marker in _FORBIDDEN_MARKERS:
        if marker in joined:
            if marker in {"hidden", "eval", "private"}:
                reasons.append("hidden_eval_marker_in_ab7_basis")
            else:
                reasons.append("scenario_label_marker_in_ab7_basis")
            break
    for token in _WORLD_SPECIFIC_FORBIDDEN:
        if token in joined:
            reasons.append("world_specific_marker_forbidden_in_ab7_substrate")
            break

    for candidate in candidate_input.recipe_candidates:
        if candidate.hidden_recipe_used or candidate.protected_eval_used:
            reasons.append("recipe_candidate_uses_protected_eval_source")
            break

    return list(dict.fromkeys(reasons))
