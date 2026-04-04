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
from substrate.grounded_semantic import build_grounded_semantic_substrate_legacy_compatibility
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import (
    build_runtime_semantic_graph,
    evaluate_runtime_graph_downstream_gate,
    persist_runtime_graph_result_via_f01,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_g01_g02_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g02-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g02-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g02-stage", content='we do not track "alpha" here tomorrow'),
        SourceMetadata(
            source_id="user-g02-stage",
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
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g02-stage"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g02-stage"),
    )
    grounded_result = build_grounded_semantic_substrate_legacy_compatibility(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref="m03:g02-stage",
        cooperation_anchor_ref="o03:g02-stage",
    )
    graph_result = build_runtime_semantic_graph(grounded_result)

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert graph_result.bundle.semantic_units
    assert graph_result.bundle.graph_edges
    assert graph_result.bundle.proposition_candidates
    assert graph_result.bundle.no_final_semantic_closure is True
    assert graph_result.no_final_semantic_closure is True
    gate = evaluate_runtime_graph_downstream_gate(graph_result)
    assert "no_final_semantic_closure" in gate.restrictions

    persisted = persist_runtime_graph_result_via_f01(
        result=graph_result,
        runtime_state=boot.state,
        transition_id="tr-g02-stage-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["runtime_semantic_graph_snapshot"]
    assert snapshot["bundle"]["semantic_units"]
    assert snapshot["bundle"]["proposition_candidates"]
    assert snapshot["bundle"]["no_final_semantic_closure"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]


def test_stage_contour_g02_typed_only_guards_no_raw_or_l04_bypass() -> None:
    with pytest.raises(TypeError):
        build_runtime_semantic_graph("raw text")

