from __future__ import annotations

from dataclasses import asdict, replace

from .models import (
    ActionSurfaceDeclaration,
    BlockedContactReason,
    ContactAuthorityFlags,
    ContactBuildInput,
    ContactConformanceCounters,
    ContactConformanceResult,
    ContactRef,
    PhenomenalContactFrame,
    SourceRef,
    ValidationStatus,
    WorldContactFrame,
    WorldEffectFrame,
)

_FORBIDDEN_MARKER_HINTS = (
    ("worldstate", BlockedContactReason.WORLDSTATE_DETECTED),
    ("world_state", BlockedContactReason.WORLDSTATE_DETECTED),
    ("backend_truth", BlockedContactReason.BACKEND_TRUTH_DETECTED),
    ("true_recipe", BlockedContactReason.TRUE_RECIPE_DETECTED),
    ("full_map", BlockedContactReason.FULL_MAP_DETECTED),
    ("hidden_identity", BlockedContactReason.HIDDEN_IDENTITY_DETECTED),
)
_FORBIDDEN_METADATA_HINTS = (
    ("worldstate", BlockedContactReason.WORLDSTATE_DETECTED),
    ("world_state", BlockedContactReason.WORLDSTATE_DETECTED),
    ("backend_truth", BlockedContactReason.BACKEND_TRUTH_DETECTED),
    ("true_recipe", BlockedContactReason.TRUE_RECIPE_DETECTED),
    ("full_map", BlockedContactReason.FULL_MAP_DETECTED),
    ("hidden_identity", BlockedContactReason.HIDDEN_IDENTITY_DETECTED),
    ("backend_object_id", BlockedContactReason.HIDDEN_IDENTITY_DETECTED),
    ("selected_action", BlockedContactReason.ACTION_POLICY_DETECTED),
    ("preferred_action", BlockedContactReason.ACTION_POLICY_DETECTED),
    ("route_plan", BlockedContactReason.ACTION_POLICY_DETECTED),
    ("if_hungry_then", BlockedContactReason.ACTION_POLICY_DETECTED),
    ("ap01", BlockedContactReason.ACTION_POLICY_DETECTED),
    ("eval_label", BlockedContactReason.PROTECTED_EVAL_ONLY),
    ("scenario_label", BlockedContactReason.SCENARIO_LABEL_ONLY),
)


def build_phenomenal_contact_frame(candidate_input: ContactBuildInput) -> ContactConformanceResult:
    if candidate_input.disabled:
        candidate_input = replace(
            candidate_input,
            public_observation_refs=(),
            public_effect_refs=(),
            passive_event_refs=(),
            action_surfaces=(),
            effect_frames=(),
            residue_refs=(),
            uncertainty_refs=(),
            conflict_refs=(),
            contact_refs=(),
        )

    blocked_reasons: list[BlockedContactReason] = []
    blocked_refs: list[str] = []
    accepted_refs: list[str] = []

    source_ids = tuple(item.source_id for item in candidate_input.source_refs)
    has_public_basis = _has_public_basis(candidate_input)
    has_public_non_scenario_source = any(item.public and not item.scenario_label for item in candidate_input.source_refs)
    all_sources_scenario = bool(candidate_input.source_refs) and all(item.scenario_label for item in candidate_input.source_refs)
    all_sources_protected = bool(candidate_input.source_refs) and all(item.protected_eval for item in candidate_input.source_refs)
    any_source_scenario = any(item.scenario_label for item in candidate_input.source_refs)
    any_source_protected = any(item.protected_eval for item in candidate_input.source_refs)

    counters = ContactConformanceCounters()
    counters_dict = asdict(counters)

    if has_public_basis and not candidate_input.source_refs:
        blocked_reasons.append(BlockedContactReason.MISSING_SOURCE_REFS)
        counters_dict["missing_source_ref_count"] += 1
        blocked_refs.extend(
            (
                *candidate_input.public_observation_refs,
                *candidate_input.public_effect_refs,
                *candidate_input.passive_event_refs,
            )
        )

    if has_public_basis and not any(item.public for item in candidate_input.source_refs):
        blocked_reasons.append(BlockedContactReason.MISSING_SOURCE_REFS)
        counters_dict["missing_source_ref_count"] += 1

    if reject_hidden_eval_payload(candidate_input, all_sources_protected):
        blocked_reasons.append(BlockedContactReason.PROTECTED_EVAL_ONLY)
        counters_dict["hidden_eval_block_count"] += 1
    elif has_public_basis and any_source_protected:
        blocked_reasons.append(BlockedContactReason.PROTECTED_EVAL_ONLY)
        counters_dict["hidden_eval_block_count"] += 1

    if reject_scenario_label_basis(candidate_input, all_sources_scenario, has_public_non_scenario_source):
        blocked_reasons.append(BlockedContactReason.SCENARIO_LABEL_ONLY)
        counters_dict["scenario_label_block_count"] += 1
    elif has_public_basis and any_source_scenario:
        blocked_reasons.append(BlockedContactReason.SCENARIO_LABEL_ONLY)
        counters_dict["scenario_label_block_count"] += 1

    if reject_backend_truth_payload(candidate_input):
        blocked_reasons.append(BlockedContactReason.BACKEND_TRUTH_DETECTED)
        counters_dict["backend_truth_block_count"] += 1

    if candidate_input.worldstate_payload_present:
        blocked_reasons.append(BlockedContactReason.WORLDSTATE_DETECTED)
        counters_dict["worldstate_block_count"] += 1

    if candidate_input.true_recipe_present:
        blocked_reasons.append(BlockedContactReason.TRUE_RECIPE_DETECTED)
        counters_dict["true_recipe_block_count"] += 1

    if candidate_input.full_map_present:
        blocked_reasons.append(BlockedContactReason.FULL_MAP_DETECTED)
        counters_dict["full_map_block_count"] += 1

    if candidate_input.hidden_identity_present:
        blocked_reasons.append(BlockedContactReason.HIDDEN_IDENTITY_DETECTED)

    if candidate_input.backend_specific_fields:
        blocked_reasons.append(BlockedContactReason.UNSUPPORTED_BACKEND_SPECIFIC_FIELD)
        blocked_refs.extend(candidate_input.backend_specific_fields)

    if ensure_lossiness_when_required(candidate_input):
        blocked_reasons.append(BlockedContactReason.LOSSINESS_REQUIRED_BUT_MISSING)
        counters_dict["lossiness_missing_count"] += 1

    marker_block = _blocked_reason_from_marker_refs(candidate_input)
    if marker_block is not None:
        blocked_reasons.append(marker_block)

    for item in candidate_input.contact_refs:
        ref_ok, ref_reason = _validate_public_ref_detail(item)
        if ref_ok:
            accepted_refs.append(item.ref_id)
        else:
            blocked_refs.append(item.ref_id)
            if ref_reason is not None:
                blocked_reasons.append(ref_reason)

    action_surface_refs: list[str] = []
    for surface in candidate_input.action_surfaces:
        action_surface_refs.append(surface.surface_ref)
        ok, reason = validate_action_surface(surface)
        if ok:
            accepted_refs.append(surface.surface_ref)
            continue
        blocked_refs.append(surface.surface_ref)
        blocked_reasons.append(reason)
        if reason is BlockedContactReason.ACTION_POLICY_DETECTED:
            counters_dict["action_policy_block_count"] += 1

    effect_surface_refs: list[str] = []
    for effect_frame in candidate_input.effect_frames:
        effect_surface_refs.append(effect_frame.effect_ref)
        ok, reason = validate_world_effect_frame(effect_frame)
        if ok:
            accepted_refs.append(effect_frame.effect_ref)
            continue
        blocked_refs.append(effect_frame.effect_ref)
        blocked_reasons.append(reason)
        if reason is BlockedContactReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER:
            counters_dict["effect_without_request_or_passive_count"] += 1

    authority_violations = _count_authority_violations(
        action_surfaces=candidate_input.action_surfaces,
        effect_frames=candidate_input.effect_frames,
    )
    counters_dict["authority_violation_count"] = authority_violations

    if has_public_basis:
        accepted_refs.extend(candidate_input.public_observation_refs)
        accepted_refs.extend(candidate_input.public_effect_refs)
        accepted_refs.extend(candidate_input.passive_event_refs)
        accepted_refs.extend(candidate_input.residue_refs)
        accepted_refs.extend(candidate_input.uncertainty_refs)
        accepted_refs.extend(candidate_input.conflict_refs)

    accepted_refs = list(dict.fromkeys(accepted_refs))
    blocked_refs = list(dict.fromkeys(blocked_refs))
    blocked_reasons = list(dict.fromkeys(blocked_reasons))

    status = _validation_status(
        has_public_basis=has_public_basis,
        blocked_reasons=tuple(blocked_reasons),
        blocked_refs=tuple(blocked_refs),
        uncertainty_refs=candidate_input.uncertainty_refs,
        conflict_refs=candidate_input.conflict_refs,
        lossiness_refs=tuple(item.marker_id for item in candidate_input.lossiness_markers),
    )

    if status is ValidationStatus.BLOCKED:
        accepted_refs = []
    if status is ValidationStatus.NOOP:
        blocked_reasons = [BlockedContactReason.EMPTY_CONTACT]
        blocked_refs = []
        accepted_refs = []

    counters_dict["accepted_ref_count"] = len(accepted_refs)
    counters_dict["blocked_ref_count"] = len(blocked_refs)
    counters = ContactConformanceCounters(**counters_dict)

    authority_flags = ContactAuthorityFlags()
    backend_truth_excluded = not (
        candidate_input.backend_truth_present
        or candidate_input.worldstate_payload_present
        or candidate_input.true_recipe_present
        or candidate_input.full_map_present
        or candidate_input.hidden_identity_present
    )
    uncertainty_marker_ids = tuple(item.marker_id for item in candidate_input.uncertainty_markers)
    lossiness_marker_ids = tuple(item.marker_id for item in candidate_input.lossiness_markers)

    world_frame = WorldContactFrame(
        frame_id=f"{candidate_input.frame_id}:world",
        tick_id=candidate_input.tick_id,
        provider_refs=candidate_input.provider_refs,
        public_observation_refs=tuple(candidate_input.public_observation_refs),
        public_effect_refs=tuple(candidate_input.public_effect_refs),
        passive_event_refs=tuple(candidate_input.passive_event_refs),
        action_surface_refs=tuple(action_surface_refs),
        effect_surface_refs=tuple(effect_surface_refs),
        residue_refs=tuple(candidate_input.residue_refs),
        uncertainty_refs=tuple(dict.fromkeys((*candidate_input.uncertainty_refs, *uncertainty_marker_ids))),
        conflict_refs=tuple(candidate_input.conflict_refs),
        source_refs=source_ids,
        lossiness_refs=lossiness_marker_ids,
        blocked_contact_reasons=tuple(blocked_reasons),
        authority_flags=authority_flags,
        hidden_eval_used=False,
        scenario_label_used=False,
        backend_truth_excluded=backend_truth_excluded,
        validation_status=status,
        action_request_emitted=False,
        world_submission_emitted=False,
        fact_claimed=False,
        cause_confirmed=False,
        mature_recipe_claimed=False,
        automation_claimed=False,
        value_assigned=False,
    )
    phenomenal_frame = PhenomenalContactFrame(
        frame_id=f"{candidate_input.frame_id}:phenomenal",
        tick_id=candidate_input.tick_id,
        provider_refs=candidate_input.provider_refs,
        public_observation_refs=world_frame.public_observation_refs,
        public_effect_refs=world_frame.public_effect_refs,
        passive_event_refs=world_frame.passive_event_refs,
        action_surface_refs=world_frame.action_surface_refs,
        effect_surface_refs=world_frame.effect_surface_refs,
        residue_refs=world_frame.residue_refs,
        uncertainty_refs=world_frame.uncertainty_refs,
        conflict_refs=world_frame.conflict_refs,
        source_refs=world_frame.source_refs,
        lossiness_refs=world_frame.lossiness_refs,
        blocked_contact_reasons=world_frame.blocked_contact_reasons,
        authority_flags=world_frame.authority_flags,
        hidden_eval_used=False,
        scenario_label_used=False,
        backend_truth_excluded=backend_truth_excluded,
        validation_status=status,
        action_request_emitted=False,
        world_submission_emitted=False,
        fact_claimed=False,
        cause_confirmed=False,
        mature_recipe_claimed=False,
        automation_claimed=False,
        value_assigned=False,
    )
    return ContactConformanceResult(
        phenomenal_contact_frame=phenomenal_frame,
        world_contact_frame=world_frame,
        counters=counters,
        blocked_reasons=tuple(blocked_reasons),
        accepted_refs=tuple(accepted_refs),
        blocked_refs=tuple(blocked_refs),
    )


def validate_contact_frame(frame: PhenomenalContactFrame | WorldContactFrame) -> bool:
    if frame.hidden_eval_used or frame.scenario_label_used:
        return False
    if frame.action_request_emitted or frame.world_submission_emitted:
        return False
    if frame.fact_claimed or frame.cause_confirmed:
        return False
    if frame.mature_recipe_claimed or frame.automation_claimed:
        return False
    if frame.value_assigned:
        return False
    return not frame.authority_flags.has_violation()


def validate_public_ref(contact_ref: ContactRef) -> bool:
    ok, _reason = _validate_public_ref_detail(contact_ref)
    return ok


def _validate_public_ref_detail(contact_ref: ContactRef) -> tuple[bool, BlockedContactReason | None]:
    if not contact_ref.source_refs:
        return False, BlockedContactReason.MISSING_SOURCE_REFS
    if contact_ref.blocked_reason is not None:
        return False, contact_ref.blocked_reason
    for forbidden_hint, _reason in _FORBIDDEN_MARKER_HINTS:
        if forbidden_hint in contact_ref.ref_id.lower():
            return False, _reason
    metadata_reason = _detect_forbidden_metadata(contact_ref.metadata)
    if metadata_reason is not None:
        return False, metadata_reason
    return True, None


def validate_action_surface(surface: ActionSurfaceDeclaration) -> tuple[bool, BlockedContactReason]:
    if not surface.source_refs:
        return False, BlockedContactReason.MISSING_SOURCE_REFS
    if surface.authority_flags.has_violation():
        return False, BlockedContactReason.ACTION_POLICY_DETECTED
    if surface.selected_action_ref or surface.action_policy_ref or surface.preferred_route_ref:
        return False, BlockedContactReason.ACTION_POLICY_DETECTED
    lowered = surface.action_kind.lower()
    if "policy" in lowered or "selected" in lowered or "route" in lowered or "ap01" in lowered:
        return False, BlockedContactReason.ACTION_POLICY_DETECTED
    return True, BlockedContactReason.UNKNOWN


def validate_world_effect_frame(frame: WorldEffectFrame) -> tuple[bool, BlockedContactReason]:
    if not frame.source_refs:
        return False, BlockedContactReason.MISSING_SOURCE_REFS
    if frame.authority_flags.has_violation():
        return False, BlockedContactReason.ACTION_POLICY_DETECTED
    effect_reason = _detect_forbidden_hint_in_refs(
        frame.effect_ref,
        *frame.public_delta_refs,
        *frame.residue_refs,
        *frame.uncertainty_refs,
        *frame.lossiness_refs,
    )
    if effect_reason is not None:
        return False, effect_reason
    if frame.fact_claimed or frame.cause_confirmed:
        return False, BlockedContactReason.UNKNOWN
    if not frame.request_ref and not frame.passive_event_ref:
        return False, BlockedContactReason.EFFECT_WITHOUT_REQUEST_OR_PASSIVE_MARKER
    return True, BlockedContactReason.UNKNOWN


def reject_backend_truth_payload(candidate_input: ContactBuildInput) -> bool:
    return bool(candidate_input.backend_truth_present)


def reject_hidden_eval_payload(candidate_input: ContactBuildInput, all_sources_protected: bool) -> bool:
    return bool(candidate_input.protected_eval_present or all_sources_protected)


def reject_scenario_label_basis(
    candidate_input: ContactBuildInput,
    all_sources_scenario: bool,
    has_public_non_scenario_source: bool,
) -> bool:
    if candidate_input.scenario_label_present and not has_public_non_scenario_source:
        return True
    return bool(all_sources_scenario and not has_public_non_scenario_source)


def ensure_source_refs(candidate_input: ContactBuildInput) -> bool:
    return bool(candidate_input.source_refs)


def ensure_lossiness_when_required(candidate_input: ContactBuildInput) -> bool:
    return bool(candidate_input.requires_lossiness_marker and not candidate_input.lossiness_markers)


def summarize_contact_conformance(result: ContactConformanceResult) -> dict[str, object]:
    frame = result.phenomenal_contact_frame
    return {
        "frame_id": frame.frame_id,
        "validation_status": frame.validation_status.value,
        "accepted_ref_count": result.counters.accepted_ref_count,
        "blocked_ref_count": result.counters.blocked_ref_count,
        "blocked_reasons": [item.value for item in result.blocked_reasons],
        "authority_flags": asdict(frame.authority_flags),
        "hidden_eval_used": frame.hidden_eval_used,
        "scenario_label_used": frame.scenario_label_used,
        "backend_truth_excluded": frame.backend_truth_excluded,
        "action_request_emitted": frame.action_request_emitted,
        "world_submission_emitted": frame.world_submission_emitted,
        "fact_claimed": frame.fact_claimed,
        "cause_confirmed": frame.cause_confirmed,
        "mature_recipe_claimed": frame.mature_recipe_claimed,
        "automation_claimed": frame.automation_claimed,
        "value_assigned": frame.value_assigned,
    }


def _has_public_basis(candidate_input: ContactBuildInput) -> bool:
    return bool(
        candidate_input.public_observation_refs
        or candidate_input.public_effect_refs
        or candidate_input.passive_event_refs
        or candidate_input.action_surfaces
        or candidate_input.effect_frames
        or candidate_input.residue_refs
        or candidate_input.uncertainty_refs
        or candidate_input.conflict_refs
        or candidate_input.contact_refs
    )


def _validation_status(
    *,
    has_public_basis: bool,
    blocked_reasons: tuple[BlockedContactReason, ...],
    blocked_refs: tuple[str, ...],
    uncertainty_refs: tuple[str, ...],
    conflict_refs: tuple[str, ...],
    lossiness_refs: tuple[str, ...],
) -> ValidationStatus:
    if not has_public_basis:
        return ValidationStatus.NOOP
    if blocked_reasons or blocked_refs:
        return ValidationStatus.BLOCKED
    if uncertainty_refs or conflict_refs or lossiness_refs:
        return ValidationStatus.PARTIAL
    return ValidationStatus.ACCEPTED


def _blocked_reason_from_marker_refs(candidate_input: ContactBuildInput) -> BlockedContactReason | None:
    refs = (
        *candidate_input.public_observation_refs,
        *candidate_input.public_effect_refs,
        *candidate_input.passive_event_refs,
        *candidate_input.residue_refs,
        *candidate_input.uncertainty_refs,
        *candidate_input.conflict_refs,
    )
    lowered = tuple(str(item).lower() for item in refs)
    if any("worldstate" in item or "world_state" in item for item in lowered):
        return BlockedContactReason.WORLDSTATE_DETECTED
    if any("true_recipe" in item for item in lowered):
        return BlockedContactReason.TRUE_RECIPE_DETECTED
    if any("full_map" in item for item in lowered):
        return BlockedContactReason.FULL_MAP_DETECTED
    if any("hidden_identity" in item for item in lowered):
        return BlockedContactReason.HIDDEN_IDENTITY_DETECTED
    return None


def _count_authority_violations(
    *,
    action_surfaces: tuple[ActionSurfaceDeclaration, ...],
    effect_frames: tuple[WorldEffectFrame, ...],
) -> int:
    violations = 0
    for item in action_surfaces:
        if item.authority_flags.has_violation():
            violations += 1
    for item in effect_frames:
        if item.authority_flags.has_violation():
            violations += 1
        if item.action_request_emitted or item.world_submission_emitted:
            violations += 1
        if item.fact_claimed or item.cause_confirmed:
            violations += 1
    return violations


def _detect_forbidden_metadata(metadata: dict[str, str]) -> BlockedContactReason | None:
    for raw_key, raw_value in metadata.items():
        if not isinstance(raw_key, str):
            return BlockedContactReason.UNSUPPORTED_BACKEND_SPECIFIC_FIELD
        if not isinstance(raw_value, str):
            return BlockedContactReason.UNSUPPORTED_BACKEND_SPECIFIC_FIELD
        haystack = f"{raw_key}::{raw_value}".lower()
        for hint, reason in _FORBIDDEN_METADATA_HINTS:
            if hint in haystack:
                return reason
    return None


def _detect_forbidden_hint_in_refs(*values: str) -> BlockedContactReason | None:
    for item in values:
        lowered = str(item).lower()
        for hint, reason in _FORBIDDEN_METADATA_HINTS:
            if hint in lowered:
                return reason
    return None
