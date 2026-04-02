import json

from substrate.contracts import TransitionKind, TransitionRequest, WriterIdentity
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.language_surface import (
    build_utterance_surface,
    persist_surface_result_via_f01,
    surface_result_to_payload,
)
from substrate.state import create_empty_state
from substrate.transition import execute_transition


def _surface(text: str):
    unit = ground_epistemic_input(
        InputMaterial(material_id=f"m-{abs(hash(text))}", content=text),
        SourceMetadata(
            source_id="roundtrip-user",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    ).unit
    return build_utterance_surface(unit)


def _contract_projection(payload: dict[str, object]) -> dict[str, object]:
    surface = payload["surface"]
    def _as_tuple(value):
        if isinstance(value, list):
            return tuple(_as_tuple(x) for x in value)
        if isinstance(value, tuple):
            return tuple(_as_tuple(x) for x in value)
        return value

    token_spans = tuple((tuple(token["span"]), token["raw_text"], token["token_kind"]) for token in surface["tokens"])
    segment_spans = tuple(
        (
            tuple(segment["span"]),
            segment["segment_kind"],
            tuple(tuple(token["span"]) for token in surface["tokens"] if token["token_id"] in set(_as_tuple(segment["token_ids"]))),
        )
        for segment in surface["segments"]
    )
    return {
        "raw_text": surface["raw_text"],
        "reversible_span_map_present": surface["reversible_span_map_present"],
        "tokens": token_spans,
        "segments": segment_spans,
        "quotes": tuple((tuple(quote["span"]), quote["quote_kind"]) for quote in surface["quotes"]),
        "insertions": tuple(
            (tuple(insertion["span"]), insertion["insertion_kind"]) for insertion in surface["insertions"]
        ),
        "ambiguities": tuple(
            (
                ambiguity["ambiguity_kind"],
                tuple(ambiguity["span"]),
                bool(ambiguity["alternatives_ref"]),
            )
            for ambiguity in surface["ambiguities"]
        ),
        "normalization": tuple(
            (record["op_name"], record["input_span_ref"], record["reversible"])
            for record in surface["normalization_log"]
        ),
    }


def test_repeated_runs_are_contract_equivalent_for_same_input() -> None:
    first = surface_result_to_payload(_surface('"blarf... zint", — сказал user'))
    second = surface_result_to_payload(_surface('"blarf... zint", — сказал user'))
    assert _contract_projection(first) == _contract_projection(second)


def test_surface_payload_roundtrip_serialization_preserves_contract_state() -> None:
    payload = surface_result_to_payload(_surface("(вставка) `code-like` blarf... zint"))
    restored = json.loads(json.dumps(payload, ensure_ascii=False))
    assert _contract_projection(payload) == _contract_projection(restored)


def test_persistence_via_f01_keeps_load_bearing_surface_state() -> None:
    boot = execute_transition(
        TransitionRequest(
            transition_id="tr-l01-hardening-boot",
            transition_kind=TransitionKind.BOOTSTRAP_INIT,
            writer=WriterIdentity.BOOTSTRAPPER,
            cause_chain=("bootstrap",),
            requested_at="2026-04-02T01:00:00+00:00",
            event_id="ev-l01-hardening-boot",
            event_payload={"schema_version": "f01"},
        ),
        create_empty_state(),
    )
    result = _surface('"blarf... zint", — сказал user')
    persisted = persist_surface_result_via_f01(
        result=result,
        runtime_state=boot.state,
        transition_id="tr-l01-hardening-persist",
        requested_at="2026-04-02T01:05:00+00:00",
    )

    snapshot = persisted.state.trace.events[-1].payload["surface_snapshot"]["surface"]
    assert snapshot["reversible_span_map_present"] is True
    assert snapshot["normalization_log"]
    assert snapshot["ambiguities"]
    assert snapshot["quotes"]
    assert snapshot["insertions"]
