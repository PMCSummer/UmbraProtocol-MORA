from __future__ import annotations

from .models import (
    AB7AutomationReadinessStatus,
    AB7ConstraintStatus,
    AB7RecipeAutomationInput,
    AB7RecipeAutomationAbductiveFrame,
    AB7Telemetry,
)


def build_ab7_telemetry(
    *,
    candidate_input: AB7RecipeAutomationInput,
    frame: AB7RecipeAutomationAbductiveFrame | None,
    unsafe_basis_count: int,
) -> AB7Telemetry:
    constraints = frame.abductive_constraints if frame is not None else ()
    readiness = frame.automation_readiness if frame is not None else ()
    return AB7Telemetry(
        tick_ref=candidate_input.tick_ref,
        recipe_candidate_count=len(candidate_input.recipe_candidates),
        precursor_candidate_count=len(candidate_input.precursor_candidates),
        constraint_count=len(constraints),
        blocked_constraint_count=sum(1 for item in constraints if item.status is AB7ConstraintStatus.BLOCKED),
        unsatisfied_constraint_count=sum(1 for item in constraints if item.status is AB7ConstraintStatus.UNSATISFIED),
        binding_count=len(frame.bindings) if frame is not None else 0,
        blocked_readiness_count=sum(
            1
            for item in readiness
            if item.readiness_status in {AB7AutomationReadinessStatus.BLOCKED, AB7AutomationReadinessStatus.AUTOMATION_FORBIDDEN_IN_AB7}
        ),
        provisional_readiness_count=sum(
            1
            for item in readiness
            if item.readiness_status in {AB7AutomationReadinessStatus.PROVISIONAL_ONLY, AB7AutomationReadinessStatus.EVIDENCE_REQUIRED}
        ),
        unsafe_basis_count=unsafe_basis_count,
        no_frame_count=1 if frame is None else 0,
    )
