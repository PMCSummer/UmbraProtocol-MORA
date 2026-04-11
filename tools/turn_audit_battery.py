from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from substrate.epistemics import (
    ClaimPolarity,
    ConfidenceLevel,
    EpistemicStatus,
    EpistemicUnit,
    ModalityClass,
    SourceClass,
)
from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.runtime_topology.models import (
    RuntimeEpistemicCaseInput,
    RuntimeRegulationSharedDomainInput,
)
from substrate.subject_tick import SubjectTickContext, SubjectTickInput
from tools.turn_audit import (
    CONTEXT_BOOL_FLAGS,
    CONTEXT_VALUE_FLAGS,
    build_turn_audit_artifact,
    collect_turn_audit_artifact_to_disk,
    write_turn_audit_artifact,
)
from tools.turn_audit_markdown import render_turn_audit_markdown_from_file


BATTERY_VERSION = "turn_audit_battery_v2"
UNRESOLVED_TOKEN = "UNRESOLVED_FOR_V1"
OVERALL_STATUSES = ("PASS", "PARTIAL", "FAIL", "UNRESOLVED")


@dataclass(frozen=True, slots=True)
class BatteryCase:
    case_id: str
    description: str
    collector_input: dict[str, Any]
    expected_emphasis_verdict: str
    tags: tuple[str, ...] = ()
    replacement_reason: str | None = None


def _build_conflicting_prior_epistemic_unit() -> EpistemicUnit:
    return EpistemicUnit(
        unit_id="battery-prior-epistemic-unit-deny",
        material_id="battery-prior-epistemic-material",
        content="line voltage nominal",
        source_id="battery.prior.reporter",
        source_class=SourceClass.REPORTER,
        modality=ModalityClass.USER_TEXT,
        status=EpistemicStatus.REPORT,
        confidence=ConfidenceLevel.MEDIUM,
        claim_key="line_voltage_nominal",
        claim_polarity=ClaimPolarity.DENY,
        classification_basis="battery seeded prior epistemic unit for conflict-path exercise",
    )


def get_battery_case_registry() -> tuple[BatteryCase, ...]:
    return (
        BatteryCase(
            case_id="bounded_clean_production_turn",
            description="Baseline lawful production contour with no explicit pressure flags.",
            collector_input={
                "case_id": "battery-bounded-clean",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
            },
            expected_emphasis_verdict="mechanistic_integrity",
            tags=("baseline", "production"),
        ),
        BatteryCase(
            case_id="route_boundary_or_nonproduction_case",
            description="Non-production helper route request without explicit allow; expected pre-execution rejection.",
            collector_input={
                "case_id": "battery-route-boundary",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "route_class": "helper_path",
            },
            expected_emphasis_verdict="mechanistic_integrity",
            tags=("route_boundary", "nonproduction", "structural"),
        ),
        BatteryCase(
            case_id="authority_mismatch_repair_detour",
            description="Nearest RT01-backed repair-detour pressure case in v1 collector surfaces.",
            collector_input={
                "case_id": "battery-authority-repair-nearest",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": True,
                "context_flags": {"require_t03_nonconvergence_preservation": True},
            },
            expected_emphasis_verdict="mechanistic_integrity",
            tags=("repair", "detour", "nearest_replacement"),
            replacement_reason=(
                "collector v1 input surface does not expose a direct authority-mismatch toggle; "
                "nearest concrete repair-detour pressure is used."
            ),
        ),
        BatteryCase(
            case_id="downstream_obedience_shared_domain_revalidate",
            description="Nearest RT01-backed revalidate pressure case on existing collector inputs.",
            collector_input={
                "case_id": "battery-downstream-revalidate-nearest",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "context_flags": {"require_s02_boundary_consumer": True},
            },
            expected_emphasis_verdict="claim_honesty",
            tags=("revalidate", "downstream_obedience", "nearest_replacement"),
            replacement_reason=(
                "shared-domain revalidation path via prior runtime state is outside current battery v1 "
                "collector input surface; nearest concrete revalidate pressure is used."
            ),
        ),
        BatteryCase(
            case_id="t01_unresolved_laundering_guard",
            description="T01 consumer pressure with unresolved preference to verify non-laundered bounded behavior.",
            collector_input={
                "case_id": "battery-t01-unresolved-guard",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": True,
                "context_flags": {"require_t01_scene_comparison_consumer": True},
            },
            expected_emphasis_verdict="claim_honesty",
            tags=("t01", "unresolved", "honesty"),
        ),
        BatteryCase(
            case_id="t02_raw_vs_propagated_integrity_pressure",
            description="T02 raw-vs-propagated distinction pressure for path-affecting checkpoint sensitivity.",
            collector_input={
                "case_id": "battery-t02-raw-vs-propagated",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "context_flags": {"require_t02_raw_vs_propagated_distinction": True},
            },
            expected_emphasis_verdict="path_affecting_sensitivity",
            tags=("t02", "integrity", "path_affecting"),
        ),
        BatteryCase(
            case_id="t03_nonconvergence_preservation_honesty",
            description="T03 nonconvergence preservation pressure with explicit bounded-honesty expectation.",
            collector_input={
                "case_id": "battery-t03-nonconvergence",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "context_flags": {"require_t03_nonconvergence_preservation": True},
            },
            expected_emphasis_verdict="claim_honesty",
            tags=("t03", "nonconvergence", "honesty"),
        ),
        BatteryCase(
            case_id="epistemic_unknown_abstain_detour",
            description="Epistemic unknown/abstain admission case expected to enforce revalidation detour via epistemic checkpoint.",
            collector_input={
                "case_id": "battery-epi-unknown-abstain",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": True,
                "epistemic_case_input": {
                    "content": "claim without grounded source basis",
                    "source_id": "battery.epistemic.unknown",
                    "source_class": "unknown",
                    "modality": "unspecified",
                    "confidence_hint": "low",
                    "claim_key": "battery_epistemic_unknown_claim",
                    "claim_polarity": "affirm",
                },
            },
            expected_emphasis_verdict="path_affecting_sensitivity",
            tags=("epistemics", "admission_checkpoint", "unknown", "abstain", "path_affecting"),
        ),
        BatteryCase(
            case_id="epistemic_observation_requirement_block",
            description="Observation-required epistemic case where report input should trigger abstain restriction and guarded path.",
            collector_input={
                "case_id": "battery-epi-observation-required",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "epistemic_case_input": {
                    "content": "operator reports a condition without sensor trace",
                    "source_id": "battery.epistemic.reporter",
                    "source_class": "reporter",
                    "modality": "user_text",
                    "confidence_hint": "medium",
                    "support_note": "reported claim only",
                    "claim_key": "battery_observation_requirement_claim",
                    "claim_polarity": "affirm",
                    "require_observation": True,
                },
            },
            expected_emphasis_verdict="claim_honesty",
            tags=("epistemics", "claim_strength", "observation_required", "restriction_guard"),
        ),
        BatteryCase(
            case_id="epistemic_conflict_no_laundering",
            description="Epistemic conflict case with opposite-polarity prior unit; conflict must stay explicit and non-laundered.",
            collector_input={
                "case_id": "battery-epi-conflict",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": True,
                "epistemic_case_input": {
                    "content": "line voltage nominal",
                    "source_id": "battery.epistemic.current_report",
                    "source_class": "reporter",
                    "modality": "user_text",
                    "confidence_hint": "medium",
                    "claim_key": "line_voltage_nominal",
                    "claim_polarity": "affirm",
                    "prior_units": (_build_conflicting_prior_epistemic_unit(),),
                },
            },
            expected_emphasis_verdict="claim_honesty",
            tags=("epistemics", "conflict", "abstain", "claim_honesty"),
        ),
        BatteryCase(
            case_id="regulation_high_override_scope_detour",
            description="Shared-runtime regulation high override case expected to enforce detour at shared runtime domain checkpoint.",
            collector_input={
                "case_id": "battery-regulation-override-high",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "regulation_shared_domain_input": {
                    "pressure_level": 0.98,
                    "escalation_stage": "critical",
                    "override_scope": "emergency",
                    "no_strong_override_claim": False,
                    "gate_accepted": True,
                    "source_state_ref": "battery.shared_regulation.high_override",
                },
            },
            expected_emphasis_verdict="path_affecting_sensitivity",
            tags=(
                "regulation",
                "override_scope",
                "shared_domain",
                "shared_runtime_domain_checkpoint",
                "path_affecting",
            ),
        ),
        BatteryCase(
            case_id="regulation_no_strong_override_claim_guard",
            description="Shared-runtime regulation guard case where no_strong_override_claim should suppress high-override detour.",
            collector_input={
                "case_id": "battery-regulation-no-strong-override",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "regulation_shared_domain_input": {
                    "pressure_level": 0.92,
                    "escalation_stage": "critical",
                    "override_scope": "emergency",
                    "no_strong_override_claim": True,
                    "gate_accepted": True,
                    "source_state_ref": "battery.shared_regulation.no_strong_override",
                },
            },
            expected_emphasis_verdict="path_affecting_sensitivity",
            tags=(
                "regulation",
                "no_strong_override_claim",
                "shared_domain",
                "shared_runtime_domain_checkpoint",
                "path_affecting",
            ),
        ),
        BatteryCase(
            case_id="regulation_pressure_tradeoff_shift",
            description="Regulation/world-effect pressure case for tradeoff-sensitive bounded routing.",
            collector_input={
                "case_id": "battery-regulation-pressure-shift",
                "energy": 66.0,
                "cognitive": 44.0,
                "safety": 74.0,
                "unresolved_preference": False,
                "context_flags": {"require_world_effect_feedback_for_success_claim": True},
            },
            expected_emphasis_verdict="path_affecting_sensitivity",
            tags=("regulation", "pressure", "tradeoff"),
        ),
    )


def _extract_case_result(
    *,
    case: BatteryCase,
    artifact_path: Path,
    markdown_path: Path,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    verdicts = artifact.get("verdicts", {})
    unresolved = artifact.get("unresolved", [])
    unresolved_count = len(unresolved) if isinstance(unresolved, list) else 1
    epistemics = artifact.get("phase_surfaces", {}).get("epistemics", {})
    regulation = artifact.get("phase_surfaces", {}).get("regulation", {})
    return {
        "case_id": case.case_id,
        "description": case.description,
        "artifact_path": str(artifact_path),
        "markdown_path": str(markdown_path),
        "route_class": artifact.get("route_and_scope", {}).get("route_class", UNRESOLVED_TOKEN),
        "final_execution_outcome": artifact.get("final_outcome", {}).get(
            "final_execution_outcome",
            UNRESOLVED_TOKEN,
        ),
        "overall_verdict": verdicts.get("overall", {}).get("status", UNRESOLVED_TOKEN),
        "mechanistic_integrity": verdicts.get("mechanistic_integrity", {}).get(
            "status",
            UNRESOLVED_TOKEN,
        ),
        "claim_honesty": verdicts.get("claim_honesty", {}).get("status", UNRESOLVED_TOKEN),
        "path_affecting_sensitivity": verdicts.get("path_affecting_sensitivity", {}).get(
            "status",
            UNRESOLVED_TOKEN,
        ),
        "epistemic_status": (
            epistemics.get("epistemic_status", UNRESOLVED_TOKEN)
            if isinstance(epistemics, dict)
            else UNRESOLVED_TOKEN
        ),
        "epistemic_should_abstain": (
            epistemics.get("epistemic_should_abstain", UNRESOLVED_TOKEN)
            if isinstance(epistemics, dict)
            else UNRESOLVED_TOKEN
        ),
        "epistemic_claim_strength": (
            epistemics.get("epistemic_claim_strength", UNRESOLVED_TOKEN)
            if isinstance(epistemics, dict)
            else UNRESOLVED_TOKEN
        ),
        "regulation_override_scope": (
            regulation.get("regulation_override_scope", UNRESOLVED_TOKEN)
            if isinstance(regulation, dict)
            else UNRESOLVED_TOKEN
        ),
        "regulation_no_strong_override_claim": (
            regulation.get("regulation_no_strong_override_claim", UNRESOLVED_TOKEN)
            if isinstance(regulation, dict)
            else UNRESOLVED_TOKEN
        ),
        "regulation_gate_accepted": (
            regulation.get("regulation_gate_accepted", UNRESOLVED_TOKEN)
            if isinstance(regulation, dict)
            else UNRESOLVED_TOKEN
        ),
        "unresolved_count": unresolved_count,
        "expected_emphasis_verdict": case.expected_emphasis_verdict,
        "tags": list(case.tags),
        "replacement_reason": case.replacement_reason,
        "failed_generation": False,
    }


def _extract_case_failure(
    *,
    case: BatteryCase,
    artifact_path: Path,
    markdown_path: Path,
    exc: Exception,
) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "description": case.description,
        "artifact_path": str(artifact_path),
        "markdown_path": str(markdown_path),
        "route_class": UNRESOLVED_TOKEN,
        "final_execution_outcome": UNRESOLVED_TOKEN,
        "overall_verdict": "FAIL",
        "mechanistic_integrity": UNRESOLVED_TOKEN,
        "claim_honesty": UNRESOLVED_TOKEN,
        "path_affecting_sensitivity": UNRESOLVED_TOKEN,
        "epistemic_status": UNRESOLVED_TOKEN,
        "epistemic_should_abstain": UNRESOLVED_TOKEN,
        "epistemic_claim_strength": UNRESOLVED_TOKEN,
        "regulation_override_scope": UNRESOLVED_TOKEN,
        "regulation_no_strong_override_claim": UNRESOLVED_TOKEN,
        "regulation_gate_accepted": UNRESOLVED_TOKEN,
        "unresolved_count": 1,
        "expected_emphasis_verdict": case.expected_emphasis_verdict,
        "tags": list(case.tags),
        "replacement_reason": case.replacement_reason,
        "failed_generation": True,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }


def _build_index_json(*, output_dir: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    fails = [case["case_id"] for case in cases if case.get("overall_verdict") == "FAIL"]
    partial = [case["case_id"] for case in cases if case.get("overall_verdict") == "PARTIAL"]
    unresolved = [
        case["case_id"]
        for case in cases
        if case.get("overall_verdict") == "UNRESOLVED" or int(case.get("unresolved_count", 0)) > 0
    ]
    return {
        "battery_version": BATTERY_VERSION,
        "case_count": len(cases),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "cases_with_fail": fails,
        "cases_with_partial": partial,
        "cases_with_unresolved": unresolved,
        "cases": cases,
    }


def _build_index_markdown(index: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Turn Audit Battery V2")
    lines.append(f"- battery_version: `{index['battery_version']}`")
    lines.append(f"- generated_at: `{index['generated_at']}`")
    lines.append(f"- output_directory: `{index['output_dir']}`")
    lines.append(f"- case_count: `{index['case_count']}`")
    lines.append("")
    lines.append(
        "| case_id | route_class | final outcome | overall | mechanistic | claim_honesty | path_affecting | epistemic_status | epistemic_should_abstain | epistemic_claim_strength | regulation_override_scope | regulation_no_strong_override_claim | regulation_gate_accepted | unresolved |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for case in index["cases"]:
        lines.append(
            "| "
            f"`{case['case_id']}` | "
            f"`{case.get('route_class', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('final_execution_outcome', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('overall_verdict', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('mechanistic_integrity', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('claim_honesty', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('path_affecting_sensitivity', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('epistemic_status', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('epistemic_should_abstain', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('epistemic_claim_strength', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('regulation_override_scope', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('regulation_no_strong_override_claim', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('regulation_gate_accepted', UNRESOLVED_TOKEN)}` | "
            f"`{case.get('unresolved_count', UNRESOLVED_TOKEN)}` |"
        )
    lines.append("")
    lines.append("## Failed / partial / unresolved cases")
    lines.append(f"- failed: {', '.join(index['cases_with_fail']) if index['cases_with_fail'] else 'none'}")
    lines.append(f"- partial: {', '.join(index['cases_with_partial']) if index['cases_with_partial'] else 'none'}")
    lines.append(
        f"- unresolved: {', '.join(index['cases_with_unresolved']) if index['cases_with_unresolved'] else 'none'}"
    )
    return "\n".join(lines).rstrip() + "\n"


def _resolve_selected_cases(case_filter: list[str] | None) -> tuple[BatteryCase, ...]:
    registry = get_battery_case_registry()
    if not case_filter:
        return registry
    requested = set(case_filter)
    mapping = {case.case_id: case for case in registry}
    unknown = sorted(requested - set(mapping))
    if unknown:
        raise ValueError(f"unknown case ids: {', '.join(unknown)}")
    return tuple(mapping[item] for item in case_filter)


def _coerce_route_class(route_class: RuntimeRouteClass | str) -> RuntimeRouteClass:
    if isinstance(route_class, RuntimeRouteClass):
        return route_class
    return RuntimeRouteClass(route_class)


def _build_context_from_flags(context_flags: dict[str, object] | None) -> SubjectTickContext | None:
    if not context_flags:
        return None
    kwargs: dict[str, object] = {}
    for key, value in context_flags.items():
        if key in CONTEXT_BOOL_FLAGS:
            kwargs[key] = bool(value)
            continue
        if key in CONTEXT_VALUE_FLAGS:
            kwargs[key] = value
            continue
        raise ValueError(f"unsupported context flag for battery case: {key}")
    return SubjectTickContext(**kwargs)


def _build_epistemic_case_input(
    payload: dict[str, Any] | RuntimeEpistemicCaseInput | None,
) -> RuntimeEpistemicCaseInput | None:
    if payload is None:
        return None
    if isinstance(payload, RuntimeEpistemicCaseInput):
        return payload
    if not isinstance(payload, dict):
        raise TypeError("epistemic_case_input must be a dict or RuntimeEpistemicCaseInput")
    prior_units = payload.get("prior_units")
    if prior_units is not None and not isinstance(prior_units, tuple):
        prior_units = tuple(prior_units)
    return RuntimeEpistemicCaseInput(
        content=payload.get("content"),
        source_id=payload.get("source_id"),
        source_class=payload.get("source_class"),
        modality=payload.get("modality"),
        confidence_hint=payload.get("confidence_hint"),
        support_note=payload.get("support_note"),
        contestation_note=payload.get("contestation_note"),
        claim_key=payload.get("claim_key"),
        claim_polarity=payload.get("claim_polarity"),
        require_observation=payload.get("require_observation"),
        prior_units=prior_units,
    )


def _build_regulation_shared_domain_input(
    payload: dict[str, Any] | RuntimeRegulationSharedDomainInput | None,
) -> RuntimeRegulationSharedDomainInput | None:
    if payload is None:
        return None
    if isinstance(payload, RuntimeRegulationSharedDomainInput):
        return payload
    if not isinstance(payload, dict):
        raise TypeError(
            "regulation_shared_domain_input must be a dict or RuntimeRegulationSharedDomainInput"
        )
    return RuntimeRegulationSharedDomainInput(
        pressure_level=payload.get("pressure_level"),
        escalation_stage=payload.get("escalation_stage"),
        override_scope=payload.get("override_scope"),
        no_strong_override_claim=payload.get("no_strong_override_claim"),
        gate_accepted=payload.get("gate_accepted"),
        source_state_ref=payload.get("source_state_ref"),
    )


def _collect_case_artifact_to_disk(
    *,
    case: BatteryCase,
    artifact_path: Path,
) -> tuple[Path, dict[str, object]]:
    case_payload = dict(case.collector_input)
    required = ("case_id", "energy", "cognitive", "safety", "unresolved_preference")
    missing = [item for item in required if item not in case_payload]
    if missing:
        raise ValueError(f"missing collector input fields for case '{case.case_id}': {', '.join(missing)}")

    case_id = str(case_payload.pop("case_id"))
    energy = float(case_payload.pop("energy"))
    cognitive = float(case_payload.pop("cognitive"))
    safety = float(case_payload.pop("safety"))
    unresolved_preference = bool(case_payload.pop("unresolved_preference"))

    context_flags = case_payload.pop("context_flags", None)
    route_class = case_payload.pop("route_class", RuntimeRouteClass.PRODUCTION_CONTOUR.value)
    allow_helper_route = bool(case_payload.pop("allow_helper_route", False))
    allow_test_only_route = bool(case_payload.pop("allow_test_only_route", False))
    allow_non_production_consumer_opt_in = bool(
        case_payload.pop("allow_non_production_consumer_opt_in", False)
    )
    persist_via_f01 = bool(case_payload.pop("persist_via_f01", False))
    seam_contract_path = case_payload.pop("seam_contract_path", None)
    runtime_state = case_payload.pop("runtime_state", None)
    transition_id = case_payload.pop("transition_id", None)
    requested_at = case_payload.pop("requested_at", None)
    raw_cause_chain = case_payload.pop("cause_chain", ("turn-audit-battery", case.case_id))

    epistemic_case_input = _build_epistemic_case_input(case_payload.pop("epistemic_case_input", None))
    regulation_shared_domain_input = _build_regulation_shared_domain_input(
        case_payload.pop("regulation_shared_domain_input", None)
    )

    if case_payload:
        unknown = ", ".join(sorted(case_payload))
        raise ValueError(f"unsupported collector input fields for case '{case.case_id}': {unknown}")

    if epistemic_case_input is None and regulation_shared_domain_input is None:
        kwargs: dict[str, object] = {
            "case_id": case_id,
            "energy": energy,
            "cognitive": cognitive,
            "safety": safety,
            "unresolved_preference": unresolved_preference,
            "context_flags": context_flags,
            "output_path": artifact_path,
            "route_class": route_class,
            "allow_helper_route": allow_helper_route,
            "allow_test_only_route": allow_test_only_route,
            "allow_non_production_consumer_opt_in": allow_non_production_consumer_opt_in,
            "persist_via_f01": persist_via_f01,
        }
        if seam_contract_path is not None:
            kwargs["seam_contract_path"] = seam_contract_path
        path, artifact = collect_turn_audit_artifact_to_disk(**kwargs)
        return path, artifact

    tick_input = SubjectTickInput(
        case_id=case_id,
        energy=energy,
        cognitive=cognitive,
        safety=safety,
        unresolved_preference=unresolved_preference,
    )
    context = _build_context_from_flags(context_flags)
    dispatch_result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=tick_input,
            context=context,
            epistemic_case_input=epistemic_case_input,
            regulation_shared_domain_input=regulation_shared_domain_input,
            route_class=_coerce_route_class(route_class),
            allow_helper_route=allow_helper_route,
            allow_test_only_route=allow_test_only_route,
            allow_non_production_consumer_opt_in=allow_non_production_consumer_opt_in,
            persist_via_f01=persist_via_f01,
            runtime_state=runtime_state,
            transition_id=transition_id,
            requested_at=requested_at,
            cause_chain=(
                tuple(raw_cause_chain)
                if isinstance(raw_cause_chain, (tuple, list))
                else (str(raw_cause_chain),)
            ),
        )
    )
    if seam_contract_path is None:
        artifact = build_turn_audit_artifact(result=dispatch_result)
    else:
        artifact = build_turn_audit_artifact(
            result=dispatch_result,
            seam_contract_path=str(seam_contract_path),
        )
    path = write_turn_audit_artifact(artifact=artifact, output_path=artifact_path)
    return path, artifact


def run_turn_audit_battery(
    *,
    output_dir: str | Path,
    case_filter: list[str] | None = None,
) -> dict[str, Any]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    cases = _resolve_selected_cases(case_filter)
    entries: list[dict[str, Any]] = []
    for case in cases:
        artifact_path = target_dir / f"{case.case_id}.json"
        markdown_path = target_dir / f"{case.case_id}.md"
        try:
            _, artifact = _collect_case_artifact_to_disk(
                case=case,
                artifact_path=artifact_path,
            )
            render_turn_audit_markdown_from_file(
                artifact_path=artifact_path,
                output_markdown_path=markdown_path,
            )
            entries.append(
                _extract_case_result(
                    case=case,
                    artifact_path=artifact_path,
                    markdown_path=markdown_path,
                    artifact=artifact,
                )
            )
        except Exception as exc:
            entries.append(
                _extract_case_failure(
                    case=case,
                    artifact_path=artifact_path,
                    markdown_path=markdown_path,
                    exc=exc,
                )
            )

    index = _build_index_json(output_dir=target_dir, cases=entries)
    index_path = target_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    index_md = _build_index_markdown(index)
    index_md_path = target_dir / "index.md"
    index_md_path.write_text(index_md, encoding="utf-8")

    return {
        "output_dir": str(target_dir),
        "index_json_path": str(index_path),
        "index_markdown_path": str(index_md_path),
        "index": index,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Turn Audit Battery Runner v2")
    parser.add_argument("--output-dir", required=True, help="directory for battery artifacts and index files")
    parser.add_argument(
        "--cases",
        help="optional comma-separated case ids; default runs full fixed registry",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    case_filter = None
    if args.cases:
        case_filter = [item.strip() for item in args.cases.split(",") if item.strip()]
    run = run_turn_audit_battery(
        output_dir=args.output_dir,
        case_filter=case_filter,
    )
    index = run["index"]
    counts = {status: 0 for status in OVERALL_STATUSES}
    for case in index["cases"]:
        status = case.get("overall_verdict")
        if status in counts:
            counts[status] += 1
    print(f"output_dir={run['output_dir']}")
    print(f"case_count={index['case_count']}")
    print(
        "overall_counts="
        f"PASS:{counts['PASS']},PARTIAL:{counts['PARTIAL']},FAIL:{counts['FAIL']},UNRESOLVED:{counts['UNRESOLVED']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
