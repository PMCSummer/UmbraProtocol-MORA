from __future__ import annotations

from substrate.ap01_subject_action_publication import (
    AP01ActionPublicationCandidate,
    AP01ActionPublicationCandidateSet,
    AP01CandidateOrigin,
    AP01DecisionStatus,
)
from substrate.subject_tick import SubjectTickContext
from tests.substrate.subject_tick_testkit import build_subject_tick


def _candidate(**overrides: object) -> AP01ActionPublicationCandidate:
    payload: dict[str, object] = {
        "candidate_id": "ap01-c1",
        "action_kind": "inspect",
        "target_ref": "station:alpha",
        "args": {"distance": 1},
        "intended_effect": "inspection",
        "source_tick_ref": "subject-tick-context-1",
        "source_cycle_ref": "cycle:subject:1",
        "source_phase_refs": ("W04:permission", "W05:routing", "W06:revision"),
        "affordance_binding_refs": (),
        "permission_refs": ("W04:permit",),
        "evidence_refs": ("W01:packet",),
        "episode_refs": ("P02:episode",),
        "residue_refs": (),
        "revalidation_refs": (),
        "blocked_claim_refs": (),
        "desired_refs": (),
        "predicted_refs": (),
        "observed_refs": (),
        "permitted_refs": ("W05:permitted",),
        "candidate_origin": AP01CandidateOrigin.SUBJECT_TICK_CANDIDATE_BASIS,
        "forbidden_basis_markers": (),
        "no_hidden_truth_used": True,
        "no_eval_only_used": True,
        "no_scenario_label_used": True,
    }
    payload.update(overrides)
    return AP01ActionPublicationCandidate(**payload)


def _tick(case_id: str, context: SubjectTickContext | None = None):
    return build_subject_tick(
        case_id=case_id,
        energy=72.0,
        cognitive=58.0,
        safety=67.0,
        unresolved_preference=False,
        context=context,
    )


def test_no_ap01_candidate_produces_no_published_request() -> None:
    result = _tick("ap01:no-candidate")
    assert result.ap01_result.telemetry.candidate_count == 0
    assert result.ap01_result.telemetry.published_request_count == 0
    assert result.state.ap01_published_request_count == 0


def test_valid_ap01_candidate_in_subject_tick_produces_projection() -> None:
    context = SubjectTickContext(
        ap01_action_publication_candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id="ap01:valid:set",
            candidates=(_candidate(),),
            source_lineage=("tests.subject_tick.ap01",),
        )
    )
    result = _tick("ap01:valid", context=context)
    assert result.ap01_result.telemetry.published_request_count == 1
    assert result.ap01_result.decisions[0].decision_status is AP01DecisionStatus.PUBLISHED
    assert result.state.ap01_candidate_count == 1
    assert result.state.ap01_published_request_count == 1
    assert result.state.ap01_execution_boundary_preserved is True
    assert result.state.ap01_must_wait_for_effect is True
    assert result.state.ap01_no_hidden_truth_used is True
    assert result.state.ap01_no_scenario_label_used is True


def test_unsafe_candidate_in_subject_tick_is_rejected() -> None:
    context = SubjectTickContext(
        ap01_action_publication_candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id="ap01:unsafe:set",
            candidates=(
                _candidate(
                    forbidden_basis_markers=("scenario_id:eval_label",),
                ),
            ),
            source_lineage=("tests.subject_tick.ap01",),
        )
    )
    result = _tick("ap01:unsafe", context=context)
    assert result.ap01_result.telemetry.published_request_count == 0
    assert result.ap01_result.telemetry.unsafe_basis_count == 1
    assert result.ap01_result.decisions[0].decision_status is AP01DecisionStatus.UNSAFE_BASIS
    assert result.state.ap01_unsafe_basis_count == 1


def test_subject_tick_does_not_fabricate_action_from_scenario_like_context() -> None:
    result = _tick("scenario_like_expected_outcome_but_no_ap01_candidate")
    assert result.ap01_result.telemetry.candidate_count == 0
    assert result.ap01_result.telemetry.published_request_count == 0
    assert result.state.ap01_candidate_count == 0
    assert result.state.ap01_published_request_count == 0


def test_ap01_compact_projection_is_allowlisted_without_raw_hidden_payload() -> None:
    context = SubjectTickContext(
        ap01_action_publication_candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id="ap01:projection:set",
            candidates=(_candidate(),),
            source_lineage=("tests.subject_tick.ap01",),
        )
    )
    result = _tick("ap01:projection", context=context)
    assert isinstance(result.state.ap01_candidate_count, int)
    assert isinstance(result.state.ap01_published_request_count, int)
    assert result.state.ap01_no_hidden_truth_used is True
    assert result.state.ap01_no_scenario_label_used is True
    assert "hidden_truth" not in result.ap01_result.reason


def test_subject_tick_rejects_test_fixture_candidate_by_default() -> None:
    context = SubjectTickContext(
        ap01_action_publication_candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id="ap01:fixture:set",
            candidates=(
                _candidate(
                    candidate_origin=AP01CandidateOrigin.TEST_FIXTURE_CANDIDATE,
                ),
            ),
            source_lineage=("tests.subject_tick.ap01",),
        )
    )
    result = _tick("ap01:fixture-origin-default-reject", context=context)
    assert result.ap01_result.telemetry.candidate_count == 1
    assert result.ap01_result.telemetry.published_request_count == 0
    assert result.ap01_result.telemetry.unsafe_basis_count == 1
    assert result.ap01_result.decisions[0].decision_status is AP01DecisionStatus.UNSAFE_BASIS
    assert result.state.ap01_published_request_count == 0
    assert result.state.ap01_unsafe_basis_count == 1
