from __future__ import annotations

from dataclasses import replace

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
from substrate.semantic_acquisition import AcquisitionStatus, build_semantic_acquisition


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


def test_repeated_words_without_support_do_not_imply_stabilization() -> None:
    base = _g04("you are tired", "m-g05-role-repeat")
    repeated_without_support = replace(
        base.bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                wrapper_id=f"{wrapped.wrapper_id}-rep",
                proposition_id=f"{wrapped.proposition_id}-rep",
                source_class=PerspectiveSourceClass.UNKNOWN,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                assertion_mode=AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
                downstream_constraints=(
                    "no_truth_upgrade",
                    "closure_requires_chain_consistency_check",
                ),
            )
            for wrapped in base.bundle.wrapped_propositions
        )
        + tuple(base.bundle.wrapped_propositions),
        chain_records=tuple(
            replace(
                record,
                chain_id=f"{record.chain_id}-rep",
                proposition_id=f"{record.proposition_id}-rep",
                source_class=PerspectiveSourceClass.UNKNOWN,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                assertion_mode=AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
            )
            for record in base.bundle.chain_records
        )
        + tuple(base.bundle.chain_records),
    )
    result = build_semantic_acquisition(repeated_without_support)
    statuses = {record.acquisition_status for record in result.bundle.acquisition_records}
    assert AcquisitionStatus.STABLE_PROVISIONAL not in statuses or AcquisitionStatus.COMPETING_PROVISIONAL in statuses


def test_same_lexical_surface_support_vs_conflict_outcomes_diverge() -> None:
    support_base = _g04("i am tired", "m-g05-role-support")
    supported_bundle = replace(
        support_base.bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                downstream_constraints=tuple(
                    constraint
                    for constraint in wrapped.downstream_constraints
                    if constraint not in {"clarification_recommended_on_owner_ambiguity"}
                ),
            )
            for wrapped in support_base.bundle.wrapped_propositions
        ),
        chain_records=tuple(
            replace(
                record,
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            )
            for record in support_base.bundle.chain_records
        ),
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.STABLE, repair_reason=None)
            for link in support_base.bundle.cross_turn_links
        ),
        ambiguity_reasons=(),
    )
    support = build_semantic_acquisition(supported_bundle)
    conflict_base = _g04("i am tired", "m-g05-role-conflict")
    conflicted_bundle = replace(
        conflict_base.bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                assertion_mode=AssertionMode.QUESTION_FRAME,
                commitment_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                perspective_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                downstream_constraints=(
                    "no_truth_upgrade",
                    "closure_requires_chain_consistency_check",
                    "clarification_recommended_on_owner_ambiguity",
                    "narrative_binding_blocked_without_commitment_owner",
                ),
            )
            for wrapped in conflict_base.bundle.wrapped_propositions
        ),
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.REPAIR_PENDING)
            for link in conflict_base.bundle.cross_turn_links
        ),
    )
    conflict = build_semantic_acquisition(conflicted_bundle)
    support_statuses = {record.acquisition_status for record in support.bundle.acquisition_records}
    conflict_statuses = {record.acquisition_status for record in conflict.bundle.acquisition_records}
    assert support_statuses != conflict_statuses
    assert AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION in conflict_statuses or AcquisitionStatus.WEAK_PROVISIONAL in conflict_statuses
