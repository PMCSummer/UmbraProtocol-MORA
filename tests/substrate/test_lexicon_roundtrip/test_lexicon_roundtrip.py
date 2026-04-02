import json

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.lexicon import (
    LexicalCoarseSemanticType,
    LexicalEntryProposal,
    LexicalSenseHypothesis,
    LexiconQueryRequest,
    UnknownLexicalObservation,
    create_empty_lexicon_state,
    create_or_update_lexicon_state,
    lexicon_result_to_payload,
    persist_lexicon_result_via_f01,
    query_lexical_entries,
    reconstruct_lexicon_state_from_snapshot,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _bootstrapped_state():
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-lexicon-roundtrip-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-03T00:00:00+00:00",
            event_id="ev-lexicon-roundtrip-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    assert boot.accepted is True
    return boot.state


def _proposal(surface: str, ref: str) -> LexicalEntryProposal:
    return LexicalEntryProposal(
        surface_form=surface,
        canonical_form=surface,
        language_code="en",
        part_of_speech_candidates=("noun",),
        sense_hypotheses=(
            LexicalSenseHypothesis(
                sense_family="entity.roundtrip",
                sense_label=f"{surface}_sense",
                coarse_semantic_type=LexicalCoarseSemanticType.ENTITY,
                confidence=0.73,
            ),
        ),
        confidence=0.73,
        evidence_ref=ref,
    )


def _state_projection(state):
    return {
        "entries": tuple(
            (
                entry.entry_id,
                entry.canonical_form,
                entry.acquisition_state.status.value,
                entry.acquisition_state.evidence_count,
                tuple((sense.sense_family, sense.sense_label) for sense in entry.sense_records),
                entry.conflict_state.value,
            )
            for entry in sorted(state.entries, key=lambda value: value.entry_id)
        ),
        "unknown_items": tuple(
            (item.unknown_id, item.surface_form, item.no_strong_meaning_claim)
            for item in state.unknown_items
        ),
        "conflict_index": state.conflict_index,
        "frozen_updates": tuple((item.surface_form, item.reason) for item in state.frozen_updates),
        "schema": (state.schema_version, state.lexicon_version, state.taxonomy_version),
    }


def test_roundtrip_snapshot_preserves_load_bearing_lexical_state() -> None:
    result = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(_proposal("gamma", "ev-round-1"),),
    )
    payload = lexicon_result_to_payload(result)
    assert payload["state"]["entries"]
    assert payload["state"]["entries"][0]["sense_records"]
    assert payload["state"]["entries"][0]["composition_profile"]
    assert payload["state"]["entries"][0]["reference_profile"]
    assert payload["state"]["entries"][0]["acquisition_state"]
    assert payload["state"]["schema_version"]
    assert payload["telemetry"]["downstream_gate"]["restrictions"] is not None


def test_persist_reconstruct_continue_preserves_lexicon_artifacts() -> None:
    runtime = _bootstrapped_state()
    first_update = create_or_update_lexicon_state(
        lexicon_state=create_empty_lexicon_state(),
        entry_proposals=(_proposal("sigma", "ev-round-2"),),
        unknown_observations=(
            UnknownLexicalObservation(
                surface_form="qzxv",
                occurrence_ref="occ-roundtrip-unknown",
                partial_pos_hint="noun",
                confidence=0.19,
                provenance="roundtrip",
            ),
        ),
    )
    persisted_first = persist_lexicon_result_via_f01(
        result=first_update,
        runtime_state=runtime,
        transition_id="tr-lexicon-roundtrip-first",
        requested_at="2026-04-03T00:01:00+00:00",
    )
    assert persisted_first.accepted is True
    first_snapshot = persisted_first.state.trace.events[-1].payload["lexicon_snapshot"]
    reconstructed_state = reconstruct_lexicon_state_from_snapshot(first_snapshot)

    uninterrupted_continue = create_or_update_lexicon_state(
        lexicon_state=first_update.updated_state,
        entry_proposals=(_proposal("sigma", "ev-round-3"),),
    )
    reconstructed_continue = create_or_update_lexicon_state(
        lexicon_state=reconstructed_state,
        entry_proposals=(_proposal("sigma", "ev-round-3"),),
    )
    assert _state_projection(uninterrupted_continue.updated_state) == _state_projection(
        reconstructed_continue.updated_state
    )

    uninterrupted_query = query_lexical_entries(
        lexicon_state=uninterrupted_continue.updated_state,
        queries=(
            LexiconQueryRequest(surface_form="sigma", language_code="en"),
            LexiconQueryRequest(surface_form="qzxv", language_code="en"),
        ),
    )
    reconstructed_query = query_lexical_entries(
        lexicon_state=reconstructed_continue.updated_state,
        queries=(
            LexiconQueryRequest(surface_form="sigma", language_code="en"),
            LexiconQueryRequest(surface_form="qzxv", language_code="en"),
        ),
    )
    assert uninterrupted_query.query_records == reconstructed_query.query_records
    assert uninterrupted_query.downstream_gate == reconstructed_query.downstream_gate

    persisted_second = persist_lexicon_result_via_f01(
        result=reconstructed_query,
        runtime_state=persisted_first.state,
        transition_id="tr-lexicon-roundtrip-second",
        requested_at="2026-04-03T00:02:00+00:00",
    )
    second_snapshot = persisted_second.state.trace.events[-1].payload["lexicon_snapshot"]
    serialized = json.loads(json.dumps(second_snapshot))
    assert serialized["state"]["entries"]
    assert serialized["state"]["unknown_items"]
    assert serialized["telemetry"]["source_lineage"] is not None
