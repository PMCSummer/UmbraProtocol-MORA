from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing import FramingStatus, build_concept_framing
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
from substrate.grounded_semantic import build_grounded_semantic_substrate_legacy_compatibility
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
    grounded = build_grounded_semantic_substrate_legacy_compatibility(
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


def test_compatible_acquisition_records_stay_compatible_in_frame_links() -> None:
    base = _g05("i am tired", "m-g06-merge-compatible")
    base_bundle = _normalized_acquisition_bundle(base.bundle)
    record = base_bundle.acquisition_records[0]
    supported_bundle = replace(
        base_bundle,
        acquisition_records=(
            replace(record, acquisition_id="acq-compatible-1", semantic_unit_id="unit-compatible"),
            replace(record, acquisition_id="acq-compatible-2", semantic_unit_id="unit-compatible"),
        ),
    )
    result = build_concept_framing(supported_bundle)
    assert any(link.compatible_framing_ids for link in result.bundle.competition_links)
    assert not any(record.framing_status is FramingStatus.COMPETING_FRAMES for record in result.bundle.framing_records)


def test_owner_scope_incompatible_records_become_frame_competition() -> None:
    base = _g05("you are tired", "m-g06-merge-competing")
    base_bundle = _normalized_acquisition_bundle(base.bundle)
    record = base_bundle.acquisition_records[0]
    incompatible_bundle = replace(
        base_bundle,
        acquisition_records=(
            replace(
                record,
                acquisition_id="acq-compete-1",
                semantic_unit_id="unit-compete",
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    conflict_reasons=tuple(dict.fromkeys((*record.support_conflict_profile.conflict_reasons, "source_scope_unknown"))),
                ),
            ),
            replace(
                record,
                acquisition_id="acq-compete-2",
                semantic_unit_id="unit-compete",
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    conflict_reasons=tuple(dict.fromkeys((*record.support_conflict_profile.conflict_reasons, "clarification_required"))),
                ),
            ),
        ),
    )
    result = build_concept_framing(incompatible_bundle)
    assert any(record.framing_status is FramingStatus.COMPETING_FRAMES for record in result.bundle.framing_records)
    assert any(link.competing_framing_ids for link in result.bundle.competition_links)
