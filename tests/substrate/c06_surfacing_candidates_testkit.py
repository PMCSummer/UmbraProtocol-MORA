from __future__ import annotations

from dataclasses import dataclass

from substrate.c06_surfacing_candidates import (
    C06SurfacingInput,
    C06SurfacingResult,
    build_c06_surfacing_candidates,
)
from substrate.o04_rupture_hostility_coercion import O04DynamicResult
from substrate.p01_project_formation import P01ProjectFormationResult
from substrate.r05_appraisal_sovereign_protective_regulation import R05ProtectiveResult
from substrate.v01_normative_permission_commitment_licensing import (
    V01LicenseResult,
    build_v01_normative_permission_commitment_licensing,
)
from substrate.v02_communicative_intent_utterance_plan_bridge import (
    V02UtterancePlanResult,
    build_v02_communicative_intent_utterance_plan_bridge,
)
from substrate.v03_surface_verbalization_causality_constrained_realization import (
    V03ConstrainedRealizationResult,
    V03RealizationInput,
    build_v03_surface_verbalization_causality_constrained_realization,
)
from tests.substrate.v02_communicative_intent_utterance_plan_bridge_testkit import (
    V02HarnessCase,
    harness_cases as v02_harness_cases,
)


@dataclass(frozen=True, slots=True)
class C06HarnessCase:
    case_id: str
    tick_index: int
    v02_case_key: str
    surfacing_input: C06SurfacingInput | None = None
    realization_input: V03RealizationInput | None = None
    r05_result: R05ProtectiveResult | None = None
    p01_result: P01ProjectFormationResult | None = None
    o04_result: O04DynamicResult | None = None
    surfacing_enabled: bool = True


def c06_input(
    *,
    input_id: str,
    prior_unresolved_question_present: bool = False,
    prior_commitment_carry_present: bool = False,
    prior_repair_open: bool = False,
    closure_resolved: bool = False,
    discourse_state_tag: str = "open_discourse",
    published_frontier_item_ids: tuple[str, ...] = (),
    workspace_item_ids: tuple[str, ...] = (),
    unresolved_ambiguity_tokens: tuple[str, ...] = (),
    confidence_residue_tokens: tuple[str, ...] = (),
    salient_but_resolved_fragments: tuple[str, ...] = (),
    published_frontier_requirement: bool = True,
    unresolved_ambiguity_preservation_required: bool = True,
    confidence_residue_preservation_required: bool = True,
) -> C06SurfacingInput:
    return C06SurfacingInput(
        input_id=input_id,
        prior_unresolved_question_present=prior_unresolved_question_present,
        prior_commitment_carry_present=prior_commitment_carry_present,
        prior_repair_open=prior_repair_open,
        closure_resolved=closure_resolved,
        discourse_state_tag=discourse_state_tag,
        published_frontier_item_ids=published_frontier_item_ids,
        workspace_item_ids=workspace_item_ids,
        unresolved_ambiguity_tokens=unresolved_ambiguity_tokens,
        confidence_residue_tokens=confidence_residue_tokens,
        salient_but_resolved_fragments=salient_but_resolved_fragments,
        published_frontier_requirement=published_frontier_requirement,
        unresolved_ambiguity_preservation_required=unresolved_ambiguity_preservation_required,
        confidence_residue_preservation_required=confidence_residue_preservation_required,
        provenance=f"tests.c06.input:{input_id}",
    )


def build_c06_harness_case(case: C06HarnessCase) -> C06SurfacingResult:
    v02_case_map = v02_harness_cases()
    if case.v02_case_key not in v02_case_map:
        raise KeyError(f"unknown v02 harness case: {case.v02_case_key}")
    v02_case: V02HarnessCase = v02_case_map[case.v02_case_key]
    r05_result = case.r05_result if case.r05_result is not None else v02_case.r05_result
    p01_result = case.p01_result if case.p01_result is not None else v02_case.p01_result

    v01_result: V01LicenseResult = build_v01_normative_permission_commitment_licensing(
        tick_id=f"v01-for-c06:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        act_candidates=v02_case.act_candidates,
        r05_result=r05_result,
        source_lineage=(f"tests.c06.v01:{case.case_id}",),
    )
    v02_result: V02UtterancePlanResult = build_v02_communicative_intent_utterance_plan_bridge(
        tick_id=f"v02-for-c06:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        v01_result=v01_result,
        r05_result=r05_result,
        o04_result=case.o04_result,
        p01_result=p01_result,
        plan_input=v02_case.plan_input,
        source_lineage=(f"tests.c06.v02:{case.case_id}",),
        prior_state=v02_case.prior_state,
        planning_enabled=v02_case.planning_enabled,
    )
    v03_result: V03ConstrainedRealizationResult = (
        build_v03_surface_verbalization_causality_constrained_realization(
            tick_id=f"v03-for-c06:{case.case_id}:{case.tick_index}",
            tick_index=case.tick_index,
            v02_result=v02_result,
            v01_result=v01_result,
            realization_input=case.realization_input,
            source_lineage=(f"tests.c06.v03:{case.case_id}",),
        )
    )
    return build_c06_surfacing_candidates(
        tick_id=f"c06:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        v03_result=v03_result,
        v02_result=v02_result,
        v01_result=v01_result,
        p01_result=p01_result,
        o04_result=case.o04_result,
        r05_result=r05_result,
        surfacing_input=case.surfacing_input,
        source_lineage=(f"tests.c06:{case.case_id}",),
        surfacing_enabled=case.surfacing_enabled,
    )


def harness_cases() -> dict[str, C06HarnessCase]:
    return {
        "baseline_assertion": C06HarnessCase(
            case_id="baseline_assertion",
            tick_index=1,
            v02_case_key="assertion_base",
        ),
        "same_text_commitment_carry": C06HarnessCase(
            case_id="same_text_commitment_carry",
            tick_index=1,
            v02_case_key="assertion_base",
            surfacing_input=c06_input(
                input_id="same-text-commitment",
                prior_commitment_carry_present=True,
                confidence_residue_tokens=("confidence:carryover",),
            ),
        ),
        "salience_vs_continuity": C06HarnessCase(
            case_id="salience_vs_continuity",
            tick_index=1,
            v02_case_key="commitment_split",
            surfacing_input=c06_input(
                input_id="salience-vs-continuity",
                prior_commitment_carry_present=True,
                confidence_residue_tokens=("confidence:carryover",),
                salient_but_resolved_fragments=("flourish-token", "vivid-phrase"),
            ),
        ),
        "dedup_commitment_repeat": C06HarnessCase(
            case_id="dedup_commitment_repeat",
            tick_index=1,
            v02_case_key="commitment_split",
            surfacing_input=c06_input(
                input_id="dedup-commitment-repeat",
                prior_commitment_carry_present=True,
                confidence_residue_tokens=("confidence:carryover",),
            ),
        ),
        "false_merge_guard": C06HarnessCase(
            case_id="false_merge_guard",
            tick_index=1,
            v02_case_key="assertion_with_unresolved_history",
            surfacing_input=c06_input(
                input_id="false-merge-guard",
                prior_unresolved_question_present=True,
            ),
        ),
        "c06_1_workspace_handoff": C06HarnessCase(
            case_id="c06_1_workspace_handoff",
            tick_index=1,
            v02_case_key="assertion_base",
            surfacing_input=c06_input(
                input_id="workspace-handoff",
                prior_unresolved_question_present=True,
                prior_commitment_carry_present=True,
                workspace_item_ids=("workspace:item:1", "workspace:item:2"),
                published_frontier_item_ids=("workspace:item:2",),
                unresolved_ambiguity_tokens=("ambiguity:1",),
                confidence_residue_tokens=("residue:1",),
            ),
        ),
        "c06_1_workspace_published_only": C06HarnessCase(
            case_id="c06_1_workspace_published_only",
            tick_index=1,
            v02_case_key="assertion_base",
            surfacing_input=c06_input(
                input_id="workspace-published-only",
                prior_unresolved_question_present=True,
                prior_commitment_carry_present=True,
                workspace_item_ids=("workspace:item:published",),
                published_frontier_item_ids=("workspace:item:published",),
                unresolved_ambiguity_tokens=("ambiguity:1",),
                confidence_residue_tokens=("residue:1",),
            ),
        ),
        "c06_1_workspace_unpublished": C06HarnessCase(
            case_id="c06_1_workspace_unpublished",
            tick_index=1,
            v02_case_key="assertion_base",
            surfacing_input=c06_input(
                input_id="workspace-unpublished",
                prior_unresolved_question_present=True,
                prior_commitment_carry_present=True,
                workspace_item_ids=("workspace:item:unpublished",),
                published_frontier_item_ids=(),
                unresolved_ambiguity_tokens=("ambiguity:1",),
                confidence_residue_tokens=("residue:1",),
            ),
        ),
        "alignment_anchor_baseline": C06HarnessCase(
            case_id="alignment_anchor_baseline",
            tick_index=1,
            v02_case_key="protective_structure",
            surfacing_input=c06_input(
                input_id="alignment-anchor-baseline",
                prior_commitment_carry_present=True,
                confidence_residue_tokens=("residue:alignment",),
            ),
        ),
        "alignment_anchor_underconstrained": C06HarnessCase(
            case_id="alignment_anchor_underconstrained",
            tick_index=1,
            v02_case_key="protective_structure",
            surfacing_input=c06_input(
                input_id="alignment-anchor-underconstrained",
                prior_commitment_carry_present=True,
                confidence_residue_tokens=("residue:alignment",),
            ),
            realization_input=V03RealizationInput(
                input_id="alignment-anchor-underconstrained",
                force_boundary_after_explanation=True,
                provenance="tests.c06.input:alignment-anchor-underconstrained",
            ),
        ),
        "no_basis": C06HarnessCase(
            case_id="no_basis",
            tick_index=1,
            v02_case_key="no_basis",
        ),
        "disabled": C06HarnessCase(
            case_id="disabled",
            tick_index=1,
            v02_case_key="assertion_base",
            surfacing_enabled=False,
        ),
    }
