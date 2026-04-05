from __future__ import annotations

from dataclasses import replace

from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
from substrate.discourse_provenance.models import (
    AssertionMode,
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
    grounded = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref=f"m05:{material_id}",
        cooperation_anchor_ref=f"o05:{material_id}",
    )
    graph = build_runtime_semantic_graph(grounded)
    applicability = build_scope_attribution(graph)
    return build_discourse_provenance_chain(applicability)


def test_paraphrastic_support_is_clustered_as_compatible() -> None:
    base = _g04("i am tired", "m-g05-merge-compatible")
    wrapped = base.bundle.wrapped_propositions[0]
    chain = base.bundle.chain_records[0]
    supported_bundle = replace(
        base.bundle,
        wrapped_propositions=(
            replace(
                wrapped,
                semantic_unit_id="unit-merge-compatible",
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            ),
            replace(
                wrapped,
                wrapper_id=f"{wrapped.wrapper_id}-paraphrase",
                proposition_id=f"{wrapped.proposition_id}-paraphrase",
                semantic_unit_id="unit-merge-compatible",
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            ),
        ),
        chain_records=(
            replace(
                chain,
                semantic_unit_id="unit-merge-compatible",
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            ),
            replace(
                chain,
                chain_id=f"{chain.chain_id}-paraphrase",
                proposition_id=f"{chain.proposition_id}-paraphrase",
                semantic_unit_id="unit-merge-compatible",
                assertion_mode=AssertionMode.DIRECT_CURRENT_COMMITMENT,
                source_class=PerspectiveSourceClass.CURRENT_UTTERER,
                commitment_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
                perspective_owner=PerspectiveOwnerClass.CURRENT_UTTERER,
            ),
        ),
    )
    result = build_semantic_acquisition(supported_bundle)
    assert any(cluster.compatible_member_ids for cluster in result.bundle.cluster_links)
    assert not any(record.acquisition_status is AcquisitionStatus.COMPETING_PROVISIONAL for record in result.bundle.acquisition_records)


def test_similar_wording_with_owner_scope_incompatibility_stays_separate_as_competing() -> None:
    base = _g04("you are tired", "m-g05-merge-competing")
    wrapped = base.bundle.wrapped_propositions[0]
    chain = base.bundle.chain_records[0]
    incompatible_bundle = replace(
        base.bundle,
        wrapped_propositions=(
            replace(
                wrapped,
                semantic_unit_id="unit-merge-incompatible",
            ),
            replace(
                wrapped,
                wrapper_id=f"{wrapped.wrapper_id}-incompatible",
                proposition_id=f"{wrapped.proposition_id}-incompatible",
                semantic_unit_id="unit-merge-incompatible",
                assertion_mode=AssertionMode.QUOTED_EXTERNAL_CONTENT,
                source_class=PerspectiveSourceClass.QUOTED_SPEAKER,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                downstream_constraints=tuple(dict.fromkeys((*wrapped.downstream_constraints, "response_should_not_flatten_owner"))),
            ),
        ),
        chain_records=(
            replace(
                chain,
                semantic_unit_id="unit-merge-incompatible",
            ),
            replace(
                chain,
                chain_id=f"{chain.chain_id}-incompatible",
                proposition_id=f"{chain.proposition_id}-incompatible",
                semantic_unit_id="unit-merge-incompatible",
                assertion_mode=AssertionMode.QUOTED_EXTERNAL_CONTENT,
                source_class=PerspectiveSourceClass.QUOTED_SPEAKER,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
            ),
        ),
    )
    result = build_semantic_acquisition(incompatible_bundle)
    assert any(record.acquisition_status is AcquisitionStatus.COMPETING_PROVISIONAL for record in result.bundle.acquisition_records)
    assert any(cluster.competing_member_ids for cluster in result.bundle.cluster_links)


def test_surface_suffix_similarity_without_shared_semantic_unit_does_not_force_merge() -> None:
    base = _g04("you are tired", "m-g05-merge-surface-only")
    wrapped = base.bundle.wrapped_propositions[0]
    chain = base.bundle.chain_records[0]
    surface_only_bundle = replace(
        base.bundle,
        wrapped_propositions=(
            replace(
                wrapped,
                semantic_unit_id=None,
                proposition_id="surface-core",
                wrapper_id="wrap-surface-core",
            ),
            replace(
                wrapped,
                semantic_unit_id=None,
                proposition_id="surface-core-alt",
                wrapper_id="wrap-surface-core-alt",
                assertion_mode=AssertionMode.QUOTED_EXTERNAL_CONTENT,
                source_class=PerspectiveSourceClass.QUOTED_SPEAKER,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
            ),
        ),
        chain_records=(
            replace(
                chain,
                semantic_unit_id=None,
                proposition_id="surface-core",
                chain_id="chain-surface-core",
            ),
            replace(
                chain,
                semantic_unit_id=None,
                proposition_id="surface-core-alt",
                chain_id="chain-surface-core-alt",
                assertion_mode=AssertionMode.QUOTED_EXTERNAL_CONTENT,
                source_class=PerspectiveSourceClass.QUOTED_SPEAKER,
                commitment_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
                perspective_owner=PerspectiveOwnerClass.EXTERNAL_OWNER,
            ),
        ),
    )
    result = build_semantic_acquisition(surface_only_bundle)
    assert not any(record.acquisition_status is AcquisitionStatus.COMPETING_PROVISIONAL for record in result.bundle.acquisition_records)
    assert all(not cluster.competing_member_ids for cluster in result.bundle.cluster_links)
