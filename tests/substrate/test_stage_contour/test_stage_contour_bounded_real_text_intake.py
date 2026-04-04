from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.dictum_candidates import build_dictum_candidates, persist_dictum_result_via_f01
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
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
    evaluate_lexical_grounding_downstream_gate,
    persist_lexical_grounding_result_via_f01,
)
from substrate.lexicon import create_seed_lexicon_state
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _run_contour(text: str, material_id: str, *, with_lexicon: bool):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(
        syntax,
        utterance_surface=surface,
        discourse_context=LexicalDiscourseContext(context_ref=f"ctx:{material_id}"),
        lexicon_state=create_seed_lexicon_state() if with_lexicon else None,
    )
    dictum = build_dictum_candidates(
        lexical,
        syntax,
        utterance_surface=surface,
        discourse_context=LexicalDiscourseContext(context_ref=f"ctx:{material_id}"),
    )
    return lexical, dictum


def test_real_text_intake_with_lexicon_handoff_stays_bounded_and_observable() -> None:
    lexical, dictum = _run_contour(
        "we saw thing and qzxv near bank yesterday",
        "m-real-text-with-lexicon",
        with_lexicon=True,
    )
    gate = evaluate_lexical_grounding_downstream_gate(lexical)

    assert lexical.lexicon_handoff_present is True
    assert lexical.lexicon_query_attempted is True
    assert lexical.lexicon_usable_basis_present is True
    assert lexical.lexicon_backed_mentions_count >= 1
    assert lexical.bundle.lexicon_primary_used is True
    assert any(
        basis.basis_class.value == "lexicon_backed"
        for basis in lexical.bundle.lexical_basis_records
    )
    assert any(
        basis.basis_class.value in {"lexicon_capped_unknown", "no_usable_lexical_basis"}
        for basis in lexical.bundle.lexical_basis_records
    )
    assert lexical.bundle.unknown_states
    assert lexical.bundle.heuristic_fallback_used is True
    assert lexical.bundle.no_final_resolution_performed is True
    assert "lexicon_query_attempted" in gate.restrictions
    assert "lexicon_usable_basis_present" in gate.restrictions
    assert "heuristic_fallback_used" in gate.restrictions
    assert "no_strong_lexical_claim_from_fallback" in gate.restrictions

    assert dictum.bundle.no_final_resolution_performed is True
    assert dictum.telemetry.input_lexical_basis_classes
    assert dictum.telemetry.lexicon_handoff_present_upstream is True
    assert dictum.telemetry.lexicon_query_attempted_upstream is True
    assert dictum.telemetry.lexicon_usable_basis_present_upstream is True
    assert dictum.telemetry.lexicon_backed_mentions_count_upstream >= 1
    assert dictum.telemetry.lexicon_handoff_missing_upstream is False
    assert "no_final_resolution_performed" in dictum.telemetry.downstream_gate.restrictions
    assert "no_strong_lexical_basis_from_upstream" in dictum.telemetry.downstream_gate.restrictions


def test_real_text_intake_without_lexicon_handoff_enters_explicit_degraded_mode() -> None:
    lexical, dictum = _run_contour(
        "we saw thing and qzxv near bank yesterday",
        "m-real-text-without-lexicon",
        with_lexicon=False,
    )
    gate = evaluate_lexical_grounding_downstream_gate(lexical)

    assert lexical.lexicon_handoff_present is False
    assert lexical.lexicon_query_attempted is False
    assert lexical.lexicon_usable_basis_present is False
    assert lexical.lexicon_backed_mentions_count == 0
    assert lexical.lexicon_handoff_missing is True
    assert lexical.lexical_basis_degraded is True
    assert lexical.no_strong_lexical_claim_without_lexicon is True
    assert "lexicon_handoff_missing" in gate.restrictions
    assert "no_strong_lexical_claim_without_lexicon" in gate.restrictions
    assert "lexicon_query_attempted" not in gate.restrictions

    assert dictum.bundle.no_final_resolution_performed is True
    assert dictum.telemetry.lexicon_handoff_missing_upstream is True
    assert dictum.telemetry.lexicon_handoff_present_upstream is False
    assert dictum.telemetry.lexicon_query_attempted_upstream is False
    assert dictum.telemetry.lexicon_usable_basis_present_upstream is False
    assert dictum.telemetry.lexicon_backed_mentions_count_upstream == 0
    assert "lexicon_handoff_missing_upstream" in dictum.telemetry.downstream_gate.restrictions
    assert "no_strong_lexical_basis_from_upstream" in dictum.telemetry.downstream_gate.restrictions


def test_real_text_intake_snapshot_preserves_degraded_lexical_provenance() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-real-text-intake-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-10T00:00:00+00:00",
            event_id="ev-real-text-intake-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True

    lexical, dictum = _run_contour(
        "we saw thing and qzxv near bank yesterday",
        "m-real-text-snapshot",
        with_lexicon=False,
    )

    persisted_lexical = persist_lexical_grounding_result_via_f01(
        result=lexical,
        runtime_state=boot.state,
        transition_id="tr-real-text-intake-lexical-persist",
        requested_at="2026-04-10T00:01:00+00:00",
    )
    assert persisted_lexical.accepted is True
    lexical_snapshot = persisted_lexical.state.trace.events[-1].payload["lexical_grounding_snapshot"]
    assert lexical_snapshot["bundle"]["lexicon_handoff_present"] is False
    assert lexical_snapshot["bundle"]["lexicon_query_attempted"] is False
    assert lexical_snapshot["bundle"]["lexicon_usable_basis_present"] is False
    assert lexical_snapshot["bundle"]["lexicon_backed_mentions_count"] == 0
    assert lexical_snapshot["telemetry"]["lexicon_query_attempted"] is False
    assert lexical_snapshot["telemetry"]["lexicon_usable_basis_present"] is False

    persisted_dictum = persist_dictum_result_via_f01(
        result=dictum,
        runtime_state=persisted_lexical.state,
        transition_id="tr-real-text-intake-dictum-persist",
        requested_at="2026-04-10T00:02:00+00:00",
    )
    assert persisted_dictum.accepted is True
    dictum_snapshot = persisted_dictum.state.trace.events[-1].payload["dictum_snapshot"]
    assert dictum_snapshot["bundle"]["lexicon_handoff_missing_upstream"] is True
    assert dictum_snapshot["bundle"]["lexicon_handoff_present_upstream"] is False
    assert dictum_snapshot["bundle"]["lexicon_query_attempted_upstream"] is False
    assert dictum_snapshot["bundle"]["lexicon_usable_basis_present_upstream"] is False
    assert dictum_snapshot["bundle"]["lexicon_backed_mentions_count_upstream"] == 0
    assert dictum_snapshot["telemetry"]["lexicon_query_attempted_upstream"] is False
    assert dictum_snapshot["telemetry"]["lexicon_usable_basis_present_upstream"] is False
