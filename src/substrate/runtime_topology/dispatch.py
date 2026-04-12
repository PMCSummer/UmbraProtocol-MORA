from __future__ import annotations

from dataclasses import replace

from substrate.contracts import (
    ContinuityDomainState,
    RegulationDomainState,
    RuntimeDomainsState,
    RuntimeState,
    ValidityDomainState,
)
from substrate.runtime_topology.models import (
    RuntimeDispatchRequest,
    RuntimeDispatchResult,
    RuntimeEpistemicCaseInput,
    RuntimeRegulationSharedDomainInput,
    RuntimeRouteClass,
)
from substrate.runtime_topology.policy import (
    build_minimal_runtime_topology_bundle,
    evaluate_runtime_dispatch_decision,
)
from substrate.runtime_tap_trace import trace_emit_active
from substrate.subject_tick import (
    SubjectTickContext,
    SubjectTickInput,
    execute_subject_tick,
    persist_subject_tick_result_via_f01,
)


def _merge_epistemic_case_input(
    *,
    tick_input: SubjectTickInput,
    context: SubjectTickContext,
    epistemic_case_input: RuntimeEpistemicCaseInput | None,
) -> tuple[SubjectTickInput, SubjectTickContext]:
    if epistemic_case_input is None:
        return tick_input, context

    tick_updates: dict[str, object] = {}
    if epistemic_case_input.content is not None:
        tick_updates["epistemic_content"] = epistemic_case_input.content
    if epistemic_case_input.source_id is not None:
        tick_updates["epistemic_source_id"] = epistemic_case_input.source_id
    if epistemic_case_input.source_class is not None:
        tick_updates["epistemic_source_class"] = epistemic_case_input.source_class
    if epistemic_case_input.modality is not None:
        tick_updates["epistemic_modality"] = epistemic_case_input.modality
    if epistemic_case_input.confidence_hint is not None:
        tick_updates["epistemic_confidence_hint"] = epistemic_case_input.confidence_hint
    if epistemic_case_input.support_note is not None:
        tick_updates["epistemic_support_note"] = epistemic_case_input.support_note
    if epistemic_case_input.contestation_note is not None:
        tick_updates["epistemic_contestation_note"] = epistemic_case_input.contestation_note
    if epistemic_case_input.claim_key is not None:
        tick_updates["epistemic_claim_key"] = epistemic_case_input.claim_key
    if epistemic_case_input.claim_polarity is not None:
        tick_updates["epistemic_claim_polarity"] = epistemic_case_input.claim_polarity

    context_updates: dict[str, object] = {}
    if epistemic_case_input.require_observation is not None:
        context_updates["require_epistemic_observation"] = epistemic_case_input.require_observation
    if epistemic_case_input.prior_units is not None:
        context_updates["prior_epistemic_units"] = epistemic_case_input.prior_units

    merged_tick_input = replace(tick_input, **tick_updates) if tick_updates else tick_input
    merged_context = replace(context, **context_updates) if context_updates else context
    return merged_tick_input, merged_context


def _build_seeded_prior_runtime_state(
    regulation_input: RuntimeRegulationSharedDomainInput,
) -> RuntimeState:
    return RuntimeState(
        domains=RuntimeDomainsState(
            regulation=RegulationDomainState(
                pressure_level=regulation_input.pressure_level
                if regulation_input.pressure_level is not None
                else 0.45,
                escalation_stage=regulation_input.escalation_stage or "steady",
                override_scope=regulation_input.override_scope or "narrow",
                no_strong_override_claim=(
                    regulation_input.no_strong_override_claim
                    if regulation_input.no_strong_override_claim is not None
                    else False
                ),
                gate_accepted=(
                    regulation_input.gate_accepted
                    if regulation_input.gate_accepted is not None
                    else True
                ),
                source_state_ref=regulation_input.source_state_ref
                or "runtime_topology.regulation_shared_domain.seed",
                updated_by_phase="R04",
                last_update_provenance="runtime_topology.dispatch.regulation_shared_domain_input",
            ),
            continuity=ContinuityDomainState(
                c04_mode_claim="continue_stream",
                c04_selected_mode="continue_stream",
                mode_legitimacy=True,
                endogenous_tick_allowed=True,
                arbitration_confidence=0.8,
                source_state_ref="runtime_topology.regulation_shared_domain.seed",
                updated_by_phase="C04",
                last_update_provenance="runtime_topology.dispatch.regulation_shared_domain_input",
            ),
            validity=ValidityDomainState(
                c05_action_claim="allow_continue",
                c05_validity_action="allow_continue",
                legality_reuse_allowed=True,
                revalidation_required=False,
                no_safe_reuse=False,
                selective_scope_targets=(),
                source_state_ref="runtime_topology.regulation_shared_domain.seed",
                updated_by_phase="C05",
                last_update_provenance="runtime_topology.dispatch.regulation_shared_domain_input",
            ),
        )
    )


def _merge_regulation_shared_domain_input(
    *,
    context: SubjectTickContext,
    regulation_input: RuntimeRegulationSharedDomainInput | None,
) -> SubjectTickContext:
    if regulation_input is None:
        return context

    prior_runtime_state = (
        context.prior_runtime_state if isinstance(context.prior_runtime_state, RuntimeState) else None
    )
    if prior_runtime_state is None:
        prior_runtime_state = _build_seeded_prior_runtime_state(regulation_input)

    regulation_updates: dict[str, object] = {
        "updated_by_phase": "R04",
        "last_update_provenance": "runtime_topology.dispatch.regulation_shared_domain_input",
    }
    if regulation_input.pressure_level is not None:
        regulation_updates["pressure_level"] = regulation_input.pressure_level
    if regulation_input.escalation_stage is not None:
        regulation_updates["escalation_stage"] = regulation_input.escalation_stage
    if regulation_input.override_scope is not None:
        regulation_updates["override_scope"] = regulation_input.override_scope
    if regulation_input.no_strong_override_claim is not None:
        regulation_updates["no_strong_override_claim"] = regulation_input.no_strong_override_claim
    if regulation_input.gate_accepted is not None:
        regulation_updates["gate_accepted"] = regulation_input.gate_accepted
    if regulation_input.source_state_ref is not None:
        regulation_updates["source_state_ref"] = regulation_input.source_state_ref

    merged_regulation = replace(
        prior_runtime_state.domains.regulation,
        **regulation_updates,
    )
    merged_runtime_state = replace(
        prior_runtime_state,
        domains=replace(
            prior_runtime_state.domains,
            regulation=merged_regulation,
        ),
    )
    return replace(context, prior_runtime_state=merged_runtime_state)


def _materialize_tick_execution_inputs(
    request: RuntimeDispatchRequest,
) -> tuple[SubjectTickInput, SubjectTickContext]:
    context = request.context if isinstance(request.context, SubjectTickContext) else SubjectTickContext()
    tick_input, context = _merge_epistemic_case_input(
        tick_input=request.tick_input,
        context=context,
        epistemic_case_input=request.epistemic_case_input,
    )
    context = _merge_regulation_shared_domain_input(
        context=context,
        regulation_input=request.regulation_shared_domain_input,
    )
    return tick_input, context


def dispatch_runtime_tick(request: RuntimeDispatchRequest) -> RuntimeDispatchResult:
    if not isinstance(request, RuntimeDispatchRequest):
        raise TypeError("dispatch_runtime_tick requires RuntimeDispatchRequest")

    bundle = build_minimal_runtime_topology_bundle()
    tick_graph = bundle.tick_graph
    trace_emit_active(
        "runtime_topology",
        "enter",
        {
            "route_class": request.route_class.value,
            "runtime_entry": bundle.runtime_entry,
        },
    )
    decision = evaluate_runtime_dispatch_decision(request=request, bundle=bundle)
    topology_values = {
        "route_class": decision.route_class.value,
        "accepted": decision.accepted,
        "route_binding_consequence": decision.route_binding_consequence.value,
        "runtime_entry": bundle.runtime_entry,
        "reason": decision.reason,
    }
    trace_emit_active("runtime_topology", "decision", topology_values)
    if not decision.accepted:
        trace_emit_active(
            "runtime_topology",
            "blocked",
            topology_values,
            note="dispatch_rejected",
        )
        trace_emit_active("runtime_topology", "exit", topology_values, note="dispatch_return")
        return RuntimeDispatchResult(
            decision=decision,
            bundle=bundle,
            tick_graph=tick_graph,
            request=request,
            subject_tick_result=None,
            persist_transition=None,
            dispatch_lineage=("runtime_topology.dispatch_runtime_tick",),
        )

    tick_input, context = _materialize_tick_execution_inputs(request)
    effective_request = replace(
        request,
        tick_input=tick_input,
        context=context,
    )

    subject_tick_result = execute_subject_tick(
        tick_input=tick_input,
        context=context,
    )
    persist_transition = None
    if effective_request.persist_via_f01:
        persist_transition = persist_subject_tick_result_via_f01(
            result=subject_tick_result,
            runtime_state=effective_request.runtime_state,
            transition_id=effective_request.transition_id,
            requested_at=effective_request.requested_at,
            cause_chain=effective_request.cause_chain,
        )

    trace_emit_active("runtime_topology", "exit", topology_values, note="dispatch_return")
    return RuntimeDispatchResult(
        decision=decision,
        bundle=bundle,
        tick_graph=tick_graph,
        request=effective_request,
        subject_tick_result=subject_tick_result,
        persist_transition=persist_transition,
        dispatch_lineage=(
            "runtime_topology.dispatch_runtime_tick",
            f"route:{effective_request.route_class.value}",
            "execution_spine:RT01",
        ),
    )


def dispatch_rt01_production_tick(
    *,
    tick_input,
    context=None,
    persist_via_f01: bool = False,
    runtime_state=None,
    transition_id: str | None = None,
    requested_at: str | None = None,
    cause_chain: tuple[str, ...] = ("runtime-topology-dispatch",),
) -> RuntimeDispatchResult:
    return dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=tick_input,
            context=context,
            route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            allow_helper_route=False,
            allow_test_only_route=False,
            persist_via_f01=persist_via_f01,
            runtime_state=runtime_state,
            transition_id=transition_id,
            requested_at=requested_at,
            cause_chain=cause_chain,
        )
    )
