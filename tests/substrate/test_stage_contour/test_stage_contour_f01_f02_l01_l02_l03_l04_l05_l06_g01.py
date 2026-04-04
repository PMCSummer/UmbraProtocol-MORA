import pytest

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_update import build_discourse_update
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    build_grounded_semantic_substrate,
    evaluate_grounded_semantic_downstream_gate,
    persist_grounded_semantic_result_via_f01,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_l05_l06_g01_normative_route_is_runtime_active() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-g01-l06-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-05T00:00:00+00:00",
            event_id="ev-g01-l06-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-g01-l06-stage", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-g01-l06-stage",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    modus = build_modus_hypotheses(dictum)
    discourse_update = build_discourse_update(modus)
    grounded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:g01-l06-stage",
        cooperation_anchor_ref="o03:g01-l06-stage",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert grounded.bundle.normative_l05_l06_route_active is True
    assert grounded.bundle.legacy_surface_cue_fallback_used is False
    assert grounded.bundle.discourse_update_not_inferred_from_surface_when_l06_available is True
    gate = evaluate_grounded_semantic_downstream_gate(grounded)
    assert "normative_l05_l06_route_active" in gate.restrictions
    assert "discourse_update_not_inferred_from_surface_when_l06_available" in gate.restrictions
    assert "legacy_surface_cue_fallback_used" not in gate.restrictions

    persisted = persist_grounded_semantic_result_via_f01(
        result=grounded,
        runtime_state=boot.state,
        transition_id="tr-g01-l06-stage-persist",
        requested_at="2026-04-05T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["grounded_semantic_snapshot"]
    assert snapshot["bundle"]["normative_l05_l06_route_active"] is True
    assert snapshot["bundle"]["legacy_surface_cue_fallback_used"] is False
    assert snapshot["bundle"]["discourse_update_not_inferred_from_surface_when_l06_available"] is True


def test_stage_contour_g01_normative_route_requires_both_typed_l05_and_l06_inputs() -> None:
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate(
            "raw dictum",
            modus_hypotheses_result_or_bundle="raw l05",
            discourse_update_result_or_bundle="raw l06",
        )
