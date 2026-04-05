import pytest

from substrate.concept_framing import build_concept_framing
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
from substrate.discourse_update import build_discourse_update
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
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import build_semantic_acquisition
from substrate.state import create_empty_state
from substrate.targeted_clarification import (
    build_targeted_clarification,
    derive_targeted_clarification_contract_view,
    evaluate_targeted_clarification_downstream_gate,
    persist_targeted_clarification_result_via_f01,
)
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_g01_g02_g03_g04_g05_g06_g07_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g07-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g07-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g07-stage", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-g07-stage",
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
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g07-stage"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g07-stage"),
    )
    modus_result = build_modus_hypotheses(dictum_result)
    discourse_update_result = build_discourse_update(modus_result)
    grounded_result = build_grounded_semantic_substrate_normative(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref="m07:g07-stage",
        cooperation_anchor_ref="o07:g07-stage",
    )
    runtime_graph_result = build_runtime_semantic_graph(grounded_result)
    applicability_result = build_scope_attribution(runtime_graph_result)
    perspective_result = build_discourse_provenance_chain(applicability_result)
    acquisition_result = build_semantic_acquisition(perspective_result)
    framing_result = build_concept_framing(acquisition_result)
    intervention_result = build_targeted_clarification(
        acquisition_result,
        framing_result,
        discourse_update_result,
    )

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert intervention_result.bundle.intervention_records
    assert intervention_result.bundle.l06_upstream_bound_here is True
    assert intervention_result.bundle.l06_update_proposal_absent is False
    assert intervention_result.bundle.l06_continuation_topology_present is True
    assert intervention_result.bundle.response_realization_contract_absent is True
    assert intervention_result.bundle.answer_binding_consumer_absent is True
    gate = evaluate_targeted_clarification_downstream_gate(intervention_result)
    assert "intervention_requires_target_binding_read" in gate.restrictions
    assert "downstream_lockouts_must_be_read" in gate.restrictions
    assert "clarification_not_equal_realized_question" in gate.restrictions
    assert "asked_question_not_equal_resolved_uncertainty" in gate.restrictions
    contract_view = derive_targeted_clarification_contract_view(intervention_result)
    assert contract_view.requires_target_binding_read is True
    assert contract_view.requires_lockouts_read is True
    assert contract_view.strong_continue_permission is False

    persisted = persist_targeted_clarification_result_via_f01(
        result=intervention_result,
        runtime_state=boot.state,
        transition_id="tr-g07-stage-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["targeted_clarification_snapshot"]
    assert snapshot["bundle"]["intervention_records"]
    assert snapshot["bundle"]["l06_upstream_bound_here"] is True
    assert snapshot["bundle"]["l06_update_proposal_absent"] is False
    assert snapshot["bundle"]["response_realization_contract_absent"] is True
    assert snapshot["bundle"]["answer_binding_consumer_absent"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]


def test_stage_contour_g07_typed_only_guard_no_raw_or_single_input_bypass() -> None:
    with pytest.raises(TypeError):
        build_targeted_clarification("raw acquisition", "raw framing", "raw discourse_update")
