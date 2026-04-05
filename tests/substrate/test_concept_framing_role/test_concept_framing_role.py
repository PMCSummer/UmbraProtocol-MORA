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
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative
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


def test_support_conflict_profile_is_decision_core_for_framing_status() -> None:
    base = _g05("you are tired", "m-g06-role-base")
    base_bundle = _normalized_acquisition_bundle(base.bundle)
    support_bundle = replace(
        base_bundle,
        acquisition_records=tuple(
            replace(
                record,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    support_reasons=tuple(dict.fromkeys((*record.support_conflict_profile.support_reasons, "cross_turn_continuity_support"))),
                    conflict_reasons=(),
                    conflict_score=0.0,
                ),
            )
            for record in base_bundle.acquisition_records
        ),
    )
    conflict_bundle = replace(
        base_bundle,
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
            )
            for record in base_bundle.acquisition_records
        ),
    )
    support = build_concept_framing(support_bundle)
    conflict = build_concept_framing(conflict_bundle)

    support_status = {record.framing_status for record in support.bundle.framing_records}
    conflict_status = {record.framing_status for record in conflict.bundle.framing_records}
    assert support_status != conflict_status
    assert FramingStatus.BLOCKED_HIGH_IMPACT_FRAME in conflict_status or FramingStatus.UNDERFRAMED_MEANING in conflict_status


def test_repeated_surface_without_structural_support_does_not_force_dominant_frame() -> None:
    base = _g05("you are tired", "m-g06-role-repeat")
    base_bundle = _normalized_acquisition_bundle(base.bundle)
    repeated_bundle = replace(
        base_bundle,
        acquisition_records=tuple(base_bundle.acquisition_records)
        + tuple(
            replace(
                record,
                acquisition_id=f"{record.acquisition_id}-rep",
                proposition_id=f"{record.proposition_id}-rep",
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    support_reasons=(),
                    support_score=0.0,
                    conflict_reasons=tuple(dict.fromkeys((*record.support_conflict_profile.conflict_reasons, "source_scope_unknown"))),
                ),
            )
            for record in base_bundle.acquisition_records
        ),
    )
    result = build_concept_framing(repeated_bundle)
    statuses = {record.framing_status for record in result.bundle.framing_records}
    assert FramingStatus.DOMINANT_PROVISIONAL_FRAME not in statuses or FramingStatus.COMPETING_FRAMES in statuses
