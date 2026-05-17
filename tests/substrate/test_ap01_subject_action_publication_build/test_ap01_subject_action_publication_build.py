from __future__ import annotations

from dataclasses import fields, is_dataclass

from substrate.ap01_subject_action_publication import (
    AP01ActionPublicationCandidate,
    AP01ActionPublicationCandidateSet,
    AP01CandidateOrigin,
    AP01DecisionStatus,
    AP01ExecutionBoundary,
    AP01WorldExecutionStatus,
    build_ap01_subject_action_publication,
    derive_ap01_action_publication_contract_view,
)


def _candidate(**overrides: object) -> AP01ActionPublicationCandidate:
    payload: dict[str, object] = {
        "candidate_id": "c1",
        "action_kind": "use_station",
        "target_ref": "station:alpha",
        "args": {"mode": "inspect_only"},
        "intended_effect": "inspection",
        "source_tick_ref": "subject-tick-test-1",
        "source_cycle_ref": "cycle:test:1",
        "source_phase_refs": ("W04:permission:1", "W05:routing:1", "W06:revision:1"),
        "affordance_binding_refs": ("A04:binding:1",),
        "permission_refs": ("W04:permit:1",),
        "evidence_refs": ("W01:packet:1",),
        "episode_refs": ("P02:episode:1",),
        "residue_refs": (),
        "revalidation_refs": (),
        "blocked_claim_refs": (),
        "desired_refs": (),
        "predicted_refs": (),
        "observed_refs": (),
        "permitted_refs": ("W05:permitted:1",),
        "candidate_origin": AP01CandidateOrigin.CORE_INTERNAL_CANDIDATE,
        "forbidden_basis_markers": (),
        "no_hidden_truth_used": True,
        "no_eval_only_used": True,
        "no_scenario_label_used": True,
    }
    payload.update(overrides)
    return AP01ActionPublicationCandidate(**payload)


def _run(candidate: AP01ActionPublicationCandidate, *, allow_fixture: bool = True):
    return build_ap01_subject_action_publication(
        tick_id="subject-tick-ap01-test",
        tick_index=1,
        candidate_set=AP01ActionPublicationCandidateSet(
            candidate_set_id="ap01:test:set",
            candidates=(candidate,),
            source_lineage=("tests.ap01",),
        ),
        allow_test_fixture_candidates=allow_fixture,
    )


def _collect_object_type_names(root: object) -> set[str]:
    seen: set[int] = set()
    type_names: set[str] = set()
    stack: list[object] = [root]
    while stack:
        current = stack.pop()
        type_names.add(type(current).__name__)
        ident = id(current)
        if ident in seen:
            continue
        seen.add(ident)
        if is_dataclass(current):
            for field in fields(current):
                stack.append(getattr(current, field.name))
            continue
        if isinstance(current, dict):
            stack.extend(current.values())
            continue
        if isinstance(current, (list, tuple, set)):
            stack.extend(current)
    return type_names


def test_publishes_valid_bounded_request() -> None:
    result = _run(_candidate())
    assert result.telemetry.published_request_count == 1
    assert result.decisions[0].decision_status is AP01DecisionStatus.PUBLISHED


def test_request_is_not_execution() -> None:
    result = _run(_candidate())
    request = result.published_requests[0]
    assert request.execution_boundary is AP01ExecutionBoundary.EXTERNAL_WORLD_ONLY
    assert request.executed_by_subject is False
    assert request.world_execution_status is AP01WorldExecutionStatus.NOT_EXECUTED_BY_SUBJECT
    assert request.must_wait_for_world_effect is True
    assert request.effect_feedback_required is True


def test_desired_state_alone_cannot_publish() -> None:
    result = _run(
        _candidate(
            permission_refs=(),
            evidence_refs=(),
            permitted_refs=(),
            desired_refs=("desired:water",),
        )
    )
    assert result.decisions[0].decision_status is AP01DecisionStatus.BLOCKED


def test_predicted_success_alone_cannot_publish() -> None:
    result = _run(
        _candidate(
            permission_refs=(),
            evidence_refs=(),
            permitted_refs=(),
            predicted_refs=("predicted:success",),
        )
    )
    assert result.decisions[0].decision_status is AP01DecisionStatus.BLOCKED


def test_affordance_available_alone_cannot_publish() -> None:
    result = _run(
        _candidate(
            permission_refs=(),
            evidence_refs=(),
            permitted_refs=(),
            affordance_binding_refs=("A04:binding:only",),
        )
    )
    assert result.decisions[0].decision_status is AP01DecisionStatus.BLOCKED


def test_world_effect_result_cannot_publish_future_action() -> None:
    result = _run(
        _candidate(
            permission_refs=(),
            evidence_refs=(),
            permitted_refs=(),
            observed_refs=("world_effect:success",),
        )
    )
    assert result.decisions[0].decision_status is AP01DecisionStatus.BLOCKED


def test_scenario_id_candidate_is_rejected() -> None:
    result = _run(_candidate(forbidden_basis_markers=("scenario_id:mirrored",)))
    assert result.decisions[0].decision_status is AP01DecisionStatus.UNSAFE_BASIS


def test_hidden_truth_or_eval_only_rejected() -> None:
    hidden = _run(_candidate(no_hidden_truth_used=False))
    eval_only = _run(_candidate(no_eval_only_used=False))
    assert hidden.decisions[0].decision_status is AP01DecisionStatus.UNSAFE_BASIS
    assert eval_only.decisions[0].decision_status is AP01DecisionStatus.UNSAFE_BASIS


def test_unknown_or_magic_action_kind_rejected() -> None:
    unknown = _run(_candidate(action_kind="unknown_action_kind"))
    magic = _run(_candidate(action_kind="trade_offer"))
    assert unknown.decisions[0].decision_status is AP01DecisionStatus.MALFORMED
    assert magic.decisions[0].decision_status is AP01DecisionStatus.MALFORMED


def test_target_required_for_targeted_action() -> None:
    targeted = _run(_candidate(action_kind="pickup", target_ref=None))
    wait_kind = _run(
        _candidate(
            action_kind="wait",
            target_ref=None,
            affordance_binding_refs=(),
            intended_effect="hold",
        )
    )
    assert targeted.decisions[0].decision_status is AP01DecisionStatus.MALFORMED
    assert wait_kind.decisions[0].decision_status is AP01DecisionStatus.PUBLISHED


def test_w04_block_or_missing_permission_blocks() -> None:
    result = _run(_candidate(permission_refs=(), permitted_refs=()))
    assert result.decisions[0].decision_status is AP01DecisionStatus.BLOCKED


def test_w06_revalidation_or_block_prevents_clean_publication() -> None:
    revalidate = _run(_candidate(revalidation_refs=("W06:revalidate",)))
    blocked = _run(_candidate(blocked_claim_refs=("W06:blocked_claim",)))
    assert revalidate.decisions[0].decision_status is AP01DecisionStatus.REVALIDATION_REQUIRED
    assert blocked.decisions[0].decision_status is AP01DecisionStatus.BLOCKED


def test_blocked_claim_refs_preserved() -> None:
    result = _run(
        _candidate(
            blocked_claim_refs=("claim:block:1",),
            residue_refs=("residue:1",),
        )
    )
    decision = result.decisions[0]
    assert decision.decision_status is AP01DecisionStatus.BLOCKED
    assert "claim:block:1" in decision.preserved_residue_refs
    assert "residue:1" in decision.preserved_residue_refs


def test_request_does_not_mutate_world() -> None:
    result = _run(_candidate())
    decision = result.decisions[0]
    assert decision.published_request is not None
    assert decision.published_request.world_execution_status.value == "not_executed_by_subject"


def test_ap01_result_does_not_emit_world_effect_or_world_action_packet() -> None:
    result = _run(_candidate())
    assert result.telemetry.published_request_count == 1
    assert len(result.published_requests) == 1
    request = result.published_requests[0]
    assert request.source_candidate_id == result.decisions[0].candidate_id

    # AP01 must publish request-only artifacts; world execution/effect packets are out of scope.
    type_names = _collect_object_type_names(result)
    assert "WorldEffectObservationPacket" not in type_names
    assert "WorldActionPacket" not in type_names

    request_fields = {f.name for f in fields(type(request))}
    assert "world_action_packet" not in request_fields
    assert "world_effect_packet" not in request_fields
    assert "emitted_world_effect" not in request_fields


def test_no_generic_stub_request() -> None:
    kind = _run(_candidate(action_kind="emit_world_action"))
    target = _run(_candidate(target_ref="external_stub_target"))
    assert kind.decisions[0].decision_status is AP01DecisionStatus.MALFORMED
    assert target.decisions[0].decision_status is AP01DecisionStatus.MALFORMED


def test_no_request_without_source_phase_refs() -> None:
    result = _run(_candidate(source_phase_refs=()))
    assert result.decisions[0].decision_status is AP01DecisionStatus.BLOCKED


def test_no_request_without_effect_wait_boundary() -> None:
    result = _run(_candidate())
    request = result.published_requests[0]
    assert request.must_wait_for_world_effect is True
    assert request.effect_feedback_required is True


def test_downstream_contract_forbids_completion_claim() -> None:
    result = _run(_candidate())
    contract = derive_ap01_action_publication_contract_view(result)
    assert contract.must_not_treat_request_as_success is True
    assert contract.must_not_treat_request_as_world_change is True
    assert contract.must_not_infer_completion_from_request is True


def test_downstream_contract_disallows_world_bridge_submission_when_no_request_published() -> None:
    blocked = _run(
        _candidate(
            permission_refs=(),
            evidence_refs=(),
            permitted_refs=(),
            desired_refs=("desired:state",),
        )
    )
    assert blocked.telemetry.published_request_count == 0
    contract = derive_ap01_action_publication_contract_view(blocked)
    assert contract.may_submit_to_world_bridge is False
    assert contract.must_not_execute_inside_subject is True
    assert contract.must_wait_for_effect_feedback is True
    assert contract.must_not_treat_request_as_success is True
    assert contract.must_not_treat_request_as_world_change is True
    assert contract.must_not_infer_completion_from_request is True


def test_test_fixture_candidate_requires_explicit_owner_allow_flag() -> None:
    fixture_candidate = _candidate(
        candidate_origin=AP01CandidateOrigin.TEST_FIXTURE_CANDIDATE
    )
    rejected = _run(fixture_candidate, allow_fixture=False)
    allowed = _run(fixture_candidate, allow_fixture=True)

    assert rejected.telemetry.published_request_count == 0
    assert rejected.telemetry.unsafe_basis_count == 1
    assert rejected.decisions[0].decision_status is AP01DecisionStatus.UNSAFE_BASIS
    assert allowed.decisions[0].decision_status is AP01DecisionStatus.PUBLISHED
