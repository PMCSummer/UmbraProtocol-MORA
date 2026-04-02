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
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
    persist_lexical_grounding_result_via_f01,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l03-soak-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-03T00:00:00+00:00",
            event_id="ev-l03-soak-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _l03_result(text: str, *, material_id: str, context: LexicalDiscourseContext | None = None):
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
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    return build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=context,
    )


def test_soak_replay_lite_preserves_uncertainty_and_bounded_growth() -> None:
    runtime_state = _bootstrapped_state()
    sequence = (
        ("alpha arrived", LexicalDiscourseContext(context_ref="ctx:soak-1")),
        ("he arrived", LexicalDiscourseContext(context_ref="ctx:soak-2", entity_bindings=(("he", "entity:alpha"),))),
        ("qzxv here", LexicalDiscourseContext(context_ref="ctx:soak-3")),
        ("bank bank", LexicalDiscourseContext(context_ref="ctx:soak-4")),
        ("it moved", LexicalDiscourseContext(context_ref="ctx:soak-5")),
        ("здесь сейчас это", LexicalDiscourseContext(context_ref="ctx:soak-6")),
        ("alpha he", LexicalDiscourseContext(context_ref="ctx:soak-7", entity_bindings=(("alpha", "entity:alpha"),))),
        ("qzxv nrmpt he", LexicalDiscourseContext(context_ref="ctx:soak-8")),
    )

    unknown_steps = 0
    conflict_steps = 0
    unresolved_steps = 0
    revision = runtime_state.runtime.revision

    for index, (text, context) in enumerate(sequence, start=1):
        result = _l03_result(text, material_id=f"m-l03-soak-{index}", context=context)
        mention_count = len(result.bundle.mention_anchors)
        candidate_count = len(result.bundle.lexeme_candidates)

        if result.bundle.unknown_states:
            unknown_steps += 1
        if result.bundle.conflicts:
            conflict_steps += 1
        if any(hypothesis.unresolved for hypothesis in result.bundle.reference_hypotheses):
            unresolved_steps += 1

        assert result.bundle.no_final_resolution_performed is True
        assert result.no_final_resolution_performed is True
        if mention_count > 0:
            assert candidate_count <= mention_count * 5

        persisted = persist_lexical_grounding_result_via_f01(
            result=result,
            runtime_state=runtime_state,
            transition_id=f"tr-l03-soak-{index}",
            requested_at=f"2026-04-03T00:{10 + index:02d}:00+00:00",
        )
        assert persisted.accepted is True
        runtime_state = persisted.state
        revision += 1
        assert runtime_state.runtime.revision == revision
        snapshot = runtime_state.trace.events[-1].payload["lexical_grounding_snapshot"]
        assert snapshot["bundle"]["no_final_resolution_performed"] is True
        assert snapshot["bundle"]["mention_anchors"] is not None
        assert snapshot["telemetry"]["generated_candidate_ids"] is not None

    assert unknown_steps > 0
    assert conflict_steps > 0
    assert unresolved_steps > 0
