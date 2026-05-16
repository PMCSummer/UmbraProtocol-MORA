from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys

from .falsifiers import (
    run_stage2_trace_falsifiers,
    run_stage25_reaction_falsifiers,
    run_symbolic_trade_falsifiers,
)
from .internal_state import SelfStateProbeRecord, build_self_state_probe_for_scenario, summarize_self_state_probe
from .models import CounterpartSignalKind, SignalAuthority, SubjectVisiblePacket
from .packets import packet_to_w01_world_packet
from .runner import run_stage1_scenario, run_stage2_trace
from .subject_reaction_probe import (
    AReactionProbeRun,
    AReactionStepRecord,
    CounterpartClaimReactionRecord,
    ExecutionSurfaceLevel,
    ExecutionSurfaceReport,
    W01W06ReactionTraceSummary,
    WorldEventReactionRecord,
    stage25_reaction_to_dict,
)


def _ensure_src_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _load_subject_tick_surfaces():
    _ensure_src_path()
    from substrate.subject_tick.models import SubjectTickContext, SubjectTickInput
    from substrate.subject_tick.update import execute_subject_tick
    from substrate.world_adapter.models import WorldAdapterInput, WorldObservationPacket

    return SubjectTickInput, SubjectTickContext, execute_subject_tick, WorldAdapterInput, WorldObservationPacket


def _world_input_from_packet(packet: SubjectVisiblePacket, *, step_index: int, world_input_cls, obs_cls):
    observation = obs_cls(
        observation_id=f"{packet.packet_id}:obs",
        observation_kind=packet.signal_kind.value,
        source_ref=packet.source_id,
        observed_at=f"step:{step_index}",
        payload_ref=f"symbolic_trade:{packet.packet_id}",
        provenance="experiments.symbolic_trade.stage25",
    )
    return world_input_cls(
        adapter_presence=True,
        adapter_available=True,
        adapter_degraded=packet.signal_kind is CounterpartSignalKind.CONTRADICTION
        or packet.signal_kind is CounterpartSignalKind.BLOCKED,
        observation_packet=observation,
        source_lineage=("experiments.symbolic_trade", "stage25"),
    )


def _tick_scalar_from_self_state(self_state: SelfStateProbeRecord) -> tuple[float, float, float]:
    deficit_count = len(self_state.deficit_markers)
    surplus_count = len(self_state.surplus_markers)
    energy = max(0.15, min(0.95, 0.6 - 0.12 * deficit_count + 0.05 * surplus_count))
    cognitive = max(0.2, min(0.95, 0.58 - 0.04 * deficit_count + 0.03 * surplus_count))
    safety = max(0.2, min(0.95, 0.62 - 0.06 * deficit_count))
    return energy, cognitive, safety


def _world_reaction_from_tick(packet: SubjectVisiblePacket, w01_gate) -> WorldEventReactionRecord:
    reasons = list(w01_gate.reason_codes)
    return WorldEventReactionRecord(
        packet_id=packet.packet_id,
        signal_kind=packet.signal_kind.value,
        source_authority=packet.source_authority.value,
        observed_event_admitted=w01_gate.blocked_count == 0 and w01_gate.revoked_count == 0,
        blocked_aperture_seen=packet.signal_kind is CounterpartSignalKind.BLOCKED,
        contradiction_seen=packet.signal_kind is CounterpartSignalKind.CONTRADICTION,
        self_state_as_world_evidence=False,
        reason_codes=tuple(reasons),
    )


def _claim_reaction_from_tick(packet: SubjectVisiblePacket, w01_gate) -> CounterpartClaimReactionRecord:
    claim_detected = packet.source_authority is SignalAuthority.COUNTERPART_CLAIM
    claim_not_fact_preserved = (not w01_gate.clean_world_claim_allowed) and packet.claim_not_fact_marker
    promoted_to_fact = claim_detected and w01_gate.clean_world_claim_allowed
    false_claim_contested = packet.signal_kind is CounterpartSignalKind.CONTRADICTION
    noisy_claim_contested = packet.signal_kind is CounterpartSignalKind.CONTRADICTION
    reasons = list(w01_gate.reason_codes)
    if claim_detected and claim_not_fact_preserved:
        reasons.append("counterpart_claim_preserved_as_claim")
    return CounterpartClaimReactionRecord(
        packet_id=packet.packet_id,
        claim_detected=claim_detected,
        claim_not_fact_preserved=claim_not_fact_preserved,
        promoted_to_fact=promoted_to_fact,
        false_claim_contested=false_claim_contested,
        noisy_claim_contested=noisy_claim_contested,
        reason_codes=tuple(reasons),
    )


def _summary_from_subject_tick(result) -> W01W06ReactionTraceSummary:
    w01_gate = result.w01_result.gate
    w02_gate = result.w02_result.gate
    w03_gate = result.w03_result.gate
    w04_gate = result.w04_result.gate
    w05_gate = result.w05_result.gate
    w06_gate = result.w06_result.gate
    coverage: list[str] = []
    coverage_evidence: list[str] = []
    for phase_code in ("W01", "W02", "W03", "W04", "W05", "W06"):
        attr_name = f"{phase_code.lower()}_result"
        phase_result = getattr(result, attr_name, None)
        if phase_result is None:
            continue
        gate = getattr(phase_result, "gate", None)
        if gate is None:
            continue
        coverage.append(phase_code)
        coverage_evidence.append(f"{phase_code}:{attr_name}.gate")

    coverage_tuple = tuple(coverage)
    coverage_verified = {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(set(coverage_tuple))
    coverage_missing_reason = None if coverage_verified else "missing_tick_phase_artifacts"
    reason_codes = tuple(
        dict.fromkeys(
            (
                *w01_gate.reason_codes,
                *w02_gate.reason_codes,
                *w03_gate.reason_codes,
                *w04_gate.reason_codes,
                *w05_gate.reason_codes,
                *w06_gate.reason_codes,
            )
        )
    )
    prohibited = (
        "desired_not_world_evidence",
        "counterpart_claim_not_fact",
        "predicted_not_permission",
        "no_correction_execution",
    )
    return W01W06ReactionTraceSummary(
        phase_coverage=coverage_tuple,
        coverage_complete=coverage_verified,
        phase_coverage_verified=coverage_verified,
        phase_coverage_verification_mode="tick_result_artifact_presence",
        phase_coverage_evidence=tuple(coverage_evidence),
        phase_coverage_missing_reason=coverage_missing_reason,
        provenance="subject_tick_real_execution",
        w04_clean_applicability_allowed=not w04_gate.no_clean_applicability,
        w04_usefulness_as_permission=any("usefulness_override" in item for item in w04_gate.reason_codes),
        w05_desired_as_observed=any("desired_as_observed" in item for item in w05_gate.reason_codes),
        w05_predicted_as_permitted=any("predicted_as_permission" in item for item in w05_gate.reason_codes),
        w05_must_not_execute_update=result.state.w05_must_not_execute_update_count > 0,
        w06_correction_candidate_created=result.state.w06_correction_candidate_count > 0,
        w06_correction_executed=False,
        w06_execution_prohibited=w06_gate.must_not_execute_correction,
        w06_residual_uncertainty_present=result.state.w06_residual_uncertainty_count > 0
        or result.state.w06_no_clean_revision,
        reason_codes=reason_codes,
        prohibited_claims=prohibited,
    )


def _summary_from_stage2_projection(scenario_id: str, step_index: int) -> W01W06ReactionTraceSummary:
    stage2 = run_stage2_trace(scenario_id, include_falsifiers=False)
    step = next((item for item in stage2.steps if item.step_index == step_index), stage2.steps[0])
    coverage = tuple(dict.fromkeys(record.phase_code for record in step.phase_records))
    reasons = tuple(dict.fromkeys(code for record in step.phase_records for code in record.reason_codes))
    prohibited = tuple(dict.fromkeys(code for record in step.phase_records for code in record.prohibited_claims))
    delta = [item for record in step.phase_records for item in record.downstream_permission_delta]
    return W01W06ReactionTraceSummary(
        phase_coverage=coverage,
        coverage_complete={"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(set(coverage)),
        phase_coverage_verified=False,
        phase_coverage_verification_mode="adapter_projection_only",
        phase_coverage_evidence=(),
        phase_coverage_missing_reason="no_tick_phase_artifacts_in_projection",
        provenance="adapter_projection",
        w04_clean_applicability_allowed=any(
            record.phase_code == "W04" and "may_deploy_candidate:true" in record.downstream_permission_delta
            for record in step.phase_records
        ),
        w04_usefulness_as_permission=any("should_trade:true" in item for item in delta),
        w05_desired_as_observed=any("desired_as_observed" in code for code in reasons),
        w05_predicted_as_permitted=any("predicted_as_permission" in code for code in reasons),
        w05_must_not_execute_update=any("must_not_execute_update:true" == item for item in delta),
        w06_correction_candidate_created=any("correction_candidate_created:true" == item for item in delta),
        w06_correction_executed=any("correction_executed:true" == item for item in delta),
        w06_execution_prohibited=all(record.execution_prohibited for record in step.phase_records if record.phase_code == "W06"),
        w06_residual_uncertainty_present=any(
            "residue" in marker for record in step.phase_records for marker in record.uncertainty_markers
        ),
        reason_codes=reasons,
        prohibited_claims=prohibited,
    )


def _visible_claim_summary(stage1_result) -> dict[str, object]:
    claim_packets = [packet for packet in stage1_result.emitted_packets if packet.source_authority is SignalAuthority.COUNTERPART_CLAIM]
    return {
        "visible_packet_count": len(stage1_result.emitted_packets),
        "counterpart_claim_count": len(claim_packets),
        "claim_packet_ids": [item.packet_id for item in claim_packets],
        "claim_not_fact_preserved_count": sum(1 for item in claim_packets if item.claim_not_fact_marker),
    }


def run_stage25_reaction_probe(
    scenario_id: str,
    *,
    include_falsifiers: bool = True,
) -> AReactionProbeRun:
    stage1 = run_stage1_scenario(scenario_id, include_falsifiers=False)
    self_state = build_self_state_probe_for_scenario(scenario_id)

    attempted: list[str] = ["subject_tick.execute_subject_tick", "owner_surface.packet_to_w01_world_packet", "stage2_adapter_projection"]
    successful: list[str] = []
    failed: list[str] = []
    fallback_reasons: list[str] = []
    callable_surfaces: list[str] = []
    steps: list[AReactionStepRecord] = []
    subject_tick_used = False
    owner_surface_used = False
    adapter_projection_used = False

    tick_success_count = 0
    tick_failure_count = 0
    tick_import_error: str | None = None

    try:
        (
            subject_tick_input_cls,
            subject_tick_context_cls,
            execute_subject_tick_fn,
            world_adapter_input_cls,
            world_observation_packet_cls,
        ) = _load_subject_tick_surfaces()
        callable_surfaces.extend(
            [
                "subject_tick.execute_subject_tick",
                "subject_tick.models.SubjectTickInput",
                "subject_tick.models.SubjectTickContext",
                "world_adapter.models.WorldAdapterInput",
            ]
        )
    except Exception as exc:  # pragma: no cover - runtime dependent
        tick_import_error = f"subject_tick_import_failed:{exc}"
        failed.append("subject_tick.execute_subject_tick")
        fallback_reasons.append(tick_import_error)
        subject_tick_input_cls = None
        subject_tick_context_cls = None
        execute_subject_tick_fn = None
        world_adapter_input_cls = None
        world_observation_packet_cls = None

    for step in stage1.steps:
        for packet in step.subject_visible_packets:
            if execute_subject_tick_fn is not None:
                try:
                    energy, cognitive, safety = _tick_scalar_from_self_state(self_state)
                    tick_input = subject_tick_input_cls(
                        case_id=f"stage25-{scenario_id}-s{step.step_index}",
                        energy=energy,
                        cognitive=cognitive,
                        safety=safety,
                    )
                    world_adapter_input = _world_input_from_packet(
                        packet,
                        step_index=step.step_index,
                        world_input_cls=world_adapter_input_cls,
                        obs_cls=world_observation_packet_cls,
                    )
                    tick_context = subject_tick_context_cls(
                        world_adapter_input=world_adapter_input,
                        require_world_grounded_transition=True,
                    )
                    tick_result = execute_subject_tick_fn(tick_input, tick_context)
                    tick_success_count += 1
                    subject_tick_used = True
                    summary = _summary_from_subject_tick(tick_result)
                    world_reaction = _world_reaction_from_tick(packet, tick_result.w01_result.gate)
                    claim_reaction = _claim_reaction_from_tick(packet, tick_result.w01_result.gate)
                    steps.append(
                        AReactionStepRecord(
                            step_index=step.step_index,
                            packet_id=packet.packet_id,
                            world_event_reaction=world_reaction,
                            counterpart_claim_reaction=claim_reaction,
                            phase_trace_summary=summary,
                            execution_surface_source="subject_tick.execute_subject_tick",
                            adapter_limitations=(),
                        )
                    )
                    continue
                except Exception as exc:  # pragma: no cover - runtime dependent
                    tick_failure_count += 1
                    failed.append(f"subject_tick.execute_subject_tick:{packet.packet_id}")
                    fallback_reasons.append(f"subject_tick_execution_failed:{packet.packet_id}:{exc}")

            # owner surface probe: ensure a real W01 owner packet can be constructed
            try:
                packet_to_w01_world_packet(packet, sequence=step.step_index)
                owner_surface_used = True
                if "owner_surface.packet_to_w01_world_packet" not in successful:
                    successful.append("owner_surface.packet_to_w01_world_packet")
            except Exception as exc:  # pragma: no cover - runtime dependent
                failed.append(f"owner_surface.packet_to_w01_world_packet:{packet.packet_id}")
                fallback_reasons.append(f"owner_surface_failed:{packet.packet_id}:{exc}")

            summary = _summary_from_stage2_projection(scenario_id, step.step_index)
            adapter_projection_used = True
            world_reaction = WorldEventReactionRecord(
                packet_id=packet.packet_id,
                signal_kind=packet.signal_kind.value,
                source_authority=packet.source_authority.value,
                observed_event_admitted=True,
                blocked_aperture_seen=packet.signal_kind is CounterpartSignalKind.BLOCKED,
                contradiction_seen=packet.signal_kind is CounterpartSignalKind.CONTRADICTION,
                self_state_as_world_evidence=False,
                reason_codes=("adapter_projection_only",),
            )
            claim_reaction = CounterpartClaimReactionRecord(
                packet_id=packet.packet_id,
                claim_detected=packet.source_authority is SignalAuthority.COUNTERPART_CLAIM,
                claim_not_fact_preserved=packet.claim_not_fact_marker,
                promoted_to_fact=False,
                false_claim_contested=packet.signal_kind is CounterpartSignalKind.CONTRADICTION,
                noisy_claim_contested=packet.signal_kind is CounterpartSignalKind.CONTRADICTION,
                reason_codes=("projection_claim_boundary_preserved",),
            )
            steps.append(
                AReactionStepRecord(
                    step_index=step.step_index,
                    packet_id=packet.packet_id,
                    world_event_reaction=world_reaction,
                    counterpart_claim_reaction=claim_reaction,
                    phase_trace_summary=summary,
                    execution_surface_source="adapter_projection",
                    adapter_limitations=("subject_tick_unavailable_or_failed",),
                )
            )

    if tick_success_count > 0 and tick_failure_count == 0:
        execution_level = ExecutionSurfaceLevel.FULL_SUBJECT_TICK_EXECUTION
        successful.append("subject_tick.execute_subject_tick")
    elif tick_success_count > 0 and tick_failure_count > 0:
        execution_level = ExecutionSurfaceLevel.PARTIAL_SUBJECT_TICK_EXECUTION
        successful.append("subject_tick.execute_subject_tick")
        adapter_projection_used = True
    elif owner_surface_used:
        execution_level = ExecutionSurfaceLevel.OWNER_SURFACE_EXECUTION
    elif adapter_projection_used:
        execution_level = ExecutionSurfaceLevel.ADAPTER_PROJECTION_ONLY
    else:
        execution_level = ExecutionSurfaceLevel.NON_EXECUTABLE
        if tick_import_error is None:
            fallback_reasons.append("no_executable_surface_available")

    if adapter_projection_used and execution_level is not ExecutionSurfaceLevel.ADAPTER_PROJECTION_ONLY and tick_success_count > 0:
        fallback_reasons.append("adapter_projection_used_for_failed_step_only")
    if adapter_projection_used and execution_level is ExecutionSurfaceLevel.OWNER_SURFACE_EXECUTION:
        fallback_reasons.append("owner_surface_available_but_phase_trace_projected")

    phase_coverage = tuple(
        sorted(
            {
                code
                for item in steps
                for code in item.phase_trace_summary.phase_coverage
            }
        )
    )
    reaction_markers = [
        "stage25_real_a_reaction_probe",
        f"execution_level:{execution_level.value}",
        f"subject_tick_used:{str(subject_tick_used).lower()}",
        f"owner_surface_used:{str(owner_surface_used).lower()}",
        f"adapter_projection_used:{str(adapter_projection_used).lower()}",
    ]
    if not {"W01", "W02", "W03", "W04", "W05", "W06"}.issubset(set(phase_coverage)):
        reaction_markers.append("phase_coverage_incomplete")

    run = AReactionProbeRun(
        scenario_id=scenario_id,
        stage="stage25_reaction_probe",
        execution_surface=ExecutionSurfaceReport(
            execution_level=execution_level,
            attempted_surfaces=tuple(dict.fromkeys(attempted)),
            successful_surfaces=tuple(dict.fromkeys(successful)),
            failed_surfaces=tuple(failed),
            fallback_reasons=tuple(dict.fromkeys(fallback_reasons)),
            callable_surfaces=tuple(dict.fromkeys(callable_surfaces)),
            subject_tick_used=subject_tick_used,
            owner_surface_used=owner_surface_used,
            adapter_projection_used=adapter_projection_used,
        ),
        self_state_probe=self_state,
        steps=tuple(steps),
        b_visible_claim_summary=_visible_claim_summary(stage1),
        reaction_markers=tuple(reaction_markers),
        falsifier_results=(),
        eval_only={
            "harness_truth": stage1.eval_only.get("harness_truth", {}),
            "success_labels": stage1.success_labels,
            "stage1_eval_only": stage1.eval_only,
            "self_state_probe_summary": summarize_self_state_probe(self_state),
        },
    )

    if include_falsifiers:
        stage1_falsifiers = run_symbolic_trade_falsifiers(stage1)
        stage2_falsifiers = run_stage2_trace_falsifiers(run_stage2_trace(scenario_id, include_falsifiers=False))
        stage25_falsifiers = run_stage25_reaction_falsifiers(run)
        merged = [asdict(item) for item in stage1_falsifiers] + [asdict(item) for item in stage2_falsifiers] + [
            asdict(item) for item in stage25_falsifiers
        ]
        run = AReactionProbeRun(
            scenario_id=run.scenario_id,
            stage=run.stage,
            execution_surface=run.execution_surface,
            self_state_probe=run.self_state_probe,
            steps=run.steps,
            b_visible_claim_summary=run.b_visible_claim_summary,
            reaction_markers=run.reaction_markers,
            falsifier_results=tuple(merged),
            claim_boundary=run.claim_boundary,
            eval_only=run.eval_only,
        )

    return run


def stage25_reaction_result_to_dict(run: AReactionProbeRun, *, include_eval_only: bool = False) -> dict[str, object]:
    return stage25_reaction_to_dict(run, include_eval_only=include_eval_only)
