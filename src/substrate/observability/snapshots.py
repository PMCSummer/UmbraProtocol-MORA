from __future__ import annotations

from typing import Any


COMPACT_KEYS: dict[str, tuple[str, ...]] = {
    "runtime_topology": ("decision", "tick_graph", "dispatch_lineage"),
    "subject_tick": ("state", "downstream_gate"),
    "world_adapter": ("state", "gate", "partial_known", "abstain"),
    "world_entry_contract": ("episode", "w01_admission", "claim_admissions", "reason"),
    "epistemics": ("allowance", "telemetry"),
    "regulation": ("state", "tradeoff", "telemetry"),
    "downstream_obedience": ("accepted", "usability_class", "restrictions", "reason"),
    "t01_semantic_field": ("state", "gate", "reason"),
    "t02_relation_binding": ("state", "gate", "reason"),
    "t03_hypothesis_competition": ("state", "gate", "reason"),
    "t04_attention_schema": ("state", "gate", "reason"),
}


def _compact_scalar_walk(value: Any, *, depth: int = 0, max_depth: int = 2) -> Any:
    if depth >= max_depth:
        if isinstance(value, dict):
            return f"<object:{len(value)}>"
        if isinstance(value, list):
            return f"<list:{len(value)}>"
        return value
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in list(value.items())[:24]:
            out[str(key)] = _compact_scalar_walk(item, depth=depth + 1, max_depth=max_depth)
        return out
    if isinstance(value, list):
        return [_compact_scalar_walk(item, depth=depth + 1, max_depth=max_depth) for item in value[:24]]
    return value


def build_compact_snapshot(*, module: str, deep_snapshot: dict[str, Any]) -> dict[str, Any]:
    keys = COMPACT_KEYS.get(module, tuple())
    if not keys:
        return _compact_scalar_walk(deep_snapshot, max_depth=2)
    compact: dict[str, Any] = {}
    for key in keys:
        if key in deep_snapshot:
            compact[key] = _compact_scalar_walk(deep_snapshot[key], max_depth=2)
    if not compact:
        return _compact_scalar_walk(deep_snapshot, max_depth=2)
    return compact
