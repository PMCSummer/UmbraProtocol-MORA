from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import FramingStatus
from substrate.discourse_update import ContinuationStatus, RepairClass
from substrate.grounded_semantic import derive_grounded_downstream_contract
from substrate.semantic_acquisition.models import AcquisitionStatus
from substrate.targeted_clarification import InterventionStatus, build_targeted_clarification
from tests.substrate.phase_axis_testkit import build_phase_axis_context


def _dictum_predicate_tokens(ctx) -> set[str]:
    return {
        candidate.predicate_frame.predicate_token_id.lower()
        for candidate in ctx.dictum.bundle.dictum_candidates
    }


def _dictum_predicate_surfaces(ctx) -> set[str]:
    raw_text = ctx.surface.surface.raw_text
    values: set[str] = set()
    for candidate in ctx.dictum.bundle.dictum_candidates:
        start = candidate.predicate_frame.predicate_span.start
        end = candidate.predicate_frame.predicate_span.end
        values.add(raw_text[start:end].strip().lower())
    return values


def _force_kinds(ctx) -> set[str]:
    return {
        hypothesis.illocution_kind.value
        for record in ctx.modus.bundle.hypothesis_records
        for hypothesis in record.illocution_hypotheses
    }


def _proposal_types(ctx) -> set[str]:
    return {proposal.proposal_type.value for proposal in ctx.discourse_update.bundle.update_proposals}


def _repair_classes(ctx) -> set[str]:
    return {repair.repair_class.value for repair in ctx.discourse_update.bundle.repair_triggers}


def _intervention_signature(ctx) -> set[tuple[str, str]]:
    return {
        (record.intervention_status.value, record.uncertainty_class.value)
        for record in ctx.intervention.bundle.intervention_records
    }


def test_axis_dictum_invariant_force_changes_propagate_across_layers() -> None:
    direct = build_phase_axis_context("alpha is stable", "axis-df-direct")
    question = build_phase_axis_context("alpha is stable?", "axis-df-question")
    quoted = build_phase_axis_context('he said "alpha is stable?"', "axis-df-quoted")

    assert direct.dictum.bundle.dictum_candidates
    assert question.dictum.bundle.dictum_candidates
    assert direct.dictum.bundle.no_final_resolution_performed is True
    assert question.dictum.bundle.no_final_resolution_performed is True
    assert _force_kinds(direct) != _force_kinds(quoted)
    assert _proposal_types(direct) != _proposal_types(quoted)
    direct_contract = derive_grounded_downstream_contract(direct.grounded_normative)
    quoted_contract = derive_grounded_downstream_contract(quoted.grounded_normative)
    assert direct_contract.source_mode != quoted_contract.source_mode
    variants = {
        tuple(sorted(_intervention_signature(ctx)))
        for ctx in (direct, question, quoted)
    }
    assert len(variants) >= 2


def test_axis_force_addressivity_can_stay_stable_while_dictum_content_changes() -> None:
    alpha = build_phase_axis_context("alpha collapsed yesterday", "axis-fd-alpha")
    beta = build_phase_axis_context("beta moved yesterday", "axis-fd-beta")

    assert _dictum_predicate_surfaces(alpha) != _dictum_predicate_surfaces(beta)
    forbidden_force = {"quoted_force_candidate", "reported_force_candidate", "echoic_force_candidate"}
    assert not (_force_kinds(alpha) & forbidden_force)
    assert not (_force_kinds(beta) & forbidden_force)
    assert _proposal_types(alpha) == _proposal_types(beta)


def test_axis_same_ambiguity_pressure_but_different_repair_target_stays_localized() -> None:
    reference_case = build_phase_axis_context("this is true", "axis-repair-reference")
    polarity_case = build_phase_axis_context("i did not say that", "axis-repair-polarity")

    assert _repair_classes(reference_case) != _repair_classes(polarity_case)
    assert all(
        repair.suggested_clarification_type.startswith("bounded_")
        for repair in reference_case.discourse_update.bundle.repair_triggers
    )
    assert all(
        repair.suggested_clarification_type.startswith("bounded_")
        for repair in polarity_case.discourse_update.bundle.repair_triggers
    )
    reference_scopes = {
        item
        for record in reference_case.intervention.bundle.intervention_records
        for item in record.minimal_question_spec.clarification_intent.allowed_semantic_scope
        if item.startswith("l06_repair_class:")
    }
    polarity_scopes = {
        item
        for record in polarity_case.intervention.bundle.intervention_records
        for item in record.minimal_question_spec.clarification_intent.allowed_semantic_scope
        if item.startswith("l06_repair_class:")
    }
    assert reference_scopes != polarity_scopes


def test_axis_nonblocking_vs_blocking_uncertainty_changes_intervention_topology() -> None:
    base = build_phase_axis_context("you are tired", "axis-blocking-base")
    nonblocking = build_targeted_clarification(
        replace(
            base.acquisition.bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    acquisition_status=AcquisitionStatus.STABLE_PROVISIONAL,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        unresolved_slots=("temporal_anchor",),
                        conflict_reasons=(),
                    ),
                )
                for record in base.acquisition.bundle.acquisition_records
            ),
        ),
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.DOMINANT_PROVISIONAL_FRAME)
                for record in base.framing.bundle.framing_records
            ),
        ),
        replace(
            base.discourse_update.bundle,
            continuation_states=tuple(
                replace(
                    state,
                    continuation_status=ContinuationStatus.PROPOSAL_ALLOWED_BUT_ACCEPTANCE_REQUIRED,
                    guarded_continue_allowed=False,
                    guarded_continue_forbidden=False,
                    blocked_update_ids=(),
                )
                for state in base.discourse_update.bundle.continuation_states
            ),
            blocked_update_ids=(),
        ),
    )
    blocking = build_targeted_clarification(
        replace(
            base.acquisition.bundle,
            acquisition_records=tuple(
                replace(
                    record,
                    acquisition_status=AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
                    support_conflict_profile=replace(
                        record.support_conflict_profile,
                        unresolved_slots=("source_scope", "commitment_owner"),
                        conflict_reasons=("source_scope_unknown", "commitment_owner_ambiguous"),
                    ),
                )
                for record in base.acquisition.bundle.acquisition_records
            ),
        ),
        replace(
            base.framing.bundle,
            framing_records=tuple(
                replace(record, framing_status=FramingStatus.BLOCKED_HIGH_IMPACT_FRAME)
                for record in base.framing.bundle.framing_records
            ),
        ),
        replace(
            base.discourse_update.bundle,
            continuation_states=tuple(
                replace(
                    state,
                    continuation_status=ContinuationStatus.BLOCKED_PENDING_REPAIR,
                    guarded_continue_allowed=False,
                    guarded_continue_forbidden=True,
                )
                for state in base.discourse_update.bundle.continuation_states
            ),
        ),
    )

    nonblocking_statuses = {record.intervention_status for record in nonblocking.bundle.intervention_records}
    blocking_statuses = {record.intervention_status for record in blocking.bundle.intervention_records}
    assert InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY not in nonblocking_statuses
    assert InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY in blocking_statuses
    assert nonblocking_statuses != blocking_statuses
