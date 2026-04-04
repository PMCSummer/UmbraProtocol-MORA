from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
from substrate.discourse_provenance.models import (
    AssertionMode,
    CrossTurnAttachmentState,
    PerspectiveOwnerClass,
    PerspectiveSourceClass,
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
from substrate.semantic_acquisition import (
    AcquisitionUsabilityClass,
    build_semantic_acquisition,
    derive_semantic_acquisition_contract_view,
    evaluate_semantic_acquisition_downstream_gate,
)


def _g04(text: str, material_id: str):
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
    grounded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m05:{material_id}",
        cooperation_anchor_ref=f"o05:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


@pytest.mark.parametrize(
    ("ablation_id", "ablate"),
    (
        (
            "remove_support_cues",
            lambda bundle: replace(
                bundle,
                wrapped_propositions=tuple(
                    replace(
                        wrapped,
                        source_class=PerspectiveSourceClass.UNKNOWN,
                        commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                    )
                    for wrapped in bundle.wrapped_propositions
                ),
            ),
        ),
        (
            "remove_conflict_cues",
            lambda bundle: replace(
                bundle,
                wrapped_propositions=tuple(
                    replace(
                        wrapped,
                        downstream_constraints=tuple(
                            constraint
                            for constraint in wrapped.downstream_constraints
                            if constraint
                            not in {
                                "clarification_recommended_on_owner_ambiguity",
                                "narrative_binding_blocked_without_commitment_owner",
                            }
                        ),
                        assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                    )
                    for wrapped in bundle.wrapped_propositions
                ),
                ambiguity_reasons=(),
            ),
        ),
        (
            "remove_continuity_signals",
            lambda bundle: replace(
                bundle,
                cross_turn_links=tuple(
                    replace(link, attachment_state=CrossTurnAttachmentState.UNKNOWN)
                    for link in bundle.cross_turn_links
                ),
            ),
        ),
        (
            "remove_repair_metadata",
            lambda bundle: replace(
                bundle,
                cross_turn_links=tuple(
                    replace(link, attachment_state=CrossTurnAttachmentState.STABLE, repair_reason=None)
                    for link in bundle.cross_turn_links
                ),
                ambiguity_reasons=tuple(
                    reason for reason in bundle.ambiguity_reasons if reason != "cross_turn_repair_pending"
                ),
            ),
        ),
        (
            "remove_perspective_sensitive_merge_constraints",
            lambda bundle: replace(
                bundle,
                wrapped_propositions=tuple(
                    replace(
                        wrapped,
                        downstream_constraints=tuple(
                            constraint
                            for constraint in wrapped.downstream_constraints
                            if constraint != "response_should_not_flatten_owner"
                        ),
                    )
                    for wrapped in bundle.wrapped_propositions
                ),
            ),
        ),
    ),
)
def test_ablation_matrix_triggers_targeted_degradation(ablation_id: str, ablate) -> None:
    base = _g04('he said "you are not tired?"', f"m-g05-ablation-{ablation_id}")
    baseline = build_semantic_acquisition(base)
    degraded = build_semantic_acquisition(ablate(base.bundle))

    baseline_sig = {
        (record.acquisition_status.value, record.stability_class.value, record.support_conflict_profile.conflict_score)
        for record in baseline.bundle.acquisition_records
    }
    degraded_sig = {
        (record.acquisition_status.value, record.stability_class.value, record.support_conflict_profile.conflict_score)
        for record in degraded.bundle.acquisition_records
    }
    assert baseline_sig != degraded_sig or baseline.bundle.ambiguity_reasons != degraded.bundle.ambiguity_reasons

    gate = evaluate_semantic_acquisition_downstream_gate(degraded)
    view = derive_semantic_acquisition_contract_view(degraded)
    assert view.requires_status_read is True
    assert view.accepted_provisional_not_commitment is True
    assert "acquisition_status_must_be_read" in gate.restrictions
    if gate.accepted and gate.usability_class is AcquisitionUsabilityClass.DEGRADED_BOUNDED:
        assert "accepted_degraded_requires_restrictions_read" in gate.restrictions
    if ablation_id in {"remove_support_cues", "remove_continuity_signals"}:
        assert gate.usability_class in {
            AcquisitionUsabilityClass.DEGRADED_BOUNDED,
            AcquisitionUsabilityClass.BLOCKED,
        } or "downstream_authority_degraded" in gate.restrictions
