from __future__ import annotations

from substrate.runtime_topology.models import (
    RuntimeContourEdge,
    RuntimeContourNode,
    RuntimeDispatchDecision,
    RuntimeDispatchRequest,
    RuntimeRouteBindingConsequence,
    RuntimeDispatchRestriction,
    RuntimeRouteClass,
    RuntimeTickGraph,
    RuntimeTopologyBundle,
)
from substrate.subject_tick import SubjectTickContext


def build_minimal_runtime_tick_graph() -> RuntimeTickGraph:
    return RuntimeTickGraph(
        graph_id="rt01.minimal_runtime_tick_graph.v1",
        contour_id="rt01_subject_tick_contour",
        runtime_order=("R", "C01", "C02", "C03", "C04", "C05", "RT01"),
        nodes=(
            RuntimeContourNode(
                node_id="node.r04",
                phase_id="R04",
                authority_role="gating",
                computational_role="evaluator",
                surfaces=("domains.regulation", "r04.override_scope"),
                checkpoint_ids=("rt01.shared_runtime_domain_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.c04",
                phase_id="C04",
                authority_role="arbitration",
                computational_role="scheduler",
                surfaces=("domains.continuity", "c04.mode_legitimacy"),
                checkpoint_ids=("rt01.c04_mode_binding",),
            ),
            RuntimeContourNode(
                node_id="node.c05",
                phase_id="C05",
                authority_role="invalidation",
                computational_role="evaluator",
                surfaces=("domains.validity", "c05.legality_reuse_allowed"),
                checkpoint_ids=("rt01.c05_legality_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.world_adapter",
                phase_id="WORLD_SEAM",
                authority_role="external_seam",
                computational_role="adapter",
                surfaces=(
                    "world_adapter.observation",
                    "world_adapter.action",
                    "world_adapter.effect_feedback",
                ),
                checkpoint_ids=("rt01.world_seam_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.s_minimal",
                phase_id="S_MINIMAL",
                authority_role="boundary_attribution",
                computational_role="contour_contract",
                surfaces=(
                    "s_minimal_contour.boundary_state",
                    "s_minimal_contour.forbidden_shortcuts",
                    "s_minimal_contour.admission",
                ),
                checkpoint_ids=("rt01.s_minimal_contour_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.a_line",
                phase_id="A_MINIMAL",
                authority_role="affordance_capability_contract",
                computational_role="contour_contract",
                surfaces=(
                    "a_line_normalization.capability_state",
                    "a_line_normalization.forbidden_shortcuts",
                    "a_line_normalization.a04_readiness",
                ),
                checkpoint_ids=("rt01.a_line_normalization_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.m_minimal",
                phase_id="M_MINIMAL",
                authority_role="memory_lifecycle_contract",
                computational_role="contour_contract",
                surfaces=(
                    "m_minimal.lifecycle_state",
                    "m_minimal.forbidden_shortcuts",
                    "m_minimal.admission",
                ),
                checkpoint_ids=("rt01.m_minimal_contour_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.rt01",
                phase_id="RT01",
                authority_role="gating",
                computational_role="execution_spine",
                surfaces=(
                    "rt01.downstream_obedience_checkpoint",
                    "rt01.world_seam_checkpoint",
                    "rt01.world_entry_checkpoint",
                    "rt01.s_minimal_contour_checkpoint",
                    "rt01.a_line_normalization_checkpoint",
                    "rt01.m_minimal_contour_checkpoint",
                    "rt01.outcome_resolution_checkpoint",
                ),
                checkpoint_ids=(
                    "rt01.downstream_obedience_checkpoint",
                    "rt01.world_seam_checkpoint",
                    "rt01.world_entry_checkpoint",
                    "rt01.s_minimal_contour_checkpoint",
                    "rt01.a_line_normalization_checkpoint",
                    "rt01.m_minimal_contour_checkpoint",
                    "rt01.outcome_resolution_checkpoint",
                ),
            ),
            RuntimeContourNode(
                node_id="node.f01",
                phase_id="F01",
                authority_role="observability_only",
                computational_role="bridge_contract",
                surfaces=("transition.execute_transition",),
                checkpoint_ids=(),
            ),
        ),
        edges=(
            RuntimeContourEdge(source_phase="R04", target_phase="C04", relation="overrides_survival"),
            RuntimeContourEdge(source_phase="R04", target_phase="RT01", relation="modulates"),
            RuntimeContourEdge(source_phase="C04", target_phase="RT01", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="RT01", relation="gates"),
            RuntimeContourEdge(source_phase="WORLD_SEAM", target_phase="RT01", relation="requires"),
            RuntimeContourEdge(source_phase="WORLD_SEAM", target_phase="S_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="S_MINIMAL", target_phase="RT01", relation="requires"),
            RuntimeContourEdge(source_phase="S_MINIMAL", target_phase="A_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="WORLD_SEAM", target_phase="A_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="A_MINIMAL", target_phase="RT01", relation="requires"),
            RuntimeContourEdge(source_phase="A_MINIMAL", target_phase="M_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="S_MINIMAL", target_phase="M_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="WORLD_SEAM", target_phase="M_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="M_MINIMAL", target_phase="RT01", relation="requires"),
            RuntimeContourEdge(source_phase="RT01", target_phase="F01", relation="persists_via_f01"),
        ),
        mandatory_checkpoint_ids=(
            "rt01.c04_mode_binding",
            "rt01.c05_legality_checkpoint",
            "rt01.downstream_obedience_checkpoint",
            "rt01.world_seam_checkpoint",
            "rt01.world_entry_checkpoint",
            "rt01.s_minimal_contour_checkpoint",
            "rt01.a_line_normalization_checkpoint",
            "rt01.m_minimal_contour_checkpoint",
            "rt01.outcome_resolution_checkpoint",
        ),
        source_of_truth_surfaces=(
            "runtime_state.domains",
            "rt01.downstream_obedience_checkpoint",
            "world_adapter.state",
            "world_entry_contract.episode",
            "s_minimal_contour.boundary_state",
            "a_line_normalization.capability_state",
            "m_minimal.lifecycle_state",
        ),
        reason="minimal production runtime graph for bounded RT01 contour wiring",
    )


def build_minimal_runtime_topology_bundle() -> RuntimeTopologyBundle:
    tick_graph = build_minimal_runtime_tick_graph()
    return RuntimeTopologyBundle(
        bundle_id="runtime-topology-bundle.rt01.v1",
        contour_id=tick_graph.contour_id,
        runtime_entry="runtime_topology.dispatch_runtime_tick",
        execution_spine_phase="RT01",
        downstream_obedience_phase="RT01",
        shared_domain_paths=(
            "domains.regulation",
            "domains.continuity",
            "domains.validity",
        ),
        enforcement_hooks=(
            "dispatch_route_classification",
            "production_route_required",
            "test_only_ablation_guard",
            "dispatch_contract_required_for_lawful_production_use",
            "world_seam_presence_contract",
            "world_entry_admission_contract",
            "s_minimal_boundary_attribution_contract",
            "a_line_normalization_capability_contract",
            "m_minimal_memory_lifecycle_contract",
        ),
        f01_transition_route="subject_tick.persist_subject_tick_result_via_f01",
        tick_graph=tick_graph,
        reason="minimal bounded production topology for RT01 contour",
    )


def evaluate_runtime_dispatch_decision(
    request: RuntimeDispatchRequest,
    bundle: RuntimeTopologyBundle,
) -> RuntimeDispatchDecision:
    restrictions: list[RuntimeDispatchRestriction] = [
        RuntimeDispatchRestriction.DISPATCH_CONTRACT_MUST_BE_READ,
        RuntimeDispatchRestriction.TOPOLOGY_BOUND_TO_RT01_CONTOUR,
    ]
    route_class = request.route_class
    has_ablation = _context_has_ablation_flags(request.context)
    route_binding_consequence = RuntimeRouteBindingConsequence.LAWFUL_PRODUCTION_CONTOUR

    if route_class == RuntimeRouteClass.PRODUCTION_CONTOUR:
        if has_ablation:
            restrictions.append(RuntimeDispatchRestriction.PRODUCTION_ROUTE_FORBIDS_ABLATION_FLAGS)
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=RuntimeRouteBindingConsequence.LAWFUL_PRODUCTION_CONTOUR,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="production contour dispatch rejected because ablation flags are test-only",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )
    elif route_class == RuntimeRouteClass.HELPER_PATH:
        route_binding_consequence = RuntimeRouteBindingConsequence.NON_LAWFUL_HELPER_ROUTE
        restrictions.append(RuntimeDispatchRestriction.HELPER_ROUTE_NOT_LAWFUL_PRODUCTION)
        if not request.allow_helper_route:
            restrictions.append(RuntimeDispatchRestriction.PRODUCTION_ROUTE_REQUIRED)
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=route_binding_consequence,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="helper route rejected for production dispatch; explicit helper allowance required",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )
        if not request.allow_non_production_consumer_opt_in:
            restrictions.append(
                RuntimeDispatchRestriction.NON_PRODUCTION_ROUTE_REQUIRES_EXPLICIT_CONSUMER_OPT_IN
            )
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=route_binding_consequence,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="helper route rejected until downstream consumer explicitly opts in to non-production route contract",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )
    elif route_class == RuntimeRouteClass.TEST_ONLY_ABLATION:
        route_binding_consequence = RuntimeRouteBindingConsequence.TEST_ONLY_ABLATION_ROUTE
        if not request.allow_test_only_route:
            restrictions.append(RuntimeDispatchRestriction.TEST_ONLY_ROUTE_REQUIRES_EXPLICIT_ALLOW)
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=route_binding_consequence,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="test-only route rejected without explicit allow_test_only_route",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )
        if not has_ablation:
            restrictions.append(RuntimeDispatchRestriction.TEST_ONLY_ROUTE_REQUIRES_ABLATION_BASIS)
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=route_binding_consequence,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="test-only route rejected because no ablation flags are active",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )
        if not request.allow_non_production_consumer_opt_in:
            restrictions.append(
                RuntimeDispatchRestriction.NON_PRODUCTION_ROUTE_REQUIRES_EXPLICIT_CONSUMER_OPT_IN
            )
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=route_binding_consequence,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="test-only route rejected until downstream consumer explicitly opts in to non-production route contract",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )

    if request.persist_via_f01:
        if route_class != RuntimeRouteClass.PRODUCTION_CONTOUR:
            restrictions.append(RuntimeDispatchRestriction.NON_PRODUCTION_ROUTE_FORBIDS_F01_PERSISTENCE)
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=route_binding_consequence,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="non-production route cannot persist via f01 contour bridge",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )
        if (
            request.runtime_state is None
            or not request.transition_id
            or not request.requested_at
            or not request.cause_chain
        ):
            restrictions.append(RuntimeDispatchRestriction.PERSISTENCE_REQUIRES_F01_INPUTS)
            return RuntimeDispatchDecision(
                accepted=False,
                lawful_production_route=False,
                route_binding_consequence=route_binding_consequence,
                route_class=route_class,
                restrictions=tuple(dict.fromkeys(restrictions)),
                reason="persist_via_f01 requires runtime_state, transition_id, requested_at and cause_chain",
                requires_dispatch_entry=True,
                topology_ref=bundle.bundle_id,
            )

    return RuntimeDispatchDecision(
        accepted=True,
        lawful_production_route=route_class == RuntimeRouteClass.PRODUCTION_CONTOUR,
        route_binding_consequence=route_binding_consequence,
        route_class=route_class,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "lawful production runtime contour route accepted"
            if route_class == RuntimeRouteClass.PRODUCTION_CONTOUR
            else "non-production route accepted with explicit bounded allowance"
        ),
        requires_dispatch_entry=True,
        topology_ref=bundle.bundle_id,
    )


def _context_has_ablation_flags(context: SubjectTickContext | None) -> bool:
    if not isinstance(context, SubjectTickContext):
        return False
    return bool(
        context.disable_gate_application
        or context.disable_c04_mode_execution_binding
        or context.disable_c05_validity_enforcement
        or context.disable_downstream_obedience_enforcement
        or context.disable_s_minimal_enforcement
        or context.disable_m_minimal_enforcement
    )
