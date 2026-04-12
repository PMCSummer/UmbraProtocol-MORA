from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from substrate.observability.adapters import ModuleObservation
from substrate.observability.context import ObservabilityContext
from substrate.observability.contracts import (
    section_normalized,
    section_not_available,
)
from substrate.observability.diffs import compute_semantic_diff
from substrate.observability.schema import validate_event_schema
from substrate.observability.snapshots import build_compact_snapshot
from substrate.observability.utils import to_jsonable


@dataclass
class TickTraceBundle:
    tick_id: str
    trace_id: str
    events: list[dict[str, Any]]
    module_snapshots: dict[str, dict[str, Any]]
    diffs: dict[str, dict[str, Any]]
    causal_edges: list[dict[str, Any]]
    compact_summary: dict[str, Any]


@dataclass
class TickTraceCollector:
    tick_id: str
    trace_id: str
    _context: ObservabilityContext = field(init=False)
    _events: list[dict[str, Any]] = field(default_factory=list)
    _events_by_span: dict[str, dict[str, Any]] = field(default_factory=dict)
    _module_snapshots: dict[str, dict[str, Any]] = field(default_factory=dict)
    _diffs: dict[str, dict[str, Any]] = field(default_factory=dict)
    _causal_edges: list[dict[str, Any]] = field(default_factory=list)
    _integrity_errors: list[str] = field(default_factory=list)
    _lifecycle_start_span_id: str | None = None

    def __post_init__(self) -> None:
        self._context = ObservabilityContext(
            tick_id=self.tick_id,
            trace_id=self.trace_id,
        )

    @property
    def events(self) -> list[dict[str, Any]]:
        return self._events

    @property
    def integrity_errors(self) -> list[str]:
        return list(self._integrity_errors)

    def _emit(self, event: dict[str, Any], *, edge_type: str = "causal_parent") -> dict[str, Any]:
        errors = validate_event_schema(event)
        if errors:
            self._integrity_errors.extend(
                [f"event[{event.get('module')}:{event.get('event_type')}]: {err}" for err in errors]
            )
        self._events.append(event)
        self._events_by_span[event["span_id"]] = event

        parent_span_id = event.get("parent_span_id")
        if isinstance(parent_span_id, str):
            self._causal_edges.append(
                {
                    "tick_id": self.tick_id,
                    "trace_id": self.trace_id,
                    "edge_type": edge_type,
                    "from_span_id": parent_span_id,
                    "to_span_id": event["span_id"],
                }
            )
            parent_event = self._events_by_span.get(parent_span_id)
            if parent_event is not None:
                parent_event.setdefault("downstream_refs", []).append(event["span_id"])
        return event

    def record_lifecycle_start(self, *, markers: dict[str, Any] | None = None) -> str:
        event = self._context.make_event(
            module="tick",
            stage="lifecycle",
            event_type="tick_started",
            event_class="lifecycle",
            parent_span_id=None,
            markers=section_normalized(to_jsonable(markers or {})),
            canonical=True,
        )
        self._emit(event)
        self._lifecycle_start_span_id = event["span_id"]
        return event["span_id"]

    def record_handoff(
        self,
        *,
        from_span_id: str,
        from_module: str,
        handoff_to: str,
        stage: str,
        contract_id: str | None,
        markers: dict[str, Any] | None = None,
    ) -> str:
        handoff_event = self._context.make_event(
            module=from_module,
            stage=stage,
            event_type=f"handoff_to_{handoff_to}",
            event_class="handoff_contract_dispatch",
            parent_span_id=from_span_id,
            markers=section_normalized(
                to_jsonable(
                    {
                        "handoff_to": handoff_to,
                        **(markers or {}),
                    }
                )
            ),
            contract_id=contract_id,
            upstream_refs=[from_span_id],
            canonical=True,
        )
        self._emit(handoff_event, edge_type="handoff")
        return handoff_event["span_id"]

    def record_module_run(
        self,
        *,
        observation: ModuleObservation,
        parent_span_id: str,
        transition_id: str | None,
        contract_id: str | None,
        decision_id: str | None,
        artifact_refs: list[str] | None = None,
    ) -> dict[str, str]:
        module = observation.module
        stage = observation.stage

        enter_event = self._context.make_event(
            module=module,
            stage=stage,
            event_type=f"{module}_module_enter",
            event_class="lifecycle",
            parent_span_id=parent_span_id,
            inputs=section_normalized(observation.inputs),
            outputs=section_normalized(observation.outputs),
            markers=section_normalized(
                {
                    "module_adapter": observation.markers.get("module_adapter"),
                }
            ),
            transition_id=transition_id,
            contract_id=contract_id,
            decision_id=decision_id,
            canonical=True,
            upstream_refs=[parent_span_id],
        )
        self._emit(enter_event)
        active_span_id = enter_event["span_id"]

        if observation.local_pre_state_available and observation.local_pre_state is not None:
            pre_state_section = section_normalized(observation.local_pre_state)
        else:
            pre_state_section = section_not_available(observation.local_pre_state_reason)

        pre_event = self._context.make_event(
            module=module,
            stage=stage,
            event_type=f"{module}_local_pre_state_capture",
            event_class="snapshot",
            parent_span_id=active_span_id,
            state_before=section_not_available("not_applicable_before_pre_capture"),
            state_after=pre_state_section,
            markers=section_normalized(
                {
                    "local_pre_state_available": observation.local_pre_state_available,
                    "local_pre_state_reason": observation.local_pre_state_reason,
                }
            ),
            transition_id=transition_id,
            contract_id=contract_id,
            decision_id=decision_id,
            upstream_refs=[active_span_id],
            canonical=True,
        )
        self._emit(pre_event)
        active_span_id = pre_event["span_id"]

        if observation.decision:
            decision_event = self._context.make_event(
                module=module,
                stage=stage,
                event_type=f"{module}_decision_recorded",
                event_class="decision",
                parent_span_id=active_span_id,
                decision=section_normalized(observation.decision),
                markers=section_normalized({"decision_raw": observation.decision_raw}),
                upstream_refs=[active_span_id],
                canonical=True,
            )
            self._emit(decision_event)
            active_span_id = decision_event["span_id"]

        if observation.constraints:
            constraint_event = self._context.make_event(
                module=module,
                stage=stage,
                event_type=f"{module}_constraints_recorded",
                event_class="constraint",
                parent_span_id=active_span_id,
                constraints=section_normalized(observation.constraints),
                markers=section_normalized({"constraint_present": True}),
                upstream_refs=[active_span_id],
                canonical=True,
            )
            self._emit(constraint_event)
            active_span_id = constraint_event["span_id"]

        if observation.failures or observation.degradations:
            failure_event = self._context.make_event(
                module=module,
                stage=stage,
                event_type=f"{module}_failure_degradation_recorded",
                event_class="failure_degradation",
                parent_span_id=active_span_id,
                failures=section_normalized(observation.failures),
                degradations=section_normalized(observation.degradations),
                markers=section_normalized({"degraded_or_failure": True}),
                upstream_refs=[active_span_id],
                canonical=True,
            )
            self._emit(failure_event)
            active_span_id = failure_event["span_id"]

        if observation.provenance:
            provenance_event = self._context.make_event(
                module=module,
                stage=stage,
                event_type=f"{module}_provenance_recorded",
                event_class="provenance_evidence",
                parent_span_id=active_span_id,
                provenance=section_normalized(observation.provenance),
                outputs=section_normalized(
                    {"provenance_fields": tuple(sorted(observation.provenance.keys()))}
                ),
                upstream_refs=[active_span_id],
                canonical=True,
            )
            self._emit(provenance_event)
            active_span_id = provenance_event["span_id"]

        if observation.ownership:
            ownership_event = self._context.make_event(
                module=module,
                stage=stage,
                event_type=f"{module}_ownership_recorded",
                event_class="provenance_evidence",
                parent_span_id=active_span_id,
                ownership=section_normalized(observation.ownership),
                upstream_refs=[active_span_id],
                canonical=True,
            )
            self._emit(ownership_event)
            active_span_id = ownership_event["span_id"]

        post_event = self._context.make_event(
            module=module,
            stage=stage,
            event_type=f"{module}_local_post_state_capture",
            event_class=observation.event_class,
            parent_span_id=active_span_id,
            state_before=pre_state_section,
            state_after=section_normalized(observation.local_post_state),
            outputs=section_normalized(observation.outputs),
            markers=section_normalized(observation.markers),
            transition_id=transition_id,
            contract_id=contract_id,
            decision_id=decision_id,
            artifact_refs=[] if artifact_refs is None else list(artifact_refs),
            upstream_refs=[active_span_id],
            canonical=True,
        )
        self._emit(post_event)

        deep_snapshot_source = (
            observation.snapshot_state
            if isinstance(observation.snapshot_state, dict)
            else observation.local_post_state.get("local_state", {})
        )
        deep_snapshot = to_jsonable(deep_snapshot_source)
        compact_snapshot = to_jsonable(
            build_compact_snapshot(module=module, deep_snapshot=deep_snapshot)
        )
        self._module_snapshots[module] = {
            "span_id": post_event["span_id"],
            "compact": compact_snapshot,
            "deep": deep_snapshot,
        }

        semantic_diff = to_jsonable(
            compute_semantic_diff(
                module=module,
                before=observation.local_pre_state if observation.local_pre_state_available else None,
                after=observation.local_post_state,
                module_local_pre_state_available=observation.local_pre_state_available,
                diff_not_available_reason=observation.local_pre_state_reason,
            )
        )
        self._diffs[module] = semantic_diff

        diff_event = self._context.make_event(
            module=module,
            stage=stage,
            event_type=f"{module}_diff_built",
            event_class="diff_state_change",
            parent_span_id=post_event["span_id"],
            state_before=pre_state_section,
            state_after=section_normalized(observation.local_post_state),
            outputs=section_normalized(
                {
                    "diff_status": semantic_diff["diff_status"],
                    "semantic_change_count": semantic_diff["semantic_change_count"],
                    "value_change_nonsemantic_count": semantic_diff["value_change_nonsemantic_count"],
                    "total_changed_path_count": semantic_diff["total_changed_path_count"],
                }
            ),
            markers=section_normalized(
                {
                    "records_truncated": semantic_diff["records_truncated"],
                    "omitted_records_count": semantic_diff["omitted_records_count"],
                }
            ),
            upstream_refs=[post_event["span_id"]],
            derived_from=[post_event["span_id"]],
            canonical=False,
            derived=True,
        )
        self._emit(diff_event, edge_type="derived_from")

        exit_event = self._context.make_event(
            module=module,
            stage=stage,
            event_type=f"{module}_module_exit",
            event_class="lifecycle",
            parent_span_id=diff_event["span_id"],
            markers=section_normalized(
                {
                    "module_local_pre_state_available": observation.local_pre_state_available,
                    "diff_status": semantic_diff["diff_status"],
                }
            ),
            upstream_refs=[diff_event["span_id"]],
            canonical=True,
        )
        self._emit(exit_event)

        return {
            "enter_span_id": enter_event["span_id"],
            "post_span_id": post_event["span_id"],
            "diff_span_id": diff_event["span_id"],
            "exit_span_id": exit_event["span_id"],
        }

    def record_lifecycle_end(self, *, parent_span_id: str, markers: dict[str, Any] | None = None) -> str:
        event = self._context.make_event(
            module="tick",
            stage="lifecycle",
            event_type="tick_completed",
            event_class="lifecycle",
            parent_span_id=parent_span_id,
            markers=section_normalized(to_jsonable(markers or {})),
            upstream_refs=[parent_span_id],
            canonical=True,
            summarized=True,
        )
        self._emit(event)
        return event["span_id"]

    def build(self) -> TickTraceBundle:
        module_order = [
            event["module"]
            for event in self._events
            if event.get("event_type", "").endswith("_module_enter")
        ]
        class_counts: dict[str, int] = {}
        for event in self._events:
            event_class = event["event_class"]
            class_counts[event_class] = class_counts.get(event_class, 0) + 1

        diff_status_counts: dict[str, int] = {}
        missing_local_pre_state_modules: list[str] = []
        for module, diff_report in self._diffs.items():
            status = str(diff_report.get("diff_status"))
            diff_status_counts[status] = diff_status_counts.get(status, 0) + 1
            basis = diff_report.get("basis", {})
            if isinstance(basis, dict) and not basis.get("module_local_pre_state_available", False):
                missing_local_pre_state_modules.append(module)

        summary = {
            "tick_id": self.tick_id,
            "trace_id": self.trace_id,
            "event_count": len(self._events),
            "module_count": len(self._module_snapshots),
            "module_order": module_order,
            "event_class_counts": class_counts,
            "handoff_count": class_counts.get("handoff_contract_dispatch", 0),
            "constraint_event_count": class_counts.get("constraint", 0),
            "failure_degradation_event_count": class_counts.get("failure_degradation", 0),
            "diff_status_counts": diff_status_counts,
            "missing_local_pre_state_modules": sorted(missing_local_pre_state_modules),
            "integrity_error_count": len(self._integrity_errors),
        }
        return TickTraceBundle(
            tick_id=self.tick_id,
            trace_id=self.trace_id,
            events=list(self._events),
            module_snapshots=dict(self._module_snapshots),
            diffs=dict(self._diffs),
            causal_edges=list(self._causal_edges),
            compact_summary=summary,
        )
