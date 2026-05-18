from __future__ import annotations

from dataclasses import asdict, replace

from substrate.ab01_event_digest import (
    AB1CompressionQuality,
    AB1EventDigestInput,
    AB1EventDigestKind,
    build_ab1_event_digests,
)


def _input(**overrides: object) -> AB1EventDigestInput:
    base = AB1EventDigestInput(
        tick_ref="ab1:test:1",
        source_refs=("src:public:observation", "src:public:effect"),
        observation_refs=("obs:1",),
        raw_window_refs=("raw:window:1",),
        effect_refs=("effect:1",),
        residue_refs=("residue:1",),
        expected_refs=("expected:delta:1",),
        observed_refs=("observed:delta:1",),
        anomaly_markers=(),
        effect_status="observed_success",
        delayed_effect_ticks=None,
        expected_inventory_delta=None,
        observed_inventory_delta=None,
        expected_body_delta=None,
        observed_body_delta=None,
        magnitude=0.55,
        noise_level=0.1,
        compression_method="ab1_public_event_digest_v1",
        compression_quality=AB1CompressionQuality.LOSSLESS,
        prediction_error_signal=0.5,
        efference_mismatch_present=False,
        public_only=True,
        hidden_eval_excluded=True,
        scenario_label_excluded=True,
        source="tests.ab1",
    )
    return replace(base, **overrides)


def _single_digest(input_value: AB1EventDigestInput):
    result = build_ab1_event_digests(input_value)
    assert len(result.digests) == 1
    return result.digests[0]


def test_ab1_detects_public_effect_mismatch() -> None:
    digest = _single_digest(_input(expected_refs=("expected:x",), observed_refs=("observed:y",)))
    assert digest.event_kind is AB1EventDigestKind.EFFECT_MISMATCH


def test_ab1_detects_blocked_effect_without_claiming_cause() -> None:
    digest = _single_digest(_input(effect_status="blocked", observed_refs=("observed:block",)))
    assert digest.event_kind is AB1EventDigestKind.UNEXPECTED_BLOCK
    assert digest.cause_claimed is False


def test_ab1_detects_inventory_delta_mismatch_from_public_refs() -> None:
    digest = _single_digest(
        _input(
            expected_inventory_delta=1,
            observed_inventory_delta=0,
            observed_refs=("observed:inventory",),
            effect_refs=("effect:inventory",),
        )
    )
    assert digest.event_kind is AB1EventDigestKind.INVENTORY_DELTA_MISMATCH


def test_ab1_detects_delayed_effect_with_uncertainty() -> None:
    digest = _single_digest(_input(delayed_effect_ticks=2, observed_refs=("observed:delay",)))
    assert digest.event_kind is AB1EventDigestKind.DELAYED_EFFECT_DETECTED
    assert digest.uncertainty > 0.0


def test_ab1_event_digest_preserves_source_refs() -> None:
    digest = _single_digest(_input(source_refs=("src:a", "src:b")))
    assert digest.source_refs == ("src:a", "src:b")


def test_ab1_event_digest_preserves_raw_window_or_basis_missing_reason() -> None:
    digest = _single_digest(_input(raw_window_refs=(), raw_window_missing_reason="window_not_available"))
    assert digest.raw_window_refs == ()
    assert digest.raw_window_missing_reason == "window_not_available"


def test_ab1_event_digest_does_not_claim_cause() -> None:
    digest = _single_digest(_input(effect_status="blocked"))
    assert digest.explicit_non_causal_closure is True
    assert digest.cause_claimed is False


def test_ab1_no_public_basis_no_digest() -> None:
    result = build_ab1_event_digests(_input(public_only=False))
    assert result.digests == ()
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab1_hidden_eval_only_no_digest() -> None:
    result = build_ab1_event_digests(_input(hidden_eval_excluded=False))
    assert result.digests == ()
    assert result.telemetry.unsafe_basis_count >= 1


def test_ab1_lossy_digest_requires_lossiness_marker() -> None:
    digest = _single_digest(_input(compression_quality=AB1CompressionQuality.LOSSY))
    assert digest.lossiness is True
    assert digest.compression_quality is AB1CompressionQuality.LOSSY


def test_ab1_rpe_signal_is_not_cause() -> None:
    digest = _single_digest(_input(prediction_error_signal=0.9))
    assert digest.cause_claimed is False
    assert digest.event_kind is not None


def test_ab1_efference_mismatch_is_not_cause() -> None:
    digest = _single_digest(_input(efference_mismatch_present=True, expected_body_delta=True, observed_body_delta=False))
    assert digest.event_kind is AB1EventDigestKind.BODY_DELTA_MISMATCH
    assert digest.cause_claimed is False


def test_ab1_digest_does_not_emit_action_candidate_or_request() -> None:
    digest = _single_digest(_input(effect_status="blocked"))
    payload = asdict(digest)
    forbidden = ("action_candidate", "ap01_request", "world_submission", "execute")
    serialized = str(payload).lower()
    assert all(token not in serialized for token in forbidden)


def test_ab1_digest_confidence_degrades_without_raw_window_refs() -> None:
    strong = _single_digest(_input(raw_window_refs=("raw:1",), raw_window_missing_reason=None, noise_level=0.0))
    weak = _single_digest(_input(raw_window_refs=(), raw_window_missing_reason="raw_missing", noise_level=0.0))
    assert weak.confidence < strong.confidence


def test_ab1_normal_noise_not_high_confidence_anomaly() -> None:
    result = build_ab1_event_digests(_input(magnitude=0.08, noise_level=0.9, expected_refs=(), observed_refs=()))
    assert result.digests == ()


def test_ab1_ablation_no_effect_refs_blocks_effect_event() -> None:
    result = build_ab1_event_digests(
        _input(
            effect_refs=(),
            expected_refs=("expected:move",),
            observed_refs=("observed:block",),
            effect_status="blocked",
        )
    )
    assert result.digests == ()


def test_ab1_ablation_no_residue_refs_blocks_residue_event() -> None:
    result = build_ab1_event_digests(
        _input(
            anomaly_markers=("residue_pattern_break",),
            residue_refs=(),
            expected_refs=(),
            observed_refs=(),
            magnitude=0.5,
            noise_level=0.1,
        )
    )
    assert result.digests == ()


def test_ab1_ablation_no_expected_refs_for_mismatch_blocks_mismatch() -> None:
    result = build_ab1_event_digests(
        _input(
            expected_refs=(),
            observed_refs=("observed:delta",),
            magnitude=0.1,
            noise_level=0.9,
        )
    )
    assert result.digests == ()


def test_ab1_ablation_no_observed_refs_no_digest() -> None:
    result = build_ab1_event_digests(
        _input(
            expected_refs=("expected:delta",),
            observed_refs=(),
            effect_refs=("effect:1",),
            magnitude=0.15,
            noise_level=0.9,
        )
    )
    assert result.digests == ()
