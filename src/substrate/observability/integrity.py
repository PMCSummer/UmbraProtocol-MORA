from __future__ import annotations

from typing import Any

from substrate.observability.collector import TickTraceBundle
from substrate.observability.schema import EVENT_CLASS_ALLOWED, validate_event_schema


DIFF_STATUS_ALLOWED = {
    "semantic_change",
    "value_change_nonsemantic",
    "no_change",
    "diff_unavailable",
}


def run_integrity_checks(bundle: TickTraceBundle) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    seen_span_ids: set[str] = set()
    event_by_span: dict[str, dict[str, Any]] = {}

    expected_order_index = 0
    for event in bundle.events:
        schema_errors = validate_event_schema(event)
        for schema_error in schema_errors:
            errors.append(f"schema_invalid:{schema_error}")

        event_class = event.get("event_class")
        if event_class not in EVENT_CLASS_ALLOWED:
            errors.append(f"invalid_event_class:{event_class}")

        span_id = event.get("span_id")
        if isinstance(span_id, str):
            if span_id in seen_span_ids:
                errors.append(f"duplicate_span:{span_id}")
            seen_span_ids.add(span_id)
            event_by_span[span_id] = event

        order_index = event.get("order_index")
        if order_index != expected_order_index:
            errors.append(
                f"ordering_gap:expected={expected_order_index},actual={order_index}"
            )
            expected_order_index = order_index if isinstance(order_index, int) else expected_order_index
        expected_order_index += 1

    for event in bundle.events:
        span_id = event.get("span_id")
        parent_span_id = event.get("parent_span_id")
        if parent_span_id is not None and parent_span_id not in event_by_span:
            errors.append(
                f"broken_parent_span_ref:event={span_id},parent={parent_span_id}"
            )
        for ref in event.get("upstream_refs", []):
            if ref not in event_by_span:
                errors.append(f"broken_causal_ref:upstream:{span_id}->{ref}")
        for ref in event.get("downstream_refs", []):
            if ref not in event_by_span:
                errors.append(f"broken_causal_ref:downstream:{span_id}->{ref}")

        for artifact_ref in event.get("artifact_refs", []):
            if not isinstance(artifact_ref, str) or not artifact_ref:
                errors.append(f"unresolved_artifact_reference:event={span_id}")
                continue
            if artifact_ref.startswith("module_snapshots/"):
                leaf = artifact_ref.split("/", 1)[1]
                module_name = leaf.split(".", 1)[0]
                if module_name not in bundle.module_snapshots:
                    errors.append(
                        f"unresolved_artifact_reference:event={span_id},artifact={artifact_ref}"
                    )
            elif artifact_ref.startswith("diffs/"):
                leaf = artifact_ref.split("/", 1)[1]
                module_name = leaf.split(".", 1)[0]
                if module_name not in bundle.diffs:
                    errors.append(
                        f"unresolved_artifact_reference:event={span_id},artifact={artifact_ref}"
                    )

    snapshot_events = [
        event
        for event in bundle.events
        if event.get("event_class") in {"snapshot", "decision", "topology_routing"}
    ]
    for event in snapshot_events:
        module = event.get("module")
        if module == "tick":
            continue
        if module not in bundle.module_snapshots:
            errors.append(f"missing_snapshot_for_module:{module}")

    for module, module_diff in bundle.diffs.items():
        if not isinstance(module_diff, dict):
            errors.append(f"malformed_diff:not_object:{module}")
            continue
        diff_status = module_diff.get("diff_status")
        if diff_status not in DIFF_STATUS_ALLOWED:
            errors.append(f"malformed_diff:invalid_status:{module}")
        basis = module_diff.get("basis")
        if not isinstance(basis, dict):
            errors.append(f"malformed_diff:missing_basis:{module}")
        else:
            if not isinstance(basis.get("module_local_pre_state_available"), bool):
                errors.append(f"malformed_diff:invalid_basis_pre_state_flag:{module}")
            if not isinstance(basis.get("diff_not_available_reason"), str):
                errors.append(f"malformed_diff:invalid_basis_reason:{module}")

        records = module_diff.get("records")
        if not isinstance(records, list):
            errors.append(f"malformed_diff:records_not_list:{module}")
            continue
        for entry in records:
            if not isinstance(entry, dict):
                errors.append(f"malformed_diff:entry_not_object:{module}")
                continue
            for key in ("path", "before", "after", "change_kind", "semantic_label"):
                if key not in entry:
                    errors.append(f"malformed_diff:missing_{key}:{module}")
            if entry.get("change_kind") not in {"semantic_change", "value_change_nonsemantic"}:
                errors.append(f"malformed_diff:invalid_change_kind:{module}")

        for key in (
            "total_changed_path_count",
            "semantic_change_count",
            "value_change_nonsemantic_count",
            "no_change_count",
            "omitted_records_count",
        ):
            value = module_diff.get(key)
            if not isinstance(value, int) or value < 0:
                errors.append(f"malformed_diff:invalid_{key}:{module}")
        if not isinstance(module_diff.get("records_truncated"), bool):
            errors.append(f"malformed_diff:invalid_records_truncated:{module}")

    if not bundle.causal_edges:
        warnings.append("no_causal_edges_recorded")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
