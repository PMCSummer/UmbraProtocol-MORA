from __future__ import annotations

import json

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import (
    build_discourse_provenance_chain,
    persist_perspective_chain_result_via_f01,
    perspective_chain_result_to_payload,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g04-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g04-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _g04_result(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate_normative(dictum, utterance_surface=surface)
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


def test_discourse_provenance_payload_keeps_load_bearing_fields() -> None:
    result = _g04_result('he said "you are tired?"', "m-g04-roundtrip-payload")
    payload = perspective_chain_result_to_payload(result)
    assert payload["bundle"]["chain_records"]
    assert payload["bundle"]["wrapped_propositions"]
    assert payload["bundle"]["cross_turn_links"]
    assert payload["bundle"]["no_truth_upgrade"] is True
    assert payload["telemetry"]["attempted_paths"]
    assert payload["telemetry"]["downstream_gate"]["usability_class"] in {
        "usable_bounded",
        "degraded_bounded",
        "blocked",
    }
    serialized = json.loads(json.dumps(payload))
    assert serialized["bundle"]["source_applicability_ref"]


def test_persist_reconstruct_continue_preserves_perspective_chain_contract() -> None:
    state = _bootstrapped_state()
    first = _g04_result("i was quoting him", "m-g04-roundtrip-first")
    persisted = persist_perspective_chain_result_via_f01(
        result=first,
        runtime_state=state,
        transition_id="tr-g04-roundtrip-first",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    snapshot = persisted.state.trace.events[-1].payload["discourse_provenance_snapshot"]
    assert snapshot["bundle"]["chain_records"]
    assert snapshot["bundle"]["wrapped_propositions"]
    assert snapshot["bundle"]["cross_turn_links"]
    assert snapshot["bundle"]["no_truth_upgrade"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"] is not None
    assert "perspective_chain_must_be_read" in snapshot["telemetry"]["downstream_gate"]["restrictions"]
    assert "accepted_chain_not_owner_truth" in snapshot["telemetry"]["downstream_gate"]["restrictions"]
