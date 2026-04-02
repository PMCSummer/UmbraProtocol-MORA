import json

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import (
    build_dictum_candidates,
    dictum_result_to_payload,
    persist_dictum_result_via_f01,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l04-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-l04-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _dictum_result(text: str, material_id: str):
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
    return build_dictum_candidates(lexical, syntax, utterance_surface=surface)


def test_dictum_payload_keeps_load_bearing_fields() -> None:
    result = _dictum_result("we do not track alpha tomorrow 3", "m-l04-roundtrip-payload")
    payload = dictum_result_to_payload(result)
    assert payload["bundle"]["dictum_candidates"]
    first = payload["bundle"]["dictum_candidates"][0]
    assert first["predicate_frame"]
    assert first["argument_slots"] is not None
    assert first["negation_markers"] is not None
    assert first["temporal_markers"] is not None
    assert first["magnitude_markers"] is not None
    assert first["underspecified_slots"] is not None
    assert payload["telemetry"]["attempted_construction_paths"]
    assert payload["telemetry"]["magnitude_marker_count"] >= 0


def test_persist_reconstruct_continue_preserves_dictum_structure() -> None:
    state = _bootstrapped_state()
    first = _dictum_result("we track alpha", "m-l04-roundtrip-first")
    persisted_first = persist_dictum_result_via_f01(
        result=first,
        runtime_state=state,
        transition_id="tr-l04-roundtrip-first",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted_first.accepted is True
    second = _dictum_result("he qzxv", "m-l04-roundtrip-second")
    persisted_second = persist_dictum_result_via_f01(
        result=second,
        runtime_state=persisted_first.state,
        transition_id="tr-l04-roundtrip-second",
        requested_at="2026-04-04T00:11:00+00:00",
    )
    assert persisted_second.accepted is True
    snapshot = persisted_second.state.trace.events[-1].payload["dictum_snapshot"]
    assert snapshot["bundle"]["dictum_candidates"] is not None
    assert snapshot["bundle"]["unknowns"] is not None
    assert snapshot["telemetry"]["processed_candidate_ids"] is not None
    serialized = json.loads(json.dumps(snapshot))
    assert serialized["bundle"]["source_syntax_ref"]
