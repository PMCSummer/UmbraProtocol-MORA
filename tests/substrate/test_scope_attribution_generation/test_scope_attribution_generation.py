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
from substrate.grounded_semantic import build_grounded_semantic_substrate_legacy_compatibility
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import (
    ApplicabilityResult,
    SourceScopeClass,
    build_scope_attribution,
)


@dataclass(frozen=True, slots=True)
class CaseSpec:
    case_id: str
    category: str
    text: str


_CASES: tuple[CaseSpec, ...] = (
    # 6 direct vs quoted contrasts.
    CaseSpec("dq-1", "direct_quoted", "i am tired"),
    CaseSpec("dq-2", "direct_quoted", '"i am tired"'),
    CaseSpec("dq-3", "direct_quoted", "you are tired"),
    CaseSpec("dq-4", "direct_quoted", '"you are tired"'),
    CaseSpec("dq-5", "direct_quoted", "он сказал, что ты устал"),
    CaseSpec("dq-6", "direct_quoted", 'он сказал: "ты устал"'),
    # 6 hypothetical/denial contrasts.
    CaseSpec("hd-1", "hypothetical_denial", "if you are tired we pause"),
    CaseSpec("hd-2", "hypothetical_denial", "if i am tired we pause"),
    CaseSpec("hd-3", "hypothetical_denial", "you are not tired"),
    CaseSpec("hd-4", "hypothetical_denial", "i am not tired"),
    CaseSpec("hd-5", "hypothetical_denial", "ты устал?"),
    CaseSpec("hd-6", "hypothetical_denial", "я не думаю, что ты устал"),
    # 6 addressee ambiguity contrasts.
    CaseSpec("aa-1", "addressee_ambiguity", "you and i are tired"),
    CaseSpec("aa-2", "addressee_ambiguity", "we are tired"),
    CaseSpec("aa-3", "addressee_ambiguity", "там это устало"),
    CaseSpec("aa-4", "addressee_ambiguity", "he said we are tired"),
    CaseSpec("aa-5", "addressee_ambiguity", "if we are tired?"),
    CaseSpec("aa-6", "addressee_ambiguity", "ты или я устал"),
    # 6 self-vs-user contamination contrasts.
    CaseSpec("su-1", "self_user_contamination", "i am tired but you are not"),
    CaseSpec("su-2", "self_user_contamination", "you are tired but i am not"),
    CaseSpec("su-3", "self_user_contamination", "he said i am tired"),
    CaseSpec("su-4", "self_user_contamination", "he said you are tired"),
    CaseSpec("su-5", "self_user_contamination", '"if you are tired"'),
    CaseSpec("su-6", "self_user_contamination", '"if i am tired"'),
)


def _pipeline(case: CaseSpec) -> ApplicabilityResult:
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=f"m-g03-{case.case_id}", content=case.text),
        SourceMetadata(
            source_id=f"user-g03-{case.case_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    grounded = build_grounded_semantic_substrate_legacy_compatibility(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m03:{case.case_id}",
        cooperation_anchor_ref=f"o03:{case.case_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    return build_scope_attribution(graph)


def test_case_matrix_contains_required_24_inputs() -> None:
    assert len(_CASES) == 24
    counts: dict[str, int] = {}
    for case in _CASES:
        counts[case.category] = counts.get(case.category, 0) + 1
    assert counts == {
        "direct_quoted": 6,
        "hypothetical_denial": 6,
        "addressee_ambiguity": 6,
        "self_user_contamination": 6,
    }


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case.case_id)
def test_g03_builds_explicit_applicability_layer(case: CaseSpec) -> None:
    result = _pipeline(case)
    assert isinstance(result, ApplicabilityResult)
    assert result.bundle.records
    assert result.bundle.permission_mappings
    assert result.no_truth_upgrade is True
    assert result.bundle.no_truth_upgrade is True
    assert result.telemetry.attempted_paths

    if case.category == "direct_quoted":
        assert any(
            record.source_scope_class
            in {
                SourceScopeClass.DIRECT_ASSERTION,
                SourceScopeClass.QUOTED,
                SourceScopeClass.REPORTED,
                SourceScopeClass.MIXED,
            }
            for record in result.bundle.records
        )
    elif case.category == "hypothetical_denial":
        assert any(
            "block_self_state_update" in record.downstream_permissions
            or "recommend_clarification" in record.downstream_permissions
            for record in result.bundle.records
        )
    elif case.category == "addressee_ambiguity":
        assert result.bundle.ambiguity_reasons or any(
            "recommend_clarification" in record.downstream_permissions
            for record in result.bundle.records
        )
    elif case.category == "self_user_contamination":
        assert any(
            "block_self_state_update" in record.downstream_permissions
            or "allow_external_model_update" in record.downstream_permissions
            for record in result.bundle.records
        )
