from __future__ import annotations

from dataclasses import replace

import experiments.symbolic_trade.falsifiers as falsifier_module
from experiments.symbolic_trade.models import (
    ApertureState,
    CounterpartSignalKind,
    SignalAuthority,
    SubjectVisiblePacket,
    TransferOutcome,
)
from experiments.symbolic_trade.phase_adapters import (
    AdapterState,
    adapt_w01,
    adapt_w02,
    adapt_w03,
    adapt_w04,
    adapt_w05,
    adapt_w06,
)
from experiments.symbolic_trade.runner import run_stage2_trace
from experiments.symbolic_trade.subject_trace import phase_record_from_adapter


def _packet(*, signal: CounterpartSignalKind, source: SignalAuthority = SignalAuthority.COUNTERPART_CLAIM, hidden_truth_excluded: bool = True, claim_not_fact: bool = True, aperture: ApertureState = ApertureState.OPEN) -> SubjectVisiblePacket:
    return SubjectVisiblePacket(
        packet_id="pkt:1",
        source_id="counterpart_b",
        source_authority=source,
        signal_kind=signal,
        resource_kind=None,
        reported_level=None,
        aperture_state=aperture,
        timestamp_or_step=1,
        provenance_ref=("tests.stage2",),
        hidden_truth_excluded=hidden_truth_excluded,
        claim_not_fact_marker=claim_not_fact,
        transfer_outcome=TransferOutcome.NOT_ATTEMPTED,
        item_kind=None,
    )


def test_w01_adapter_never_accepts_hidden_truth_leak() -> None:
    packet = _packet(signal=CounterpartSignalKind.RESOURCE_STATUS_CLAIM, hidden_truth_excluded=False)
    _, out = adapt_w01(packet, trace_id="t", step_index=1)
    assert out.decision_status == "rejected"
    assert "hidden_truth_leak_detected" in out.reason_codes


def test_w02_does_not_promote_one_shot_claim_to_stable_regularity() -> None:
    packet = _packet(signal=CounterpartSignalKind.RESOURCE_STATUS_CLAIM)
    packet = replace(packet, resource_kind=None, reported_level=None)
    state = AdapterState(seen_claim_counts={})
    _, out = adapt_w02(packet, trace_id="t", state=state)
    assert out.decision_status in {"single_claim_scaffold_only", "no_candidate"}
    assert "no_one_shot_mature_regularity" in out.prohibited_claims


def test_w03_does_not_synthesize_trade_schema_without_support() -> None:
    packet = _packet(signal=CounterpartSignalKind.RESOURCE_STATUS_CLAIM)
    state = AdapterState(seen_claim_counts={})
    _, out = adapt_w03(packet, trace_id="t", state=state)
    assert out.decision_status == "insufficient_support"
    assert "no_trade_schema_from_language_prior_alone" in out.prohibited_claims


def test_w04_does_not_approve_usefulness_as_permission() -> None:
    packet = _packet(signal=CounterpartSignalKind.RESOURCE_STATUS_CLAIM)
    _, out = adapt_w04(packet, trace_id="t")
    assert "no_usefulness_as_permission" in out.prohibited_claims
    assert "may_deploy_candidate:false" in out.downstream_permission_delta


def test_w05_keeps_desired_predicted_observed_permitted_separation() -> None:
    packet = _packet(signal=CounterpartSignalKind.PRESENCE_PING, source=SignalAuthority.OBSERVED_EVENT, claim_not_fact=False)
    _, out = adapt_w05(packet, trace_id="t", w04_status="bounded_applicability_candidate")
    assert "desired_predicted_observed_permitted_separated" in out.reason_codes
    assert "desired_not_evidence" in out.prohibited_claims
    assert "predicted_utility_not_permission" in out.prohibited_claims


def test_w06_correction_candidate_never_executed_and_residue_preserved() -> None:
    packet = _packet(signal=CounterpartSignalKind.CONTRADICTION, source=SignalAuthority.OBSERVED_EVENT, claim_not_fact=False)
    _, out = adapt_w06(packet, trace_id="t", w05_status="mismatch_routed")
    assert "execution_prohibited:true" in out.downstream_permission_delta
    assert "correction_executed:false" in out.downstream_permission_delta
    assert any("residue" in marker for marker in out.uncertainty_markers)


def test_stage2_falsifier_detects_missing_w01_to_w06_coverage() -> None:
    run = run_stage2_trace("presence_only", include_falsifiers=False)
    first_step = run.steps[0]
    filtered = tuple(record for record in first_step.phase_records if record.phase_code != "W06")
    mutated_step = replace(first_step, phase_records=filtered)
    mutated_run = replace(run, steps=(mutated_step,) + run.steps[1:], phase_coverage=tuple(code for code in run.phase_coverage if code != "W06"))
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["phase_trace_without_w01_to_w06_coverage"] is False


def test_stage2_falsifier_detects_core_contamination_with_untracked_forbidden_path(monkeypatch) -> None:
    run = run_stage2_trace("presence_only", include_falsifiers=False)
    monkeypatch.setattr(falsifier_module, "_modified_paths", lambda _repo_root: ())
    monkeypatch.setattr(falsifier_module, "_untracked_paths", lambda _repo_root: ("src/substrate/w06_shadow.py",))
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(run)}
    assert outcomes["phase_adapter_core_contamination"] is False


def test_stage2_falsifier_detects_core_contamination_with_untracked_subject_tick_path(monkeypatch) -> None:
    run = run_stage2_trace("presence_only", include_falsifiers=False)
    monkeypatch.setattr(falsifier_module, "_modified_paths", lambda _repo_root: ())
    monkeypatch.setattr(
        falsifier_module,
        "_untracked_paths",
        lambda _repo_root: ("src/substrate/subject_tick/shadow_probe.py",),
    )
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(run)}
    assert outcomes["phase_adapter_core_contamination"] is False


def test_stage2_falsifier_detects_w06_execution_guard_break() -> None:
    run = run_stage2_trace("presence_only", include_falsifiers=False)
    step = run.steps[0]
    w06 = next(record for record in step.phase_records if record.phase_code == "W06")
    broken = replace(
        w06,
        downstream_permission_delta=tuple("execution_prohibited:false" if x == "execution_prohibited:true" else x for x in w06.downstream_permission_delta),
        execution_prohibited=False,
    )
    rebuilt = tuple(broken if record.trace_id == w06.trace_id and record.phase_code == "W06" else record for record in step.phase_records)
    mutated_run = replace(run, steps=(replace(step, phase_records=rebuilt),) + run.steps[1:])
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["w06_correction_candidate_executed"] is False


def test_stage2_falsifier_detects_one_shot_regularization_promotion() -> None:
    run = run_stage2_trace("presence_only", include_falsifiers=False)
    step = run.steps[0]
    w02 = next(record for record in step.phase_records if record.phase_code == "W02")
    promoted = replace(w02, decision_status="provisional_repeated_pattern", reason_codes=("stable_reliability_from_single_signal",))
    rebuilt = tuple(promoted if record.trace_id == w02.trace_id and record.phase_code == "W02" else record for record in step.phase_records)
    mutated_run = replace(run, steps=(replace(step, phase_records=rebuilt),) + run.steps[1:])
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["one_shot_claim_promoted_by_w02_or_w03"] is False


def test_stage2_falsifier_detects_w04_usefulness_as_permission_shortcut() -> None:
    run = run_stage2_trace("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    w04 = next(record for record in step.phase_records if record.phase_code == "W04")
    bad = replace(w04, reason_codes=w04.reason_codes + ("usefulness_override",), downstream_permission_delta=w04.downstream_permission_delta + ("should_trade:true",))
    rebuilt = tuple(bad if record.trace_id == w04.trace_id and record.phase_code == "W04" else record for record in step.phase_records)
    mutated_run = replace(run, steps=(replace(step, phase_records=rebuilt),) + run.steps[1:])
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["w04_usefulness_as_permission"] is False


def test_stage2_falsifier_detects_w05_desired_or_predicted_as_permission_shortcut() -> None:
    run = run_stage2_trace("mirrored_resource_asymmetry", include_falsifiers=False)
    step = run.steps[0]
    w05 = next(record for record in step.phase_records if record.phase_code == "W05")
    bad = replace(
        w05,
        reason_codes=w05.reason_codes + ("desired_as_permission",),
        prohibited_claims=tuple(item for item in w05.prohibited_claims if item != "desired_not_evidence"),
        downstream_permission_delta=tuple(
            "execution_authorization_granted:true" if item == "execution_authorization_granted:false" else item
            for item in w05.downstream_permission_delta
        ),
    )
    rebuilt = tuple(bad if record.trace_id == w05.trace_id and record.phase_code == "W05" else record for record in step.phase_records)
    mutated_run = replace(run, steps=(replace(step, phase_records=rebuilt),) + run.steps[1:])
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["w05_desired_or_predicted_as_permission"] is False


def test_stage2_falsifier_detects_eval_label_in_phase_trace() -> None:
    run = run_stage2_trace("eval_label_leak_attack", include_falsifiers=False)
    step = run.steps[0]
    record = step.phase_records[0]
    leaked = replace(record, reason_codes=record.reason_codes + ("mutually_beneficial_trade_possible_eval_only",))
    rebuilt = tuple(leaked if item.trace_id == record.trace_id and item.phase_code == record.phase_code else item for item in step.phase_records)
    mutated_run = replace(run, steps=(replace(step, phase_records=rebuilt),) + run.steps[1:])
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["eval_label_in_phase_trace"] is False


def test_stage2_falsifier_detects_blocked_aperture_clean_applicability_mutation() -> None:
    run = run_stage2_trace("blocked_aperture", include_falsifiers=False)
    target_step = next(step for step in run.steps if any(item.signal_kind == "blocked_signal" for item in step.packet_refs))
    w04 = next(record for record in target_step.phase_records if record.phase_code == "W04")
    bad = replace(
        w04,
        decision_status="bounded_applicability_candidate",
        downstream_permission_delta=tuple(
            "may_deploy_candidate:true" if item.startswith("may_deploy_candidate:") else item
            for item in w04.downstream_permission_delta
        ),
    )
    rebuilt = tuple(
        bad if record.trace_id == w04.trace_id and record.phase_code == "W04" else record
        for record in target_step.phase_records
    )
    mutated_steps = tuple(
        replace(step, phase_records=rebuilt) if step.step_index == target_step.step_index else step
        for step in run.steps
    )
    mutated_run = replace(run, steps=mutated_steps)
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["blocked_aperture_still_allows_clean_applicability"] is False


def test_stage2_falsifier_detects_false_counterpart_claim_promoted_to_truth_mutation() -> None:
    run = run_stage2_trace("false_counterpart_claim", include_falsifiers=False)
    step = run.steps[0]
    w01 = next(record for record in step.phase_records if record.phase_code == "W01")
    bad = replace(
        w01,
        decision_status="admitted",
        reason_codes=tuple(item for item in w01.reason_codes if item != "counterpart_claim_admitted_as_scaffold"),
    )
    rebuilt = tuple(
        bad if record.trace_id == w01.trace_id and record.phase_code == "W01" else record
        for record in step.phase_records
    )
    mutated_run = replace(run, steps=(replace(step, phase_records=rebuilt),) + run.steps[1:])
    outcomes = {x.name: x.passed for x in falsifier_module.run_stage2_trace_falsifiers(mutated_run)}
    assert outcomes["false_counterpart_claim_becomes_truth"] is False
