from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import (
    LexicalDiscourseContext,
    build_lexical_grounding_hypotheses,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import (
    CertaintyClass,
    DictumOrModusClass,
    PolarityClass,
    RuntimeGraphResult,
    SemanticUnitKind,
    build_runtime_semantic_graph,
)


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    category: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    # Negation cases.
    CaseSpec("neg-1", "negation", "we do not track alpha"),
    CaseSpec("neg-2", "negation", "alpha is not stable"),
    CaseSpec("neg-3", "negation", "мы не считаем beta готовым"),
    CaseSpec("neg-4", "negation", "if alpha is not ready, wait"),
    # Source scope cases.
    CaseSpec("src-1", "source_scope", '"alpha moved"'),
    CaseSpec("src-2", "source_scope", "operator said alpha moved"),
    CaseSpec("src-3", "source_scope", 'according to analyst, "beta shifted"'),
    CaseSpec("src-4", "source_scope", '"delta failed", said observer'),
    # Dictum/modus cases.
    CaseSpec("dm-1", "dictum_modus", "maybe alpha can move?"),
    CaseSpec("dm-2", "dictum_modus", "perhaps we should wait"),
    CaseSpec("dm-3", "dictum_modus", "может ли beta быть готов?"),
    CaseSpec("dm-4", "dictum_modus", "well we must hold"),
    # Ambiguity cases.
    CaseSpec("amb-1", "ambiguity", "alpha... beta??"),
    CaseSpec("amb-2", "ambiguity", "if alpha then beta, or gamma??"),
    CaseSpec("amb-3", "ambiguity", '"alpha"... said he??'),
    CaseSpec("amb-4", "ambiguity", "delta maybe... maybe not"),
    # Missing-argument cases.
    CaseSpec("miss-1", "missing_argument", "because alpha"),
    CaseSpec("miss-2", "missing_argument", "if ready"),
    CaseSpec("miss-3", "missing_argument", "там это"),
    CaseSpec("miss-4", "missing_argument", "she said"),
    # Embedding/coordination cases.
    CaseSpec("emb-1", "embedding_coord", "if alpha moves and beta waits, gamma reports"),
    CaseSpec("emb-2", "embedding_coord", "we track alpha and beta"),
    CaseSpec("emb-3", "embedding_coord", "unless delta recovers, epsilon holds"),
    CaseSpec("emb-4", "embedding_coord", "alpha or beta can move"),
)


def _g02_pipeline(case: CaseSpec) -> RuntimeGraphResult:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-g02-{case.case_id}", content=case.text),
        SourceMetadata(
            source_id=f"user-g02-{case.case_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface_result = build_utterance_surface(epistemic.unit)
    syntax_result = build_morphosyntax_candidate_space(surface_result)
    lexical_result = build_lexical_grounding_hypotheses(
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref=f"ctx-g02-{case.case_id}"),
    )
    dictum_result = build_dictum_candidates(
        lexical_result,
        syntax_result,
        utterance_surface=surface_result,
        discourse_context=LexicalDiscourseContext(context_ref=f"ctx-g02-{case.case_id}"),
    )
    grounded_result = build_grounded_semantic_substrate_normative(
        dictum_result,
        utterance_surface=surface_result,
        memory_anchor_ref=f"m03:{case.case_id}",
        cooperation_anchor_ref=f"o03:{case.case_id}",
    )
    return build_runtime_semantic_graph(grounded_result)


def test_case_matrix_contains_required_24_inputs() -> None:
    assert len(_CASES) == 24
    category_counts: dict[str, int] = {}
    for case in _CASES:
        category_counts[case.category] = category_counts.get(case.category, 0) + 1
    assert category_counts == {
        "negation": 4,
        "source_scope": 4,
        "dictum_modus": 4,
        "ambiguity": 4,
        "missing_argument": 4,
        "embedding_coord": 4,
    }


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_g02_builds_runtime_graph_for_required_case_matrix(case: CaseSpec) -> None:
    result = _g02_pipeline(case)
    assert isinstance(result, RuntimeGraphResult)
    assert result.bundle.semantic_units
    assert result.bundle.graph_edges
    assert result.bundle.proposition_candidates
    assert result.no_final_semantic_closure is True
    assert result.bundle.no_final_semantic_closure is True
    assert result.telemetry.attempted_paths
    assert any(unit.unit_kind is SemanticUnitKind.FRAME_NODE for unit in result.bundle.semantic_units)

    if case.category == "negation":
        assert any(candidate.polarity is PolarityClass.NEGATED for candidate in result.bundle.proposition_candidates)
    elif case.category == "source_scope":
        assert any(
            bool(candidate.source_scope_refs) or candidate.certainty_class is not CertaintyClass.ASSERTED
            for candidate in result.bundle.proposition_candidates
        )
    elif case.category == "dictum_modus":
        assert any(unit.unit_kind is SemanticUnitKind.MODUS_NODE for unit in result.bundle.semantic_units)
        assert any(
            candidate.dictum_or_modus_class is DictumOrModusClass.DICTUM
            for candidate in result.bundle.proposition_candidates
        )
    elif case.category == "ambiguity":
        assert result.bundle.graph_alternatives
    elif case.category == "missing_argument":
        assert result.bundle.unresolved_role_slots
    elif case.category == "embedding_coord":
        assert len(result.bundle.graph_edges) >= len(result.bundle.role_bindings)


def test_runtime_graph_is_not_isomorphic_to_g01_scaffold_shape() -> None:
    result = _g02_pipeline(CaseSpec("shape", "negation", "we do not track alpha"))
    assert result.telemetry.semantic_unit_count != 0
    assert result.telemetry.role_binding_count != 0
    assert result.telemetry.proposition_count != 0
    assert result.telemetry.semantic_unit_count != result.telemetry.proposition_count or result.telemetry.edge_count > 0
