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
    grounded = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m05:{material_id}",
        cooperation_anchor_ref=f"o05:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


def test_status_drives_downstream_contract_not_raw_candidate_presence() -> None:
    base = _g04("i am tired", "m-g05-status-base")
    stable_bundle = replace(
        base.bundle,
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
            for wrapped in base.bundle.wrapped_propositions
        ),
        chain_records=tuple(
            replace(
                record,
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            )
            for record in base.bundle.chain_records
        ),
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.STABLE, repair_reason=None)
            for link in base.bundle.cross_turn_links
        ),
        ambiguity_reasons=(),
    )
    stable = build_semantic_acquisition(stable_bundle)
    stable_view = derive_semantic_acquisition_contract_view(stable)

    weak_bundle = replace(
        stable_bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                assertion_mode=AssertionMode.QUESTION_FRAME,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            )
            for wrapped in stable_bundle.wrapped_propositions
        ),
    )
    weak = build_semantic_acquisition(weak_bundle)
    weak_view = derive_semantic_acquisition_contract_view(weak)

    context_bundle = replace(
        stable_bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                source_class=PerspectiveSourceClass.UNKNOWN,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                assertion_mode=AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
                downstream_constraints=tuple(
                    constraint
                    for constraint in wrapped.downstream_constraints
                    if constraint not in {
                        "response_should_not_flatten_owner",
                        "response_should_not_echo_as_direct_user_belief",
                    }
                ),
            )
            for wrapped in stable_bundle.wrapped_propositions
        ),
        chain_records=tuple(
            replace(
                record,
                source_class=PerspectiveSourceClass.UNKNOWN,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                assertion_mode=AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
            )
            for record in stable_bundle.chain_records
        ),
    )
    context = build_semantic_acquisition(context_bundle)
    context_view = derive_semantic_acquisition_contract_view(context)

    assert stable_view.stable_provisional_present is True or stable_view.weak_provisional_present is True
    assert weak_view.weak_provisional_present is True or weak_view.blocked_pending_clarification_present is True
    assert (
        context_view.context_only_present is True
        or context_view.blocked_pending_clarification_present is True
        or context_view.weak_provisional_present is True
    )
    assert stable_view.provisional_uptake_allowed is True
    assert context_view.memory_uptake_allowed is False
    assert stable_view.requires_status_read is True
    assert stable_view.requires_restrictions_read is True
    assert stable_view.accepted_provisional_not_commitment is True
    assert context_view.requires_status_read is True
    assert context_view.degraded_authority_present is True
    assert context_view.accepted_degraded_requires_restrictions_read is True


def test_competing_and_blocked_meanings_are_first_class_not_hidden_in_score() -> None:
    base = _g04("you are tired", "m-g05-compete")
    if len(base.bundle.wrapped_propositions) == 1:
        wrapped = base.bundle.wrapped_propositions[0]
        chain = base.bundle.chain_records[0]
        base = replace(
            base,
            bundle=replace(
                base.bundle,
                wrapped_propositions=(
                    wrapped,
                    replace(
                        wrapped,
                        wrapper_id=f"{wrapped.wrapper_id}-alt",
                        proposition_id=f"{wrapped.proposition_id}-alt",
                        semantic_unit_id=wrapped.semantic_unit_id,
                        commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        assertion_mode=AssertionMode.QUOTED_EXTERNAL_CONTENT,
                        source_class=PerspectiveSourceClass.QUOTED_SPEAKER,
                    ),
                ),
                chain_records=(
                    chain,
                    replace(
                        chain,
                        chain_id=f"{chain.chain_id}-alt",
                        proposition_id=f"{chain.proposition_id}-alt",
                        commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        assertion_mode=AssertionMode.QUOTED_EXTERNAL_CONTENT,
                        source_class=PerspectiveSourceClass.QUOTED_SPEAKER,
                    ),
                ),
                cross_turn_links=(
                    *base.bundle.cross_turn_links,
                    replace(
                        base.bundle.cross_turn_links[0],
                        link_id=f"{base.bundle.cross_turn_links[0].link_id}-alt",
                        chain_id=f"{base.bundle.chain_records[0].chain_id}-alt",
                        attachment_state=CrossTurnAttachmentState.REPAIR_PENDING,
                    ),
                ),
            ),
        )

    result = build_semantic_acquisition(base)
    gate = evaluate_semantic_acquisition_downstream_gate(result)
    statuses = {record.acquisition_status for record in result.bundle.acquisition_records}
    assert AcquisitionStatus.COMPETING_PROVISIONAL in statuses or AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION in statuses
    assert "competing_meanings_preserved" in gate.restrictions or "closure_blocked_pending_clarification" in gate.restrictions
    assert "memory_uptake_blocked" in gate.restrictions


def test_top1_confidence_shortcut_not_equivalent_to_g05_mechanism() -> None:
    base = _g04("you are tired", "m-g05-top1")
    if len(base.bundle.wrapped_propositions) == 1:
        wrapped = base.bundle.wrapped_propositions[0]
        chain = base.bundle.chain_records[0]
        base = replace(
            base,
            bundle=replace(
                base.bundle,
                wrapped_propositions=(
                    wrapped,
                    replace(
                        wrapped,
                        wrapper_id=f"{wrapped.wrapper_id}-alt",
                        proposition_id=f"{wrapped.proposition_id}-alt",
                        commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        assertion_mode=AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
                        source_class=PerspectiveSourceClass.REPORTED_SOURCE,
                    ),
                ),
                chain_records=(
                    chain,
                    replace(
                        chain,
                        chain_id=f"{chain.chain_id}-alt",
                        proposition_id=f"{chain.proposition_id}-alt",
                        commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                        assertion_mode=AssertionMode.REPORTED_EXTERNAL_COMMITMENT,
                        source_class=PerspectiveSourceClass.REPORTED_SOURCE,
                    ),
                ),
            ),
        )

    result = build_semantic_acquisition(base)
    statuses = {record.acquisition_status for record in result.bundle.acquisition_records}
    naive_top1 = max(result.bundle.acquisition_records, key=lambda r: r.confidence)
    naive_claims_stable = naive_top1.acquisition_status is AcquisitionStatus.STABLE_PROVISIONAL
    assert (
        AcquisitionStatus.COMPETING_PROVISIONAL in statuses
        or AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION in statuses
        or not naive_claims_stable
    )


def test_gate_exposes_usable_vs_degraded_bounded_acquisition() -> None:
    stable = build_semantic_acquisition(_g04("i am tired", "m-g05-gate-stable"))
    stable_gate = evaluate_semantic_acquisition_downstream_gate(stable)
    degraded = build_semantic_acquisition(_g04("if you are tired?", "m-g05-gate-degraded"))
    degraded_gate = evaluate_semantic_acquisition_downstream_gate(degraded)

    assert stable_gate.usability_class in {
        AcquisitionUsabilityClass.USABLE_BOUNDED,
        AcquisitionUsabilityClass.DEGRADED_BOUNDED,
    }
    assert degraded_gate.usability_class in {
        AcquisitionUsabilityClass.DEGRADED_BOUNDED,
        AcquisitionUsabilityClass.BLOCKED,
    }
    if degraded_gate.accepted:
        assert "accepted_degraded_requires_restrictions_read" in degraded_gate.restrictions
    assert "accepted_provisional_not_commitment" in stable_gate.restrictions
