from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import build_utterance_surface, persist_surface_result_via_f01
from substrate.morphosyntax import (
    AgreementStatus,
    build_morphosyntax_candidate_space,
    persist_syntax_result_via_f01,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-contour-lang-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T00:00:00+00:00",
            event_id="ev-contour-lang-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _surface(text: str, mid: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=mid, content=text),
        SourceMetadata(
            source_id=f"user-{mid}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    return build_utterance_surface(epistemic.unit)


def test_language_contour_replay_preserves_surface_and_syntax_uncertainty() -> None:
    punctuation_plain = build_morphosyntax_candidate_space(_surface("alpha beta gamma", "m-lang-a"))
    punctuation_marked = build_morphosyntax_candidate_space(_surface("alpha beta; gamma delta.", "m-lang-b"))
    assert punctuation_marked.telemetry.clause_count >= punctuation_plain.telemetry.clause_count

    quote = _surface('"alpha beta"', "m-lang-quote")
    plain = _surface("alpha beta", "m-lang-plain")
    assert quote.surface.quotes
    assert not plain.surface.quotes

    noisy = _surface("!!! ... ?? \"unterminated", "m-lang-noisy")
    assert noisy.surface.ambiguities
    assert noisy.partial_known is True

    unmatched = build_morphosyntax_candidate_space(_surface("we do not track alpha beta", "m-lang-neg"))
    unresolved = unmatched.hypothesis_set.hypotheses[0].unresolved_attachments
    assert any(item.relation_hint == "negation_scope_ambiguous" for item in unresolved)
    assert unmatched.telemetry.negation_carrier_count > 0

    agreement_ok = build_morphosyntax_candidate_space(_surface("we are ready.", "m-lang-agr-ok"))
    agreement_bad = build_morphosyntax_candidate_space(_surface("we is ready.", "m-lang-agr-bad"))
    ok_statuses = {cue.status for cue in agreement_ok.hypothesis_set.hypotheses[0].agreement_cues}
    bad_statuses = {cue.status for cue in agreement_bad.hypothesis_set.hypotheses[0].agreement_cues}
    assert AgreementStatus.CONFLICT not in ok_statuses
    assert AgreementStatus.CONFLICT in bad_statuses

    ambiguous = build_morphosyntax_candidate_space(_surface("alpha beta ... gamma delta", "m-lang-amb"))
    assert ambiguous.hypothesis_set.no_selected_winner is True
    assert ambiguous.hypothesis_set.ambiguity_present is True
    assert len(ambiguous.hypothesis_set.hypotheses) > 1 or any(
        hypothesis.unresolved_attachments for hypothesis in ambiguous.hypothesis_set.hypotheses
    )

    assert not hasattr(ambiguous.hypothesis_set, "dictum")
    assert not hasattr(ambiguous.hypothesis_set, "illocution")


def test_language_contour_persistence_keeps_load_bearing_fields() -> None:
    runtime = _bootstrapped_state()
    surface_result = _surface('("alpha") we do not track beta ... gamma', "m-lang-persist")
    syntax_result = build_morphosyntax_candidate_space(surface_result)

    persisted_surface = persist_surface_result_via_f01(
        result=surface_result,
        runtime_state=runtime,
        transition_id="tr-contour-lang-surface",
        requested_at="2026-04-02T00:06:00+00:00",
    )
    persisted_syntax = persist_syntax_result_via_f01(
        result=syntax_result,
        runtime_state=persisted_surface.state,
        transition_id="tr-contour-lang-syntax",
        requested_at="2026-04-02T00:07:00+00:00",
    )

    assert persisted_surface.accepted is True
    assert persisted_syntax.accepted is True

    surface_snapshot = persisted_surface.state.trace.events[-1].payload["surface_snapshot"]
    syntax_snapshot = persisted_syntax.state.trace.events[-1].payload["syntax_snapshot"]

    assert surface_snapshot["surface"]["reversible_span_map_present"] is True
    assert surface_snapshot["surface"]["quotes"]
    assert surface_snapshot["surface"]["insertions"]
    assert surface_snapshot["surface"]["ambiguities"]
    assert surface_snapshot["surface"]["normalization_log"]

    first_hypothesis = syntax_snapshot["hypothesis_set"]["hypotheses"][0]
    assert syntax_snapshot["hypothesis_set"]["no_selected_winner"] is True
    assert first_hypothesis["clause_graph"]["clauses"]
    assert first_hypothesis["token_features"]
    assert first_hypothesis["edges"]
    assert first_hypothesis["unresolved_attachments"]
    assert syntax_snapshot["telemetry"]["negation_carrier_count"] >= 0
