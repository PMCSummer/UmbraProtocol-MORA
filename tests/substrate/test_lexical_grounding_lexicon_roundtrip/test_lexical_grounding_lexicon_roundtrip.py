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
    lexical_grounding_result_to_payload,
    persist_lexical_grounding_result_via_f01,
)
from substrate.lexicon import create_seed_lexicon_state
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l03-lexicon-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-06T00:00:00+00:00",
            event_id="ev-l03-lexicon-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _syntax_result(text: str, material_id: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    return build_morphosyntax_candidate_space(surface_result), surface_result


def _basis_signature(payload: dict[str, object]) -> tuple[tuple[str, str, bool], ...]:
    bundle = payload["bundle"]
    return tuple(
        (
            record["mention_id"],
            record["basis_class"],
            bool(record["heuristic_fallback_used"]),
        )
        for record in bundle["lexical_basis_records"]
    )


def test_roundtrip_preserves_lexicon_backed_vs_fallback_basis_markers() -> None:
    syntax_result, surface_result = _syntax_result(
        "thing bank",
        "m-l03-lexicon-roundtrip",
    )
    result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        lexicon_state=create_seed_lexicon_state(),
    )
    payload = lexical_grounding_result_to_payload(result)
    assert payload["bundle"]["lexical_basis_records"]
    assert payload["bundle"]["lexicon_primary_used"] is True
    assert payload["bundle"]["lexicon_handoff_present"] is True
    assert payload["bundle"]["lexicon_query_attempted"] is True
    assert payload["bundle"]["lexicon_usable_basis_present"] is True
    assert payload["bundle"]["lexicon_backed_mentions_count"] >= 1
    assert payload["bundle"]["heuristic_fallback_used"] is True
    assert payload["bundle"]["fallback_reasons"]
    assert payload["telemetry"]["lexicon_query_attempted"] is True
    assert payload["telemetry"]["lexicon_usable_basis_present"] is True
    assert payload["telemetry"]["lexicon_backed_mentions_count"] >= 1
    assert payload["telemetry"]["lexicon_backed_mention_count"] >= 1
    assert payload["telemetry"]["heuristic_fallback_mention_count"] >= 1

    runtime = _bootstrapped_state()
    persisted = persist_lexical_grounding_result_via_f01(
        result=result,
        runtime_state=runtime,
        transition_id="tr-l03-lexicon-roundtrip-persist",
        requested_at="2026-04-06T00:05:00+00:00",
    )
    snapshot = persisted.state.trace.events[-1].payload["lexical_grounding_snapshot"]

    assert _basis_signature(snapshot) == _basis_signature(payload)
    assert snapshot["bundle"]["lexicon_query_attempted"] is True
    assert snapshot["bundle"]["lexicon_usable_basis_present"] is True
    assert snapshot["bundle"]["no_strong_lexical_claim_from_fallback"] is True
