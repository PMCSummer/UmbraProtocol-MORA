from __future__ import annotations

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_update import (
    L06ContinuationReasonCode,
    L06ProposalPermissionCode,
    L06ProposalRestrictionCode,
    L06RestrictionCode,
    build_discourse_update,
    evaluate_discourse_update_downstream_gate,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    G01CoverageCode,
    G01NormativeBindingFailureCode,
    G01RestrictionCode,
    build_grounded_semantic_substrate,
    evaluate_grounded_semantic_downstream_gate,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import (
    L05CautionCode,
    L05RestrictionCode,
    build_modus_hypotheses,
    evaluate_modus_hypothesis_downstream_gate,
)
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.targeted_clarification import (
    G07DecisionBasisCode,
    G07LockoutCode,
    G07RestrictionCode,
    evaluate_targeted_clarification_downstream_gate,
)


def _pipeline(text: str, material_id: str):
    epistemic = ground_epistemic_input(
        InputMaterial(material_id=material_id, content=text),
        SourceMetadata(
            source_id=f"user-{material_id}",
            source_class=SourceClass.REPORTER,
            modality=ModalityClass.USER_TEXT,
            confidence_hint=ConfidenceLevel.MEDIUM,
        ),
    )
    surface = build_utterance_surface(epistemic.unit)
    syntax = build_morphosyntax_candidate_space(surface)
    lexical = build_lexical_grounding_hypotheses(syntax, utterance_surface=surface)
    dictum = build_dictum_candidates(lexical, syntax, utterance_surface=surface)
    modus = build_modus_hypotheses(dictum)
    discourse_update = build_discourse_update(modus)
    return surface, dictum, modus, discourse_update


def test_l05_emits_typed_cautions_and_typed_gate_restrictions() -> None:
    _, _, modus, _ = _pipeline('he said "you are tired?"', "typed-l05")
    gate = evaluate_modus_hypothesis_downstream_gate(modus)
    record = modus.bundle.hypothesis_records[0]

    assert all(isinstance(code, L05RestrictionCode) for code in gate.restrictions)
    assert L05RestrictionCode.LIKELY_ILLOCUTION_NOT_SETTLED_INTENT in gate.restrictions
    assert all(isinstance(code, L05CautionCode) for code in record.downstream_cautions)


def test_l06_emits_typed_proposal_codes_and_typed_gate_restrictions() -> None:
    _, _, _, discourse_update = _pipeline('he said "you are tired?"', "typed-l06")
    gate = evaluate_discourse_update_downstream_gate(discourse_update)

    assert all(isinstance(code, L06RestrictionCode) for code in gate.restrictions)
    for proposal in discourse_update.bundle.update_proposals:
        assert all(
            isinstance(code, L06ProposalPermissionCode)
            for code in proposal.downstream_permissions
        )
        assert all(
            isinstance(code, L06ProposalRestrictionCode)
            for code in proposal.downstream_restrictions
        )
    for continuation in discourse_update.bundle.continuation_states:
        assert isinstance(
            continuation.block_or_guard_reason_code, L06ContinuationReasonCode
        )


def test_g01_uses_typed_route_and_binding_failure_codes() -> None:
    surface_a, dictum_a, _, _ = _pipeline("alpha is stable", "typed-g01-a")
    _, dictum_b, modus_b, discourse_b = _pipeline("beta is stable", "typed-g01-b")
    with pytest.raises(TypeError) as exc:
        build_grounded_semantic_substrate(
            dictum_a,
            utterance_surface=surface_a,
            memory_anchor_ref="m03:typed-g01-a",
            cooperation_anchor_ref="o03:typed-g01-a",
            modus_hypotheses_result_or_bundle=modus_b,
            discourse_update_result_or_bundle=discourse_b,
        )
    assert (
        G01NormativeBindingFailureCode.L05_SOURCE_DICTUM_REF_MISMATCH.value
        in str(exc.value)
    )

    surface, dictum, modus, discourse_update = _pipeline(
        'he said "alpha is stable?"',
        "typed-g01-normative",
    )
    grounded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:typed-g01-normative",
        cooperation_anchor_ref="o03:typed-g01-normative",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    gate = evaluate_grounded_semantic_downstream_gate(grounded)
    assert all(isinstance(code, G01RestrictionCode) for code in gate.restrictions)
    assert G01CoverageCode.L05_L06_NORMATIVE_ROUTE_ACTIVE in grounded.bundle.low_coverage_reasons


def test_g07_emits_typed_restrictions_decision_basis_and_lockouts(g07_factory) -> None:
    result = g07_factory('he said "you are tired?"', "typed-g07").intervention
    gate = evaluate_targeted_clarification_downstream_gate(result)

    assert all(isinstance(code, G07RestrictionCode) for code in gate.restrictions)
    for record in result.bundle.intervention_records:
        assert all(
            isinstance(code, G07DecisionBasisCode)
            for code in record.decision.decision_basis
        )
        assert all(isinstance(code, G07LockoutCode) for code in record.downstream_lockouts)
