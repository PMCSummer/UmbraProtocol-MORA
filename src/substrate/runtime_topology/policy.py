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
        runtime_order=(
            "EPISTEMICS",
            "R",
            "C01",
            "C02",
            "C03",
            "C04",
            "C05",
            "S01",
            "S02",
            "S03",
            "S04",
            "S05",
            "T01",
            "T02",
            "T03",
            "T04",
            "O01",
            "O02",
            "RT01",
        ),
        nodes=(
            RuntimeContourNode(
                node_id="node.epistemics",
                phase_id="EPISTEMICS",
                authority_role="gating",
                computational_role="grounded_classifier",
                surfaces=(
                    "epistemics.grounded_unit",
                    "epistemics.downstream_allowance",
                ),
                checkpoint_ids=("rt01.epistemic_admission_checkpoint",),
            ),
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
                node_id="node.n_minimal",
                phase_id="N_MINIMAL",
                authority_role="narrative_commitment_contract",
                computational_role="contour_contract",
                surfaces=(
                    "n_minimal.commitment_state",
                    "n_minimal.forbidden_shortcuts",
                    "n_minimal.admission",
                ),
                checkpoint_ids=("rt01.n_minimal_contour_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.s01_efference_copy",
                phase_id="S01",
                authority_role="computational",
                computational_role="evaluator",
                surfaces=(
                    "s01_efference_copy.latest_comparison",
                    "s01_efference_copy.pending_predictions",
                    "s01_efference_copy.prediction_validity",
                ),
                checkpoint_ids=("rt01.s01_efference_copy_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.s02_prediction_boundary",
                phase_id="S02",
                authority_role="prediction_boundary_seam_contract",
                computational_role="boundary_ledger_aggregator",
                surfaces=(
                    "s02_prediction_boundary.seam_ledger",
                    "s02_prediction_boundary.controllability_vs_predictability",
                    "s02_prediction_boundary.mixed_source_boundary",
                ),
                checkpoint_ids=("rt01.s02_prediction_boundary_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.s03_ownership_weighted_learning",
                phase_id="S03",
                authority_role="modulatory_only",
                computational_role="learning_update_router",
                surfaces=(
                    "s03_ownership_weighted_learning.learning_attribution_ledger",
                    "s03_ownership_weighted_learning.target_update_routes",
                    "s03_ownership_weighted_learning.freeze_or_defer_state",
                ),
                checkpoint_ids=(
                    "rt01.s03_ownership_weighted_learning_checkpoint",
                ),
            ),
            RuntimeContourNode(
                node_id="node.s04_interoceptive_self_binding",
                phase_id="S04",
                authority_role="self_binding_contract",
                computational_role="interoceptive_binding_ledger",
                surfaces=(
                    "s04_interoceptive_self_binding.binding_entries",
                    "s04_interoceptive_self_binding.core_channels",
                    "s04_interoceptive_self_binding.contested_channels",
                ),
                checkpoint_ids=("rt01.s04_interoceptive_self_binding_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.s05_multi_cause_attribution_factorization",
                phase_id="S05",
                authority_role="factorized_attribution_contract",
                computational_role="bounded_multi_cause_factorizer",
                surfaces=(
                    "s05_multi_cause_attribution_factorization.factorization_packet",
                    "s05_multi_cause_attribution_factorization.compatibility_filtering",
                    "s05_multi_cause_attribution_factorization.residual_discipline",
                    "s05_multi_cause_attribution_factorization.downstream_route_contract",
                ),
                checkpoint_ids=("rt01.s05_multi_cause_attribution_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.t01_semantic_field",
                phase_id="T01",
                authority_role="semantic_field_contract",
                computational_role="preverbal_scene_compiler",
                surfaces=(
                    "t01_semantic_field.active_scene",
                    "t01_semantic_field.preverbal_consumer_contract",
                ),
                checkpoint_ids=("rt01.t01_semantic_field_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.t02_relation_binding",
                phase_id="T02",
                authority_role="relation_binding_constraint_contract",
                computational_role="preverbal_constraint_propagator",
                surfaces=(
                    "t02_relation_binding.constrained_scene",
                    "t02_relation_binding.constraint_objects",
                    "t02_relation_binding.propagation_records",
                    "t02_relation_binding.raw_vs_propagated_distinction",
                    "t02_relation_binding.preverbal_consumer_contract",
                ),
                checkpoint_ids=(
                    "rt01.t02_relation_binding_checkpoint",
                    "rt01.t02_raw_vs_propagated_integrity_checkpoint",
                ),
            ),
            RuntimeContourNode(
                node_id="node.t03_hypothesis_competition",
                phase_id="T03",
                authority_role="hypothesis_competition_contract",
                computational_role="preverbal_convergence_resolver",
                surfaces=(
                    "t03_hypothesis_competition.competition_ledger",
                    "t03_hypothesis_competition.publication_frontier",
                    "t03_hypothesis_competition.convergence_state",
                    "t03_hypothesis_competition.preverbal_consumer_contract",
                ),
                checkpoint_ids=("rt01.t03_hypothesis_competition_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.t04_attention_schema",
                phase_id="T04",
                authority_role="attention_schema_focus_ownership_contract",
                computational_role="preverbal_focus_ownership_model",
                surfaces=(
                    "t04_attention_schema.focus_targets",
                    "t04_attention_schema.peripheral_targets",
                    "t04_attention_schema.focus_ownership",
                    "t04_attention_schema.preverbal_consumer_contract",
                ),
                checkpoint_ids=("rt01.t04_attention_schema_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.o01_other_entity_model",
                phase_id="O01",
                authority_role="other_entity_model_contract",
                computational_role="bounded_other_entity_modeling",
                surfaces=(
                    "o01_other_entity_model.entities",
                    "o01_other_entity_model.revision_history",
                    "o01_other_entity_model.entity_individuation",
                    "o01_other_entity_model.uncertainty_partition",
                ),
                checkpoint_ids=("rt01.o01_other_entity_model_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.o02_intersubjective_allostasis",
                phase_id="O02",
                authority_role="intersubjective_regulation_contract",
                computational_role="bounded_interactional_allostasis",
                surfaces=(
                    "o02_intersubjective_allostasis.regulation_state",
                    "o02_intersubjective_allostasis.regulation_levers",
                    "o02_intersubjective_allostasis.boundary_protection_status",
                    "o02_intersubjective_allostasis.repair_pressure",
                ),
                checkpoint_ids=("rt01.o02_intersubjective_allostasis_checkpoint",),
            ),
            RuntimeContourNode(
                node_id="node.rt01",
                phase_id="RT01",
                authority_role="gating",
                computational_role="execution_spine",
                surfaces=(
                    "rt01.epistemic_admission_checkpoint",
                    "rt01.downstream_obedience_checkpoint",
                    "rt01.world_seam_checkpoint",
                    "rt01.world_entry_checkpoint",
                    "rt01.s_minimal_contour_checkpoint",
                    "rt01.a_line_normalization_checkpoint",
                    "rt01.m_minimal_contour_checkpoint",
                    "rt01.n_minimal_contour_checkpoint",
                    "rt01.t01_semantic_field_checkpoint",
                    "rt01.s02_prediction_boundary_checkpoint",
                    "rt01.s04_interoceptive_self_binding_checkpoint",
                    "rt01.s05_multi_cause_attribution_checkpoint",
                    "rt01.t02_relation_binding_checkpoint",
                    "rt01.t02_raw_vs_propagated_integrity_checkpoint",
                    "rt01.t03_hypothesis_competition_checkpoint",
                    "rt01.t04_attention_schema_checkpoint",
                    "rt01.o01_other_entity_model_checkpoint",
                    "rt01.o02_intersubjective_allostasis_checkpoint",
                    "rt01.outcome_resolution_checkpoint",
                ),
                checkpoint_ids=(
                    "rt01.epistemic_admission_checkpoint",
                    "rt01.downstream_obedience_checkpoint",
                    "rt01.world_seam_checkpoint",
                    "rt01.world_entry_checkpoint",
                    "rt01.s_minimal_contour_checkpoint",
                    "rt01.a_line_normalization_checkpoint",
                    "rt01.m_minimal_contour_checkpoint",
                    "rt01.n_minimal_contour_checkpoint",
                    "rt01.t01_semantic_field_checkpoint",
                    "rt01.s02_prediction_boundary_checkpoint",
                    "rt01.s04_interoceptive_self_binding_checkpoint",
                    "rt01.s05_multi_cause_attribution_checkpoint",
                    "rt01.t02_relation_binding_checkpoint",
                    "rt01.t02_raw_vs_propagated_integrity_checkpoint",
                    "rt01.t03_hypothesis_competition_checkpoint",
                    "rt01.t04_attention_schema_checkpoint",
                    "rt01.o01_other_entity_model_checkpoint",
                    "rt01.o02_intersubjective_allostasis_checkpoint",
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
            RuntimeContourEdge(source_phase="EPISTEMICS", target_phase="R04", relation="gates"),
            RuntimeContourEdge(source_phase="R04", target_phase="C04", relation="overrides_survival"),
            RuntimeContourEdge(source_phase="R04", target_phase="RT01", relation="modulates"),
            RuntimeContourEdge(source_phase="C04", target_phase="RT01", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="RT01", relation="gates"),
            RuntimeContourEdge(source_phase="C04", target_phase="S01", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="S01", relation="requests_revalidation"),
            RuntimeContourEdge(source_phase="C04", target_phase="S02", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="S02", relation="requests_revalidation"),
            RuntimeContourEdge(source_phase="S01", target_phase="RT01", relation="modulates"),
            RuntimeContourEdge(source_phase="S01", target_phase="S02", relation="requires"),
            RuntimeContourEdge(source_phase="S02", target_phase="S03", relation="requires"),
            RuntimeContourEdge(source_phase="C04", target_phase="S03", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="S03", relation="requests_revalidation"),
            RuntimeContourEdge(source_phase="S03", target_phase="S04", relation="requires"),
            RuntimeContourEdge(source_phase="C04", target_phase="S04", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="S04", relation="requests_revalidation"),
            RuntimeContourEdge(source_phase="S04", target_phase="S05", relation="requires"),
            RuntimeContourEdge(source_phase="C04", target_phase="S05", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="S05", relation="requests_revalidation"),
            RuntimeContourEdge(source_phase="S05", target_phase="S_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="S03", target_phase="T01", relation="modulates"),
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
            RuntimeContourEdge(source_phase="S_MINIMAL", target_phase="N_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="A_MINIMAL", target_phase="N_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="M_MINIMAL", target_phase="N_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="WORLD_SEAM", target_phase="N_MINIMAL", relation="requires"),
            RuntimeContourEdge(source_phase="N_MINIMAL", target_phase="T01", relation="requires"),
            RuntimeContourEdge(source_phase="S_MINIMAL", target_phase="T01", relation="requires"),
            RuntimeContourEdge(source_phase="M_MINIMAL", target_phase="T01", relation="requires"),
            RuntimeContourEdge(source_phase="A_MINIMAL", target_phase="T01", relation="requires"),
            RuntimeContourEdge(source_phase="WORLD_SEAM", target_phase="T01", relation="requires"),
            RuntimeContourEdge(source_phase="T01", target_phase="T02", relation="requires"),
            RuntimeContourEdge(source_phase="T02", target_phase="T03", relation="requires"),
            RuntimeContourEdge(source_phase="T03", target_phase="T04", relation="requires"),
            RuntimeContourEdge(source_phase="T04", target_phase="O01", relation="requires"),
            RuntimeContourEdge(source_phase="O01", target_phase="O02", relation="modulates"),
            RuntimeContourEdge(source_phase="S05", target_phase="O02", relation="modulates"),
            RuntimeContourEdge(source_phase="T03", target_phase="O02", relation="modulates"),
            RuntimeContourEdge(source_phase="R04", target_phase="O02", relation="gates"),
            RuntimeContourEdge(source_phase="C04", target_phase="O02", relation="arbitrates"),
            RuntimeContourEdge(source_phase="C05", target_phase="O02", relation="requests_revalidation"),
            RuntimeContourEdge(source_phase="O02", target_phase="RT01", relation="requires"),
            RuntimeContourEdge(source_phase="RT01", target_phase="F01", relation="persists_via_f01"),
        ),
        mandatory_checkpoint_ids=(
            "rt01.epistemic_admission_checkpoint",
            "rt01.c04_mode_binding",
            "rt01.c05_legality_checkpoint",
            "rt01.downstream_obedience_checkpoint",
            "rt01.world_seam_checkpoint",
            "rt01.world_entry_checkpoint",
            "rt01.s_minimal_contour_checkpoint",
            "rt01.a_line_normalization_checkpoint",
            "rt01.m_minimal_contour_checkpoint",
            "rt01.n_minimal_contour_checkpoint",
            "rt01.s01_efference_copy_checkpoint",
            "rt01.s02_prediction_boundary_checkpoint",
            "rt01.s03_ownership_weighted_learning_checkpoint",
            "rt01.s04_interoceptive_self_binding_checkpoint",
            "rt01.s05_multi_cause_attribution_checkpoint",
            "rt01.t01_semantic_field_checkpoint",
            "rt01.t02_relation_binding_checkpoint",
            "rt01.t02_raw_vs_propagated_integrity_checkpoint",
            "rt01.t03_hypothesis_competition_checkpoint",
            "rt01.t04_attention_schema_checkpoint",
            "rt01.o01_other_entity_model_checkpoint",
            "rt01.o02_intersubjective_allostasis_checkpoint",
            "rt01.outcome_resolution_checkpoint",
        ),
        source_of_truth_surfaces=(
            "epistemics.grounded_unit",
            "epistemics.downstream_allowance",
            "runtime_state.domains",
            "rt01.downstream_obedience_checkpoint",
            "world_adapter.state",
            "world_entry_contract.episode",
            "s_minimal_contour.boundary_state",
            "a_line_normalization.capability_state",
            "m_minimal.lifecycle_state",
            "n_minimal.commitment_state",
            "s01_efference_copy.latest_comparison",
            "s02_prediction_boundary.seam_ledger",
            "s02_prediction_boundary.controllability_vs_predictability",
            "s03_ownership_weighted_learning.learning_attribution_ledger",
            "s03_ownership_weighted_learning.target_update_routes",
            "s03_ownership_weighted_learning.freeze_or_defer_state",
            "s04_interoceptive_self_binding.binding_entries",
            "s04_interoceptive_self_binding.core_channels",
            "s04_interoceptive_self_binding.contested_channels",
            "s05_multi_cause_attribution_factorization.factorization_packet",
            "s05_multi_cause_attribution_factorization.compatibility_filtering",
            "s05_multi_cause_attribution_factorization.residual_discipline",
            "t01_semantic_field.active_scene",
            "t02_relation_binding.constrained_scene",
            "t02_relation_binding.raw_vs_propagated_distinction",
            "t03_hypothesis_competition.competition_ledger",
            "t03_hypothesis_competition.publication_frontier",
            "t04_attention_schema.focus_ownership",
            "t04_attention_schema.focus_targets",
            "o01_other_entity_model.entities",
            "o01_other_entity_model.entity_individuation",
            "o02_intersubjective_allostasis.regulation_state",
            "o02_intersubjective_allostasis.boundary_protection_status",
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
            "n_minimal_narrative_commitment_contract",
            "s01_efference_copy_comparator_contract",
            "s02_prediction_boundary_self_vs_world_seam_contract",
            "s03_ownership_weighted_learning_packet_routing_contract",
            "s04_interoceptive_self_binding_binding_ledger_contract",
            "s05_multi_cause_attribution_factorization_contract",
            "t01_semantic_field_contract",
            "t02_relation_binding_constraint_propagation_contract",
            "t02_raw_vs_propagated_integrity_contract",
            "t03_hypothesis_competition_contract",
            "t04_attention_schema_focus_ownership_contract",
            "o01_other_entity_model_contract",
            "o02_intersubjective_allostasis_contract",
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
        or context.disable_n_minimal_enforcement
        or context.disable_s01_enforcement
        or context.disable_s01_prediction_registration
        or context.disable_s02_enforcement
        or context.disable_s03_enforcement
        or context.disable_s04_enforcement
        or context.disable_s05_enforcement
        or context.disable_o01_enforcement
        or context.disable_o02_enforcement
        or context.disable_t01_unresolved_slot_maintenance
        or context.disable_t01_field_enforcement
        or (
            context.t02_assembly_mode is not None
            and str(context.t02_assembly_mode).strip()
            and str(context.t02_assembly_mode).strip() != "bounded_constraint_propagation"
        )
        or context.disable_t02_enforcement
        or (
            context.t03_competition_mode is not None
            and str(context.t03_competition_mode).strip()
            and str(context.t03_competition_mode).strip() != "bounded_competition"
        )
        or context.disable_t03_enforcement
        or context.disable_t04_enforcement
    )
