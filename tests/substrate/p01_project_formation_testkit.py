from __future__ import annotations

from dataclasses import dataclass

from substrate.p01_project_formation import (
    P01AuthoritySourceKind,
    P01IntentionStackState,
    P01PriorityClass,
    P01ProjectSignalInput,
    build_p01_project_formation,
)
from tests.substrate.o03_strategy_class_evaluation_testkit import (
    build_o03_harness_case,
    harness_cases as o03_harness_cases,
)


@dataclass(frozen=True, slots=True)
class P01HarnessCase:
    case_id: str
    tick_index: int
    signals: tuple[P01ProjectSignalInput, ...]
    o03_case_id: str | None = "cooperative_transparent"
    formation_enabled: bool = True


def p01_signal(
    *,
    signal_id: str,
    authority: P01AuthoritySourceKind,
    target: str,
    grounded: bool = True,
    signal_kind: str = "directive",
    open_loop_marker: bool = False,
    blocker_present: bool = False,
    missing_precondition_marker: bool = False,
    completion_evidence_present: bool = False,
    policy_disallow_marker: bool = False,
    clarification_block_marker: bool = False,
    temporal_validity_marker: bool = True,
    persistent_obligation_marker: bool = False,
    conflict_group_id: str | None = None,
    priority_hint: P01PriorityClass | None = None,
    continuation_of_prior_project_id: str | None = None,
) -> P01ProjectSignalInput:
    return P01ProjectSignalInput(
        signal_id=signal_id,
        signal_kind=signal_kind,
        authority_source_kind=authority,
        target_summary=target,
        grounded_basis_present=grounded,
        open_loop_marker=open_loop_marker,
        blocker_present=blocker_present,
        missing_precondition_marker=missing_precondition_marker,
        temporal_validity_marker=temporal_validity_marker,
        continuation_of_prior_project_id=continuation_of_prior_project_id,
        completion_evidence_present=completion_evidence_present,
        policy_disallow_marker=policy_disallow_marker,
        clarification_block_marker=clarification_block_marker,
        priority_hint=priority_hint,
        persistent_obligation_marker=persistent_obligation_marker,
        conflict_group_id=conflict_group_id,
        provenance=f"tests.p01.signal:{signal_id}",
    )


def build_p01_harness_case(
    case: P01HarnessCase,
    *,
    prior_state: P01IntentionStackState | None = None,
):
    o03_result = (
        build_o03_harness_case(o03_harness_cases()[case.o03_case_id])
        if case.o03_case_id is not None
        else None
    )
    return build_p01_project_formation(
        tick_id=f"p01:{case.case_id}:{case.tick_index}",
        tick_index=case.tick_index,
        signals=case.signals,
        prior_state=prior_state,
        o03_result=o03_result,
        source_lineage=(f"tests.p01:{case.case_id}",),
        formation_enabled=case.formation_enabled,
    )


def harness_cases() -> dict[str, P01HarnessCase]:
    return {
        "user_directive": P01HarnessCase(
            case_id="user_directive",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="p1",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                ),
            ),
        ),
        "standing_obligation": P01HarnessCase(
            case_id="standing_obligation",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="p2",
                    authority=P01AuthoritySourceKind.STANDING_OBLIGATION,
                    target="prepare nightly reviewer run",
                    signal_kind="obligation",
                    persistent_obligation_marker=True,
                ),
            ),
        ),
        "low_authority_suggestion": P01HarnessCase(
            case_id="low_authority_suggestion",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="p3",
                    authority=P01AuthoritySourceKind.LOW_AUTHORITY_SUGGESTION,
                    target="prepare nightly reviewer run",
                    signal_kind="suggestion",
                ),
            ),
        ),
        "disallowed_self_generated": P01HarnessCase(
            case_id="disallowed_self_generated",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="p4",
                    authority=P01AuthoritySourceKind.DISALLOWED_SELF_GENERATED_IDEA,
                    target="launch unrelated autonomous initiative",
                ),
            ),
        ),
        "missing_precondition": P01HarnessCase(
            case_id="missing_precondition",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="p5",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prepare nightly reviewer run",
                    missing_precondition_marker=True,
                    blocker_present=True,
                ),
            ),
        ),
        "conflict_pair_equal_authority": P01HarnessCase(
            case_id="conflict_pair_equal_authority",
            tick_index=1,
            signals=(
                p01_signal(
                    signal_id="p6a",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prioritize exhaustive diagnostics",
                    conflict_group_id="group-a",
                ),
                p01_signal(
                    signal_id="p6b",
                    authority=P01AuthoritySourceKind.EXPLICIT_USER_DIRECTIVE,
                    target="prioritize minimal quick turnaround",
                    conflict_group_id="group-a",
                ),
            ),
        ),
        "disabled": P01HarnessCase(
            case_id="disabled",
            tick_index=1,
            signals=(),
            o03_case_id=None,
            formation_enabled=False,
        ),
    }

