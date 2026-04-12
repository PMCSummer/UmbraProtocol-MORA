from __future__ import annotations

from typing import Any


SEMANTIC_LABEL_RULES: dict[str, dict[str, str]] = {
    "epistemics": {
        "local_state.allowance.claim_strength": "claim_strength_shift",
        "local_state.unit.status": "epistemic_status_shift",
    },
    "t03_hypothesis_competition": {
        "local_state.state.current_leader_hypothesis_id": "leader_changed",
        "local_state.state.convergence_status": "convergence_status_changed",
    },
    "downstream_obedience": {
        "local_state.usability_class": "downstream_obedience_changed",
        "local_state.accepted": "downstream_gate_acceptance_changed",
    },
    "subject_tick": {
        "local_state.state.final_execution_outcome": "execution_outcome_changed",
        "local_state.state.execution_stance": "execution_stance_changed",
    },
}


def _flatten_scalars(value: Any, *, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten_scalars(item, prefix=child_prefix))
        return out
    if isinstance(value, list):
        out = {}
        for idx, item in enumerate(value):
            child_prefix = f"{prefix}[{idx}]"
            out.update(_flatten_scalars(item, prefix=child_prefix))
        return out
    return {prefix: value}


def compute_semantic_diff(
    *,
    module: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    module_local_pre_state_available: bool,
    diff_not_available_reason: str,
    max_records: int = 256,
) -> dict[str, Any]:
    if not module_local_pre_state_available or before is None:
        return {
            "diff_status": "diff_unavailable",
            "basis": {
                "module_local_pre_state_available": False,
                "diff_not_available_reason": diff_not_available_reason or "no_local_pre_state",
            },
            "records": [],
            "total_changed_path_count": 0,
            "semantic_change_count": 0,
            "value_change_nonsemantic_count": 0,
            "no_change_count": 0,
            "records_truncated": False,
            "omitted_records_count": 0,
        }

    before_flat = _flatten_scalars(before or {})
    after_flat = _flatten_scalars(after or {})
    changed_paths = [
        path
        for path in sorted(set(before_flat) | set(after_flat))
        if before_flat.get(path) != after_flat.get(path)
    ]
    labels = SEMANTIC_LABEL_RULES.get(module, {})
    semantic_count = 0
    nonsemantic_count = 0
    records: list[dict[str, Any]] = []
    for path in changed_paths[:max_records]:
        semantic_label = labels.get(path)
        if semantic_label:
            semantic_count += 1
            records.append(
                {
                    "path": path,
                    "before": before_flat.get(path),
                    "after": after_flat.get(path),
                    "change_kind": "semantic_change",
                    "semantic_label": semantic_label,
                }
            )
        else:
            nonsemantic_count += 1
            records.append(
                {
                    "path": path,
                    "before": before_flat.get(path),
                    "after": after_flat.get(path),
                    "change_kind": "value_change_nonsemantic",
                    "semantic_label": None,
                }
            )

    if changed_paths and len(changed_paths) > max_records:
        remaining = len(changed_paths) - max_records
        extra_semantic = sum(1 for path in changed_paths[max_records:] if labels.get(path))
        semantic_count += extra_semantic
        nonsemantic_count += remaining - extra_semantic
        records_truncated = True
        omitted_records_count = remaining
    else:
        records_truncated = False
        omitted_records_count = 0

    if not changed_paths:
        status = "no_change"
        no_change_count = 1
    elif semantic_count > 0:
        status = "semantic_change"
        no_change_count = 0
    else:
        status = "value_change_nonsemantic"
        no_change_count = 0

    return {
        "diff_status": status,
        "basis": {
            "module_local_pre_state_available": True,
            "diff_not_available_reason": "",
        },
        "records": records,
        "total_changed_path_count": len(changed_paths),
        "semantic_change_count": semantic_count,
        "value_change_nonsemantic_count": nonsemantic_count,
        "no_change_count": no_change_count,
        "records_truncated": records_truncated,
        "omitted_records_count": omitted_records_count,
    }
