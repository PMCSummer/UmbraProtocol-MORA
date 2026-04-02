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
)
from substrate.lexicon import create_seed_lexicon_state
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _run_language_contour(text: str, material_id: str, *, with_lexicon: bool):
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


def test_stage_contour_mixed_human_like_input_preserves_boundedness() -> None:
    lexical, dictum = _run_language_contour(
        "we saw bank qzxv yesterday",
        "m-stage-lexicon-l03-l04-mixed",
        with_lexicon=True,
    )

    assert lexical.lexicon_primary_used is True
    assert any(
        basis.basis_class.value == "lexicon_backed"
        for basis in lexical.bundle.lexical_basis_records
    )
    assert any(
        basis.basis_class.value in {"lexicon_capped_unknown", "no_usable_lexical_basis"}
        for basis in lexical.bundle.lexical_basis_records
    )
    assert lexical.bundle.unknown_states

    assert dictum.bundle.no_final_resolution_performed is True
    assert dictum.telemetry.input_lexical_basis_classes
    assert dictum.telemetry.fallback_basis_present is True
    assert dictum.telemetry.lexicon_basis_missing_or_capped is True
    assert "no_final_resolution_performed" in dictum.telemetry.downstream_gate.restrictions


def test_stage_contour_lexicon_ablation_is_measurably_degraded() -> None:
    with_lexicon_l03, with_lexicon_l04 = _run_language_contour(
        "thing",
        "m-stage-lexicon-l03-l04-with",
        with_lexicon=True,
    )
    without_lexicon_l03, without_lexicon_l04 = _run_language_contour(
        "thing",
        "m-stage-lexicon-l03-l04-without",
        with_lexicon=False,
    )

    with_gate = evaluate_lexical_grounding_downstream_gate(with_lexicon_l03)
    without_gate = evaluate_lexical_grounding_downstream_gate(without_lexicon_l03)

    assert with_lexicon_l03.lexicon_handoff_missing is False
    assert without_lexicon_l03.lexicon_handoff_missing is True
    assert with_lexicon_l03.no_strong_lexical_claim_without_lexicon is False
    assert without_lexicon_l03.no_strong_lexical_claim_without_lexicon is True
    assert "lexicon_handoff_missing" not in with_gate.restrictions
    assert "lexicon_handoff_missing" in without_gate.restrictions

    assert with_lexicon_l04.telemetry.lexicon_handoff_missing_upstream is False
    assert without_lexicon_l04.telemetry.lexicon_handoff_missing_upstream is True
    assert (
        "no_strong_lexical_basis_from_upstream"
        not in with_lexicon_l04.telemetry.downstream_gate.restrictions
    )
    assert (
        "no_strong_lexical_basis_from_upstream"
        in without_lexicon_l04.telemetry.downstream_gate.restrictions
    )
    assert with_lexicon_l04.telemetry.input_lexical_basis_classes != (
        without_lexicon_l04.telemetry.input_lexical_basis_classes
    )


def test_stage_contour_l04_snapshot_keeps_l03_basis_bridge() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-lexicon-l03-l04-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-09T00:00:00+00:00",
            event_id="ev-stage-lexicon-l03-l04-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True

    _, dictum = _run_language_contour(
        "thing",
        "m-stage-lexicon-l03-l04-snapshot",
        with_lexicon=False,
    )

    persisted = persist_dictum_result_via_f01(
        result=dictum,
        runtime_state=boot.state,
        transition_id="tr-stage-lexicon-l03-l04-persist",
        requested_at="2026-04-09T00:01:00+00:00",
    )
    assert persisted.accepted is True

    snapshot = persisted.state.trace.events[-1].payload["dictum_snapshot"]
    assert snapshot["bundle"]["lexicon_handoff_missing_upstream"] is True
    assert snapshot["bundle"]["no_strong_lexical_basis_from_upstream"] is True
    assert snapshot["telemetry"]["lexicon_handoff_missing_upstream"] is True
    assert snapshot["telemetry"]["no_strong_lexical_basis_from_upstream"] is True
