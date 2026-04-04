import pytest

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_update import (
    build_discourse_update,
    derive_discourse_update_contract_view,
    evaluate_discourse_update_downstream_gate,
    persist_discourse_update_result_via_f01,
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
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_l03_l04_l05_l06_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l06-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-05T00:00:00+00:00",
            event_id="ev-l06-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_events = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l06-stage", content='he said "you are tired?"'),
        SourceMetadata(
            source_id="user-l06-stage",
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

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_events
    assert discourse_update.bundle.update_proposals
    assert discourse_update.bundle.repair_triggers
    gate = evaluate_discourse_update_downstream_gate(discourse_update)
    assert "proposal_requires_acceptance" in gate.restrictions
    assert "interpretation_not_equal_accepted_update" in gate.restrictions
    assert "repair_trigger_must_be_localized" in gate.restrictions
    assert "legacy_bypass_risk_present" in gate.restrictions
    contract = derive_discourse_update_contract_view(discourse_update)
    assert contract.requires_acceptance_read is True
    assert contract.requires_repair_read is True
    assert contract.strong_update_permission is False

    persisted = persist_discourse_update_result_via_f01(
        result=discourse_update,
        runtime_state=boot.state,
        transition_id="tr-l06-stage-persist",
        requested_at="2026-04-05T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    snapshot = persisted.state.trace.events[-1].payload["discourse_update_snapshot"]
    assert snapshot["bundle"]["update_proposals"]
    assert snapshot["bundle"]["repair_triggers"]
    assert snapshot["bundle"]["legacy_g01_bypass_risk_present"] is True
    assert snapshot["telemetry"]["downstream_gate"]["restrictions"]


def test_stage_contour_l06_typed_only_guard_no_raw_bypass() -> None:
    with pytest.raises(TypeError):
        build_discourse_update("raw l05")
