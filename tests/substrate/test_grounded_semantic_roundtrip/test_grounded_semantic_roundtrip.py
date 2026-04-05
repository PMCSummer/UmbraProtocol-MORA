from __future__ import annotations

import json

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    build_grounded_semantic_substrate_legacy_compatibility,
    grounded_semantic_result_to_payload,
    persist_grounded_semantic_result_via_f01,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g01-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g01-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _g01_result(text: str, material_id: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    return build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )


def test_grounded_semantic_payload_keeps_load_bearing_fields() -> None:
    result = _g01_result('operator said "alpha maybe moved"...', "m-g01-roundtrip-payload")
    payload = grounded_semantic_result_to_payload(result)
    assert payload["bundle"]["substrate_units"]
    assert payload["bundle"]["phrase_scaffolds"]
    assert payload["bundle"]["operator_carriers"]
    assert payload["bundle"]["dictum_carriers"]
    assert payload["bundle"]["modus_carriers"] is not None
    assert payload["bundle"]["source_anchors"] is not None
    assert payload["bundle"]["uncertainty_markers"] is not None
    assert payload["bundle"]["no_final_semantic_resolution"] is True
    assert payload["bundle"]["source_modus_ref_kind"] == "not_bound"
    assert payload["bundle"]["source_discourse_update_ref_kind"] == "not_bound"
    assert payload["telemetry"]["downstream_gate"]["restrictions"]
    serialized = json.loads(json.dumps(payload))
    assert serialized["bundle"]["source_dictum_ref"]


def test_persist_reconstruct_continue_preserves_g01_scaffold_contract() -> None:
    state = _bootstrapped_state()
    first = _g01_result("we do not track alpha", "m-g01-roundtrip-first")
    persisted = persist_grounded_semantic_result_via_f01(
        result=first,
        runtime_state=state,
        transition_id="tr-g01-roundtrip-first",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    snapshot = persisted.state.trace.events[-1].payload["grounded_semantic_snapshot"]
    assert snapshot["bundle"]["phrase_scaffolds"]
    assert snapshot["bundle"]["operator_carriers"] is not None
    assert snapshot["bundle"]["uncertainty_markers"] is not None
    assert snapshot["bundle"]["no_final_semantic_resolution"] is True
    assert snapshot["bundle"]["source_modus_ref_kind"] == "not_bound"
    assert snapshot["bundle"]["source_discourse_update_ref_kind"] == "not_bound"
    assert snapshot["telemetry"]["attempted_paths"]

    second = _g01_result("we do not track alpha", "m-g01-roundtrip-first")
    assert first.bundle.low_coverage_mode == second.bundle.low_coverage_mode
    assert len(first.bundle.operator_carriers) == len(second.bundle.operator_carriers)
    assert len(first.bundle.phrase_scaffolds) == len(second.bundle.phrase_scaffolds)
