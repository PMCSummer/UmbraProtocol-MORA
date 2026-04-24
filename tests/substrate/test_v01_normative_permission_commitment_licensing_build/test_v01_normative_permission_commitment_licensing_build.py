from __future__ import annotations

from substrate.v01_normative_permission_commitment_licensing import (
    V01ActType,
    V01CommitmentDeltaKind,
)
from tests.substrate.v01_normative_permission_commitment_licensing_testkit import (
    V01HarnessCase,
    build_v01_harness_case,
    harness_cases,
    v01_candidate,
)


def test_same_content_different_act_type_changes_license_and_commitment() -> None:
    proposition = "prop:same-content-licensing"
    assertion = build_v01_harness_case(
        V01HarnessCase(
            case_id="assertion-contrast",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="assertion-contrast-1",
                    act_type=V01ActType.ASSERTION,
                    proposition_ref=proposition,
                    evidence_strength=0.86,
                    authority_basis_present=True,
                ),
            ),
        )
    )
    advice = build_v01_harness_case(
        V01HarnessCase(
            case_id="advice-contrast",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="advice-contrast-1",
                    act_type=V01ActType.ADVICE,
                    proposition_ref=proposition,
                    evidence_strength=0.86,
                    authority_basis_present=False,
                    helpfulness_pressure=0.9,
                ),
            ),
        )
    )
    promise = build_v01_harness_case(
        V01HarnessCase(
            case_id="promise-contrast",
            tick_index=1,
            act_candidates=(
                v01_candidate(
                    act_id="promise-contrast-1",
                    act_type=V01ActType.PROMISE,
                    proposition_ref=proposition,
                    evidence_strength=0.86,
                    authority_basis_present=True,
                    commitment_target_ref="target:contrast",
                ),
            ),
        )
    )
    assert assertion.state.licensed_act_count == 1
    assert advice.state.denied_act_count == 1
    assert promise.state.commitment_delta_count == 1
    assert advice.state.commitment_delta_count == 0
    assert promise.state.commitment_deltas[0].delta_kind in {
        V01CommitmentDeltaKind.CREATE_COMMITMENT,
        V01CommitmentDeltaKind.COMMITMENT_DENIED,
    }


def test_assertion_licensing_changes_with_evidence_strength() -> None:
    cases = harness_cases()
    strong = build_v01_harness_case(cases["assertion_strong"])
    weak = build_v01_harness_case(cases["assertion_weak"])
    missing = build_v01_harness_case(cases["assertion_missing"])
    assert strong.state.licensed_act_count == 1
    assert strong.state.conditional_act_count == 0
    assert strong.state.mandatory_qualifier_count == 0
    assert weak.state.licensed_act_count == 1
    assert weak.state.conditional_act_count == 1
    assert weak.state.mandatory_qualifier_count > strong.state.mandatory_qualifier_count
    assert missing.state.denied_act_count == 1
    assert missing.state.licensed_act_count == 0
    assert missing.state.denied_acts[0].blocking_reason_code == "insufficient_assertion_basis"


def test_promise_commitment_delta_created_only_when_lawfully_licensed() -> None:
    cases = harness_cases()
    strong = build_v01_harness_case(cases["promise_strong"])
    weakened = build_v01_harness_case(cases["promise_weakened_by_assertion_split"])
    assert strong.state.commitment_delta_count == 1
    assert strong.state.commitment_deltas[0].delta_kind is V01CommitmentDeltaKind.CREATE_COMMITMENT
    assert strong.state.commitment_deltas[0].allowed is True
    assert weakened.state.assertion_allowed_commitment_denied is True
    assert weakened.state.commitment_delta_count == 1
    assert weakened.state.commitment_deltas[0].delta_kind is V01CommitmentDeltaKind.COMMITMENT_DENIED
    assert weakened.state.commitment_deltas[0].allowed is False


def test_assertion_does_not_auto_create_promise_like_commitment() -> None:
    assertion = build_v01_harness_case(harness_cases()["assertion_strong"])
    assert assertion.state.commitment_delta_count == 0
    assert assertion.state.promise_like_act_denied is False


def test_denied_surface_and_blocking_reason_are_preserved() -> None:
    denied = build_v01_harness_case(harness_cases()["advice_helpfulness_shortcut"])
    assert denied.state.denied_act_count == 1
    assert denied.state.denied_acts[0].act_type is V01ActType.ADVICE
    assert denied.state.denied_acts[0].blocking_reason_code == "helpfulness_not_authority_basis"
    assert denied.state.denied_acts[0].alternative_narrowed_act_type is V01ActType.QUESTION


def test_conditional_license_produces_mandatory_qualifier_binding() -> None:
    weak = build_v01_harness_case(harness_cases()["assertion_weak"])
    assert weak.state.conditional_act_count == 1
    assert weak.state.mandatory_qualifier_count > 0
    assert "qualified_assertion_required" in weak.state.mandatory_qualifiers
    assert weak.gate.qualifier_binding_consumer_ready is True


def test_helpfulness_pressure_does_not_upgrade_underlicensed_advice() -> None:
    advice = build_v01_harness_case(harness_cases()["advice_helpfulness_shortcut"])
    assert advice.state.cannot_license_advice is True
    assert advice.state.licensed_act_count == 0
    assert advice.state.denied_act_count == 1


def test_implicit_promise_leakage_is_blocked() -> None:
    split = build_v01_harness_case(harness_cases()["promise_weakened_by_assertion_split"])
    assert split.state.licensed_act_count == 1
    assert split.state.denied_act_count == 1
    assert split.state.promise_like_act_denied is True
    assert split.state.alternative_narrowed_act_available is True
    assert split.state.clarification_before_commitment is True


def test_protective_defer_can_narrow_advice_without_blanket_silence() -> None:
    protected = build_v01_harness_case(harness_cases()["protective_defer_advice"])
    assert protected.state.protective_defer_required is True
    assert protected.state.denied_act_count == 1
    assert protected.state.denied_acts[0].blocking_reason_code == "protective_defer_required"
    assert protected.state.denied_acts[0].alternative_narrowed_act_type is V01ActType.BOUNDARY_STATEMENT


def test_disabled_path_returns_honest_insufficient_basis_fallback() -> None:
    disabled = build_v01_harness_case(harness_cases()["disabled"])
    assert disabled.state.candidate_act_count == 0
    assert disabled.state.insufficient_license_basis is True
    assert disabled.gate.license_consumer_ready is False
    assert "v01_disabled" in disabled.gate.restrictions
