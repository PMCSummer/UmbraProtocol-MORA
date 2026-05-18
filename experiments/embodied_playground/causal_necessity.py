from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CausalNecessityClaimSafeVerdict(str, Enum):
    MORA_CAUSAL_LOAD_BEARING = "mora_causal_load_bearing"
    PARTIAL_CAUSAL_EVIDENCE = "partial_causal_evidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class AblationOutcomeClass(str, Enum):
    EXPECTED_DEGRADATION_OBSERVED = "expected_degradation_observed"
    HARD_ABLATION_NO_EFFECT = "hard_ablation_no_effect"
    NON_INFORMATIVE_ABLATION = "non_informative_ablation"
    EXPECTED_NO_EFFECT_DUE_MISSING_BASIS = "expected_no_effect_due_missing_basis"


class AblationKind(str, Enum):
    REMOVE_BASIS = "remove_basis"
    BLOCK_PUBLIC_BASIS = "block_public_basis"
    SUPPRESS_ACP01 = "suppress_acp01"
    SUPPRESS_AP01_PUBLICATION = "suppress_ap01_publication"
    SUPPRESS_EFFECT_FEEDBACK = "suppress_effect_feedback"
    SUPPRESS_DRIVE_BASIS = "suppress_drive_basis"
    SUPPRESS_CAPABILITY_BASIS = "suppress_capability_basis"
    SUPPRESS_CAPACITY_BASIS = "suppress_capacity_basis"
    SUPPRESS_PROXIMITY_BASIS = "suppress_proximity_basis"
    SUPPRESS_RESIDUE_FEEDBACK = "suppress_residue_feedback"


@dataclass(frozen=True, slots=True)
class ExpectedDegradation:
    ablation_id: str
    expected: tuple[str, ...]
    allowed_outcomes: tuple[str, ...]
    forbidden_outcomes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AblationSpec:
    ablation_id: str
    seam_id: str
    description: str
    ablation_kind: AblationKind
    expected_degradation: ExpectedDegradation
    forbidden_fallbacks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AblationTrace:
    ablation_id: str
    scenario_id: str
    subject_tick_used: bool
    acp01_used: bool
    acp01_candidate_count: int
    ap01_published_count: int
    world_submission_count: int
    effect_feedback_count: int
    revalidation_count: int
    residue_count: int
    blocked_count: int
    hidden_eval_used: bool
    scenario_label_used: bool
    degradation_observed: bool
    unexpected_success: bool
    boundary_violations: tuple[str, ...]
    basis_flow: dict[str, bool]
    ablation_outcome_class: AblationOutcomeClass = AblationOutcomeClass.NON_INFORMATIVE_ABLATION
    non_informative_reason: str | None = None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StrictModeTrace:
    strict_mode_enabled: bool
    auto_builder_detected: bool
    fabricated_basis_refs: tuple[str, ...]
    upstream_basis_refs: tuple[str, ...]
    downstream_basis_refs: tuple[str, ...]
    valid_basis_flow: bool
    violations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CausalNecessityMetricSummary:
    ablation_sensitivity_score: float
    silent_fabrication_count: int
    unexpected_success_count: int
    boundary_integrity_score: float
    basis_flow_integrity_score: float
    degradation_match_rate: float
    hidden_substitution_count: int
    no_effect_ablation_count: int
    hard_ablation_no_effect_count: int
    non_informative_ablation_count: int
    expected_no_effect_due_missing_basis_count: int
    expected_degradation_count: int


@dataclass(frozen=True, slots=True)
class CausalNecessityRun:
    run_id: str
    scenario_id: str
    mode: str
    baseline_trace: AblationTrace
    ablation_traces: tuple[AblationTrace, ...]
    strict_trace: StrictModeTrace
    expected_degradations: tuple[ExpectedDegradation, ...]
    observed_degradations: tuple[str, ...]
    falsifier_results: dict[str, bool]
    metric_summary: CausalNecessityMetricSummary
    claim_safe_verdict: CausalNecessityClaimSafeVerdict
    summary: str
    claim_boundary: str = (
        "P9 causal necessity evidence only; not consciousness or general autonomy proof."
    )


def required_ablation_specs() -> tuple[AblationSpec, ...]:
    return (
        AblationSpec(
            ablation_id="no_acp01",
            seam_id="acp01_internal_candidate_production",
            description="Suppress ACP01 candidate production path.",
            ablation_kind=AblationKind.SUPPRESS_ACP01,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_acp01",
                expected=("no_candidate", "no_publication", "no_world_submission"),
                allowed_outcomes=("blocked_or_revalidation",),
                forbidden_outcomes=("unexpected_success",),
            ),
            forbidden_fallbacks=("manual_provider", "scenario_shortcut"),
        ),
        AblationSpec(
            ablation_id="no_ap01",
            seam_id="ap01_subject_action_publication",
            description="Suppress AP01 publication/execution path.",
            ablation_kind=AblationKind.SUPPRESS_AP01_PUBLICATION,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_ap01",
                expected=("no_publication", "no_world_submission"),
                allowed_outcomes=("no_candidate",),
                forbidden_outcomes=("world_submission",),
            ),
            forbidden_fallbacks=("direct_bridge_submit",),
        ),
        AblationSpec(
            ablation_id="no_drive_basis",
            seam_id="drive_basis",
            description="Suppress drive basis while object is visible.",
            ablation_kind=AblationKind.SUPPRESS_DRIVE_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_drive_basis",
                expected=("no_candidate", "no_publication"),
                allowed_outcomes=("abstain",),
                forbidden_outcomes=("pickup_without_drive",),
            ),
            forbidden_fallbacks=("visible_object_shortcut",),
        ),
        AblationSpec(
            ablation_id="no_public_object_basis",
            seam_id="public_object_basis",
            description="Withhold public object basis while drive is present.",
            ablation_kind=AblationKind.BLOCK_PUBLIC_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_public_object_basis",
                expected=("no_candidate", "no_publication"),
                allowed_outcomes=("abstain",),
                forbidden_outcomes=("drive_only_pickup",),
            ),
            forbidden_fallbacks=("hidden_substitution",),
        ),
        AblationSpec(
            ablation_id="no_action_surface_basis",
            seam_id="action_surface_basis",
            description="Remove action-surface basis for pickup path.",
            ablation_kind=AblationKind.REMOVE_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_action_surface_basis",
                expected=("no_candidate", "no_publication"),
                allowed_outcomes=("abstain",),
                forbidden_outcomes=("action_surface_fabricated",),
            ),
            forbidden_fallbacks=("surface_fabrication",),
        ),
        AblationSpec(
            ablation_id="no_proximity_basis",
            seam_id="proximity_basis",
            description="Suppress proximity/reachability basis.",
            ablation_kind=AblationKind.SUPPRESS_PROXIMITY_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_proximity_basis",
                expected=("no_publication", "blocked_or_revalidation"),
                allowed_outcomes=("no_candidate",),
                forbidden_outcomes=("pickup_without_proximity",),
            ),
            forbidden_fallbacks=("distance_ignored",),
        ),
        AblationSpec(
            ablation_id="no_capacity_basis",
            seam_id="capacity_basis",
            description="Suppress inventory capacity basis.",
            ablation_kind=AblationKind.SUPPRESS_CAPACITY_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_capacity_basis",
                expected=("no_publication", "blocked_or_revalidation"),
                allowed_outcomes=("no_candidate",),
                forbidden_outcomes=("pickup_without_capacity",),
            ),
            forbidden_fallbacks=("capacity_ignored",),
        ),
        AblationSpec(
            ablation_id="no_effect_feedback",
            seam_id="effect_feedback_path",
            description="Suppress effect feedback into next tick context.",
            ablation_kind=AblationKind.SUPPRESS_EFFECT_FEEDBACK,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_effect_feedback",
                expected=("no_feedback_claim",),
                allowed_outcomes=("no_candidate",),
                forbidden_outcomes=("fabricated_effect_feedback",),
            ),
            forbidden_fallbacks=("fabricated_feedback",),
        ),
        AblationSpec(
            ablation_id="no_residue_feedback",
            seam_id="w06_like_residue_path",
            description="Suppress residue/revalidation feedback for blocked effects.",
            ablation_kind=AblationKind.SUPPRESS_RESIDUE_FEEDBACK,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_residue_feedback",
                expected=("blocked_or_revalidation",),
                allowed_outcomes=("no_candidate",),
                forbidden_outcomes=("clean_success_without_residue",),
            ),
            forbidden_fallbacks=("failure_erasure",),
        ),
        AblationSpec(
            ablation_id="no_permission_basis",
            seam_id="w04_like_permission_gate",
            description="Suppress permission/applicability basis.",
            ablation_kind=AblationKind.REMOVE_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_permission_basis",
                expected=("no_publication", "blocked_or_revalidation"),
                allowed_outcomes=("no_candidate",),
                forbidden_outcomes=("permission_free_publish",),
            ),
            forbidden_fallbacks=("permit_shortcut",),
        ),
        AblationSpec(
            ablation_id="no_prediction_permission_separation",
            seam_id="w05_like_prediction_permission_separation",
            description="Check desire/prediction not treated as permission.",
            ablation_kind=AblationKind.REMOVE_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="no_prediction_permission_separation",
                expected=("no_completion",),
                allowed_outcomes=("blocked_or_revalidation",),
                forbidden_outcomes=("desire_as_permission",),
            ),
            forbidden_fallbacks=("prediction_as_success",),
        ),
        AblationSpec(
            ablation_id="hidden_eval_substitution_attempt",
            seam_id="public_eval_boundary",
            description="Attempt hidden/eval substitution under missing public basis.",
            ablation_kind=AblationKind.BLOCK_PUBLIC_BASIS,
            expected_degradation=ExpectedDegradation(
                ablation_id="hidden_eval_substitution_attempt",
                expected=("no_hidden_substitution", "no_publication"),
                allowed_outcomes=("no_candidate",),
                forbidden_outcomes=("hidden_substitution",),
            ),
            forbidden_fallbacks=("hidden_eval_targeting",),
        ),
    )


def ablation_spec_for_id(ablation_id: str) -> AblationSpec:
    for spec in required_ablation_specs():
        if spec.ablation_id == ablation_id:
            return spec
    raise ValueError(f"Unknown ablation id: {ablation_id}")


def default_ablation_ids() -> tuple[str, ...]:
    return tuple(spec.ablation_id for spec in required_ablation_specs())
