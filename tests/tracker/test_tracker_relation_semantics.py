from __future__ import annotations

import copy
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TRACKER_ROOT = ROOT / "tracker"
if str(TRACKER_ROOT) not in sys.path:
    sys.path.insert(0, str(TRACKER_ROOT))

from roadmap_tracker.model import (  # noqa: E402
    EDGE_RELATION_DEFAULT,
    EDGE_RELATION_LABELS,
    EDGE_RELATION_STYLE_HINTS,
    GraphEdge,
    Phase,
    RoadmapModel,
    phase_objective_text,
)


def _minimal_phase(code: str, title: str, after: str | None = None) -> dict:
    payload = {
        "code": code,
        "title": title,
        "track": "build",
        "line": "misc",
        "status": "later",
        "status_source": "user",
        "spec": {"objective": f"{code} objective", "includes": [], "rationale": "", "excludes": []},
        "notes": "",
        "implemented_after": after,
        "conceptually_after": [],
        "claim_blocked_by": [],
        "validation_state": "planned",
        "claim_role": "core_foundation_or_support",
        "priority_bucket": "historical_foundation",
        "risk_tags": [],
        "claim_state": "unknown",
        "maturity": "L1_theoretical_only",
        "knowledge_card": {},
        "related_node_ids": [],
    }
    if after is not None:
        payload["after"] = after
    return payload


def test_relation_schema_defaults_and_unknown_fallback() -> None:
    missing = GraphEdge.from_dict({"source": "a", "target": "b"})
    assert missing.relation == EDGE_RELATION_DEFAULT

    unknown = GraphEdge.from_dict({"source": "a", "target": "b", "relation": "non_existing_relation"})
    assert unknown.relation == EDGE_RELATION_DEFAULT

    typed = GraphEdge.from_dict({"source": "a", "target": "b", "relation": "gates"})
    assert typed.relation == "gates"
    assert typed.to_dict()["relation"] == "gates"

    legacy = GraphEdge.from_dict({"source": "a", "target": "b", "relation": "blocks_claim"})
    assert legacy.relation == "invalidates"


def test_tracker_roundtrip_preserves_mixed_relation_types() -> None:
    raw = {
        "schema_version": 5,
        "phases": [],
        "graph": {
            "nodes": [
                {"node_id": "node::alpha", "label": "Alpha", "node_type": "mechanism"},
                {"node_id": "node::beta", "label": "Beta", "node_type": "mechanism"},
            ],
            "edges": [
                {"source": "node::alpha", "target": "node::beta", "relation": "requires", "layer": "workflow"},
                {"source": "node::alpha", "target": "node::beta", "relation": "gates", "layer": "workflow"},
                {"source": "node::alpha", "target": "node::beta", "relation": "invalidates", "layer": "validation"},
                {"source": "node::alpha", "target": "node::beta", "relation": "requests_revalidation", "layer": "workflow"},
            ],
        },
    }
    model = RoadmapModel.from_json(copy.deepcopy(raw))
    dumped = model.to_dict()
    relations = [edge["relation"] for edge in dumped["graph"]["edges"]]
    assert "requires" in relations
    assert "gates" in relations
    assert "invalidates" in relations
    assert "requests_revalidation" in relations
    assert len(dumped["graph"]["edges"]) == 4


def test_relation_edit_roundtrip_keeps_updated_value() -> None:
    model = RoadmapModel.from_json(
        {
            "schema_version": 5,
            "phases": [],
            "graph": {
                "nodes": [
                    {"node_id": "node::alpha", "label": "Alpha", "node_type": "mechanism"},
                    {"node_id": "node::beta", "label": "Beta", "node_type": "mechanism"},
                ],
                "edges": [
                    {"source": "node::alpha", "target": "node::beta", "relation": "requires", "layer": "workflow"},
                ],
            },
        }
    )
    model.graph_edges[0].relation = "gates"
    dumped = model.to_dict()
    assert dumped["graph"]["edges"][0]["relation"] == "gates"
    reloaded = RoadmapModel.from_json(dumped)
    assert reloaded.graph_edges[0].relation == "gates"


def test_edge_relation_vocab_defaults_to_explicit_registry_on_save() -> None:
    raw = {
        "schema_version": 4,
        "phases": [],
        "graph": {
            "nodes": [
                {"node_id": "node::alpha", "label": "Alpha", "node_type": "mechanism"},
                {"node_id": "node::beta", "label": "Beta", "node_type": "mechanism"},
            ],
            "edges": [
                {"source": "node::alpha", "target": "node::beta", "layer": "workflow"},
            ],
        },
    }
    model = RoadmapModel.from_json(raw)
    dumped = model.to_dict()
    assert dumped["graph"]["edges"][0]["relation"] == EDGE_RELATION_DEFAULT
    assert dumped["edge_relation_vocab"] == EDGE_RELATION_LABELS


def test_conservative_migration_upgrades_clear_edges_and_keeps_ambiguous_requires() -> None:
    raw = {
        "schema_version": 4,
        "phases": [
            _minimal_phase("R04", "survival force"),
            _minimal_phase("C04", "mode arbitration", after="R04"),
            _minimal_phase("C05", "temporal validity", after="C04"),
            _minimal_phase("S01", "efference", after="C05"),
            _minimal_phase("F01", "foundation"),
            _minimal_phase("F02", "grounding", after="F01"),
        ],
        "graph": {"nodes": [], "edges": []},
    }
    model = RoadmapModel.from_json(raw)
    edges = {(edge.source, edge.target): edge.relation for edge in model.graph_edges}

    assert edges.get(("phase::C04", "phase::C05")) == "arbitrates"
    assert edges.get(("phase::C05", "phase::S01")) == "requests_revalidation"
    assert edges.get(("phase::R04", "phase::C04")) == "overrides_survival"
    assert edges.get(("phase::F01", "phase::F02")) == "requires"


def test_migration_is_stable_on_repeated_runs() -> None:
    raw = {
        "schema_version": 5,
        "phases": [
            _minimal_phase("R04", "survival force"),
            _minimal_phase("C04", "mode arbitration", after="R04"),
            _minimal_phase("C05", "temporal validity", after="C04"),
        ],
        "graph": {"nodes": [], "edges": []},
    }
    model = RoadmapModel.from_json(raw)
    first_relations = [(edge.source, edge.target, edge.relation) for edge in model.graph_edges]
    changed = model.conservative_relation_migration()
    second_relations = [(edge.source, edge.target, edge.relation) for edge in model.graph_edges]

    assert changed == 0
    assert first_relations == second_relations


def test_relation_style_mapping_is_relation_sensitive() -> None:
    assert EDGE_RELATION_STYLE_HINTS["requires"] != EDGE_RELATION_STYLE_HINTS["gates"]
    assert EDGE_RELATION_STYLE_HINTS["requires"] != EDGE_RELATION_STYLE_HINTS["invalidates"]
    assert EDGE_RELATION_STYLE_HINTS["observes_only"] != EDGE_RELATION_STYLE_HINTS["overrides_survival"]


def test_commit_phase_description_idempotent_no_long_form_duplication() -> None:
    phase = Phase.from_dict(
        {
            "code": "C02",
            "title": "scheduler",
            "spec": {
                "objective": "Only this objective should persist.",
                "includes": ["A", "B"],
                "rationale": "Because bounded scope matters.",
                "excludes": ["X"],
            },
            "knowledge_card": {
                "functional_role": "Do one bounded thing.",
                "forbidden_shortcuts": ["Do not duplicate text."],
            },
        }
    )
    seed_objective = phase.spec["objective"]
    assert "Directive:" in phase.rendered_description()

    for _ in range(3):
        phase.spec["objective"] = phase_objective_text(phase)

    assert phase.spec["objective"] == seed_objective
    assert "Directive:" not in phase.spec["objective"]
    assert "Included surfaces:" not in phase.spec["objective"]


def test_phase_selection_editor_uses_raw_objective_text_path() -> None:
    app_source = (TRACKER_ROOT / "roadmap_tracker" / "app.py").read_text(encoding="utf-8")
    assert "self.phase_description_edit.setPlainText(phase_objective_text(phase))" in app_source


def test_json_file_migrated_to_new_relation_vocabulary_shape() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    raw = json.loads(roadmap_path.read_text(encoding="utf-8"))
    edge_relations = [edge.get("relation", EDGE_RELATION_DEFAULT) for edge in raw.get("graph", {}).get("edges", [])]
    assert "arbitrates" in edge_relations
    assert "requests_revalidation" in edge_relations
    assert "overrides_survival" in edge_relations
    assert "invalidates" in edge_relations


def test_canonical_roadmap_load_save_roundtrip_keeps_non_requires_relations() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    dumped = model.to_dict()
    edge_relations = [edge.get("relation", EDGE_RELATION_DEFAULT) for edge in dumped.get("graph", {}).get("edges", [])]
    assert "gates" in edge_relations
    assert "arbitrates" in edge_relations
    assert "requests_revalidation" in edge_relations
