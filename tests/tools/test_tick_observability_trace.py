from __future__ import annotations

import json
from pathlib import Path

import pytest

from substrate.runtime_tap_trace import (
    MODULE_ALLOWED_FIELDS,
    TRACE_STEP_ALLOWED,
    activate_tick_trace,
    deactivate_tick_trace,
    finish_tick_trace,
    reset_trace_state,
)
from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.simple_trace import run_tick_and_write_simple_trace
from substrate.subject_tick import SubjectTickInput
from tools.tick_observability_trace import main as tick_trace_main

FORBIDDEN_VOCABULARY = (
    "likely_subject_issue",
    "likely_observability_gap",
    "likely_harness_gap",
    "mixed_or_ambiguous",
    "reconciliation_triage",
    "sensitivity",
    "verdict",
)

HOSTED_CONTOUR_SEGMENTS = (
    "c01_stream_kernel",
    "c02_tension_scheduler",
    "c03_stream_diversification",
    "s01_efference_copy",
    "s02_prediction_boundary",
    "s03_ownership_weighted_learning",
    "s04_interoceptive_self_binding",
    "s05_multi_cause_attribution_factorization",
    "o01_other_entity_model",
    "s_minimal_contour",
    "a_line_normalization",
    "m_minimal",
    "n_minimal",
)

HOSTED_CONTOUR_FIELDS: dict[str, set[str]] = {
    "c01_stream_kernel": {
        "stream_state",
        "kernel_ready",
        "stream_load",
        "kernel_blocked",
        "active_stream_count",
    },
    "c02_tension_scheduler": {
        "tension_level",
        "scheduler_state",
        "pressure_binding",
        "tension_blocked",
        "schedule_ready",
    },
    "c03_stream_diversification": {
        "diversification_state",
        "active_branches",
        "branch_pressure",
        "diversification_blocked",
        "diversification_ready",
    },
    "s01_efference_copy": {
        "efference_available",
        "trace_ready",
        "action_projection_present",
        "efference_blocked",
    },
    "s02_prediction_boundary": {
        "prediction_boundary_status",
        "boundary_integrity",
        "boundary_blocked",
        "prediction_ready",
    },
    "s03_ownership_weighted_learning": {
        "ownership_status",
        "ownership_confidence",
        "learning_weight_applied",
        "ownership_blocked",
    },
    "s04_interoceptive_self_binding": {
        "strong_bound_count",
        "weak_bound_count",
        "contested_count",
        "provisional_count",
        "no_stable_core_claim",
        "strongest_binding_strength",
        "contamination_detected",
        "rebinding_event",
        "stale_binding_drop_count",
    },
    "s05_multi_cause_attribution_factorization": {
        "dominant_slot_count",
        "residual_share",
        "residual_class",
        "underdetermined_split",
        "contamination_present",
        "temporal_misalignment_present",
        "reattribution_happened",
        "downstream_route_class",
        "factorization_consumer_ready",
        "learning_route_ready",
    },
    "o01_other_entity_model": {
        "entity_count",
        "current_user_model_ready",
        "third_party_models_active",
        "stable_claim_count",
        "temporary_hypothesis_count",
        "contradiction_count",
        "knowledge_boundary_known_count",
        "projection_guard_triggered",
        "no_safe_state_claim",
        "downstream_consumer_ready",
    },
    "s_minimal_contour": {
        "minimal_self_status",
        "minimal_self_ready",
        "contour_blocked",
    },
    "a_line_normalization": {
        "normalization_status",
        "normalized_ready",
        "normalization_blocked",
        "normalization_scope",
    },
    "m_minimal": {
        "minimal_memory_status",
        "memory_ready",
        "memory_blocked",
    },
    "n_minimal": {
        "minimal_narrative_status",
        "narrative_ready",
        "narrative_blocked",
    },
}


def _load_events(path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _run_sample_trace(
    tmp_path: Path,
    *,
    case_id: str = "runtime-trace-case",
    route_class: str = "production_contour",
) -> tuple[Path, list[dict[str, object]]]:
    reset_trace_state()
    result = run_tick_and_write_simple_trace(
        case_id=case_id,
        energy=66.0,
        cognitive=44.0,
        safety=74.0,
        unresolved_preference=False,
        output_root=tmp_path / "trace-out",
        route_class=route_class,
    )
    trace_path = Path(result["trace_path"])
    assert trace_path.exists()
    events = _load_events(trace_path)
    assert events
    return trace_path, events


def _module_decision_event(events: list[dict[str, object]], module: str) -> dict[str, object]:
    for event in events:
        if str(event["module"]) == module and str(event["step"]) == "decision":
            return event
    raise AssertionError(f"decision event not found for module={module}")


def _module_events(events: list[dict[str, object]], module: str) -> list[dict[str, object]]:
    return [event for event in events if str(event["module"]) == module]


def _first_order(events: list[dict[str, object]], module: str, step: str = "decision") -> int:
    for event in events:
        if str(event["module"]) == module and str(event["step"]) == step:
            return int(event["order"])
    raise AssertionError(f"{step} event not found for module={module}")


def test_runtime_truth_trace_survives_mid_tick_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import substrate.subject_tick.update as subject_tick_update

    reset_trace_state()
    tick_id = "subject-tick-midfail-1"
    token = activate_tick_trace(tick_id=tick_id, output_root=tmp_path / "trace-out")
    monkeypatch.setattr(
        subject_tick_update,
        "build_t02_constrained_scene",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("forced_t02_failure")),
    )

    with pytest.raises(RuntimeError, match="forced_t02_failure"):
        dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=SubjectTickInput(
                    case_id="midfail",
                    energy=66.0,
                    cognitive=44.0,
                    safety=74.0,
                    unresolved_preference=False,
                ),
                route_class=RuntimeRouteClass.PRODUCTION_CONTOUR,
            )
        )

    deactivate_tick_trace(token)
    meta = finish_tick_trace(tick_id=tick_id)
    trace_path = Path(meta["trace_path"])
    events = _load_events(trace_path)
    modules = {str(event["module"]) for event in events}
    assert "runtime_topology" in modules
    assert "world_adapter" in modules
    assert "t01_semantic_field" in modules
    subject_tick_steps = {
        str(event["step"]) for event in events if str(event["module"]) == "subject_tick"
    }
    assert "decision" not in subject_tick_steps
    assert "exit" not in subject_tick_steps
    assert int(meta["event_count"]) == len(events)


def test_trace_lines_have_minimal_envelope_and_runtime_order(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-ordering")
    expected_keys = {"tick_id", "order", "module", "step", "values", "note"}
    orders = [int(event["order"]) for event in events]
    assert orders == list(range(len(events)))
    for event in events:
        assert set(event.keys()) == expected_keys
        assert event["step"] in TRACE_STEP_ALLOWED
        assert isinstance(event["values"], dict)


def test_non_accepted_route_does_not_replay_static_module_order(tmp_path: Path) -> None:
    _, events = _run_sample_trace(
        tmp_path,
        case_id="runtime-helper-blocked",
        route_class="helper_path",
    )
    modules = {str(event["module"]) for event in events}
    assert modules == {"runtime_topology"}
    steps = [str(event["step"]) for event in events]
    assert "blocked" in steps
    assert "decision" in steps


def test_no_synthetic_enter_with_all_none(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-enter-values")
    enter_events = [event for event in events if event["step"] == "enter"]
    assert enter_events
    for event in enter_events:
        values = event["values"]
        assert isinstance(values, dict)
        assert values
        assert not all(value is None for value in values.values())


def test_field_whitelists_are_enforced_per_module(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-whitelist")
    for event in events:
        module = str(event["module"])
        values = event["values"]
        assert isinstance(values, dict)
        assert set(values.keys()).issubset(set(MODULE_ALLOWED_FIELDS[module]))
        if module == "downstream_obedience":
            assert "restrictions" not in values
            assert "restriction_count" in values


def test_regulation_trace_enrichment_fields_are_compact_and_runtime_local(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-regulation-enrichment")
    event = _module_decision_event(events, "regulation")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        (
            "pressure_level",
            "escalation_stage",
            "override_scope",
            "gate_accepted",
            "dominant_axis",
            "claim_strength",
        )
    ).issubset(set(values.keys()))
    assert isinstance(values["pressure_level"], (int, float))
    assert isinstance(values["escalation_stage"], str)
    assert isinstance(values["override_scope"], str)
    assert isinstance(values["gate_accepted"], bool)
    assert isinstance(values["claim_strength"], str)
    assert len(json.dumps(values, ensure_ascii=True)) < 500


def test_downstream_trace_enrichment_is_compact_and_no_full_payload_leak(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-downstream-enrichment")
    event = _module_decision_event(events, "downstream_obedience")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        ("accepted", "usability_class", "top_restrictions", "restriction_count", "blocked_reason")
    ).issubset(set(values.keys()))
    assert isinstance(values["accepted"], bool)
    assert isinstance(values["usability_class"], str)
    assert isinstance(values["restriction_count"], int)
    assert isinstance(values["top_restrictions"], list)
    assert len(values["top_restrictions"]) <= 3
    assert all(isinstance(item, str) and len(item) <= 96 for item in values["top_restrictions"])
    assert "restrictions" not in values
    assert len(json.dumps(values, ensure_ascii=True)) < 500


def test_subject_output_kind_is_emitted_and_consistent(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-output-kind")
    event = _module_decision_event(events, "subject_tick")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        (
            "output_kind",
            "materialized_output",
            "final_execution_outcome",
            "active_execution_mode",
            "abstain",
            "abstain_reason",
        )
    ).issubset(set(values.keys()))

    output_kind = values["output_kind"]
    assert output_kind in {
        "contentful_output",
        "bounded_idle_continuation",
        "abstention_output",
        "no_material_output",
    }
    if output_kind == "bounded_idle_continuation":
        assert values["materialized_output"] is True
        assert values["final_execution_outcome"] == "continue"
        assert values["abstain"] is False
        assert values["active_execution_mode"] in {"idle", "hold_safe_idle"}
    if output_kind == "abstention_output":
        assert values["abstain"] is True
    if output_kind == "no_material_output":
        assert (values["materialized_output"] is False) or (
            values["final_execution_outcome"] == "halt"
        )
    if output_kind == "contentful_output":
        assert values["materialized_output"] is True
        assert values["abstain"] is False
        assert values["active_execution_mode"] not in {"idle", "hold_safe_idle"}


def test_t03_clarity_emits_nonconvergence_basis_signal(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-t03-clarity")
    event = _module_decision_event(events, "t03_hypothesis_competition")
    values = event["values"]
    assert isinstance(values, dict)
    assert set(
        (
            "leader",
            "conflict_count",
            "open_slot_count",
            "convergence_status",
            "nonconvergence_preserved",
            "no_viable_leader",
            "nonconvergence_basis",
        )
    ).issubset(set(values.keys()))
    assert isinstance(values["conflict_count"], int)
    assert isinstance(values["open_slot_count"], int)
    assert isinstance(values["no_viable_leader"], bool)
    assert isinstance(values["nonconvergence_basis"], str)
    assert values["nonconvergence_basis"] in {
        "converged_or_provisional",
        "conflict",
        "open_slot_incompleteness",
        "no_admissible_leader",
        "nonconvergence_unspecified",
    }
    assert " " not in values["nonconvergence_basis"]
    assert len(values["nonconvergence_basis"]) <= 64
    if values["convergence_status"] == "honest_nonconvergence":
        assert values["nonconvergence_basis"] != "converged_or_provisional"


def test_rt01_contract_gate_segments_emit_runtime_events(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-rt01-contract-gates")
    for module in (
        "c04_mode_arbitration",
        "c05_temporal_validity",
        "world_seam_enforcement",
        "bounded_outcome_resolution",
    ):
        module_events = _module_events(events, module)
        assert module_events
        steps = {str(event["step"]) for event in module_events}
        assert "decision" in steps
        assert "exit" in steps


def test_rt01_contract_gate_segments_emit_local_not_subject_aggregate_values(
    tmp_path: Path,
) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-rt01-local-vs-aggregate")
    subject_values = _module_decision_event(events, "subject_tick")["values"]
    c04_values = _module_decision_event(events, "c04_mode_arbitration")["values"]
    c05_values = _module_decision_event(events, "c05_temporal_validity")["values"]

    assert isinstance(subject_values, dict)
    assert isinstance(c04_values, dict)
    assert isinstance(c05_values, dict)

    assert "selected_mode" in c04_values
    assert "validity_status" in c05_values
    assert "selected_mode" not in subject_values
    assert "validity_status" not in subject_values
    assert c04_values["selected_mode"] != subject_values["active_execution_mode"]
    assert c05_values["validity_status"] != subject_values["final_execution_outcome"]


def test_rt01_contract_gate_fields_whitelisted_and_compact(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-rt01-whitelist")
    expected_fields: dict[str, set[str]] = {
        "c04_mode_arbitration": {
            "selected_mode",
            "mode_source",
            "mode_conflict_present",
            "arbitration_stable",
            "handoff_ready",
        },
        "c05_temporal_validity": {
            "validity_status",
            "legality_class",
            "revalidation_required",
            "temporal_blocked",
            "validity_ready",
        },
        "world_seam_enforcement": {
            "world_transition_allowed",
            "seam_blocked",
            "seam_block_reason",
            "world_grounded_ready",
        },
        "bounded_outcome_resolution": {
            "bounded_outcome_class",
            "output_allowed",
            "materialization_mode",
            "bounded_reason",
            "outcome_ready",
        },
    }
    for module, required in expected_fields.items():
        values = _module_decision_event(events, module)["values"]
        assert isinstance(values, dict)
        assert required.issubset(set(values.keys()))
        assert set(values.keys()).issubset(set(MODULE_ALLOWED_FIELDS[module]))
        assert "restrictions" not in values
        assert "execution_checkpoints" not in values
        assert len(json.dumps(values, ensure_ascii=True)) < 600


def test_rt01_contract_gate_runtime_order_matches_execution_contour(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-rt01-order")
    assert _first_order(events, "regulation") < _first_order(events, "c04_mode_arbitration")
    assert _first_order(events, "c04_mode_arbitration") < _first_order(events, "c05_temporal_validity")
    assert _first_order(events, "c05_temporal_validity") < _first_order(events, "downstream_obedience")
    assert _first_order(events, "world_entry_contract", "exit") < _first_order(
        events, "world_seam_enforcement"
    )
    assert _first_order(events, "world_seam_enforcement") < _first_order(events, "t01_semantic_field")
    assert _first_order(events, "bounded_outcome_resolution") < _first_order(events, "subject_tick")


def test_rt01_contract_gate_runtime_taps_defined_in_execute_subject_tick_source() -> None:
    source = Path("src/substrate/subject_tick/update.py").read_text(encoding="utf-8")
    for module in (
        "c04_mode_arbitration",
        "c05_temporal_validity",
        "world_seam_enforcement",
        "bounded_outcome_resolution",
    ):
        assert f'trace_emit_active("{module}"' in source


def test_s05_factorization_runtime_segment_emits_compact_local_fields(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-s05-fields")
    values = _module_decision_event(events, "s05_multi_cause_attribution_factorization")[
        "values"
    ]
    assert isinstance(values, dict)
    required = HOSTED_CONTOUR_FIELDS["s05_multi_cause_attribution_factorization"]
    assert required.issubset(set(values.keys()))
    assert set(values.keys()).issubset(
        set(MODULE_ALLOWED_FIELDS["s05_multi_cause_attribution_factorization"])
    )
    assert isinstance(values["residual_share"], (int, float))
    assert isinstance(values["factorization_consumer_ready"], bool)
    assert isinstance(values["learning_route_ready"], bool)
    assert "state" not in values
    assert "telemetry" not in values
    assert len(json.dumps(values, ensure_ascii=True)) < 700


def test_s05_factorization_runtime_order_is_between_s04_and_s_minimal(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-s05-order")
    assert _first_order(events, "s04_interoceptive_self_binding") < _first_order(
        events, "s05_multi_cause_attribution_factorization"
    )
    assert _first_order(events, "s05_multi_cause_attribution_factorization") < _first_order(
        events, "s_minimal_contour"
    )


def test_hosted_contour_segments_emit_runtime_events_when_executed(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-hosted-contour-presence")
    for module in HOSTED_CONTOUR_SEGMENTS:
        module_events = _module_events(events, module)
        assert module_events
        steps = {str(event["step"]) for event in module_events}
        assert "enter" in steps
        assert "decision" in steps
        assert "exit" in steps


def test_hosted_contour_segments_are_absent_when_route_not_executed(tmp_path: Path) -> None:
    _, events = _run_sample_trace(
        tmp_path,
        case_id="runtime-hosted-contour-not-executed",
        route_class="helper_path",
    )
    modules = {str(event["module"]) for event in events}
    for module in HOSTED_CONTOUR_SEGMENTS:
        assert module not in modules


def test_hosted_contour_fields_are_whitelisted_compact_and_non_aggregate(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-hosted-contour-whitelist")
    subject_values = _module_decision_event(events, "subject_tick")["values"]
    assert isinstance(subject_values, dict)

    for module in HOSTED_CONTOUR_SEGMENTS:
        values = _module_decision_event(events, module)["values"]
        required = HOSTED_CONTOUR_FIELDS[module]
        assert isinstance(values, dict)
        assert required.issubset(set(values.keys()))
        assert set(values.keys()).issubset(set(MODULE_ALLOWED_FIELDS[module]))
        assert "state" not in values
        assert "telemetry" not in values
        assert "execution_checkpoints" not in values
        assert len(json.dumps(values, ensure_ascii=True)) < 700
        for key in required:
            assert key not in subject_values


def test_hosted_contour_segments_follow_real_runtime_order(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-hosted-contour-order")
    assert _first_order(events, "regulation") < _first_order(events, "c01_stream_kernel")
    assert _first_order(events, "c01_stream_kernel") < _first_order(events, "c02_tension_scheduler")
    assert _first_order(events, "c02_tension_scheduler") < _first_order(
        events, "c03_stream_diversification"
    )
    assert _first_order(events, "c03_stream_diversification") < _first_order(
        events, "c04_mode_arbitration"
    )
    assert _first_order(events, "world_seam_enforcement") < _first_order(events, "s01_efference_copy")
    assert _first_order(events, "s01_efference_copy") < _first_order(events, "s02_prediction_boundary")
    assert _first_order(events, "s02_prediction_boundary") < _first_order(
        events, "s03_ownership_weighted_learning"
    )
    assert _first_order(events, "s03_ownership_weighted_learning") < _first_order(
        events, "s04_interoceptive_self_binding"
    )
    assert _first_order(events, "s04_interoceptive_self_binding") < _first_order(
        events, "s05_multi_cause_attribution_factorization"
    )
    assert _first_order(events, "s05_multi_cause_attribution_factorization") < _first_order(
        events, "s_minimal_contour"
    )
    assert _first_order(events, "t04_attention_schema") < _first_order(events, "o01_other_entity_model")
    assert _first_order(events, "o01_other_entity_model") < _first_order(
        events, "bounded_outcome_resolution"
    )
    assert _first_order(events, "s_minimal_contour") < _first_order(events, "a_line_normalization")
    assert _first_order(events, "a_line_normalization") < _first_order(events, "m_minimal")
    assert _first_order(events, "m_minimal") < _first_order(events, "n_minimal")
    assert _first_order(events, "n_minimal") < _first_order(events, "t01_semantic_field")
    assert _first_order(events, "bounded_outcome_resolution") < _first_order(events, "subject_tick")


def test_hosted_contour_middle_gap_is_now_runtime_visible(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-hosted-contour-gap-closure")
    reg_order = _first_order(events, "regulation")
    subject_order = _first_order(events, "subject_tick")
    middle_modules = {
        str(event["module"])
        for event in events
        if reg_order < int(event["order"]) < subject_order
    }
    visible = middle_modules.intersection(set(HOSTED_CONTOUR_SEGMENTS))
    assert len(visible) >= 8


def test_hosted_contour_runtime_taps_exist_in_subject_tick_source() -> None:
    source = Path("src/substrate/subject_tick/update.py").read_text(encoding="utf-8")
    for module in HOSTED_CONTOUR_SEGMENTS:
        assert module in source
        assert "trace_emit_active(" in source


def test_blocked_steps_only_appear_on_actual_blocked_paths(tmp_path: Path) -> None:
    _, events = _run_sample_trace(
        tmp_path,
        case_id="runtime-blocked-route",
        route_class="helper_path",
    )
    blocked_events = [event for event in events if event["step"] == "blocked"]
    assert blocked_events
    for blocked in blocked_events:
        module = str(blocked["module"])
        values = blocked["values"]
        if module == "runtime_topology":
            assert values.get("accepted") is False


def test_representative_modules_have_runtime_steps(tmp_path: Path) -> None:
    _, events = _run_sample_trace(tmp_path, case_id="runtime-step-presence")
    by_module: dict[str, list[str]] = {}
    for event in events:
        by_module.setdefault(str(event["module"]), []).append(str(event["step"]))

    for module in (
        "runtime_topology",
        "world_adapter",
        "world_entry_contract",
        "epistemics",
        "regulation",
        "t01_semantic_field",
        "t02_relation_binding",
        "t03_hypothesis_competition",
        "o01_other_entity_model",
        "downstream_obedience",
        "subject_tick",
    ):
        assert "enter" in by_module[module]
        assert "decision" in by_module[module]
        assert "exit" in by_module[module]


def test_no_verdict_vocabulary_anywhere_on_main_path(tmp_path: Path) -> None:
    trace_path, _ = _run_sample_trace(tmp_path, case_id="runtime-neutral-vocab")
    payload = trace_path.read_text(encoding="utf-8")
    for token in FORBIDDEN_VOCABULARY:
        assert token not in payload


def test_no_snapshot_map_reconstruction_path_in_simple_trace_module() -> None:
    source = Path("src/substrate/simple_trace.py").read_text(encoding="utf-8")
    assert "_build_snapshot_map" not in source
    assert "_MODULE_FIELD_PATHS" not in source
    assert "_MODULE_BLOCKED_RULES" not in source


def test_cli_smoke_writes_single_jsonl(tmp_path: Path) -> None:
    reset_trace_state()
    output_dir = tmp_path / "cli-out"
    exit_code = tick_trace_main(
        [
            "--case-id",
            "runtime-cli",
            "--energy",
            "66",
            "--cognitive",
            "44",
            "--safety",
            "74",
            "--unresolved-preference",
            "false",
            "--output-dir",
            str(output_dir),
        ]
    )
    assert exit_code == 0
    files = sorted(item for item in output_dir.iterdir() if item.is_file())
    assert len(files) == 1
    assert files[0].suffix == ".jsonl"
    events = _load_events(files[0])
    assert events
    assert {"tick_id", "order", "module", "step", "values", "note"} == set(events[0].keys())
