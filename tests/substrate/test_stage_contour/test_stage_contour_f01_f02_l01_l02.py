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
from substrate.morphosyntax import (
    build_morphosyntax_candidate_space,
    persist_syntax_result_via_f01,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l02-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-l02-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision
    start_event_count = len(boot.state.trace.events)

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l02-stage", content="we do not track alpha beta"),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)

    assert boot.state.runtime.revision == start_revision
    assert len(boot.state.trace.events) == start_event_count
    assert syntax_result.hypothesis_set.source_surface_ref == surface_result.surface.epistemic_unit_ref

    persisted = persist_syntax_result_via_f01(
        result=syntax_result,
        runtime_state=boot.state,
        transition_id="tr-l02-persist",
        requested_at="2026-04-02T00:05:00+00:00",
    )

    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == start_revision + 1

    payload = persisted.state.trace.events[-1].payload["syntax_snapshot"]
    assert payload["hypothesis_set"]["source_surface_ref"] == surface_result.surface.epistemic_unit_ref
    assert payload["hypothesis_set"]["no_selected_winner"] is True
    assert payload["hypothesis_set"]["hypotheses"]
    first_hypothesis = payload["hypothesis_set"]["hypotheses"][0]
    assert first_hypothesis["token_features"]
    assert first_hypothesis["edges"]
    assert first_hypothesis["agreement_cues"]
    assert first_hypothesis["unresolved_attachments"]
    assert payload["telemetry"]["attempted_paths"]
    assert payload["telemetry"]["morphology_feature_count"] > 0
