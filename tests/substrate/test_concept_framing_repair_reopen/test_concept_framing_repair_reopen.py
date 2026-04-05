from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing import FramingStatus, ReframingConditionKind, build_concept_framing
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


def test_correction_and_quote_repair_produce_explicit_reframing_conditions() -> None:
    base = _g05("no, i did not say that", "m-g06-reopen")
    repaired_bundle = replace(
        base.bundle,
        acquisition_records=tuple(
            replace(
                record,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    conflict_reasons=tuple(
                        dict.fromkeys(
                            (
                                *record.support_conflict_profile.conflict_reasons,
                                "cross_turn_repair_pending",
                                "clarification_required",
                            )
                        )
                    ),
                ),
            )
            for record in base.bundle.acquisition_records
        ),
    )
    result = build_concept_framing(repaired_bundle)
    kinds = {
        condition.condition_kind
        for record in result.bundle.framing_records
        for condition in record.reframing_conditions
    }
    assert ReframingConditionKind.REOPEN_ON_CORRECTION in kinds or ReframingConditionKind.REOPEN_ON_QUOTE_REPAIR in kinds
    assert ReframingConditionKind.REOPEN_ON_DISCOURSE_CONTINUATION in kinds


def test_repair_changes_prior_framing_materially_not_only_adds_duplicate() -> None:
    stable_base = _g05("i am tired", "m-g06-reopen-stable")
    stable_bundle = _normalized_acquisition_bundle(stable_base.bundle)
    stable = build_concept_framing(stable_bundle)
    corrected_base = replace(
        stable_base,
        bundle=stable_bundle,
    )
    corrected_bundle = replace(
        corrected_base.bundle,
        acquisition_records=tuple(
            replace(
                record,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    conflict_reasons=tuple(
                        dict.fromkeys(
                            (*record.support_conflict_profile.conflict_reasons, "clarification_required", "source_scope_unknown")
                        )
                    ),
                    unresolved_slots=tuple(dict.fromkeys((*record.support_conflict_profile.unresolved_slots, "source_scope"))),
                ),
            )
            for record in corrected_base.bundle.acquisition_records
        ),
    )
    corrected = build_concept_framing(corrected_bundle)

    stable_by_acq = {record.acquisition_id: record for record in stable.bundle.framing_records}
    corrected_by_acq = {record.acquisition_id: record for record in corrected.bundle.framing_records}
    assert stable_by_acq.keys() == corrected_by_acq.keys()
    assert any(record.framing_status in {FramingStatus.UNDERFRAMED_MEANING, FramingStatus.BLOCKED_HIGH_IMPACT_FRAME} for record in corrected.bundle.framing_records)
    assert any(
        stable_by_acq[key].framing_status != corrected_by_acq[key].framing_status
        or stable_by_acq[key].vulnerability_profile.vulnerability_level != corrected_by_acq[key].vulnerability_profile.vulnerability_level
        or {cond.condition_kind for cond in stable_by_acq[key].reframing_conditions}
        != {cond.condition_kind for cond in corrected_by_acq[key].reframing_conditions}
        for key in stable_by_acq
    )
