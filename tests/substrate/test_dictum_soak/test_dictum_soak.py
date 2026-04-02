from substrate.dictum_candidates import (
    build_dictum_candidates,
    persist_dictum_result_via_f01,
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
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l04-soak-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T01:00:00+00:00",
            event_id="ev-l04-soak-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _dictum_result(text: str, material_id: str, context: LexicalDiscourseContext):
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
        discourse_context=context,
    )
    return build_dictum_candidates(
        lexical,
        syntax,
        utterance_surface=surface,
        discourse_context=context,
    )


def test_soak_replay_lite_keeps_uncertainty_and_bounded_growth() -> None:
    runtime = _bootstrapped_state()
    sequence = (
        ("we track alpha", LexicalDiscourseContext(context_ref="ctx:l04-soak-1")),
        ("he tracks alpha", LexicalDiscourseContext(context_ref="ctx:l04-soak-2", entity_bindings=(("he", "entity:alpha"),))),
        ("he qzxv", LexicalDiscourseContext(context_ref="ctx:l04-soak-3")),
        ('"alpha" moved', LexicalDiscourseContext(context_ref="ctx:l04-soak-4")),
        ("we do not track alpha beta", LexicalDiscourseContext(context_ref="ctx:l04-soak-5")),
        ("do this now", LexicalDiscourseContext(context_ref="ctx:l04-soak-6")),
    )

    unknown_steps = 0
    underspecified_steps = 0
    conflict_steps = 0

    for index, (text, context) in enumerate(sequence, start=1):
        result = _dictum_result(text, f"m-l04-soak-{index}", context)
        if result.bundle.unknowns:
            unknown_steps += 1
        if any(candidate.underspecified_slots for candidate in result.bundle.dictum_candidates):
            underspecified_steps += 1
        if result.bundle.conflicts:
            conflict_steps += 1

        assert result.no_final_resolution_performed is True
        for candidate in result.bundle.dictum_candidates:
            assert len(candidate.argument_slots) <= 4
            assert len(candidate.underspecified_slots) <= 5

        persisted = persist_dictum_result_via_f01(
            result=result,
            runtime_state=runtime,
            transition_id=f"tr-l04-soak-{index}",
            requested_at=f"2026-04-04T01:{10 + index:02d}:00+00:00",
        )
        assert persisted.accepted is True
        runtime = persisted.state
        snapshot = runtime.trace.events[-1].payload["dictum_snapshot"]
        assert snapshot["bundle"]["dictum_candidates"] is not None
        assert snapshot["bundle"]["no_final_resolution_performed"] is True

    assert unknown_steps > 0
    assert underspecified_steps > 0
    assert conflict_steps >= 0
