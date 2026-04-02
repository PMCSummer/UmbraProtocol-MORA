import pytest

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEntryProposal,
    LexicalEpisodeStatus,
    LexicalSenseHypothesis,
    LexicalUsageEpisode,
    create_empty_lexicon_state,
    create_or_update_lexicon_state,
    persist_lexical_learning_result_via_f01,
    persist_lexicon_result_via_f01,
    record_lexical_usage_episode,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _proposal() -> LexicalEntryProposal:
    return LexicalEntryProposal(
        surface_form="theta",
        canonical_form="theta",
        language_code="en",
        part_of_speech_candidates=("noun",),
        sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.theta",
                sense_label="theta_entity",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.75,
            ),
        ),
        confidence=0.75,
        evidence_ref="ev-stage-lexicon",
    )


def test_stage_contour_f01_lexicon_preserves_single_write_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-lexicon-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-03T00:00:00+00:00",
            event_id="ev-stage-lexicon-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    start_revision = boot.state.runtime.revision

    update = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(_proposal(),),
    )
    assert update.updated_state.entries
    assert boot.state.runtime.revision == start_revision

    persisted = persist_lexicon_result_via_f01(
        result=update,
        runtime_state=boot.state,
        transition_id="tr-stage-lexicon-persist",
        requested_at="2026-04-03T00:10:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == start_revision + 1
    snapshot = persisted.state.trace.events[-1].payload["lexicon_snapshot"]
    assert snapshot["state"]["entries"]
    assert snapshot["state"]["entries"][0]["sense_records"]
    assert snapshot["telemetry"]["attempted_paths"]


def test_stage_contour_lexicon_typed_only_guard() -> None:
    with pytest.raises(TypeError):
        create_or_update_lexicon_state(entry_proposals=("raw",))


def test_stage_contour_f01_lexicon_learning_persistence_seam() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-stage-lexicon-learning-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-stage-lexicon-learning-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    base_revision = boot.state.runtime.revision
    learning = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(
            LexicalUsageEpisode(
                episode_id="ep-stage-lex",
                observed_surface_form="stageword",
                observed_lemma_hint="stageword",
                language_code="en",
                observed_context_keys=("turn",),
                source_kind="test",
                proposed_sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.stageword",
                        sense_label="stageword_entity",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                        confidence=0.7,
                    ),
                ),
                proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
                usage_span="stageword usage",
                confidence=0.7,
                evidence_quality=0.72,
                step_index=1,
                episode_status=LexicalEpisodeStatus.RECORDED,
                provenance="test.stage",
            ),
        ),
    )
    assert boot.state.runtime.revision == base_revision
    persisted = persist_lexical_learning_result_via_f01(
        result=learning,
        runtime_state=boot.state,
        transition_id="tr-stage-lexicon-learning-persist",
        requested_at="2026-04-04T00:05:00+00:00",
    )
    assert persisted.accepted is True
    assert persisted.state.runtime.revision == base_revision + 1
    payload = persisted.state.trace.events[-1].payload["lexicon_learning_snapshot"]
    assert payload["state"]["usage_episodes"]
