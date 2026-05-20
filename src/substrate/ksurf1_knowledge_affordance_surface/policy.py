from __future__ import annotations

from dataclasses import asdict, replace

from .models import (
    KnowledgeAffordanceFrame,
    KnowledgeAffordanceKind,
    KnowledgeProviderRef,
    KnowledgeSlotState,
    KnowledgeSurfaceCounters,
    KnowledgeSurfaceInput,
    KnowledgeSurfaceValidationResult,
    KnowledgeSurfaceValidationStatus,
    KSurfAuthorityFlags,
    LockedSlotRef,
    MachineStatusHintRef,
    ObjectiveHintRef,
    PartialSlotRef,
    ProviderClaimRef,
    ProviderConflictFrame,
    ProviderKind,
    ScannerCandidateHintRef,
    StationCapabilityHintRef,
    TransformationHintRef,
)

_FORBIDDEN_ORACLE_TOKENS: tuple[str, ...] = (
    "truth_authority",
    "true_recipe",
    "recipe_truth",
    "worldstate",
    "full_map",
    "backend_object_id",
    "hidden_label",
    "eval_label",
    "scenario_label",
    "identity_truth",
    "selected_action",
    "preferred_action",
    "goal_selection",
    "action_permission",
    "value_assignment",
    "mature_recipe",
    "mature_skill",
    "automation",
    "root_cause",
    "definitive_cause",
    "cause_confirmed",
    "true_identity",
    "definitive_identity",
    "identity_confirmed",
    "ab7_ready",
    "ab7_readiness",
    "p15_mature_recipe",
    "p16_value_chain",
)
_VALUE_MARKERS: tuple[str, ...] = (
    "rarity",
    "rare",
    "epic",
    "legendary",
    "valuable",
    "reward_value",
    "value_chain",
    "expected_value",
)
_ACTION_MARKERS: tuple[str, ...] = (
    "selected_action",
    "preferred_action",
    "route_plan",
    "if_then_policy",
    "solution_sequence",
    "factory_steps",
    "ordered_plan",
    "required_action_order",
)
_GOAL_MARKERS: tuple[str, ...] = ("subject_goal", "goal_selection", "must_do")
_CAUSE_MARKERS: tuple[str, ...] = ("root_cause", "definitive_cause", "cause_confirmed")
_IDENTITY_TRUTH_MARKERS: tuple[str, ...] = ("identity_truth", "true_identity", "definitive_identity", "identity_confirmed")
_LIVED_EVIDENCE_MARKERS: tuple[str, ...] = ("observed_truth", "lived_evidence", "proven_by_provider")
_STALE_MARKERS: tuple[str, ...] = ("stale", "cached", "partial", "lossy", "sampled")


def build_knowledge_affordance_frame(
    surface_input: KnowledgeSurfaceInput,
) -> KnowledgeSurfaceValidationResult:
    blocked: list[str] = []
    warnings: list[str] = []
    trace: list[str] = []
    counters = KnowledgeSurfaceCounters(
        provider_count=len(surface_input.provider_refs),
        claim_count=len(surface_input.provider_claim_refs),
        locked_slot_count=len(surface_input.locked_slot_refs),
        partial_slot_count=len(surface_input.partial_slot_refs),
    )
    counts = asdict(counters)

    if not surface_input.frame_id:
        blocked.append("missing_frame_id")

    if _is_noop(surface_input):
        frame = KnowledgeAffordanceFrame(
            frame_id=surface_input.frame_id or "ksurf1:noop",
            provider_refs=(),
            provider_claim_refs=(),
            knowledge_hint_refs=(),
            locked_slot_refs=(),
            partial_slot_refs=(),
            transformation_hint_refs=(),
            station_capability_hint_refs=(),
            objective_hint_refs=(),
            machine_status_hint_refs=(),
            scanner_candidate_hint_refs=(),
            provider_conflict_refs=(),
            source_refs=(),
            uncertainty_refs=(),
            lossiness_refs=(),
            residue_refs=(),
            blocked_provider_reasons=("noop_input",),
            authority_flags=KSurfAuthorityFlags(),
            validation_status=KnowledgeSurfaceValidationStatus.NOOP,
            counters=KnowledgeSurfaceCounters(**counts),
        )
        return KnowledgeSurfaceValidationResult(
            status=KnowledgeSurfaceValidationStatus.NOOP,
            blocked_reasons=("noop_input",),
            warnings=(),
            counters=KnowledgeSurfaceCounters(**counts),
            frame=frame,
            authority_flags=KSurfAuthorityFlags(),
            conformance_trace=("noop",),
        )

    provider_map = {item.provider_id: item for item in surface_input.provider_refs}
    for provider in surface_input.provider_refs:
        issues = validate_knowledge_provider_ref(provider)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        counts["hidden_eval_block_count"] += sum(1 for item in issues if "protected_eval" in item)
        counts["scenario_label_block_count"] += sum(1 for item in issues if "scenario_label" in item)
        counts["oracle_payload_block_count"] += sum(1 for item in issues if "oracle_payload" in item)
        counts["selected_action_block_count"] += sum(1 for item in issues if "selected_action" in item or "action_authority" in item)
        counts["value_assignment_block_count"] += sum(1 for item in issues if "value_assignment" in item)
        counts["mature_recipe_block_count"] += sum(1 for item in issues if "mature_recipe" in item)
        counts["lived_evidence_block_count"] += sum(1 for item in issues if "lived_evidence" in item)
        trace.append(f"provider:{provider.provider_id}:{'ok' if not issues else 'blocked'}")

    for claim in surface_input.provider_claim_refs:
        issues = validate_provider_claim(claim=claim, provider_map=provider_map)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        counts["oracle_payload_block_count"] += sum(1 for item in issues if "oracle_payload" in item)
        counts["selected_action_block_count"] += sum(1 for item in issues if "selected_action" in item)
        counts["value_assignment_block_count"] += sum(1 for item in issues if "value_assignment" in item)
        counts["mature_recipe_block_count"] += sum(1 for item in issues if "mature_recipe" in item)
        counts["lived_evidence_block_count"] += sum(1 for item in issues if "lived_evidence" in item)
        if claim.stale_marker is not None:
            counts["stale_or_lossy_count"] += 1
        trace.append(f"claim:{claim.claim_id}:{'ok' if not issues else 'blocked'}")

    for slot in surface_input.locked_slot_refs:
        issues = validate_locked_slot(slot)
        blocked.extend(issues)
        counts["unlock_without_public_basis_count"] += sum(1 for item in issues if "unlock_without_public_basis" in item)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        trace.append(f"locked_slot:{slot.slot_id}:{'ok' if not issues else 'blocked'}")

    for slot in surface_input.partial_slot_refs:
        issues = validate_partial_slot(slot)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        trace.append(f"partial_slot:{slot.slot_id}:{'ok' if not issues else 'blocked'}")

    for hint in surface_input.transformation_hint_refs:
        issues = validate_transformation_hint(hint)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        counts["mature_recipe_block_count"] += sum(1 for item in issues if "mature" in item)
        trace.append(f"transformation:{hint.hint_id}:{'ok' if not issues else 'blocked'}")

    for hint in surface_input.station_capability_hint_refs:
        issues = validate_station_capability_hint(hint)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        trace.append(f"station_hint:{hint.hint_id}:{'ok' if not issues else 'blocked'}")

    for hint in surface_input.objective_hint_refs:
        issues = validate_objective_hint(hint)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        counts["selected_action_block_count"] += sum(1 for item in issues if "goal_authority" in item)
        trace.append(f"objective_hint:{hint.hint_id}:{'ok' if not issues else 'blocked'}")

    for hint in surface_input.machine_status_hint_refs:
        issues = validate_machine_status_hint(hint)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        counts["oracle_payload_block_count"] += sum(1 for item in issues if "diagnosis_authority" in item or "cause" in item)
        trace.append(f"machine_status:{hint.hint_id}:{'ok' if not issues else 'blocked'}")

    for hint in surface_input.scanner_candidate_hint_refs:
        issues = validate_scanner_candidate_hint(hint)
        blocked.extend(issues)
        counts["missing_source_ref_count"] += sum(1 for item in issues if "missing_source_refs" in item)
        counts["oracle_payload_block_count"] += sum(1 for item in issues if "identity_truth" in item)
        trace.append(f"scanner_hint:{hint.hint_id}:{'ok' if not issues else 'blocked'}")

    conflicts = detect_provider_conflicts(surface_input)
    if conflicts:
        counts["conflict_count"] = len(conflicts)
        counts["provider_conflict_count"] = len(conflicts)
        warnings.extend(f"provider_conflict:{item.conflict_id}" for item in conflicts)
        trace.extend(f"conflict:{item.conflict_id}" for item in conflicts)

    counts["hint_count"] = (
        len(surface_input.transformation_hint_refs)
        + len(surface_input.station_capability_hint_refs)
        + len(surface_input.objective_hint_refs)
        + len(surface_input.machine_status_hint_refs)
        + len(surface_input.scanner_candidate_hint_refs)
    )

    blocked = list(dict.fromkeys(blocked))
    warnings = list(dict.fromkeys(warnings))
    counts["blocked_provider_count"] = len(blocked)
    status = (
        KnowledgeSurfaceValidationStatus.BLOCKED
        if blocked
        else (KnowledgeSurfaceValidationStatus.PARTIAL if warnings else KnowledgeSurfaceValidationStatus.ACCEPTED)
    )

    frame = _build_frame(
        surface_input=surface_input,
        status=status,
        blocked=tuple(blocked),
        counters=KnowledgeSurfaceCounters(**counts),
        conflicts=conflicts,
    )
    return KnowledgeSurfaceValidationResult(
        status=status,
        blocked_reasons=tuple(blocked),
        warnings=tuple(warnings),
        counters=KnowledgeSurfaceCounters(**counts),
        frame=frame,
        authority_flags=KSurfAuthorityFlags(),
        conformance_trace=tuple(trace),
    )


def validate_knowledge_provider_ref(provider_ref: KnowledgeProviderRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not provider_ref.provider_id:
        issues.append("provider:missing_id")
    if not provider_ref.source_refs:
        issues.append(f"provider:{provider_ref.provider_id}:missing_source_refs")
    if not provider_ref.public:
        issues.append(f"provider:{provider_ref.provider_id}:non_public_provider_forbidden")
    if provider_ref.protected_eval:
        issues.append(f"provider:{provider_ref.provider_id}:protected_eval_forbidden")
    if provider_ref.scenario_label:
        issues.append(f"provider:{provider_ref.provider_id}:scenario_label_forbidden")
    if provider_ref.authority_flags.has_violation():
        issues.append(f"provider:{provider_ref.provider_id}:authority_violation")
    issues.extend(reject_provider_truth_oracle(provider_ref.metadata, prefix=f"provider:{provider_ref.provider_id}"))
    issues.extend(reject_provider_action_authority(provider_ref.metadata, prefix=f"provider:{provider_ref.provider_id}"))
    issues.extend(reject_provider_value_assignment(provider_ref.metadata, prefix=f"provider:{provider_ref.provider_id}"))
    issues.extend(reject_provider_lived_evidence_claim(provider_ref.metadata, prefix=f"provider:{provider_ref.provider_id}"))
    issues.extend(reject_hidden_or_scenario_provider_data(provider_ref.metadata, prefix=f"provider:{provider_ref.provider_id}"))
    issues.extend(validate_metadata_bounds(provider_ref.metadata, prefix=f"provider:{provider_ref.provider_id}"))
    if provider_ref.provider_kind is ProviderKind.UNKNOWN_PROVIDER:
        if not provider_ref.uncertainty_refs:
            issues.append(f"provider:{provider_ref.provider_id}:unknown_provider_requires_uncertainty")
        if not provider_ref.lossiness_refs:
            issues.append(f"provider:{provider_ref.provider_id}:unknown_provider_requires_lossiness")
    if provider_ref.lossiness_refs or _contains_any(_flatten_metadata(provider_ref.metadata), _STALE_MARKERS):
        if not provider_ref.uncertainty_refs:
            issues.append(f"provider:{provider_ref.provider_id}:stale_or_lossy_without_uncertainty")
    return tuple(dict.fromkeys(issues))


def validate_provider_claim(claim: ProviderClaimRef, provider_map: dict[str, KnowledgeProviderRef]) -> tuple[str, ...]:
    issues: list[str] = []
    if claim.provider_ref not in provider_map:
        issues.append(f"claim:{claim.claim_id}:unknown_provider_ref")
    if not claim.source_refs:
        issues.append(f"claim:{claim.claim_id}:missing_source_refs")
    if claim.blocked_reason is not None:
        issues.append(f"claim:{claim.claim_id}:preblocked:{claim.blocked_reason}")
    if claim.authority_marker.lower() in {"truth", "oracle", "fact"}:
        issues.append(f"claim:{claim.claim_id}:oracle_payload")
    issues.extend(reject_provider_truth_oracle(claim.metadata, prefix=f"claim:{claim.claim_id}"))
    issues.extend(reject_provider_action_authority(claim.metadata, prefix=f"claim:{claim.claim_id}"))
    issues.extend(reject_provider_value_assignment(claim.metadata, prefix=f"claim:{claim.claim_id}"))
    issues.extend(reject_provider_lived_evidence_claim(claim.metadata, prefix=f"claim:{claim.claim_id}"))
    issues.extend(reject_hidden_or_scenario_provider_data(claim.metadata, prefix=f"claim:{claim.claim_id}"))
    issues.extend(validate_metadata_bounds(claim.metadata, prefix=f"claim:{claim.claim_id}"))
    if claim.claim_text_ref and _contains_any(claim.claim_text_ref.lower(), _GOAL_MARKERS):
        issues.append(f"claim:{claim.claim_id}:goal_authority_forbidden")
    if claim.claim_text_ref and _contains_any(claim.claim_text_ref.lower(), _CAUSE_MARKERS):
        issues.append(f"claim:{claim.claim_id}:cause_confirmation_forbidden")
    return tuple(dict.fromkeys(issues))


def validate_locked_slot(slot: LockedSlotRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not slot.source_refs:
        issues.append(f"locked_slot:{slot.slot_id}:missing_source_refs")
    if slot.slot_state is not KnowledgeSlotState.LOCKED:
        issues.append(f"locked_slot:{slot.slot_id}:slot_state_must_be_locked")
    if slot.unlock_basis_refs and not ensure_unlock_basis(slot.unlock_basis_refs):
        issues.append(f"locked_slot:{slot.slot_id}:unlock_without_public_basis")
    return tuple(dict.fromkeys(issues))


def validate_partial_slot(slot: PartialSlotRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not slot.source_refs:
        issues.append(f"partial_slot:{slot.slot_id}:missing_source_refs")
    if not slot.known_part_refs:
        issues.append(f"partial_slot:{slot.slot_id}:missing_known_part_refs")
    if not slot.unknown_part_refs:
        issues.append(f"partial_slot:{slot.slot_id}:missing_unknown_part_refs")
    if not slot.uncertainty_refs and not slot.lossiness_refs:
        issues.append(f"partial_slot:{slot.slot_id}:partial_requires_uncertainty_or_lossiness")
    return tuple(dict.fromkeys(issues))


def validate_transformation_hint(hint: TransformationHintRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not hint.source_refs:
        issues.append(f"transformation_hint:{hint.hint_id}:missing_source_refs")
    if hint.maturity:
        issues.append(f"transformation_hint:{hint.hint_id}:mature_transformation_forbidden")
    if not hint.input_candidate_refs or not hint.output_candidate_refs:
        issues.append(f"transformation_hint:{hint.hint_id}:missing_input_or_output_candidates")
    return tuple(dict.fromkeys(issues))


def validate_station_capability_hint(hint: StationCapabilityHintRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not hint.source_refs:
        issues.append(f"station_hint:{hint.hint_id}:missing_source_refs")
    if not hint.station_ref:
        issues.append(f"station_hint:{hint.hint_id}:missing_station_ref")
    return tuple(dict.fromkeys(issues))


def validate_objective_hint(hint: ObjectiveHintRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not hint.source_refs:
        issues.append(f"objective_hint:{hint.hint_id}:missing_source_refs")
    if hint.goal_authority:
        issues.append(f"objective_hint:{hint.hint_id}:goal_authority_forbidden")
    if hint.objective_text_ref and _contains_any(hint.objective_text_ref.lower(), _ACTION_MARKERS + _GOAL_MARKERS):
        issues.append(f"objective_hint:{hint.hint_id}:planner_or_goal_payload_forbidden")
    reward_surface = " ".join(item.lower() for item in hint.reward_hint_refs)
    if _contains_any(reward_surface, _VALUE_MARKERS):
        issues.append(f"objective_hint:{hint.hint_id}:reward_value_assignment_forbidden")
    return tuple(dict.fromkeys(issues))


def validate_machine_status_hint(hint: MachineStatusHintRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not hint.source_refs:
        issues.append(f"machine_status_hint:{hint.hint_id}:missing_source_refs")
    if hint.diagnosis_authority:
        issues.append(f"machine_status_hint:{hint.hint_id}:diagnosis_authority_forbidden")
    status_surface = " ".join(item.lower() for item in hint.status_candidate_refs)
    if _contains_any(status_surface, _CAUSE_MARKERS):
        issues.append(f"machine_status_hint:{hint.hint_id}:cause_confirmation_forbidden")
    return tuple(dict.fromkeys(issues))


def validate_scanner_candidate_hint(hint: ScannerCandidateHintRef) -> tuple[str, ...]:
    issues: list[str] = []
    if not hint.source_refs:
        issues.append(f"scanner_hint:{hint.hint_id}:missing_source_refs")
    if hint.identity_truth:
        issues.append(f"scanner_hint:{hint.hint_id}:identity_truth_forbidden")
    identity_surface = " ".join(item.lower() for item in hint.identity_candidate_refs)
    if _contains_any(identity_surface, _IDENTITY_TRUTH_MARKERS):
        issues.append(f"scanner_hint:{hint.hint_id}:identity_truth_payload_forbidden")
    return tuple(dict.fromkeys(issues))


def detect_provider_conflicts(surface_input: KnowledgeSurfaceInput) -> tuple[ProviderConflictFrame, ...]:
    by_target: dict[str, list[ProviderClaimRef]] = {}
    for claim in surface_input.provider_claim_refs:
        key = claim.target_ref or claim.subject_ref
        if key:
            by_target.setdefault(key, []).append(claim)
    out: list[ProviderConflictFrame] = []
    for target, claims in by_target.items():
        if len(claims) < 2:
            continue
        texts = {item.claim_text_ref or "" for item in claims}
        providers = {item.provider_ref for item in claims}
        if len(texts) > 1 or len(providers) > 1:
            out.append(
                ProviderConflictFrame(
                    conflict_id=f"conflict:{target}",
                    provider_refs=tuple(sorted(providers)),
                    conflicting_claim_refs=tuple(item.claim_id for item in claims),
                    conflict_kind="provider_claim_disagreement",
                    affected_slot_refs=tuple(
                        sorted({slot for claim in claims for slot in claim.slot_refs})
                    ),
                    affected_hint_refs=tuple(item.claim_id for item in claims),
                    source_refs=tuple(
                        sorted({src for claim in claims for src in claim.source_refs})
                    ),
                    uncertainty_refs=("uncertain:provider_conflict",),
                    residue_refs=("residue:provider_conflict",),
                    resolution_status="unresolved",
                    chosen_winner=None,
                )
            )
    return tuple(out)


def reject_provider_truth_oracle(metadata: dict[str, str], *, prefix: str) -> tuple[str, ...]:
    out: list[str] = []
    flat = _flatten_metadata(metadata)
    if _contains_any(flat, _FORBIDDEN_ORACLE_TOKENS):
        out.append(f"{prefix}:oracle_payload_forbidden")
    return tuple(out)


def reject_provider_action_authority(metadata: dict[str, str], *, prefix: str) -> tuple[str, ...]:
    if _contains_any(_flatten_metadata(metadata), _ACTION_MARKERS):
        return (f"{prefix}:selected_action_or_policy_forbidden",)
    return ()


def reject_provider_value_assignment(metadata: dict[str, str], *, prefix: str) -> tuple[str, ...]:
    if _contains_any(_flatten_metadata(metadata), _VALUE_MARKERS):
        return (f"{prefix}:value_assignment_forbidden",)
    return ()


def reject_provider_lived_evidence_claim(metadata: dict[str, str], *, prefix: str) -> tuple[str, ...]:
    if _contains_any(_flatten_metadata(metadata), _LIVED_EVIDENCE_MARKERS):
        return (f"{prefix}:lived_evidence_claim_forbidden",)
    return ()


def reject_hidden_or_scenario_provider_data(metadata: dict[str, str], *, prefix: str) -> tuple[str, ...]:
    lower = _flatten_metadata(metadata)
    out: list[str] = []
    if "eval" in lower or "hidden" in lower or "protected" in lower:
        out.append(f"{prefix}:protected_eval_hidden_payload_forbidden")
    if "scenario" in lower:
        out.append(f"{prefix}:scenario_label_payload_forbidden")
    return tuple(out)


def ensure_source_refs(source_refs: tuple[str, ...]) -> bool:
    return bool(source_refs)


def ensure_unlock_basis(unlock_basis_refs: tuple[str, ...]) -> bool:
    allowed_prefixes = (
        "public_discovery:",
        "public_contact:",
        "public_inspection:",
        "public_scan:",
        "public_quest_state_change:",
        "public_machine_status:",
    )
    return any(item.lower().startswith(allowed_prefixes) for item in unlock_basis_refs)


def ensure_lossiness_for_stale_or_partial(
    *,
    stale_marker: str | None,
    lossiness_refs: tuple[str, ...],
    uncertainty_refs: tuple[str, ...],
) -> bool:
    if stale_marker is None:
        return True
    return bool(lossiness_refs and uncertainty_refs)


def summarize_knowledge_surface_conformance(
    result: KnowledgeSurfaceValidationResult,
) -> dict[str, object]:
    frame = result.frame
    return {
        "status": result.status.value,
        "blocked_reasons": result.blocked_reasons,
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "has_frame": frame is not None,
        "authority_flags": asdict(result.authority_flags),
        "action_request_emitted": frame.action_request_emitted if frame else False,
        "action_selected": frame.action_selected if frame else False,
        "goal_selected": frame.goal_selected if frame else False,
        "fact_claimed": frame.fact_claimed if frame else False,
        "cause_confirmed": frame.cause_confirmed if frame else False,
        "value_assigned": frame.value_assigned if frame else False,
        "mature_recipe_claimed": frame.mature_recipe_claimed if frame else False,
        "mature_skill_claimed": frame.mature_skill_claimed if frame else False,
        "automation_claimed": frame.automation_claimed if frame else False,
    }


def _build_frame(
    *,
    surface_input: KnowledgeSurfaceInput,
    status: KnowledgeSurfaceValidationStatus,
    blocked: tuple[str, ...],
    counters: KnowledgeSurfaceCounters,
    conflicts: tuple[ProviderConflictFrame, ...],
) -> KnowledgeAffordanceFrame:
    provider_ids = tuple(item.provider_id for item in surface_input.provider_refs)
    claim_ids = tuple(item.claim_id for item in surface_input.provider_claim_refs)
    transformation_ids = tuple(item.hint_id for item in surface_input.transformation_hint_refs)
    station_ids = tuple(item.hint_id for item in surface_input.station_capability_hint_refs)
    objective_ids = tuple(item.hint_id for item in surface_input.objective_hint_refs)
    machine_ids = tuple(item.hint_id for item in surface_input.machine_status_hint_refs)
    scanner_ids = tuple(item.hint_id for item in surface_input.scanner_candidate_hint_refs)
    locked_ids = tuple(item.slot_id for item in surface_input.locked_slot_refs)
    partial_ids = tuple(item.slot_id for item in surface_input.partial_slot_refs)
    conflict_ids = tuple(item.conflict_id for item in conflicts)
    source_refs = tuple(
        dict.fromkeys(
            (
                *(src for provider in surface_input.provider_refs for src in provider.source_refs),
                *(src for claim in surface_input.provider_claim_refs for src in claim.source_refs),
                *(src for item in surface_input.locked_slot_refs for src in item.source_refs),
                *(src for item in surface_input.partial_slot_refs for src in item.source_refs),
                *(src for item in surface_input.transformation_hint_refs for src in item.source_refs),
                *(src for item in surface_input.station_capability_hint_refs for src in item.source_refs),
                *(src for item in surface_input.objective_hint_refs for src in item.source_refs),
                *(src for item in surface_input.machine_status_hint_refs for src in item.source_refs),
                *(src for item in surface_input.scanner_candidate_hint_refs for src in item.source_refs),
            )
        )
    )
    uncertainty_refs = tuple(
        dict.fromkeys(
            (
                *(ref for provider in surface_input.provider_refs for ref in provider.uncertainty_refs),
                *(ref for claim in surface_input.provider_claim_refs for ref in claim.uncertainty_refs),
                *(ref for slot in surface_input.locked_slot_refs for ref in slot.uncertainty_refs),
                *(ref for slot in surface_input.partial_slot_refs for ref in slot.uncertainty_refs),
                *(ref for hint in surface_input.transformation_hint_refs for ref in hint.uncertainty_refs),
                *(ref for hint in surface_input.station_capability_hint_refs for ref in hint.uncertainty_refs),
                *(ref for hint in surface_input.objective_hint_refs for ref in hint.uncertainty_refs),
                *(ref for hint in surface_input.machine_status_hint_refs for ref in hint.uncertainty_refs),
                *(ref for hint in surface_input.scanner_candidate_hint_refs for ref in hint.uncertainty_refs),
                *(ref for conflict in conflicts for ref in conflict.uncertainty_refs),
            )
        )
    )
    lossiness_refs = tuple(
        dict.fromkeys(
            (
                *(ref for provider in surface_input.provider_refs for ref in provider.lossiness_refs),
                *(ref for claim in surface_input.provider_claim_refs for ref in claim.lossiness_refs),
                *(ref for slot in surface_input.locked_slot_refs for ref in slot.lossiness_refs),
                *(ref for slot in surface_input.partial_slot_refs for ref in slot.lossiness_refs),
                *(ref for hint in surface_input.transformation_hint_refs for ref in hint.lossiness_refs),
                *(ref for hint in surface_input.station_capability_hint_refs for ref in hint.lossiness_refs),
                *(ref for hint in surface_input.objective_hint_refs for ref in hint.lossiness_refs),
                *(ref for hint in surface_input.machine_status_hint_refs for ref in hint.lossiness_refs),
                *(ref for hint in surface_input.scanner_candidate_hint_refs for ref in hint.lossiness_refs),
            )
        )
    )
    knowledge_hint_refs = tuple(
        dict.fromkeys(
            (
                *transformation_ids,
                *station_ids,
                *objective_ids,
                *machine_ids,
                *scanner_ids,
                *claim_ids,
            )
        )
    )
    return KnowledgeAffordanceFrame(
        frame_id=surface_input.frame_id,
        provider_refs=provider_ids,
        provider_claim_refs=claim_ids,
        knowledge_hint_refs=knowledge_hint_refs,
        locked_slot_refs=locked_ids,
        partial_slot_refs=partial_ids,
        transformation_hint_refs=transformation_ids,
        station_capability_hint_refs=station_ids,
        objective_hint_refs=objective_ids,
        machine_status_hint_refs=machine_ids,
        scanner_candidate_hint_refs=scanner_ids,
        provider_conflict_refs=conflict_ids,
        source_refs=source_refs,
        uncertainty_refs=uncertainty_refs,
        lossiness_refs=lossiness_refs,
        residue_refs=tuple(dict.fromkeys((*surface_input.residue_refs, *(item for c in conflicts for item in c.residue_refs)))),
        blocked_provider_reasons=blocked,
        authority_flags=KSurfAuthorityFlags(),
        validation_status=status,
        counters=counters,
        action_request_emitted=False,
        action_selected=False,
        goal_selected=False,
        fact_claimed=False,
        cause_confirmed=False,
        value_assigned=False,
        mature_recipe_claimed=False,
        mature_skill_claimed=False,
        automation_claimed=False,
    )


def _flatten_metadata(metadata: dict[str, str]) -> str:
    return " ".join(f"{k}:{v}" for k, v in metadata.items()).lower()


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(item in haystack for item in needles)


def validate_metadata_bounds(metadata: dict[str, str], *, prefix: str) -> tuple[str, ...]:
    issues: list[str] = []
    if len(metadata) > 32:
        issues.append(f"{prefix}:metadata_item_limit_exceeded")
    for key, value in metadata.items():
        key_s = str(key)
        value_s = str(value)
        if len(key_s) > 128:
            issues.append(f"{prefix}:metadata_key_oversized")
        if len(value_s) > 512:
            issues.append(f"{prefix}:metadata_value_oversized")
    return tuple(dict.fromkeys(issues))


def _is_noop(surface_input: KnowledgeSurfaceInput) -> bool:
    return not (
        surface_input.provider_refs
        or surface_input.provider_claim_refs
        or surface_input.locked_slot_refs
        or surface_input.partial_slot_refs
        or surface_input.transformation_hint_refs
        or surface_input.station_capability_hint_refs
        or surface_input.objective_hint_refs
        or surface_input.machine_status_hint_refs
        or surface_input.scanner_candidate_hint_refs
    )
