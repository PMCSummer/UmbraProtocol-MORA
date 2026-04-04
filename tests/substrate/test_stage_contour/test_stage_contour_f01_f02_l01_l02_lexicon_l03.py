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
from substrate.lexical_grounding import (
    build_lexical_grounding_hypotheses,
    persist_lexical_grounding_result_via_f01,
)
from substrate.lexicon import create_seed_lexicon_state
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def test_stage_contour_f01_f02_l01_l02_lexicon_l03_keeps_typed_path_and_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l03-lexicon-stage-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-06T00:00:00+00:00",
            event_id="ev-l03-lexicon-stage-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision

    epistemic = ground_epistemic_input(
        InputMaterial(material_id="m-l03-lexicon-stage", content="thing bank"),
        SourceMetadata(
            source_id="user-l03-lexicon-stage",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )

    assert result.lexicon_primary_used is True
    assert result.lexicon_handoff_present is True
    assert result.lexicon_query_attempted is True
    assert result.lexicon_usable_basis_present is True
    assert result.lexicon_backed_mentions_count >= 1
    assert result.bundle.lexical_basis_records
    assert boot.state.runtime.revision == start_revision

    persisted = persist_lexical_grounding_result_via_f01(
        result=result,
        runtime_state=boot.state,
        transition_id="tr-l03-lexicon-stage-persist",
        requested_at="2026-04-06T00:05:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["lexical_grounding_snapshot"]
    assert snapshot["bundle"]["lexical_basis_records"]
    assert snapshot["bundle"]["lexicon_primary_used"] is True
    assert snapshot["bundle"]["lexicon_handoff_present"] is True
    assert snapshot["bundle"]["lexicon_query_attempted"] is True
    assert snapshot["bundle"]["lexicon_usable_basis_present"] is True
    assert snapshot["bundle"]["lexicon_backed_mentions_count"] >= 1
