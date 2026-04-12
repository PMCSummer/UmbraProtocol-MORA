from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from substrate.contracts import (
    ContinuityDomainState,
    RegulationDomainState,
    RuntimeDomainsState,
    RuntimeState,
    ValidityDomainState,
)
from substrate.runtime_tap_trace import (
    deactivate_tick_trace,
    derive_tick_id,
    finish_tick_trace,
    reset_trace_state,
    start_tick_trace,
)
from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.runtime_topology.models import (
    RuntimeEpistemicCaseInput,
    RuntimeRegulationSharedDomainInput,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput
from substrate.world_adapter.models import (
    WorldActionPacket,
    WorldAdapterInput,
    WorldEffectObservationPacket,
    WorldObservationPacket,
)

TRACE_EVENT_KEYS = {"tick_id", "order", "module", "step", "values", "note"}
REQUIRED_SCENARIO_FAMILIES = {
    "world_absence_poverty",
    "epistemic_fragility",
    "regulation_mode_validity_pressure",
    "ownership_self_prediction_instability",
    "memory_narrative_temptation",
}


@dataclass(frozen=True, slots=True)
class EdgyBehavioralCase:
    case_id: str
    scenario_family: str
    scenario_intent: str
    key_tension_axis: tuple[str, ...]
    what_to_inspect_in_trace: tuple[str, ...]
    why_this_case_exists: str
    paired_with: str | None = None
    coverage_tags: tuple[str, ...] = ()
    energy: float = 66.0
    cognitive: float = 44.0
    safety: float = 74.0
    unresolved_preference: bool = False
    route_class: str = RuntimeRouteClass.PRODUCTION_CONTOUR.value
    context_overrides: Mapping[str, object] = field(default_factory=dict)
    epistemic_overrides: Mapping[str, object] = field(default_factory=dict)
    regulation_overrides: Mapping[str, object] = field(default_factory=dict)


def _obs(case_id: str) -> WorldObservationPacket:
    return WorldObservationPacket(
        observation_id=f"obs-{case_id}",
        observation_kind="external_state_snapshot",
        source_ref=f"sensor/{case_id}",
        observed_at=f"{case_id}-obs-t0",
        payload_ref=f"payload://obs/{case_id}",
        provenance="edgy_battery.world_observation",
    )


def _action(case_id: str, *, action_id: str | None = None) -> WorldActionPacket:
    token = action_id or f"act-{case_id}"
    return WorldActionPacket(
        action_id=token,
        action_kind="emit_world_action",
        target_ref=f"target/{case_id}",
        requested_at=f"{case_id}-act-t0",
        payload_ref=f"payload://act/{case_id}",
        provenance="edgy_battery.world_action",
    )


def _effect(
    case_id: str,
    *,
    action_id: str,
    success: bool,
) -> WorldEffectObservationPacket:
    return WorldEffectObservationPacket(
        effect_id=f"eff-{case_id}",
        action_id=action_id,
        effect_kind="world_effect_observation",
        observed_at=f"{case_id}-eff-t0",
        success=success,
        source_ref=f"effect/{case_id}",
        provenance="edgy_battery.world_effect",
    )


def _world_absent_input() -> WorldAdapterInput:
    return WorldAdapterInput(
        adapter_presence=False,
        adapter_available=False,
        adapter_degraded=False,
        source_lineage=("edgy_battery.world_absent",),
        reason="edgy_battery.world_absent",
    )


def _world_observation_only_input(case_id: str) -> WorldAdapterInput:
    return WorldAdapterInput(
        adapter_presence=True,
        adapter_available=True,
        adapter_degraded=False,
        observation_packet=_obs(case_id),
        source_lineage=("edgy_battery.world_observation_only",),
        reason="edgy_battery.world_observation_only",
    )


def _world_uncorrelated_effect_input(case_id: str) -> WorldAdapterInput:
    action_packet = _action(case_id, action_id=f"act-{case_id}-primary")
    return WorldAdapterInput(
        adapter_presence=True,
        adapter_available=True,
        adapter_degraded=False,
        observation_packet=_obs(case_id),
        action_packet=action_packet,
        effect_packet=_effect(
            case_id,
            action_id=f"act-{case_id}-foreign",
            success=False,
        ),
        source_lineage=("edgy_battery.world_uncorrelated_effect",),
        reason="edgy_battery.world_uncorrelated_effect",
    )


def _world_correlated_effect_input(case_id: str) -> WorldAdapterInput:
    action_packet = _action(case_id, action_id=f"act-{case_id}-primary")
    return WorldAdapterInput(
        adapter_presence=True,
        adapter_available=True,
        adapter_degraded=False,
        observation_packet=_obs(case_id),
        action_packet=action_packet,
        effect_packet=_effect(case_id, action_id=action_packet.action_id, success=True),
        source_lineage=("edgy_battery.world_correlated_effect",),
        reason="edgy_battery.world_correlated_effect",
    )


def _world_action_without_observation_input(case_id: str) -> WorldAdapterInput:
    return WorldAdapterInput(
        adapter_presence=True,
        adapter_available=True,
        adapter_degraded=False,
        action_packet=_action(case_id),
        source_lineage=("edgy_battery.world_action_without_observation",),
        reason="edgy_battery.world_action_without_observation",
    )


def _prior_runtime_state(
    *,
    revalidation_required: bool,
    no_safe_reuse: bool,
    override_scope: str = "narrow",
    no_strong_override_claim: bool = True,
) -> RuntimeState:
    return RuntimeState(
        domains=RuntimeDomainsState(
            regulation=RegulationDomainState(
                pressure_level=0.7,
                escalation_stage="steady",
                override_scope=override_scope,
                no_strong_override_claim=no_strong_override_claim,
                gate_accepted=True,
                source_state_ref="edgy_battery.prior_runtime.regulation",
                updated_by_phase="R04",
                last_update_provenance="edgy_battery.seed",
            ),
            continuity=ContinuityDomainState(
                c04_mode_claim="continue_stream",
                c04_selected_mode="continue_stream",
                mode_legitimacy=True,
                endogenous_tick_allowed=True,
                arbitration_confidence=0.72,
                source_state_ref="edgy_battery.prior_runtime.continuity",
                updated_by_phase="C04",
                last_update_provenance="edgy_battery.seed",
            ),
            validity=ValidityDomainState(
                c05_action_claim=(
                    "halt_reuse_and_rebuild_scope"
                    if no_safe_reuse
                    else "run_selective_revalidation"
                    if revalidation_required
                    else "allow_continue"
                ),
                c05_validity_action=(
                    "halt_reuse_and_rebuild_scope"
                    if no_safe_reuse
                    else "run_selective_revalidation"
                    if revalidation_required
                    else "allow_continue"
                ),
                legality_reuse_allowed=not (revalidation_required or no_safe_reuse),
                revalidation_required=revalidation_required,
                no_safe_reuse=no_safe_reuse,
                selective_scope_targets=("memory_surface",) if revalidation_required else (),
                source_state_ref="edgy_battery.prior_runtime.validity",
                updated_by_phase="C05",
                last_update_provenance="edgy_battery.seed",
            ),
        )
    )


CASE_BATTERY: tuple[EdgyBehavioralCase, ...] = (
    EdgyBehavioralCase(
        case_id="world_absent_no_basis",
        scenario_family="world_absence_poverty",
        scenario_intent="No world adapter presence and explicit world-grounding requirement.",
        key_tension_axis=("world_presence:none", "world_grounding:required"),
        what_to_inspect_in_trace=(
            "world_adapter",
            "world_entry_contract",
            "world_seam_enforcement",
            "downstream_obedience",
            "subject_tick",
        ),
        why_this_case_exists="Baseline for world-absence behavior and bounded seam enforcement.",
        paired_with="world_partial_observation_only",
        coverage_tags=("A1_world_absent",),
        context_overrides={
            "world_adapter_input": _world_absent_input(),
            "require_world_grounded_transition": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="world_partial_observation_only",
        scenario_family="world_absence_poverty",
        scenario_intent="World is partially present via observation, but effect basis is still missing.",
        key_tension_axis=("world_presence:partial", "effect_basis:missing", "action_projection:present"),
        what_to_inspect_in_trace=(
            "world_adapter",
            "world_entry_contract",
            "s01_efference_copy",
            "s02_prediction_boundary",
            "subject_tick",
        ),
        why_this_case_exists="Counterfactual to world absence with minimal world signal and action projection pressure.",
        paired_with="world_absent_no_basis",
        coverage_tags=("A2_world_partial", "D13_action_projection_without_safe_world_basis"),
        context_overrides={
            "world_adapter_input": _world_observation_only_input("world_partial_observation_only"),
            "emit_world_action_candidate": True,
            "require_world_grounded_transition": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="world_contradictory_uncorrelated_effect",
        scenario_family="world_absence_poverty",
        scenario_intent="World action/effect are present but effect feedback is uncorrelated.",
        key_tension_axis=("world_effect_correlation:false", "seam_integrity:stressed"),
        what_to_inspect_in_trace=(
            "world_adapter",
            "world_entry_contract",
            "world_seam_enforcement",
            "s02_prediction_boundary",
            "bounded_outcome_resolution",
        ),
        why_this_case_exists="Covers contradictory world seam where effect evidence exists but fails correlation discipline.",
        paired_with="world_correlated_effect_reference",
        coverage_tags=("A3_world_contradictory", "D12_prediction_boundary_invalidated"),
        context_overrides={
            "world_adapter_input": _world_uncorrelated_effect_input("world_contradictory_uncorrelated_effect"),
            "require_world_grounded_transition": True,
            "require_world_effect_feedback_for_success_claim": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="world_correlated_effect_reference",
        scenario_family="world_absence_poverty",
        scenario_intent="Counterfactual to contradictory world: same structure but correlated effect feedback.",
        key_tension_axis=("world_effect_correlation:true", "seam_integrity:improved"),
        what_to_inspect_in_trace=(
            "world_adapter",
            "world_entry_contract",
            "world_seam_enforcement",
            "downstream_obedience",
            "subject_tick",
        ),
        why_this_case_exists="Pair for isolating impact of correlation on world seam gating.",
        paired_with="world_contradictory_uncorrelated_effect",
        coverage_tags=("A3_counterfactual_correlated",),
        context_overrides={
            "world_adapter_input": _world_correlated_effect_input("world_correlated_effect_reference"),
            "require_world_grounded_transition": True,
            "require_world_effect_feedback_for_success_claim": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="epistemic_weak_report_low_conf",
        scenario_family="epistemic_fragility",
        scenario_intent="Weak report-like epistemic signal must stay report-like, not observation-like.",
        key_tension_axis=("epistemic_status:report", "confidence:low"),
        what_to_inspect_in_trace=("epistemics", "regulation", "t03_hypothesis_competition", "subject_tick"),
        why_this_case_exists="Baseline epistemic fragility without strict observation requirement.",
        paired_with="epistemic_report_observation_required",
        coverage_tags=("B4_weak_report_like_signal",),
        epistemic_overrides={
            "content": "heard second-hand claim with weak support",
            "source_id": "reporter/weak",
            "source_class": "reporter",
            "modality": "user_text",
            "confidence_hint": "low",
            "support_note": "single_report_without_sensor_basis",
        },
    ),
    EdgyBehavioralCase(
        case_id="epistemic_report_observation_required",
        scenario_family="epistemic_fragility",
        scenario_intent="Same weak report signal, but strict observation requirement pushes abstain boundary.",
        key_tension_axis=("epistemic_require_observation:true", "signal:report_low"),
        what_to_inspect_in_trace=("epistemics", "c05_temporal_validity", "bounded_outcome_resolution", "subject_tick"),
        why_this_case_exists="Counterfactual showing effect of strict epistemic observation requirement.",
        paired_with="epistemic_weak_report_low_conf",
        coverage_tags=("B5_abstain_boundary",),
        epistemic_overrides={
            "content": "heard second-hand claim with weak support",
            "source_id": "reporter/weak",
            "source_class": "reporter",
            "modality": "user_text",
            "confidence_hint": "low",
            "support_note": "single_report_without_sensor_basis",
            "require_observation": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="epistemic_quasi_observation_non_sensor",
        scenario_family="epistemic_fragility",
        scenario_intent="Tempting quasi-observation shape should not become a strong world claim.",
        key_tension_axis=("source_class:reporter", "modality:sensor_stream", "quasi_observation:true"),
        what_to_inspect_in_trace=("epistemics", "world_entry_contract", "s02_prediction_boundary", "subject_tick"),
        why_this_case_exists="Checks that non-sensor pseudo-observation does not get upgraded.",
        paired_with="epistemic_true_sensor_observation",
        coverage_tags=("B6_tempting_quasi_observation",),
        epistemic_overrides={
            "content": "stream-like text that looks like observation but source is not sensor",
            "source_id": "reporter/quasi-observation",
            "source_class": "reporter",
            "modality": "sensor_stream",
            "confidence_hint": "high",
        },
    ),
    EdgyBehavioralCase(
        case_id="epistemic_true_sensor_observation",
        scenario_family="epistemic_fragility",
        scenario_intent="Counterfactual true sensor observation with stronger epistemic basis.",
        key_tension_axis=("source_class:sensor", "modality:sensor_stream", "confidence:high"),
        what_to_inspect_in_trace=("epistemics", "regulation", "bounded_outcome_resolution", "subject_tick"),
        why_this_case_exists="Pair for quasi-observation case to isolate epistemic-source legitimacy effects.",
        paired_with="epistemic_quasi_observation_non_sensor",
        coverage_tags=("B6_counterfactual_sensor_observation",),
        epistemic_overrides={
            "content": "sensor reading with explicit stream provenance",
            "source_id": "sensor/alpha",
            "source_class": "sensor",
            "modality": "sensor_stream",
            "confidence_hint": "high",
            "support_note": "calibrated_sensor_surface",
        },
    ),
    EdgyBehavioralCase(
        case_id="regulation_high_pressure_guarded_continue",
        scenario_family="regulation_mode_validity_pressure",
        scenario_intent="High regulation pressure with narrow override should remain bounded continuation.",
        key_tension_axis=("pressure:high", "override_scope:narrow", "detour:none_or_light"),
        what_to_inspect_in_trace=("regulation", "c04_mode_arbitration", "c05_temporal_validity", "subject_tick"),
        why_this_case_exists="Covers high-pressure regulation without forcing emergency override detour.",
        paired_with="regulation_emergency_override_detour",
        coverage_tags=("C7_high_pressure_bounded_continuation",),
        regulation_overrides={
            "pressure_level": 0.93,
            "escalation_stage": "threat",
            "override_scope": "narrow",
            "no_strong_override_claim": True,
            "gate_accepted": True,
            "source_state_ref": "edgy_battery.regulation.high_pressure",
        },
    ),
    EdgyBehavioralCase(
        case_id="regulation_emergency_override_detour",
        scenario_family="regulation_mode_validity_pressure",
        scenario_intent="Emergency override scope should pressure contour into repair/revalidation detour.",
        key_tension_axis=("pressure:critical", "override_scope:emergency", "detour:expected"),
        what_to_inspect_in_trace=(
            "regulation",
            "c04_mode_arbitration",
            "bounded_outcome_resolution",
            "downstream_obedience",
            "subject_tick",
        ),
        why_this_case_exists="Counterfactual to narrow high-pressure case showing emergency override impact.",
        paired_with="regulation_high_pressure_guarded_continue",
        coverage_tags=("C10_legality_revalidation_pressure_no_full_collapse",),
        regulation_overrides={
            "pressure_level": 0.97,
            "escalation_stage": "critical",
            "override_scope": "emergency",
            "no_strong_override_claim": False,
            "gate_accepted": True,
            "source_state_ref": "edgy_battery.regulation.emergency_override",
        },
    ),
    EdgyBehavioralCase(
        case_id="mode_quiescent_safe_idle_conflict",
        scenario_family="regulation_mode_validity_pressure",
        scenario_intent="Mode arbitration constrained to quiescent path with safe-idle behavior.",
        key_tension_axis=("endogenous_tick:disabled", "mode_source:quiescent"),
        what_to_inspect_in_trace=("c04_mode_arbitration", "c05_temporal_validity", "bounded_outcome_resolution", "subject_tick"),
        why_this_case_exists="Explicit mode-conflict/safe-idle contour under constrained endogenous authority.",
        paired_with="mode_endogenous_relief_variant",
        coverage_tags=("C8_mode_conflict_safe_idle",),
        energy=52.0,
        cognitive=35.0,
        safety=82.0,
        context_overrides={
            "allow_endogenous_tick": False,
            "external_turn_present": False,
            "mode_resource_budget": 0.22,
            "mode_cooldown_active": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="mode_endogenous_relief_variant",
        scenario_family="regulation_mode_validity_pressure",
        scenario_intent="Counterfactual with endogenous allowance and stronger budget for mode shift.",
        key_tension_axis=("endogenous_tick:enabled", "resource_budget:high"),
        what_to_inspect_in_trace=("c04_mode_arbitration", "c05_temporal_validity", "subject_tick"),
        why_this_case_exists="Pair to safe-idle mode case with one critical variable family relaxed.",
        paired_with="mode_quiescent_safe_idle_conflict",
        coverage_tags=("C8_mode_shift_counterfactual",),
        energy=81.0,
        cognitive=69.0,
        safety=58.0,
        unresolved_preference=True,
        context_overrides={
            "allow_endogenous_tick": True,
            "external_turn_present": False,
            "mode_resource_budget": 0.95,
            "mode_cooldown_active": False,
            "allow_provisional_carry": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="temporal_validity_tight_revalidation",
        scenario_family="regulation_mode_validity_pressure",
        scenario_intent="Temporal validity surface preloaded with revalidation requirement but not hard halt.",
        key_tension_axis=("validity:revalidation_required", "legality:no_full_collapse"),
        what_to_inspect_in_trace=("c05_temporal_validity", "bounded_outcome_resolution", "subject_tick"),
        why_this_case_exists="Covers tight legality/validity pressure that should detour without forcing full halt.",
        paired_with="temporal_validity_permissive_reuse",
        coverage_tags=("C9_temporal_validity_tight", "C10_legality_revalidation_pressure_no_full_collapse"),
        context_overrides={
            "prior_runtime_state": _prior_runtime_state(
                revalidation_required=True,
                no_safe_reuse=False,
            ),
            "dependency_trigger_hits": ("dep_shift_1", "dep_shift_2"),
            "context_shift_markers": ("context_drift",),
            "contradicted_source_refs": ("source/contested",),
        },
    ),
    EdgyBehavioralCase(
        case_id="temporal_validity_permissive_reuse",
        scenario_family="regulation_mode_validity_pressure",
        scenario_intent="Counterfactual temporal validity with permissive shared validity surface.",
        key_tension_axis=("validity:reuse_allowed", "revalidation_required:false"),
        what_to_inspect_in_trace=("c05_temporal_validity", "bounded_outcome_resolution", "subject_tick"),
        why_this_case_exists="Pair for isolating c05 pressure effect on contour outcome routing.",
        paired_with="temporal_validity_tight_revalidation",
        coverage_tags=("C9_counterfactual_permissive_validity",),
        context_overrides={
            "prior_runtime_state": _prior_runtime_state(
                revalidation_required=False,
                no_safe_reuse=False,
            ),
        },
    ),
    EdgyBehavioralCase(
        case_id="ownership_prediction_memory_narrative_temptation_weak",
        scenario_family="ownership_self_prediction_instability",
        scenario_intent="Ownership ambiguity and memory/narrative claim pressure on weak world basis.",
        key_tension_axis=(
            "ownership_ambiguity:high",
            "prediction_boundary:stressed",
            "memory_claim:required_without_basis",
            "narrative_claim:required_without_basis",
        ),
        what_to_inspect_in_trace=(
            "s01_efference_copy",
            "s02_prediction_boundary",
            "s03_ownership_weighted_learning",
            "s_minimal_contour",
            "m_minimal",
            "n_minimal",
            "subject_tick",
        ),
        why_this_case_exists="Concentrates ownership/prediction instability with explicit memory+narrative temptation pressure.",
        paired_with="ownership_prediction_memory_narrative_temptation_stronger",
        coverage_tags=(
            "D11_ownership_ambiguity",
            "D12_prediction_boundary_invalidated",
            "E14_memory_temptation_without_safe_claim",
            "E15_narrative_temptation_without_safe_claim",
        ),
        unresolved_preference=True,
        context_overrides={
            "world_adapter_input": _world_action_without_observation_input(
                "ownership_prediction_memory_narrative_temptation_weak"
            ),
            "emit_world_action_candidate": True,
            "require_self_side_claim": True,
            "require_self_controlled_transition_claim": True,
            "require_s02_boundary_consumer": True,
            "require_memory_safe_claim": True,
            "require_narrative_safe_claim": True,
            "strict_mixed_attribution_guard": True,
        },
    ),
    EdgyBehavioralCase(
        case_id="ownership_prediction_memory_narrative_temptation_stronger",
        scenario_family="memory_narrative_temptation",
        scenario_intent="Counterfactual: same temptation pressure with stronger world support and correlated effect.",
        key_tension_axis=(
            "ownership_basis:improved",
            "prediction_boundary:stronger_signal",
            "memory_narrative_pressure:same",
        ),
        what_to_inspect_in_trace=(
            "world_adapter",
            "s02_prediction_boundary",
            "s03_ownership_weighted_learning",
            "s_minimal_contour",
            "m_minimal",
            "n_minimal",
            "subject_tick",
        ),
        why_this_case_exists="Paired variant for checking whether slightly stronger basis changes bounded behavior.",
        paired_with="ownership_prediction_memory_narrative_temptation_weak",
        coverage_tags=("E16_stronger_support_counterfactual",),
        unresolved_preference=True,
        context_overrides={
            "world_adapter_input": _world_correlated_effect_input(
                "ownership_prediction_memory_narrative_temptation_stronger"
            ),
            "require_world_grounded_transition": True,
            "require_world_effect_feedback_for_success_claim": True,
            "require_self_side_claim": True,
            "require_self_controlled_transition_claim": True,
            "require_s02_boundary_consumer": True,
            "require_memory_safe_claim": True,
            "require_narrative_safe_claim": True,
            "strict_mixed_attribution_guard": True,
        },
    ),
)


def _build_context(case: EdgyBehavioralCase) -> SubjectTickContext:
    return SubjectTickContext(**dict(case.context_overrides))


def _build_epistemic_case_input(case: EdgyBehavioralCase) -> RuntimeEpistemicCaseInput | None:
    if not case.epistemic_overrides:
        return None
    return RuntimeEpistemicCaseInput(**dict(case.epistemic_overrides))


def _build_regulation_input(case: EdgyBehavioralCase) -> RuntimeRegulationSharedDomainInput | None:
    if not case.regulation_overrides:
        return None
    return RuntimeRegulationSharedDomainInput(**dict(case.regulation_overrides))


def _load_trace_events(path: Path) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    events: list[dict[str, object]] = []
    for line in lines:
        if line.strip():
            events.append(json.loads(line))
    return events


def _run_case(case: EdgyBehavioralCase, traces_dir: Path) -> dict[str, object]:
    tick_id = derive_tick_id(case.case_id, prior_tick_index=None)
    token = start_tick_trace(tick_id=tick_id, output_root=traces_dir)
    try:
        dispatch_runtime_tick(
            RuntimeDispatchRequest(
                tick_input=SubjectTickInput(
                    case_id=case.case_id,
                    energy=case.energy,
                    cognitive=case.cognitive,
                    safety=case.safety,
                    unresolved_preference=case.unresolved_preference,
                ),
                context=_build_context(case),
                epistemic_case_input=_build_epistemic_case_input(case),
                regulation_shared_domain_input=_build_regulation_input(case),
                route_class=RuntimeRouteClass(case.route_class),
            )
        )
    finally:
        deactivate_tick_trace(token)

    meta = finish_tick_trace(tick_id=tick_id)
    trace_path = Path(str(meta["trace_path"])).resolve()
    events = _load_trace_events(trace_path)
    if int(meta["event_count"]) != len(events):
        raise RuntimeError(
            f"trace event count mismatch for {case.case_id}: "
            f"meta={meta['event_count']} actual={len(events)}"
        )

    return {
        "case_id": case.case_id,
        "scenario_family": case.scenario_family,
        "scenario_intent": case.scenario_intent,
        "paired_with": case.paired_with,
        "key_tension_axis": list(case.key_tension_axis),
        "what_to_inspect_in_trace": list(case.what_to_inspect_in_trace),
        "why_this_case_exists": case.why_this_case_exists,
        "coverage_tags": list(case.coverage_tags),
        "tick_id": tick_id,
        "trace_path": str(trace_path),
        "event_count": len(events),
    }


def run_battery_sanity_checks(manifest: Mapping[str, object]) -> dict[str, bool]:
    cases_raw = manifest.get("cases", [])
    cases = list(cases_raw) if isinstance(cases_raw, list) else []
    case_ids = [str(case.get("case_id")) for case in cases if isinstance(case, dict)]
    unique_case_ids = len(case_ids) == len(set(case_ids))
    traces_created_non_empty = True
    jsonl_valid = True
    for case in cases:
        if not isinstance(case, dict):
            traces_created_non_empty = False
            jsonl_valid = False
            continue
        trace_path = Path(str(case.get("trace_path", "")))
        if (not trace_path.exists()) or trace_path.stat().st_size <= 0:
            traces_created_non_empty = False
            jsonl_valid = False
            continue
        try:
            events = _load_trace_events(trace_path)
        except Exception:
            jsonl_valid = False
            continue
        if not events:
            traces_created_non_empty = False
        for index, event in enumerate(events):
            if set(event.keys()) != TRACE_EVENT_KEYS:
                jsonl_valid = False
                break
            if int(event["order"]) != index:
                jsonl_valid = False
                break

    case_ids_set = set(case_ids)
    manifest_required_fields_ok = True
    paired_refs_valid = True
    for case in cases:
        if not isinstance(case, dict):
            manifest_required_fields_ok = False
            continue
        if not str(case.get("scenario_intent", "")).strip():
            manifest_required_fields_ok = False
        inspect_targets = case.get("what_to_inspect_in_trace", [])
        if not isinstance(inspect_targets, list) or not inspect_targets:
            manifest_required_fields_ok = False
        pair = case.get("paired_with")
        if pair is not None and str(pair) not in case_ids_set:
            paired_refs_valid = False

    represented_families = {
        str(case.get("scenario_family"))
        for case in cases
        if isinstance(case, dict)
    }
    diversity_not_single_family = len(represented_families) > 1
    required_families_present = REQUIRED_SCENARIO_FAMILIES.issubset(represented_families)

    return {
        "unique_case_ids": unique_case_ids,
        "traces_created_non_empty": traces_created_non_empty,
        "manifest_required_fields_ok": manifest_required_fields_ok,
        "paired_refs_valid": paired_refs_valid,
        "diversity_not_single_family": diversity_not_single_family,
        "required_families_present": required_families_present,
        "jsonl_valid": jsonl_valid,
    }


def _render_manifest_markdown(manifest: Mapping[str, object]) -> str:
    lines: list[str] = [
        "# Edgy Behavioral Case Battery",
        "",
        f"- generated_at: {manifest['generated_at']}",
        f"- case_count: {manifest['case_count']}",
        f"- traces_dir: {manifest['traces_dir']}",
        "",
        "| case_id | family | paired_with | key_tension_axis | what_to_inspect_in_trace |",
        "|---|---|---|---|---|",
    ]
    for case in manifest["cases"]:
        lines.append(
            "| {case_id} | {family} | {pair} | {axis} | {inspect} |".format(
                case_id=case["case_id"],
                family=case["scenario_family"],
                pair=case["paired_with"] or "-",
                axis=", ".join(case["key_tension_axis"]),
                inspect=", ".join(case["what_to_inspect_in_trace"]),
            )
        )
    lines.append("")
    return "\n".join(lines)


def generate_edgy_behavioral_case_battery(*, output_dir: str | Path) -> dict[str, object]:
    root = Path(output_dir).expanduser().resolve()
    traces_dir = root / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    reset_trace_state()

    runs = [_run_case(case, traces_dir) for case in CASE_BATTERY]
    manifest: dict[str, object] = {
        "battery_name": "Edgy Behavioral Case Battery for Subject Runtime Trace",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "case_count": len(runs),
        "traces_dir": str(traces_dir),
        "scenario_families": sorted({run["scenario_family"] for run in runs}),
        "cases": runs,
    }
    manifest_json_path = root / "battery_manifest.json"
    manifest_md_path = root / "battery_manifest.md"
    manifest_json_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest_md_path.write_text(_render_manifest_markdown(manifest), encoding="utf-8")

    checks = run_battery_sanity_checks(manifest)
    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise RuntimeError(f"battery sanity checks failed: {', '.join(failed)}")

    return {
        "output_dir": str(root),
        "traces_dir": str(traces_dir),
        "manifest_path": str(manifest_json_path),
        "manifest_md_path": str(manifest_md_path),
        "manifest": manifest,
        "checks": checks,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate edgy behavioral runtime-trace battery for manual inspection."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Output directory for traces and manifest files.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print output summary as JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = generate_edgy_behavioral_case_battery(output_dir=args.output_dir)
    if args.json_output:
        print(
            json.dumps(
                {
                    "case_count": result["manifest"]["case_count"],
                    "traces_dir": result["traces_dir"],
                    "manifest_path": result["manifest_path"],
                    "manifest_md_path": result["manifest_md_path"],
                    "checks": result["checks"],
                },
                ensure_ascii=False,
            )
        )
    else:
        print(f"case_count={result['manifest']['case_count']}")
        print(f"traces_dir={result['traces_dir']}")
        print(f"manifest_path={result['manifest_path']}")
        print(f"manifest_md_path={result['manifest_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
