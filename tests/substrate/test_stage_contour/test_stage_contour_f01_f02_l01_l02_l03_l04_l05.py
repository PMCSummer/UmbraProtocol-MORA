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
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import (
    build_modus_hypotheses,
    derive_modus_hypothesis_contract_view,
    evaluate_modus_hypothesis_downstream_gate,
    persist_modus_hypothesis_result_via_f01,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_l05_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l05-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-l05-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l05-stage", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-l05-stage",
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
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
    )
    modus_result = build_modus_hypotheses(dictum_result)

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert modus_result.bundle.hypothesis_records
    gate = evaluate_modus_hypothesis_downstream_gate(modus_result)
    assert "dictum_not_equal_force" in gate.restrictions
    assert "likely_illocution_not_settled_intent" in gate.restrictions
    assert "quoted_force_not_current_commitment" in gate.restrictions
    assert "l06_downstream_absent" in gate.restrictions
    assert "legacy_l04_g01_shortcut_operational_debt" in gate.restrictions
    assert "legacy_shortcut_bypass_risk" in gate.restrictions
    contract = derive_modus_hypothesis_contract_view(modus_result)
    assert contract.multi_hypothesis_present is True
    assert contract.strong_intent_resolution_permitted is False
    assert contract.discourse_update_permission is False

    persisted = persist_modus_hypothesis_result_via_f01(
        result=modus_result,
        runtime_state=boot.state,
        transition_id="tr-l05-stage-persist",
        requested_at="2026-04-04T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["modus_hypothesis_snapshot"]
    assert snapshot["bundle"]["hypothesis_records"]
    assert snapshot["bundle"]["l06_downstream_absent"] is True
    assert snapshot["bundle"]["discourse_update_consumer_absent"] is True
    assert snapshot["bundle"]["repair_trigger_consumer_absent"] is True
    assert snapshot["bundle"]["legacy_l04_g01_shortcut_operational_debt"] is True
    assert snapshot["bundle"]["legacy_shortcut_bypass_risk"] is True
    assert snapshot["telemetry"]["attempted_paths"]
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]


def test_stage_contour_l05_typed_only_guard_no_raw_bypass() -> None:
    with pytest.raises(TypeError):
        build_modus_hypotheses("raw dictum")
