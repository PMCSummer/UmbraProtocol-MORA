from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import (
    build_utterance_surface,
    persist_surface_result_via_f01,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_uses_single_runtime_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l01-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-l01-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    initial_revision = boot.state.runtime.revision

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l01-stage", content='"blarf zint", — сказал user'),
        SourceMetadata(
            source_id="user-source",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    assert surface_result.surface.tokens
    assert surface_result.surface.reversible_span_map_present is True
    assert boot.state.runtime.revision == initial_revision

    persisted = persist_surface_result_via_f01(
        result=surface_result,
        runtime_state=boot.state,
        transition_id="tr-l01-persist",
        requested_at="2026-04-02T00:05:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.provenance.writer == WriterIdentity.TRANSITION_ENGINE
    assert persisted.provenance.transition_kind == TransitionKind.APPLY_INTERNAL_EVENT
    assert persisted.state.runtime.revision == initial_revision + 1
    assert "surface_snapshot" in persisted.state.trace.events[-1].payload
    snapshot = persisted.state.trace.events[-1].payload["surface_snapshot"]["surface"]
    assert snapshot["reversible_span_map_present"] is True
    assert snapshot["tokens"]
    assert snapshot["segments"]
    assert snapshot["quotes"]
    assert snapshot["normalization_log"]
