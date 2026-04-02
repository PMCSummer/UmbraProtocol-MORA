from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEpisodeRecordContext,
    LexicalEpisodeStatus,
    LexicalHypothesisStatus,
    LexicalSenseHypothesis,
    LexicalUsageEpisode,
    consolidate_lexical_hypotheses,
    create_empty_lexicon_state,
    lexicon_result_to_payload,
    persist_lexical_learning_result_via_f01,
    record_lexical_usage_episode,
    reconstruct_lexicon_state_from_snapshot,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _boot_runtime():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-lex-ep-round-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-04T00:00:00+00:00",
            event_id="ev-lex-ep-round-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _episode(episode_id: str) -> LexicalUsageEpisode:
    return LexicalUsageEpisode(
        episode_id=episode_id,
        observed_surface_form="epis",
        observed_lemma_hint="epis",
        language_code="en",
        observed_context_keys=("turn",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.epis",
                sense_label="epis_entity",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.7,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span="epis use",
        confidence=0.7,
        evidence_quality=0.72,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )


def test_episode_learning_roundtrip_preserves_support_and_continue_equivalence() -> None:
    first = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-r1"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2),
    )
    runtime = _boot_runtime()
    persisted = persist_lexical_learning_result_via_f01(
        result=first,
        runtime_state=runtime,
        transition_id="tr-lex-ep-round-1",
        requested_at="2026-04-04T00:01:00+00:00",
    )
    snapshot = persisted.state.trace.events[-1].payload["lexicon_learning_snapshot"]
    reconstructed = reconstruct_lexicon_state_from_snapshot(snapshot)
    assert reconstructed.usage_episodes
    assert reconstructed.provisional_hypotheses
    assert reconstructed.provisional_hypotheses[0].support_count == 1

    uninterrupted = record_lexical_usage_episode(
        lexicon_state=first.updated_state,
        episodes=(_episode("ep-r2"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2),
    )
    continued = record_lexical_usage_episode(
        lexicon_state=reconstructed,
        episodes=(_episode("ep-r2"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2),
    )
    u_h = uninterrupted.updated_state.provisional_hypotheses[0]
    c_h = continued.updated_state.provisional_hypotheses[0]
    assert (u_h.support_count, u_h.status, u_h.promotion_eligibility) == (
        c_h.support_count,
        c_h.status,
        c_h.promotion_eligibility,
    )
    payload = lexicon_result_to_payload(continued)
    assert payload["state"]["usage_episodes"]
    assert payload["state"]["provisional_hypotheses"]
    assert "candidate_role_hints" in payload["state"]["provisional_hypotheses"][0]
    assert "schema_version" in payload["state"]["provisional_hypotheses"][0]


def test_conflicted_hypothesis_roundtrip_continue_preserves_frozen_learning_state() -> None:
    first = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-fz-1"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, freeze_on_conflict=True),
    )
    conflict_episode = LexicalUsageEpisode(
        episode_id="ep-fz-2",
        observed_surface_form="epis",
        observed_lemma_hint="epis",
        language_code="en",
        observed_context_keys=("turn",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.epis",
                sense_label="epis_conflict",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                compatibility_cues=("cue_conflict_target",),
                anti_cues=("cue_a",),
                confidence=0.72,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span="epis conflict",
        confidence=0.72,
        evidence_quality=0.72,
        step_index=2,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
    )
    second = record_lexical_usage_episode(
        lexicon_state=first.updated_state,
        episodes=(conflict_episode,),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, freeze_on_conflict=True),
    )
    hypothesis = second.updated_state.provisional_hypotheses[0]
    assert hypothesis.status in {LexicalHypothesisStatus.FROZEN, LexicalHypothesisStatus.CONFLICTED}

    runtime = _boot_runtime()
    persisted = persist_lexical_learning_result_via_f01(
        result=second,
        runtime_state=runtime,
        transition_id="tr-lex-ep-round-frozen",
        requested_at="2026-04-04T00:03:00+00:00",
    )
    reconstructed = reconstruct_lexicon_state_from_snapshot(
        persisted.state.trace.events[-1].payload["lexicon_learning_snapshot"]
    )
    continued = record_lexical_usage_episode(
        lexicon_state=reconstructed,
        episodes=(_episode("ep-fz-3"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, freeze_on_conflict=True),
    )
    continued_hypothesis = continued.updated_state.provisional_hypotheses[0]
    assert continued_hypothesis.status in {LexicalHypothesisStatus.FROZEN, LexicalHypothesisStatus.CONFLICTED}
    assert "ep-fz-3" in continued.blocked_episode_ids


def test_roundtrip_hypothesis_version_mismatch_is_capped_on_continue() -> None:
    recorded = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-vr-1"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2),
    )
    payload = lexicon_result_to_payload(recorded)
    payload["state"]["provisional_hypotheses"][0]["schema_version"] = "lexicon.schema.v999"
    reconstructed = reconstruct_lexicon_state_from_snapshot(payload)
    consolidated = consolidate_lexical_hypotheses(lexicon_state=reconstructed)
    frozen_hypothesis = consolidated.updated_state.provisional_hypotheses[0]
    assert frozen_hypothesis.status == LexicalHypothesisStatus.FROZEN
    assert consolidated.promoted_hypothesis_ids == ()
    assert "hypothesis_schema_version_mismatch" in consolidated.telemetry.compatibility_markers

    continued = record_lexical_usage_episode(
        lexicon_state=consolidated.updated_state,
        episodes=(_episode("ep-vr-2"),),
    )
    assert "ep-vr-2" in continued.blocked_episode_ids
