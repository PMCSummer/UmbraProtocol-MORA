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
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import (
    build_scope_attribution,
    derive_applicability_contract_view,
    evaluate_applicability_downstream_gate,
    persist_applicability_result_via_f01,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_g01_g02_g03_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g03-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g03-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g03-stage", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-g03-stage",
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
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g03-stage"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g03-stage"),
    )
    grounded_result = build_grounded_semantic_substrate_normative(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref="m03:g03-stage",
        cooperation_anchor_ref="o03:g03-stage",
    )
    runtime_graph_result = build_runtime_semantic_graph(grounded_result)
    applicability_result = build_scope_attribution(runtime_graph_result)

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert applicability_result.bundle.records
    assert applicability_result.bundle.permission_mappings
    assert applicability_result.bundle.no_truth_upgrade is True
    assert applicability_result.no_truth_upgrade is True
    gate = evaluate_applicability_downstream_gate(applicability_result)
    assert "no_truth_upgrade" in gate.restrictions
    assert "permissions_must_be_read" in gate.restrictions
    contract_view = derive_applicability_contract_view(applicability_result)
    assert contract_view.requires_permission_read is True
    assert contract_view.requires_restriction_read is True

    persisted = persist_applicability_result_via_f01(
        result=applicability_result,
        runtime_state=boot.state,
        transition_id="tr-g03-stage-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["scope_attribution_snapshot"]
    assert snapshot["bundle"]["records"]
    assert snapshot["bundle"]["permission_mappings"]
    assert snapshot["bundle"]["no_truth_upgrade"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]


def test_stage_contour_g03_typed_only_guards_no_raw_or_g02_bypass() -> None:
    with pytest.raises(TypeError):
        build_scope_attribution("raw text")
