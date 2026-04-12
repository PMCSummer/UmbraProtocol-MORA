from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from substrate.observability.adapters import build_core_observations
from substrate.observability.collector import TickTraceBundle, TickTraceCollector
from substrate.observability.integrity import run_integrity_checks
from substrate.observability.storage import write_trace_bundle
from substrate.observability.utils import short_ref, to_jsonable, utc_now_iso
from substrate.runtime_topology import RuntimeDispatchRequest, RuntimeRouteClass, dispatch_runtime_tick
from substrate.subject_tick import SubjectTickInput
from substrate.runtime_topology.models import RuntimeDispatchResult


def build_trace_bundle_from_dispatch_result(
    *,
    result: RuntimeDispatchResult,
    tick_id: str | None = None,
    trace_id: str | None = None,
) -> tuple[TickTraceBundle, dict[str, Any]]:
    if result.subject_tick_result is None:
        raise ValueError("subject_tick_result is required for observability trace bundle")
    effective_tick_id = tick_id or result.subject_tick_result.state.tick_id
    effective_trace_id = trace_id or short_ref("trace", effective_tick_id, utc_now_iso())
    collector = TickTraceCollector(
        tick_id=effective_tick_id,
        trace_id=effective_trace_id,
    )
    lifecycle_start_span_id = collector.record_lifecycle_start(
        markers={
            "runtime_entry": result.bundle.runtime_entry,
            "route_class_requested": result.request.route_class.value,
        }
    )
    observations = build_core_observations(result)
    parent_span_id = lifecycle_start_span_id
    for idx, observation in enumerate(observations):
        run_spans = collector.record_module_run(
            observation=observation,
            parent_span_id=parent_span_id,
            transition_id=short_ref(effective_tick_id, "transition", str(idx)),
            decision_id=short_ref(effective_tick_id, observation.module, "decision", str(idx)),
            contract_id=short_ref(effective_tick_id, observation.module, "contract", str(idx)),
            artifact_refs=[f"module_snapshots/{observation.module}.deep.json"],
        )
        if idx < len(observations) - 1:
            next_observation = observations[idx + 1]
            parent_span_id = collector.record_handoff(
                from_span_id=run_spans["exit_span_id"],
                from_module=observation.module,
                handoff_to=next_observation.module,
                stage=observation.stage,
                contract_id=short_ref("handoff", observation.module, next_observation.module),
                markers={"handoff_chain_index": idx + 1},
            )
        else:
            parent_span_id = run_spans["exit_span_id"]

    collector.record_lifecycle_end(
        parent_span_id=parent_span_id,
        markers={
            "module_count": len(observations),
            "route_binding_consequence": result.decision.route_binding_consequence.value,
        }
    )
    bundle = collector.build()
    integrity = run_integrity_checks(bundle)
    return bundle, integrity


def write_trace_bundle_for_dispatch_result(
    *,
    result: RuntimeDispatchResult,
    output_root: str | Path,
    tick_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    bundle, integrity = build_trace_bundle_from_dispatch_result(
        result=result,
        tick_id=tick_id,
        trace_id=trace_id,
    )
    file_paths = write_trace_bundle(
        bundle=bundle,
        integrity_report=integrity,
        output_root=output_root,
    )
    return {
        "tick_id": bundle.tick_id,
        "trace_id": bundle.trace_id,
        "integrity": integrity,
        **file_paths,
    }


def run_tick_and_write_trace_bundle(
    *,
    case_id: str,
    energy: float,
    cognitive: float,
    safety: float,
    unresolved_preference: bool,
    output_root: str | Path,
    route_class: str = "production_contour",
) -> dict[str, Any]:
    dispatch_result = dispatch_runtime_tick(
        RuntimeDispatchRequest(
            tick_input=SubjectTickInput(
                case_id=case_id,
                energy=energy,
                cognitive=cognitive,
                safety=safety,
                unresolved_preference=unresolved_preference,
            ),
            route_class=RuntimeRouteClass(route_class),
        )
    )
    return write_trace_bundle_for_dispatch_result(
        result=dispatch_result,
        output_root=output_root,
    )


def read_compact_summary(path: str | Path) -> dict[str, Any]:
    summary_path = Path(path)
    return to_jsonable(json.loads(summary_path.read_text(encoding="utf-8")))
