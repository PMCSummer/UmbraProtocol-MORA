from __future__ import annotations

from dataclasses import asdict, replace

from substrate.ab_subject_tick_integration import ABLiveTickInput
from substrate.umwelt0_phenomenal_contact import (
    ActionSurfaceDeclaration,
    ContactAuthorityFlags,
    ValidationStatus,
    WorldEffectFrame,
)

from .models import (
    ContactChannelKind,
    ContactProjectionConfig,
    ContactProjectionInput,
    ProjectedABInput,
    ProjectedACP01Basis,
    ProjectedAP01Lineage,
    ProjectedSubjectTickInputs,
    ProjectionCounters,
    ProjectionTrace,
)

_ACTION_POLICY_HINTS: tuple[str, ...] = ("selected", "policy", "route", "command", "ap01")
_TRUTH_ORACLE_HINTS: tuple[str, ...] = (
    "worldstate",
    "world_state",
    "backend_truth",
    "true_recipe",
    "full_map",
    "hidden_identity",
    "hidden_id",
)
_CAPABILITY_HINTS: tuple[str, ...] = ("capability", "affordance")


def project_contact_frame_to_subject_inputs(
    projection_input: ContactProjectionInput,
    config: ContactProjectionConfig | None = None,
) -> ProjectedSubjectTickInputs:
    cfg = config or ContactProjectionConfig()
    contact_result = projection_input.contact_result
    frame = contact_result.phenomenal_contact_frame
    authority_flags = ContactAuthorityFlags()

    blocked_reasons: list[str] = []
    traces: list[ProjectionTrace] = []
    counters = ProjectionCounters(contact_ref_count=len(contact_result.accepted_refs))

    if frame.validation_status in {ValidationStatus.BLOCKED, ValidationStatus.REJECTED}:
        blocked_reasons.append("umwelt0_frame_not_projectable")
        return _blocked_projection(
            projection_input=projection_input,
            blocked_reasons=blocked_reasons,
            counters=replace(counters, blocked_ref_count=len(contact_result.blocked_refs)),
            traces=traces,
            status="blocked",
            authority_flags=authority_flags,
        )

    if frame.validation_status is ValidationStatus.NOOP:
        blocked_reasons.append("umwelt0_noop_contact")
        return _blocked_projection(
            projection_input=projection_input,
            blocked_reasons=blocked_reasons,
            counters=counters,
            traces=traces,
            status="noop",
            authority_flags=authority_flags,
        )

    if projection_input.contact_result.world_contact_frame.hidden_eval_used:
        blocked_reasons.append("hidden_eval_used_by_contact")
        counters = replace(counters, blocked_hidden_eval_count=counters.blocked_hidden_eval_count + 1)
    if projection_input.contact_result.world_contact_frame.scenario_label_used:
        blocked_reasons.append("scenario_label_used_by_contact")
        counters = replace(counters, blocked_scenario_label_count=counters.blocked_scenario_label_count + 1)
    if blocked_reasons:
        return _blocked_projection(
            projection_input=projection_input,
            blocked_reasons=blocked_reasons,
            counters=replace(counters, blocked_ref_count=len(contact_result.blocked_refs)),
            traces=traces,
            status="blocked",
            authority_flags=authority_flags,
        )

    channel_map = _build_channel_map(projection_input, cfg)
    channel_refs = _channel_ref_groups(channel_map)
    counters = replace(counters, unknown_channel_count=sum(1 for ch in channel_map.values() if ch is ContactChannelKind.UNKNOWN_PUBLIC))

    ab_projection = (
        project_contact_frame_to_ab_input(projection_input, cfg, channel_refs)
        if cfg.enable_ab_projection
        else ProjectedABInput(blocked_reasons=("ab_projection_disabled",), channel_refs=channel_refs)
    )
    acp_projection = (
        project_contact_frame_to_acp01_basis(projection_input, cfg, channel_refs)
        if cfg.enable_acp01_projection
        else ProjectedACP01Basis(blocked_reasons=("acp01_projection_disabled",), channel_refs=channel_refs)
    )
    ap_lineage = (
        project_effect_frame_to_ap01_lineage(projection_input, cfg)
        if cfg.enable_ap01_lineage_projection
        else ProjectedAP01Lineage(blocked_reasons=("ap01_lineage_projection_disabled",))
    )

    projected_ab_ref_count = (
        len(ab_projection.public_observation_refs)
        + len(ab_projection.public_effect_refs)
        + len(ab_projection.residue_refs)
        + len(ab_projection.uncertainty_refs)
        + len(ab_projection.conflict_refs)
    )
    projected_acp_basis_count = (
        len(acp_projection.action_surface_basis_refs)
        + len(acp_projection.pressure_basis_refs)
        + len(acp_projection.capability_basis_refs)
        + len(acp_projection.target_context_refs)
        + len(acp_projection.resource_context_refs)
        + len(acp_projection.station_context_refs)
        + len(acp_projection.entity_context_refs)
        + len(acp_projection.map_context_refs)
        + len(acp_projection.knowledge_hint_refs)
        + len(acp_projection.language_hint_refs)
        + len(acp_projection.sensory_candidate_refs)
    )
    projected_ap01_lineage_count = len(ap_lineage.request_refs) + len(ap_lineage.effect_refs) + len(ap_lineage.correlation_refs)

    counters = replace(
        counters,
        projected_ab_ref_count=projected_ab_ref_count,
        projected_acp01_basis_count=projected_acp_basis_count,
        projected_ap01_lineage_count=projected_ap01_lineage_count,
        blocked_ref_count=len(contact_result.blocked_refs),
        blocked_action_policy_count=(
            counters.blocked_action_policy_count
            + sum(
                1
                for item in (*ab_projection.blocked_reasons, *acp_projection.blocked_reasons, *ap_lineage.blocked_reasons)
                if "action_policy" in item
            )
        ),
        blocked_truth_oracle_count=(
            counters.blocked_truth_oracle_count
            + sum(
                1
                for item in (*ab_projection.blocked_reasons, *acp_projection.blocked_reasons, *ap_lineage.blocked_reasons)
                if "truth_oracle" in item
            )
        ),
        bounded_ref_limit_triggered_count=_bounded_ref_limit_trigger_count(
            projection_input=projection_input,
            config=cfg,
            ab_projection=ab_projection,
            acp_projection=acp_projection,
            ap_lineage=ap_lineage,
        ),
    )

    _append_trace(
        traces=traces,
        stage_name="project_ab_input",
        input_refs=contact_result.accepted_refs,
        output_refs=ab_projection.public_basis_refs,
        channel_kind=None,
        decision="projected",
        blocked_reason=None if not ab_projection.blocked_reasons else ",".join(ab_projection.blocked_reasons),
        authority_flags=authority_flags,
    )
    _append_trace(
        traces=traces,
        stage_name="project_acp01_basis",
        input_refs=contact_result.accepted_refs,
        output_refs=acp_projection.public_basis_refs,
        channel_kind=None,
        decision="projected",
        blocked_reason=None if not acp_projection.blocked_reasons else ",".join(acp_projection.blocked_reasons),
        authority_flags=authority_flags,
    )
    _append_trace(
        traces=traces,
        stage_name="project_ap01_lineage",
        input_refs=contact_result.accepted_refs,
        output_refs=ap_lineage.public_basis_refs,
        channel_kind=None,
        decision="projected",
        blocked_reason=None if not ap_lineage.blocked_reasons else ",".join(ap_lineage.blocked_reasons),
        authority_flags=authority_flags,
    )

    blocked_union = tuple(
        dict.fromkeys(
            (
                *blocked_reasons,
                *ab_projection.blocked_reasons,
                *acp_projection.blocked_reasons,
                *ap_lineage.blocked_reasons,
            )
        )
    )
    all_basis = tuple(
        dict.fromkeys(
            (
                *contact_result.accepted_refs,
                *ab_projection.public_basis_refs,
                *acp_projection.public_basis_refs,
                *ap_lineage.public_basis_refs,
            )
        )
    )

    return ProjectedSubjectTickInputs(
        projection_id=projection_input.projection_id,
        source_contact_frame_ref=frame.frame_id,
        projection_status="partial" if blocked_union else "accepted",
        projected_ab_input=ab_projection,
        projected_acp01_basis=acp_projection,
        projected_ap01_lineage=ap_lineage,
        public_basis_refs=all_basis,
        blocked_projection_reasons=blocked_union,
        authority_flags=authority_flags,
        counters=counters,
        traces=tuple(traces),
        hidden_eval_used=False,
        scenario_label_used=False,
        action_request_emitted=False,
        world_submission_emitted=False,
        fact_claimed=False,
        cause_confirmed=False,
        value_assigned=False,
        mature_recipe_claimed=False,
        mature_skill_claimed=False,
        automation_claimed=False,
    )


def project_contact_frame_to_ab_input(
    projection_input: ContactProjectionInput,
    config: ContactProjectionConfig,
    channel_refs: dict[str, tuple[str, ...]] | None = None,
) -> ProjectedABInput:
    frame = projection_input.contact_result.phenomenal_contact_frame
    channel_ref_map = channel_refs or {}
    public_basis_refs = tuple(
        dict.fromkeys(
            (
                *frame.public_observation_refs,
                *frame.public_effect_refs,
                *frame.passive_event_refs,
                *frame.residue_refs,
                *frame.uncertainty_refs,
                *frame.conflict_refs,
            )
        )
    )

    ab_live_input = ABLiveTickInput(
        tick_id=frame.tick_id or projection_input.projection_id,
        public_observation_refs=frame.public_observation_refs,
        public_effect_refs=frame.public_effect_refs,
        residue_refs=frame.residue_refs,
        uncertainty_refs=frame.uncertainty_refs,
        conflict_refs=frame.conflict_refs,
        ap01_request_refs=tuple(dict.fromkeys(tuple(item.request_ref for item in projection_input.world_effect_frames if item.request_ref))),
        action_effect_refs=tuple(
            dict.fromkeys(
                tuple(
                    f"corr:{item.request_ref}->{item.effect_ref}"
                    for item in projection_input.world_effect_frames
                    if item.request_ref
                )
            )
        ),
        prior_frontier_refs=projection_input.prior_frontier_refs,
        prior_ab_state_refs=projection_input.prior_ab_state_refs,
        recipe_candidate_refs=projection_input.recipe_candidate_refs,
        precursor_candidate_refs=projection_input.precursor_candidate_refs,
        value_chain_refs=projection_input.value_chain_refs,
        factory_chain_refs=projection_input.factory_chain_refs,
        protected_eval_present=False,
        scenario_label_present=False,
        p13_credit_refs=projection_input.p13_credit_refs,
        p14_station_affordance_refs=projection_input.p14_station_affordance_refs,
    )

    return ProjectedABInput(
        public_observation_refs=_cap(frame.public_observation_refs, config.max_projected_refs_per_channel),
        public_effect_refs=_cap(frame.public_effect_refs, config.max_projected_refs_per_channel),
        passive_public_event_refs=_cap(frame.passive_event_refs, config.max_projected_refs_per_channel),
        residue_refs=_cap(frame.residue_refs, config.max_projected_refs_per_channel),
        uncertainty_refs=_cap(frame.uncertainty_refs, config.max_projected_refs_per_channel),
        conflict_refs=_cap(frame.conflict_refs, config.max_projected_refs_per_channel),
        ap01_request_refs=_cap(ab_live_input.ap01_request_refs, config.max_projected_refs_per_channel),
        action_effect_refs=_cap(ab_live_input.action_effect_refs, config.max_projected_refs_per_channel),
        public_basis_refs=_cap(public_basis_refs, config.max_projected_refs_per_channel * 4),
        blocked_reasons=(),
        channel_refs=channel_ref_map,
        ab_live_input_candidate=ab_live_input,
    )


def project_contact_frame_to_acp01_basis(
    projection_input: ContactProjectionInput,
    config: ContactProjectionConfig,
    channel_refs: dict[str, tuple[str, ...]] | None = None,
) -> ProjectedACP01Basis:
    frame = projection_input.contact_result.phenomenal_contact_frame
    blocked_reasons: list[str] = []
    action_surface_basis_refs: list[str] = []
    capability_basis_refs: list[str] = []
    target_context_refs: list[str] = []

    valid_surfaces = project_action_surfaces_as_basis(projection_input.action_surface_declarations, config)
    for surface, blocked in valid_surfaces:
        if blocked is not None:
            blocked_reasons.append(blocked)
            continue
        action_surface_basis_refs.append(surface.surface_ref)
        capability_basis_refs.extend(surface.required_capability_refs)
        if surface.target_ref:
            target_context_refs.append(surface.target_ref)

    knowledge_hint_refs = project_knowledge_surfaces_as_hints(channel_refs or {})
    language_hint_refs = project_language_surfaces_as_testimony_hints(channel_refs or {})
    sensory_candidate_refs = project_sensory_candidates_as_public_candidates(channel_refs or {})
    pressure_basis_refs = _extract_explicit_pressure_basis(channel_refs or {})
    station_context_refs = tuple(item for item in frame.public_observation_refs if "station:" in item)
    resource_context_refs = tuple(item for item in frame.public_observation_refs if "resource:" in item)
    entity_context_refs = tuple(item for item in frame.public_observation_refs if "entity:" in item)
    map_context_refs = tuple(item for item in frame.public_observation_refs if "map:" in item or "route:" in item)

    public_basis_refs = tuple(
        dict.fromkeys(
            (
                *action_surface_basis_refs,
                *pressure_basis_refs,
                *capability_basis_refs,
                *target_context_refs,
                *resource_context_refs,
                *station_context_refs,
                *entity_context_refs,
                *map_context_refs,
                *knowledge_hint_refs,
                *language_hint_refs,
                *sensory_candidate_refs,
                *frame.residue_refs,
                *frame.uncertainty_refs,
            )
        )
    )

    return ProjectedACP01Basis(
        action_surface_basis_refs=tuple(action_surface_basis_refs[: config.max_action_surface_basis_items]),
        pressure_basis_refs=_cap(pressure_basis_refs, config.max_projected_refs_per_channel),
        capability_basis_refs=_cap(tuple(dict.fromkeys(capability_basis_refs)), config.max_projected_refs_per_channel),
        target_context_refs=_cap(tuple(dict.fromkeys(target_context_refs)), config.max_projected_refs_per_channel),
        resource_context_refs=_cap(resource_context_refs, config.max_projected_refs_per_channel),
        station_context_refs=_cap(station_context_refs, config.max_projected_refs_per_channel),
        entity_context_refs=_cap(entity_context_refs, config.max_projected_refs_per_channel),
        map_context_refs=_cap(map_context_refs, config.max_projected_refs_per_channel),
        knowledge_hint_refs=_cap(knowledge_hint_refs, config.max_projected_refs_per_channel),
        language_hint_refs=_cap(language_hint_refs, config.max_projected_refs_per_channel),
        sensory_candidate_refs=_cap(sensory_candidate_refs, config.max_projected_refs_per_channel),
        residue_constraint_refs=_cap(frame.residue_refs, config.max_projected_refs_per_channel),
        uncertainty_constraint_refs=_cap(frame.uncertainty_refs, config.max_projected_refs_per_channel),
        public_basis_refs=_cap(public_basis_refs, config.max_projected_refs_per_channel * 6),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        channel_refs=channel_refs or {},
    )


def project_effect_frame_to_ap01_lineage(
    projection_input: ContactProjectionInput,
    config: ContactProjectionConfig,
) -> ProjectedAP01Lineage:
    blocked_reasons: list[str] = []
    request_refs: list[str] = []
    effect_refs: list[str] = []
    source_refs: list[str] = []
    correlation_refs: list[str] = []

    for item in projection_input.world_effect_frames:
        ok, reason = validate_world_effect_frame_for_projection(item, config)
        if not ok:
            blocked_reasons.append(reason or "invalid_effect_frame")
            continue
        effect_refs.append(item.effect_ref)
        source_refs.extend(item.source_refs)
        if item.request_ref:
            request_refs.append(item.request_ref)
            correlation_refs.append(f"corr:{item.request_ref}->{item.effect_ref}")
        elif item.passive_event_ref:
            correlation_refs.append(f"passive:{item.passive_event_ref}->{item.effect_ref}")

    public_basis_refs = tuple(dict.fromkeys((*request_refs, *effect_refs, *source_refs, *correlation_refs)))
    return ProjectedAP01Lineage(
        request_refs=_cap(tuple(dict.fromkeys(request_refs)), config.max_projected_refs_per_channel),
        effect_refs=_cap(tuple(dict.fromkeys(effect_refs)), config.max_projected_refs_per_channel),
        source_refs=_cap(tuple(dict.fromkeys(source_refs)), config.max_projected_refs_per_channel),
        public_basis_refs=_cap(public_basis_refs, config.max_projected_refs_per_channel * 3),
        correlation_refs=_cap(tuple(dict.fromkeys(correlation_refs)), config.max_projected_refs_per_channel),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
    )


def classify_contact_channel(
    ref_id: str,
    projection_input: ContactProjectionInput,
) -> ContactChannelKind:
    if ref_id in projection_input.channel_overrides:
        return projection_input.channel_overrides[ref_id]

    lowered = ref_id.lower()
    if _contains_any(lowered, ("knowledge", "jei", "encyclopedia", "questbook", "manual", "scanner", "tooltip", "machine_ui", "status_panel")):
        return ContactChannelKind.KNOWLEDGE_AFFORDANCE
    if _contains_any(lowered, ("utterance", "speech", "claim", "directive", "question", "language")):
        return ContactChannelKind.LANGUAGE_CONTACT
    if _contains_any(lowered, ("sensory", "visual", "audio", "touch", "smell", "percept")):
        return ContactChannelKind.SENSORY_CANDIDATE
    if _contains_any(lowered, ("pressure", "viability", "body", "damage", "blocked_movement")):
        return ContactChannelKind.BODY_INTERNAL
    if _contains_any(lowered, ("other_actor", "social", "demonstration", "warning", "proposal")):
        return ContactChannelKind.SOCIAL_EXTERNAL_ACTOR
    if _contains_any(lowered, ("system", "backend_status", "connection_status", "machine_status")):
        return ContactChannelKind.SYSTEM_STATUS
    if _contains_any(lowered, ("resource:", "station:", "entity:", "map:", "route:", "symbolic_world", "inventory")):
        return ContactChannelKind.SYMBOLIC_WORLD
    return ContactChannelKind.UNKNOWN_PUBLIC


def project_action_surfaces_as_basis(
    action_surfaces: tuple[ActionSurfaceDeclaration, ...],
    config: ContactProjectionConfig,
) -> tuple[tuple[ActionSurfaceDeclaration, str | None], ...]:
    rows: list[tuple[ActionSurfaceDeclaration, str | None]] = []
    for item in action_surfaces:
        if not item.source_refs:
            rows.append((item, "missing_source_for_action_surface"))
            continue
        if item.selected_action_ref or item.action_policy_ref or item.preferred_route_ref:
            rows.append((item, "action_policy_surface_rejected"))
            continue
        lowered = item.action_kind.lower()
        if config.reject_action_policy and _contains_any(lowered, _ACTION_POLICY_HINTS):
            rows.append((item, "action_policy_surface_rejected"))
            continue
        if item.authority_flags.has_violation():
            rows.append((item, "action_surface_authority_violation"))
            continue
        rows.append((item, None))
    return tuple(rows)


def project_knowledge_surfaces_as_hints(channel_refs: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    return channel_refs.get(ContactChannelKind.KNOWLEDGE_AFFORDANCE.value, ())


def project_language_surfaces_as_testimony_hints(channel_refs: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    return channel_refs.get(ContactChannelKind.LANGUAGE_CONTACT.value, ())


def project_sensory_candidates_as_public_candidates(channel_refs: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    return channel_refs.get(ContactChannelKind.SENSORY_CANDIDATE.value, ())


def validate_projection_authority(result: ProjectedSubjectTickInputs) -> bool:
    if result.authority_flags.has_violation():
        return False
    if result.action_request_emitted or result.world_submission_emitted:
        return False
    if result.fact_claimed or result.cause_confirmed:
        return False
    if result.value_assigned or result.mature_recipe_claimed or result.mature_skill_claimed or result.automation_claimed:
        return False
    return not result.hidden_eval_used and not result.scenario_label_used


def summarize_projection_result(result: ProjectedSubjectTickInputs) -> dict[str, object]:
    return {
        "projection_id": result.projection_id,
        "source_contact_frame_ref": result.source_contact_frame_ref,
        "projection_status": result.projection_status,
        "ab_ref_count": result.counters.projected_ab_ref_count,
        "acp01_basis_count": result.counters.projected_acp01_basis_count,
        "ap01_lineage_count": result.counters.projected_ap01_lineage_count,
        "blocked_reasons": result.blocked_projection_reasons,
        "authority_flags": asdict(result.authority_flags),
        "action_request_emitted": result.action_request_emitted,
        "world_submission_emitted": result.world_submission_emitted,
        "fact_claimed": result.fact_claimed,
        "cause_confirmed": result.cause_confirmed,
        "value_assigned": result.value_assigned,
        "mature_recipe_claimed": result.mature_recipe_claimed,
        "mature_skill_claimed": result.mature_skill_claimed,
        "automation_claimed": result.automation_claimed,
    }


def validate_world_effect_frame_for_projection(
    effect_frame: WorldEffectFrame,
    config: ContactProjectionConfig,
) -> tuple[bool, str | None]:
    if not effect_frame.source_refs:
        return False, "effect_missing_source_refs"
    if effect_frame.authority_flags.has_violation():
        return False, "effect_authority_violation"
    if effect_frame.fact_claimed or effect_frame.cause_confirmed:
        return False, "effect_truth_oracle_rejected"
    if config.reject_truth_oracle:
        if _contains_any(effect_frame.effect_ref.lower(), _TRUTH_ORACLE_HINTS):
            return False, "effect_truth_oracle_rejected"
        if any(_contains_any(item.lower(), _TRUTH_ORACLE_HINTS) for item in effect_frame.public_delta_refs):
            return False, "effect_truth_oracle_rejected"
    if not effect_frame.request_ref and not effect_frame.passive_event_ref:
        return False, "effect_requires_request_or_passive_marker"
    return True, None


def _blocked_projection(
    *,
    projection_input: ContactProjectionInput,
    blocked_reasons: list[str],
    counters: ProjectionCounters,
    traces: list[ProjectionTrace],
    status: str,
    authority_flags: ContactAuthorityFlags,
) -> ProjectedSubjectTickInputs:
    reason_tuple = tuple(dict.fromkeys(blocked_reasons))
    return ProjectedSubjectTickInputs(
        projection_id=projection_input.projection_id,
        source_contact_frame_ref=projection_input.contact_result.phenomenal_contact_frame.frame_id,
        projection_status=status,
        projected_ab_input=ProjectedABInput(blocked_reasons=reason_tuple),
        projected_acp01_basis=ProjectedACP01Basis(blocked_reasons=reason_tuple),
        projected_ap01_lineage=ProjectedAP01Lineage(blocked_reasons=reason_tuple),
        public_basis_refs=(),
        blocked_projection_reasons=reason_tuple,
        authority_flags=authority_flags,
        counters=counters,
        traces=tuple(traces),
        hidden_eval_used=False,
        scenario_label_used=False,
        action_request_emitted=False,
        world_submission_emitted=False,
        fact_claimed=False,
        cause_confirmed=False,
        value_assigned=False,
        mature_recipe_claimed=False,
        mature_skill_claimed=False,
        automation_claimed=False,
    )


def _build_channel_map(
    projection_input: ContactProjectionInput,
    config: ContactProjectionConfig,
) -> dict[str, ContactChannelKind]:
    frame = projection_input.contact_result.phenomenal_contact_frame
    refs = tuple(
        dict.fromkeys(
            (
                *frame.public_observation_refs,
                *frame.public_effect_refs,
                *frame.passive_event_refs,
                *frame.residue_refs,
                *frame.uncertainty_refs,
                *frame.conflict_refs,
            )
        )
    )
    mapping: dict[str, ContactChannelKind] = {}
    for item in refs:
        channel = classify_contact_channel(item, projection_input)
        if channel is ContactChannelKind.UNKNOWN_PUBLIC and not config.allow_unknown_public_channels:
            continue
        mapping[item] = channel
    return mapping


def _channel_ref_groups(channel_map: dict[str, ContactChannelKind]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {}
    for ref_id, kind in channel_map.items():
        grouped.setdefault(kind.value, []).append(ref_id)
    return {key: tuple(value) for key, value in grouped.items()}


def _append_trace(
    *,
    traces: list[ProjectionTrace],
    stage_name: str,
    input_refs: tuple[str, ...],
    output_refs: tuple[str, ...],
    channel_kind: ContactChannelKind | None,
    decision: str,
    blocked_reason: str | None,
    authority_flags: ContactAuthorityFlags,
) -> None:
    traces.append(
        ProjectionTrace(
            stage_name=stage_name,
            input_refs=input_refs,
            output_refs=output_refs,
            channel_kind=channel_kind,
            decision=decision,
            blocked_reason=blocked_reason,
            authority_flags=authority_flags,
        )
    )


def _cap(items: tuple[str, ...], max_count: int) -> tuple[str, ...]:
    return items[:max_count]


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(token in haystack for token in needles)


def _extract_explicit_pressure_basis(channel_refs: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    body_refs = channel_refs.get(ContactChannelKind.BODY_INTERNAL.value, ())
    explicit_prefixes = ("pressure:", "body:pressure:", "body_pressure:", "viability:")
    return tuple(item for item in body_refs if item.lower().startswith(explicit_prefixes))


def _bounded_ref_limit_trigger_count(
    *,
    projection_input: ContactProjectionInput,
    config: ContactProjectionConfig,
    ab_projection: ProjectedABInput,
    acp_projection: ProjectedACP01Basis,
    ap_lineage: ProjectedAP01Lineage,
) -> int:
    triggered = 0
    frame = projection_input.contact_result.phenomenal_contact_frame
    if len(frame.public_observation_refs) > len(ab_projection.public_observation_refs):
        triggered += 1
    if len(frame.public_effect_refs) > len(ab_projection.public_effect_refs):
        triggered += 1
    if len(frame.residue_refs) > len(ab_projection.residue_refs):
        triggered += 1
    if len(projection_input.action_surface_declarations) > len(acp_projection.action_surface_basis_refs):
        triggered += 1
    if len(projection_input.world_effect_frames) > len(ap_lineage.effect_refs):
        triggered += 1
    return triggered
