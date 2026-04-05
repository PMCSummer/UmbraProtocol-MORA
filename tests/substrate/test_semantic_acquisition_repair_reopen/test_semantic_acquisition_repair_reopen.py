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
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.runtime_semantic_graph import build_runtime_semantic_graph
from substrate.scope_attribution import build_scope_attribution
from substrate.semantic_acquisition import (
    AcquisitionStatus,
    RevisionConditionKind,
    build_semantic_acquisition,
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
    grounded = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m05:{material_id}",
        cooperation_anchor_ref=f"o05:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


def test_correction_and_quote_repair_create_explicit_reopen_hooks() -> None:
    base = _g04("no, i did not say that", "m-g05-reopen")
    repaired_bundle = replace(
        base.bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                assertion_mode=AssertionMode.DENIAL_FRAME,
                commitment_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                perspective_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                downstream_constraints=tuple(dict.fromkeys((*wrapped.downstream_constraints, "clarification_recommended_on_owner_ambiguity"))),
            )
            for wrapped in base.bundle.wrapped_propositions
        ),
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.REPAIR_PENDING)
            for link in base.bundle.cross_turn_links
        ),
    )
    result = build_semantic_acquisition(repaired_bundle)
    kinds = {
        cond.condition_kind
        for record in result.bundle.acquisition_records
        for cond in record.revision_conditions
    }
    assert RevisionConditionKind.REOPEN_ON_CORRECTION in kinds
    assert RevisionConditionKind.REOPEN_ON_QUOTE_REPAIR in kinds
    assert RevisionConditionKind.REOPEN_ON_CLARIFICATION_ANSWER in kinds


def test_reopen_is_explicit_not_hidden_duplication() -> None:
    stable_base = _g04("i am tired", "m-g05-reopen-stable")
    stable_bundle = replace(
        stable_base.bundle,
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
            for wrapped in stable_base.bundle.wrapped_propositions
        ),
        chain_records=tuple(
            replace(
                record,
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            )
            for record in stable_base.bundle.chain_records
        ),
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.STABLE, repair_reason=None)
            for link in stable_base.bundle.cross_turn_links
        ),
        ambiguity_reasons=(),
    )
    stable = build_semantic_acquisition(stable_bundle)
    corrected_base = replace(
        stable_base,
        bundle=stable_bundle,
    )
    corrected_bundle = replace(
        corrected_base.bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                assertion_mode=AssertionMode.DENIAL_FRAME,
                commitment_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                perspective_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                downstream_constraints=tuple(dict.fromkeys((*wrapped.downstream_constraints, "clarification_recommended_on_owner_ambiguity"))),
            )
            for wrapped in corrected_base.bundle.wrapped_propositions
        ),
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.REPAIR_PENDING)
            for link in corrected_base.bundle.cross_turn_links
        ),
    )
    corrected = build_semantic_acquisition(corrected_bundle)

    assert len(stable.bundle.acquisition_records) == len(corrected.bundle.acquisition_records)
    stable_by_prop = {record.proposition_id: record for record in stable.bundle.acquisition_records}
    corrected_by_prop = {record.proposition_id: record for record in corrected.bundle.acquisition_records}
    assert stable_by_prop.keys() == corrected_by_prop.keys()
    assert any(record.acquisition_status is AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION for record in corrected.bundle.acquisition_records)
    assert any(record.revision_conditions for record in corrected.bundle.acquisition_records)
    assert any(
        stable_by_prop[prop_id].acquisition_status != corrected_by_prop[prop_id].acquisition_status
        or stable_by_prop[prop_id].support_conflict_profile.conflict_score
        != corrected_by_prop[prop_id].support_conflict_profile.conflict_score
        or {
            cond.condition_kind for cond in stable_by_prop[prop_id].revision_conditions
        }
        != {
            cond.condition_kind for cond in corrected_by_prop[prop_id].revision_conditions
        }
        for prop_id in stable_by_prop
    )
