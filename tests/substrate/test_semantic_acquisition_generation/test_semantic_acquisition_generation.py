from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
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
from substrate.semantic_acquisition import (
    SemanticAcquisitionResult,
    build_semantic_acquisition,
)


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    category: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    CaseSpec("sp-1", "support", "i am tired"),
    CaseSpec("sp-2", "support", "you are tired"),
    CaseSpec("sp-3", "support", "we are tired"),
    CaseSpec("sp-4", "support", "he is tired"),
    CaseSpec("sp-5", "support", "it is cold"),
    CaseSpec("cf-1", "conflict", "if you are tired"),
    CaseSpec("cf-2", "conflict", "you are tired?"),
    CaseSpec("cf-3", "conflict", "i do not think you are tired"),
    CaseSpec("cf-4", "conflict", '"you are tired"'),
    CaseSpec("cf-5", "conflict", "he said that you are tired"),
    CaseSpec("rp-1", "repair", "no, i did not say that"),
    CaseSpec("rp-2", "repair", "i was quoting him"),
    CaseSpec("rp-3", "repair", "it was him who said that"),
    CaseSpec("rp-4", "repair", "нет, это не я сказал"),
    CaseSpec("rp-5", "repair", "я цитировал его"),
    CaseSpec("mx-1", "mixed", "you and i are tired"),
    CaseSpec("mx-2", "mixed", "ты или я устал"),
    CaseSpec("mx-3", "mixed", "if we are tired?"),
    CaseSpec("mx-4", "mixed", "там это устало"),
    CaseSpec("mx-5", "mixed", "he asked if we are tired"),
)


def _g05(case: CaseSpec) -> SemanticAcquisitionResult:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-g05-{case.case_id}", content=case.text),
        SourceMetadata(
            source_id=f"user-g05-{case.case_id}",
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
        memory_anchor_ref=f"m05:{case.case_id}",
        cooperation_anchor_ref=f"o05:{case.case_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    perspective = build_discourse_provenance_chain(applicability)
    return build_semantic_acquisition(perspective)


def test_case_matrix_contains_20_inputs() -> None:
    assert len(_CASES) == 20
    counts: dict[str, int] = {}
    for case in _CASES:
        counts[case.category] = counts.get(case.category, 0) + 1
    assert counts == {
        "support": 5,
        "conflict": 5,
        "repair": 5,
        "mixed": 5,
    }


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_g05_builds_typed_provisional_acquisition_layer(case: CaseSpec) -> None:
    result = _g05(case)
    assert isinstance(result, SemanticAcquisitionResult)
    assert result.bundle.acquisition_records
    assert result.bundle.cluster_links
    assert result.no_final_semantic_closure is True
    assert result.bundle.no_final_semantic_closure is True
    assert result.telemetry.attempted_paths

    if case.category == "support":
        assert any(
            record.support_conflict_profile.support_reasons
            for record in result.bundle.acquisition_records
        )
    elif case.category == "conflict":
        assert any(
            record.support_conflict_profile.conflict_reasons
            for record in result.bundle.acquisition_records
        )
    elif case.category == "repair":
        assert any(
            record.revision_conditions
            for record in result.bundle.acquisition_records
        )
    elif case.category == "mixed":
        assert result.bundle.ambiguity_reasons or any(
            record.support_conflict_profile.unresolved_slots
            for record in result.bundle.acquisition_records
        )
