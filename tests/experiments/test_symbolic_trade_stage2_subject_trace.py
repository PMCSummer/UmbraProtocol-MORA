from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from experiments.symbolic_trade import stage2_result_to_dict
from experiments.symbolic_trade.falsifiers import run_stage2_trace_falsifiers
from experiments.symbolic_trade.runner import list_scenarios, run_stage2_trace


def test_stage2_modules_import_from_repo_root_without_manual_pythonpath() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import experiments.symbolic_trade.subject_trace as st; import experiments.symbolic_trade.phase_adapters as pa; import experiments.symbolic_trade.stage2_runner as sr; print('ok')",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_stage2_subject_trace_run_serializes_deterministically() -> None:
    run_a = run_stage2_trace("mirrored_resource_asymmetry", include_falsifiers=False)
    run_b = run_stage2_trace("mirrored_resource_asymmetry", include_falsifiers=False)
    assert stage2_result_to_dict(run_a) == stage2_result_to_dict(run_b)


def test_stage2_trace_has_w01_to_w06_coverage_for_all_scenarios() -> None:
    for scenario in list_scenarios():
        run = run_stage2_trace(scenario, include_falsifiers=False)
        assert {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(set(run.phase_coverage)), scenario


def test_phase_trace_record_contains_required_fields() -> None:
    run = run_stage2_trace("resource_claim_contact", include_falsifiers=False)
    record = run.steps[0].phase_records[0]
    assert record.phase_code in {"W01", "W02", "W03", "W04", "W05", "W06"}
    assert record.source_packet_ids
    assert isinstance(record.uncertainty_markers, tuple)
    assert isinstance(record.downstream_permission_delta, tuple)


def test_presence_only_trace_has_no_trade_claim_or_mature_regularity() -> None:
    run = run_stage2_trace("presence_only", include_falsifiers=False)
    for step in run.steps:
        for record in step.phase_records:
            blob = " ".join(record.reason_codes + record.output_refs).lower()
            assert "mutual_benefit" not in blob
            assert "stable_exchange_rule" not in blob


def test_resource_claim_contact_preserves_counterpart_claim_boundary() -> None:
    run = run_stage2_trace("resource_claim_contact", include_falsifiers=False)
    w01_records = [r for s in run.steps for r in s.phase_records if r.phase_code == "W01"]
    assert any("counterpart_claim_admitted_as_scaffold" in r.reason_codes for r in w01_records)
    assert all("no_counterpart_inventory_fact" in r.prohibited_claims for r in w01_records)


def test_blocked_aperture_routes_to_w04_block_or_revalidate() -> None:
    run = run_stage2_trace("blocked_aperture", include_falsifiers=False)
    w04_records = [r for s in run.steps for r in s.phase_records if r.phase_code == "W04"]
    blocked_seen = [r for r in w04_records if any(ref == "aperture:blocked" for ref in r.input_refs)]
    assert blocked_seen
    assert all(r.decision_status in {"blocked", "revalidate_required"} for r in blocked_seen)


def test_noisy_signal_retains_uncertainty_or_revalidate_markers() -> None:
    run = run_stage2_trace("noisy_signal", include_falsifiers=False)
    w06_records = [r for s in run.steps for r in s.phase_records if r.phase_code == "W06"]
    assert any(r.uncertainty_markers for r in w06_records)


def test_transfer_seen_without_trade_token_does_not_infer_trade_intent() -> None:
    run = run_stage2_trace("transfer_seen_without_trade_token", include_falsifiers=False)
    for step in run.steps:
        for record in step.phase_records:
            blob = " ".join(record.reason_codes + record.prohibited_claims).lower()
            assert "trade_intent_inferred" not in blob


def test_eval_label_leak_attack_does_not_leak_eval_labels_into_phase_trace() -> None:
    run = run_stage2_trace("eval_label_leak_attack", include_falsifiers=False)
    records_blob = "\n".join(
        " ".join(record.input_refs + record.output_refs + record.reason_codes)
        for step in run.steps
        for record in step.phase_records
    )
    assert "mutually_beneficial_trade_possible_eval_only" not in records_blob


def test_stage2_falsifiers_pass_on_clean_trace() -> None:
    run = run_stage2_trace("mirrored_resource_asymmetry", include_falsifiers=False)
    results = run_stage2_trace_falsifiers(run)
    assert all(item.passed for item in results)


def test_full_serialized_phase_trace_keeps_eval_only_and_hidden_truth_out_of_visible_sections() -> None:
    run = run_stage2_trace("mirrored_resource_asymmetry", include_falsifiers=False)

    default_payload = stage2_result_to_dict(run, include_eval_only=False)
    assert "eval_only" not in default_payload
    default_blob = json.dumps(default_payload.get("steps", []), sort_keys=True)
    assert "harness_truth" not in default_blob
    assert "mutually_beneficial_trade_possible_eval_only" not in default_blob
    assert "success_labels" not in default_blob

    eval_payload = stage2_result_to_dict(run, include_eval_only=True)
    assert "eval_only" in eval_payload
    eval_blob = json.dumps(eval_payload.get("steps", []), sort_keys=True)
    assert "harness_truth" not in eval_blob
    assert "mutually_beneficial_trade_possible_eval_only" not in eval_blob
    assert "success_labels" not in eval_blob
