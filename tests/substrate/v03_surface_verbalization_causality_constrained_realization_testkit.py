from __future__ import annotations

from dataclasses import dataclass

from substrate.v01_normative_permission_commitment_licensing import (
    V01LicenseResult,
    build_v01_normative_permission_commitment_licensing,
)
from substrate.v03_surface_verbalization_causality_constrained_realization import (
    V03ConstrainedRealizationResult,
    V03RealizationInput,
    build_v03_surface_verbalization_causality_constrained_realization,
)
from tests.substrate.v02_communicative_intent_utterance_plan_bridge_testkit import (
    V02HarnessCase,
    build_v02_harness_case,
    harness_cases as v02_harness_cases,
)


@dataclass(frozen=True, slots=True)
class V03HarnessCase:
    case_id: str
    tick_index: int
    v02_case_key: str
    realization_input: V03RealizationInput | None = None
    realization_enabled: bool = True


def v03_input(
    *,
    input_id: str,
    surface_variant: str = "default",
    selected_branch_id: str | None = None,
    tamper_qualifier_locality_segment_id: str | None = None,
    inject_blocked_expansion_token: str | None = None,
    inject_protected_omission_token: str | None = None,
    force_boundary_after_explanation: bool = False,
    force_commitment_phrase: bool = False,
    prefer_fluency_over_hard_constraints: bool = False,
) -> V03RealizationInput:
    return V03RealizationInput(
        input_id=input_id,
        surface_variant=surface_variant,
        selected_branch_id=selected_branch_id,
        tamper_qualifier_locality_segment_id=tamper_qualifier_locality_segment_id,
        inject_blocked_expansion_token=inject_blocked_expansion_token,
        inject_protected_omission_token=inject_protected_omission_token,
        force_boundary_after_explanation=force_boundary_after_explanation,
        force_commitment_phrase=force_commitment_phrase,
        prefer_fluency_over_hard_constraints=prefer_fluency_over_hard_constraints,
        provenance=f"tests.v03.input:{input_id}",
    )


def build_v03_harness_case(case: V03HarnessCase) -> V03ConstrainedRealizationResult:
    v02_case_map = v02_harness_cases()
    if case.v02_case_key not in v02_case_map:
        raise KeyError(f"unknown v02 harness case: {case.v02_case_key}")
    v02_case: V02HarnessCase = v02_case_map[case.v02_case_key]
    v01_result: V01LicenseResult = build_v01_normative_permission_commitment_licensing(
        tick_id=f"v01-for-v03:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        act_candidates=v02_case.act_candidates,
        r05_result=v02_case.r05_result,
        source_lineage=(f"tests.v03.v01:{case.case_id}",),
    )
    v02_result = build_v02_harness_case(v02_case)
    return build_v03_surface_verbalization_causality_constrained_realization(
        tick_id=f"v03:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        v02_result=v02_result,
        v01_result=v01_result,
        realization_input=case.realization_input,
        source_lineage=(f"tests.v03:{case.case_id}",),
        realization_enabled=case.realization_enabled,
    )


def harness_cases() -> dict[str, V03HarnessCase]:
    return {
        "baseline_assertion": V03HarnessCase(
            case_id="baseline_assertion",
            tick_index=1,
            v02_case_key="assertion_base",
        ),
        "weak_assertion_with_qualifiers": V03HarnessCase(
            case_id="weak_assertion_with_qualifiers",
            tick_index=1,
            v02_case_key="weak_assertion_qualifier_binding",
        ),
        "qualifier_locality_tamper": V03HarnessCase(
            case_id="qualifier_locality_tamper",
            tick_index=1,
            v02_case_key="weak_assertion_qualifier_binding",
            realization_input=v03_input(
                input_id="qualifier-locality-tamper",
                tamper_qualifier_locality_segment_id="seg:1:qualification",
            ),
        ),
        "blocked_expansion_leak": V03HarnessCase(
            case_id="blocked_expansion_leak",
            tick_index=1,
            v02_case_key="commitment_split",
            realization_input=v03_input(
                input_id="blocked-expansion-leak",
                inject_blocked_expansion_token="expand:promise-for-split-1",
            ),
        ),
        "protective_structure_baseline": V03HarnessCase(
            case_id="protective_structure_baseline",
            tick_index=1,
            v02_case_key="protective_structure",
        ),
        "protected_omission_leak": V03HarnessCase(
            case_id="protected_omission_leak",
            tick_index=1,
            v02_case_key="commitment_split",
            realization_input=v03_input(
                input_id="protected-omission-leak",
                inject_protected_omission_token="omit:promise-for-split-1",
            ),
        ),
        "boundary_order_violation": V03HarnessCase(
            case_id="boundary_order_violation",
            tick_index=1,
            v02_case_key="protective_structure",
            realization_input=v03_input(
                input_id="boundary-after-explanation-tamper",
                force_boundary_after_explanation=True,
            ),
        ),
        "implicit_commitment_leak": V03HarnessCase(
            case_id="implicit_commitment_leak",
            tick_index=1,
            v02_case_key="commitment_split",
            realization_input=v03_input(
                input_id="implicit-commitment-leak",
                force_commitment_phrase=True,
                prefer_fluency_over_hard_constraints=True,
            ),
        ),
        "paraphrase_variant": V03HarnessCase(
            case_id="paraphrase_variant",
            tick_index=1,
            v02_case_key="weak_assertion_qualifier_binding",
            realization_input=v03_input(
                input_id="paraphrase-variant",
                surface_variant="paraphrase",
            ),
        ),
        "no_basis": V03HarnessCase(
            case_id="no_basis",
            tick_index=1,
            v02_case_key="no_basis",
        ),
        "disabled": V03HarnessCase(
            case_id="disabled",
            tick_index=1,
            v02_case_key="assertion_base",
            realization_enabled=False,
        ),
    }
