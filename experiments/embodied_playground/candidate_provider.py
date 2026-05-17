from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Protocol

try:
    from substrate.ap01_subject_action_publication import (
        AP01ActionPublicationCandidate,
        AP01ActionPublicationCandidateSet,
        AP01CandidateOrigin,
    )
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from substrate.ap01_subject_action_publication import (
        AP01ActionPublicationCandidate,
        AP01ActionPublicationCandidateSet,
        AP01CandidateOrigin,
    )

from experiments.embodied_playground.models import ActionSpaceFrame, ObservationFrame


class CandidateProvider(Protocol):
    provider_kind: str
    candidate_origin: AP01CandidateOrigin
    no_scenario_label_used: bool
    no_hidden_truth_used: bool
    no_eval_only_used: bool

    def provide_candidates(
        self,
        *,
        bridge_tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
    ) -> AP01ActionPublicationCandidateSet | None: ...


@dataclass(frozen=True, slots=True)
class ManualCandidateSpec:
    action_kind: str
    target_ref: str | None = None
    args: dict[str, object] = field(default_factory=dict)
    intended_effect: str | None = None
    permission_refs: tuple[str, ...] = ("W04:permit",)
    evidence_refs: tuple[str, ...] = ("W01:observation",)
    episode_refs: tuple[str, ...] = ("P02:episode",)
    affordance_binding_refs: tuple[str, ...] = ("A04:binding",)
    source_phase_refs: tuple[str, ...] = ("W04:permission", "W05:routing", "W06:revision")
    permitted_refs: tuple[str, ...] = ("W05:permitted",)
    residue_refs: tuple[str, ...] = ()
    revalidation_refs: tuple[str, ...] = ()
    blocked_claim_refs: tuple[str, ...] = ()
    desired_refs: tuple[str, ...] = ()
    predicted_refs: tuple[str, ...] = ()
    observed_refs: tuple[str, ...] = ()
    forbidden_basis_markers: tuple[str, ...] = ()
    no_hidden_truth_used: bool = True
    no_eval_only_used: bool = True
    no_scenario_label_used: bool = True


@dataclass(slots=True)
class ManualCandidateProvider:
    plans_by_tick: dict[int, tuple[ManualCandidateSpec, ...]]
    provider_kind: str = "manual_candidate_provider"
    candidate_origin: AP01CandidateOrigin = AP01CandidateOrigin.SUBJECT_TICK_CANDIDATE_BASIS
    no_scenario_label_used: bool = True
    no_hidden_truth_used: bool = True
    no_eval_only_used: bool = True

    def provide_candidates(
        self,
        *,
        bridge_tick_index: int,
        observation: ObservationFrame,
        action_space: ActionSpaceFrame,
    ) -> AP01ActionPublicationCandidateSet | None:
        _ = observation
        _ = action_space
        specs = self.plans_by_tick.get(bridge_tick_index)
        if not specs:
            return None

        candidates: list[AP01ActionPublicationCandidate] = []
        for offset, spec in enumerate(specs, start=1):
            candidates.append(
                AP01ActionPublicationCandidate(
                    candidate_id=f"manual:candidate:{bridge_tick_index}:{offset}",
                    action_kind=spec.action_kind,
                    target_ref=spec.target_ref,
                    args=dict(spec.args),
                    intended_effect=spec.intended_effect or f"{spec.action_kind}_effect",
                    source_tick_ref=f"bridge_subject_tick:{bridge_tick_index}",
                    source_cycle_ref=f"bridge_cycle:{bridge_tick_index}",
                    source_phase_refs=spec.source_phase_refs,
                    affordance_binding_refs=spec.affordance_binding_refs,
                    permission_refs=spec.permission_refs,
                    evidence_refs=spec.evidence_refs,
                    episode_refs=spec.episode_refs,
                    residue_refs=spec.residue_refs,
                    revalidation_refs=spec.revalidation_refs,
                    blocked_claim_refs=spec.blocked_claim_refs,
                    desired_refs=spec.desired_refs,
                    predicted_refs=spec.predicted_refs,
                    observed_refs=spec.observed_refs,
                    permitted_refs=spec.permitted_refs,
                    candidate_origin=self.candidate_origin,
                    forbidden_basis_markers=spec.forbidden_basis_markers,
                    no_hidden_truth_used=spec.no_hidden_truth_used,
                    no_eval_only_used=spec.no_eval_only_used,
                    no_scenario_label_used=spec.no_scenario_label_used,
                )
            )

        return AP01ActionPublicationCandidateSet(
            candidate_set_id=f"manual:candidate_set:{bridge_tick_index}",
            candidates=tuple(candidates),
            source_lineage=("embodied_playground.p3.manual_candidate_provider",),
            reason="manual_candidate_input",
        )
