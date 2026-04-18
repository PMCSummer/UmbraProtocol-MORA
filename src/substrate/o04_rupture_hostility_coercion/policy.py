from __future__ import annotations

from substrate.o03_strategy_class_evaluation import O03StrategyClass, O03StrategyEvaluationResult
from substrate.o04_rupture_hostility_coercion.models import (
    O04CertaintyBand,
    O04DirectionalityKind,
    O04DynamicGateDecision,
    O04DynamicLink,
    O04DynamicModel,
    O04DynamicResult,
    O04DynamicType,
    O04InteractionEventInput,
    O04LegitimacyHintStatus,
    O04LeverageSurfaceKind,
    O04RuptureStatus,
    O04ScopeMarker,
    O04SeverityBand,
    O04Telemetry,
)
from substrate.p01_project_formation import P01ProjectFormationResult


def build_o04_rupture_hostility_coercion(
    *,
    tick_id: str,
    tick_index: int,
    interaction_events: tuple[O04InteractionEventInput, ...],
    o03_result: O03StrategyEvaluationResult | None,
    p01_result: P01ProjectFormationResult | None,
    history_depth_band: str,
    source_lineage: tuple[str, ...],
    prior_state: O04DynamicModel | None = None,
    modeling_enabled: bool = True,
) -> O04DynamicResult:
    if not modeling_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    events = tuple(item for item in interaction_events if isinstance(item, O04InteractionEventInput))
    if not events:
        return _build_no_signal_result(
            tick_id=tick_id,
            tick_index=tick_index,
            source_lineage=source_lineage,
        )

    links: list[O04DynamicLink] = []
    hostility_candidates: list[str] = []
    coercion_candidates: list[str] = []
    retaliation_candidates: list[str] = []
    counterevidence: list[str] = []
    uncertainty_markers: list[str] = []
    agent_refs = sorted(
        {
            ref
            for event in events
            for ref in (event.actor_ref, event.target_ref)
            if isinstance(ref, str) and ref.strip()
        }
    )
    repeated_withdrawal_count = 0
    repair_attempt_count = 0
    escalation_count = 0
    tone_shortcut_forbidden_applied = False
    legitimacy_underconstrained = False
    dependency_underconstrained = False

    for index, event in enumerate(events, start=1):
        leverage_surface = _infer_leverage_surface(event)
        has_structure = leverage_surface is not O04LeverageSurfaceKind.NONE_DETECTED
        directionality = _event_directionality(event)
        dynamic_type = _classify_event_dynamic_type(event, has_structure=has_structure)
        severity = _severity_for_event(event=event, dynamic_type=dynamic_type)
        certainty = _certainty_for_event(
            event=event,
            dynamic_type=dynamic_type,
            has_structure=has_structure,
            directionality=directionality,
        )
        if (
            event.speech_act_kind in {"harsh_statement", "aggressive_tone"}
            and not has_structure
        ):
            tone_shortcut_forbidden_applied = True
            uncertainty_markers.append("tone_only_harshness_restricted")
        if event.legitimacy_hint_status is O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN and has_structure:
            legitimacy_underconstrained = True
            uncertainty_markers.append("legitimacy_underconstrained")
        if (
            dynamic_type in {
                O04DynamicType.COERCIVE_PRESSURE_CANDIDATE,
                O04DynamicType.FORCED_COMPLIANCE_CANDIDATE,
            }
            and not event.dependency_surface_present
            and not event.blocked_option_present
        ):
            dependency_underconstrained = True
            uncertainty_markers.append("dependency_model_underconstrained")

        evidence_refs = [event.evidence_ref or f"event:{event.event_id}"]
        if event.project_link_ref:
            evidence_refs.append(f"project:{event.project_link_ref}")
        counter_refs: list[str] = []
        if event.repair_attempt_marker:
            repair_attempt_count += 1
            counter_refs.append("repair_attempt_present")
        if event.consent_marker:
            counter_refs.append("consent_marker_present")
        if event.counterevidence_ref:
            counter_refs.append(event.counterevidence_ref)

        if dynamic_type in {
            O04DynamicType.COERCIVE_PRESSURE_CANDIDATE,
            O04DynamicType.FORCED_COMPLIANCE_CANDIDATE,
            O04DynamicType.EXCLUSION_SEQUENCE_CANDIDATE,
        }:
            coercion_candidates.append(f"link:{tick_id}:{index}")
        if dynamic_type in {
            O04DynamicType.HOSTILITY_CANDIDATE,
            O04DynamicType.RETALIATORY_ESCALATION_CANDIDATE,
        }:
            hostility_candidates.append(f"link:{tick_id}:{index}")
        if dynamic_type is O04DynamicType.RETALIATORY_ESCALATION_CANDIDATE:
            retaliation_candidates.append(f"link:{tick_id}:{index}")
        if event.access_withdrawal_present or event.commitment_break_marker or event.exclusion_marker:
            repeated_withdrawal_count += 1
        if event.escalation_shift_marker:
            escalation_count += 1
        counterevidence.extend(counter_refs)

        links.append(
            O04DynamicLink(
                link_id=f"link:{tick_id}:{index}",
                actor_ref=event.actor_ref,
                target_ref=event.target_ref,
                dynamic_type=dynamic_type,
                leverage_surface=leverage_surface,
                blocked_option_ref=event.event_id if event.blocked_option_present else None,
                threatened_outcome_ref=event.event_id if event.threatened_loss_present else None,
                directionality_kind=directionality,
                legitimacy_hint_status=event.legitimacy_hint_status,
                severity_band=severity,
                certainty_band=certainty,
                evidence_refs=tuple(dict.fromkeys(evidence_refs)),
                counterevidence_refs=tuple(dict.fromkeys(counter_refs)),
                temporal_scope=f"history:{history_depth_band}",
                status="active_candidate",
                provenance=event.provenance,
            )
        )

    directionality_kind = _directionality_kind(tuple(links))
    rupture_status = _rupture_status(
        repeated_withdrawal_count=repeated_withdrawal_count,
        repair_attempt_count=repair_attempt_count,
        escalation_count=escalation_count,
        history_depth_band=history_depth_band,
    )
    rupture_status, rupture_carry_markers = _apply_prior_rupture_carry(
        prior_state=prior_state,
        current_status=rupture_status,
        repeated_withdrawal_count=repeated_withdrawal_count,
        repair_attempt_count=repair_attempt_count,
        history_depth_band=history_depth_band,
    )
    uncertainty_markers.extend(rupture_carry_markers)
    dominant = _dominant_dynamic_type(
        links=tuple(links),
        rupture_status=rupture_status,
        coercion_candidates=tuple(coercion_candidates),
    )
    top_severity = _top_band(tuple(link.severity_band for link in links))
    top_certainty = _top_band(tuple(link.certainty_band for link in links))
    no_safe_dynamic_claim = bool(
        not coercion_candidates
        and not hostility_candidates
        and rupture_status is O04RuptureStatus.NO_RUPTURE_BASIS
        and dominant in {O04DynamicType.DISAGREEMENT_ONLY, O04DynamicType.AMBIGUOUS_PRESSURE}
    )
    if no_safe_dynamic_claim:
        uncertainty_markers.append("no_safe_dynamic_claim")

    o03_link = (
        isinstance(o03_result, O03StrategyEvaluationResult)
        and o03_result.state.high_local_gain_but_high_entropy
    )
    p01_link = (
        isinstance(p01_result, P01ProjectFormationResult)
        and p01_result.state.conflicting_authority
    )
    if o03_link:
        uncertainty_markers.append("o03_high_entropy_context")
    if p01_link:
        uncertainty_markers.append("p01_conflicting_authority_context")

    state = O04DynamicModel(
        interaction_model_id=f"o04-dynamic:{tick_id}",
        agent_refs=tuple(agent_refs),
        directional_links=tuple(links),
        rupture_status=rupture_status,
        hostility_candidates=tuple(dict.fromkeys(hostility_candidates)),
        coercion_candidates=tuple(dict.fromkeys(coercion_candidates)),
        retaliation_candidates=tuple(dict.fromkeys(retaliation_candidates)),
        counterevidence_summary=tuple(dict.fromkeys(counterevidence)),
        uncertainty_markers=tuple(dict.fromkeys(uncertainty_markers)),
        no_safe_dynamic_claim=no_safe_dynamic_claim,
        dependency_model_underconstrained=dependency_underconstrained,
        tone_shortcut_forbidden_applied=tone_shortcut_forbidden_applied,
        legitimacy_boundary_underconstrained=legitimacy_underconstrained,
        justification_links=tuple(
            dict.fromkeys(
                (
                    f"event_count:{len(events)}",
                    f"dominant_dynamic_type:{dominant.value}",
                    f"directionality:{directionality_kind.value}",
                    f"rupture_status:{rupture_status.value}",
                    f"prior_carry_applied:{'yes' if rupture_carry_markers else 'no'}",
                    f"coercion_candidates:{len(coercion_candidates)}",
                    f"hostility_candidates:{len(hostility_candidates)}",
                    "o04_structural_basis_only",
                )
            )
        ),
        provenance="o04.rupture_hostility_coercion.policy",
        source_lineage=source_lineage,
        last_update_provenance="o04.rupture_hostility_coercion.policy",
    )
    gate = _build_gate(state=state, directionality_kind=directionality_kind)
    scope_marker = O04ScopeMarker(
        scope="rt01_hosted_o04_first_slice",
        rt01_hosted_only=True,
        o04_first_slice_only=True,
        r05_not_implemented=True,
        v_line_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="bounded o04 slice; r05/v-line/p04 remain open seams",
    )
    telemetry = O04Telemetry(
        interaction_model_id=state.interaction_model_id,
        tick_index=tick_index,
        dynamic_type=dominant,
        rupture_status=state.rupture_status,
        severity_band=top_severity,
        certainty_band=top_certainty,
        directionality_kind=directionality_kind,
        leverage_surface=_dominant_leverage_surface(tuple(links)),
        legitimacy_hint_status=_dominant_legitimacy_hint(tuple(links)),
        coercion_candidate_count=len(state.coercion_candidates),
        hostility_candidate_count=len(state.hostility_candidates),
        no_safe_dynamic_claim=state.no_safe_dynamic_claim,
        dependency_model_underconstrained=state.dependency_model_underconstrained,
        downstream_consumer_ready=gate.dynamic_contract_consumer_ready,
    )
    return O04DynamicResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=(
            "o04 produced bounded structural rupture/hostility/coercion dynamics from typed actor-target events, "
            "leverage surfaces, directionality and legitimacy hints"
        ),
    )


def _build_gate(
    *,
    state: O04DynamicModel,
    directionality_kind: O04DirectionalityKind,
) -> O04DynamicGateDecision:
    coercive_structure_candidate = bool(state.coercion_candidates)
    rupture_risk_active = state.rupture_status in {
        O04RuptureStatus.RUPTURE_RISK_ONLY,
        O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE,
        O04RuptureStatus.DEESCALATED_BUT_NOT_CLOSED,
    }
    directionality_ready = directionality_kind is not O04DirectionalityKind.DIRECTIONALITY_AMBIGUOUS
    dynamic_contract_ready = bool(
        not state.no_safe_dynamic_claim
        and (
            coercive_structure_candidate
            or rupture_risk_active
            or bool(state.hostility_candidates)
        )
    )
    protective_handoff_ready = bool(
        dynamic_contract_ready
        and directionality_ready
        and (
            coercive_structure_candidate
            or state.rupture_status is O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE
        )
    )
    restrictions: list[str] = []
    if state.no_safe_dynamic_claim:
        restrictions.append("no_safe_dynamic_claim")
    if coercive_structure_candidate:
        restrictions.append("coercive_structure_candidate")
    if rupture_risk_active:
        restrictions.append("rupture_risk_active")
    if state.legitimacy_boundary_underconstrained:
        restrictions.append("legitimacy_underconstrained")
    if not directionality_ready:
        restrictions.append("directionality_ambiguous")
    if state.tone_shortcut_forbidden_applied:
        restrictions.append("tone_shortcut_forbidden_applied")
    if state.dependency_model_underconstrained:
        restrictions.append("dependency_model_underconstrained")
    return O04DynamicGateDecision(
        dynamic_contract_consumer_ready=dynamic_contract_ready,
        directionality_consumer_ready=directionality_ready,
        protective_handoff_consumer_ready=protective_handoff_ready,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="o04 gate exposes bounded dynamic-contract, directionality and protective-handoff readiness",
    )


def _build_no_signal_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> O04DynamicResult:
    state = O04DynamicModel(
        interaction_model_id=f"o04-dynamic:{tick_id}",
        agent_refs=(),
        directional_links=(),
        rupture_status=O04RuptureStatus.NO_RUPTURE_BASIS,
        hostility_candidates=(),
        coercion_candidates=(),
        retaliation_candidates=(),
        counterevidence_summary=(),
        uncertainty_markers=("no_interaction_events", "no_safe_dynamic_claim"),
        no_safe_dynamic_claim=True,
        dependency_model_underconstrained=True,
        tone_shortcut_forbidden_applied=False,
        legitimacy_boundary_underconstrained=True,
        justification_links=("event_count:0", "no_safe_dynamic_claim"),
        provenance="o04.rupture_hostility_coercion.no_signal",
        source_lineage=source_lineage,
        last_update_provenance="o04.rupture_hostility_coercion.no_signal",
    )
    gate = O04DynamicGateDecision(
        dynamic_contract_consumer_ready=False,
        directionality_consumer_ready=False,
        protective_handoff_consumer_ready=False,
        restrictions=(
            "no_safe_dynamic_claim",
            "directionality_ambiguous",
            "dependency_model_underconstrained",
        ),
        reason="o04 requires typed multi-agent structural events; no safe dynamic claim available",
    )
    scope_marker = O04ScopeMarker(
        scope="rt01_hosted_o04_first_slice",
        rt01_hosted_only=True,
        o04_first_slice_only=True,
        r05_not_implemented=True,
        v_line_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="o04 no-signal fallback",
    )
    telemetry = O04Telemetry(
        interaction_model_id=state.interaction_model_id,
        tick_index=tick_index,
        dynamic_type=O04DynamicType.AMBIGUOUS_PRESSURE,
        rupture_status=state.rupture_status,
        severity_band=O04SeverityBand.LOW,
        certainty_band=O04CertaintyBand.WEAK,
        directionality_kind=O04DirectionalityKind.DIRECTIONALITY_AMBIGUOUS,
        leverage_surface=O04LeverageSurfaceKind.NONE_DETECTED,
        legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN,
        coercion_candidate_count=0,
        hostility_candidate_count=0,
        no_safe_dynamic_claim=True,
        dependency_model_underconstrained=True,
        downstream_consumer_ready=False,
    )
    return O04DynamicResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    source_lineage: tuple[str, ...],
) -> O04DynamicResult:
    state = O04DynamicModel(
        interaction_model_id=f"o04-dynamic:{tick_id}",
        agent_refs=(),
        directional_links=(),
        rupture_status=O04RuptureStatus.NO_RUPTURE_BASIS,
        hostility_candidates=(),
        coercion_candidates=(),
        retaliation_candidates=(),
        counterevidence_summary=(),
        uncertainty_markers=("o04_disabled", "no_safe_dynamic_claim"),
        no_safe_dynamic_claim=True,
        dependency_model_underconstrained=True,
        tone_shortcut_forbidden_applied=False,
        legitimacy_boundary_underconstrained=True,
        justification_links=("o04_disabled",),
        provenance="o04.rupture_hostility_coercion.disabled",
        source_lineage=source_lineage,
        last_update_provenance="o04.rupture_hostility_coercion.disabled",
    )
    gate = O04DynamicGateDecision(
        dynamic_contract_consumer_ready=False,
        directionality_consumer_ready=False,
        protective_handoff_consumer_ready=False,
        restrictions=(
            "o04_disabled",
            "no_safe_dynamic_claim",
            "directionality_ambiguous",
        ),
        reason="o04 rupture/hostility/coercion modeling disabled in ablation context",
    )
    scope_marker = O04ScopeMarker(
        scope="rt01_hosted_o04_first_slice",
        rt01_hosted_only=True,
        o04_first_slice_only=True,
        r05_not_implemented=True,
        v_line_not_implemented=True,
        p04_not_implemented=True,
        repo_wide_adoption=False,
        reason="o04 disabled path",
    )
    telemetry = O04Telemetry(
        interaction_model_id=state.interaction_model_id,
        tick_index=tick_index,
        dynamic_type=O04DynamicType.AMBIGUOUS_PRESSURE,
        rupture_status=state.rupture_status,
        severity_band=O04SeverityBand.LOW,
        certainty_band=O04CertaintyBand.WEAK,
        directionality_kind=O04DirectionalityKind.DIRECTIONALITY_AMBIGUOUS,
        leverage_surface=O04LeverageSurfaceKind.NONE_DETECTED,
        legitimacy_hint_status=O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN,
        coercion_candidate_count=0,
        hostility_candidate_count=0,
        no_safe_dynamic_claim=True,
        dependency_model_underconstrained=True,
        downstream_consumer_ready=False,
    )
    return O04DynamicResult(
        state=state,
        gate=gate,
        scope_marker=scope_marker,
        telemetry=telemetry,
        reason=gate.reason,
    )


def _infer_leverage_surface(event: O04InteractionEventInput) -> O04LeverageSurfaceKind:
    if event.blocked_option_present:
        return O04LeverageSurfaceKind.BLOCKED_OPTION
    if event.sanction_power_present and event.threatened_loss_present:
        return O04LeverageSurfaceKind.SANCTION_THREAT
    if event.access_withdrawal_present and event.dependency_surface_present:
        return O04LeverageSurfaceKind.DEPENDENCY_WITHDRAWAL
    if event.access_withdrawal_present:
        return O04LeverageSurfaceKind.ACCESS_WITHDRAWAL
    if event.resource_control_present:
        return O04LeverageSurfaceKind.RESOURCE_CONTROL
    if event.commitment_break_marker:
        return O04LeverageSurfaceKind.COMMITMENT_LEVERAGE
    if event.exclusion_marker:
        return O04LeverageSurfaceKind.EXCLUSION_CHANNEL
    return O04LeverageSurfaceKind.NONE_DETECTED


def _event_directionality(event: O04InteractionEventInput) -> O04DirectionalityKind:
    if event.actor_ref and event.target_ref and event.actor_ref != event.target_ref:
        return O04DirectionalityKind.ONE_WAY
    return O04DirectionalityKind.DIRECTIONALITY_AMBIGUOUS


def _classify_event_dynamic_type(
    event: O04InteractionEventInput,
    *,
    has_structure: bool,
) -> O04DynamicType:
    if (
        has_structure
        and event.blocked_option_present
        and event.threatened_loss_present
        and (event.dependency_surface_present or event.resource_control_present or event.sanction_power_present)
    ):
        if (
            event.legitimacy_hint_status is O04LegitimacyHintStatus.LEGITIMACY_SUPPORTED
            and not event.sanction_power_present
        ):
            if event.refusal_marker:
                return O04DynamicType.BOUNDARY_ENFORCEMENT_BOUNDED
            return O04DynamicType.HARD_BARGAINING
        if event.refusal_marker:
            return O04DynamicType.FORCED_COMPLIANCE_CANDIDATE
        return O04DynamicType.COERCIVE_PRESSURE_CANDIDATE
    if event.exclusion_marker and (event.access_withdrawal_present or event.blocked_option_present):
        return O04DynamicType.EXCLUSION_SEQUENCE_CANDIDATE
    if event.commitment_break_marker and event.escalation_shift_marker:
        return O04DynamicType.RETALIATORY_ESCALATION_CANDIDATE
    if has_structure and event.legitimacy_hint_status is O04LegitimacyHintStatus.LEGITIMACY_SUPPORTED:
        if event.refusal_marker:
            return O04DynamicType.BOUNDARY_ENFORCEMENT_BOUNDED
        return O04DynamicType.HARD_BARGAINING
    if has_structure:
        return O04DynamicType.AMBIGUOUS_PRESSURE
    if event.escalation_shift_marker or event.speech_act_kind in {"harsh_statement", "aggressive_tone"}:
        return O04DynamicType.HOSTILITY_CANDIDATE
    return O04DynamicType.DISAGREEMENT_ONLY


def _severity_for_event(
    *,
    event: O04InteractionEventInput,
    dynamic_type: O04DynamicType,
) -> O04SeverityBand:
    if dynamic_type in {
        O04DynamicType.FORCED_COMPLIANCE_CANDIDATE,
        O04DynamicType.RETALIATORY_ESCALATION_CANDIDATE,
    }:
        return O04SeverityBand.HIGH
    if dynamic_type in {
        O04DynamicType.COERCIVE_PRESSURE_CANDIDATE,
        O04DynamicType.EXCLUSION_SEQUENCE_CANDIDATE,
        O04DynamicType.RUPTURE_ACTIVE,
        O04DynamicType.RUPTURE_RISK,
    }:
        return O04SeverityBand.MODERATE
    if event.escalation_shift_marker:
        return O04SeverityBand.MODERATE
    return O04SeverityBand.LOW


def _certainty_for_event(
    *,
    event: O04InteractionEventInput,
    dynamic_type: O04DynamicType,
    has_structure: bool,
    directionality: O04DirectionalityKind,
) -> O04CertaintyBand:
    if not has_structure:
        return O04CertaintyBand.WEAK
    if dynamic_type in {
        O04DynamicType.COERCIVE_PRESSURE_CANDIDATE,
        O04DynamicType.FORCED_COMPLIANCE_CANDIDATE,
    } and directionality is not O04DirectionalityKind.DIRECTIONALITY_AMBIGUOUS:
        if event.legitimacy_hint_status in {
            O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
            O04LegitimacyHintStatus.LEGITIMACY_CONTESTED,
        }:
            return O04CertaintyBand.STRONG
    return O04CertaintyBand.BOUNDED


def _directionality_kind(links: tuple[O04DynamicLink, ...]) -> O04DirectionalityKind:
    pairs = {
        (link.actor_ref, link.target_ref)
        for link in links
        if link.actor_ref and link.target_ref and link.actor_ref != link.target_ref
    }
    if not pairs:
        return O04DirectionalityKind.DIRECTIONALITY_AMBIGUOUS
    actors = {pair[0] for pair in pairs}
    targets = {pair[1] for pair in pairs}
    reciprocal = any((target, actor) in pairs for actor, target in pairs)
    if len(pairs) >= 3 and (len(actors) >= 2 and len(targets) >= 2):
        return O04DirectionalityKind.CHAIN_LIKE
    if reciprocal:
        if len(actors) != len(targets):
            return O04DirectionalityKind.ASYMMETRIC_MUTUAL
        return O04DirectionalityKind.MUTUAL
    return O04DirectionalityKind.ONE_WAY


def _rupture_status(
    *,
    repeated_withdrawal_count: int,
    repair_attempt_count: int,
    escalation_count: int,
    history_depth_band: str,
) -> O04RuptureStatus:
    if repeated_withdrawal_count >= 3 and escalation_count >= 1 and repair_attempt_count == 0:
        return O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE
    if repeated_withdrawal_count >= 2 and repair_attempt_count == 0:
        return O04RuptureStatus.RUPTURE_RISK_ONLY
    if repeated_withdrawal_count >= 1 and repair_attempt_count >= 1:
        return O04RuptureStatus.REPAIR_IN_PROGRESS
    if history_depth_band in {"medium", "deep"} and repeated_withdrawal_count >= 1:
        return O04RuptureStatus.RUPTURE_RISK_ONLY
    if repair_attempt_count >= 1 and escalation_count == 0:
        return O04RuptureStatus.DEESCALATED_BUT_NOT_CLOSED
    return O04RuptureStatus.NO_RUPTURE_BASIS


def _apply_prior_rupture_carry(
    *,
    prior_state: O04DynamicModel | None,
    current_status: O04RuptureStatus,
    repeated_withdrawal_count: int,
    repair_attempt_count: int,
    history_depth_band: str,
) -> tuple[O04RuptureStatus, tuple[str, ...]]:
    if not isinstance(prior_state, O04DynamicModel):
        return current_status, ()

    prior_status = prior_state.rupture_status
    if prior_status not in {
        O04RuptureStatus.RUPTURE_RISK_ONLY,
        O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE,
        O04RuptureStatus.DEESCALATED_BUT_NOT_CLOSED,
    }:
        return current_status, ()

    # Bounded carry: persist rupture-risk one step under continued withdrawal signals.
    if (
        current_status is O04RuptureStatus.NO_RUPTURE_BASIS
        and repeated_withdrawal_count >= 1
        and repair_attempt_count == 0
    ):
        return O04RuptureStatus.RUPTURE_RISK_ONLY, ("prior_rupture_carry_forward",)

    # Bounded downgrade: prior rupture-risk/active can soften under fresh repair evidence.
    if (
        prior_status in {
            O04RuptureStatus.RUPTURE_RISK_ONLY,
            O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE,
        }
        and repair_attempt_count >= 1
        and repeated_withdrawal_count == 0
    ):
        return O04RuptureStatus.DEESCALATED_BUT_NOT_CLOSED, ("prior_rupture_repair_downgrade",)

    # No sticky carry on thin single-step evidence: reset to current recompute.
    if current_status is O04RuptureStatus.NO_RUPTURE_BASIS and history_depth_band == "single":
        return current_status, ("prior_rupture_not_sticky",)

    return current_status, ()


def _dominant_dynamic_type(
    *,
    links: tuple[O04DynamicLink, ...],
    rupture_status: O04RuptureStatus,
    coercion_candidates: tuple[str, ...],
) -> O04DynamicType:
    if rupture_status is O04RuptureStatus.RUPTURE_ACTIVE_CANDIDATE:
        return O04DynamicType.RUPTURE_ACTIVE
    if rupture_status is O04RuptureStatus.RUPTURE_RISK_ONLY:
        return O04DynamicType.RUPTURE_RISK
    if coercion_candidates:
        for link in links:
            if link.dynamic_type is O04DynamicType.FORCED_COMPLIANCE_CANDIDATE:
                return O04DynamicType.FORCED_COMPLIANCE_CANDIDATE
        return O04DynamicType.COERCIVE_PRESSURE_CANDIDATE
    if links:
        return links[0].dynamic_type
    return O04DynamicType.AMBIGUOUS_PRESSURE


def _top_band(
    values: tuple[O04SeverityBand | O04CertaintyBand, ...],
) -> O04SeverityBand | O04CertaintyBand:
    if not values:
        return O04SeverityBand.LOW
    first = values[0]
    if isinstance(first, O04SeverityBand):
        if any(isinstance(item, O04SeverityBand) and item is O04SeverityBand.HIGH for item in values):
            return O04SeverityBand.HIGH
        if any(
            isinstance(item, O04SeverityBand) and item is O04SeverityBand.MODERATE
            for item in values
        ):
            return O04SeverityBand.MODERATE
        return O04SeverityBand.LOW
    if any(isinstance(item, O04CertaintyBand) and item is O04CertaintyBand.STRONG for item in values):
        return O04CertaintyBand.STRONG
    if any(
        isinstance(item, O04CertaintyBand) and item is O04CertaintyBand.BOUNDED
        for item in values
    ):
        return O04CertaintyBand.BOUNDED
    return O04CertaintyBand.WEAK


def _dominant_leverage_surface(links: tuple[O04DynamicLink, ...]) -> O04LeverageSurfaceKind:
    for link in links:
        if link.leverage_surface is not O04LeverageSurfaceKind.NONE_DETECTED:
            return link.leverage_surface
    return O04LeverageSurfaceKind.NONE_DETECTED


def _dominant_legitimacy_hint(
    links: tuple[O04DynamicLink, ...],
) -> O04LegitimacyHintStatus:
    priority = (
        O04LegitimacyHintStatus.LEGITIMACY_ABSENT,
        O04LegitimacyHintStatus.LEGITIMACY_CONTESTED,
        O04LegitimacyHintStatus.LEGITIMACY_SUPPORTED,
        O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN,
    )
    present = {link.legitimacy_hint_status for link in links}
    for item in priority:
        if item in present:
            return item
    return O04LegitimacyHintStatus.LEGITIMACY_UNKNOWN
