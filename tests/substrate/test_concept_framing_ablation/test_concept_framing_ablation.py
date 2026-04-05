from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.concept_framing import (
    FramingUsabilityClass,
    build_concept_framing,
    derive_concept_framing_contract_view,
    evaluate_concept_framing_downstream_gate,
)
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
from substrate.semantic_acquisition.models import AcquisitionStatus, RevisionCondition, RevisionConditionKind


def _g05(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m06:{material_id}",
        cooperation_anchor_ref=f"o06:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    perspective = build_discourse_provenance_chain(applicability)
    return build_semantic_acquisition(perspective)


def _normalized_acquisition_bundle(bundle):
    return replace(
        bundle,
        acquisition_records=tuple(
            replace(
                record,
                acquisition_status=AcquisitionStatus.WEAK_PROVISIONAL,
                blocked_reason=None,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    support_reasons=("chain_object_present", "provenance_path_present"),
                    support_score=2.0,
                    conflict_reasons=(
                        "assertion_mode:question_frame",
                        "owner_flattening_risk",
                        "source_scope_unknown",
                    ),
                    conflict_score=1.0,
                    unresolved_slots=(),
                ),
                revision_conditions=(
                    RevisionCondition(
                        condition_id="rev-clarification",
                        condition_kind=RevisionConditionKind.REOPEN_ON_CLARIFICATION_ANSWER,
                        trigger_reason="clarification answer may reframe ownership-sensitive reading",
                        confidence=0.6,
                        provenance="test-normalized-revision-basis",
                    ),
                ),
                downstream_permissions=("no_final_semantic_closure", "allow_provisional_semantic_uptake"),
            )
            for record in bundle.acquisition_records
        ),
        ambiguity_reasons=(),
    )


@pytest.mark.parametrize(
    ("ablation_id", "ablate"),
    (
        (
            "remove_support_cues",
            lambda bundle: replace(
                bundle,
                acquisition_records=tuple(
                    replace(
                        record,
                        support_conflict_profile=replace(
                            record.support_conflict_profile,
                            support_reasons=(),
                            support_score=0.0,
                        ),
                    )
                    for record in bundle.acquisition_records
                ),
            ),
        ),
        (
            "remove_conflict_cues",
            lambda bundle: replace(
                bundle,
                acquisition_records=tuple(
                    replace(
                        record,
                        support_conflict_profile=replace(
                            record.support_conflict_profile,
                            conflict_reasons=(),
                            conflict_score=0.0,
                            unresolved_slots=(),
                        ),
                    )
                    for record in bundle.acquisition_records
                ),
                ambiguity_reasons=(),
            ),
        ),
        (
            "remove_continuity_repair_signals",
            lambda bundle: replace(
                bundle,
                acquisition_records=tuple(
                    replace(record, revision_conditions=())
                    for record in bundle.acquisition_records
                ),
            ),
        ),
        (
            "remove_perspective_sensitive_constraints",
            lambda bundle: replace(
                bundle,
                acquisition_records=tuple(
                    replace(
                        record,
                        support_conflict_profile=replace(
                            record.support_conflict_profile,
                            conflict_reasons=tuple(
                                reason
                                for reason in record.support_conflict_profile.conflict_reasons
                                if reason not in {"owner_flattening_risk", "source_scope_unknown"}
                            ),
                        ),
                    )
                    for record in bundle.acquisition_records
                ),
            ),
        ),
    ),
)
def test_ablation_matrix_changes_framing_outcome_or_contract(ablation_id: str, ablate) -> None:
    base = _g05('he said "you are not tired?"', f"m-g06-ablation-{ablation_id}")
    base_bundle = _normalized_acquisition_bundle(base.bundle)
    baseline = build_concept_framing(base_bundle)
    degraded = build_concept_framing(ablate(base_bundle))
    baseline_gate = evaluate_concept_framing_downstream_gate(baseline)
    degraded_gate = evaluate_concept_framing_downstream_gate(degraded)

    baseline_sig = {
        (
            record.framing_status.value,
            record.frame_family.value,
            record.vulnerability_profile.vulnerability_level.value,
            tuple(sorted(record.vulnerability_profile.fragility_reasons)),
            tuple(sorted(condition.condition_kind.value for condition in record.reframing_conditions)),
        )
        for record in baseline.bundle.framing_records
    }
    degraded_sig = {
        (
            record.framing_status.value,
            record.frame_family.value,
            record.vulnerability_profile.vulnerability_level.value,
            tuple(sorted(record.vulnerability_profile.fragility_reasons)),
            tuple(sorted(condition.condition_kind.value for condition in record.reframing_conditions)),
        )
        for record in degraded.bundle.framing_records
    }
    assert (
        baseline_sig != degraded_sig
        or baseline.bundle.ambiguity_reasons != degraded.bundle.ambiguity_reasons
        or baseline.bundle.low_coverage_reasons != degraded.bundle.low_coverage_reasons
        or baseline_gate.restrictions != degraded_gate.restrictions
    )

    gate = degraded_gate
    view = derive_concept_framing_contract_view(degraded)
    assert view.requires_status_read is True
    assert view.requires_cautions_read is True
    if gate.accepted and gate.usability_class is FramingUsabilityClass.DEGRADED_BOUNDED:
        assert "accepted_degraded_requires_restrictions_read" in gate.restrictions
