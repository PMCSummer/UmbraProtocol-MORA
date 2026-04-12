from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from substrate.observability.contracts import coerce_section_contract
from substrate.observability.utils import short_ref, utc_now_iso


@dataclass
class ObservabilityContext:
    tick_id: str
    trace_id: str
    _order_index: int = 0
    _span_counter: int = 0
    _module_run_counter: int = 0
    _span_depths: dict[str, int] = field(default_factory=dict)

    def next_order_index(self) -> int:
        order = self._order_index
        self._order_index += 1
        return order

    def new_span(self, *, module: str, parent_span_id: str | None) -> tuple[str, str, int]:
        span_id = short_ref(self.trace_id, "span", str(self._span_counter))
        self._span_counter += 1
        module_run_id = short_ref(self.tick_id, module, "run", str(self._module_run_counter))
        self._module_run_counter += 1
        parent_depth = -1
        if parent_span_id is not None:
            parent_depth = self._span_depths.get(parent_span_id, -1)
        causal_depth = parent_depth + 1
        if causal_depth < 0:
            causal_depth = 0
        self._span_depths[span_id] = causal_depth
        return span_id, module_run_id, causal_depth

    def make_event(
        self,
        *,
        module: str,
        stage: str,
        event_type: str,
        event_class: str,
        parent_span_id: str | None,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        state_before: dict[str, Any] | None = None,
        state_after: dict[str, Any] | None = None,
        decision: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        failures: dict[str, Any] | None = None,
        degradations: dict[str, Any] | None = None,
        markers: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
        ownership: dict[str, Any] | None = None,
        upstream_refs: list[str] | None = None,
        downstream_refs: list[str] | None = None,
        transition_id: str | None = None,
        contract_id: str | None = None,
        decision_id: str | None = None,
        artifact_refs: list[str] | None = None,
        derived_from: list[str] | None = None,
        canonical: bool = True,
        derived: bool = False,
        inferred: bool = False,
        summarized: bool = False,
    ) -> dict[str, Any]:
        span_id, module_run_id, causal_depth = self.new_span(
            module=module,
            parent_span_id=parent_span_id,
        )
        return {
            "tick_id": self.tick_id,
            "trace_id": self.trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "module": module,
            "stage": stage,
            "event_type": event_type,
            "event_class": event_class,
            "timestamp": utc_now_iso(),
            "order_index": self.next_order_index(),
            "causal_depth": causal_depth,
            "inputs": coerce_section_contract(inputs),
            "outputs": coerce_section_contract(outputs),
            "state_before": coerce_section_contract(state_before),
            "state_after": coerce_section_contract(state_after),
            "decision": coerce_section_contract(decision),
            "constraints": coerce_section_contract(constraints),
            "failures": coerce_section_contract(failures),
            "degradations": coerce_section_contract(degradations),
            "markers": coerce_section_contract(markers),
            "provenance": coerce_section_contract(provenance),
            "ownership": coerce_section_contract(ownership),
            "upstream_refs": [] if upstream_refs is None else list(upstream_refs),
            "downstream_refs": [] if downstream_refs is None else list(downstream_refs),
            "module_run_id": module_run_id,
            "transition_id": transition_id,
            "contract_id": contract_id,
            "decision_id": decision_id,
            "artifact_refs": [] if artifact_refs is None else list(artifact_refs),
            "derived_from": [] if derived_from is None else list(derived_from),
            "canonical": canonical,
            "derived": derived,
            "inferred": inferred,
            "summarized": summarized,
        }
