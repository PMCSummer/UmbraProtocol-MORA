from __future__ import annotations

from dataclasses import dataclass

from substrate.ab01_event_digest import (
    AB1CompressionQuality,
    AB1EventDigestInput,
    AB1EventDigestResult,
    build_ab1_event_digests,
)

from .body_action_proof import run_body_action_proof_case


@dataclass(frozen=True, slots=True)
class AB1ProbeCase:
    case_id: str
    description: str


def list_ab1_probe_cases() -> tuple[AB1ProbeCase, ...]:
    return (
        AB1ProbeCase("blocked_movement_effect", "blocked movement effect produces non-causal anomaly digest"),
        AB1ProbeCase("pickup_inventory_delta", "pickup inventory delta mismatch digest"),
        AB1ProbeCase("effect_mismatch", "expected-vs-observed effect mismatch digest"),
        AB1ProbeCase("hidden_eval_only", "hidden/eval-only basis produces no digest"),
    )


def run_ab1_probe_case(case_id: str) -> AB1EventDigestResult:
    if case_id == "blocked_movement_effect":
        run = run_body_action_proof_case(
            scenario_id="internal_move_forward_blocked_wall",
            ticks=2,
            strict_internal_mode=True,
        )
        step = next(item for item in run.step_summaries if item.world_submission_count > 0)
        return build_ab1_event_digests(
            AB1EventDigestInput(
                tick_ref=f"ab1:probe:{case_id}",
                source_refs=("probe:p10_bridge_trace",),
                observation_refs=(step.next_observation_id or "obs:blocked",),
                raw_window_refs=("probe:raw:blocked_effect",),
                effect_refs=(step.world_effect_id or "effect:blocked",),
                residue_refs=("probe:residue:blocked",),
                expected_refs=("expected:movement_success",),
                observed_refs=("observed:movement_blocked",),
                effect_status=step.effect_status,
                magnitude=0.8,
                noise_level=0.1,
                compression_quality=AB1CompressionQuality.LOSSY,
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab1_probe.blocked_movement",
            )
        )
    if case_id == "pickup_inventory_delta":
        run = run_body_action_proof_case(
            scenario_id="internal_pickup_visible_reachable_item",
            ticks=2,
            strict_internal_mode=True,
        )
        step = next(item for item in run.step_summaries if item.world_submission_count > 0)
        return build_ab1_event_digests(
            AB1EventDigestInput(
                tick_ref=f"ab1:probe:{case_id}",
                source_refs=("probe:p10_bridge_trace",),
                observation_refs=(step.next_observation_id or "obs:pickup",),
                raw_window_refs=("probe:raw:pickup_delta",),
                effect_refs=(step.world_effect_id or "effect:pickup",),
                residue_refs=(),
                expected_refs=("expected:inventory_delta:2",),
                observed_refs=("observed:inventory_delta:1",),
                expected_inventory_delta=2,
                observed_inventory_delta=1,
                magnitude=0.55,
                noise_level=0.15,
                compression_quality=AB1CompressionQuality.LOSSLESS,
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab1_probe.pickup_inventory_delta",
            )
        )
    if case_id == "effect_mismatch":
        run = run_body_action_proof_case(
            scenario_id="internal_move_forward_open",
            ticks=2,
            strict_internal_mode=True,
        )
        step = next(item for item in run.step_summaries if item.world_submission_count > 0)
        return build_ab1_event_digests(
            AB1EventDigestInput(
                tick_ref=f"ab1:probe:{case_id}",
                source_refs=("probe:p10_bridge_trace",),
                observation_refs=(step.next_observation_id or "obs:effect_mismatch",),
                raw_window_refs=("probe:raw:effect_mismatch",),
                effect_refs=(step.world_effect_id or "effect:move",),
                residue_refs=("probe:residue:mismatch",),
                expected_refs=("expected:location:grid:2,0",),
                observed_refs=("observed:location:grid:2,1",),
                magnitude=0.6,
                noise_level=0.2,
                compression_quality=AB1CompressionQuality.LOSSY,
                prediction_error_signal=0.6,
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab1_probe.effect_mismatch",
            )
        )
    if case_id == "hidden_eval_only":
        return build_ab1_event_digests(
            AB1EventDigestInput(
                tick_ref=f"ab1:probe:{case_id}",
                source_refs=("probe:hidden_eval",),
                observation_refs=("obs:hidden_eval",),
                raw_window_refs=(),
                raw_window_missing_reason="public_window_missing",
                effect_refs=("effect:hidden_eval",),
                residue_refs=("residue:hidden_eval",),
                expected_refs=("expected:hidden",),
                observed_refs=("observed:hidden",),
                magnitude=0.9,
                noise_level=0.0,
                compression_quality=AB1CompressionQuality.LOSSY,
                public_only=True,
                hidden_eval_excluded=False,
                scenario_label_excluded=True,
                source="ab1_probe.hidden_eval_only",
            )
        )
    raise ValueError(f"Unknown AB1 probe case: {case_id}")
