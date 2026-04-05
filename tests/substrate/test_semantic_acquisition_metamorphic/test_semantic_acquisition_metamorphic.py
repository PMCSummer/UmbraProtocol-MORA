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
from substrate.semantic_acquisition import build_semantic_acquisition


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


def test_same_lexical_core_with_provenance_variants_changes_acquisition_outcome() -> None:
    direct = build_semantic_acquisition(_g04("you are tired", "m-g05-meta-direct"))
    quote = build_semantic_acquisition(_g04('"you are tired"', "m-g05-meta-quote"))
    report = build_semantic_acquisition(_g04("he said that you are tired", "m-g05-meta-report"))

    resumed_base = _g04('"you are tired"', "m-g05-meta-resumed")
    resumed_bundle = replace(
        resumed_base.bundle,
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.REATTACHED)
            for link in resumed_base.bundle.cross_turn_links
        ),
    )
    resumed = build_semantic_acquisition(resumed_bundle)

    repaired_base = _g04("he said that you are tired", "m-g05-meta-repaired")
    repaired_bundle = replace(
        repaired_base.bundle,
        wrapped_propositions=tuple(
            replace(
                wrapped,
                assertion_mode=AssertionMode.DENIAL_FRAME,
                commitment_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                perspective_owner=PerspectiveOwnerClass.UNRESOLVED_OWNER,
                downstream_constraints=tuple(dict.fromkeys((*wrapped.downstream_constraints, "clarification_recommended_on_owner_ambiguity"))),
            )
            for wrapped in repaired_base.bundle.wrapped_propositions
        ),
        cross_turn_links=tuple(
            replace(link, attachment_state=CrossTurnAttachmentState.REPAIR_PENDING)
            for link in repaired_base.bundle.cross_turn_links
        ),
    )
    repaired = build_semantic_acquisition(repaired_bundle)

    sig = lambda result: {(r.acquisition_status.value, r.stability_class.value) for r in result.bundle.acquisition_records}
    variants = {tuple(sorted(signature)) for signature in map(sig, (direct, quote, report, resumed, repaired))}
    assert len(variants) >= 2


def test_nesting_order_shift_changes_chain_sensitive_acquisition_or_marks_ambiguity() -> None:
    a = build_semantic_acquisition(_g04("petya said masha thinks i am afraid", "m-g05-meta-nest-a"))
    b = build_semantic_acquisition(_g04("petya thinks masha said i am afraid", "m-g05-meta-nest-b"))
    sig_a = {(r.acquisition_status.value, r.support_conflict_profile.conflict_score) for r in a.bundle.acquisition_records}
    sig_b = {(r.acquisition_status.value, r.support_conflict_profile.conflict_score) for r in b.bundle.acquisition_records}
    if sig_a == sig_b:
        assert a.bundle.ambiguity_reasons or b.bundle.ambiguity_reasons
    else:
        assert sig_a != sig_b


def test_same_content_with_modality_shift_changes_revision_and_status_behavior() -> None:
    asserted = build_semantic_acquisition(_g04("you are tired", "m-g05-meta-asserted"))
    hypothetical = build_semantic_acquisition(_g04("if you are tired", "m-g05-meta-hypothetical"))
    questioned = build_semantic_acquisition(_g04("you are tired?", "m-g05-meta-questioned"))

    asserted_revisions = {cond.condition_kind.value for r in asserted.bundle.acquisition_records for cond in r.revision_conditions}
    hypo_revisions = {cond.condition_kind.value for r in hypothetical.bundle.acquisition_records for cond in r.revision_conditions}
    questioned_revisions = {cond.condition_kind.value for r in questioned.bundle.acquisition_records for cond in r.revision_conditions}
    asserted_statuses = {r.acquisition_status.value for r in asserted.bundle.acquisition_records}
    hypo_statuses = {r.acquisition_status.value for r in hypothetical.bundle.acquisition_records}
    questioned_statuses = {r.acquisition_status.value for r in questioned.bundle.acquisition_records}

    assert (
        asserted_revisions != hypo_revisions
        or asserted_revisions != questioned_revisions
        or asserted_statuses != hypo_statuses
        or asserted_statuses != questioned_statuses
        or asserted.bundle.ambiguity_reasons != hypothetical.bundle.ambiguity_reasons
        or asserted.bundle.ambiguity_reasons != questioned.bundle.ambiguity_reasons
    )
