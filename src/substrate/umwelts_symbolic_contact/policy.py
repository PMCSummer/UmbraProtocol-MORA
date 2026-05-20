from __future__ import annotations

from dataclasses import asdict

from substrate.umwelt0_phenomenal_contact import ContactAuthorityFlags

from .models import (
    ActionSurfaceSpec,
    ContactChannelDeclaration,
    ContactIR,
    ContactSpec,
    ContactSpecCounters,
    ContactSpecValidationResult,
    EffectSurfaceSpec,
    ForbiddenPayloadRule,
    ProviderSurfaceSpec,
    PublicRefDeclaration,
    UMWELT0ConstructionPlan,
    UMWELTSChannelKind,
    UMWELTSRefKind,
    UMWELTSValidationStatus,
)

_POLICY_FORBIDDEN = (
    "selected_action",
    "preferred_action",
    "if_then_policy",
    "route_plan",
    "goal_selection",
    "behavior_tree",
    "scripted_solution",
    "factory_sequence",
    "solution_sequence",
    "factory_steps",
    "ordered_plan",
    "required_action_order",
    "craft_then_place_then_run",
    "intrinsic_need",
    "drive_weight",
    "homeostatic_rule",
    "subject_goal",
    "badness_function",
)
_RECIPE_ORACLE_FORBIDDEN = (
    "true_recipe",
    "recipe_truth",
    "exact_hidden_recipe",
    "authoritative_recipe_table",
    "hidden_transformation_truth",
)
_BACKEND_TRUTH_FORBIDDEN = (
    "worldstate",
    "full_world_state",
    "hidden_map",
    "full_map",
    "backend_object_id",
    "hidden_label",
    "eval_label",
    "scenario_label_as_basis",
)


def validate_contact_spec(spec: ContactSpec) -> ContactSpecValidationResult:
    blocked: list[str] = []
    warnings: list[str] = []
    trace: list[str] = []
    counters = ContactSpecCounters(
        channel_count=len(spec.channel_declarations),
        ref_count=len(spec.public_ref_declarations),
        action_surface_count=len(spec.action_surface_declarations),
        effect_surface_count=len(spec.effect_surface_declarations),
        provider_count=len(spec.provider_declarations),
        unknown_channel_count=sum(1 for c in spec.channel_declarations if c.channel_kind is UMWELTSChannelKind.UNKNOWN_PUBLIC),
    )

    _ensure_authority_false(spec.authority_profile, blocked, trace)
    _reject_forbidden_payloads_in_metadata(spec.metadata, blocked, counters, trace)
    channel_map = {item.channel_id: item for item in spec.channel_declarations}
    _apply_forbidden_rules(spec, spec.forbidden_payload_rules, blocked, counters, trace)

    channel_ids = set(channel_map)
    source_requirement_missing_count = 0
    lossiness_requirement_missing_count = 0
    bounded_limit_triggered_count = 0
    selected_action_block_count = 0
    true_recipe_block_count = 0
    full_map_block_count = 0
    hidden_label_block_count = 0
    worldstate_block_count = 0
    backend_specific_leak_count = 0
    authority_violation_count = 0

    for channel in spec.channel_declarations:
        channel_issues = validate_channel_declaration(channel)
        blocked.extend(channel_issues)
        source_requirement_missing_count += sum(1 for issue in channel_issues if "source" in issue)
        lossiness_requirement_missing_count += sum(1 for issue in channel_issues if "lossiness" in issue)
        bounded_limit_triggered_count += sum(1 for issue in channel_issues if "bounded" in issue)
        trace.append(f"channel:{channel.channel_id}:{'ok' if not channel_issues else 'blocked'}")

    for ref_item in spec.public_ref_declarations:
        ref_issues = validate_public_ref_declaration(ref_item, channel_map)
        blocked.extend(ref_issues)
        source_requirement_missing_count += sum(1 for issue in ref_issues if "source" in issue)
        backend_specific_leak_count += sum(1 for issue in ref_issues if "backend_specific" in issue)
        true_recipe_block_count += sum(1 for issue in ref_issues if "true_recipe" in issue)
        full_map_block_count += sum(1 for issue in ref_issues if "full_map" in issue)
        hidden_label_block_count += sum(1 for issue in ref_issues if "hidden_label" in issue)
        worldstate_block_count += sum(1 for issue in ref_issues if "worldstate" in issue)
        trace.append(f"ref:{ref_item.ref_id}:{'ok' if not ref_issues else 'blocked'}")

    for surface in spec.action_surface_declarations:
        action_issues = validate_action_surface_spec(surface, channel_ids)
        blocked.extend(action_issues)
        selected_action_block_count += sum(1 for issue in action_issues if "selected_action" in issue or "planner_policy" in issue)
        source_requirement_missing_count += sum(1 for issue in action_issues if "source" in issue)
        authority_violation_count += sum(1 for issue in action_issues if "authority" in issue)
        trace.append(f"action_surface:{surface.surface_id}:{'ok' if not action_issues else 'blocked'}")

    for effect in spec.effect_surface_declarations:
        effect_issues = validate_effect_surface_spec(effect, channel_ids)
        blocked.extend(effect_issues)
        source_requirement_missing_count += sum(1 for issue in effect_issues if "source" in issue)
        authority_violation_count += sum(1 for issue in effect_issues if "authority" in issue)
        true_recipe_block_count += sum(1 for issue in effect_issues if "true_recipe" in issue)
        worldstate_block_count += sum(1 for issue in effect_issues if "worldstate" in issue)
        trace.append(f"effect_surface:{effect.effect_surface_id}:{'ok' if not effect_issues else 'blocked'}")

    for provider in spec.provider_declarations:
        provider_issues = validate_provider_surface_spec(provider, channel_ids)
        blocked.extend(provider_issues)
        source_requirement_missing_count += sum(1 for issue in provider_issues if "source" in issue)
        authority_violation_count += sum(1 for issue in provider_issues if "authority" in issue)
        trace.append(f"provider:{provider.provider_id}:{'ok' if not provider_issues else 'blocked'}")

    provider_warnings = _detect_provider_conflicts(spec.provider_declarations)
    if provider_warnings:
        warnings.extend(provider_warnings)
        trace.extend(f"provider_conflict:{item}" for item in provider_warnings)

    if spec.lossiness_requirements.required_when_partial and not spec.lossiness_requirements.lossiness_refs:
        blocked.append("lossiness_requirement_missing_for_partial_spec")
        lossiness_requirement_missing_count += 1
        trace.append("spec:lossiness:blocked")

    if spec.uncertainty_requirements.required_when_ambiguous and not spec.uncertainty_requirements.uncertainty_refs:
        warnings.append("uncertainty_refs_missing_for_ambiguous_spec")
        trace.append("spec:uncertainty:warning")

    blocked = list(dict.fromkeys(blocked))
    warnings = list(dict.fromkeys(warnings))
    status = UMWELTSValidationStatus.BLOCKED if blocked else (UMWELTSValidationStatus.PARTIAL if warnings else UMWELTSValidationStatus.ACCEPTED)

    counters = ContactSpecCounters(
        channel_count=counters.channel_count,
        ref_count=counters.ref_count,
        action_surface_count=counters.action_surface_count,
        effect_surface_count=counters.effect_surface_count,
        provider_count=counters.provider_count,
        blocked_item_count=len(blocked),
        source_requirement_missing_count=source_requirement_missing_count,
        lossiness_requirement_missing_count=lossiness_requirement_missing_count,
        forbidden_payload_count=sum(
            1 for token in blocked if _contains_any(token, _POLICY_FORBIDDEN + _RECIPE_ORACLE_FORBIDDEN + _BACKEND_TRUTH_FORBIDDEN)
        ),
        backend_specific_leak_count=backend_specific_leak_count,
        selected_action_block_count=selected_action_block_count,
        true_recipe_block_count=true_recipe_block_count,
        full_map_block_count=full_map_block_count,
        hidden_label_block_count=hidden_label_block_count,
        worldstate_block_count=worldstate_block_count,
        authority_violation_count=authority_violation_count,
        unknown_channel_count=counters.unknown_channel_count,
        bounded_limit_triggered_count=bounded_limit_triggered_count,
    )

    normalized_ir = None
    plan = None
    if status in {UMWELTSValidationStatus.ACCEPTED, UMWELTSValidationStatus.PARTIAL}:
        normalized_ir = normalize_contact_spec_to_ir(spec, counters, warnings)
        plan = build_umwelt0_construction_plan(spec, normalized_ir)

    return ContactSpecValidationResult(
        spec_id=spec.spec_id,
        status=status,
        blocked_reasons=tuple(blocked),
        warnings=tuple(warnings),
        counters=counters,
        normalized_ir=normalized_ir,
        authority_flags=ContactAuthorityFlags(),
        conformance_trace=tuple(trace),
        umwelt0_construction_plan=plan,
        action_request_emitted=False,
        world_action_emitted=False,
        fact_claimed=False,
        cause_confirmed=False,
        value_assigned=False,
        mature_recipe_claimed=False,
        mature_skill_claimed=False,
        automation_claimed=False,
    )


def normalize_contact_spec_to_ir(
    spec: ContactSpec,
    counters: ContactSpecCounters | None = None,
    warnings: list[str] | None = None,
) -> ContactIR:
    trace = ["normalize:start", f"channels:{len(spec.channel_declarations)}", f"refs:{len(spec.public_ref_declarations)}"]
    blocked_items: list[str] = []
    normalized_channels: list[ContactChannelDeclaration] = []
    normalized_refs: list[PublicRefDeclaration] = []
    normalized_actions: list[ActionSurfaceSpec] = []
    normalized_effects: list[EffectSurfaceSpec] = []
    normalized_providers: list[ProviderSurfaceSpec] = []
    bounded_trigger = 0

    for channel in spec.channel_declarations:
        if channel.max_refs < 1:
            blocked_items.append(f"channel:{channel.channel_id}:invalid_max_refs")
            continue
        normalized_channels.append(channel)

    channel_bounds = {item.channel_id: item.max_refs for item in normalized_channels}
    ref_count_per_channel: dict[str, int] = {key: 0 for key in channel_bounds}

    for ref_item in spec.public_ref_declarations:
        if ref_item.channel_id not in channel_bounds:
            blocked_items.append(f"ref:{ref_item.ref_id}:unknown_channel")
            continue
        ref_count_per_channel[ref_item.channel_id] += 1
        if ref_count_per_channel[ref_item.channel_id] > channel_bounds[ref_item.channel_id]:
            bounded_trigger += 1
            blocked_items.append(f"ref:{ref_item.ref_id}:channel_max_refs_exceeded")
            continue
        normalized_refs.append(ref_item)

    for item in spec.action_surface_declarations:
        normalized_actions.append(item)
    for item in spec.effect_surface_declarations:
        normalized_effects.append(item)
    for item in spec.provider_declarations:
        normalized_providers.append(item)

    blocked_items = list(dict.fromkeys(blocked_items))
    ir_status = UMWELTSValidationStatus.PARTIAL if blocked_items or warnings else UMWELTSValidationStatus.ACCEPTED
    local_counters = counters or ContactSpecCounters()
    local_counters = ContactSpecCounters(
        **{**asdict(local_counters), "blocked_item_count": max(local_counters.blocked_item_count, len(blocked_items)), "bounded_limit_triggered_count": max(local_counters.bounded_limit_triggered_count, bounded_trigger)}
    )
    trace.append(f"normalize:status:{ir_status.value}")
    return ContactIR(
        ir_id=f"ir:{spec.spec_id}",
        source_spec_ref=spec.spec_id,
        normalized_channels=tuple(normalized_channels),
        normalized_refs=tuple(normalized_refs),
        normalized_action_surfaces=tuple(normalized_actions),
        normalized_effect_surfaces=tuple(normalized_effects),
        normalized_providers=tuple(normalized_providers),
        blocked_items=tuple(blocked_items),
        conformance_status=ir_status,
        authority_flags=ContactAuthorityFlags(),
        counters=local_counters,
        traces=tuple(trace),
    )


def validate_channel_declaration(channel: ContactChannelDeclaration) -> tuple[str, ...]:
    issues: list[str] = []
    if not channel.channel_id:
        issues.append("channel_missing_id")
    if channel.max_refs < 1:
        issues.append(f"channel:{channel.channel_id}:bounded_max_refs_required")
    if channel.requires_source_refs and not channel.public and channel.channel_kind is not UMWELTSChannelKind.UNKNOWN_PUBLIC:
        issues.append(f"channel:{channel.channel_id}:public_channel_required")
    if channel.channel_kind is UMWELTSChannelKind.UNKNOWN_PUBLIC and not channel.allows_unknown_refs:
        issues.append(f"channel:{channel.channel_id}:unknown_channel_without_allowance")
    if channel.channel_kind is UMWELTSChannelKind.UNKNOWN_PUBLIC and channel.max_refs > 32:
        issues.append(f"channel:{channel.channel_id}:unknown_channel_unbounded")
    _ensure_authority_false(channel.authority_flags, issues, None, prefix=f"channel:{channel.channel_id}")
    return tuple(issues)


def validate_public_ref_declaration(
    ref_item: PublicRefDeclaration,
    known_channels: dict[str, ContactChannelDeclaration],
) -> tuple[str, ...]:
    issues: list[str] = []
    if ref_item.channel_id not in known_channels:
        issues.append(f"ref:{ref_item.ref_id}:unknown_channel")
    if ref_item.source_requirements.required and not ref_item.source_requirements.source_refs:
        issues.append(f"ref:{ref_item.ref_id}:source_requirements_missing")
    if ref_item.backend_ref and not ref_item.backend_ref.startswith(("public:", "transformed:")):
        issues.append(f"ref:{ref_item.ref_id}:backend_specific_field_untranslated")

    if ref_item.channel_id in known_channels:
        channel = known_channels[ref_item.channel_id]
        if channel.channel_kind is UMWELTSChannelKind.UNKNOWN_PUBLIC:
            if not ref_item.uncertainty_policy.required_when_ambiguous:
                issues.append(f"ref:{ref_item.ref_id}:unknown_channel_uncertainty_policy_missing")
            if not ref_item.uncertainty_policy.uncertainty_refs:
                issues.append(f"ref:{ref_item.ref_id}:unknown_channel_uncertainty_refs_missing")

    metadata_tokens = tuple(ref_item.allowed_metadata_keys)
    haystack = (ref_item.ref_id, ref_item.backend_ref or "", *ref_item.forbidden_markers, *metadata_tokens)
    if any(_contains_any(token.lower(), _POLICY_FORBIDDEN) for token in haystack):
        issues.append(f"ref:{ref_item.ref_id}:planner_payload_forbidden")
    issues.extend(_reject_true_recipe_or_full_map(*haystack, prefix=f"ref:{ref_item.ref_id}"))
    issues.extend(_reject_backend_worldstate(*haystack, prefix=f"ref:{ref_item.ref_id}"))
    issues.extend(_reject_hidden_labels(*haystack, prefix=f"ref:{ref_item.ref_id}"))
    _ensure_authority_false(ref_item.authority_flags, issues, None, prefix=f"ref:{ref_item.ref_id}")
    return tuple(dict.fromkeys(issues))


def validate_action_surface_spec(surface: ActionSurfaceSpec, known_channels: set[str]) -> tuple[str, ...]:
    issues: list[str] = []
    if surface.channel_id not in known_channels:
        issues.append(f"action_surface:{surface.surface_id}:unknown_channel")
    if surface.source_requirements.required and not surface.source_requirements.source_refs:
        issues.append(f"action_surface:{surface.surface_id}:source_requirements_missing")
    issues.extend(reject_selected_action_policy(surface, prefix=f"action_surface:{surface.surface_id}"))
    issues.extend(
        _reject_true_recipe_or_full_map(
            surface.surface_id,
            surface.action_kind,
            *surface.forbidden_policy_fields,
            *_iter_token_strings(surface.metadata),
            prefix=f"action_surface:{surface.surface_id}",
        )
    )
    issues.extend(
        _reject_backend_worldstate(
            surface.surface_id,
            surface.action_kind,
            *surface.forbidden_policy_fields,
            *_iter_token_strings(surface.metadata),
            prefix=f"action_surface:{surface.surface_id}",
        )
    )
    issues.extend(
        _reject_hidden_labels(
            surface.surface_id,
            surface.action_kind,
            *surface.forbidden_policy_fields,
            *_iter_token_strings(surface.metadata),
            prefix=f"action_surface:{surface.surface_id}",
        )
    )
    _ensure_authority_false(surface.authority_flags, issues, None, prefix=f"action_surface:{surface.surface_id}")
    return tuple(dict.fromkeys(issues))


def validate_effect_surface_spec(effect: EffectSurfaceSpec, known_channels: set[str]) -> tuple[str, ...]:
    issues: list[str] = []
    if effect.channel_id not in known_channels:
        issues.append(f"effect_surface:{effect.effect_surface_id}:unknown_channel")
    if not effect.request_correlated_allowed and not effect.passive_event_allowed:
        issues.append(f"effect_surface:{effect.effect_surface_id}:must_allow_request_or_passive")
    if not effect.required_source_refs:
        issues.append(f"effect_surface:{effect.effect_surface_id}:source_requirements_missing")
    issues.extend(
        _reject_true_recipe_or_full_map(
            effect.effect_surface_id,
            effect.effect_kind,
            *effect.residue_policy,
            *effect.required_delta_refs,
            *_iter_token_strings(effect.metadata),
            prefix=f"effect_surface:{effect.effect_surface_id}",
        )
    )
    issues.extend(
        _reject_backend_worldstate(
            effect.effect_surface_id,
            effect.effect_kind,
            *effect.residue_policy,
            *effect.required_delta_refs,
            *_iter_token_strings(effect.metadata),
            prefix=f"effect_surface:{effect.effect_surface_id}",
        )
    )
    issues.extend(
        _reject_hidden_labels(
            effect.effect_surface_id,
            effect.effect_kind,
            *effect.residue_policy,
            *effect.required_delta_refs,
            *_iter_token_strings(effect.metadata),
            prefix=f"effect_surface:{effect.effect_surface_id}",
        )
    )
    _ensure_authority_false(effect.authority_flags, issues, None, prefix=f"effect_surface:{effect.effect_surface_id}")
    return tuple(dict.fromkeys(issues))


def validate_provider_surface_spec(provider: ProviderSurfaceSpec, known_channels: set[str]) -> tuple[str, ...]:
    issues: list[str] = []
    if provider.channel_id not in known_channels:
        issues.append(f"provider:{provider.provider_id}:unknown_channel")
    if provider.source_requirements.required and not provider.source_requirements.source_refs:
        issues.append(f"provider:{provider.provider_id}:source_requirements_missing")
    if provider.truth_authority:
        issues.append(f"provider:{provider.provider_id}:truth_authority_forbidden")
    if provider.can_mature_recipe:
        issues.append(f"provider:{provider.provider_id}:mature_recipe_forbidden")
    if provider.can_assign_value:
        issues.append(f"provider:{provider.provider_id}:assign_value_forbidden")
    if provider.can_select_action:
        issues.append(f"provider:{provider.provider_id}:action_selection_forbidden")
    issues.extend(
        _reject_true_recipe_or_full_map(
            provider.provider_id,
            provider.provider_kind,
            *_iter_token_strings(provider.metadata),
            prefix=f"provider:{provider.provider_id}",
        )
    )
    issues.extend(
        _reject_backend_worldstate(
            provider.provider_id,
            provider.provider_kind,
            *_iter_token_strings(provider.metadata),
            prefix=f"provider:{provider.provider_id}",
        )
    )
    issues.extend(
        _reject_hidden_labels(
            provider.provider_id,
            provider.provider_kind,
            *_iter_token_strings(provider.metadata),
            prefix=f"provider:{provider.provider_id}",
        )
    )
    return tuple(dict.fromkeys(issues))


def reject_forbidden_payloads(spec: ContactSpec) -> tuple[str, ...]:
    blocked: list[str] = []
    blocked.extend(_reject_forbidden_payloads_in_metadata(spec.metadata, [], None, None, collect_only=True))
    for rule in spec.forbidden_payload_rules:
        for token in rule.blocked_tokens:
            if _contains_any(token.lower(), _POLICY_FORBIDDEN + _RECIPE_ORACLE_FORBIDDEN + _BACKEND_TRUTH_FORBIDDEN):
                blocked.append(f"forbidden_rule:{rule.rule_id}:{token}")
    return tuple(dict.fromkeys(blocked))


def reject_selected_action_policy(surface: ActionSurfaceSpec, *, prefix: str) -> tuple[str, ...]:
    tokens = (surface.action_kind, *surface.forbidden_policy_fields, *surface.metadata.keys(), *surface.metadata.values())
    return tuple(
        f"{prefix}:selected_action_policy_forbidden:{token}"
        for token in tokens
        if _contains_any(token.lower(), _POLICY_FORBIDDEN)
    )


def reject_true_recipe_or_full_map(spec: ContactSpec) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            [
                *(_reject_true_recipe_or_full_map(spec.spec_id, spec.backend_family, *spec.metadata.keys(), *spec.metadata.values(), prefix=f"spec:{spec.spec_id}")),
                *(_reject_true_recipe_or_full_map(*(item.ref_id for item in spec.public_ref_declarations), prefix=f"spec:{spec.spec_id}:refs")),
            ]
        )
    )


def reject_backend_worldstate(spec: ContactSpec) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            _reject_backend_worldstate(
                spec.spec_id,
                spec.backend_family,
                *spec.metadata.keys(),
                *spec.metadata.values(),
                prefix=f"spec:{spec.spec_id}",
            )
        )
    )


def reject_hidden_labels(spec: ContactSpec) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            _reject_hidden_labels(
                spec.spec_id,
                spec.backend_family,
                *spec.metadata.keys(),
                *spec.metadata.values(),
                prefix=f"spec:{spec.spec_id}",
            )
        )
    )


def ensure_source_requirements(spec: ContactSpec) -> tuple[str, ...]:
    issues: list[str] = []
    if spec.source_requirements.required and not spec.source_requirements.source_refs:
        issues.append("spec:source_requirements_missing")
    for channel in spec.channel_declarations:
        if channel.requires_source_refs and not spec.source_requirements.source_refs:
            issues.append(f"channel:{channel.channel_id}:source_requirements_missing")
    for ref_item in spec.public_ref_declarations:
        if ref_item.source_requirements.required and not ref_item.source_requirements.source_refs:
            issues.append(f"ref:{ref_item.ref_id}:source_requirements_missing")
    return tuple(dict.fromkeys(issues))


def ensure_lossiness_requirements(spec: ContactSpec) -> tuple[str, ...]:
    issues: list[str] = []
    if spec.lossiness_requirements.required_when_partial and not spec.lossiness_requirements.lossiness_refs:
        issues.append("spec:lossiness_requirements_missing")
    for channel in spec.channel_declarations:
        if channel.requires_lossiness_when_partial and not spec.lossiness_requirements.lossiness_refs:
            issues.append(f"channel:{channel.channel_id}:lossiness_requirements_missing")
    return tuple(dict.fromkeys(issues))


def build_umwelt0_construction_plan(spec: ContactSpec, ir: ContactIR) -> UMWELT0ConstructionPlan:
    public_observation_refs: list[str] = []
    public_effect_refs: list[str] = []
    passive_event_refs: list[str] = []
    action_surface_refs: list[str] = []
    effect_surface_refs: list[str] = []
    residue_refs: list[str] = []
    uncertainty_refs: list[str] = []
    conflict_refs: list[str] = []
    source_refs: list[str] = list(spec.source_requirements.source_refs)
    lossiness_refs: list[str] = list(spec.lossiness_requirements.lossiness_refs)

    for ref_item in ir.normalized_refs:
        source_refs.extend(ref_item.source_requirements.source_refs)
        uncertainty_refs.extend(ref_item.uncertainty_policy.uncertainty_refs)
        lossiness_refs.extend(ref_item.lossiness_policy.lossiness_refs)
        if ref_item.ref_kind is UMWELTSRefKind.EFFECT:
            public_effect_refs.append(ref_item.ref_id)
        elif ref_item.ref_kind is UMWELTSRefKind.RESIDUE:
            residue_refs.append(ref_item.ref_id)
        elif ref_item.ref_kind is UMWELTSRefKind.UNCERTAINTY:
            uncertainty_refs.append(ref_item.ref_id)
        elif ref_item.ref_kind is UMWELTSRefKind.CONFLICT:
            conflict_refs.append(ref_item.ref_id)
        elif ref_item.ref_kind is UMWELTSRefKind.LOSSINESS:
            lossiness_refs.append(ref_item.ref_id)
        else:
            public_observation_refs.append(ref_item.ref_id)

    for action_surface in ir.normalized_action_surfaces:
        action_surface_refs.append(action_surface.surface_id)
        source_refs.extend(action_surface.source_requirements.source_refs)

    for effect_surface in ir.normalized_effect_surfaces:
        effect_surface_refs.append(effect_surface.effect_surface_id)
        source_refs.extend(effect_surface.required_source_refs)
        if effect_surface.passive_event_allowed and not effect_surface.request_correlated_allowed:
            passive_event_refs.append(effect_surface.effect_surface_id)
        else:
            public_effect_refs.append(effect_surface.effect_surface_id)
        residue_refs.extend(effect_surface.residue_policy)
        conflict_refs.extend(effect_surface.required_delta_refs)

    blocked_reasons = tuple(dict.fromkeys(ir.blocked_items))
    return UMWELT0ConstructionPlan(
        plan_id=f"umwelt0-plan:{spec.spec_id}",
        source_spec_ref=spec.spec_id,
        source_ir_ref=ir.ir_id,
        public_observation_refs=tuple(dict.fromkeys(public_observation_refs)),
        public_effect_refs=tuple(dict.fromkeys(public_effect_refs)),
        passive_event_refs=tuple(dict.fromkeys(passive_event_refs)),
        action_surface_refs=tuple(dict.fromkeys(action_surface_refs)),
        effect_surface_refs=tuple(dict.fromkeys(effect_surface_refs)),
        residue_refs=tuple(dict.fromkeys(residue_refs)),
        uncertainty_refs=tuple(dict.fromkeys(uncertainty_refs)),
        conflict_refs=tuple(dict.fromkeys(conflict_refs)),
        source_refs=tuple(dict.fromkeys(source_refs)),
        lossiness_refs=tuple(dict.fromkeys(lossiness_refs)),
        blocked_reasons=blocked_reasons,
        authority_flags=ContactAuthorityFlags(),
        hidden_eval_used=False,
        scenario_label_used=False,
        backend_truth_excluded=True,
        action_request_emitted=False,
        world_submission_emitted=False,
        fact_claimed=False,
        cause_confirmed=False,
        value_assigned=False,
        mature_recipe_claimed=False,
        mature_skill_claimed=False,
        automation_claimed=False,
    )


def summarize_contact_spec_conformance(result: ContactSpecValidationResult) -> dict[str, object]:
    return {
        "spec_id": result.spec_id,
        "status": result.status.value,
        "blocked_reasons": result.blocked_reasons,
        "warnings": result.warnings,
        "counters": asdict(result.counters),
        "authority_flags": asdict(result.authority_flags),
        "has_normalized_ir": result.normalized_ir is not None,
        "has_umwelt0_plan": result.umwelt0_construction_plan is not None,
        "action_request_emitted": result.action_request_emitted,
        "world_action_emitted": result.world_action_emitted,
        "fact_claimed": result.fact_claimed,
        "cause_confirmed": result.cause_confirmed,
        "value_assigned": result.value_assigned,
        "mature_recipe_claimed": result.mature_recipe_claimed,
        "mature_skill_claimed": result.mature_skill_claimed,
        "automation_claimed": result.automation_claimed,
    }


def _apply_forbidden_rules(
    spec: ContactSpec,
    rules: tuple[ForbiddenPayloadRule, ...],
    blocked: list[str],
    counters: ContactSpecCounters,
    trace: list[str],
) -> None:
    for rule in rules:
        if not rule.rule_id:
            blocked.append("forbidden_rule:missing_rule_id")
            trace.append("rule:missing_id:block")
            continue
        if not rule.blocked_tokens:
            blocked.append(f"forbidden_rule:{rule.rule_id}:empty_blocked_tokens")
            trace.append(f"rule:{rule.rule_id}:empty_tokens:block")
            continue
        if not rule.applies_to:
            blocked.append(f"forbidden_rule:{rule.rule_id}:missing_applies_to")
            trace.append(f"rule:{rule.rule_id}:missing_applies_to:block")
            continue
        matches = _scan_rule_matches(spec, rule)
        for match in matches:
            blocked.append(f"forbidden_rule:{rule.rule_id}:{match}")
        trace.append(
            f"rule:{rule.rule_id}:{'blocked' if matches else 'registered'}"
        )


def _reject_forbidden_payloads_in_metadata(
    metadata: dict[str, str],
    blocked: list[str],
    counters: ContactSpecCounters | None,
    trace: list[str] | None,
    *,
    collect_only: bool = False,
) -> tuple[str, ...]:
    local: list[str] = []
    for haystack in _iter_token_strings(metadata):
        lowered = haystack.lower()
        if len(lowered) > 1024:
            local.append("metadata:oversized_value")
        for token in _matching_tokens(lowered, _POLICY_FORBIDDEN):
            local.append(f"metadata:planner_payload:{token}")
        for token in _matching_tokens(lowered, _RECIPE_ORACLE_FORBIDDEN):
            local.append(f"metadata:true_recipe_payload:{token}")
        for token in _matching_tokens(lowered, _BACKEND_TRUTH_FORBIDDEN):
            local.append(f"metadata:backend_truth_payload:{token}")
    if collect_only:
        return tuple(dict.fromkeys(local))
    blocked.extend(local)
    if trace is not None and local:
        trace.append("metadata:blocked")
    return tuple(dict.fromkeys(local))


def _reject_true_recipe_or_full_map(*items: str, prefix: str) -> list[str]:
    issues: list[str] = []
    for item in items:
        lowered = str(item).lower()
        if _contains_any(lowered, _RECIPE_ORACLE_FORBIDDEN):
            issues.append(f"{prefix}:true_recipe_forbidden")
        if "full_map" in lowered or "hidden_map" in lowered:
            issues.append(f"{prefix}:full_map_forbidden")
    return issues


def _reject_backend_worldstate(*items: str, prefix: str) -> list[str]:
    issues: list[str] = []
    for item in items:
        lowered = str(item).lower()
        if "worldstate" in lowered or "full_world_state" in lowered or "backend_object_id" in lowered:
            issues.append(f"{prefix}:worldstate_forbidden")
    return issues


def _reject_hidden_labels(*items: str, prefix: str) -> list[str]:
    issues: list[str] = []
    for item in items:
        lowered = str(item).lower()
        if "hidden_label" in lowered or "eval_label" in lowered or "scenario_label_as_basis" in lowered:
            issues.append(f"{prefix}:hidden_label_forbidden")
    return issues


def _contains_any(haystack: str, tokens: tuple[str, ...]) -> bool:
    lowered = haystack.lower()
    return any(token in lowered for token in tokens)


def _matching_tokens(haystack: str, tokens: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(token for token in tokens if token in haystack)


def _scan_rule_matches(spec: ContactSpec, rule: ForbiddenPayloadRule) -> tuple[str, ...]:
    matches: list[str] = []
    applies = {value.lower() for value in rule.applies_to}
    blocked_tokens = tuple(token.lower() for token in rule.blocked_tokens)

    def _match(scope: str, values: tuple[str, ...]) -> None:
        for value in values:
            lowered = value.lower()
            for token in blocked_tokens:
                if token in lowered:
                    matches.append(f"{scope}:{token}")

    if "spec" in applies or "metadata" in applies:
        _match("spec", _iter_token_strings(spec.metadata))

    if "ref" in applies:
        for ref_item in spec.public_ref_declarations:
            _match(
                f"ref:{ref_item.ref_id}",
                (
                    ref_item.ref_id,
                    ref_item.ref_kind.value,
                    ref_item.channel_id,
                    ref_item.backend_ref or "",
                    *ref_item.forbidden_markers,
                    *ref_item.allowed_metadata_keys,
                ),
            )

    if "action_surface" in applies:
        for surface in spec.action_surface_declarations:
            _match(
                f"action_surface:{surface.surface_id}",
                (
                    surface.surface_id,
                    surface.action_kind,
                    surface.channel_id,
                    *surface.forbidden_policy_fields,
                    *_iter_token_strings(surface.metadata),
                ),
            )

    if "effect_surface" in applies:
        for effect in spec.effect_surface_declarations:
            _match(
                f"effect_surface:{effect.effect_surface_id}",
                (
                    effect.effect_surface_id,
                    effect.effect_kind,
                    effect.channel_id,
                    *effect.required_delta_refs,
                    *effect.residue_policy,
                    *_iter_token_strings(effect.metadata),
                ),
            )

    if "provider" in applies:
        for provider in spec.provider_declarations:
            _match(
                f"provider:{provider.provider_id}",
                (
                    provider.provider_id,
                    provider.provider_kind,
                    provider.channel_id,
                    provider.authority_class,
                    *_iter_token_strings(provider.metadata),
                ),
            )

    if "channel" in applies:
        for channel in spec.channel_declarations:
            _match(
                f"channel:{channel.channel_id}",
                (channel.channel_id, channel.channel_kind.value, channel.provider_ref or ""),
            )

    return tuple(dict.fromkeys(matches))


def _iter_token_strings(value: object, *, _depth: int = 0, _max_depth: int = 5) -> tuple[str, ...]:
    if _depth > _max_depth:
        return ("max_depth_exceeded",)
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        tokens: list[str] = []
        for key, item in value.items():
            tokens.extend(_iter_token_strings(key, _depth=_depth + 1, _max_depth=_max_depth))
            tokens.extend(_iter_token_strings(item, _depth=_depth + 1, _max_depth=_max_depth))
        return tuple(tokens)
    if isinstance(value, (list, tuple, set)):
        tokens: list[str] = []
        for item in value:
            tokens.extend(_iter_token_strings(item, _depth=_depth + 1, _max_depth=_max_depth))
        return tuple(tokens)
    return (str(value),)


def _detect_provider_conflicts(providers: tuple[ProviderSurfaceSpec, ...]) -> tuple[str, ...]:
    by_claim_ref: dict[str, tuple[str, bool, bool, bool, bool, bool]] = {}
    warnings: list[str] = []
    for provider in providers:
        claim_ref = provider.metadata.get("claim_ref")
        if not claim_ref:
            continue
        signature = (
            provider.authority_class,
            provider.hint_only,
            provider.truth_authority,
            provider.can_mature_recipe,
            provider.can_assign_value,
            provider.can_select_action,
        )
        prior = by_claim_ref.get(claim_ref)
        if prior is None:
            by_claim_ref[claim_ref] = signature
            continue
        if prior != signature:
            warnings.append(f"provider_conflict:{claim_ref}")
    return tuple(dict.fromkeys(warnings))


def _ensure_authority_false(
    flags: ContactAuthorityFlags,
    blocked: list[str],
    trace: list[str] | None,
    *,
    prefix: str = "spec",
) -> None:
    if flags.has_violation():
        blocked.append(f"{prefix}:authority_violation")
        if trace is not None:
            trace.append(f"{prefix}:authority_block")
