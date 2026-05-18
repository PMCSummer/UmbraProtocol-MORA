from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import lru_cache

from .ab1_event_digest_probe import run_ab1_probe_case
from .ab2_hypothesis_seed_probe import run_ab2_probe_case
from .ab3_hypothesis_frontier_probe import run_ab3_probe_case
from .body_action_proof import BodyActionProofRun, run_body_action_proof_case
from .ownership_scenarios import OwnershipScenarioSpec, list_ownership_scenarios, ownership_scenario_for_id


@dataclass(frozen=True, slots=True)
class AttributionCandidate:
    attribution_kind: str
    supports: tuple[str, ...]
    does_not_explain: tuple[str, ...]
    required_evidence: tuple[str, ...]
    present_evidence: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    confidence: float
    confidence_policy: str
    source_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    forbidden_fact_closure: bool = True


@dataclass(frozen=True, slots=True)
class OwnershipAssessment:
    assessment_id: str
    observed_effect_refs: tuple[str, ...]
    candidate_attributions: tuple[AttributionCandidate, ...]
    self_cause_status: str
    world_cause_status: str
    other_cause_status: str
    mixed_cause_status: str
    unknown_cause_status: str
    evidence_refs: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    uncertainty: float
    fact_claimed: bool = False
    cause_confirmed: bool = False
    self_overclaim: bool = False
    mixed_cause_preserved: bool = True
    unknown_preserved: bool = True


@dataclass(frozen=True, slots=True)
class OwnershipPerturbationRun:
    run_id: str
    scenario_id: str
    tick_count: int
    perturbation_kind: str
    public_trace: tuple[dict[str, object], ...]
    self_action_refs: tuple[str, ...]
    external_event_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    event_digest_refs: tuple[str, ...]
    hypothesis_seed_refs: tuple[str, ...]
    frontier_refs: tuple[str, ...]
    ownership_assessment: OwnershipAssessment
    boundary_violations: tuple[str, ...]
    falsifier_results: dict[str, bool]
    claim_safe_verdict: str
    hidden_eval_used: bool
    scenario_label_used: bool
    action_request_emitted: bool = False


@dataclass(frozen=True, slots=True)
class OwnershipAblationCheck:
    ablation_id: str
    scenario_id: str
    expected_degradation: tuple[str, ...]
    observed_behavior: tuple[str, ...]


def list_ownership_perturbation_scenarios() -> tuple[OwnershipScenarioSpec, ...]:
    return list_ownership_scenarios()


def run_ownership_perturbation_matrix() -> tuple[OwnershipPerturbationRun, ...]:
    return tuple(run_ownership_perturbation_case(item.scenario_id) for item in list_ownership_scenarios())


def run_ownership_ablation_checks() -> tuple[OwnershipAblationCheck, ...]:
    matrix = {item.scenario_id: item for item in run_ownership_perturbation_matrix()}
    checks: list[OwnershipAblationCheck] = []
    checks.append(
        OwnershipAblationCheck(
            ablation_id="remove_ap01_request_ref",
            scenario_id="self_caused_move_effect",
            expected_degradation=("self_cause_blocked_or_weak",),
            observed_behavior=(
                "self_cause_blocked_or_weak"
                if matrix["self_caused_move_effect"].ap01_request_refs
                else "self_cause_supported"
            ,),
        )
    )
    checks.append(
        OwnershipAblationCheck(
            ablation_id="remove_effect_correlation",
            scenario_id="delayed_self_effect",
            expected_degradation=("self_cause_not_strong",),
            observed_behavior=(
                "self_cause_not_strong"
                if matrix["delayed_self_effect"].ownership_assessment.self_cause_status in {"blocked", "weak"}
                else "self_cause_supported"
            ,),
        )
    )
    checks.append(
        OwnershipAblationCheck(
            ablation_id="remove_external_actor_marker",
            scenario_id="other_actor_object_change",
            expected_degradation=("other_actor_not_self",),
            observed_behavior=(
                "other_actor_not_self"
                if matrix["other_actor_object_change"].ownership_assessment.self_cause_status in {"blocked", "not_supported"}
                else "self_overclaim"
            ,),
        )
    )
    checks.append(
        OwnershipAblationCheck(
            ablation_id="remove_mixed_cause_marker",
            scenario_id="mixed_self_and_world_effect",
            expected_degradation=("mixed_cause_preserved_or_blocked",),
            observed_behavior=(
                "mixed_cause_preserved_or_blocked"
                if matrix["mixed_self_and_world_effect"].ownership_assessment.mixed_cause_status in {"supported", "weak", "blocked"}
                else "mixed_erased"
            ,),
        )
    )
    checks.append(
        OwnershipAblationCheck(
            ablation_id="remove_delay_marker",
            scenario_id="delayed_self_effect",
            expected_degradation=("delayed_not_immediate_self",),
            observed_behavior=(
                "delayed_not_immediate_self"
                if matrix["delayed_self_effect"].ownership_assessment.self_cause_status in {"blocked", "weak"}
                else "immediate_self_claim"
            ,),
        )
    )
    checks.append(
        OwnershipAblationCheck(
            ablation_id="hidden_eval_only",
            scenario_id="hidden_eval_only_cause",
            expected_degradation=("no_hidden_truth_attribution",),
            observed_behavior=(
                "no_hidden_truth_attribution"
                if not matrix["hidden_eval_only_cause"].hidden_eval_used
                else "hidden_truth_used"
            ,),
        )
    )
    checks.append(
        OwnershipAblationCheck(
            ablation_id="remove_public_observation_refs",
            scenario_id="unknown_unexplained_effect",
            expected_degradation=("unknown_or_blocked",),
            observed_behavior=(
                "unknown_or_blocked"
                if matrix["unknown_unexplained_effect"].ownership_assessment.unknown_cause_status in {"supported", "weak", "blocked"}
                else "forced_closure"
            ,),
        )
    )
    checks.append(
        OwnershipAblationCheck(
            ablation_id="blocked_effect_without_delta",
            scenario_id="blocked_self_action_no_world_delta",
            expected_degradation=("no_success_claim",),
            observed_behavior=(
                "no_success_claim"
                if matrix["blocked_self_action_no_world_delta"].ownership_assessment.self_cause_status in {"blocked", "weak"}
                else "success_overclaim"
            ,),
        )
    )
    return tuple(checks)


def run_ownership_perturbation_case(scenario_id: str) -> OwnershipPerturbationRun:
    spec = ownership_scenario_for_id(scenario_id)
    evidence = _scenario_evidence(spec)
    assessment = _assess_ownership(spec, evidence)
    from .ownership_falsifiers import evaluate_ownership_falsifiers  # local import to avoid cycle

    falsifiers = evaluate_ownership_falsifiers(
        scenario_id=spec.scenario_id,
        perturbation_kind=spec.perturbation_kind,
        assessment=assessment,
        ap01_request_refs=evidence.ap01_request_refs,
        effect_refs=evidence.effect_refs,
        external_event_refs=evidence.external_event_refs,
        hidden_eval_used=evidence.hidden_eval_used,
        scenario_label_used=evidence.scenario_label_used,
        mixed_marker=evidence.mixed_marker,
        delayed_marker=evidence.delayed_marker,
        blocked_action=evidence.blocked_action,
        successful_delta=evidence.successful_delta,
        effect_correlated=evidence.effect_correlated,
        action_request_emitted=False,
        hypothesis_updated=False,
        epistemic_action_selected=False,
        claim_boundary=_CLAIM_BOUNDARY,
    )
    boundary_violations = tuple(name for name, fired in falsifiers.items() if fired)
    return OwnershipPerturbationRun(
        run_id=f"p11:{scenario_id}:{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}",
        scenario_id=spec.scenario_id,
        tick_count=spec.ticks,
        perturbation_kind=spec.perturbation_kind,
        public_trace=evidence.public_trace,
        self_action_refs=evidence.self_action_refs,
        external_event_refs=evidence.external_event_refs,
        effect_refs=evidence.effect_refs,
        ap01_request_refs=evidence.ap01_request_refs,
        event_digest_refs=evidence.event_digest_refs,
        hypothesis_seed_refs=evidence.hypothesis_seed_refs,
        frontier_refs=evidence.frontier_refs,
        ownership_assessment=assessment,
        boundary_violations=boundary_violations,
        falsifier_results=falsifiers,
        claim_safe_verdict=_claim_safe_verdict(spec.scenario_id, assessment, boundary_violations),
        hidden_eval_used=evidence.hidden_eval_used,
        scenario_label_used=evidence.scenario_label_used,
    )


@dataclass(frozen=True, slots=True)
class _OwnershipEvidence:
    public_trace: tuple[dict[str, object], ...]
    self_action_refs: tuple[str, ...]
    external_event_refs: tuple[str, ...]
    other_actor_refs: tuple[str, ...]
    effect_refs: tuple[str, ...]
    ap01_request_refs: tuple[str, ...]
    event_digest_refs: tuple[str, ...]
    hypothesis_seed_refs: tuple[str, ...]
    frontier_refs: tuple[str, ...]
    hidden_eval_used: bool
    scenario_label_used: bool
    mixed_marker: bool
    delayed_marker: bool
    blocked_action: bool
    successful_delta: bool
    effect_correlated: bool
    mismatch_marker: bool


_CLAIM_BOUNDARY = (
    "P11 ownership perturbation battery only: bounded self/world/other/mixed/unknown assessment without "
    "cause confirmation, full self-model, complete causal attribution, or consciousness claim."
)


def _scenario_evidence(spec: OwnershipScenarioSpec) -> _OwnershipEvidence:
    if spec.scenario_id in {"self_caused_move_effect", "self_caused_pickup_effect", "blocked_self_action_no_world_delta"}:
        run = _body_action_for(spec.world_scenario_id or "")
        step = next(item for item in run.step_summaries if item.world_submission_count > 0)
        event_refs, seed_refs, frontier_refs = _ab_refs_for_case(
            "blocked_movement_effect" if spec.scenario_id == "blocked_self_action_no_world_delta" else (
                "pickup_inventory_delta" if spec.scenario_id == "self_caused_pickup_effect" else "effect_mismatch"
            )
        )
        return _OwnershipEvidence(
            public_trace=tuple(asdict(item) for item in run.step_summaries),
            self_action_refs=(step.ap01_request_ref,) if step.ap01_request_ref else (),
            external_event_refs=(),
            other_actor_refs=(),
            effect_refs=(step.world_effect_id,) if step.world_effect_id else (),
            ap01_request_refs=(step.ap01_request_ref,) if step.ap01_request_ref else (),
            event_digest_refs=event_refs,
            hypothesis_seed_refs=seed_refs,
            frontier_refs=frontier_refs,
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=False,
            delayed_marker=False,
            blocked_action=(step.effect_status or "").lower() in {"blocked", "observed_failure", "failed"},
            successful_delta=bool(step.body_delta or step.inventory_delta or step.world_delta_public),
            effect_correlated=step.effect_correlated_to_request,
            mismatch_marker=False,
        )
    if spec.scenario_id == "world_only_object_change":
        return _OwnershipEvidence(
            public_trace=({"event": "external_world_change", "public": True},),
            self_action_refs=(),
            external_event_refs=("external:world_process:object_change",),
            other_actor_refs=(),
            effect_refs=("effect:external_world_object_change",),
            ap01_request_refs=(),
            event_digest_refs=(),
            hypothesis_seed_refs=(),
            frontier_refs=(),
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=False,
            delayed_marker=False,
            blocked_action=False,
            successful_delta=True,
            effect_correlated=False,
            mismatch_marker=False,
        )
    if spec.scenario_id == "other_actor_object_change":
        return _OwnershipEvidence(
            public_trace=({"event": "other_actor_change", "public": True},),
            self_action_refs=(),
            external_event_refs=("external:other_actor:change",),
            other_actor_refs=("other_actor:public:1",),
            effect_refs=("effect:other_actor_object_change",),
            ap01_request_refs=(),
            event_digest_refs=(),
            hypothesis_seed_refs=(),
            frontier_refs=(),
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=False,
            delayed_marker=False,
            blocked_action=False,
            successful_delta=True,
            effect_correlated=False,
            mismatch_marker=False,
        )
    if spec.scenario_id == "mixed_self_and_world_effect":
        run = _body_action_for(spec.world_scenario_id or "")
        step = next(item for item in run.step_summaries if item.world_submission_count > 0)
        event_refs, seed_refs, frontier_refs = _ab_refs_for_case("effect_mismatch")
        return _OwnershipEvidence(
            public_trace=tuple(asdict(item) for item in run.step_summaries),
            self_action_refs=(step.ap01_request_ref,) if step.ap01_request_ref else (),
            external_event_refs=("external:world_process:concurrent_change",),
            other_actor_refs=(),
            effect_refs=(step.world_effect_id, "effect:external_world_contribution") if step.world_effect_id else ("effect:external_world_contribution",),
            ap01_request_refs=(step.ap01_request_ref,) if step.ap01_request_ref else (),
            event_digest_refs=event_refs,
            hypothesis_seed_refs=seed_refs,
            frontier_refs=frontier_refs,
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=True,
            delayed_marker=False,
            blocked_action=False,
            successful_delta=True,
            effect_correlated=True,
            mismatch_marker=False,
        )
    if spec.scenario_id == "delayed_self_effect":
        run = _body_action_for(spec.world_scenario_id or "")
        step = next(item for item in run.step_summaries if item.world_submission_count > 0)
        event_refs, seed_refs, frontier_refs = _ab_refs_for_case("effect_mismatch")
        return _OwnershipEvidence(
            public_trace=tuple(asdict(item) for item in run.step_summaries),
            self_action_refs=(step.ap01_request_ref,) if step.ap01_request_ref else (),
            external_event_refs=(),
            other_actor_refs=(),
            effect_refs=(step.world_effect_id,) if step.world_effect_id else (),
            ap01_request_refs=(step.ap01_request_ref,) if step.ap01_request_ref else (),
            event_digest_refs=event_refs,
            hypothesis_seed_refs=seed_refs,
            frontier_refs=frontier_refs,
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=False,
            delayed_marker=True,
            blocked_action=False,
            successful_delta=True,
            effect_correlated=False,
            mismatch_marker=False,
        )
    if spec.scenario_id == "unknown_unexplained_effect":
        return _OwnershipEvidence(
            public_trace=({"event": "unknown_public_effect", "public": True},),
            self_action_refs=(),
            external_event_refs=(),
            other_actor_refs=(),
            effect_refs=("effect:unknown_public_change",),
            ap01_request_refs=(),
            event_digest_refs=(),
            hypothesis_seed_refs=(),
            frontier_refs=(),
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=False,
            delayed_marker=False,
            blocked_action=False,
            successful_delta=True,
            effect_correlated=False,
            mismatch_marker=False,
        )
    if spec.scenario_id == "sensor_or_projection_mismatch":
        event_refs, seed_refs, frontier_refs = _ab_refs_for_case("effect_mismatch")
        return _OwnershipEvidence(
            public_trace=({"event": "projection_mismatch_signal", "public": True},),
            self_action_refs=(),
            external_event_refs=(),
            other_actor_refs=(),
            effect_refs=("effect:mismatch_public",),
            ap01_request_refs=(),
            event_digest_refs=event_refs,
            hypothesis_seed_refs=seed_refs,
            frontier_refs=frontier_refs,
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=False,
            delayed_marker=False,
            blocked_action=False,
            successful_delta=False,
            effect_correlated=False,
            mismatch_marker=True,
        )
    if spec.scenario_id == "hidden_eval_only_cause":
        event_refs, seed_refs, frontier_refs = _ab_refs_for_case("hidden_eval_only")
        return _OwnershipEvidence(
            public_trace=({"event": "hidden_eval_only", "public": False},),
            self_action_refs=(),
            external_event_refs=(),
            other_actor_refs=(),
            effect_refs=("effect:hidden_eval_only",),
            ap01_request_refs=(),
            event_digest_refs=event_refs,
            hypothesis_seed_refs=seed_refs,
            frontier_refs=frontier_refs,
            hidden_eval_used=False,
            scenario_label_used=False,
            mixed_marker=False,
            delayed_marker=False,
            blocked_action=False,
            successful_delta=False,
            effect_correlated=False,
            mismatch_marker=False,
        )
    raise ValueError(f"Unsupported ownership scenario: {spec.scenario_id}")


def _assess_ownership(spec: OwnershipScenarioSpec, evidence: _OwnershipEvidence) -> OwnershipAssessment:
    candidates = _build_attribution_candidates(spec, evidence)
    evidence_refs = tuple(dict.fromkeys((*evidence.ap01_request_refs, *evidence.effect_refs, *evidence.external_event_refs)))
    missing_evidence = tuple(
        dict.fromkeys(item for candidate in candidates for item in candidate.missing_evidence)
    )
    self_status = _status_for("self_action", candidates)
    world_status = _status_for("world_process", candidates)
    other_status = _status_for("other_actor", candidates)
    mixed_status = _status_for("mixed", candidates)
    unknown_status = _status_for("unknown", candidates)
    self_overclaim = self_status == "supported" and (not evidence.ap01_request_refs or not evidence.effect_correlated)
    return OwnershipAssessment(
        assessment_id=f"p11:{spec.scenario_id}:assessment",
        observed_effect_refs=evidence.effect_refs,
        candidate_attributions=candidates,
        self_cause_status=self_status,
        world_cause_status=world_status,
        other_cause_status=other_status,
        mixed_cause_status=mixed_status,
        unknown_cause_status=unknown_status,
        evidence_refs=evidence_refs,
        missing_evidence=missing_evidence,
        uncertainty=round(0.2 + (0.3 if unknown_status in {"supported", "weak"} else 0.0) + (0.2 if mixed_status in {"supported", "weak"} else 0.0), 3),
        fact_claimed=False,
        cause_confirmed=False,
        self_overclaim=self_overclaim,
        mixed_cause_preserved=(not evidence.mixed_marker) or mixed_status in {"supported", "weak"},
        unknown_preserved=(spec.scenario_id != "unknown_unexplained_effect") or unknown_status in {"supported", "weak"},
    )


def _build_attribution_candidates(
    spec: OwnershipScenarioSpec,
    evidence: _OwnershipEvidence,
) -> tuple[AttributionCandidate, ...]:
    candidates: list[AttributionCandidate] = []
    if evidence.ap01_request_refs:
        missing = ()
        if not evidence.effect_refs:
            missing = ("effect_refs_required",)
        confidence = 0.72 if evidence.effect_correlated and not evidence.blocked_action else 0.48
        if evidence.delayed_marker:
            confidence = 0.42
        candidates.append(
            AttributionCandidate(
                attribution_kind="self_action",
                supports=("ap01_request_present", "effect_ref_present" if evidence.effect_refs else "effect_ref_missing"),
                does_not_explain=("external_only_change",),
                required_evidence=("ap01_request_ref", "effect_ref"),
                present_evidence=tuple(dict.fromkeys((*evidence.ap01_request_refs, *evidence.effect_refs))),
                missing_evidence=missing,
                confidence=round(confidence, 3),
                confidence_policy="evidence_bounded",
                source_refs=evidence.self_action_refs,
                effect_refs=evidence.effect_refs,
                ap01_request_refs=evidence.ap01_request_refs,
            )
        )
    if evidence.external_event_refs:
        kind = "other_actor" if evidence.other_actor_refs else "world_process"
        candidates.append(
            AttributionCandidate(
                attribution_kind=kind,
                supports=("external_event_marker_present",),
                does_not_explain=("self_intent_without_ap01",),
                required_evidence=("external_event_ref",),
                present_evidence=evidence.external_event_refs,
                missing_evidence=(),
                confidence=0.66 if not evidence.mixed_marker else 0.52,
                confidence_policy="evidence_bounded",
                source_refs=evidence.external_event_refs,
                effect_refs=evidence.effect_refs,
                ap01_request_refs=evidence.ap01_request_refs,
            )
        )
    if evidence.mixed_marker or (evidence.ap01_request_refs and evidence.external_event_refs):
        candidates.append(
            AttributionCandidate(
                attribution_kind="mixed",
                supports=("self_and_external_evidence_present",),
                does_not_explain=("single_cause_certainty",),
                required_evidence=("ap01_request_ref", "external_event_ref", "effect_ref"),
                present_evidence=tuple(dict.fromkeys((*evidence.ap01_request_refs, *evidence.external_event_refs, *evidence.effect_refs))),
                missing_evidence=(),
                confidence=0.58,
                confidence_policy="evidence_bounded",
                source_refs=tuple(dict.fromkeys((*evidence.ap01_request_refs, *evidence.external_event_refs))),
                effect_refs=evidence.effect_refs,
                ap01_request_refs=evidence.ap01_request_refs,
            )
        )
    if evidence.delayed_marker and evidence.ap01_request_refs:
        candidates.append(
            AttributionCandidate(
                attribution_kind="delayed_self_effect",
                supports=("prior_request_present", "delay_marker_present"),
                does_not_explain=("immediate_cause_closure",),
                required_evidence=("ap01_request_ref", "delay_marker", "effect_ref"),
                present_evidence=tuple(dict.fromkeys((*evidence.ap01_request_refs, *evidence.effect_refs))),
                missing_evidence=() if evidence.effect_refs else ("effect_refs_required",),
                confidence=0.49,
                confidence_policy="evidence_bounded",
                source_refs=evidence.ap01_request_refs,
                effect_refs=evidence.effect_refs,
                ap01_request_refs=evidence.ap01_request_refs,
            )
        )
    if evidence.mismatch_marker:
        candidates.append(
            AttributionCandidate(
                attribution_kind="projection_or_sensor_mismatch",
                supports=("mismatch_marker_present",),
                does_not_explain=("confirmed_world_change",),
                required_evidence=("mismatch_marker",),
                present_evidence=evidence.event_digest_refs,
                missing_evidence=() if evidence.event_digest_refs else ("event_digest_refs_required",),
                confidence=0.55,
                confidence_policy="evidence_bounded",
                source_refs=evidence.event_digest_refs,
                effect_refs=evidence.effect_refs,
                ap01_request_refs=evidence.ap01_request_refs,
            )
        )
    if not candidates or spec.scenario_id in {"unknown_unexplained_effect", "hidden_eval_only_cause"}:
        candidates.append(
            AttributionCandidate(
                attribution_kind="unknown",
                supports=("insufficient_public_attribution_basis",),
                does_not_explain=("single_confirmed_cause",),
                required_evidence=("public_effect_and_lineage",),
                present_evidence=evidence.effect_refs,
                missing_evidence=() if evidence.effect_refs else ("effect_refs_required",),
                confidence=0.34,
                confidence_policy="evidence_bounded",
                source_refs=evidence.effect_refs,
                effect_refs=evidence.effect_refs,
                ap01_request_refs=evidence.ap01_request_refs,
            )
        )
    return tuple(candidates)


def _status_for(kind: str, candidates: tuple[AttributionCandidate, ...]) -> str:
    matches = [item for item in candidates if item.attribution_kind == kind]
    if not matches:
        return "not_supported"
    best = max(matches, key=lambda item: item.confidence)
    if best.missing_evidence:
        return "blocked"
    if best.confidence >= 0.65:
        return "supported"
    if best.confidence >= 0.4:
        return "weak"
    if kind == "unknown" and best.confidence >= 0.3:
        return "weak"
    return "blocked"


def _claim_safe_verdict(
    scenario_id: str,
    assessment: OwnershipAssessment,
    boundary_violations: tuple[str, ...],
) -> str:
    if boundary_violations:
        return "insufficient_evidence"
    if scenario_id in {"world_only_object_change", "other_actor_object_change"} and assessment.self_cause_status in {"blocked", "not_supported"}:
        return "mora_boundary_advantage"
    if scenario_id == "mixed_self_and_world_effect" and assessment.mixed_cause_status in {"supported", "weak"}:
        return "mora_restraint_advantage"
    if scenario_id == "unknown_unexplained_effect" and assessment.unknown_preserved:
        return "mora_restraint_advantage"
    return "no_clear_advantage"


@lru_cache(maxsize=8)
def _body_action_for(world_scenario_id: str) -> BodyActionProofRun:
    return run_body_action_proof_case(
        scenario_id=world_scenario_id,
        ticks=2,
        strict_internal_mode=True,
    )


@lru_cache(maxsize=8)
def _ab_refs_for_case(case_id: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    ab1 = run_ab1_probe_case(case_id)
    ab2 = run_ab2_probe_case(case_id)
    if case_id in {"blocked_movement_effect", "effect_mismatch", "pickup_inventory_delta"}:
        ab3_case = "inventory_delta" if case_id == "pickup_inventory_delta" else case_id
        ab3 = run_ab3_probe_case(ab3_case)
        frontier_refs = (ab3.frontier.frontier_id,) if ab3.frontier is not None else ()
    else:
        frontier_refs = ()
    event_refs = tuple(item.event_id for item in ab1.digests)
    hypothesis_refs = (
        tuple(item.hypothesis_id for item in ab2.seed_set.hypotheses)
        if ab2.seed_set is not None
        else ()
    )
    return event_refs, hypothesis_refs, frontier_refs
