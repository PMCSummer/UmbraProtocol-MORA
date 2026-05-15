from __future__ import annotations

from collections import Counter

from .models import (
    CounterpartSignalKind,
    FalsifierResult,
    ScenarioResult,
    ScenarioStage,
    ScenarioStep,
)
from .packets import emission_to_subject_packet
from .scripted_counterpart import build_scripted_stage1_scenario, stage1_scenarios


def _phase_obligations_for_signal(signal: CounterpartSignalKind) -> tuple[str, ...]:
    shared = (
        "w01_admit_typed_packet",
        "w01_preserve_source_authority",
        "w01_preserve_claim_vs_fact",
        "w02_no_one_shot_mature_claim",
        "w03_bounded_schema_only_if_supported",
        "w04_applicability_only_not_action_selection",
        "w05_channel_separation_and_mismatch_routing",
        "w06_operational_consequence_no_correction_execution",
    )
    if signal is CounterpartSignalKind.BLOCKED:
        return shared + ("aperture_block_constrains_transfer_feasibility",)
    if signal is CounterpartSignalKind.CONTRADICTION:
        return shared + ("contradiction_requires_uncertainty_or_revalidation",)
    return shared


def build_stage1_result(scenario_id: str) -> ScenarioResult:
    scripted = build_scripted_stage1_scenario(scenario_id)

    steps: list[ScenarioStep] = []
    visible_packets = []
    obligations: set[str] = set()

    for index, emission in enumerate(scripted.emissions, start=1):
        packets = ()
        if emission.visible_to_subject:
            packet = emission_to_subject_packet(emission, packet_id=f"{scenario_id}:packet:{index}")
            visible_packets.append(packet)
            packets = (packet,)

        step_obligations = _phase_obligations_for_signal(emission.signal_kind)
        obligations.update(step_obligations)
        steps.append(
            ScenarioStep(
                step_index=index,
                scripted_b_emission=emission,
                subject_visible_packets=packets,
                harness_truth_snapshot_ref=f"{scenario_id}:truth:step:{index}",
                expected_phase_obligations=step_obligations,
                eval_only_success_labels=scripted.eval_only_labels,
            )
        )

    signal_counts = Counter(packet.signal_kind.value for packet in visible_packets)
    blocked_seen = any(packet.signal_kind is CounterpartSignalKind.BLOCKED for packet in visible_packets)
    contradiction_seen = any(packet.signal_kind is CounterpartSignalKind.CONTRADICTION for packet in visible_packets)
    transfer_outcomes = tuple(packet.transfer_outcome.value for packet in visible_packets if packet.signal_kind is CounterpartSignalKind.TRANSFER_RESULT)

    claim_discipline_markers = [
        "counterpart_claim_not_fact",
        "hidden_truth_excluded",
        "no_trade_specific_shortcut_signals",
    ]
    if contradiction_seen:
        claim_discipline_markers.append("contradiction_visible_without_cleanup")
    if blocked_seen:
        claim_discipline_markers.append("blocked_aperture_constrains_transfer")

    trace_summary = {
        "packet_count": len(visible_packets),
        "signal_counts": dict(signal_counts),
        "blocked_aperture_seen": blocked_seen,
        "transfer_feasible": not blocked_seen,
        "contradiction_seen": contradiction_seen,
        "transfer_outcomes": transfer_outcomes,
    }

    return ScenarioResult(
        scenario_id=scenario_id,
        stage=ScenarioStage.STAGE_1_SCRIPTED_COUNTERPART,
        steps=tuple(steps),
        emitted_packets=tuple(visible_packets),
        phase_obligation_summary=tuple(sorted(obligations)),
        falsifier_results=tuple(),
        trace_summary=trace_summary,
        success_labels=scripted.eval_only_labels,
        claim_discipline_markers=tuple(claim_discipline_markers),
        eval_only={
            "harness_truth": {
                "a": {kind.value: level.value for kind, level in scripted.a_truth.resource_levels.items()},
                "b": {kind.value: level.value for kind, level in scripted.b_truth.resource_levels.items()},
            },
            "hidden_truth_is_subject_invisible": True,
        },
    )


def stage0_packet_dry_run_result() -> ScenarioResult:
    result = build_stage1_result("resource_claim_contact")
    return ScenarioResult(
        scenario_id="stage0_packet_dry_run",
        stage=ScenarioStage.STAGE_0_PACKET_DRY_RUN,
        steps=result.steps,
        emitted_packets=result.emitted_packets,
        phase_obligation_summary=result.phase_obligation_summary,
        falsifier_results=tuple(),
        trace_summary=result.trace_summary,
        success_labels=("packet_contract_valid",),
        claim_discipline_markers=result.claim_discipline_markers,
        eval_only=result.eval_only,
    )


def list_symbolic_trade_scenarios() -> tuple[str, ...]:
    return stage1_scenarios()


def with_falsifier_results(result: ScenarioResult, outcomes: tuple[FalsifierResult, ...]) -> ScenarioResult:
    return ScenarioResult(
        scenario_id=result.scenario_id,
        stage=result.stage,
        steps=result.steps,
        emitted_packets=result.emitted_packets,
        phase_obligation_summary=result.phase_obligation_summary,
        falsifier_results=outcomes,
        trace_summary=result.trace_summary,
        success_labels=result.success_labels,
        claim_discipline_markers=result.claim_discipline_markers,
        eval_only=result.eval_only,
    )
