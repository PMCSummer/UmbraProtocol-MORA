import json

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.morphosyntax import (
    build_morphosyntax_candidate_space,
    persist_syntax_result_via_f01,
    syntax_result_to_payload,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l02-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-l02-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _syntax_result(text: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l02-roundtrip", content=text),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    return build_morphosyntax_candidate_space(surface_result)


def test_roundtrip_snapshot_preserves_load_bearing_syntax_fields() -> None:
    result = _syntax_result("we do not track alpha ... beta")
    payload = syntax_result_to_payload(result)
    hypothesis = payload["hypothesis_set"]["hypotheses"][0]

    assert hypothesis["clause_graph"]["clauses"]
    assert hypothesis["edges"]
    assert hypothesis["unresolved_attachments"]
    assert hypothesis["token_features"]
    assert hypothesis["agreement_cues"]
    assert hypothesis["clause_graph"]["clauses"][0]["negation_carrier_ids"] or payload["telemetry"][
        "negation_carrier_count"
    ] > 0
    assert payload["telemetry"]["ambiguity_reasons"]


def test_persistence_via_f01_keeps_structural_snapshot_and_telemetry_integrity() -> None:
    state = _bootstrapped_state()
    result = _syntax_result("we do not track alpha ... beta")
    persisted = persist_syntax_result_via_f01(
        result=result,
        runtime_state=state,
        transition_id="tr-l02-roundtrip-persist",
        requested_at="2026-04-02T00:05:00+00:00",
    )
    assert persisted.accepted is True
    snapshot = persisted.state.trace.events[-1].payload["syntax_snapshot"]
    first = snapshot["hypothesis_set"]["hypotheses"][0]

    assert first["clause_graph"]["clauses"]
    assert first["edges"]
    assert first["unresolved_attachments"]
    assert first["token_features"]
    assert first["agreement_cues"]
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["input_surface_ref"] == snapshot["hypothesis_set"]["source_surface_ref"]

    as_json = json.loads(json.dumps(snapshot))
    assert as_json["hypothesis_set"]["hypotheses"][0]["clause_graph"]["clauses"]
    assert as_json["hypothesis_set"]["hypotheses"][0]["edges"]
    assert as_json["telemetry"]["ambiguity_reasons"]
