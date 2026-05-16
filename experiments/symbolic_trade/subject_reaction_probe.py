from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum

from .internal_state import SelfStateProbeRecord


class ExecutionSurfaceLevel(str, Enum):
    FULL_SUBJECT_TICK_EXECUTION = "full_subject_tick_execution"
    PARTIAL_SUBJECT_TICK_EXECUTION = "partial_subject_tick_execution"
    OWNER_SURFACE_EXECUTION = "owner_surface_execution"
    ADAPTER_PROJECTION_ONLY = "adapter_projection_only"
    NON_EXECUTABLE = "non_executable"


@dataclass(frozen=True, slots=True)
class ExecutionSurfaceReport:
    execution_level: ExecutionSurfaceLevel
    attempted_surfaces: tuple[str, ...]
    successful_surfaces: tuple[str, ...]
    failed_surfaces: tuple[str, ...]
    fallback_reasons: tuple[str, ...]
    callable_surfaces: tuple[str, ...]
    subject_tick_used: bool
    owner_surface_used: bool
    adapter_projection_used: bool


@dataclass(frozen=True, slots=True)
class WorldEventReactionRecord:
    packet_id: str
    signal_kind: str
    source_authority: str
    observed_event_admitted: bool
    blocked_aperture_seen: bool
    contradiction_seen: bool
    self_state_as_world_evidence: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CounterpartClaimReactionRecord:
    packet_id: str
    claim_detected: bool
    claim_not_fact_preserved: bool
    promoted_to_fact: bool
    false_claim_contested: bool
    noisy_claim_contested: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class W01W06ReactionTraceSummary:
    phase_coverage: tuple[str, ...]
    coverage_complete: bool
    phase_coverage_verified: bool
    phase_coverage_verification_mode: str
    phase_coverage_evidence: tuple[str, ...]
    phase_coverage_missing_reason: str | None
    provenance: str
    w04_clean_applicability_allowed: bool
    w04_usefulness_as_permission: bool
    w05_desired_as_observed: bool
    w05_predicted_as_permitted: bool
    w05_must_not_execute_update: bool
    w06_correction_candidate_created: bool
    w06_correction_executed: bool
    w06_execution_prohibited: bool
    w06_residual_uncertainty_present: bool
    reason_codes: tuple[str, ...]
    prohibited_claims: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProbeClaimBoundaryRecord:
    allowed_claim: str
    forbidden_claims: tuple[str, ...]
    instrumentation_only: bool
    adapter_projection_not_competence: bool


@dataclass(frozen=True, slots=True)
class AReactionStepRecord:
    step_index: int
    packet_id: str
    world_event_reaction: WorldEventReactionRecord
    counterpart_claim_reaction: CounterpartClaimReactionRecord
    phase_trace_summary: W01W06ReactionTraceSummary
    execution_surface_source: str
    adapter_limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AReactionProbeRun:
    scenario_id: str
    stage: str
    execution_surface: ExecutionSurfaceReport
    self_state_probe: SelfStateProbeRecord
    steps: tuple[AReactionStepRecord, ...]
    b_visible_claim_summary: dict[str, object]
    reaction_markers: tuple[str, ...]
    falsifier_results: tuple[dict[str, object], ...] = ()
    claim_boundary: ProbeClaimBoundaryRecord = field(
        default_factory=lambda: ProbeClaimBoundaryRecord(
            allowed_claim=(
                "stage2.5 exposes bounded A-side reaction traces at the highest currently executable surface"
            ),
            forbidden_claims=(
                "no_autonomous_trade_claim",
                "no_negotiation_claim",
                "no_natural_language_claim",
                "no_economic_agency_claim",
                "no_subjective_need_awareness_claim",
                "no_social_cognition_claim",
            ),
            instrumentation_only=True,
            adapter_projection_not_competence=True,
        )
    )
    eval_only: dict[str, object] = field(default_factory=dict)


def stage25_reaction_to_dict(run: AReactionProbeRun, *, include_eval_only: bool = False) -> dict[str, object]:
    payload = {
        "scenario_id": run.scenario_id,
        "stage": run.stage,
        "execution_surface": asdict(run.execution_surface),
        "self_state_probe": asdict(run.self_state_probe),
        "steps": [asdict(step) for step in run.steps],
        "b_visible_claim_summary": run.b_visible_claim_summary,
        "reaction_markers": list(run.reaction_markers),
        "falsifier_results": list(run.falsifier_results),
        "claim_boundary": asdict(run.claim_boundary),
    }
    if include_eval_only:
        payload["eval_only"] = run.eval_only
    return payload
