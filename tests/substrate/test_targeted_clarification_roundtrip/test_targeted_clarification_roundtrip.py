from __future__ import annotations

from substrate.targeted_clarification import (
    build_targeted_clarification,
    targeted_clarification_result_to_payload,
)


def test_snapshot_roundtrip_contains_load_bearing_intervention_fields(g07_factory) -> None:
    ctx = g07_factory('he said "you are tired?"', "g07-roundtrip")
    result = build_targeted_clarification(
        ctx.acquisition,
        ctx.framing,
        ctx.discourse_update,
    )
    payload = targeted_clarification_result_to_payload(result)
    assert payload["bundle"]["intervention_records"]
    assert payload["bundle"]["source_acquisition_ref_kind"] == "phase_native_derived_ref"
    assert payload["bundle"]["source_framing_ref_kind"] == "phase_native_derived_ref"
    assert payload["bundle"]["source_discourse_update_ref_kind"] == "phase_native_derived_ref"
    assert payload["bundle"]["source_acquisition_ref"] != payload["bundle"]["source_acquisition_lineage_ref"]
    assert payload["bundle"]["source_framing_ref"] != payload["bundle"]["source_framing_lineage_ref"]
    assert payload["bundle"]["source_discourse_update_ref"] != payload["bundle"]["source_discourse_update_lineage_ref"]
    first = payload["bundle"]["intervention_records"][0]
    assert "uncertainty_target_id" in first
    assert "intervention_status" in first
    assert "minimal_question_spec" in first
    assert "forbidden_presuppositions" in first
    assert "expected_evidence_gain" in first
    assert "downstream_lockouts" in first
    assert payload["bundle"]["l06_upstream_bound_here"] is True
    assert payload["bundle"]["l06_update_proposal_absent"] is False
    assert payload["bundle"]["response_realization_contract_absent"] is True
    assert payload["bundle"]["answer_binding_consumer_absent"] is True
    assert payload["telemetry"]["source_acquisition_ref_kind"] == "phase_native_derived_ref"
    assert payload["telemetry"]["source_framing_ref_kind"] == "phase_native_derived_ref"
    assert payload["telemetry"]["source_discourse_update_ref_kind"] == "phase_native_derived_ref"
    assert payload["telemetry"]["downstream_gate"]["restrictions"]
