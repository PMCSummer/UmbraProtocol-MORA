from __future__ import annotations

from dataclasses import dataclass

from substrate.contracts import RuntimeState, TransitionKind, TransitionRequest, TransitionResult, WriterIdentity
from substrate.discourse_update.models import (
    AcceptanceStatus,
    ContinuationStatus,
    DiscourseUpdateBundle,
    DiscourseUpdateResult,
    GuardedContinuationState,
    ProposalType,
    RepairClass,
    RepairTrigger,
    UpdateProposal,
)
from substrate.discourse_update.policy import evaluate_discourse_update_downstream_gate
from substrate.discourse_update.telemetry import (
    build_discourse_update_telemetry,
    discourse_update_result_snapshot,
)
from substrate.modus_hypotheses.models import (
    AddressivityKind,
    IllocutionKind,
    ModusHypothesisBundle,
    ModusHypothesisRecord,
    ModusHypothesisResult,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "l06.validate_typed_inputs",
    "l06.update_proposal_projection",
    "l06.localized_repair_trigger_projection",
    "l06.block_or_guarded_continuation",
    "l06.acceptance_required_gate",
    "l06.downstream_gate",
)

_L06_DEFAULT_DOWNSTREAM_ABSENCE_REASONS: tuple[str, ...] = (
    "downstream_update_acceptor_absent",
    "repair_consumer_absent",
    "discourse_state_mutation_consumer_absent",
    "legacy_g01_bypass_risk_present",
)


@dataclass(frozen=True, slots=True)
class _L06SourceRefs:
    source_modus_ref: str
    source_modus_ref_kind: str
    source_modus_lineage_ref: str
    bundle_ref: str


@dataclass(frozen=True, slots=True)
class _L06DownstreamAbsence:
    downstream_update_acceptor_absent: bool
    repair_consumer_absent: bool
    discourse_state_mutation_consumer_absent: bool
    legacy_g01_bypass_risk_present: bool
    low_coverage_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ContinuationDecision:
    status: ContinuationStatus
    guarded_allowed: bool
    guarded_forbidden: bool
    reason: str


_PROPOSAL_BASE_RESTRICTIONS: tuple[str, ...] = (
    "l06_object_presence_not_acceptance",
    "proposal_requires_acceptance",
    "acceptance_required_must_be_read",
    "accepted_proposal_not_accepted_update",
    "proposal_effects_not_yet_authorized",
    "proposal_not_truth",
    "proposal_not_self_update",
    "update_record_not_state_mutation",
    "interpretation_not_equal_accepted_update",
)

_CONTINUATION_STATUS_PERMISSIONS: dict[ContinuationStatus, tuple[str, ...]] = {
    ContinuationStatus.BLOCKED_PENDING_REPAIR: ("proposal_withheld_pending_repair",),
    ContinuationStatus.GUARDED_CONTINUE: ("proposal_guarded_forwardable_if_limits_read",),
    ContinuationStatus.ABSTAIN_UPDATE_WITHHELD: ("proposal_withheld_not_forwardable",),
    ContinuationStatus.PROPOSAL_ALLOWED_BUT_ACCEPTANCE_REQUIRED: (
        "proposal_forwardable_if_acceptor_exists",
    ),
}

_CONTINUATION_STATUS_RESTRICTIONS: dict[ContinuationStatus, tuple[str, ...]] = {
    ContinuationStatus.BLOCKED_PENDING_REPAIR: ("blocked_update_must_be_read",),
    ContinuationStatus.GUARDED_CONTINUE: (
        "guarded_continue_requires_limits_read",
        "guarded_continue_not_acceptance",
    ),
    ContinuationStatus.ABSTAIN_UPDATE_WITHHELD: ("abstain_update_withheld_must_be_read",),
    ContinuationStatus.PROPOSAL_ALLOWED_BUT_ACCEPTANCE_REQUIRED: (),
}


def build_discourse_update(
    modus_result_or_bundle: ModusHypothesisResult | ModusHypothesisBundle,
) -> DiscourseUpdateResult:
    modus_bundle, source_lineage = _extract_modus_input(modus_result_or_bundle)
    if not modus_bundle.hypothesis_records:
        return _abstain_result(
            modus_bundle=modus_bundle,
            source_lineage=source_lineage,
            reason="l05 hypothesis records are empty",
        )
    proposals: list[UpdateProposal] = []
    repairs: list[RepairTrigger] = []
    continuations: list[GuardedContinuationState] = []
    blocked_update_ids: list[str] = []
    guarded_update_ids: list[str] = []
    ambiguity_reasons = list(modus_bundle.ambiguity_reasons)
    low_coverage_reasons = list(modus_bundle.low_coverage_reasons)

    for index, record in enumerate(modus_bundle.hypothesis_records, start=1):
        proposal_type = _proposal_type_from_record(record)
        proposal_id = f"update-proposal-{index}"
        localized_repairs = _localized_repairs(record, proposal_id)
        repairs.extend(localized_repairs)
        continuation = _continuation_state(
            record=record,
            proposal_id=proposal_id,
            repairs_for_record=tuple(localized_repairs),
            continuation_index=index,
        )
        continuations.append(continuation)
        proposal = UpdateProposal(
            proposal_id=proposal_id,
            source_record_ids=(record.record_id, record.source_dictum_candidate_id),
            proposal_type=proposal_type,
            target_discourse_surface=f"dictum-candidate:{record.source_dictum_candidate_id}",
            proposed_effects=_proposed_effects_from_type(proposal_type),
            acceptance_required=True,
            acceptance_status=AcceptanceStatus.NOT_ACCEPTED,
            commitment_candidate=_commitment_candidate(record),
            proposal_basis=(
                f"dictum:{record.source_dictum_candidate_id}",
                f"entropy:{record.uncertainty_entropy}",
                *record.downstream_cautions,
            ),
            uncertainty_markers=record.uncertainty_markers,
            downstream_permissions=_proposal_permissions_for_continuation(continuation.continuation_status),
            downstream_restrictions=_proposal_restrictions_for_continuation(
                continuation_status=continuation.continuation_status,
                has_localized_repair=bool(localized_repairs),
            ),
            provenance="l06 update proposal from l05 hypothesis record",
        )
        proposals.append(proposal)
        if continuation.continuation_status is ContinuationStatus.BLOCKED_PENDING_REPAIR:
            blocked_update_ids.append(proposal_id)
        elif continuation.continuation_status is ContinuationStatus.GUARDED_CONTINUE:
            guarded_update_ids.append(proposal_id)

    source_refs = _derive_source_refs(
        modus_bundle=modus_bundle,
        proposals=proposals,
        repairs=repairs,
        continuations=continuations,
    )
    downstream_absence = _default_downstream_absence()
    low_coverage_reasons.extend(downstream_absence.low_coverage_reasons)

    bundle = DiscourseUpdateBundle(
        bundle_ref=source_refs.bundle_ref,
        source_modus_ref=source_refs.source_modus_ref,
        source_modus_ref_kind=source_refs.source_modus_ref_kind,
        source_modus_lineage_ref=source_refs.source_modus_lineage_ref,
        source_dictum_ref=modus_bundle.source_dictum_ref,
        source_syntax_ref=modus_bundle.source_syntax_ref,
        source_surface_ref=modus_bundle.source_surface_ref,
        linked_modus_record_ids=tuple(record.record_id for record in modus_bundle.hypothesis_records),
        update_proposals=tuple(proposals),
        repair_triggers=tuple(repairs),
        continuation_states=tuple(continuations),
        blocked_update_ids=tuple(dict.fromkeys(blocked_update_ids)),
        guarded_update_ids=tuple(dict.fromkeys(guarded_update_ids)),
        acceptance_required_count=len(proposals),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        low_coverage_mode=bool(low_coverage_reasons),
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        interpretation_not_equal_accepted_update=True,
        no_common_ground_mutation_performed=True,
        no_self_state_mutation_performed=True,
        no_final_acceptance_performed=True,
        downstream_update_acceptor_absent=downstream_absence.downstream_update_acceptor_absent,
        repair_consumer_absent=downstream_absence.repair_consumer_absent,
        discourse_state_mutation_consumer_absent=downstream_absence.discourse_state_mutation_consumer_absent,
        legacy_g01_bypass_risk_present=downstream_absence.legacy_g01_bypass_risk_present,
        downstream_authority_degraded=True,
        reason="l06 projected acceptance-required discourse updates with localized repair gating",
    )
    gate = evaluate_discourse_update_downstream_gate(bundle)
    telemetry = build_discourse_update_telemetry(
        bundle=bundle,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    source_refs.bundle_ref,
                    source_refs.source_modus_ref,
                    source_refs.source_modus_lineage_ref,
                    modus_bundle.source_dictum_ref,
                    modus_bundle.source_syntax_ref,
                    *((modus_bundle.source_surface_ref,) if modus_bundle.source_surface_ref else ()),
                    *source_lineage,
                )
            )
        ),
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="l05 interpretation hypotheses became acceptance-required update proposals and localized repair triggers",
    )
    partial_known_reason = (
        "; ".join(bundle.ambiguity_reasons)
        if bundle.ambiguity_reasons
        else ("; ".join(bundle.low_coverage_reasons) if bundle.low_coverage_reasons else None)
    )
    return DiscourseUpdateResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=_estimate_result_confidence(bundle),
        partial_known=bool(bundle.ambiguity_reasons or bundle.low_coverage_mode),
        partial_known_reason=partial_known_reason,
        abstain=not gate.accepted,
        abstain_reason=None if gate.accepted else gate.reason,
        no_final_acceptance_performed=True,
    )


def discourse_update_result_to_payload(result: DiscourseUpdateResult) -> dict[str, object]:
    return discourse_update_result_snapshot(result)


def persist_discourse_update_result_via_f01(
    *,
    result: DiscourseUpdateResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("l06-discourse-update-proposals-and-repair-triggers",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"discourse-update-step-{transition_id}",
            "discourse_update_snapshot": discourse_update_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_modus_input(
    modus_result_or_bundle: ModusHypothesisResult | ModusHypothesisBundle,
) -> tuple[ModusHypothesisBundle, tuple[str, ...]]:
    if isinstance(modus_result_or_bundle, ModusHypothesisResult):
        return modus_result_or_bundle.bundle, modus_result_or_bundle.telemetry.source_lineage
    if isinstance(modus_result_or_bundle, ModusHypothesisBundle):
        return modus_result_or_bundle, ()
    raise TypeError("build_discourse_update requires ModusHypothesisResult or ModusHypothesisBundle")


def _proposal_type_from_record(record: ModusHypothesisRecord) -> ProposalType:
    kinds = {hypothesis.illocution_kind for hypothesis in record.illocution_hypotheses}
    if IllocutionKind.QUOTED_FORCE_CANDIDATE in kinds:
        return ProposalType.QUOTED_CONTENT_UPDATE
    if IllocutionKind.REPORTED_FORCE_CANDIDATE in kinds:
        return ProposalType.REPORTED_CONTENT_UPDATE
    if IllocutionKind.ECHOIC_FORCE_CANDIDATE in kinds:
        return ProposalType.ECHOIC_CONTENT_UPDATE
    if IllocutionKind.INTERROGATIVE_CANDIDATE in kinds:
        return ProposalType.QUESTION_INTERPRETATION_UPDATE
    if IllocutionKind.DIRECTIVE_CANDIDATE in kinds:
        return ProposalType.DIRECTIVE_INTERPRETATION_UPDATE
    if IllocutionKind.UNKNOWN_FORCE_CANDIDATE in kinds and len(kinds) == 1:
        return ProposalType.UNKNOWN_INTERPRETATION_UPDATE
    return ProposalType.ASSERTION_UPDATE


def _proposed_effects_from_type(proposal_type: ProposalType) -> tuple[str, ...]:
    if proposal_type is ProposalType.QUESTION_INTERPRETATION_UPDATE:
        return ("interpret_as_question_candidate", "defer_commitment_binding")
    if proposal_type is ProposalType.DIRECTIVE_INTERPRETATION_UPDATE:
        return ("interpret_as_directive_candidate", "require_permission_bridge")
    if proposal_type in {ProposalType.REPORTED_CONTENT_UPDATE, ProposalType.QUOTED_CONTENT_UPDATE, ProposalType.ECHOIC_CONTENT_UPDATE}:
        return ("bind_reported_or_quoted_content_candidate", "prevent_current_speaker_commitment_transfer")
    if proposal_type is ProposalType.UNKNOWN_INTERPRETATION_UPDATE:
        return ("preserve_unknown_interpretation", "withhold_update_acceptance")
    return ("interpret_as_assertive_candidate", "require_acceptance_before_update")


def _commitment_candidate(record: ModusHypothesisRecord) -> bool:
    if record.quoted_speech_state.quote_or_echo_present:
        return False
    if "addressivity_target_unresolved" in record.downstream_cautions:
        return False
    return True


def _localized_repairs(record: ModusHypothesisRecord, proposal_id: str) -> tuple[RepairTrigger, ...]:
    repairs: list[RepairTrigger] = []
    repair_index = 0
    for marker in record.uncertainty_markers:
        repair_index += 1
        repair = _repair_from_marker(
            record=record,
            marker=marker,
            proposal_id=proposal_id,
            repair_id=f"repair-{record.record_id}-{repair_index}",
        )
        if repair is not None:
            repairs.append(repair)
    if not repairs and record.uncertainty_entropy >= 0.75:
        repairs.append(
            RepairTrigger(
                repair_id=f"repair-{record.record_id}-entropy",
                repair_class=RepairClass.FORCE_REPAIR,
                localized_trouble_source="illocution_entropy",
                localized_ref_ids=(record.record_id,),
                why_this_is_broken="force alternatives remain high-entropy and require localized disambiguation",
                suggested_clarification_type="bounded_force_disambiguation",
                blocked_updates=(proposal_id,),
                guarded_continue_allowed=False,
                guarded_continue_forbidden=True,
                repair_basis=("high_illocution_entropy",),
                provenance="l06 localized force repair from l05 entropy profile",
            )
        )
    return tuple(repairs)


def _repair_from_marker(
    *,
    record: ModusHypothesisRecord,
    marker: str,
    proposal_id: str,
    repair_id: str,
) -> RepairTrigger | None:
    if marker == "unresolved_argument_slots":
        return RepairTrigger(
            repair_id=repair_id,
            repair_class=RepairClass.MISSING_ARGUMENT_REPAIR,
            localized_trouble_source="argument_slot_binding",
            localized_ref_ids=(record.source_dictum_candidate_id, record.record_id),
            why_this_is_broken="argument slot unresolved and update target cannot be safely committed",
            suggested_clarification_type="bounded_argument_binding",
            blocked_updates=(proposal_id,),
            guarded_continue_allowed=False,
            guarded_continue_forbidden=True,
            repair_basis=("unresolved_argument_slots",),
            provenance="l06 missing-argument repair from l05 unresolved slot marker",
        )
    if marker == "scope_ambiguity":
        return RepairTrigger(
            repair_id=repair_id,
            repair_class=RepairClass.SCOPE_REPAIR,
            localized_trouble_source="scope_binding",
            localized_ref_ids=(record.source_dictum_candidate_id,),
            why_this_is_broken="scope remains ambiguous and candidate update cannot be localized safely",
            suggested_clarification_type="bounded_scope_disambiguation",
            blocked_updates=(proposal_id,),
            guarded_continue_allowed=False,
            guarded_continue_forbidden=True,
            repair_basis=("scope_ambiguity",),
            provenance="l06 scope repair from l05 scope ambiguity marker",
        )
    if marker == "negation_scope_ambiguity":
        return RepairTrigger(
            repair_id=repair_id,
            repair_class=RepairClass.POLARITY_REPAIR,
            localized_trouble_source="polarity_binding",
            localized_ref_ids=(record.source_dictum_candidate_id,),
            why_this_is_broken="negation scope is unresolved and polarity cannot be accepted for discourse update",
            suggested_clarification_type="bounded_polarity_disambiguation",
            blocked_updates=(proposal_id,),
            guarded_continue_allowed=False,
            guarded_continue_forbidden=True,
            repair_basis=("negation_scope_ambiguity",),
            provenance="l06 polarity repair from l05 negation ambiguity marker",
        )
    if marker == "quoted_or_echoic_force_present":
        return RepairTrigger(
            repair_id=repair_id,
            repair_class=RepairClass.FORCE_REPAIR,
            localized_trouble_source="quoted_force_owner_binding",
            localized_ref_ids=(record.source_dictum_candidate_id, record.record_id),
            why_this_is_broken="quoted/echoic force owner must be localized before any acceptance",
            suggested_clarification_type="bounded_force_owner_disambiguation",
            blocked_updates=(proposal_id,),
            guarded_continue_allowed=True,
            guarded_continue_forbidden=False,
            repair_basis=("quoted_or_echoic_force_present",),
            provenance="l06 force repair from quoted/echoic marker",
        )
    if marker == "high_illocution_entropy":
        return RepairTrigger(
            repair_id=repair_id,
            repair_class=RepairClass.FORCE_REPAIR,
            localized_trouble_source="force_topology",
            localized_ref_ids=(record.record_id,),
            why_this_is_broken="high illocution entropy indicates unresolved force topology",
            suggested_clarification_type="bounded_force_disambiguation",
            blocked_updates=(proposal_id,),
            guarded_continue_allowed=False,
            guarded_continue_forbidden=True,
            repair_basis=("high_illocution_entropy",),
            provenance="l06 force repair from entropy marker",
        )
    return None


def _continuation_state(
    *,
    record: ModusHypothesisRecord,
    proposal_id: str,
    repairs_for_record: tuple[RepairTrigger, ...],
    continuation_index: int,
) -> GuardedContinuationState:
    decision = _resolve_continuation_decision(
        record=record,
        repairs_for_record=repairs_for_record,
    )
    status = decision.status

    return GuardedContinuationState(
        continuation_id=f"continuation-{continuation_index}",
        source_record_id=record.record_id,
        continuation_status=status,
        blocked_update_ids=(proposal_id,) if status is ContinuationStatus.BLOCKED_PENDING_REPAIR else (),
        guarded_continue_allowed=decision.guarded_allowed,
        guarded_continue_forbidden=decision.guarded_forbidden,
        acceptance_required=True,
        block_or_guard_reason=decision.reason,
        localized_repair_refs=tuple(trigger.repair_id for trigger in repairs_for_record),
    )


def _resolve_continuation_decision(
    *,
    record: ModusHypothesisRecord,
    repairs_for_record: tuple[RepairTrigger, ...],
) -> _ContinuationDecision:
    hard_block = any(
        trigger.repair_class
        in {
            RepairClass.MISSING_ARGUMENT_REPAIR,
            RepairClass.SCOPE_REPAIR,
            RepairClass.POLARITY_REPAIR,
            RepairClass.REFERENCE_REPAIR,
        }
        and trigger.guarded_continue_forbidden
        for trigger in repairs_for_record
    )
    if hard_block:
        return _ContinuationDecision(
            status=ContinuationStatus.BLOCKED_PENDING_REPAIR,
            guarded_allowed=False,
            guarded_forbidden=True,
            reason="blocked pending localized repair",
        )

    guarded = any(trigger.guarded_continue_allowed for trigger in repairs_for_record)
    if guarded:
        return _ContinuationDecision(
            status=ContinuationStatus.GUARDED_CONTINUE,
            guarded_allowed=True,
            guarded_forbidden=False,
            reason="guarded continuation allowed with localized repair obligations",
        )

    if repairs_for_record:
        return _ContinuationDecision(
            status=ContinuationStatus.BLOCKED_PENDING_REPAIR,
            guarded_allowed=False,
            guarded_forbidden=True,
            reason="repair required before update acceptance",
        )

    if record.uncertainty_entropy >= 0.85:
        return _ContinuationDecision(
            status=ContinuationStatus.GUARDED_CONTINUE,
            guarded_allowed=True,
            guarded_forbidden=False,
            reason="high entropy keeps continuation guarded despite no explicit repair class",
        )

    if record.uncertainty_entropy >= 0.7:
        return _ContinuationDecision(
            status=ContinuationStatus.ABSTAIN_UPDATE_WITHHELD,
            guarded_allowed=False,
            guarded_forbidden=True,
            reason="update withheld due to unresolved entropy without lawful repair-ready continuation",
        )

    return _ContinuationDecision(
        status=ContinuationStatus.PROPOSAL_ALLOWED_BUT_ACCEPTANCE_REQUIRED,
        guarded_allowed=False,
        guarded_forbidden=False,
        reason="proposal allowed but acceptance is still required",
    )


def _proposal_permissions_for_continuation(
    continuation_status: ContinuationStatus,
) -> tuple[str, ...]:
    return _CONTINUATION_STATUS_PERMISSIONS[continuation_status]


def _proposal_restrictions_for_continuation(
    *,
    continuation_status: ContinuationStatus,
    has_localized_repair: bool,
) -> tuple[str, ...]:
    restrictions = list(_PROPOSAL_BASE_RESTRICTIONS)
    if has_localized_repair:
        restrictions.append("repair_localization_must_be_read")
    restrictions.extend(_CONTINUATION_STATUS_RESTRICTIONS[continuation_status])
    return tuple(dict.fromkeys(restrictions))


def _derive_l05_bundle_ref(modus_bundle: ModusHypothesisBundle) -> str:
    head = modus_bundle.hypothesis_records[0].record_id if modus_bundle.hypothesis_records else "none"
    return f"l05.bundle:{head}:n={len(modus_bundle.hypothesis_records)}"


def _derive_l06_bundle_ref(
    source_modus_ref: str,
    proposals: list[UpdateProposal] | tuple[UpdateProposal, ...],
    repairs: list[RepairTrigger] | tuple[RepairTrigger, ...],
    continuations: list[GuardedContinuationState] | tuple[GuardedContinuationState, ...],
) -> str:
    proposal_head = proposals[0].proposal_id if proposals else "none"
    repair_head = repairs[0].repair_id if repairs else "none"
    continuation_head = continuations[0].continuation_id if continuations else "none"
    return (
        f"l06.bundle:{source_modus_ref}:{proposal_head}:{repair_head}:{continuation_head}:"
        f"p={len(proposals)}:r={len(repairs)}:c={len(continuations)}"
    )


def _derive_source_refs(
    *,
    modus_bundle: ModusHypothesisBundle,
    proposals: list[UpdateProposal] | tuple[UpdateProposal, ...],
    repairs: list[RepairTrigger] | tuple[RepairTrigger, ...],
    continuations: list[GuardedContinuationState] | tuple[GuardedContinuationState, ...],
) -> _L06SourceRefs:
    source_modus_ref = _derive_l05_bundle_ref(modus_bundle)
    source_modus_lineage_ref = modus_bundle.source_dictum_ref
    return _L06SourceRefs(
        source_modus_ref=source_modus_ref,
        source_modus_ref_kind="phase_native_derived_ref",
        source_modus_lineage_ref=source_modus_lineage_ref,
        bundle_ref=_derive_l06_bundle_ref(source_modus_ref, proposals, repairs, continuations),
    )


def _default_downstream_absence() -> _L06DownstreamAbsence:
    return _L06DownstreamAbsence(
        downstream_update_acceptor_absent=True,
        repair_consumer_absent=True,
        discourse_state_mutation_consumer_absent=True,
        legacy_g01_bypass_risk_present=True,
        low_coverage_reasons=_L06_DEFAULT_DOWNSTREAM_ABSENCE_REASONS,
    )


def _estimate_result_confidence(bundle: DiscourseUpdateBundle) -> float:
    base = 0.67
    base -= min(0.24, len(bundle.repair_triggers) * 0.02)
    base -= min(0.22, len(bundle.blocked_update_ids) * 0.04)
    if bundle.low_coverage_mode:
        base -= min(0.28, len(bundle.low_coverage_reasons) * 0.04)
    if not bundle.update_proposals:
        base -= 0.24
    return max(0.08, min(0.9, round(base, 4)))


def _abstain_result(
    *,
    modus_bundle: ModusHypothesisBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> DiscourseUpdateResult:
    source_refs = _derive_source_refs(
        modus_bundle=modus_bundle,
        proposals=(),
        repairs=(),
        continuations=(),
    )
    downstream_absence = _default_downstream_absence()
    bundle = DiscourseUpdateBundle(
        bundle_ref=source_refs.bundle_ref,
        source_modus_ref=source_refs.source_modus_ref,
        source_modus_ref_kind=source_refs.source_modus_ref_kind,
        source_modus_lineage_ref=source_refs.source_modus_lineage_ref,
        source_dictum_ref=modus_bundle.source_dictum_ref,
        source_syntax_ref=modus_bundle.source_syntax_ref,
        source_surface_ref=modus_bundle.source_surface_ref,
        linked_modus_record_ids=(),
        update_proposals=(),
        repair_triggers=(),
        continuation_states=(),
        blocked_update_ids=(),
        guarded_update_ids=(),
        acceptance_required_count=0,
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=(
            "abstain",
            *downstream_absence.low_coverage_reasons,
        ),
        interpretation_not_equal_accepted_update=True,
        no_common_ground_mutation_performed=True,
        no_self_state_mutation_performed=True,
        no_final_acceptance_performed=True,
        downstream_update_acceptor_absent=downstream_absence.downstream_update_acceptor_absent,
        repair_consumer_absent=downstream_absence.repair_consumer_absent,
        discourse_state_mutation_consumer_absent=downstream_absence.discourse_state_mutation_consumer_absent,
        legacy_g01_bypass_risk_present=downstream_absence.legacy_g01_bypass_risk_present,
        downstream_authority_degraded=True,
        reason="l06 abstained due to insufficient l05 basis",
    )
    gate = evaluate_discourse_update_downstream_gate(bundle)
    telemetry = build_discourse_update_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="insufficient l05 basis -> l06 abstain",
    )
    return DiscourseUpdateResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_acceptance_performed=True,
    )
