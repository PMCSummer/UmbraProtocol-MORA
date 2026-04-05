from __future__ import annotations

from dataclasses import dataclass

import pytest

from substrate.concept_framing import ConceptFramingResult, build_concept_framing
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
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import build_semantic_acquisition


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    category: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    CaseSpec("d-1", "descriptive", "i am tired"),
    CaseSpec("d-2", "descriptive", "you are tired"),
    CaseSpec("d-3", "descriptive", "we are tired"),
    CaseSpec("d-4", "descriptive", "it is cold"),
    CaseSpec("n-1", "normative_like", "you should rest"),
    CaseSpec("n-2", "normative_like", "you must stop"),
    CaseSpec("n-3", "normative_like", "you have to comply"),
    CaseSpec("n-4", "normative_like", "you ought to wait"),
    CaseSpec("t-1", "threat_like", "you are dangerous"),
    CaseSpec("t-2", "threat_like", "he might hurt you"),
    CaseSpec("t-3", "threat_like", "this is risky"),
    CaseSpec("t-4", "threat_like", "that sounds threatening"),
    CaseSpec("q-1", "questioned", "you are tired?"),
    CaseSpec("q-2", "questioned", "if you are tired"),
    CaseSpec("q-3", "questioned", "are you sure you are tired"),
    CaseSpec("q-4", "questioned", "if this is dangerous"),
    CaseSpec("r-1", "repair", "no, i did not say that"),
    CaseSpec("r-2", "repair", "i was quoting him"),
    CaseSpec("r-3", "repair", "this was not my claim"),
    CaseSpec("r-4", "repair", "это не я сказал"),
    CaseSpec("m-1", "mixed", 'he said "you are tired?"'),
    CaseSpec("m-2", "mixed", 'she said "you should stop"'),
    CaseSpec("m-3", "mixed", "if he said i am dangerous"),
    CaseSpec("m-4", "mixed", "i think he said you are wrong"),
)


def _g06(case: CaseSpec) -> ConceptFramingResult:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-g06-{case.case_id}", content=case.text),
        SourceMetadata(
            source_id=f"user-g06-{case.case_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m06:{case.case_id}",
        cooperation_anchor_ref=f"o06:{case.case_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    perspective = build_discourse_provenance_chain(applicability)
    acquisition = build_semantic_acquisition(perspective)
    return build_concept_framing(acquisition)


def test_case_matrix_contains_24_inputs() -> None:
    assert len(_CASES) == 24


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_g06_builds_typed_concept_framing_layer(case: CaseSpec) -> None:
    result = _g06(case)
    assert isinstance(result, ConceptFramingResult)
    assert result.bundle.framing_records
    assert result.bundle.competition_links
    assert result.bundle.l06_update_proposal_not_bound_here is True
    assert result.no_final_semantic_closure is True
    assert result.telemetry.attempted_paths
    assert all(record.framing_basis for record in result.bundle.framing_records)
    assert all(record.vulnerability_profile for record in result.bundle.framing_records)

    if case.category in {"questioned", "repair", "mixed"}:
        assert (
            result.bundle.ambiguity_reasons
            or any(record.reframing_conditions for record in result.bundle.framing_records)
        )
