from __future__ import annotations

from dataclasses import replace

from substrate.w06_error_driven_revision import (
    W06ConsequenceType,
    W06ContradictionIntakeView,
    W06InputBundle,
    W06MismatchClass,
    W06MismatchIntakeView,
    W06PriorSchemaLineageView,
    W06ResultBundle,
    W06RevisionContext,
    W06RevisionScope,
    build_w06_error_driven_revision,
)


def w06_mismatch(case_id: str, **overrides) -> W06MismatchIntakeView:
    base = W06MismatchIntakeView(
        mismatch_id=f"{case_id}:mismatch:1",
        compared_channels=("predicted", "observed"),
        mismatch_class=W06MismatchClass.PREDICTED_VS_OBSERVED,
        mismatch_direction="predicted_vs_observed",
        severity="medium",
        confidence=0.7,
        evidence_refs=(f"{case_id}:evidence:1",),
        ambiguity_markers=(),
        competing_class_candidates=("world_model", "affordance"),
        target_scope=("local_scope",),
        target_layer="world_model_interface",
        update_candidate_type="bounded_update_candidate",
        execution_prohibited=True,
        constitutional_guard_flags=(),
        required_revalidation=False,
        source_reliability=0.8,
        evidence_precision=0.8,
        prior_strength=0.7,
        effective_prior_gain=0.6,
        provenance=("tests.w06", case_id, "mismatch"),
    )
    return replace(base, **overrides)


def w06_contradiction(case_id: str, **overrides) -> W06ContradictionIntakeView:
    base = W06ContradictionIntakeView(
        contradiction_id=f"{case_id}:contradiction:1",
        conflict_type="trace_conflict",
        conflicting_trace_refs=(f"{case_id}:trace:1", f"{case_id}:trace:2"),
        affected_scope=("local_scope",),
        affected_maturity_level="mixed",
        schema_id=f"{case_id}:schema",
        prior_id=f"{case_id}:prior",
        object_id=f"{case_id}:object",
        severity="medium",
        unresolved_status=True,
        previous_consequence="none",
        evidence_refs=(f"{case_id}:evidence:1",),
        provenance=("tests.w06", case_id, "contradiction"),
    )
    return replace(base, **overrides)


def w06_lineage(case_id: str, **overrides) -> W06PriorSchemaLineageView:
    base = W06PriorSchemaLineageView(
        prior_id=f"{case_id}:prior",
        schema_id=f"{case_id}:schema",
        regularity_id=f"{case_id}:regularity",
        object_id=f"{case_id}:object",
        maturity_level="mixed",
        authority_scope=("bounded_scope",),
        context_scope=("bounded_context",),
        stale_status=False,
        confidence_band="medium",
        negative_evidence_refs=(f"{case_id}:neg:1",),
        contradiction_refs=(),
        prohibited_claims=("no_universal_world_truth", "no_action_authorization"),
    )
    return replace(base, **overrides)


def w06_context(case_id: str, **overrides) -> W06RevisionContext:
    base = W06RevisionContext(
        cycle_id=f"{case_id}:cycle",
        stream_id="rt01",
        temporal_window=(1, 2),
        revalidation_loop_id=f"{case_id}:loop",
        repeated_revalidation_count=0,
        progress_detected=True,
        protected_targets=(),
        allowed_revision_scopes=(
            W06RevisionScope.LOCAL,
            W06RevisionScope.OBJECT_LEVEL,
            W06RevisionScope.SCHEMA_LEVEL,
            W06RevisionScope.AFFORDANCE_LEVEL,
            W06RevisionScope.ACTION_EFFECT_LEVEL,
            W06RevisionScope.OWNERSHIP_LEVEL,
            W06RevisionScope.GOAL_SATISFACTION_LEVEL,
            W06RevisionScope.VALIDITY_LEVEL,
            W06RevisionScope.TEMPORAL_WINDOW_LEVEL,
            W06RevisionScope.POLICY_HINT_LEVEL,
            W06RevisionScope.AUTHORITY_SCOPE_LEVEL,
        ),
        global_revision_allowed=False,
        consumer_id="tests.w06.consumer",
        loop_threshold=3,
    )
    return replace(base, **overrides)


def w06_bundle(case_id: str, **overrides) -> W06InputBundle:
    base = W06InputBundle(
        bundle_id=f"{case_id}:w06:bundle",
        source_lineage=("tests.w06", case_id),
        mismatch_intake=w06_mismatch(case_id),
        contradiction_intake=(w06_contradiction(case_id),),
        lineage_view=w06_lineage(case_id),
        revision_context=w06_context(case_id),
        reason=case_id,
    )
    return replace(base, **overrides)


def build_w06_harness(case_id: str, *, input_bundle: W06InputBundle | None, enforcement_enabled: bool = True) -> W06ResultBundle:
    return build_w06_error_driven_revision(
        tick_id=f"tests.w06:{case_id}",
        tick_index=1,
        input_bundle=input_bundle,
        enforcement_enabled=enforcement_enabled,
    )


def clone_bundle(base: W06InputBundle, **changes) -> W06InputBundle:
    return replace(base, **changes)


def consequence(result: W06ResultBundle) -> W06ConsequenceType:
    return result.decision.consequence_type
