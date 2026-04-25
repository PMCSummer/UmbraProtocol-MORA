from __future__ import annotations

from dataclasses import dataclass

from substrate.c06_surfacing_candidates import (
    C06SurfacingInput,
    C06SurfacingResult,
    build_c06_surfacing_candidates,
)
from substrate.o04_rupture_hostility_coercion import O04DynamicResult
from substrate.p01_project_formation import P01ProjectFormationResult
from substrate.p02_intervention_episode_layer_licensed_action_trace import (
    P02ExecutionEvent,
    P02InterventionEpisodeInput,
    P02InterventionEpisodeResult,
    P02LicensedActionSnapshot,
    P02OutcomeEvidence,
    build_p02_intervention_episode_layer_licensed_action_trace,
)
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
class P02HarnessCase:
    case_id: str
    tick_index: int
    v02_case_key: str
    episode_input: P02InterventionEpisodeInput | None = None
    c06_input: C06SurfacingInput | None = None
    realization_input: V03RealizationInput | None = None
    r05_result: R05ProtectiveResult | None = None
    p01_result: P01ProjectFormationResult | None = None
    o04_result: O04DynamicResult | None = None
    episode_enabled: bool = True


def p02_license_snapshot(
    *,
    action_id: str,
    source_license_ref: str,
    license_scope_ref: str,
    allowed: bool = True,
    project_ref: str | None = None,
) -> P02LicensedActionSnapshot:
    return P02LicensedActionSnapshot(
        action_id=action_id,
        source_license_ref=source_license_ref,
        license_scope_ref=license_scope_ref,
        project_ref=project_ref,
        allowed=allowed,
        provenance=f"tests.p02.license:{action_id}",
    )


def p02_execution_event(
    *,
    event_id: str,
    action_ref: str,
    event_kind: str,
    order_index: int,
    source_license_ref: str | None = None,
    project_ref: str | None = None,
    continuation_hint: bool = True,
    new_episode_hint: bool = False,
) -> P02ExecutionEvent:
    return P02ExecutionEvent(
        event_id=event_id,
        action_ref=action_ref,
        event_kind=event_kind,
        order_index=order_index,
        source_license_ref=source_license_ref,
        project_ref=project_ref,
        continuation_hint=continuation_hint,
        new_episode_hint=new_episode_hint,
        provenance=f"tests.p02.event:{event_id}",
    )


def p02_outcome_evidence(
    *,
    evidence_id: str,
    action_ref: str,
    evidence_kind: str,
    verified: bool = False,
    conflicting: bool = False,
) -> P02OutcomeEvidence:
    return P02OutcomeEvidence(
        evidence_id=evidence_id,
        action_ref=action_ref,
        evidence_kind=evidence_kind,
        verified=verified,
        conflicting=conflicting,
        provenance=f"tests.p02.evidence:{evidence_id}",
    )


def p02_episode_input(
    *,
    input_id: str,
    licensed_actions: tuple[P02LicensedActionSnapshot, ...] = (),
    execution_events: tuple[P02ExecutionEvent, ...] = (),
    outcome_evidence: tuple[P02OutcomeEvidence, ...] = (),
    side_effect_refs: tuple[str, ...] = (),
    project_refs: tuple[str, ...] = (),
) -> P02InterventionEpisodeInput:
    return P02InterventionEpisodeInput(
        input_id=input_id,
        licensed_actions=licensed_actions,
        execution_events=execution_events,
        outcome_evidence=outcome_evidence,
        side_effect_refs=side_effect_refs,
        project_refs=project_refs,
        provenance=f"tests.p02.input:{input_id}",
    )


def build_p02_harness_case(case: P02HarnessCase) -> P02InterventionEpisodeResult:
    v02_case_map = v02_harness_cases()
    if case.v02_case_key not in v02_case_map:
        raise KeyError(f"unknown v02 harness case: {case.v02_case_key}")
    v02_case: V02HarnessCase = v02_case_map[case.v02_case_key]
    r05_result = case.r05_result if case.r05_result is not None else v02_case.r05_result
    p01_result = case.p01_result if case.p01_result is not None else v02_case.p01_result
    v01_result: V01LicenseResult = build_v01_normative_permission_commitment_licensing(
        tick_id=f"v01-for-p02:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        act_candidates=v02_case.act_candidates,
        r05_result=r05_result,
        source_lineage=(f"tests.p02.v01:{case.case_id}",),
    )
    v02_result: V02UtterancePlanResult = build_v02_communicative_intent_utterance_plan_bridge(
        tick_id=f"v02-for-p02:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        v01_result=v01_result,
        r05_result=r05_result,
        o04_result=case.o04_result,
        p01_result=p01_result,
        plan_input=v02_case.plan_input,
        source_lineage=(f"tests.p02.v02:{case.case_id}",),
        prior_state=v02_case.prior_state,
        planning_enabled=v02_case.planning_enabled,
    )
    v03_result: V03ConstrainedRealizationResult = (
        build_v03_surface_verbalization_causality_constrained_realization(
            tick_id=f"v03-for-p02:{case.case_id}:{case.tick_index}",
            tick_index=case.tick_index,
            v02_result=v02_result,
            v01_result=v01_result,
            realization_input=case.realization_input,
            source_lineage=(f"tests.p02.v03:{case.case_id}",),
        )
    )
    c06_result: C06SurfacingResult = build_c06_surfacing_candidates(
        tick_id=f"c06-for-p02:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        v03_result=v03_result,
        v02_result=v02_result,
        v01_result=v01_result,
        p01_result=p01_result,
        o04_result=case.o04_result,
        r05_result=r05_result,
        surfacing_input=case.c06_input,
        source_lineage=(f"tests.p02.c06:{case.case_id}",),
    )
    return build_p02_intervention_episode_layer_licensed_action_trace(
        tick_id=f"p02:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        c06_result=c06_result,
        v03_result=v03_result,
        v02_result=v02_result,
        v01_result=v01_result,
        episode_input=case.episode_input,
        source_lineage=(f"tests.p02:{case.case_id}",),
        episode_enabled=case.episode_enabled,
    )


def harness_cases() -> dict[str, P02HarnessCase]:
    licensed = p02_license_snapshot(
        action_id="act:episode-step",
        source_license_ref="v01:licensed:act:episode-step",
        license_scope_ref="assertion",
        allowed=True,
    )
    base_event = p02_execution_event(
        event_id="ev:1",
        action_ref="act:episode-step",
        event_kind="executed",
        order_index=1,
        source_license_ref=licensed.source_license_ref,
    )
    return {
        "schema_baseline": P02HarnessCase(
            case_id="schema_baseline",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="schema-baseline",
                licensed_actions=(licensed,),
                execution_events=(base_event,),
                outcome_evidence=(
                    p02_outcome_evidence(
                        evidence_id="e:verified-success",
                        action_ref="act:episode-step",
                        evidence_kind="verified_success",
                        verified=True,
                    ),
                ),
            ),
        ),
        "same_events_license_ok": P02HarnessCase(
            case_id="same_events_license_ok",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="same-events-license-ok",
                licensed_actions=(licensed,),
                execution_events=(base_event,),
                outcome_evidence=(
                    p02_outcome_evidence(
                        evidence_id="e:ok",
                        action_ref="act:episode-step",
                        evidence_kind="verified_success",
                        verified=True,
                    ),
                ),
            ),
        ),
        "same_events_license_missing": P02HarnessCase(
            case_id="same_events_license_missing",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="same-events-license-missing",
                licensed_actions=(),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:1",
                        action_ref="act:episode-step",
                        event_kind="executed",
                        order_index=1,
                    ),
                ),
            ),
        ),
        "same_execution_outcome_variants_verified": P02HarnessCase(
            case_id="same_execution_outcome_variants_verified",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="execution-verified",
                licensed_actions=(licensed,),
                execution_events=(base_event,),
                outcome_evidence=(
                    p02_outcome_evidence(
                        evidence_id="e:verified",
                        action_ref="act:episode-step",
                        evidence_kind="verified_success",
                        verified=True,
                    ),
                ),
            ),
        ),
        "same_execution_outcome_variants_unverified": P02HarnessCase(
            case_id="same_execution_outcome_variants_unverified",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="execution-unverified",
                licensed_actions=(licensed,),
                execution_events=(base_event,),
            ),
        ),
        "same_execution_outcome_variants_conflicted": P02HarnessCase(
            case_id="same_execution_outcome_variants_conflicted",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="execution-conflicted",
                licensed_actions=(licensed,),
                execution_events=(base_event,),
                outcome_evidence=(
                    p02_outcome_evidence(
                        evidence_id="e:success",
                        action_ref="act:episode-step",
                        evidence_kind="verified_success",
                        verified=True,
                    ),
                    p02_outcome_evidence(
                        evidence_id="e:conflict",
                        action_ref="act:episode-step",
                        evidence_kind="verified_failure",
                        conflicting=True,
                    ),
                ),
            ),
        ),
        "boundary_continue": P02HarnessCase(
            case_id="boundary_continue",
            tick_index=1,
            v02_case_key="assertion_with_unresolved_history",
            episode_input=p02_episode_input(
                input_id="boundary-continue",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:1",
                        action_ref="act:episode-step",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                    p02_execution_event(
                        event_id="ev:2",
                        action_ref="act:episode-step",
                        event_kind="retry",
                        order_index=2,
                        source_license_ref=licensed.source_license_ref,
                        continuation_hint=True,
                    ),
                ),
            ),
        ),
        "boundary_split": P02HarnessCase(
            case_id="boundary_split",
            tick_index=1,
            v02_case_key="assertion_with_unresolved_history",
            episode_input=p02_episode_input(
                input_id="boundary-split",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:1",
                        action_ref="act:episode-step",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                    p02_execution_event(
                        event_id="ev:2",
                        action_ref="act:episode-step:next",
                        event_kind="executed",
                        order_index=2,
                        new_episode_hint=True,
                    ),
                ),
            ),
        ),
        "boundary_adversarial_hint_conflict": P02HarnessCase(
            case_id="boundary_adversarial_hint_conflict",
            tick_index=1,
            v02_case_key="assertion_with_unresolved_history",
            episode_input=p02_episode_input(
                input_id="boundary-adversarial-hint-conflict",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:1",
                        action_ref="act:episode-step",
                        event_kind="executed",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                    p02_execution_event(
                        event_id="ev:2",
                        action_ref="act:episode-step",
                        event_kind="retry",
                        order_index=2,
                        source_license_ref=licensed.source_license_ref,
                        continuation_hint=True,
                        new_episode_hint=True,
                    ),
                ),
            ),
        ),
        "partial_case": P02HarnessCase(
            case_id="partial_case",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="partial-case",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:partial",
                        action_ref="act:episode-step",
                        event_kind="partial",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
            ),
        ),
        "blocked_case": P02HarnessCase(
            case_id="blocked_case",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="blocked-case",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:blocked",
                        action_ref="act:episode-step",
                        event_kind="blocked",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
            ),
        ),
        "overrun_case": P02HarnessCase(
            case_id="overrun_case",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="overrun-case",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:overrun",
                        action_ref="act:outside-license",
                        event_kind="executed",
                        order_index=1,
                    ),
                ),
            ),
        ),
        "residue_case": P02HarnessCase(
            case_id="residue_case",
            tick_index=1,
            v02_case_key="commitment_split",
            episode_input=p02_episode_input(
                input_id="residue-case",
                licensed_actions=(licensed,),
                execution_events=(base_event,),
                side_effect_refs=("side-effect:pending",),
            ),
        ),
        "anti_completion_inflation": P02HarnessCase(
            case_id="anti_completion_inflation",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_input=p02_episode_input(
                input_id="anti-completion-inflation",
                licensed_actions=(licensed,),
                execution_events=(
                    p02_execution_event(
                        event_id="ev:emitted",
                        action_ref="act:episode-step",
                        event_kind="emitted",
                        order_index=1,
                        source_license_ref=licensed.source_license_ref,
                    ),
                ),
            ),
        ),
        "disabled": P02HarnessCase(
            case_id="disabled",
            tick_index=1,
            v02_case_key="assertion_base",
            episode_enabled=False,
        ),
        "no_basis": P02HarnessCase(
            case_id="no_basis",
            tick_index=1,
            v02_case_key="no_basis",
        ),
    }
