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
    AUTHORITY_ROLE_LABELS,
    COMPUTATIONAL_ROLE_LABELS,
    EDGE_RELATION_DEFAULT,
    EDGE_RELATION_LABELS,
    EDGE_RELATION_STYLE_HINTS,
    GraphEdge,
    Phase,
    RoadmapModel,
    SEAM_RELATION_EXPECTATIONS,
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
        "authority_role": "computational",
        "computational_role": "unknown",
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
    assert GraphEdge.from_dict({"source": "a", "target": "b", "relation": "supports"}).relation == "modulates"
    assert GraphEdge.from_dict({"source": "a", "target": "b", "relation": "grounds"}).relation == "requires"


def test_phase_role_schema_defaults_and_unknown_fallback() -> None:
    phase = Phase.from_dict({"code": "X01", "title": "x"})
    assert phase.authority_role == "computational"
    assert phase.computational_role == "unknown"

    unknown = Phase.from_dict(
        {
            "code": "X02",
            "title": "x2",
            "authority_role": "not_a_role",
            "computational_role": "also_not_a_role",
        }
    )
    assert unknown.authority_role == "computational"
    assert unknown.computational_role == "unknown"

    typed = Phase.from_dict(
        {
            "code": "X03",
            "title": "x3",
            "authority_role": "arbitration",
            "computational_role": "scheduler",
        }
    )
    assert typed.authority_role == "arbitration"
    assert typed.computational_role == "scheduler"


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
    assert dumped["authority_role_vocab"] == AUTHORITY_ROLE_LABELS
    assert dumped["computational_role_vocab"] == COMPUTATIONAL_ROLE_LABELS


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
    assert "supports" not in edge_relations
    assert "grounds" not in edge_relations
    assert "refines" not in edge_relations


def test_canonical_roadmap_load_save_roundtrip_keeps_non_requires_relations() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    dumped = model.to_dict()
    edge_relations = [edge.get("relation", EDGE_RELATION_DEFAULT) for edge in dumped.get("graph", {}).get("edges", [])]
    assert "gates" in edge_relations
    assert "arbitrates" in edge_relations
    assert "requests_revalidation" in edge_relations
    assert set(edge_relations).issubset(set(EDGE_RELATION_LABELS))


def test_phase_role_roundtrip_is_preserved_for_mixed_assignments() -> None:
    raw = {
        "schema_version": 5,
        "phases": [
            _minimal_phase("F01", "foundation"),
            _minimal_phase("C04", "mode arbitration", after="F01"),
        ],
        "graph": {"nodes": [], "edges": []},
    }
    raw["phases"][0]["authority_role"] = "observability_only"
    raw["phases"][0]["computational_role"] = "bridge_contract"
    raw["phases"][1]["authority_role"] = "arbitration"
    raw["phases"][1]["computational_role"] = "scheduler"
    model = RoadmapModel.from_json(raw)
    dumped = model.to_dict()
    by_code = {phase["code"]: phase for phase in dumped["phases"]}
    assert by_code["F01"]["authority_role"] == "observability_only"
    assert by_code["F01"]["computational_role"] == "bridge_contract"
    assert by_code["C04"]["authority_role"] == "arbitration"
    assert by_code["C04"]["computational_role"] == "scheduler"


def test_seam_relation_consistency_for_representative_pairs() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    violations = model.seam_relation_consistency_violations()
    assert violations == []


def test_seam_relation_consistency_detects_relation_drift() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    target_pair = ("C04", "C05")
    expected = SEAM_RELATION_EXPECTATIONS[target_pair]
    assert expected == "arbitrates"
    for edge in model.graph_edges:
        if edge.source == "phase::C04" and edge.target == "phase::C05":
            edge.relation = "requires"
            break
    else:
        raise AssertionError("Missing C04->C05 edge in canonical roadmap.")
    violations = model.seam_relation_consistency_violations()
    assert any("C04->C05 expected=arbitrates actual=requires" in item for item in violations)


def test_requires_vs_gates_and_invalidates_vs_revalidation_are_distinct() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    relation_by_pair = {(edge.source, edge.target): edge.relation for edge in model.graph_edges}
    assert relation_by_pair[("phase::C01", "phase::C02")] == "requires"
    assert relation_by_pair[("phase::C02", "phase::C04")] == "gates"
    assert relation_by_pair[("phase::S05", "phase::S04")] == "invalidates"
    assert relation_by_pair[("phase::C05", "phase::S04")] == "requests_revalidation"
    assert relation_by_pair[("phase::C05", "phase::D01")] == "requests_revalidation"


def test_observes_only_links_remain_non_enforcement_relations() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    relation_by_pair = {(edge.source, edge.target): edge.relation for edge in model.graph_edges}
    for pair in [
        ("phase::A01", "phase::D01"),
        ("phase::A02", "phase::D01"),
        ("phase::A03", "phase::D01"),
        ("phase::N01", "phase::D01"),
        ("phase::N02", "phase::D01"),
        ("phase::N03", "phase::D01"),
        ("phase::RT01", "phase::D01"),
    ]:
        assert relation_by_pair[pair] == "observes_only"


def test_rt01_present_and_marked_closed_runtime_phase() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    raw = json.loads(roadmap_path.read_text(encoding="utf-8"))
    phases = {phase.get("code"): phase for phase in raw.get("phases", [])}
    assert "RT01" in phases
    rt01 = phases["RT01"]
    assert rt01.get("status") == "closed"
    assert rt01.get("validation_state") == "implemented_baseline"
    assert rt01.get("maturity") in {"L7_stable_in_contour", "L8_externally_benchmarked"}
    assert rt01.get("claim_state") in {"telemetry_supported", "implemented"}


def test_rt01_relations_present_and_authority_safe() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    relation_by_pair = {(edge.source, edge.target): edge.relation for edge in model.graph_edges}
    assert relation_by_pair[("phase::C01", "phase::RT01")] == "requires"
    assert relation_by_pair[("phase::C04", "phase::RT01")] == "arbitrates"
    assert relation_by_pair[("phase::C05", "phase::RT01")] == "gates"
    assert relation_by_pair[("phase::RT01", "phase::D01")] == "observes_only"
    assert relation_by_pair[("phase::C04", "phase::RT01")] != relation_by_pair[("phase::C05", "phase::RT01")]


def test_target_phase_authority_and_computational_roles_are_machine_readable() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    raw = json.loads(roadmap_path.read_text(encoding="utf-8"))
    phases = {phase.get("code"): phase for phase in raw.get("phases", [])}

    assert phases["C05"]["authority_role"] == "invalidation"
    assert phases["C04"]["authority_role"] == "arbitration"
    assert phases["R04"]["authority_role"] == "gating"
    assert phases["F01"]["authority_role"] == "observability_only"
    assert phases["RT01"]["authority_role"] == "gating"
    assert phases["D01"]["authority_role"] == "observability_only"

    assert phases["C05"]["computational_role"] == "evaluator"
    assert phases["C04"]["computational_role"] == "scheduler"
    assert phases["R04"]["computational_role"] == "evaluator"
    assert phases["F01"]["computational_role"] == "bridge_contract"
    assert phases["RT01"]["computational_role"] == "execution_spine"
    assert phases["D01"]["computational_role"] == "observability"


def test_role_readiness_summary_is_frontier_only_not_map_wide_for_current_roadmap() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    summary = model.role_readiness_summary()
    assert summary["frontier_role_typed"] is True
    assert summary["map_wide_role_ready"] is False
    assert summary["role_frontier_only"] is True
    assert summary["fallback_phase_count"] > 0


def test_subject_tick_role_source_packet_exposes_explicit_source_and_flags() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    packet = model.subject_tick_role_source_packet()
    assert packet["source_ref"] == "roadmap.phase_role_frontier_packet.v1"
    assert packet["frontier_role_typed"] is True
    assert packet["map_wide_role_ready"] is False
    assert packet["role_frontier_only"] is True
    assert packet["phase_authority_roles"]["C04"] == "arbitration"
    assert packet["phase_authority_roles"]["C05"] == "invalidation"
    assert packet["phase_authority_roles"]["D01"] == "observability_only"


def test_phase_execution_packet_includes_machine_readable_role_readiness_summary() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    packet = model.build_phase_execution_packet("RT01")
    readiness = packet.get("role_readiness", {})
    assert readiness.get("frontier_role_typed") is True
    assert readiness.get("map_wide_role_ready") is False
    assert readiness.get("role_frontier_only") is True


def test_missing_pair_c01_t01_is_now_present() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    relation_by_pair = {(edge.source, edge.target): edge.relation for edge in model.graph_edges}
    assert relation_by_pair[("phase::C01", "phase::T01")] == "requires"


def test_targeted_self_world_learning_retagging_is_present() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    relation_by_pair = {(edge.source, edge.target): edge.relation for edge in model.graph_edges}
    assert relation_by_pair[("phase::N03", "phase::O02")] == "modulates"
    assert relation_by_pair[("phase::T03", "phase::O02")] == "modulates"
    assert relation_by_pair[("phase::S05", "phase::O02")] == "modulates"
    assert relation_by_pair[("phase::O02", "phase::O03")] == "modulates"
    assert relation_by_pair[("phase::S05", "phase::O03")] == "modulates"
    assert relation_by_pair[("phase::S05", "phase::A01")] == "modulates"
    assert relation_by_pair[("phase::S05", "phase::A02")] == "modulates"
    assert relation_by_pair[("phase::S05", "phase::A03")] == "modulates"


def test_audited_frontier_seam_contract_matches_graph_pairs() -> None:
    roadmap_path = TRACKER_ROOT / "UmbraProtocol_MORA_language_refactor.json"
    model = RoadmapModel.from_json(json.loads(roadmap_path.read_text(encoding="utf-8")))
    frontier = [
        "C01.seam.md",
        "C02.seam.md",
        "C03.seam.md",
        "C04.seam.md",
        "C05.seam.md",
        "R04.seam.md",
        "D01.seam.md",
        "S01.seam.md",
        "S02.seam.md",
        "S03.seam.md",
        "S04.seam.md",
        "S05.seam.md",
        "A01.seam.md",
        "A02.seam.md",
        "A03.seam.md",
        "M01.seam.md",
        "M02.seam.md",
        "M03.seam.md",
        "O01.seam.md",
        "O02.seam.md",
        "RT01.seam.md",
    ]
    violations = model.seam_relation_contract_violations(seam_files=frontier)
    assert violations == []


def test_seam_docs_include_relation_semantic_contract_blocks() -> None:
    seam_dir = ROOT / "docs" / "seams"
    required = {
        "C01.seam.md": ["C01 -> C02/C03/C04/C05/RT01: `requires`", "C01 -> S01/S02/S03/S04/S05/T01: `requires`"],
        "C02.seam.md": ["C02 -> C03: `gates`", "C02 -> C04: `gates`", "C02 -> C05: `gates`"],
        "C03.seam.md": ["C03 -> C04: `modulates`", "C03 -> C05: `modulates`"],
        "C04.seam.md": ["C04 -> C05: `arbitrates`", "C04 -> RT01: `arbitrates`"],
        "C05.seam.md": ["`requests_revalidation`", "C05 -> RT01: `gates`"],
        "R04.seam.md": ["R04 -> C04/S01/S02/S03/S04/S05: `overrides_survival`"],
        "D01.seam.md": ["A01/A02/A03/N01/N02/N03/RT01 -> D01: `observes_only`", "C05 -> D01: `requests_revalidation`", "D01 -> M01: `modulates`"],
        "S01.seam.md": ["C04 -> S01: `arbitrates`", "R04 -> S01: `overrides_survival`"],
        "S02.seam.md": ["C04 -> S02: `arbitrates`", "R04 -> S02: `overrides_survival`"],
        "S03.seam.md": ["C04 -> S03: `arbitrates`", "R04 -> S03: `overrides_survival`"],
        "S04.seam.md": ["S04 -> O01: `body_world_couples`"],
        "S05.seam.md": ["S05 -> D01/M01/M02/M03: `feedback_learns`"],
        "O01.seam.md": ["O01 -> O02: `modulates`", "O01 -> O03: `modulates`"],
        "O02.seam.md": ["C04 -> O02: `arbitrates`", "R04 -> O02: `gates`", "O01/N03/S05/T03 -> O02: `modulates`"],
        "A01.seam.md": ["C04 -> A01: `arbitrates`", "R04 -> A01: `gates`", "S05 -> A01: `modulates`"],
        "A02.seam.md": ["A01 -> A02: `requires`", "R04 -> A02: `gates`", "S05 -> A02: `modulates`"],
        "A03.seam.md": ["A01/A02 -> A03: `requires`", "C04 -> A03: `arbitrates`", "S05 -> A03: `modulates`"],
        "M01.seam.md": ["D01 -> M01: `modulates`", "R04 -> M01: `gates`", "S05 -> M01: `feedback_learns`"],
        "M02.seam.md": ["M01 -> M02: `requires`", "C05 -> M02: `requests_revalidation`", "S05 -> M02: `feedback_learns`"],
        "M03.seam.md": ["M01/M02 -> M03: `requires`", "C05 -> M03: `requests_revalidation`", "S05 -> M03: `feedback_learns`"],
        "RT01.seam.md": ["C04 -> RT01: `arbitrates`", "C05 -> RT01: `gates`", "RT01 -> D01: `observes_only`"],
    }
    for seam_name, fragments in required.items():
        text = (seam_dir / seam_name).read_text(encoding="utf-8")
        assert "## RELATION SEMANTIC CONTRACT" in text
        for fragment in fragments:
            assert fragment in text


def test_key_seams_encode_authority_and_computational_role_contracts() -> None:
    seam_dir = ROOT / "docs" / "seams"
    required = {
        "F01.seam.md": [
            "authority_role: `observability_only`",
            "computational_role: `bridge_contract`",
        ],
        "R04.seam.md": [
            "authority_role: `gating`",
            "computational_role: `evaluator`",
        ],
        "C04.seam.md": [
            "authority_role: `arbitration`",
            "computational_role: `scheduler`",
        ],
        "C05.seam.md": [
            "authority_role: `invalidation`",
            "computational_role: `evaluator`",
        ],
        "D01.seam.md": [
            "authority_role: `observability_only`",
            "computational_role: `observability`",
        ],
        "RT01.seam.md": [
            "authority_role: `gating`",
            "computational_role: `execution_spine`",
        ],
    }
    for seam_name, fragments in required.items():
        text = (seam_dir / seam_name).read_text(encoding="utf-8")
        assert "## PHASE ROLE CONTRACT" in text
        for fragment in fragments:
            assert fragment in text
