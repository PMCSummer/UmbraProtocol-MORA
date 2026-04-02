from dataclasses import fields, replace

import pytest

from substrate.lexicon import (
    LexicalAcquisitionMode,
    LexicalCoarseSemanticType,
    LexicalCompositionRole,
    LexicalEntryProposal,
    LexicalEpisodeRecordContext,
    LexicalEpisodeRecordResult,
    LexicalEpisodeStatus,
    LexicalHypothesisConsolidationContext,
    LexicalHypothesisUpdateResult,
    LexicalSenseHypothesis,
    LexicalUsageEpisode,
    create_or_update_lexicon_state,
    create_empty_lexicon_state,
    consolidate_lexical_hypotheses,
    record_lexical_usage_episode,
)


def test_episode_learning_typed_only_input_rejected() -> None:
    with pytest.raises(TypeError):
        record_lexical_usage_episode(lexicon_state=create_empty_lexicon_state(), episodes=("raw",))
    with pytest.raises(TypeError):
        consolidate_lexical_hypotheses(lexicon_state="raw")


def test_episode_learning_compatibility_guard_blocks_honestly() -> None:
    result = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(),
        context=LexicalEpisodeRecordContext(expected_schema_version="lexicon.schema.v999"),
    )
    assert result.abstain is True
    assert result.downstream_gate.accepted is False
    assert "compatibility_mismatch" in result.downstream_gate.restrictions
    assert "schema_version_mismatch" in result.telemetry.compatibility_markers


def test_episode_models_do_not_claim_parser_or_dictum_layers() -> None:
    forbidden = {"dictum", "proposition", "illocution", "commitment", "world_truth", "final_referent"}
    record_fields = {field_info.name for field_info in fields(LexicalEpisodeRecordResult)}
    update_fields = {field_info.name for field_info in fields(LexicalHypothesisUpdateResult)}
    assert forbidden.isdisjoint(record_fields)
    assert forbidden.isdisjoint(update_fields)


def test_consolidate_respects_typed_context() -> None:
    with pytest.raises(TypeError):
        consolidate_lexical_hypotheses(
            lexicon_state=create_empty_lexicon_state(),
            context="raw",
        )
    result = consolidate_lexical_hypotheses(
        lexicon_state=create_empty_lexicon_state(),
        context=LexicalHypothesisConsolidationContext(),
    )
    assert result.no_final_meaning_resolution_performed is True


def _episode(
    episode_id: str,
    *,
    surface: str = "boundword",
    schema_version: str = "lexicon.schema.v1",
    lexicon_version: str = "lexicon.seed.v1",
    taxonomy_version: str = "lexicon.taxonomy.v1",
) -> LexicalUsageEpisode:
    return LexicalUsageEpisode(
        episode_id=episode_id,
        observed_surface_form=surface,
        observed_lemma_hint=surface,
        language_code="en",
        observed_context_keys=("ctx",),
        source_kind="test",
        proposed_sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family=f"entity.{surface}",
                sense_label=f"{surface}_sense",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.75,
            ),
        ),
        proposed_role_hints=(LexicalCompositionRole.PARTICIPANT,),
        usage_span=f"{surface} usage",
        confidence=0.75,
        evidence_quality=0.75,
        step_index=1,
        episode_status=LexicalEpisodeStatus.RECORDED,
        provenance="test.episode",
        schema_version=schema_version,
        lexicon_version=lexicon_version,
        taxonomy_version=taxonomy_version,
    )


def test_episode_payload_version_mismatch_is_runtime_block_not_soft_marker() -> None:
    blocked = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(
            _episode(
                "ep-vm-1",
                schema_version="lexicon.schema.v999",
            ),
        ),
    )
    assert blocked.recorded_episode_ids == ()
    assert blocked.blocked_episode_ids == ("ep-vm-1",)
    assert blocked.updated_state.provisional_hypotheses == ()
    assert blocked.updated_state.usage_episodes[-1].episode_status == LexicalEpisodeStatus.BLOCKED
    assert "episode_schema_version_mismatch" in blocked.telemetry.compatibility_markers


def test_hypothesis_version_mismatch_is_frozen_and_not_promoted() -> None:
    recorded = record_lexical_usage_episode(
        lexicon_state=create_empty_lexicon_state(),
        episodes=(_episode("ep-vm-2"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.6),
    )
    hypothesis = recorded.updated_state.provisional_hypotheses[0]
    mismatched_state = replace(
        recorded.updated_state,
        provisional_hypotheses=(
            replace(hypothesis, schema_version="lexicon.schema.v999"),
        ),
    )
    consolidated = consolidate_lexical_hypotheses(lexicon_state=mismatched_state)
    updated_hypothesis = consolidated.updated_state.provisional_hypotheses[0]
    assert consolidated.promoted_hypothesis_ids == ()
    assert updated_hypothesis.promotion_eligibility is False
    assert updated_hypothesis.status.value == "frozen"
    assert "hypothesis_schema_version_mismatch" in consolidated.telemetry.compatibility_markers


def test_direct_update_and_episode_promotion_are_not_confused_in_acquisition_origin() -> None:
    direct = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(
            LexicalEntryProposal(
                surface_form="manual_word",
                canonical_form="manual_word",
                language_code="en",
                part_of_speech_candidates=("noun",),
                sense_hypotheses=(
                    LexicalSenseHypothesis(
                        sense_family="entity.manual_word",
                        sense_label="manual_word_sense",
                        coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                    ),
                ),
                confidence=0.7,
                evidence_ref="manual.curation",
            ),
        ),
    )
    direct_entry = direct.updated_state.entries[0]
    assert direct_entry.acquisition_mode == LexicalAcquisitionMode.DIRECT_CURATION

    first = record_lexical_usage_episode(
        lexicon_state=direct.updated_state,
        episodes=(_episode("ep-prom-1", surface="learn_word"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.6),
    )
    second = record_lexical_usage_episode(
        lexicon_state=first.updated_state,
        episodes=(_episode("ep-prom-2", surface="learn_word"),),
        context=LexicalEpisodeRecordContext(min_support_for_promotion=2, promotion_confidence_threshold=0.6),
    )
    consolidated = consolidate_lexical_hypotheses(
        lexicon_state=second.updated_state,
        context=LexicalHypothesisConsolidationContext(min_support_for_promotion=2, promotion_confidence_threshold=0.6),
    )
    learned_entries = [entry for entry in consolidated.updated_state.entries if entry.canonical_form == "learn_word"]
    assert learned_entries
    assert any(entry.acquisition_mode == LexicalAcquisitionMode.EPISODE_PROMOTION for entry in learned_entries)
