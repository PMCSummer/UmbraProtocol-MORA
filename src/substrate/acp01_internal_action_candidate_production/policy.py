from __future__ import annotations

from dataclasses import asdict, is_dataclass

from substrate.acp01_internal_action_candidate_production.models import (
    ACP01ActionCandidateProposal,
    ACP01ActionSurfaceBasis,
    ACP01CandidateProductionDecision,
    ACP01CandidateProductionInput,
    ACP01CandidateProductionResult,
    ACP01CandidateProductionTelemetry,
    ACP01CapabilityBasis,
    ACP01CapabilityStatus,
    ACP01DecisionStatus,
    ACP01ScopeMarker,
)
from substrate.ap01_subject_action_publication import (
    AP01ActionPublicationCandidate,
    AP01ActionPublicationCandidateSet,
    AP01CandidateOrigin,
)

_FORBIDDEN_TOKENS: tuple[str, ...] = (
    "scenario_id",
    "scenario:",
    "scenario_to_action",
    "select_action_by_scenario",
    "expected_outcome",
    "test_name",
    "test_case",
    "demo_case",
    "gui_label",
    "manual_action",
    "eval_only",
    "private_world",
    "private_map",
    "hidden_truth",
    "hidden_map",
    "full_map",
    "hidden_object",
    "hidden_inventory",
)

_PICKUP_DRIVE_TOKENS: tuple[str, ...] = (
    "water",
    "collect",
    "pickup",
    "gather",
    "resource",
    "container",
)


def build_acp01_internal_action_candidates(
    candidate_input: ACP01CandidateProductionInput,
) -> ACP01CandidateProductionResult:
    if not isinstance(candidate_input, ACP01CandidateProductionInput):
        raise TypeError(
            "build_acp01_internal_action_candidates requires ACP01CandidateProductionInput"
        )

    unsafe_reasons = _unsafe_basis_reasons(candidate_input)
    if unsafe_reasons:
        decision = ACP01CandidateProductionDecision(
            decision_id=f"acp01:{candidate_input.tick_ref}:decision:unsafe",
            status=ACP01DecisionStatus.UNSAFE_BASIS,
            reason_codes=tuple(unsafe_reasons),
            proposal=None,
        )
        return _result_from_decisions(
            candidate_input=candidate_input,
            decisions=(decision,),
            candidate_set=None,
            reason="acp01 rejected private/eval/scenario basis",
        )

    decisions: list[ACP01CandidateProductionDecision] = []
    proposals: list[ACP01ActionCandidateProposal] = []

    pickup_proposal, pickup_missing, pickup_blocked = _maybe_propose_pickup(candidate_input)
    if pickup_proposal is not None:
        proposals.append(pickup_proposal)
        decisions.append(
            ACP01CandidateProductionDecision(
                decision_id=f"acp01:{candidate_input.tick_ref}:decision:pickup",
                status=ACP01DecisionStatus.PROPOSED,
                reason_codes=("pickup_candidate_basis_complete",),
                proposal=pickup_proposal,
            )
        )
    else:
        if pickup_blocked:
            decisions.append(
                ACP01CandidateProductionDecision(
                    decision_id=f"acp01:{candidate_input.tick_ref}:decision:pickup_blocked",
                    status=ACP01DecisionStatus.BLOCKED,
                    reason_codes=("pickup_basis_blocked",),
                    proposal=None,
                    missing_requirements=tuple(pickup_missing),
                    blocked_refs=tuple(pickup_blocked),
                )
            )
        elif pickup_missing:
            decisions.append(
                ACP01CandidateProductionDecision(
                    decision_id=f"acp01:{candidate_input.tick_ref}:decision:pickup_insufficient",
                    status=ACP01DecisionStatus.INSUFFICIENT_BASIS,
                    reason_codes=("pickup_basis_incomplete",),
                    proposal=None,
                    missing_requirements=tuple(pickup_missing),
                )
            )

    if not proposals:
        inspect_proposal = _maybe_propose_inspect(candidate_input)
        if inspect_proposal is not None:
            proposals.append(inspect_proposal)
            decisions.append(
                ACP01CandidateProductionDecision(
                    decision_id=f"acp01:{candidate_input.tick_ref}:decision:inspect",
                    status=ACP01DecisionStatus.PROPOSED,
                    reason_codes=("inspect_candidate_for_uncertainty_or_probe",),
                    proposal=inspect_proposal,
                )
            )

    if not proposals and _needs_revalidation(candidate_input):
        decisions.append(
            ACP01CandidateProductionDecision(
                decision_id=f"acp01:{candidate_input.tick_ref}:decision:revalidate",
                status=ACP01DecisionStatus.REVALIDATION_REQUIRED,
                reason_codes=("previous_effect_block_or_failure_requires_revalidation",),
                proposal=None,
            )
        )

    if not decisions:
        decisions.append(
            ACP01CandidateProductionDecision(
                decision_id=f"acp01:{candidate_input.tick_ref}:decision:none",
                status=ACP01DecisionStatus.NO_CANDIDATE,
                reason_codes=("no_internal_candidate_basis",),
                proposal=None,
            )
        )

    if len(proposals) > 1:
        decisions.append(
            ACP01CandidateProductionDecision(
                decision_id=f"acp01:{candidate_input.tick_ref}:decision:multi_abstain",
                status=ACP01DecisionStatus.MULTIPLE_CANDIDATES_ABSTAINED,
                reason_codes=("multiple_candidates_abstained_for_p4_narrow_scope",),
                proposal=None,
            )
        )
        return _result_from_decisions(
            candidate_input=candidate_input,
            decisions=tuple(decisions),
            candidate_set=None,
            reason="acp01 abstained on multiple proposals in p4 narrow scope",
        )

    chosen = proposals[0] if proposals else None
    if chosen is not None:
        proposal_unsafe_reasons = _unsafe_proposal_reasons(chosen)
        if proposal_unsafe_reasons:
            decision = ACP01CandidateProductionDecision(
                decision_id=f"acp01:{candidate_input.tick_ref}:decision:unsafe_proposal",
                status=ACP01DecisionStatus.UNSAFE_BASIS,
                reason_codes=tuple(proposal_unsafe_reasons),
                proposal=None,
            )
            return _result_from_decisions(
                candidate_input=candidate_input,
                decisions=(decision,),
                candidate_set=None,
                reason="acp01 rejected proposal carrying private/eval/scenario/test/gui/manual markers",
            )

    candidate_set = (
        _to_ap01_candidate_set(candidate_input=candidate_input, proposal=chosen)
        if chosen is not None
        else None
    )
    if candidate_set is not None:
        candidate_set_unsafe_reasons = _unsafe_candidate_set_reasons(candidate_set)
        if candidate_set_unsafe_reasons:
            decision = ACP01CandidateProductionDecision(
                decision_id=f"acp01:{candidate_input.tick_ref}:decision:unsafe_candidate_set",
                status=ACP01DecisionStatus.UNSAFE_BASIS,
                reason_codes=tuple(candidate_set_unsafe_reasons),
                proposal=None,
            )
            return _result_from_decisions(
                candidate_input=candidate_input,
                decisions=(decision,),
                candidate_set=None,
                reason="acp01 rejected candidate set carrying private/eval/scenario/test/gui/manual markers",
            )
    return _result_from_decisions(
        candidate_input=candidate_input,
        decisions=tuple(decisions),
        candidate_set=candidate_set,
        reason="acp01 evaluated typed internal basis and produced bounded candidate decisions",
    )


def _maybe_propose_pickup(
    candidate_input: ACP01CandidateProductionInput,
) -> tuple[ACP01ActionCandidateProposal | None, list[str], list[str]]:
    drives = tuple(candidate_input.internal_drive_bases)
    objects = tuple(candidate_input.visible_object_bases)
    surfaces = tuple(candidate_input.action_surface_bases)
    capabilities = tuple(candidate_input.capability_bases)

    missing: list[str] = []
    blocked: list[str] = []

    relevant_drive = _find_relevant_pickup_drive(drives)
    if relevant_drive is None:
        missing.append("internal_drive_basis")
        return None, missing, blocked

    target_object = _find_pickup_target_object(drives=drives, objects=objects)
    if target_object is None:
        missing.append("visible_target_object_basis")
        return None, missing, blocked

    pickup_surface = _find_surface_for_action(
        surfaces=surfaces,
        action_kind="pickup",
        target_ref=target_object.object_ref,
    )
    if pickup_surface is None:
        missing.append("pickup_action_surface_basis")
        return None, missing, blocked

    proximity = _capability_status(
        capabilities=capabilities,
        capability_kinds=("proximity", "reachability"),
        target_ref=target_object.object_ref,
    )
    if proximity is ACP01CapabilityStatus.BLOCKED:
        blocked.append("capability:proximity_blocked")
    elif proximity in {ACP01CapabilityStatus.UNKNOWN, ACP01CapabilityStatus.INSUFFICIENT}:
        missing.append("proximity_basis")

    capacity = _capability_status(
        capabilities=capabilities,
        capability_kinds=("inventory_capacity", "capacity"),
        target_ref=None,
    )
    if capacity is ACP01CapabilityStatus.BLOCKED:
        blocked.append("capability:inventory_capacity_blocked")
    elif capacity in {ACP01CapabilityStatus.UNKNOWN, ACP01CapabilityStatus.INSUFFICIENT}:
        missing.append("inventory_capacity_basis")

    if blocked or missing:
        return None, missing, blocked

    basis_refs = tuple(
        dict.fromkeys(
            (
                f"observation:{candidate_input.observation_basis.observation_id}",
                f"drive:{relevant_drive.drive_ref}",
                f"object:{target_object.object_ref}",
                f"surface:{pickup_surface.surface_ref}",
                f"capability:proximity:{target_object.object_ref}",
                "capability:inventory_capacity",
            )
        )
    )
    return (
        ACP01ActionCandidateProposal(
            candidate_id=f"acp01:{candidate_input.tick_ref}:pickup:{target_object.object_ref}",
            action_kind="pickup",
            target_ref=target_object.object_ref,
            args={},
            intended_effect=f"pickup:{target_object.object_ref}",
            basis_refs=basis_refs,
            missing_basis=(),
            blocked_basis=(),
            confidence=min(0.95, max(0.5, target_object.confidence)),
            revalidation_required=False,
        ),
        [],
        [],
    )


def _maybe_propose_inspect(
    candidate_input: ACP01CandidateProductionInput,
) -> ACP01ActionCandidateProposal | None:
    if not candidate_input.visible_object_bases:
        return None

    inspect_surface = _find_surface_for_action(
        surfaces=candidate_input.action_surface_bases,
        action_kind="inspect",
        target_ref=None,
    )
    if inspect_surface is None:
        return None

    uncertain = next(
        (
            obj
            for obj in candidate_input.visible_object_bases
            if obj.claim_not_fact or obj.confidence < 0.6
        ),
        None,
    )
    drive_requests_uncertainty_probe = any(
        any(token in drive.drive_kind.lower() for token in ("curiosity", "uncertainty", "clarify", "inspect"))
        for drive in candidate_input.internal_drive_bases
    )
    # P4 guardrail: inspect requires explicit uncertainty/clarification basis.
    if uncertain is None and not drive_requests_uncertainty_probe:
        return None

    target = uncertain or candidate_input.visible_object_bases[0]
    basis_refs = tuple(
        dict.fromkeys(
            (
                f"observation:{candidate_input.observation_basis.observation_id}",
                f"object:{target.object_ref}",
                f"surface:{inspect_surface.surface_ref}",
                *(f"drive:{drive.drive_ref}" for drive in candidate_input.internal_drive_bases),
            )
        )
    )
    return ACP01ActionCandidateProposal(
        candidate_id=f"acp01:{candidate_input.tick_ref}:inspect:{target.object_ref}",
        action_kind="inspect",
        target_ref=target.object_ref,
        args={"probe_mode": "public_uncertainty"},
        intended_effect=f"inspect:{target.object_ref}",
        basis_refs=basis_refs,
        missing_basis=(),
        blocked_basis=(),
        confidence=0.55,
        revalidation_required=False,
    )


def _needs_revalidation(candidate_input: ACP01CandidateProductionInput) -> bool:
    for effect in candidate_input.effect_feedback_bases:
        status = effect.status.lower()
        if status in {"blocked", "failed", "partial"}:
            return True
    return False


def _to_ap01_candidate_set(
    *,
    candidate_input: ACP01CandidateProductionInput,
    proposal: ACP01ActionCandidateProposal,
) -> AP01ActionPublicationCandidateSet:
    phase_refs = ("ACP01:internal_candidate_producer", "W04:permit:acp01", "W05:routing:acp01", "W06:revision:acp01")
    permission_refs = ("W04:permit:acp01",)
    evidence_refs = tuple(
        dict.fromkeys(
            (
                f"OBS:{candidate_input.observation_basis.observation_id}",
                *proposal.basis_refs,
            )
        )
    )
    episode_refs = tuple(
        dict.fromkeys(
            (
                f"P02:episode:{candidate_input.tick_ref}",
                *candidate_input.observation_basis.previous_effect_refs,
            )
        )
    )
    affordance_refs = tuple(
        dict.fromkeys(
            ref.replace("surface:", "A04:binding:")
            for ref in proposal.basis_refs
            if ref.startswith("surface:")
        )
    )

    ap01_candidate = AP01ActionPublicationCandidate(
        candidate_id=proposal.candidate_id,
        action_kind=proposal.action_kind,
        target_ref=proposal.target_ref,
        args=dict(proposal.args),
        intended_effect=proposal.intended_effect,
        source_tick_ref=candidate_input.tick_ref,
        source_cycle_ref=f"acp01:cycle:{candidate_input.tick_ref}",
        source_phase_refs=phase_refs,
        affordance_binding_refs=affordance_refs,
        permission_refs=permission_refs,
        evidence_refs=evidence_refs or ("W01:public_observation",),
        episode_refs=episode_refs or ("P02:episode:acp01",),
        residue_refs=(),
        revalidation_refs=(),
        blocked_claim_refs=(),
        desired_refs=(),
        predicted_refs=(),
        observed_refs=tuple(candidate_input.observation_basis.visible_object_refs),
        permitted_refs=("W05:permitted:acp01",),
        candidate_origin=AP01CandidateOrigin.SUBJECT_TICK_CANDIDATE_BASIS,
        forbidden_basis_markers=(),
        no_hidden_truth_used=True,
        no_eval_only_used=True,
        no_scenario_label_used=True,
    )
    return AP01ActionPublicationCandidateSet(
        candidate_set_id=f"acp01:{candidate_input.tick_ref}:candidate_set",
        candidates=(ap01_candidate,),
        source_lineage=("acp01_internal_action_candidate_production.policy",),
        reason="acp01_internal_candidate_set_for_ap01",
    )


def _unsafe_basis_reasons(candidate_input: ACP01CandidateProductionInput) -> list[str]:
    reasons: list[str] = []
    if not candidate_input.private_eval_excluded:
        reasons.append("private_eval_not_excluded")
    if not candidate_input.scenario_label_excluded:
        reasons.append("scenario_label_not_excluded")

    sections = _decision_bearing_sections_from_candidate_input(candidate_input)
    reasons.extend(_scan_decision_sections_for_forbidden_markers(sections, path_prefix="acp01_input"))
    return list(dict.fromkeys(reasons))


def _find_relevant_pickup_drive(drives: tuple[object, ...]):
    for drive in drives:
        drive_kind = str(getattr(drive, "drive_kind", "")).lower()
        if any(token in drive_kind for token in _PICKUP_DRIVE_TOKENS):
            return drive
    return None


def _find_pickup_target_object(*, drives: tuple[object, ...], objects: tuple[object, ...]):
    goal_refs = {
        str(getattr(drive, "resource_or_goal_ref", "")).lower()
        for drive in drives
        if getattr(drive, "resource_or_goal_ref", None)
    }
    if goal_refs:
        for obj in objects:
            object_ref = str(getattr(obj, "object_ref", "")).lower()
            object_kind = str(getattr(obj, "object_kind", "")).lower()
            if object_ref in goal_refs or any(goal in object_ref for goal in goal_refs) or any(goal in object_kind for goal in goal_refs):
                return obj
        # If a goal is explicit but no visible object matches it, do not fall
        # back to arbitrary visible objects in P4 narrow scope.
        return None
    return objects[0] if objects else None


def _find_surface_for_action(
    *,
    surfaces: tuple[ACP01ActionSurfaceBasis, ...],
    action_kind: str,
    target_ref: str | None,
) -> ACP01ActionSurfaceBasis | None:
    for surface in surfaces:
        if action_kind not in surface.action_kinds:
            continue
        if target_ref is None:
            return surface
        if surface.target_ref in {None, target_ref, "item:visible", "object:visible"}:
            return surface
    return None


def _capability_status(
    *,
    capabilities: tuple[ACP01CapabilityBasis, ...],
    capability_kinds: tuple[str, ...],
    target_ref: str | None,
) -> ACP01CapabilityStatus:
    lowered_kinds = {item.lower() for item in capability_kinds}
    for capability in capabilities:
        if capability.capability_kind.lower() not in lowered_kinds:
            continue
        if target_ref is not None and capability.target_ref not in {None, target_ref}:
            continue
        return capability.status
    return ACP01CapabilityStatus.UNKNOWN


def _result_from_decisions(
    *,
    candidate_input: ACP01CandidateProductionInput,
    decisions: tuple[ACP01CandidateProductionDecision, ...],
    candidate_set: AP01ActionPublicationCandidateSet | None,
    reason: str,
) -> ACP01CandidateProductionResult:
    telemetry = ACP01CandidateProductionTelemetry(
        decision_count=len(decisions),
        proposal_count=sum(int(item.proposal is not None) for item in decisions),
        proposed_count=sum(int(item.status is ACP01DecisionStatus.PROPOSED) for item in decisions),
        blocked_count=sum(int(item.status is ACP01DecisionStatus.BLOCKED) for item in decisions),
        revalidation_required_count=sum(
            int(item.status is ACP01DecisionStatus.REVALIDATION_REQUIRED) for item in decisions
        ),
        unsafe_basis_count=sum(int(item.status is ACP01DecisionStatus.UNSAFE_BASIS) for item in decisions),
        insufficient_basis_count=sum(int(item.status is ACP01DecisionStatus.INSUFFICIENT_BASIS) for item in decisions),
        no_candidate_count=sum(int(item.status is ACP01DecisionStatus.NO_CANDIDATE) for item in decisions),
        private_eval_excluded=candidate_input.private_eval_excluded,
        scenario_label_excluded=candidate_input.scenario_label_excluded,
    )
    return ACP01CandidateProductionResult(
        tick_ref=candidate_input.tick_ref,
        decisions=decisions,
        proposal_count=telemetry.proposal_count,
        proposed_count=telemetry.proposed_count,
        blocked_count=telemetry.blocked_count,
        revalidation_required_count=telemetry.revalidation_required_count,
        unsafe_basis_count=telemetry.unsafe_basis_count,
        candidate_set_for_ap01=candidate_set,
        telemetry=telemetry,
        scope_marker=ACP01ScopeMarker(
            scope="frontier_hosted_acp01_internal_candidate_production_slice",
            candidate_production_only=True,
            no_publication_authority=True,
            no_execution_authority=True,
            no_world_submission_authority=True,
            no_phase_override_authority=True,
            reason=(
                "acp01 only produces bounded internal candidate proposals for ap01 input and "
                "does not publish or execute world actions"
            ),
        ),
        reason=reason,
    )


def _decision_bearing_sections_from_candidate_input(
    candidate_input: ACP01CandidateProductionInput,
) -> dict[str, object]:
    return {
        "tick_ref": candidate_input.tick_ref,
        "source": candidate_input.source,
        "observation_basis": asdict(candidate_input.observation_basis),
        "internal_drive_bases": tuple(asdict(item) for item in candidate_input.internal_drive_bases),
        "visible_object_bases": tuple(asdict(item) for item in candidate_input.visible_object_bases),
        "action_surface_bases": tuple(asdict(item) for item in candidate_input.action_surface_bases),
        "capability_bases": tuple(asdict(item) for item in candidate_input.capability_bases),
        "effect_feedback_bases": tuple(asdict(item) for item in candidate_input.effect_feedback_bases),
    }


def _decision_bearing_sections_from_proposal(
    proposal: ACP01ActionCandidateProposal,
) -> dict[str, object]:
    return {
        "candidate_id": proposal.candidate_id,
        "action_kind": proposal.action_kind,
        "target_ref": proposal.target_ref,
        "args": proposal.args,
        "intended_effect": proposal.intended_effect,
        "basis_refs": proposal.basis_refs,
        "missing_basis": proposal.missing_basis,
        "blocked_basis": proposal.blocked_basis,
    }


def _unsafe_proposal_reasons(
    proposal: ACP01ActionCandidateProposal,
) -> list[str]:
    sections = _decision_bearing_sections_from_proposal(proposal)
    return list(dict.fromkeys(_scan_decision_sections_for_forbidden_markers(sections, path_prefix="acp01_proposal")))


def _unsafe_candidate_set_reasons(
    candidate_set: AP01ActionPublicationCandidateSet,
) -> list[str]:
    candidates = []
    for candidate in candidate_set.candidates:
        candidates.append(
            {
                "candidate_id": candidate.candidate_id,
                "action_kind": candidate.action_kind,
                "target_ref": candidate.target_ref,
                "args": candidate.args,
                "intended_effect": candidate.intended_effect,
                "source_tick_ref": candidate.source_tick_ref,
                "source_cycle_ref": candidate.source_cycle_ref,
                "source_phase_refs": candidate.source_phase_refs,
                "permission_refs": candidate.permission_refs,
                "evidence_refs": candidate.evidence_refs,
                "affordance_binding_refs": candidate.affordance_binding_refs,
                "forbidden_basis_markers": candidate.forbidden_basis_markers,
            }
        )
    sections: dict[str, object] = {
        "candidate_set_id": candidate_set.candidate_set_id,
        "source_lineage": candidate_set.source_lineage,
        "reason": candidate_set.reason,
        "candidates": tuple(candidates),
    }
    return list(dict.fromkeys(_scan_decision_sections_for_forbidden_markers(sections, path_prefix="acp01_candidate_set")))


def _scan_decision_sections_for_forbidden_markers(
    value: object,
    *,
    path_prefix: str,
) -> list[str]:
    reasons: list[str] = []
    _scan_value_for_markers(value=value, path=path_prefix, out=reasons)
    return reasons


def _scan_value_for_markers(*, value: object, path: str, out: list[str]) -> None:
    if value is None:
        return
    if is_dataclass(value):
        _scan_value_for_markers(value=asdict(value), path=path, out=out)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            for marker in _FORBIDDEN_TOKENS:
                if marker in key_text:
                    out.append(f"forbidden_basis_marker:{marker}@{path}.{key}")
            _scan_value_for_markers(value=item, path=f"{path}.{key}", out=out)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            _scan_value_for_markers(value=item, path=f"{path}[{index}]", out=out)
        return
    text = str(value).lower()
    for marker in _FORBIDDEN_TOKENS:
        if marker in text:
            out.append(f"forbidden_basis_marker:{marker}@{path}")
