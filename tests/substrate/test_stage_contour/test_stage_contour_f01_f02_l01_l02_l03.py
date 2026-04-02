import pytest

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
    persist_lexical_grounding_result_via_f01,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l03-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-03T00:00:00+00:00",
            event_id="ev-l03-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l03-stage", content='he said "bank" here now'),
        SourceMetadata(
            source_id="user-l03-stage",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    lexical_result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(
            context_ref="ctx:l03-stage",
            indexical_bindings=(("location", "loc:chat"), ("time", "time:turn")),
        ),
    )

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert lexical_result.bundle.no_final_resolution_performed is True
    assert lexical_result.bundle.mention_anchors
    assert lexical_result.bundle.lexeme_candidates

    persisted = persist_lexical_grounding_result_via_f01(
        result=lexical_result,
        runtime_state=boot.state,
        transition_id="tr-l03-stage-persist",
        requested_at="2026-04-03T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["lexical_grounding_snapshot"]
    assert snapshot["bundle"]["mention_anchors"]
    assert snapshot["bundle"]["lexeme_candidates"]
    assert snapshot["bundle"]["reference_hypotheses"]
    assert snapshot["bundle"]["deixis_candidates"] is not None
    assert snapshot["bundle"]["syntax_instability_present"] in (True, False)
    assert snapshot["bundle"]["no_final_resolution_performed"] is True
    assert snapshot["bundle"]["mention_anchors"][0]["supporting_syntax_hypothesis_refs"]
    assert snapshot["telemetry"]["attempted_grounding_paths"]


def test_stage_contour_l03_replay_stability_and_typed_only_bypass_guard() -> None:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l03-stage-replay", content="he bank here"),
        SourceMetadata(
            source_id="user-l03-stage-replay",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    context = LexicalDiscourseContext(context_ref="ctx:l03-stage-replay")

    first = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=context,
    )
    second = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=context,
    )

    first_signature = (
        len(first.bundle.mention_anchors),
        len(first.bundle.lexeme_candidates),
        len(first.bundle.reference_hypotheses),
        len(first.bundle.deixis_candidates),
        len(first.bundle.unknown_states),
        len(first.bundle.conflicts),
        tuple(sorted(first.bundle.ambiguity_reasons)),
    )
    second_signature = (
        len(second.bundle.mention_anchors),
        len(second.bundle.lexeme_candidates),
        len(second.bundle.reference_hypotheses),
        len(second.bundle.deixis_candidates),
        len(second.bundle.unknown_states),
        len(second.bundle.conflicts),
        tuple(sorted(second.bundle.ambiguity_reasons)),
    )

    assert first_signature == second_signature
    assert first.bundle.no_final_resolution_performed is True
    assert second.bundle.no_final_resolution_performed is True

    with pytest.raises(TypeError):
        build_lexical_grounding_hypotheses("raw text")
