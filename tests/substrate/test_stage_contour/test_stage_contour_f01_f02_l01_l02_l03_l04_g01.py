import pytest

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
    evaluate_grounded_semantic_downstream_gate,
    persist_grounded_semantic_result_via_f01,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_g01_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g01-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g01-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g01-stage", content='we do not track "alpha" here tomorrow'),
        SourceMetadata(
            source_id="user-g01-stage",
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
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g01-stage"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g01-stage"),
    )
    grounded_result = build_grounded_semantic_substrate_legacy_compatibility(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref="m03:g01-stage",
        cooperation_anchor_ref="o03:g01-stage",
    )

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert grounded_result.bundle.substrate_units
    assert grounded_result.bundle.phrase_scaffolds
    assert grounded_result.bundle.normative_l05_l06_route_active is False
    assert grounded_result.bundle.legacy_surface_cue_fallback_used is True
    assert grounded_result.bundle.legacy_surface_cue_path_not_normative is True
    assert grounded_result.bundle.no_final_semantic_resolution is True
    assert grounded_result.no_final_semantic_resolution is True
    gate = evaluate_grounded_semantic_downstream_gate(grounded_result)
    assert "no_final_semantic_resolution" in gate.restrictions
    assert "legacy_surface_cue_fallback_used" in gate.restrictions
    assert "legacy_surface_cue_path_not_normative" in gate.restrictions
    assert "l04_only_input_not_equivalent_to_l05_l06_route" in gate.restrictions

    persisted = persist_grounded_semantic_result_via_f01(
        result=grounded_result,
        runtime_state=boot.state,
        transition_id="tr-g01-stage-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["grounded_semantic_snapshot"]
    assert snapshot["bundle"]["substrate_units"]
    assert snapshot["bundle"]["phrase_scaffolds"]
    assert snapshot["bundle"]["operator_carriers"] is not None
    assert snapshot["bundle"]["source_anchors"] is not None
    assert snapshot["bundle"]["normative_l05_l06_route_active"] is False
    assert snapshot["bundle"]["legacy_surface_cue_fallback_used"] is True
    assert snapshot["bundle"]["no_final_semantic_resolution"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]


def test_stage_contour_g01_typed_only_guards_no_raw_bypass() -> None:
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate_legacy_compatibility("raw dictum")
