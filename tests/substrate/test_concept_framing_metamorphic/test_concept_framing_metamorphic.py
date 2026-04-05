from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing import build_concept_framing
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_provenance import build_discourse_provenance_chain
from substrate.discourse_provenance.models import CrossTurnAttachmentState
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


def test_near_surface_variants_with_different_provenance_change_framing() -> None:
    direct = build_concept_framing(_g05("you are tired", "m-g06-meta-direct"))
    quote = build_concept_framing(_g05('"you are tired"', "m-g06-meta-quote"))
    report = build_concept_framing(_g05("he said that you are tired", "m-g06-meta-report"))

    sig = lambda result: {
        (record.framing_status.value, record.frame_family.value, tuple(record.downstream_cautions))
        for record in result.bundle.framing_records
    }
    variants = {tuple(sorted(signature)) for signature in map(sig, (direct, quote, report))}
    assert len(variants) >= 2


def test_same_lexical_core_with_repair_transition_reopens_framing() -> None:
    base = _g05('he said "you are tired"', "m-g06-meta-repair-base")
    initial = build_concept_framing(base)
    repaired_bundle = replace(
        base.bundle,
        acquisition_records=tuple(
            replace(
                record,
                support_conflict_profile=replace(
                    record.support_conflict_profile,
                    conflict_reasons=tuple(
                        dict.fromkeys((*record.support_conflict_profile.conflict_reasons, "cross_turn_repair_pending"))
                    ),
                ),
            )
            for record in base.bundle.acquisition_records
        ),
    )
    repaired = build_concept_framing(repaired_bundle)

    initial_sig = {
        (record.framing_status.value, tuple(cond.condition_kind.value for cond in record.reframing_conditions))
        for record in initial.bundle.framing_records
    }
    repaired_sig = {
        (record.framing_status.value, tuple(cond.condition_kind.value for cond in record.reframing_conditions))
        for record in repaired.bundle.framing_records
    }
    assert initial_sig != repaired_sig or repaired.bundle.ambiguity_reasons


def test_modality_like_shift_changes_frame_competition_or_vulnerability() -> None:
    base = _g05("you are tired", "m-g06-meta-assert")
    asserted_bundle = _normalized_acquisition_bundle(base.bundle)
    asserted = build_concept_framing(asserted_bundle)
    hypothetical = build_concept_framing(
        replace(
            asserted_bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        conflict_reasons=("assertion_mode:hypothetical_branch",),
                        conflict_score=1.0,
                    ),
                )
                for record in asserted_bundle.acquisition_records
            ),
        )
    )
    questioned = build_concept_framing(
        replace(
            asserted_bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        conflict_reasons=("assertion_mode:question_frame",),
                        conflict_score=1.0,
                    ),
                )
                for record in asserted_bundle.acquisition_records
            ),
        )
    )

    profile = lambda result: {
        (
            record.frame_family.value,
            record.framing_status.value,
            record.vulnerability_profile.vulnerability_level.value,
        )
        for record in result.bundle.framing_records
    }
    assert profile(asserted) != profile(hypothetical) or profile(asserted) != profile(questioned)
