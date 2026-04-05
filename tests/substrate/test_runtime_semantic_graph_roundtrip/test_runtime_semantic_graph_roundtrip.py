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
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import (
    build_runtime_semantic_graph,
    persist_runtime_graph_result_via_f01,
    runtime_graph_result_to_payload,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g02-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g02-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _g02_result(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m03:{material_id}",
        cooperation_anchor_ref=f"o03:{material_id}",
    )
    return build_runtime_semantic_graph(grounded)


def test_runtime_graph_payload_keeps_load_bearing_fields() -> None:
    result = _g02_result('operator said "alpha maybe moved"...', "m-g02-roundtrip-payload")
    payload = runtime_graph_result_to_payload(result)
    assert payload["bundle"]["semantic_units"]
    assert payload["bundle"]["role_bindings"] is not None
    assert payload["bundle"]["graph_edges"] is not None
    assert payload["bundle"]["proposition_candidates"]
    assert payload["bundle"]["graph_alternatives"] is not None
    assert payload["bundle"]["no_final_semantic_closure"] is True
    assert payload["telemetry"]["attempted_paths"]
    assert payload["telemetry"]["downstream_gate"]["usability_class"] in {
        "usable_bounded",
        "degraded_bounded",
        "blocked",
    }
    assert payload["telemetry"]["downstream_gate"]["restrictions"]
    serialized = json.loads(json.dumps(payload))
    assert serialized["bundle"]["source_grounded_ref"]


def test_persist_reconstruct_continue_preserves_runtime_graph_contract() -> None:
    state = _bootstrapped_state()
    first = _g02_result("we do not track alpha", "m-g02-roundtrip-first")
    persisted = persist_runtime_graph_result_via_f01(
        result=first,
        runtime_state=state,
        transition_id="tr-g02-roundtrip-first",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    snapshot = persisted.state.trace.events[-1].payload["runtime_semantic_graph_snapshot"]
    assert snapshot["bundle"]["semantic_units"]
    assert snapshot["bundle"]["proposition_candidates"]
    assert snapshot["bundle"]["no_final_semantic_closure"] is True
    assert snapshot["telemetry"]["attempted_paths"]

    second = _g02_result("we do not track alpha", "m-g02-roundtrip-first")
    assert first.bundle.low_coverage_mode == second.bundle.low_coverage_mode
    assert len(first.bundle.proposition_candidates) == len(second.bundle.proposition_candidates)
    assert len(first.bundle.graph_edges) == len(second.bundle.graph_edges)
