from __future__ import annotations

import json

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import (
    build_semantic_acquisition,
    persist_semantic_acquisition_result_via_f01,
    semantic_acquisition_result_to_payload,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g05-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g05-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _g05_result(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate(dictum, utterance_surface=surface)
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    perspective = build_discourse_provenance_chain(applicability)
    return build_semantic_acquisition(perspective)


def test_semantic_acquisition_payload_keeps_load_bearing_fields() -> None:
    result = _g05_result("he said that you are tired?", "m-g05-roundtrip-payload")
    payload = semantic_acquisition_result_to_payload(result)
    assert payload["bundle"]["acquisition_records"]
    assert payload["bundle"]["cluster_links"]
    assert payload["bundle"]["no_final_semantic_closure"] is True
    assert payload["telemetry"]["attempted_paths"]
    assert payload["telemetry"]["downstream_gate"]["usability_class"] in {
        "usable_bounded",
        "degraded_bounded",
        "blocked",
    }
    serialized = json.loads(json.dumps(payload))
    assert serialized["bundle"]["source_perspective_chain_ref"]


def test_persist_reconstruct_continue_preserves_semantic_acquisition_contract() -> None:
    state = _bootstrapped_state()
    first = _g05_result("i was quoting him", "m-g05-roundtrip-first")
    persisted = persist_semantic_acquisition_result_via_f01(
        result=first,
        runtime_state=state,
        transition_id="tr-g05-roundtrip-first",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    snapshot = persisted.state.trace.events[-1].payload["semantic_acquisition_snapshot"]
    assert snapshot["bundle"]["acquisition_records"]
    assert snapshot["bundle"]["cluster_links"]
    assert snapshot["bundle"]["no_final_semantic_closure"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"] is not None
    assert "acquisition_status_must_be_read" in snapshot["telemetry"]["downstream_gate"]["restrictions"]
