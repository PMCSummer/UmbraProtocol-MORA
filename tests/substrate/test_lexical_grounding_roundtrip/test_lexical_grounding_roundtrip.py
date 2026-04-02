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
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
    lexical_grounding_result_to_payload,
    persist_lexical_grounding_result_via_f01,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l03-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-03T00:00:00+00:00",
            event_id="ev-l03-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _l03_result(text: str, *, material_id: str, context: LexicalDiscourseContext | None = None):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    return build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=context,
    )


def test_roundtrip_payload_contains_load_bearing_lexical_reference_fields() -> None:
    result = _l03_result(
        'he said "bank" here qzxv',
        material_id="m-l03-roundtrip-payload",
        context=LexicalDiscourseContext(context_ref="ctx:roundtrip"),
    )
    payload = lexical_grounding_result_to_payload(result)

    assert payload["bundle"]["mention_anchors"]
    assert payload["bundle"]["lexeme_candidates"]
    assert payload["bundle"]["sense_candidates"]
    assert payload["bundle"]["entity_candidates"]
    assert payload["bundle"]["reference_hypotheses"]
    assert payload["bundle"]["deixis_candidates"]
    assert payload["bundle"]["unknown_states"] is not None
    assert payload["bundle"]["conflicts"] is not None
    assert payload["bundle"]["no_final_resolution_performed"] is True
    assert payload["telemetry"]["attempted_grounding_paths"]
    assert payload["telemetry"]["generated_candidate_ids"]
    assert payload["telemetry"]["downstream_gate"]["restrictions"] is not None


def test_persist_reconstruct_continue_preserves_artifacts_and_lineage() -> None:
    state = _bootstrapped_state()
    initial_revision = state.runtime.revision

    first = _l03_result(
        "he arrived here now",
        material_id="m-l03-roundtrip-first",
        context=LexicalDiscourseContext(
            context_ref="ctx:first",
            indexical_bindings=(("location", "loc:one"),),
        ),
    )
    persisted_first = persist_lexical_grounding_result_via_f01(
        result=first,
        runtime_state=state,
        transition_id="tr-l03-roundtrip-first",
        requested_at="2026-04-03T00:10:00+00:00",
    )
    assert persisted_first.accepted is True
    assert persisted_first.state.runtime.revision == initial_revision + 1

    second = _l03_result(
        "qzxv he",
        material_id="m-l03-roundtrip-second",
        context=LexicalDiscourseContext(context_ref="ctx:second"),
    )
    persisted_second = persist_lexical_grounding_result_via_f01(
        result=second,
        runtime_state=persisted_first.state,
        transition_id="tr-l03-roundtrip-second",
        requested_at="2026-04-03T00:11:00+00:00",
    )
    assert persisted_second.accepted is True
    assert persisted_second.state.runtime.revision == initial_revision + 2

    first_snapshot = persisted_first.state.trace.events[-1].payload["lexical_grounding_snapshot"]
    second_snapshot = persisted_second.state.trace.events[-1].payload["lexical_grounding_snapshot"]

    assert first_snapshot["bundle"]["mention_anchors"]
    assert first_snapshot["bundle"]["reference_hypotheses"]
    assert first_snapshot["bundle"]["deixis_candidates"]
    assert second_snapshot["bundle"]["unknown_states"]
    assert second_snapshot["bundle"]["reference_hypotheses"]
    assert second_snapshot["bundle"]["no_final_resolution_performed"] is True

    serialized = json.loads(json.dumps(second_snapshot))
    assert serialized["bundle"]["mention_anchors"]
    assert serialized["telemetry"]["source_lineage"]
