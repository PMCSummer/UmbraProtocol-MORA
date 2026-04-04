from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import (
    PerspectiveChainResult,
    build_discourse_provenance_chain,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import build_grounded_semantic_substrate
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    category: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    # 5 nested-report cases
    CaseSpec("nr-1", "nested_report", "petya said that masha thinks i am afraid"),
    CaseSpec("nr-2", "nested_report", "petya thinks that masha said i am afraid"),
    CaseSpec("nr-3", "nested_report", "он сказал, что она думает, что я боюсь"),
    CaseSpec("nr-4", "nested_report", "она думает, что он сказал, что я боюсь"),
    CaseSpec("nr-5", "nested_report", "he reported that she believed that i was tired"),
    # 5 quote-vs-assert cases
    CaseSpec("qa-1", "quote_vs_assert", "you are tired"),
    CaseSpec("qa-2", "quote_vs_assert", '"you are tired"'),
    CaseSpec("qa-3", "quote_vs_assert", 'he said "you are tired"'),
    CaseSpec("qa-4", "quote_vs_assert", "he said that you are tired"),
    CaseSpec("qa-5", "quote_vs_assert", 'i said: "i am tired"'),
    # 5 cross-turn repair cases
    CaseSpec("cr-1", "cross_turn_repair", "no, i did not say that"),
    CaseSpec("cr-2", "cross_turn_repair", "i was quoting him"),
    CaseSpec("cr-3", "cross_turn_repair", "he said that, not me"),
    CaseSpec("cr-4", "cross_turn_repair", "нет, это не я сказал"),
    CaseSpec("cr-5", "cross_turn_repair", "я цитировал его"),
    # 5 modus-at-different-level cases
    CaseSpec("ml-1", "modus_level", "i think you are tired"),
    CaseSpec("ml-2", "modus_level", "if you are tired, rest"),
    CaseSpec("ml-3", "modus_level", "you are tired?"),
    CaseSpec("ml-4", "modus_level", "i do not think you are tired"),
    CaseSpec("ml-5", "modus_level", "he asked if you are tired"),
)


def _g04(case: CaseSpec) -> PerspectiveChainResult:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-g04-{case.case_id}", content=case.text),
        SourceMetadata(
            source_id=f"user-g04-{case.case_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m04:{case.case_id}",
        cooperation_anchor_ref=f"o04:{case.case_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


def test_case_matrix_contains_required_20_inputs() -> None:
    assert len(_CASES) == 20
    counts: dict[str, int] = {}
    for case in _CASES:
        counts[case.category] = counts.get(case.category, 0) + 1
    assert counts == {
        "nested_report": 5,
        "quote_vs_assert": 5,
        "cross_turn_repair": 5,
        "modus_level": 5,
    }


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_g04_builds_explicit_perspective_chain_layer(case: CaseSpec) -> None:
    result = _g04(case)
    assert isinstance(result, PerspectiveChainResult)
    assert result.bundle.chain_records
    assert result.bundle.commitment_lineages
    assert result.bundle.wrapped_propositions
    assert result.bundle.cross_turn_links
    assert result.no_truth_upgrade is True
    assert result.bundle.no_truth_upgrade is True
    assert result.telemetry.attempted_paths

    if case.category == "nested_report":
        assert any(record.discourse_level >= 2 for record in result.bundle.chain_records)
    elif case.category == "quote_vs_assert":
        assert any(
            "response_should_not_flatten_owner" in wrapped.downstream_constraints
            or wrapped.assertion_mode.value
            in {
                "direct_current_commitment",
                "quoted_external_content",
                "reported_external_commitment",
                "unresolved",
                "mixed",
            }
            for wrapped in result.bundle.wrapped_propositions
        )
    elif case.category == "cross_turn_repair":
        assert result.bundle.cross_turn_links
    elif case.category == "modus_level":
        assert any(
            wrapped.assertion_mode.value
            in {
                "hypothetical_branch",
                "question_frame",
                "denial_frame",
                "direct_current_commitment",
                "attributed_belief",
                "unresolved",
                "mixed",
            }
            for wrapped in result.bundle.wrapped_propositions
        )


def test_nested_structures_yield_distinct_chain_topology_or_explicit_degradation() -> None:
    a = _g04(CaseSpec("nested-a", "nested_report", "petya said that masha thinks i am afraid"))
    b = _g04(CaseSpec("nested-b", "nested_report", "petya thinks that masha said i am afraid"))
    topo_a = {(record.discourse_level, record.assertion_mode.value, record.commitment_owner.value) for record in a.bundle.chain_records}
    topo_b = {(record.discourse_level, record.assertion_mode.value, record.commitment_owner.value) for record in b.bundle.chain_records}
    if topo_a == topo_b:
        assert a.bundle.ambiguity_reasons or b.bundle.ambiguity_reasons
    else:
        assert topo_a != topo_b
