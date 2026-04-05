from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.concept_framing import FramingStatus, build_concept_framing
from substrate.concept_framing.models import VulnerabilityLevel
from substrate.dictum_candidates import build_dictum_candidates
from substrate.discourse_update import (
    AcceptanceStatus,
    ContinuationStatus,
    build_discourse_update,
)
from substrate.epistemics import (
    ConfidenceLevel,
    InputMaterial,
    ModalityClass,
    SourceClass,
    SourceMetadata,
    ground_epistemic_input,
)
from substrate.grounded_semantic import (
    OperatorKind,
    build_grounded_semantic_substrate,
)
from substrate.language_surface import build_utterance_surface
from substrate.lexical_grounding import build_lexical_grounding_hypotheses
from substrate.modus_hypotheses import ModusEvidenceKind, build_modus_hypotheses
from substrate.morphosyntax import build_morphosyntax_candidate_space
from substrate.semantic_acquisition import AcquisitionStatus
from substrate.targeted_clarification import (
    G07DecisionBasisCode,
    G07LockoutCode,
    InterventionStatus,
    build_targeted_clarification,
)
from tests.substrate.g01_testkit import build_grounded_semantic_substrate_normative


def _l04_l05_l06_pipeline(text: str, material_id: str):
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
    modus = build_modus_hypotheses(dictum)
    discourse_update = build_discourse_update(modus)
    return surface, dictum, modus, discourse_update


def _drop_l05_evidence_kinds(modus_bundle, forbidden_kinds: set[ModusEvidenceKind]):
    return replace(
        modus_bundle,
        hypothesis_records=tuple(
            replace(
                record,
                evidence_records=tuple(
                    evidence
                    for evidence in record.evidence_records
                    if evidence.evidence_kind not in forbidden_kinds
                ),
            )
            for record in modus_bundle.hypothesis_records
        ),
    )


def test_l05_to_l06_obedience_evidence_gap_changes_repair_and_continuation() -> None:
    _, _, modus, discourse_update = _l04_l05_l06_pipeline(
        'he said "you are tired?"',
        "consumer-obedience-l05-l06-evidence-gap",
    )
    degraded_modus_bundle = _drop_l05_evidence_kinds(
        modus.bundle,
        {ModusEvidenceKind.FORCE_CUE, ModusEvidenceKind.ADDRESSIVITY_CUE},
    )
    degraded = build_discourse_update(degraded_modus_bundle)

    assert len(degraded.bundle.repair_triggers) > len(discourse_update.bundle.repair_triggers)
    assert any(
        "l05_force_evidence_missing" in trigger.repair_basis
        for trigger in degraded.bundle.repair_triggers
    )
    assert any(
        "l05_addressivity_evidence_missing" in trigger.repair_basis
        for trigger in degraded.bundle.repair_triggers
    )
    assert any(
        state.continuation_status is ContinuationStatus.BLOCKED_PENDING_REPAIR
        for state in degraded.bundle.continuation_states
    )


def test_l05_to_l06_obedience_quote_caution_gap_blocks_projection() -> None:
    _, _, modus, _ = _l04_l05_l06_pipeline(
        'he said "you are tired?"',
        "consumer-obedience-l05-l06-quote-caution",
    )
    degraded_modus_bundle = replace(
        modus.bundle,
        hypothesis_records=tuple(
            replace(
                record,
                downstream_cautions=tuple(
                    caution
                    for caution in record.downstream_cautions
                    if caution != "quoted_force_not_current_commitment"
                ),
            )
            for record in modus.bundle.hypothesis_records
        ),
    )
    degraded = build_discourse_update(degraded_modus_bundle)

    assert any(
        "l05_quote_commitment_caution_missing" in trigger.repair_basis
        for trigger in degraded.bundle.repair_triggers
    )
    assert any(
        state.continuation_status is ContinuationStatus.BLOCKED_PENDING_REPAIR
        for state in degraded.bundle.continuation_states
    )


def test_l05_to_g01_obedience_modality_evidence_changes_normative_projection() -> None:
    surface, dictum, modus, discourse_update = _l04_l05_l06_pipeline(
        "maybe alpha is stable",
        "consumer-obedience-l05-g01-modality",
    )
    baseline = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:consumer-obedience-l05-g01-modality",
        cooperation_anchor_ref="o03:consumer-obedience-l05-g01-modality",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    degraded_modus_bundle = _drop_l05_evidence_kinds(
        modus.bundle,
        {ModusEvidenceKind.MODALITY_CUE},
    )
    degraded_discourse_update = build_discourse_update(degraded_modus_bundle)
    degraded = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:consumer-obedience-l05-g01-modality",
        cooperation_anchor_ref="o03:consumer-obedience-l05-g01-modality",
        modus_hypotheses_result_or_bundle=degraded_modus_bundle,
        discourse_update_result_or_bundle=degraded_discourse_update,
    )

    baseline_modality_ops = sum(
        1 for carrier in baseline.bundle.operator_carriers if carrier.operator_kind is OperatorKind.MODALITY
    )
    degraded_modality_ops = sum(
        1 for carrier in degraded.bundle.operator_carriers if carrier.operator_kind is OperatorKind.MODALITY
    )
    assert baseline_modality_ops >= degraded_modality_ops
    assert any(
        "modality evidence record" in marker.reason
        for marker in degraded.bundle.uncertainty_markers
    )


def test_l06_to_g01_obedience_rejects_acceptance_boundary_violations() -> None:
    surface, dictum, modus, discourse_update = _l04_l05_l06_pipeline(
        "alpha is stable",
        "consumer-obedience-l06-g01-acceptance",
    )
    acceptance_required_false = replace(
        discourse_update.bundle,
        update_proposals=tuple(
            replace(proposal, acceptance_required=False)
            for proposal in discourse_update.bundle.update_proposals
        ),
    )
    accepted_status = replace(
        discourse_update.bundle,
        update_proposals=tuple(
            replace(proposal, acceptance_status=AcceptanceStatus.ACCEPTED)
            for proposal in discourse_update.bundle.update_proposals
        ),
    )

    with pytest.raises(TypeError):
        build_grounded_semantic_substrate(
            dictum,
            utterance_surface=surface,
            memory_anchor_ref="m03:consumer-obedience-l06-g01-acceptance",
            cooperation_anchor_ref="o03:consumer-obedience-l06-g01-acceptance",
            modus_hypotheses_result_or_bundle=modus,
            discourse_update_result_or_bundle=acceptance_required_false,
        )
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate(
            dictum,
            utterance_surface=surface,
            memory_anchor_ref="m03:consumer-obedience-l06-g01-accepted",
            cooperation_anchor_ref="o03:consumer-obedience-l06-g01-accepted",
            modus_hypotheses_result_or_bundle=modus,
            discourse_update_result_or_bundle=accepted_status,
        )


def test_l06_to_g07_obedience_blocks_when_acceptance_boundary_is_violated(g07_factory) -> None:
    ctx = g07_factory("you are tired?", "consumer-obedience-l06-g07-acceptance")
    degraded_l06 = replace(
        ctx.discourse_update.bundle,
        update_proposals=tuple(
            replace(proposal, acceptance_status=AcceptanceStatus.ACCEPTED)
            for proposal in ctx.discourse_update.bundle.update_proposals
        ),
    )
    result = build_targeted_clarification(ctx.acquisition, ctx.framing, degraded_l06)
    statuses = {record.intervention_status for record in result.bundle.intervention_records}
    decision_basis = {
        basis
        for record in result.bundle.intervention_records
        for basis in record.decision.decision_basis
    }

    assert InterventionStatus.ASK_NOW not in statuses
    assert InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY in statuses
    assert (
        G07DecisionBasisCode.L06_UPDATE_ACCEPTANCE_BOUNDARY_VIOLATED
        in decision_basis
    )


def test_g05_to_g06_obedience_acquisition_status_changes_frame_topology(g07_factory) -> None:
    ctx = g07_factory("you are dangerous", "consumer-obedience-g05-g06")
    base_record = ctx.acquisition.bundle.acquisition_records[0]

    stable_acq_bundle = replace(
        ctx.acquisition.bundle,
        acquisition_records=(
            replace(
                base_record,
                acquisition_status=AcquisitionStatus.STABLE_PROVISIONAL,
                support_conflict_profile=replace(
                    base_record.support_conflict_profile,
                    support_score=4.0,
                    conflict_score=0.0,
                    conflict_reasons=(),
                    unresolved_slots=(),
                ),
            ),
        ),
    )
    blocked_acq_bundle = replace(
        ctx.acquisition.bundle,
        acquisition_records=(
            replace(
                base_record,
                acquisition_status=AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
                support_conflict_profile=replace(
                    base_record.support_conflict_profile,
                    conflict_score=5.0,
                    conflict_reasons=("binding_blocked", "source_scope_unknown"),
                    unresolved_slots=("commitment_owner", "source_scope"),
                ),
            ),
        ),
    )

    stable_frame = build_concept_framing(stable_acq_bundle)
    blocked_frame = build_concept_framing(blocked_acq_bundle)

    assert stable_frame.bundle.framing_records[0].framing_status is FramingStatus.DOMINANT_PROVISIONAL_FRAME
    assert blocked_frame.bundle.framing_records[0].framing_status is FramingStatus.BLOCKED_HIGH_IMPACT_FRAME
    assert blocked_frame.bundle.framing_records[0].vulnerability_profile.high_impact is True


def test_g05_to_g07_obedience_questionability_changes_with_acquisition_structure(g07_factory) -> None:
    ctx = g07_factory("you are tired?", "consumer-obedience-g05-g07")
    base_record = ctx.acquisition.bundle.acquisition_records[0]
    stable_acq_bundle = replace(
        ctx.acquisition.bundle,
        acquisition_records=(
            replace(
                base_record,
                acquisition_status=AcquisitionStatus.STABLE_PROVISIONAL,
                support_conflict_profile=replace(
                    base_record.support_conflict_profile,
                    unresolved_slots=(),
                    conflict_reasons=(),
                    support_score=4.0,
                    conflict_score=0.0,
                ),
            ),
        ),
    )
    blocked_acq_bundle = replace(
        ctx.acquisition.bundle,
        acquisition_records=(
            replace(
                base_record,
                acquisition_status=AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
                support_conflict_profile=replace(
                    base_record.support_conflict_profile,
                    unresolved_slots=("source_scope", "commitment_owner"),
                    conflict_reasons=("source_scope_unknown",),
                ),
            ),
        ),
    )
    stable_frame_bundle = replace(
        ctx.framing.bundle,
        framing_records=(
            replace(
                ctx.framing.bundle.framing_records[0],
                acquisition_id=base_record.acquisition_id,
                framing_status=FramingStatus.DOMINANT_PROVISIONAL_FRAME,
            ),
        ),
    )
    blocked_frame_bundle = replace(
        ctx.framing.bundle,
        framing_records=(
            replace(
                ctx.framing.bundle.framing_records[0],
                acquisition_id=base_record.acquisition_id,
                framing_status=FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
            ),
        ),
    )
    stable = build_targeted_clarification(stable_acq_bundle, stable_frame_bundle, ctx.discourse_update)
    blocked = build_targeted_clarification(blocked_acq_bundle, blocked_frame_bundle, ctx.discourse_update)
    baseline_statuses = {record.intervention_status for record in stable.bundle.intervention_records}
    blocked_statuses = {record.intervention_status for record in blocked.bundle.intervention_records}

    assert blocked_statuses != baseline_statuses
    assert InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY in blocked_statuses


def test_g06_to_g07_obedience_high_impact_vs_context_changes_lockouts(g07_factory) -> None:
    ctx = g07_factory("you are dangerous", "consumer-obedience-g06-g07")
    base_record = ctx.framing.bundle.framing_records[0]

    high_impact_frame = replace(
        ctx.framing.bundle,
        framing_records=(
            replace(
                base_record,
                framing_status=FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
                vulnerability_profile=replace(
                    base_record.vulnerability_profile,
                    high_impact=True,
                    vulnerability_level=VulnerabilityLevel.HIGH,
                ),
            ),
        ),
    )
    context_only_frame = replace(
        ctx.framing.bundle,
        framing_records=(
            replace(
                base_record,
                framing_status=FramingStatus.CONTEXT_ONLY_FRAME_HINT,
                vulnerability_profile=replace(
                    base_record.vulnerability_profile,
                    high_impact=False,
                    vulnerability_level=VulnerabilityLevel.MODERATE,
                ),
            ),
        ),
    )

    high_impact = build_targeted_clarification(ctx.acquisition, high_impact_frame, ctx.discourse_update)
    context_only = build_targeted_clarification(ctx.acquisition, context_only_frame, ctx.discourse_update)
    high_impact_lockouts = {
        lockout
        for record in high_impact.bundle.intervention_records
        for lockout in record.downstream_lockouts
    }
    context_lockouts = {
        lockout
        for record in context_only.bundle.intervention_records
        for lockout in record.downstream_lockouts
    }

    assert G07LockoutCode.PLANNING_FORBIDDEN_ON_CURRENT_FRAME in high_impact_lockouts
    assert (
        G07LockoutCode.SAFETY_ESCALATION_NOT_AUTHORIZED_FROM_CURRENT_EVIDENCE
        in high_impact_lockouts
    )
    assert G07LockoutCode.APPRAISAL_CONTEXT_ONLY in context_lockouts


def test_g01_runtime_route_is_normative_only_after_legacy_retirement(g07_factory) -> None:
    ctx = g07_factory('he said "alpha is stable?"', "consumer-obedience-route-contrast")
    surface, dictum, modus, discourse_update = _l04_l05_l06_pipeline(
        'he said "alpha is stable?"',
        "consumer-obedience-route-contrast-direct",
    )
    normative = build_grounded_semantic_substrate(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:consumer-obedience-route-contrast",
        cooperation_anchor_ref="o03:consumer-obedience-route-contrast",
        modus_hypotheses_result_or_bundle=modus,
        discourse_update_result_or_bundle=discourse_update,
    )
    with pytest.raises(TypeError):
        build_grounded_semantic_substrate(
            dictum,
            utterance_surface=surface,
            memory_anchor_ref="m03:consumer-obedience-route-compat",
            cooperation_anchor_ref="o03:consumer-obedience-route-compat",
        )
    helper_result = build_grounded_semantic_substrate_normative(
        dictum,
        utterance_surface=surface,
        memory_anchor_ref="m03:consumer-obedience-route-compat",
        cooperation_anchor_ref="o03:consumer-obedience-route-compat",
    )

    assert normative.bundle.normative_l05_l06_route_active is True
    assert helper_result.bundle.normative_l05_l06_route_active is True
    assert any(record.route_class == "normative" for record in normative.bundle.evidence_records)
    assert all(record.route_class != "compatibility" for record in helper_result.bundle.evidence_records)
