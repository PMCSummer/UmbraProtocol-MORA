from __future__ import annotations

from dataclasses import dataclass

from substrate.o01_other_entity_model import (
    O01EntitySignal,
    O01OtherEntityModelState,
    build_o01_other_entity_model,
)


def _signal(
    *,
    signal_id: str,
    authority: str,
    relation: str,
    claim: str,
    entity_id_hint: str | None = None,
    referent_label: str | None = None,
    confidence: float = 0.72,
    grounded: bool = True,
    quoted: bool = False,
    turn_index: int = 1,
    target_claim: str | None = None,
) -> O01EntitySignal:
    return O01EntitySignal(
        signal_id=signal_id,
        entity_id_hint=entity_id_hint,
        referent_label=referent_label,
        source_authority=authority,
        relation_class=relation,
        claim_value=claim,
        confidence=confidence,
        grounded=grounded,
        quoted=quoted,
        turn_index=turn_index,
        provenance=f"tests.o01.signal:{signal_id}",
        target_claim=target_claim,
    )


@dataclass(frozen=True, slots=True)
class O01HarnessCase:
    case_id: str
    tick_index: int
    signals: tuple[O01EntitySignal, ...]


def build_o01(
    *,
    case_id: str,
    tick_index: int,
    signals: tuple[O01EntitySignal, ...],
    prior_state: O01OtherEntityModelState | None = None,
    model_enabled: bool = True,
):
    return build_o01_other_entity_model(
        tick_id=f"o01-{case_id}-{tick_index}",
        tick_index=tick_index,
        signals=signals,
        prior_state=prior_state,
        source_lineage=(f"test:o01:{case_id}",),
        model_enabled=model_enabled,
    )


def build_o01_harness_case(
    case: O01HarnessCase,
    *,
    prior_state: O01OtherEntityModelState | None = None,
):
    return build_o01(
        case_id=case.case_id,
        tick_index=case.tick_index,
        signals=case.signals,
        prior_state=prior_state,
    )


def harness_sequences() -> dict[str, O01HarnessCase]:
    return {
        "stable_preference_repeated": O01HarnessCase(
            case_id="stable_preference_repeated",
            tick_index=1,
            signals=(
                _signal(
                    signal_id="sp1",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_concise_answers",
                    referent_label="user",
                ),
                _signal(
                    signal_id="sp2",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_concise_answers",
                    referent_label="user",
                    turn_index=2,
                ),
            ),
        ),
        "temporary_request_one_off": O01HarnessCase(
            case_id="temporary_request_one_off",
            tick_index=1,
            signals=(
                _signal(
                    signal_id="tmp1",
                    authority="current_user_direct",
                    relation="temporary_state",
                    claim="request_fast_reply_now",
                    referent_label="user",
                ),
            ),
        ),
        "revision_correction": O01HarnessCase(
            case_id="revision_correction",
            tick_index=2,
            signals=(
                _signal(
                    signal_id="rc1",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_detailed_answers",
                    referent_label="user",
                ),
                _signal(
                    signal_id="rc2",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_detailed_answers",
                    referent_label="user",
                    turn_index=2,
                ),
                _signal(
                    signal_id="rc3",
                    authority="current_user_direct",
                    relation="correction",
                    claim="not_detailed_anymore",
                    referent_label="user",
                    target_claim="prefers_detailed_answers",
                    turn_index=3,
                ),
            ),
        ),
        "revision_contradiction_preserved": O01HarnessCase(
            case_id="revision_contradiction_preserved",
            tick_index=3,
            signals=(
                _signal(
                    signal_id="cp1",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="uses_terminal",
                    referent_label="user",
                ),
                _signal(
                    signal_id="cp2",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="not:uses_terminal",
                    referent_label="user",
                    turn_index=2,
                ),
                _signal(
                    signal_id="cp3",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="uses_terminal",
                    referent_label="user",
                    turn_index=3,
                ),
                _signal(
                    signal_id="cp4",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="not:uses_terminal",
                    referent_label="user",
                    turn_index=4,
                ),
            ),
        ),
        "third_party_quoted": O01HarnessCase(
            case_id="third_party_quoted",
            tick_index=2,
            signals=(
                _signal(
                    signal_id="tp1",
                    authority="quoted_third_party",
                    relation="stable_claim",
                    claim="prefers_verbose",
                    entity_id_hint="third_party:alex",
                    referent_label="alex",
                    quoted=True,
                ),
                _signal(
                    signal_id="tp1b",
                    authority="quoted_third_party",
                    relation="stable_claim",
                    claim="prefers_verbose",
                    entity_id_hint="third_party:alex",
                    referent_label="alex",
                    quoted=True,
                    turn_index=2,
                ),
                _signal(
                    signal_id="tp2",
                    authority="current_user_direct",
                    relation="goal_hint",
                    claim="wants_short_answer",
                    referent_label="user",
                    turn_index=2,
                ),
            ),
        ),
        "referenced_other_separate": O01HarnessCase(
            case_id="referenced_other_separate",
            tick_index=2,
            signals=(
                _signal(
                    signal_id="ro1",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="prefers_structured_lists",
                    referent_label="user",
                ),
                _signal(
                    signal_id="ro2",
                    authority="referenced_other",
                    relation="goal_hint",
                    claim="needs_translation",
                    referent_label="colleague",
                    entity_id_hint="referenced_other:colleague",
                ),
            ),
        ),
        "competing_referent": O01HarnessCase(
            case_id="competing_referent",
            tick_index=2,
            signals=(
                _signal(
                    signal_id="cr1",
                    authority="referenced_other",
                    relation="goal_hint",
                    claim="needs_report",
                    referent_label="manager",
                    entity_id_hint="referenced_other:manager_v1",
                ),
                _signal(
                    signal_id="cr2",
                    authority="referenced_other",
                    relation="goal_hint",
                    claim="needs_report",
                    referent_label="manager",
                    entity_id_hint="referenced_other:manager_v2",
                    turn_index=2,
                ),
            ),
        ),
        "knowledge_unknown": O01HarnessCase(
            case_id="knowledge_unknown",
            tick_index=1,
            signals=(
                _signal(
                    signal_id="ku1",
                    authority="current_user_direct",
                    relation="ignorance",
                    claim="does_not_know_api_rate_limit",
                    referent_label="user",
                ),
            ),
        ),
        "knowledge_later_known": O01HarnessCase(
            case_id="knowledge_later_known",
            tick_index=2,
            signals=(
                _signal(
                    signal_id="kk1",
                    authority="current_user_direct",
                    relation="knowledge_boundary",
                    claim="knows_api_rate_limit_now",
                    referent_label="user",
                ),
                _signal(
                    signal_id="kk2",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="knows_api_rate_limit_now",
                    referent_label="user",
                    turn_index=2,
                ),
                _signal(
                    signal_id="kk3",
                    authority="current_user_direct",
                    relation="stable_claim",
                    claim="knows_api_rate_limit_now",
                    referent_label="user",
                    turn_index=3,
                ),
            ),
        ),
        "projection_adversarial": O01HarnessCase(
            case_id="projection_adversarial",
            tick_index=1,
            signals=(
                _signal(
                    signal_id="pa1",
                    authority="self_internal_bias",
                    relation="stable_claim",
                    claim="prefers_long_storytelling",
                    referent_label="user",
                ),
                _signal(
                    signal_id="pa2",
                    authority="current_user_direct",
                    relation="goal_hint",
                    claim="wants_direct_answer",
                    referent_label="user",
                    turn_index=2,
                ),
            ),
        ),
        "stale_memory_contradiction": O01HarnessCase(
            case_id="stale_memory_contradiction",
            tick_index=3,
            signals=(
                _signal(
                    signal_id="sm1",
                    authority="interaction_grounded",
                    relation="stable_claim",
                    claim="prefers_json",
                    referent_label="user",
                ),
                _signal(
                    signal_id="sm2",
                    authority="current_user_direct",
                    relation="correction",
                    claim="now_prefers_plaintext",
                    referent_label="user",
                    target_claim="prefers_json",
                    turn_index=4,
                ),
            ),
        ),
    }
