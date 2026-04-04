import pytest

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import (
    build_discourse_provenance_chain,
    derive_perspective_chain_contract_view,
    evaluate_perspective_chain_downstream_gate,
    persist_perspective_chain_result_via_f01,
)
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
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_g01_g02_g03_g04_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g04-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-g04-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g04-stage", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-g04-stage",
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
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g04-stage"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref="ctx:g04-stage"),
    )
    grounded_result = build_grounded_semantic_substrate_legacy_compatibility(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref="m04:g04-stage",
        cooperation_anchor_ref="o04:g04-stage",
    )
    runtime_graph_result = build_runtime_semantic_graph(grounded_result)
    applicability_result = build_scope_attribution(runtime_graph_result)
    perspective_chain_result = build_discourse_provenance_chain(applicability_result)

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert perspective_chain_result.bundle.chain_records
    assert perspective_chain_result.bundle.commitment_lineages
    assert perspective_chain_result.bundle.wrapped_propositions
    assert perspective_chain_result.bundle.no_truth_upgrade is True
    gate = evaluate_perspective_chain_downstream_gate(perspective_chain_result)
    assert "no_truth_upgrade" in gate.restrictions
    assert "perspective_chain_must_be_read" in gate.restrictions
    assert "accepted_chain_not_owner_truth" in gate.restrictions
    contract_view = derive_perspective_chain_contract_view(perspective_chain_result)
    assert contract_view.requires_chain_read is True
    assert contract_view.requires_usability_read is True
    assert contract_view.accepted_chain_not_owner_truth is True
    assert contract_view.strong_owner_commitment_permitted is False

    persisted = persist_perspective_chain_result_via_f01(
        result=perspective_chain_result,
        runtime_state=boot.state,
        transition_id="tr-g04-stage-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["discourse_provenance_snapshot"]
    assert snapshot["bundle"]["chain_records"]
    assert snapshot["bundle"]["wrapped_propositions"]
    assert snapshot["bundle"]["cross_turn_links"]
    assert snapshot["bundle"]["no_truth_upgrade"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]


def test_stage_contour_g04_typed_only_guard_no_raw_or_g03_bypass() -> None:
    with pytest.raises(TypeError):
        build_discourse_provenance_chain("raw text")
