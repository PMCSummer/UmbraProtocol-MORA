import pytest

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import (
    build_dictum_candidates,
    evaluate_dictum_downstream_gate,
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
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _build_dictum_result(material_id: str, text: str, context_ref: str):
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
    lexical_result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref=context_ref),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref=context_ref),
    )
    return epistemic, dictum_result


def _dictum_structure_signature(result) -> tuple[object, ...]:
    candidate_signature = tuple(
        (
            candidate.predicate_frame.clause_id,
            candidate.predicate_frame.quotation_sensitive,
            tuple(
                (
                    slot.role_label,
                    slot.unresolved,
                    slot.unresolved_reason,
                    len(slot.lexical_candidate_ids),
                    len(slot.reference_candidate_ids),
                )
                for slot in candidate.argument_slots
            ),
            tuple(
                (
                    marker.marker_kind,
                    marker.ambiguous,
                    marker.reason,
                )
                for marker in candidate.scope_markers
            ),
            tuple(
                (
                    marker.scope_ambiguous,
                    marker.reason,
                )
                for marker in candidate.negation_markers
            ),
            tuple(
                (
                    marker.anchor_kind.value,
                    marker.unresolved,
                    marker.reason,
                )
                for marker in candidate.temporal_markers
            ),
            tuple(
                (
                    marker.marker_kind,
                    marker.value_hint,
                    marker.unresolved,
                    marker.reason,
                )
                for marker in candidate.magnitude_markers
            ),
            tuple(
                (slot.slot_id_or_field, slot.reason)
                for slot in candidate.underspecified_slots
            ),
            candidate.ambiguity_reasons,
            candidate.polarity.value,
            candidate.quotation_sensitive,
        )
        for candidate in result.bundle.dictum_candidates
    )
    return (
        candidate_signature,
        len(result.bundle.conflicts),
        len(result.bundle.unknowns),
        result.telemetry.underspecified_slot_count,
        result.telemetry.scope_ambiguity_count,
        tuple(result.telemetry.downstream_gate.restrictions),
    )


def test_stage_contour_f01_f02_l01_l02_l03_l04_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l04-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-l04-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l04-stage", content='we do not track "alpha" here tomorrow'),
        SourceMetadata(
            source_id="user-l04-stage",
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
        discourse_context=LexicalDiscourseContext(context_ref="ctx:l04-stage"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:l04-stage"),
    )

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert dictum_result.bundle.dictum_candidates
    assert dictum_result.bundle.no_final_resolution_performed is True

    persisted = persist_dictum_result_via_f01(
        result=dictum_result,
        runtime_state=boot.state,
        transition_id="tr-l04-stage-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["dictum_snapshot"]
    assert snapshot["bundle"]["dictum_candidates"]
    assert snapshot["bundle"]["no_final_resolution_performed"] is True
    first = snapshot["bundle"]["dictum_candidates"][0]
    assert first["predicate_frame"]["predicate_token_id"]
    assert first["argument_slots"] is not None
    assert first["negation_markers"] is not None
    assert first["temporal_markers"] is not None
    assert first["underspecified_slots"] is not None
    assert snapshot["telemetry"]["magnitude_marker_count"] >= 0
    assert epistemic.unit.unit_id in snapshot["telemetry"]["source_lineage"]
    assert snapshot["telemetry"]["attempted_construction_paths"]


def test_stage_contour_l04_typed_only_guards_no_raw_bypass() -> None:
    with pytest.raises(TypeError):
        build_dictum_candidates("raw lexical", "raw syntax")


def test_stage_contour_l04_replay_stability_no_hidden_finalization_drift() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l04-stage-replay-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:20:00+00:00",
            event_id="ev-l04-stage-replay-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True

    _, first = _build_dictum_result(
        material_id="m-l04-stage-replay",
        text='we do not track "alpha" here tomorrow',
        context_ref="ctx:l04-stage-replay",
    )
    first_signature = _dictum_structure_signature(first)
    first_gate = evaluate_dictum_downstream_gate(first)

    persisted = persist_dictum_result_via_f01(
        result=first,
        runtime_state=boot.state,
        transition_id="tr-l04-stage-replay-persist",
        requested_at="2026-04-04T00:21:00+00:00",
    )
    assert persisted.accepted is True

    _, second = _build_dictum_result(
        material_id="m-l04-stage-replay",
        text='we do not track "alpha" here tomorrow',
        context_ref="ctx:l04-stage-replay",
    )
    second_signature = _dictum_structure_signature(second)
    second_gate = evaluate_dictum_downstream_gate(second)

    assert first.no_final_resolution_performed is True
    assert second.no_final_resolution_performed is True
    assert first_signature == second_signature
    assert first_gate.restrictions == second_gate.restrictions
