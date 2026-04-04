from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing import (
    FramingUsabilityClass,
    build_concept_framing,
    derive_concept_framing_contract_view,
    evaluate_concept_framing_downstream_gate,
)
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
from substrate.semantic_acquisition import build_semantic_acquisition
from substrate.semantic_acquisition.models import AcquisitionStatus


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
    grounded = build_grounded_semantic_substrate(
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
                    conflict_reasons=(),
                    conflict_score=0.0,
                    unresolved_slots=(),
                ),
                revision_conditions=(),
                downstream_permissions=("no_final_semantic_closure", "allow_provisional_semantic_uptake"),
            )
            for record in bundle.acquisition_records
        ),
        ambiguity_reasons=(),
    )


def test_framing_contract_requires_status_usability_and_cautions_read() -> None:
    base = _g05("i am tired", "m-g06-contract-base")
    framed = build_concept_framing(base)
    view = derive_concept_framing_contract_view(framed)
    gate = evaluate_concept_framing_downstream_gate(framed)

    assert view.requires_status_read is True
    assert view.requires_cautions_read is True
    assert view.accepted_provisional_not_closure is True
    assert "l06_update_proposal_absent" in gate.restrictions
    assert "framing_requires_discourse_update_read" in gate.restrictions
    assert view.strong_closure_permitted is False


def test_blocked_or_competing_high_impact_frames_do_not_look_normal() -> None:
    base = _g05("i am tired", "m-g06-contract-high-impact")
    perspective = base.bundle
    degraded_bundle = replace(
        perspective,
        acquisition_records=tuple(
            replace(
                record,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    conflict_reasons=tuple(
                        dict.fromkeys(
                            (
                                *record.support_conflict_profile.conflict_reasons,
                                "clarification_required",
                                "binding_blocked",
                                "source_scope_unknown",
                            )
                        )
                    ),
                    unresolved_slots=tuple(dict.fromkeys((*record.support_conflict_profile.unresolved_slots, "source_scope"))),
                ),
                acquisition_status=record.acquisition_status,
            )
            for record in perspective.acquisition_records
        ),
    )
    framed = build_concept_framing(degraded_bundle)
    view = derive_concept_framing_contract_view(framed)
    gate = evaluate_concept_framing_downstream_gate(framed)

    assert view.planning_blocked_high_impact_frame is True
    assert view.memory_uptake_allowed is False
    assert view.accepted_degraded_requires_restrictions_read is True
    assert gate.usability_class in {FramingUsabilityClass.DEGRADED_BOUNDED, FramingUsabilityClass.BLOCKED}


def test_similar_surface_different_upstream_structure_changes_frame_contract() -> None:
    base = _g05("you are tired", "m-g06-contract-surface")
    base_bundle = _normalized_acquisition_bundle(base.bundle)
    conservative = build_concept_framing(base_bundle)

    escalated_bundle = replace(
        base.bundle,
        acquisition_records=tuple(
            replace(
                record,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    conflict_reasons=tuple(dict.fromkeys((*record.support_conflict_profile.conflict_reasons, "owner_flattening_risk"))),
                ),
            )
            for record in base_bundle.acquisition_records
        ),
    )
    escalated = build_concept_framing(escalated_bundle)

    conservative_view = derive_concept_framing_contract_view(conservative)
    escalated_view = derive_concept_framing_contract_view(escalated)
    assert (
        conservative_view.competing_frames_present != escalated_view.competing_frames_present
        or conservative_view.blocked_high_impact_frame_present != escalated_view.blocked_high_impact_frame_present
        or conservative_view.planning_blocked_high_impact_frame != escalated_view.planning_blocked_high_impact_frame
    )
