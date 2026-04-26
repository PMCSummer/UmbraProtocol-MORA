from __future__ import annotations

from substrate.subject_tick.models import (
    SubjectTickGateDecision,
    SubjectTickOutcome,
    SubjectTickRestrictionCode,
    SubjectTickResult,
    SubjectTickState,
    SubjectTickUsabilityClass,
)


def evaluate_subject_tick_downstream_gate(
    subject_tick_state_or_result: SubjectTickState | SubjectTickResult,
) -> SubjectTickGateDecision:
    if isinstance(subject_tick_state_or_result, SubjectTickResult):
        state = subject_tick_state_or_result.state
    elif isinstance(subject_tick_state_or_result, SubjectTickState):
        state = subject_tick_state_or_result
    else:
        raise TypeError(
            "evaluate_subject_tick_downstream_gate requires SubjectTickState/SubjectTickResult"
        )

    restrictions: list[SubjectTickRestrictionCode] = [
        SubjectTickRestrictionCode.FIXED_ORDER_MUST_BE_READ,
        SubjectTickRestrictionCode.R_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C01_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C02_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C03_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C04_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C05_GATE_MUST_BE_READ,
        SubjectTickRestrictionCode.C04_MODE_SELECTION_MUST_BE_ENFORCED,
        SubjectTickRestrictionCode.C05_VALIDITY_ACTION_MUST_BE_ENFORCED,
        SubjectTickRestrictionCode.C05_RESTRICTIONS_MUST_NOT_BE_IGNORED,
        SubjectTickRestrictionCode.OUTCOME_MUST_BE_BOUNDED,
        SubjectTickRestrictionCode.EXECUTION_STANCE_MUST_BE_READ,
        SubjectTickRestrictionCode.CHECKPOINT_DECISIONS_MUST_BE_READ,
        SubjectTickRestrictionCode.C04_MODE_CLAIM_MUST_BE_READ,
        SubjectTickRestrictionCode.C05_ACTION_CLAIM_MUST_BE_READ,
        SubjectTickRestrictionCode.AUTHORITY_ROLES_MUST_BE_READ,
        SubjectTickRestrictionCode.DOWNSTREAM_OBEDIENCE_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.DOWNSTREAM_OBEDIENCE_RESTRICTIONS_MUST_BE_ENFORCED,
        SubjectTickRestrictionCode.WORLD_SEAM_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.W_ENTRY_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.W_ENTRY_FORBIDDEN_CLAIMS_MUST_BE_READ,
        SubjectTickRestrictionCode.W_ENTRY_ADMISSION_CRITERIA_MUST_BE_READ,
        SubjectTickRestrictionCode.S_MINIMAL_CONTOUR_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.S_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
        SubjectTickRestrictionCode.A_LINE_NORMALIZATION_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.A_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
        SubjectTickRestrictionCode.M_MINIMAL_CONTOUR_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.M_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
        SubjectTickRestrictionCode.N_MINIMAL_CONTOUR_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.N_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
        SubjectTickRestrictionCode.T01_SEMANTIC_FIELD_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.T01_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
        SubjectTickRestrictionCode.T02_RELATION_BINDING_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.T02_FORBIDDEN_SHORTCUTS_MUST_BE_READ,
        SubjectTickRestrictionCode.T03_HYPOTHESIS_COMPETITION_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.T04_ATTENTION_SCHEMA_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.S01_EFFERENCE_COPY_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.S02_PREDICTION_BOUNDARY_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.S03_OWNERSHIP_WEIGHTED_LEARNING_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.S04_INTEROCEPTIVE_SELF_BINDING_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.S05_MULTI_CAUSE_ATTRIBUTION_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.O01_OTHER_ENTITY_MODEL_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.O02_INTERSUBJECTIVE_ALLOSTASIS_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.O03_STRATEGY_CLASS_EVALUATION_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.P01_PROJECT_FORMATION_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.O04_DYNAMIC_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.V01_LICENSE_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.V02_PLAN_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.V03_CONSTRAINED_REALIZATION_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.C06_SURFACING_CANDIDATES_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.P02_INTERVENTION_EPISODE_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.P03_CREDIT_ASSIGNMENT_CONTRACT_MUST_BE_READ,
        SubjectTickRestrictionCode.P04_COUNTERFACTUAL_SIMULATION_CONTRACT_MUST_BE_READ,
    ]
    usability = SubjectTickUsabilityClass.USABLE_BOUNDED
    accepted = True
    reason = "bounded subject tick contour enforces phase contracts in runtime order"

    if state.revalidation_needed or state.final_execution_outcome == SubjectTickOutcome.REVALIDATE:
        usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "runtime contour requires selective revalidation before unrestricted continuation"
    if state.repair_needed or state.final_execution_outcome == SubjectTickOutcome.REPAIR:
        usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "runtime contour requires repair path before strong continuation"
    if state.final_execution_outcome == SubjectTickOutcome.HALT:
        accepted = False
        usability = SubjectTickUsabilityClass.BLOCKED
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "runtime contour halted by upstream legality/contract restrictions"
    if state.downstream_obedience_status in {
        "insufficient_authority_basis",
        "invalidated_upstream_surface",
        "blocked_by_survival_override",
    }:
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "downstream obedience contract rejected continue path despite local helper surfaces"
    if (
        state.world_require_grounded_transition
        and not state.world_entry_world_grounded_transition_admissible
    ):
        restrictions.append(
            SubjectTickRestrictionCode.WORLD_GROUNDED_TRANSITION_REQUIRES_WORLD_PRESENCE
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "world grounded transition requested but world seam grounding is unavailable"
    if (
        state.world_require_effect_feedback_for_success_claim
        and not state.world_entry_world_effect_success_admissible
    ):
        restrictions.append(
            SubjectTickRestrictionCode.WORLD_EFFECT_FEEDBACK_REQUIRED_FOR_SUCCESS_CLAIM
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "world effect feedback required for externally effected claim but effect observation is absent"
    if state.s_require_self_side_claim and not state.s_no_safe_self_claim:
        restrictions.append(SubjectTickRestrictionCode.S_SELF_WORLD_BOUNDARY_REQUIRED_FOR_SELF_CLAIMS)
    if state.s_require_self_controlled_transition_claim:
        restrictions.append(SubjectTickRestrictionCode.S_OWNERSHIP_CONTROL_DISCIPLINE_REQUIRED)
    if state.s_require_self_side_claim and state.s_no_safe_self_claim:
        restrictions.append(SubjectTickRestrictionCode.S_SELF_WORLD_BOUNDARY_REQUIRED_FOR_SELF_CLAIMS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "self-side claim requested but s-minimal contour has no safe self attribution basis"
    if state.s_require_world_side_claim and state.s_no_safe_world_claim:
        restrictions.append(SubjectTickRestrictionCode.S_SELF_WORLD_BOUNDARY_REQUIRED_FOR_SELF_CLAIMS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "world-side claim requested but s-minimal contour has no safe world attribution basis"
    if (
        state.s_require_self_controlled_transition_claim
        and state.s_attribution_class != "self_controlled_transition_claim"
    ):
        restrictions.append(SubjectTickRestrictionCode.S_OWNERSHIP_CONTROL_DISCIPLINE_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "self-controlled transition requested but s-minimal contour lacks lawful controllability basis"
    if (
        state.s_strict_mixed_attribution_guard
        and "mixed_attribution_without_uncertainty_marking" in state.s_forbidden_shortcuts
        and (
            state.s_require_self_side_claim
            or state.s_require_world_side_claim
            or state.s_require_self_controlled_transition_claim
            or state.world_require_grounded_transition
            or state.world_require_effect_feedback_for_success_claim
        )
    ):
        restrictions.append(SubjectTickRestrictionCode.S_OWNERSHIP_CONTROL_DISCIPLINE_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "mixed self/world attribution requires explicit uncertainty marking before continue"
    if state.a_require_capability_claim and not state.a_available_capability_claim_allowed:
        restrictions.append(SubjectTickRestrictionCode.A_CAPABILITY_CLAIM_REQUIRES_BASIS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "capability claim requested but a-line normalization marks basis as unavailable"
    if state.a_require_capability_claim and state.a_policy_conditioned_capability_present:
        restrictions.append(
            SubjectTickRestrictionCode.A_POLICY_GATED_CAPABILITY_REQUIRES_GATE
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "policy-conditioned capability cannot be consumed as free available capability"
    if state.a_require_capability_claim and state.a_underconstrained:
        restrictions.append(SubjectTickRestrictionCode.A_CAPABILITY_CLAIM_REQUIRES_BASIS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "capability claim requested while a-line substrate remains underconstrained"
    if state.m_require_memory_safe_claim and not state.m_safe_memory_claim_allowed:
        restrictions.append(
            SubjectTickRestrictionCode.M_SAFE_MEMORY_CLAIM_REQUIRES_LIFECYCLE_BASIS
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "safe memory claim requested but m-minimal lifecycle does not provide safe bounded basis"
            )
    if state.m_require_memory_safe_claim and (
        state.m_review_required
        or state.m_stale_risk in {"medium", "high"}
        or state.m_conflict_risk in {"medium", "high"}
    ):
        restrictions.append(
            SubjectTickRestrictionCode.M_SAFE_MEMORY_CLAIM_REQUIRES_LIFECYCLE_BASIS
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "safe memory claim requested while memory surface is stale/conflicted/review-bound"
    if state.n_require_narrative_safe_claim and not state.n_safe_narrative_commitment_allowed:
        restrictions.append(SubjectTickRestrictionCode.N_SAFE_NARRATIVE_CLAIM_REQUIRES_BASIS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "safe narrative commitment requested but n-minimal contour does not provide lawful basis"
            )
    if state.n_require_narrative_safe_claim and (
        state.n_underconstrained
        or state.n_ambiguity_residue
        or state.n_contradiction_risk in {"medium", "high"}
    ):
        restrictions.append(SubjectTickRestrictionCode.N_SAFE_NARRATIVE_CLAIM_REQUIRES_BASIS)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "safe narrative commitment requested while n-minimal surface remains ambiguous/contradictory"
            )
    if (
        state.t01_require_preverbal_scene_consumer
        and not state.t01_preverbal_consumer_ready
    ):
        restrictions.append(
            SubjectTickRestrictionCode.T01_PREVERBAL_SCENE_REQUIRED_FOR_CONSUMER
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "t01 preverbal scene consumer requested but semantic field is not cleanly consumable"
            )
    if (
        state.t01_require_preverbal_scene_consumer
        and "premature_scene_closure" in state.t01_forbidden_shortcuts
    ):
        restrictions.append(
            SubjectTickRestrictionCode.T01_PREVERBAL_SCENE_REQUIRED_FOR_CONSUMER
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "t01 unresolved laundering risk detected under pre-verbal consumer pressure"
            )
    if state.t01_require_preverbal_scene_consumer and state.t01_no_clean_scene_commit:
        restrictions.append(
            SubjectTickRestrictionCode.T01_PREVERBAL_SCENE_REQUIRED_FOR_CONSUMER
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "t01 scene remains no-clean under claim pressure; clarification/revalidation required"
    if (
        state.t01_require_scene_comparison_consumer
        and not state.t01_scene_comparison_ready
    ):
        restrictions.append(
            SubjectTickRestrictionCode.T01_SCENE_COMPARISON_REQUIRED_FOR_CONSUMER
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "t01 comparison consumer requested but scene is not comparison-ready"
    t02_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.t02_relation_binding_checkpoint"
        ),
        None,
    )
    if t02_checkpoint is not None and t02_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.T02_CONSTRAINED_SCENE_REQUIRED_FOR_CONSUMER)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "t02 constrained-scene consumer checkpoint requires detour before downstream continuation"
            )
    t02_integrity_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.t02_raw_vs_propagated_integrity_checkpoint"
        ),
        None,
    )
    if (
        state.t02_require_raw_vs_propagated_distinction
        and not state.t02_raw_vs_propagated_distinct
    ):
        restrictions.append(
            SubjectTickRestrictionCode.T02_RAW_VS_PROPAGATED_DISTINCTION_REQUIRED
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "t02 raw-vs-propagated distinction required but constrained scene surface collapsed"
            )
    if (
        t02_integrity_checkpoint is not None
        and t02_integrity_checkpoint.status.value != "allowed"
    ):
        restrictions.append(
            SubjectTickRestrictionCode.T02_RAW_VS_PROPAGATED_DISTINCTION_REQUIRED
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "t02 raw-vs-propagated integrity checkpoint requires detour before downstream continuation"
            )
    t03_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.t03_hypothesis_competition_checkpoint"
        ),
        None,
    )
    if t03_checkpoint is not None and t03_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.T03_CONVERGENCE_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "t03 hypothesis competition checkpoint requires detour before downstream continuation"
            )
    if (
        state.t03_require_convergence_consumer
        and not state.t03_convergence_consumer_ready
    ):
        restrictions.append(SubjectTickRestrictionCode.T03_CONVERGENCE_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "t03 convergence consumer requested but no lawful converged leader is consumable"
    if state.t03_require_frontier_consumer and not state.t03_frontier_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.T03_FRONTIER_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "t03 frontier consumer requested but publication frontier is not consumable"
    if (
        state.t03_require_nonconvergence_preservation
        and not state.t03_nonconvergence_preserved
    ):
        restrictions.append(
            SubjectTickRestrictionCode.T03_NONCONVERGENCE_PRESERVATION_REQUIRED
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "t03 nonconvergence preservation requested but frontier collapsed under ambiguity"
            )
    t04_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.t04_attention_schema_checkpoint"
        ),
        None,
    )
    if t04_checkpoint is not None and t04_checkpoint.status.value != "allowed":
        if "focus_ownership" in t04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.T04_FOCUS_OWNERSHIP_CONSUMER_REQUIRED)
        if "reportable_focus" in t04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.T04_REPORTABLE_FOCUS_CONSUMER_REQUIRED)
        if "peripheral_preservation" in t04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.T04_PERIPHERAL_PRESERVATION_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "t04 attention schema checkpoint requires detour before downstream continuation"

    s01_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.s01_efference_copy_checkpoint"
        ),
        None,
    )
    if state.s01_require_comparison_consumer and not state.s01_comparison_ready:
        restrictions.append(SubjectTickRestrictionCode.S01_COMPARISON_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s01 comparison consumer requested but no lawful comparison is ready"
    if (
        state.s01_require_prediction_validity_consumer
        and not state.s01_prediction_validity_ready
    ):
        restrictions.append(
            SubjectTickRestrictionCode.S01_PREDICTION_VALIDITY_CONSUMER_REQUIRED
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s01 prediction validity consumer requested but prediction set is stale/contaminated"
    if (
        state.s01_require_unexpected_change_consumer
        and state.s01_unexpected_change_detected
    ):
        restrictions.append(
            SubjectTickRestrictionCode.S01_UNEXPECTED_CHANGE_CONSUMER_REQUIRED
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s01 unexpected change consumer requested and unexpected observed change remains unresolved"
    if s01_checkpoint is not None and s01_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.S01_COMPARISON_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s01 efference-copy checkpoint requires detour before downstream continuation"

    s02_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.s02_prediction_boundary_checkpoint"
        ),
        None,
    )
    if state.s02_require_boundary_consumer and not state.s02_boundary_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.S02_BOUNDARY_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s02 boundary consumer requested but no clean seam boundary is consumable"
    if (
        state.s02_require_controllability_consumer
        and not state.s02_controllability_consumer_ready
    ):
        restrictions.append(SubjectTickRestrictionCode.S02_CONTROLLABILITY_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s02 controllability consumer requested but controllability basis is unavailable"
    if state.s02_require_mixed_source_consumer and not state.s02_mixed_source_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.S02_MIXED_SOURCE_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s02 mixed-source consumer requested but mixed boundary is not preserved"
    if s02_checkpoint is not None and s02_checkpoint.status.value != "allowed":
        if "boundary" in s02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.S02_BOUNDARY_CONSUMER_REQUIRED)
        if "controllability" in s02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S02_CONTROLLABILITY_CONSUMER_REQUIRED
            )
        if "mixed_source" in s02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.S02_MIXED_SOURCE_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s02 prediction boundary checkpoint requires detour before downstream continuation"

    s03_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.s03_ownership_weighted_learning_checkpoint"
        ),
        None,
    )
    if (
        state.s03_require_learning_packet_consumer
        and not state.s03_learning_packet_consumer_ready
    ):
        restrictions.append(SubjectTickRestrictionCode.S03_LEARNING_PACKET_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s03 learning packet consumer requested but lawful ownership-weighted packet is unavailable"
    if state.s03_require_mixed_update_consumer and not state.s03_mixed_update_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.S03_MIXED_UPDATE_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s03 mixed update consumer requested but split ownership update packet is unavailable"
    if (
        state.s03_require_freeze_obedience_consumer
        and not state.s03_freeze_obedience_consumer_ready
    ):
        restrictions.append(
            SubjectTickRestrictionCode.S03_FREEZE_OBEDIENCE_CONSUMER_REQUIRED
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s03 freeze-obedience consumer requested but freeze/defer route is not lawfully consumable"
    if s03_checkpoint is not None and s03_checkpoint.status.value != "allowed":
        if "learning_packet" in s03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S03_LEARNING_PACKET_CONSUMER_REQUIRED
            )
        if "mixed_update" in s03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S03_MIXED_UPDATE_CONSUMER_REQUIRED
            )
        if "freeze_obedience" in s03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S03_FREEZE_OBEDIENCE_CONSUMER_REQUIRED
            )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "s03 ownership-weighted learning checkpoint requires detour before downstream continuation"

    s04_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.s04_interoceptive_self_binding_checkpoint"
        ),
        None,
    )
    if s04_checkpoint is not None and s04_checkpoint.status.value != "allowed":
        if "stable_core" in s04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S04_STABLE_CORE_CONSUMER_REQUIRED
            )
        if "contested" in s04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S04_CONTESTED_CONSUMER_REQUIRED
            )
        if "no_stable_core" in s04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S04_NO_STABLE_CORE_CONSUMER_REQUIRED
            )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "s04 interoceptive self-binding checkpoint requires detour before downstream continuation"
            )

    s05_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.s05_multi_cause_attribution_checkpoint"
        ),
        None,
    )
    if s05_checkpoint is not None:
        if "factorized_consumer" in s05_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S05_FACTORIZED_CONSUMER_REQUIRED
            )
        if "low_residual_learning_route" in s05_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S05_LOW_RESIDUAL_LEARNING_ROUTE_REQUIRED
            )
        if "forbid_single_cause_collapse_shape_aware" in s05_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.S05_SINGLE_CAUSE_COLLAPSE_FORBIDDEN
            )
    if s05_checkpoint is not None and s05_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "s05 multi-cause attribution checkpoint requires detour before downstream continuation"
            )

    o01_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.o01_other_entity_model_checkpoint"
        ),
        None,
    )
    if o01_checkpoint is not None:
        if "require_o01_entity_individuation_consumer" in o01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O01_ENTITY_INDIVIDUATION_CONSUMER_REQUIRED
            )
        if "require_o01_clarification_ready_consumer" in o01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O01_CLARIFICATION_READY_CONSUMER_REQUIRED
            )
        if "default_o01_competing_entity_clarification" in o01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O01_CLARIFICATION_READY_CONSUMER_REQUIRED
            )
        if "default_o01_belief_overlay_clarification" in o01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O01_CLARIFICATION_READY_CONSUMER_REQUIRED
            )
        if "o01_projection_guard_triggered" in o01_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.O01_PROJECTION_GUARD_REQUIRED)
    if o01_checkpoint is not None and o01_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "o01 other-entity model checkpoint requires detour before downstream continuation"

    o02_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.o02_intersubjective_allostasis_checkpoint"
        ),
        None,
    )
    if o02_checkpoint is not None:
        if "require_o02_repair_sensitive_consumer" in o02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O02_REPAIR_SENSITIVE_CONSUMER_REQUIRED
            )
        if "require_o02_boundary_preserving_consumer" in o02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O02_BOUNDARY_PRESERVING_CONSUMER_REQUIRED
            )
        if "default_o02_repair_sensitive_clarification_detour" in o02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O02_REPAIR_SENSITIVE_CONSUMER_REQUIRED
            )
        if "default_o02_conservative_clarification_detour" in o02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O02_REPAIR_SENSITIVE_CONSUMER_REQUIRED
            )
        if "o02_politeness_only_collapse_forbidden" in o02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O02_POLITENESS_ONLY_COLLAPSE_FORBIDDEN
            )
    if state.o02_s05_shape_modulation_applied:
        restrictions.append(
            SubjectTickRestrictionCode.O02_REPAIR_SENSITIVE_CONSUMER_REQUIRED
        )
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = (
                "o02 typed s05-shape modulation requires bounded repair-sensitive caution before unrestricted continuation"
            )
    if state.o02_strong_disagreement_guard_applied:
        restrictions.append(
            SubjectTickRestrictionCode.O02_POLITENESS_ONLY_COLLAPSE_FORBIDDEN
        )
    if o02_checkpoint is not None and o02_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "o02 intersubjective allostasis checkpoint requires detour before downstream continuation"
            )

    o03_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.o03_strategy_class_evaluation_checkpoint"
        ),
        None,
    )
    if o03_checkpoint is not None:
        if "require_o03_strategy_contract_consumer" in o03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O03_STRATEGY_CONTRACT_CONSUMER_REQUIRED
            )
        if "require_o03_cooperative_selection_consumer" in o03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O03_COOPERATIVE_SELECTION_CONSUMER_REQUIRED
            )
        if "require_o03_transparency_preserving_consumer" in o03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O03_TRANSPARENCY_PRESERVING_CONSUMER_REQUIRED
            )
        if "default_o03_transparency_clarification_detour" in o03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.O03_TRANSPARENCY_INCREASE_REQUIRED)
        if "default_o03_exploitative_candidate_block_detour" in o03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O03_EXPLOITATIVE_CANDIDATE_BLOCK_REQUIRED
            )
        if "default_o03_dependency_lock_in_detour" in o03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O03_EXPLOITATIVE_CANDIDATE_BLOCK_REQUIRED
            )
            restrictions.append(SubjectTickRestrictionCode.O03_COOPERATIVE_DEFAULT_REQUIRED)
        if "o03_politeness_equivalence_forbidden" in o03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O03_POLITENESS_EQUIVALENCE_FORBIDDEN
            )
    if state.o03_no_safe_classification or state.o03_strategy_underconstrained:
        restrictions.append(SubjectTickRestrictionCode.O03_COOPERATIVE_DEFAULT_REQUIRED)
    if state.o03_concealed_state_divergence_required:
        restrictions.append(SubjectTickRestrictionCode.O03_TRANSPARENCY_INCREASE_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.O03_POLITENESS_EQUIVALENCE_FORBIDDEN)
    if state.o03_high_local_gain_but_high_entropy:
        restrictions.append(SubjectTickRestrictionCode.O03_COOPERATIVE_DEFAULT_REQUIRED)
        restrictions.append(
            SubjectTickRestrictionCode.O03_EXPLOITATIVE_CANDIDATE_BLOCK_REQUIRED
        )
    if (
        state.o03_dependency_risk_band == "high"
        and state.o03_reversibility_band == "low"
        and state.o03_local_effectiveness_pressure == "high"
    ):
        restrictions.append(SubjectTickRestrictionCode.O03_EXPLOITATIVE_CANDIDATE_BLOCK_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.O03_COOPERATIVE_DEFAULT_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.O03_TRANSPARENCY_INCREASE_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = (
                "o03 dependency/reversibility semantic guard blocks lock-in style candidate even under matched local utility"
            )
    if state.o03_strategy_class in {
        "manipulation_risk_high",
        "high_local_gain_but_high_entropy",
    } and state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
        restrictions.append(
            SubjectTickRestrictionCode.O03_EXPLOITATIVE_CANDIDATE_BLOCK_REQUIRED
        )
        usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
        reason = (
            "o03 strategy-class semantics require transparency/cooperative safeguards before unrestricted continuation"
        )
    if o03_checkpoint is not None and o03_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "o03 strategy class checkpoint requires detour before downstream continuation"
            )

    p01_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.p01_project_formation_checkpoint"
        ),
        None,
    )
    if p01_checkpoint is not None:
        if "require_p01_intention_stack_consumer" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_INTENTION_STACK_CONSUMER_REQUIRED
            )
        if "require_p01_authority_bound_consumer" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_AUTHORITY_BOUND_FORMATION_REQUIRED
            )
        if "require_p01_project_handoff_consumer" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_PROJECT_HANDOFF_CONSUMER_REQUIRED
            )
        if "default_p01_missing_precondition_detour" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_PROJECT_HANDOFF_CONSUMER_REQUIRED
            )
        if "default_p01_conflict_arbitration_detour" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_CONFLICT_ARBITRATION_REQUIRED
            )
        if "default_p01_stale_project_detour" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_STALE_ACTIVE_PROJECT_FORBIDDEN
            )
        if "prompt_local_capture_risk" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_PROMPT_LOCAL_SUBSTITUTION_FORBIDDEN
            )
        if "stale_active_project_detected" in p01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P01_STALE_ACTIVE_PROJECT_FORBIDDEN
            )

    p01_surface_present = bool(
        state.p01_active_project_count
        + state.p01_candidate_project_count
        + state.p01_suspended_project_count
        + state.p01_rejected_project_count
    )
    if state.p01_prompt_local_capture_risk and p01_surface_present:
        restrictions.append(
            SubjectTickRestrictionCode.P01_PROMPT_LOCAL_SUBSTITUTION_FORBIDDEN
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p01 prompt-local substitution guard triggered; authority-bounded project continuation is blocked"
    if state.p01_conflicting_authority and p01_surface_present:
        restrictions.append(SubjectTickRestrictionCode.P01_CONFLICT_ARBITRATION_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and state.p01_arbitration_count == 0
        ):
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            reason = "p01 conflicting authority requires explicit arbitration record before continuation"
    if state.p01_stale_active_project_detected and p01_surface_present:
        restrictions.append(SubjectTickRestrictionCode.P01_STALE_ACTIVE_PROJECT_FORBIDDEN)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and state.p01_active_project_count > 0
        ):
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            reason = "p01 stale active project detected; continuation requires termination/review handling"
    if (
        state.p01_no_safe_project_formation
        and p01_surface_present
        and not state.p01_project_handoff_ready
        and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    ):
        restrictions.append(SubjectTickRestrictionCode.P01_PROJECT_HANDOFF_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        accepted = False
        usability = SubjectTickUsabilityClass.BLOCKED
        reason = "p01 no-safe-formation state blocks project handoff continuation until grounding/arbitration constraints are resolved"

    o04_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.o04_rupture_hostility_coercion_checkpoint"
        ),
        None,
    )
    if o04_checkpoint is not None:
        if "require_o04_dynamic_contract_consumer" in o04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O04_DYNAMIC_CONTRACT_CONSUMER_REQUIRED
            )
        if "require_o04_directionality_consumer" in o04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O04_DIRECTIONALITY_CONSUMER_REQUIRED
            )
        if "require_o04_protective_handoff_consumer" in o04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O04_PROTECTIVE_HANDOFF_CONSUMER_REQUIRED
            )
        if "default_o04_coercive_structure_detour" in o04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O04_STRONG_COERCION_CLAIM_REQUIRES_STRUCTURE
            )
        if "default_o04_rupture_risk_detour" in o04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.O04_RUPTURE_TRACKING_REQUIRED)
        if "default_o04_legitimacy_ambiguity_detour" in o04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O04_DIRECTIONALITY_REQUIRED_FOR_STRONG_PRESSURE_CLAIM
            )
        if "tone_shortcut_forbidden_applied" in o04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.O04_TONE_ONLY_SHORTCUT_FORBIDDEN)
        if "directionality_ambiguous" in o04_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.O04_DIRECTIONALITY_REQUIRED_FOR_STRONG_PRESSURE_CLAIM
            )

    if state.o04_tone_shortcut_forbidden_applied:
        restrictions.append(SubjectTickRestrictionCode.O04_TONE_ONLY_SHORTCUT_FORBIDDEN)
    if (
        state.o04_coercion_candidate_count > 0
        and state.o04_directionality_kind != "directionality_ambiguous"
        and not state.o04_no_safe_dynamic_claim
    ):
        if state.o04_legitimacy_hint_status in {"legitimacy_absent", "legitimacy_contested"}:
            restrictions.append(
                SubjectTickRestrictionCode.O04_PROTECTIVE_HANDOFF_CONSUMER_REQUIRED
            )
            if (
                state.final_execution_outcome == SubjectTickOutcome.CONTINUE
                and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
            ):
                usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
                restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
                reason = (
                    "o04 typed legitimacy-pressure semantics require protective handoff before unrestricted continuation"
                )
        elif state.o04_legitimacy_hint_status == "legitimacy_supported":
            restrictions.append(SubjectTickRestrictionCode.O04_DYNAMIC_CONTRACT_CONSUMER_REQUIRED)
    if (
        state.o04_coercion_candidate_count > 0
        and state.o04_directionality_kind == "directionality_ambiguous"
    ):
        restrictions.append(
            SubjectTickRestrictionCode.O04_DIRECTIONALITY_REQUIRED_FOR_STRONG_PRESSURE_CLAIM
        )
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "o04 coercive-pressure claim requires non-ambiguous directionality before continuation"
    if state.o04_coercion_candidate_count > 0:
        restrictions.append(
            SubjectTickRestrictionCode.O04_STRONG_COERCION_CLAIM_REQUIRES_STRUCTURE
        )
    if state.o04_rupture_status in {
        "rupture_risk_only",
        "rupture_active_candidate",
        "deescalated_but_not_closed",
    }:
        restrictions.append(SubjectTickRestrictionCode.O04_RUPTURE_TRACKING_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "o04 rupture-tracking surface requires bounded caution before unrestricted continuation"
    if o04_checkpoint is not None and o04_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "o04 rupture/hostility/coercion checkpoint requires detour before downstream continuation"
            )

    r05_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.r05_protective_regulation_checkpoint"
        ),
        None,
    )
    if r05_checkpoint is not None:
        restrictions.append(
            SubjectTickRestrictionCode.R05_PROTECTIVE_REGULATION_CONTRACT_MUST_BE_READ
        )
        if "require_r05_protective_state_consumer" in r05_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.R05_PROTECTIVE_STATE_CONSUMER_REQUIRED
            )
        if "require_r05_surface_inhibition_consumer" in r05_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.R05_SURFACE_INHIBITION_CONSUMER_REQUIRED
            )
        if "require_r05_release_contract_consumer" in r05_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.R05_RELEASE_CONTRACT_CONSUMER_REQUIRED
            )
        if "default_r05_protective_override_detour" in r05_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.R05_PROJECT_OVERRIDE_ACTIVE)
        if "default_r05_surface_throttle_detour" in r05_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.R05_SURFACE_THROTTLE_REQUIRED)
        if "default_r05_release_recheck_detour" in r05_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.R05_RELEASE_RECHECK_REQUIRED)

    if state.r05_insufficient_basis_for_override:
        restrictions.append(SubjectTickRestrictionCode.R05_INSUFFICIENT_BASIS_FOR_OVERRIDE)
    if state.r05_regulation_conflict:
        restrictions.append(SubjectTickRestrictionCode.R05_REGULATION_CONFLICT)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = (
                "r05 regulation conflict requires bounded caution and explicit recheck before unrestricted continuation"
            )
    if (
        state.r05_protective_mode == "active_protective_mode"
        and state.r05_project_override_active
        and state.r05_release_pending
    ):
        restrictions.append(SubjectTickRestrictionCode.R05_PROJECT_OVERRIDE_ACTIVE)
        restrictions.append(SubjectTickRestrictionCode.R05_RELEASE_RECHECK_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "r05 active protective override remains release-pending; continuation requires bounded detour"
            )
    elif (
        state.r05_inhibited_surface_count > 0
        and state.r05_protective_mode in {"degraded_operation_only", "recovery_in_progress"}
    ):
        restrictions.append(SubjectTickRestrictionCode.R05_SURFACE_THROTTLE_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "r05 surface-specific inhibition throttles continuation while preserving bounded operation"
    if r05_checkpoint is not None and r05_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "r05 protective regulation checkpoint requires detour before downstream continuation"
            )

    v01_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id
            == "rt01.v01_normative_permission_commitment_licensing_checkpoint"
        ),
        None,
    )
    if v01_checkpoint is not None:
        if "require_v01_license_consumer" in v01_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V01_LICENSE_CONSUMER_REQUIRED)
        if "require_v01_commitment_delta_consumer" in v01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V01_COMMITMENT_DELTA_CONSUMER_REQUIRED
            )
        if "require_v01_qualifier_binding_consumer" in v01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V01_QUALIFIER_BINDING_CONSUMER_REQUIRED
            )
        if "default_v01_unlicensed_act_detour" in v01_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V01_UNLICENSED_ACT_DETOUR_REQUIRED
            )
        if "default_v01_qualification_required_detour" in v01_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V01_QUALIFICATION_REQUIRED)
        if "default_v01_commitment_denied_detour" in v01_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V01_COMMITMENT_DENIED)
        if "protective_defer_required" in v01_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V01_PROTECTIVE_DEFER_REQUIRED)

    v01_basis_present = bool(state.v01_candidate_act_count > 0)
    v01_allowed_qualifier_ids = {
        "preserve_explicit_uncertainty",
        "qualified_assertion_required",
        "advice_basis_disclosure_required",
        "bounded_commitment_scope",
        "request_scope_clarification_required",
    }
    v01_qualifier_ids = set(state.v01_mandatory_qualifier_ids)
    if v01_basis_present and state.v01_denied_act_count > 0:
        restrictions.append(SubjectTickRestrictionCode.V01_UNLICENSED_ACT_DETOUR_REQUIRED)
    if (
        v01_basis_present
        and state.v01_insufficient_license_basis
    ):
        restrictions.append(SubjectTickRestrictionCode.V01_INSUFFICIENT_LICENSE_BASIS)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            reason = "v01 insufficient licensing basis blocks continuation under act-level licensing pressure"
    if (
        v01_basis_present
        and state.v01_conditional_act_count > 0
        and state.v01_mandatory_qualifier_count > 0
    ):
        restrictions.append(SubjectTickRestrictionCode.V01_QUALIFICATION_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "v01 conditional license requires mandatory qualifier binding before unrestricted continuation"
    if (
        v01_basis_present
        and state.v01_conditional_act_count > 0
        and state.v01_mandatory_qualifier_count > 0
    ):
        if len(v01_qualifier_ids) != state.v01_mandatory_qualifier_count:
            restrictions.append(SubjectTickRestrictionCode.V01_QUALIFIER_BINDING_CONSUMER_REQUIRED)
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
                accepted = False
                usability = SubjectTickUsabilityClass.BLOCKED
                reason = "v01 mandatory qualifier identity/count mismatch blocks continuation"
        elif not v01_qualifier_ids.issubset(v01_allowed_qualifier_ids):
            restrictions.append(SubjectTickRestrictionCode.V01_QUALIFIER_BINDING_CONSUMER_REQUIRED)
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
                accepted = False
                usability = SubjectTickUsabilityClass.BLOCKED
                reason = "v01 qualifier identity substitution detected; bounded continuation denied"
    if v01_basis_present and state.v01_promise_like_act_denied:
        restrictions.append(SubjectTickRestrictionCode.V01_COMMITMENT_DENIED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and not state.v01_alternative_narrowed_act_available
        ):
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            reason = "v01 promise-like commitment denied without narrowed licensed alternative"
        elif (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "v01 commitment-denied path requires narrowed licensed act continuation"
    if v01_basis_present and state.v01_protective_defer_required:
        restrictions.append(SubjectTickRestrictionCode.V01_PROTECTIVE_DEFER_REQUIRED)
    if (
        v01_basis_present
        and state.v01_commitment_delta_count > 0
        and not state.v01_promise_like_act_denied
    ):
        restrictions.append(SubjectTickRestrictionCode.V01_COMMITMENT_DELTA_CONSUMER_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = (
                "v01 commitment-creating license path requires bounded commitment-delta handoff before unrestricted continuation"
            )
    if (
        v01_basis_present
        and not state.v01_license_consumer_ready
        and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    ):
        accepted = False
        usability = SubjectTickUsabilityClass.BLOCKED
        restrictions.append(SubjectTickRestrictionCode.V01_LICENSE_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        reason = "v01 candidate basis present but license consumer surface is not ready"
    if (
        v01_basis_present
        and state.v01_conditional_act_count > 0
        and not state.v01_qualifier_binding_consumer_ready
    ):
        restrictions.append(SubjectTickRestrictionCode.V01_QUALIFIER_BINDING_CONSUMER_REQUIRED)
    if v01_checkpoint is not None and v01_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "v01 normative permission/commitment checkpoint requires detour before downstream continuation"
            )

    v02_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.v02_utterance_plan_checkpoint"
        ),
        None,
    )
    if v02_checkpoint is not None:
        if "require_v02_plan_consumer" in v02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V02_PLAN_CONSUMER_REQUIRED)
        if "require_v02_ordering_consumer" in v02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V02_ORDERING_CONSUMER_REQUIRED)
        if "require_v02_realization_contract_consumer" in v02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V02_REALIZATION_CONTRACT_CONSUMER_REQUIRED
            )
        if "default_v02_partial_plan_detour" in v02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V02_PARTIAL_PLAN_DETOUR_REQUIRED)
        if "default_v02_clarification_first_detour" in v02_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V02_CLARIFICATION_FIRST_DETOUR_REQUIRED
            )
        if (
            "default_v02_protective_boundary_first_detour"
            in v02_checkpoint.required_action
        ):
            restrictions.append(
                SubjectTickRestrictionCode.V02_PROTECTIVE_BOUNDARY_FIRST_DETOUR_REQUIRED
            )

    v02_basis_present = bool(state.v02_segment_count > 0)
    v02_expected_qualifier_ids = tuple(dict.fromkeys(state.v01_mandatory_qualifier_ids))
    v02_attached_qualifier_ids = tuple(dict.fromkeys(state.v02_mandatory_qualifier_ids))
    if v02_basis_present and state.v02_blocked_expansion_count > 0:
        restrictions.append(SubjectTickRestrictionCode.V02_BLOCKED_EXPANSIONS_MUST_BE_RESPECTED)
    if v02_basis_present and state.v02_protected_omission_count > 0:
        restrictions.append(SubjectTickRestrictionCode.V02_PROTECTED_OMISSIONS_MUST_BE_RESPECTED)
    if v02_basis_present and state.v02_mandatory_qualifier_attachment_count > 0:
        restrictions.append(SubjectTickRestrictionCode.V02_ORDERING_CONSUMER_REQUIRED)
        qualifier_identity_mismatch = bool(
            not v02_attached_qualifier_ids
            or (
                v02_expected_qualifier_ids
                and v02_attached_qualifier_ids != v02_expected_qualifier_ids
            )
        )
        if qualifier_identity_mismatch:
            restrictions.append(
                SubjectTickRestrictionCode.V02_QUALIFIER_IDENTITY_BINDING_REQUIRED
            )
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
                accepted = False
                usability = SubjectTickUsabilityClass.BLOCKED
                reason = (
                    "v02 mandatory qualifier identity binding mismatch detected for typed utterance-plan bridge"
                )
        elif (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "v02 mandatory qualifier attachment requires ordering-aware downstream consumption"
    if v02_basis_present and state.v02_unresolved_branching:
        restrictions.append(SubjectTickRestrictionCode.V02_UNRESOLVED_BRANCHING_REQUIRES_REVIEW)
    if v02_basis_present and state.v02_partial_plan_only:
        restrictions.append(SubjectTickRestrictionCode.V02_PARTIAL_PLAN_DETOUR_REQUIRED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            reason = "v02 partial-plan-only state blocks unrestricted continuation"
    if v02_basis_present and state.v02_clarification_first_required:
        restrictions.append(SubjectTickRestrictionCode.V02_CLARIFICATION_FIRST_DETOUR_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "v02 clarification-first plan requires bounded detour before continuation"
    if v02_basis_present and state.v02_protective_boundary_first:
        restrictions.append(
            SubjectTickRestrictionCode.V02_PROTECTIVE_BOUNDARY_FIRST_DETOUR_REQUIRED
        )
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "v02 protective-boundary-first plan requires bounded downstream handling"
    if (
        v02_basis_present
        and state.v02_segment_count > 1
        and state.v02_ordering_edge_count <= 0
        and not state.v02_partial_plan_only
    ):
        restrictions.append(SubjectTickRestrictionCode.V02_ORDERING_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "v02 segment ordering graph mismatch detected for multi-segment plan"
    if (
        v02_basis_present
        and state.v02_plan_consumer_ready
        and state.v02_discourse_history_sensitive
        and state.v02_segment_count > 1
        and state.v02_ordering_edge_count > 0
        and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    ):
        restrictions.append(SubjectTickRestrictionCode.V02_ORDERING_CONSUMER_REQUIRED)
        if usability == SubjectTickUsabilityClass.USABLE_BOUNDED:
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = (
                "v02 discourse-history-sensitive plan requires ordering-consumer acknowledgement before unrestricted continuation"
            )
    if (
        v02_basis_present
        and not state.v02_plan_consumer_ready
        and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    ):
        restrictions.append(SubjectTickRestrictionCode.V02_PLAN_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        accepted = False
        usability = SubjectTickUsabilityClass.BLOCKED
        reason = "v02 plan basis present but downstream plan consumer is not ready"
    if (
        v02_basis_present
        and not state.v02_realization_contract_consumer_ready
        and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
    ):
        restrictions.append(
            SubjectTickRestrictionCode.V02_REALIZATION_CONTRACT_CONSUMER_REQUIRED
        )
        if usability == SubjectTickUsabilityClass.USABLE_BOUNDED:
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "v02 realization contract is not ready for unrestricted continuation"
    if v02_checkpoint is not None and v02_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "v02 communicative-intent/utterance-plan checkpoint requires detour before downstream continuation"
            )

    v03_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.v03_constrained_realization_checkpoint"
        ),
        None,
    )
    if v03_checkpoint is not None:
        if "require_v03_realization_consumer" in v03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V03_REALIZATION_CONSUMER_REQUIRED)
        if "require_v03_alignment_consumer" in v03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V03_ALIGNMENT_CONSUMER_REQUIRED)
        if "require_v03_constraint_report_consumer" in v03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V03_CONSTRAINT_REPORT_CONSUMER_REQUIRED
            )
        if "default_v03_realization_failure_detour" in v03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V03_REALIZATION_FAILURE_DETOUR_REQUIRED
            )
        if "default_v03_alignment_violation_detour" in v03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.V03_ALIGNMENT_VIOLATION_DETOUR_REQUIRED
            )
        if "default_v03_boundary_order_detour" in v03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.V03_BOUNDARY_ORDER_DETOUR_REQUIRED)

    v03_basis_present = bool(state.v03_segment_count > 0)
    if v03_basis_present and state.v03_hard_constraint_violation_count > 0:
        restrictions.append(SubjectTickRestrictionCode.V03_REALIZATION_FAILURE_DETOUR_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "v03 hard constrained-realization violations block unrestricted continuation"
    if v03_basis_present and state.v03_qualifier_locality_failures > 0:
        restrictions.append(SubjectTickRestrictionCode.V03_QUALIFIER_LOCALITY_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "v03 qualifier-locality failure blocks continuation until constrained realization is repaired"
    if v03_basis_present and state.v03_blocked_expansion_leak_detected:
        restrictions.append(SubjectTickRestrictionCode.V03_BLOCKED_EXPANSION_LEAK_FORBIDDEN)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "v03 blocked-expansion leakage detected; continuation denied under constrained realization contract"
    if (
        v03_basis_present
        and state.v03_boundary_before_explanation_required
        and not state.v03_boundary_before_explanation_satisfied
    ):
        restrictions.append(SubjectTickRestrictionCode.V03_BOUNDARY_ORDER_DETOUR_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "v03 boundary-before-explanation ordering violation blocks unrestricted continuation"
    if v03_basis_present and not state.v03_realization_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.V03_REALIZATION_CONSUMER_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "v03 realization basis present but realization-consumer surface is not ready"
    if (
        v03_basis_present
        and state.v03_boundary_before_explanation_required
        and state.v03_boundary_before_explanation_satisfied
        and state.v03_hard_constraint_violation_count <= 0
        and state.v03_qualifier_locality_failures <= 0
        and not state.v03_blocked_expansion_leak_detected
        and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
        and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
    ):
        restrictions.append(SubjectTickRestrictionCode.V03_BOUNDARY_ORDER_DETOUR_REQUIRED)
        usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
        reason = (
            "v03 boundary-first constrained realization is satisfied but still requires bounded downstream handling"
        )
    if (
        v03_basis_present
        and state.v03_segment_count > 1
        and state.v01_conditional_act_count > 0
        and state.v03_hard_constraint_violation_count <= 0
        and state.v03_qualifier_locality_failures <= 0
        and state.v03_aligned_segment_count == state.v03_segment_count
    ):
        restrictions.append(SubjectTickRestrictionCode.V03_ALIGNMENT_CONSUMER_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = (
                "v03 multi-segment constrained realization requires explicit alignment consumer handling before unrestricted continuation"
            )
    if (
        v03_basis_present
        and state.v03_partial_realization_only
        and state.v03_replan_required
    ):
        restrictions.append(SubjectTickRestrictionCode.V03_REPLAN_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "v03 partial constrained realization requires bounded replan handoff"
    if v03_checkpoint is not None and v03_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "v03 constrained realization checkpoint requires detour before downstream continuation"
            )

    c06_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.c06_surfacing_candidates_checkpoint"
        ),
        None,
    )
    if c06_checkpoint is not None:
        if "require_c06_candidate_set_consumer" in c06_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.C06_CANDIDATE_SET_CONSUMER_REQUIRED)
        if "require_c06_suppression_report_consumer" in c06_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.C06_SUPPRESSION_REPORT_CONSUMER_REQUIRED)
        if "require_c06_identity_merge_consumer" in c06_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.C06_IDENTITY_MERGE_CONSUMER_REQUIRED)
        if "default_c06_candidate_ambiguity_detour" in c06_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.C06_CANDIDATE_AMBIGUITY_DETOUR_REQUIRED)
        if "default_c06_commitment_carryover_detour" in c06_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.C06_COMMITMENT_CARRYOVER_DETOUR_REQUIRED)
        if "default_c06_protective_monitor_detour" in c06_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.C06_PROTECTIVE_MONITOR_DETOUR_REQUIRED)

    c06_basis_present = bool(
        state.c06_surfaced_candidate_count > 0
        or state.c06_suppressed_item_count > 0
    )
    if c06_basis_present and state.c06_ambiguous_candidate_count > 0:
        restrictions.append(SubjectTickRestrictionCode.C06_CANDIDATE_AMBIGUITY_DETOUR_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "c06 surfaced ambiguous continuity candidates and requires bounded revalidation"
    if c06_basis_present and state.c06_commitment_carryover_count > 0:
        restrictions.append(SubjectTickRestrictionCode.C06_COMMITMENT_CARRYOVER_DETOUR_REQUIRED)
        if (
            state.c06_confidence_residue_preserved
            and state.c06_published_frontier_requirement_satisfied
            and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = (
                "c06 surfaced commitment carryover with preserved confidence residue and requires bounded continuation handling"
            )
    if c06_basis_present and state.c06_protective_monitor_count > 0:
        restrictions.append(SubjectTickRestrictionCode.C06_PROTECTIVE_MONITOR_DETOUR_REQUIRED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "c06 surfaced protective monitor continuity cue and requires protective-bounded continuation"
    if c06_basis_present and not state.c06_published_frontier_requirement_satisfied:
        restrictions.append(SubjectTickRestrictionCode.C06_FRONTIER_PUBLICATION_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "c06 frontier publication requirement was violated by surfaced candidates"
    if c06_basis_present and not state.c06_confidence_residue_preserved:
        restrictions.append(SubjectTickRestrictionCode.C06_CONFIDENCE_RESIDUE_PRESERVATION_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "c06 confidence residue was not preserved and requires bounded review handling"
    if c06_basis_present and not state.c06_candidate_set_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.C06_CANDIDATE_SET_CONSUMER_REQUIRED)
    if c06_basis_present and not state.c06_suppression_report_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.C06_SUPPRESSION_REPORT_CONSUMER_REQUIRED)
    if c06_basis_present and not state.c06_identity_merge_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.C06_IDENTITY_MERGE_CONSUMER_REQUIRED)
    if c06_checkpoint is not None and c06_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = (
                "c06 surfaced-candidates checkpoint requires detour before downstream continuation"
            )

    p02_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.p02_intervention_episode_checkpoint"
        ),
        None,
    )
    if p02_checkpoint is not None:
        if "require_p02_episode_consumer" in p02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P02_EPISODE_CONSUMER_REQUIRED)
        if "require_p02_boundary_consumer" in p02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P02_BOUNDARY_CONSUMER_REQUIRED)
        if "require_p02_verification_consumer" in p02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P02_VERIFICATION_CONSUMER_REQUIRED)
        if "default_p02_awaiting_verification_detour" in p02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P02_AWAITING_VERIFICATION_DETOUR_REQUIRED)
        if "default_p02_possible_overrun_detour" in p02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P02_POSSIBLE_OVERRUN_DETOUR_REQUIRED)
        if "default_p02_residue_followup_detour" in p02_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P02_RESIDUE_FOLLOWUP_DETOUR_REQUIRED)

    p02_basis_present = bool(
        state.p02_episode_count > 0
        or state.p02_residue_count > 0
        or state.p02_awaiting_verification
    )
    if p02_basis_present and state.p02_awaiting_verification:
        restrictions.append(SubjectTickRestrictionCode.P02_AWAITING_VERIFICATION_DETOUR_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.P02_COMPLETION_INFLATION_FORBIDDEN)
        if (
            state.p02_overrun_detected
            and state.p02_license_link_missing
            and state.final_execution_outcome == SubjectTickOutcome.CONTINUE
        ):
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p02 detected licensed-action uncertainty with possible overrun and blocks optimistic completion"
        elif (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "p02 awaiting verification keeps continuation bounded until outcome verification is resolved"
    if p02_basis_present and state.p02_overrun_detected:
        restrictions.append(SubjectTickRestrictionCode.P02_POSSIBLE_OVERRUN_DETOUR_REQUIRED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p02 detected intervention overrun and requires strict bounded detour before continuation"
    if p02_basis_present and state.p02_residue_count > 0:
        restrictions.append(SubjectTickRestrictionCode.P02_RESIDUE_FOLLOWUP_DETOUR_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "p02 residue remains after intervention episode and requires bounded follow-up handoff"
    if (
        p02_basis_present
        and state.p02_partial_episode_count > 0
        and not state.p02_awaiting_verification
        and not state.p02_overrun_detected
    ):
        restrictions.append(SubjectTickRestrictionCode.P02_EPISODE_CONSUMER_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "p02 partial intervention episode requires bounded continuation and explicit episode consumer handling"
    if p02_basis_present and state.p02_boundary_ambiguous:
        restrictions.append(SubjectTickRestrictionCode.P02_BOUNDARY_CONSUMER_REQUIRED)
    if p02_basis_present and state.p02_license_link_missing:
        restrictions.append(SubjectTickRestrictionCode.P02_EPISODE_CONSUMER_REQUIRED)
    if p02_basis_present and not state.p02_verification_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P02_VERIFICATION_CONSUMER_REQUIRED)
    if p02_basis_present and not state.p02_episode_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P02_EPISODE_CONSUMER_REQUIRED)
    if p02_basis_present and not state.p02_boundary_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P02_BOUNDARY_CONSUMER_REQUIRED)
    if p02_checkpoint is not None and p02_checkpoint.status.value != "allowed":
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p02 intervention-episode checkpoint requires detour before downstream continuation"

    p03_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.p03_credit_assignment_checkpoint"
        ),
        None,
    )
    if p03_checkpoint is not None:
        if "require_p03_credit_record_consumer" in p03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P03_CREDIT_RECORD_CONSUMER_REQUIRED)
        if "require_p03_no_update_consumer" in p03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P03_NO_UPDATE_CONSUMER_REQUIRED)
        if "require_p03_update_recommendation_consumer" in p03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P03_UPDATE_RECOMMENDATION_CONSUMER_REQUIRED
            )
        if "default_p03_confounded_association_detour" in p03_checkpoint.required_action:
            restrictions.append(
                SubjectTickRestrictionCode.P03_CONFOUNDED_ASSOCIATION_DETOUR_REQUIRED
            )
        if "default_p03_outcome_window_open_detour" in p03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P03_OUTCOME_WINDOW_OPEN_DETOUR_REQUIRED)
        if "default_p03_negative_side_effect_detour" in p03_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P03_NEGATIVE_SIDE_EFFECT_DETOUR_REQUIRED)

    p03_basis_present = bool(
        state.p03_evaluated_episode_count > 0
        or state.p03_credit_record_count > 0
        or state.p03_no_update_count > 0
        or state.p03_window_open_count > 0
        or state.p03_confounded_credit_count > 0
    )
    if p03_basis_present:
        restrictions.append(
            SubjectTickRestrictionCode.P03_RAW_OUTCOME_IMPRESSION_LEARNING_FORBIDDEN
        )
    if p03_basis_present and state.p03_window_open_count > 0:
        restrictions.append(SubjectTickRestrictionCode.P03_OUTCOME_WINDOW_OPEN_DETOUR_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "p03 outcome window remains open; continuation stays bounded with no-update discipline"
    if p03_basis_present and state.p03_confounded_credit_count > 0:
        restrictions.append(SubjectTickRestrictionCode.P03_CONFOUNDED_ASSOCIATION_DETOUR_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p03 confounded association blocks confident downstream continuation"
    if p03_basis_present and state.p03_side_effect_dominant_count > 0:
        restrictions.append(SubjectTickRestrictionCode.P03_NEGATIVE_SIDE_EFFECT_DETOUR_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "p03 retained dominant negative side-effects and requires guarded continuation"
    if p03_basis_present and state.p03_negative_credit_count > 0 and state.p03_guarded_update_count > 0:
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p03 negative guarded recommendation blocks optimistic continuation"
    if p03_basis_present and not state.p03_credit_record_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P03_CREDIT_RECORD_CONSUMER_REQUIRED)
    if p03_basis_present and not state.p03_no_update_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P03_NO_UPDATE_CONSUMER_REQUIRED)
    if p03_basis_present and not state.p03_update_recommendation_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P03_UPDATE_RECOMMENDATION_CONSUMER_REQUIRED)
    if p03_basis_present and not state.p03_downstream_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p03 produced no consumer-ready attribution surface for downstream learning path"

    p04_checkpoint = next(
        (
            checkpoint
            for checkpoint in state.execution_checkpoints
            if checkpoint.checkpoint_id == "rt01.p04_counterfactual_policy_simulation_checkpoint"
        ),
        None,
    )
    if p04_checkpoint is not None:
        if "require_p04_branch_record_consumer" in p04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P04_BRANCH_RECORD_CONSUMER_REQUIRED)
        if "require_p04_comparison_consumer" in p04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P04_COMPARISON_CONSUMER_REQUIRED)
        if "require_p04_excluded_policy_consumer" in p04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P04_EXCLUDED_POLICY_CONSUMER_REQUIRED)
        if "default_p04_unstable_region_detour" in p04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P04_UNSTABLE_REGION_DETOUR_REQUIRED)
        if "default_p04_no_clear_dominance_detour" in p04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P04_NO_CLEAR_DOMINANCE_DETOUR_REQUIRED)
        if "default_p04_excluded_policy_hazard_detour" in p04_checkpoint.required_action:
            restrictions.append(SubjectTickRestrictionCode.P04_EXCLUDED_POLICY_HAZARD_DETOUR_REQUIRED)

    p04_basis_present = bool(
        state.p04_branch_count > 0
        or state.p04_excluded_policy_count > 0
        or state.p04_unstable_region_count > 0
        or state.p04_no_clear_dominance_count > 0
    )
    if p04_basis_present and state.p04_unstable_region_count > 0:
        restrictions.append(SubjectTickRestrictionCode.P04_UNSTABLE_REGION_DETOUR_REQUIRED)
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p04 unstable region blocks clear branch ranking and requires bounded comparison-only detour"
    if p04_basis_present and state.p04_no_clear_dominance_count > 0:
        restrictions.append(SubjectTickRestrictionCode.P04_NO_CLEAR_DOMINANCE_DETOUR_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "p04 found no clear branch dominance; continuation remains bounded and comparison-only"
    if p04_basis_present and state.p04_guardrail_exclusion_count > 0:
        restrictions.append(SubjectTickRestrictionCode.P04_EXCLUDED_POLICY_HAZARD_DETOUR_REQUIRED)
        if (
            state.final_execution_outcome == SubjectTickOutcome.CONTINUE
            and usability == SubjectTickUsabilityClass.USABLE_BOUNDED
        ):
            usability = SubjectTickUsabilityClass.DEGRADED_BOUNDED
            reason = "p04 excluded guardrail-violating policies and requires hazard-aware continuation"
    if p04_basis_present and not state.p04_branch_record_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P04_BRANCH_RECORD_CONSUMER_REQUIRED)
    if p04_basis_present and not state.p04_comparison_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P04_COMPARISON_CONSUMER_REQUIRED)
    if p04_basis_present and state.p04_excluded_policy_count > 0 and not state.p04_excluded_policy_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.P04_EXCLUDED_POLICY_CONSUMER_REQUIRED)
    if p04_basis_present and not state.p04_downstream_consumer_ready:
        restrictions.append(SubjectTickRestrictionCode.DOWNSTREAM_AUTHORITY_DEGRADED)
        if state.final_execution_outcome == SubjectTickOutcome.CONTINUE:
            accepted = False
            usability = SubjectTickUsabilityClass.BLOCKED
            reason = "p04 produced no consumer-ready simulation surface for downstream branch comparison"

    return SubjectTickGateDecision(
        accepted=accepted,
        usability_class=usability,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=reason,
        state_ref=f"{state.tick_id}@{state.tick_index}",
    )
