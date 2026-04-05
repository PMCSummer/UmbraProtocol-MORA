from __future__ import annotations

from dataclasses import dataclass

from substrate.concept_framing.models import ConceptFramingBundle, ConceptFramingResult, FrameFamily, FramingStatus
from substrate.contracts import RuntimeState, TransitionKind, TransitionRequest, TransitionResult, WriterIdentity
from substrate.discourse_update.models import (
    AcceptanceStatus,
    ContinuationStatus,
    DiscourseUpdateBundle,
    DiscourseUpdateResult,
    RepairClass,
)
from substrate.semantic_acquisition.models import (
    AcquisitionStatus,
    ProvisionalAcquisitionRecord,
    SemanticAcquisitionBundle,
    SemanticAcquisitionResult,
)
from substrate.targeted_clarification.models import (
    AbstainPolicy,
    AskPolicy,
    ClarificationIntent,
    ExpectedEvidenceGain,
    GuardedContinuePolicy,
    InterventionBundle,
    InterventionDecision,
    InterventionRecord,
    InterventionStatus,
    MinimalQuestionSpec,
    TargetedClarificationResult,
    UncertaintyClass,
)
from substrate.targeted_clarification.policy import evaluate_targeted_clarification_downstream_gate
from substrate.targeted_clarification.telemetry import build_targeted_clarification_telemetry, targeted_clarification_result_snapshot
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g07.validate_typed_inputs",
    "g07.l06_upstream_binding",
    "g07.targeted_uncertainty_selection",
    "g07.repair_localization_alignment",
    "g07.questionability_policy",
    "g07.minimal_question_spec_build",
    "g07.answer_binding_readiness",
    "g07.downstream_lockouts",
    "g07.downstream_gate",
)


@dataclass(frozen=True, slots=True)
class _G07SourceRefs:
    source_acquisition_ref: str
    source_acquisition_ref_kind: str
    source_acquisition_lineage_ref: str
    source_framing_ref: str
    source_framing_ref_kind: str
    source_framing_lineage_ref: str
    source_discourse_update_ref: str
    source_discourse_update_ref_kind: str
    source_discourse_update_lineage_ref: str


def build_targeted_clarification(
    semantic_acquisition_result_or_bundle: SemanticAcquisitionResult | SemanticAcquisitionBundle,
    concept_framing_result_or_bundle: ConceptFramingResult | ConceptFramingBundle,
    discourse_update_result_or_bundle: DiscourseUpdateResult | DiscourseUpdateBundle,
) -> TargetedClarificationResult:
    acq_bundle, acq_lineage = _extract_acq_input(semantic_acquisition_result_or_bundle)
    frame_bundle, frame_lineage = _extract_frame_input(concept_framing_result_or_bundle)
    discourse_bundle, discourse_lineage = _extract_discourse_update_input(discourse_update_result_or_bundle)
    source_refs = _derive_source_refs(
        acq_bundle=acq_bundle,
        frame_bundle=frame_bundle,
        discourse_bundle=discourse_bundle,
    )
    if not acq_bundle.acquisition_records or not frame_bundle.framing_records:
        return _abstain_result(
            acq_bundle,
            frame_bundle,
            discourse_bundle,
            tuple(dict.fromkeys((*acq_lineage, *frame_lineage, *discourse_lineage))),
            "g05/g06 missing records",
        )

    ambiguity = list(acq_bundle.ambiguity_reasons) + list(frame_bundle.ambiguity_reasons)
    low_coverage = (
        list(acq_bundle.low_coverage_reasons)
        + list(frame_bundle.low_coverage_reasons)
        + list(discourse_bundle.low_coverage_reasons)
    )
    l06_upstream_bound_here = True
    l06_repair_basis_bound_here = bool(discourse_bundle.repair_triggers)
    l06_update_proposal_absent = not bool(discourse_bundle.update_proposals)
    l06_repair_localization_must_be_read = bool(discourse_bundle.repair_triggers)
    l06_proposal_requires_acceptance_read = bool(discourse_bundle.update_proposals)
    l06_update_not_accepted = all(
        proposal.acceptance_status is not AcceptanceStatus.ACCEPTED
        for proposal in discourse_bundle.update_proposals
    )
    intervention_not_discourse_acceptance = True
    l06_block_or_guard_must_be_read = bool(discourse_bundle.continuation_states)
    l06_continuation_topology_present = bool(discourse_bundle.continuation_states)
    response_realization_contract_absent = True
    answer_binding_consumer_absent = True
    if l06_update_proposal_absent:
        low_coverage.append("l06_update_proposal_absent")
    if discourse_bundle.repair_consumer_absent:
        low_coverage.append("l06_repair_consumer_absent")
    if discourse_bundle.downstream_update_acceptor_absent:
        low_coverage.append("l06_downstream_update_acceptor_absent")
    if discourse_bundle.discourse_state_mutation_consumer_absent:
        low_coverage.append("l06_discourse_state_mutation_consumer_absent")
    if discourse_bundle.legacy_g01_bypass_risk_present:
        low_coverage.append("legacy_g01_bypass_risk_present")
    low_coverage.extend(
        ["response_realization_contract_absent", "answer_binding_consumer_absent"]
    )
    if frame_bundle.source_perspective_chain_ref != acq_bundle.source_perspective_chain_ref:
        ambiguity.append("acquisition_framing_reference_mismatch")
        low_coverage.append("acquisition_framing_reference_mismatch")

    by_acq = {record.acquisition_id: record for record in acq_bundle.acquisition_records}
    records: list[InterventionRecord] = []
    l06_target_drift_detected = False
    l06_repair_localization_incompatible = False
    for idx, frame_record in enumerate(frame_bundle.framing_records, start=1):
        acq = by_acq.get(frame_record.acquisition_id)
        if acq is None:
            records.append(_missing_acquisition_record(frame_record.framing_id, idx))
            low_coverage.append("missing_acquisition_for_framing_record")
            continue
        uncertainty_class = _derive_uncertainty_class(acq, frame_record.framing_status)
        l06_ctx = _l06_context_for_uncertainty(discourse_bundle, uncertainty_class)
        if l06_ctx["target_alignment_required"] and not l06_ctx["target_alignment_ok"]:
            l06_target_drift_detected = True
            l06_repair_localization_incompatible = True
        target_id = (
            f"target:semantic-unit:{acq.semantic_unit_id}"
            if acq.semantic_unit_id
            else f"target:acquisition:{acq.acquisition_id}:frame:{frame_record.framing_id}"
        )
        forbidden = _forbidden_presuppositions(
            acq,
            uncertainty_class,
            frame_record.frame_family,
            include_l06_acceptance_boundary=l06_proposal_requires_acceptance_read,
        )
        question_spec = _question_spec(
            idx,
            target_id,
            uncertainty_class,
            frame_record.frame_family,
            forbidden,
            l06_ctx["repair_refs"],
            l06_ctx["repair_classes"],
        )
        gain = _expected_gain(acq, frame_record.framing_status, uncertainty_class)
        status, basis, questionability = _select_status(
            acq,
            frame_record.framing_status,
            uncertainty_class,
            gain,
            l06_update_proposal_absent,
            l06_blocked_for_target=l06_ctx["blocked_for_target"],
            l06_guarded_for_target=l06_ctx["guarded_for_target"],
            l06_withheld_for_target=l06_ctx["withheld_for_target"],
            l06_target_alignment_ok=l06_ctx["target_alignment_ok"],
            l06_target_alignment_required=l06_ctx["target_alignment_required"],
        )
        if l06_ctx["target_alignment_required"] and not l06_ctx["target_alignment_ok"]:
            basis = tuple(dict.fromkeys((*basis, "l06_g07_target_drift_detected")))
        decision = InterventionDecision(
            selected_status=status,
            decision_basis=tuple(dict.fromkeys(basis)),
            blocking_uncertainty=status
            in {
                InterventionStatus.ASK_NOW,
                InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY,
            },
            questionability_sufficient=questionability,
            cost_worthwhile=gain.worth_cost,
        )
        records.append(
            InterventionRecord(
                intervention_id=f"intervention-{idx}",
                source_record_ids=(acq.acquisition_id, frame_record.framing_id),
                uncertainty_target_id=target_id,
                uncertainty_class=uncertainty_class,
                intervention_status=status,
                ask_policy=AskPolicy(
                    should_ask=status is InterventionStatus.ASK_NOW,
                    urgency="high" if gain.gain_score >= 0.62 else ("medium" if gain.gain_score >= 0.45 else "low"),
                    reason="ask only for target-bound uncertainty with material evidence gain",
                ),
                abstain_policy=AbstainPolicy(
                    should_abstain=status in {
                        InterventionStatus.ABSTAIN_WITHOUT_QUESTION,
                        InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY,
                        InterventionStatus.CLARIFICATION_NOT_WORTH_COST,
                    },
                    mode=status.value,
                    reason="abstain/defer when questionability is unsafe, incomplete, or low-value",
                ),
                guarded_continue_policy=GuardedContinuePolicy(
                    should_continue=status in {InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS, InterventionStatus.DEFER_UNTIL_NEEDED},
                    required_limits=("closure_blocked_until_answer", "planning_forbidden_on_current_frame", "memory_uptake_deferred"),
                    reason="guarded continuation keeps uncertainty first-class and blocks closure inflation",
                ),
                minimal_question_spec=question_spec,
                forbidden_presuppositions=forbidden,
                expected_evidence_gain=gain,
                downstream_lockouts=_lockouts(
                    status,
                    uncertainty_class,
                    frame_record.vulnerability_profile.high_impact,
                    l06_ctx["blocked_for_target"],
                    l06_ctx["guarded_for_target"],
                    l06_ctx["withheld_for_target"],
                ),
                l06_repair_binding_refs=l06_ctx["repair_refs"],
                l06_repair_classes=l06_ctx["repair_classes"],
                l06_continuation_statuses=l06_ctx["continuation_statuses"],
                l06_alignment_ok=l06_ctx["target_alignment_ok"],
                reopen_conditions=_reopen_conditions(acq, frame_record),
                decision=decision,
                confidence=_record_confidence(acq.confidence, frame_record.confidence, status, gain.gain_score),
                provenance="g07 targeted clarification from g05 acquisition + g06 framing + l06 discourse update topology",
            )
        )

    repair_trigger_basis_incomplete = (
        frame_bundle.repair_trigger_basis_incomplete
        or not bool(discourse_bundle.repair_triggers)
        or any(
            condition.startswith("g06:") and "repair" in condition
            for record in records
            for condition in record.reopen_conditions
        )
    )
    answer_binding_ready = bool(records) and all(
        record.uncertainty_target_id and record.reopen_conditions for record in records
    )
    if not answer_binding_ready:
        low_coverage.append("answer_binding_not_ready")
    if answer_binding_consumer_absent and any(
        record.intervention_status is InterventionStatus.ASK_NOW for record in records
    ):
        low_coverage.append("ask_now_without_answer_binding_executor")
    if l06_target_drift_detected:
        low_coverage.append("l06_g07_target_drift_detected")
    if l06_repair_localization_incompatible:
        low_coverage.append("l06_repair_localization_incompatible")
    if not l06_update_not_accepted:
        low_coverage.append("l06_update_acceptance_state_unexpected")
    if not l06_continuation_topology_present:
        low_coverage.append("l06_continuation_topology_missing")
    degraded = bool(
        low_coverage
        or any(
            record.intervention_status
            in {
                InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY,
                InterventionStatus.ABSTAIN_WITHOUT_QUESTION,
                InterventionStatus.DEFER_UNTIL_NEEDED,
                InterventionStatus.CLARIFICATION_NOT_WORTH_COST,
            }
            for record in records
        )
    )
    if degraded:
        low_coverage.append("downstream_authority_degraded")

    bundle = InterventionBundle(
        source_acquisition_ref=source_refs.source_acquisition_ref,
        source_acquisition_ref_kind=source_refs.source_acquisition_ref_kind,
        source_acquisition_lineage_ref=source_refs.source_acquisition_lineage_ref,
        source_framing_ref=source_refs.source_framing_ref,
        source_framing_ref_kind=source_refs.source_framing_ref_kind,
        source_framing_lineage_ref=source_refs.source_framing_lineage_ref,
        source_discourse_update_ref=source_refs.source_discourse_update_ref,
        source_discourse_update_ref_kind=source_refs.source_discourse_update_ref_kind,
        source_discourse_update_lineage_ref=source_refs.source_discourse_update_lineage_ref,
        source_perspective_chain_ref=acq_bundle.source_perspective_chain_ref,
        source_applicability_ref=acq_bundle.source_applicability_ref,
        source_runtime_graph_ref=acq_bundle.source_runtime_graph_ref,
        source_grounded_ref=acq_bundle.source_grounded_ref,
        source_dictum_ref=acq_bundle.source_dictum_ref,
        source_syntax_ref=acq_bundle.source_syntax_ref,
        source_surface_ref=acq_bundle.source_surface_ref,
        linked_acquisition_ids=tuple(record.acquisition_id for record in acq_bundle.acquisition_records),
        linked_framing_ids=tuple(record.framing_id for record in frame_bundle.framing_records),
        linked_update_proposal_ids=tuple(proposal.proposal_id for proposal in discourse_bundle.update_proposals),
        linked_repair_ids=tuple(repair.repair_id for repair in discourse_bundle.repair_triggers),
        intervention_records=tuple(records),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity)),
        low_coverage_mode=bool(low_coverage),
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage)),
        l06_upstream_bound_here=l06_upstream_bound_here,
        l06_repair_basis_bound_here=l06_repair_basis_bound_here,
        l06_update_proposal_absent=l06_update_proposal_absent,
        l06_repair_localization_must_be_read=l06_repair_localization_must_be_read,
        l06_proposal_requires_acceptance_read=l06_proposal_requires_acceptance_read,
        l06_update_not_accepted=l06_update_not_accepted,
        intervention_not_discourse_acceptance=intervention_not_discourse_acceptance,
        l06_block_or_guard_must_be_read=l06_block_or_guard_must_be_read,
        l06_continuation_topology_present=l06_continuation_topology_present,
        l06_g07_target_alignment_required=bool(discourse_bundle.repair_triggers),
        l06_g07_target_drift_detected=l06_target_drift_detected,
        l06_repair_localization_incompatible=l06_repair_localization_incompatible,
        repair_trigger_basis_incomplete=repair_trigger_basis_incomplete,
        response_realization_contract_absent=response_realization_contract_absent,
        answer_binding_consumer_absent=answer_binding_consumer_absent,
        answer_binding_ready=answer_binding_ready,
        answer_binding_hooks=(
            "bind_answer_to_uncertainty_target",
            "reopen_linked_acquisition_and_framing_records",
            "preserve_forbidden_presuppositions_on_realization",
        ),
        intervention_requires_target_binding_read=True,
        downstream_lockouts_must_be_read=True,
        clarification_not_equal_realized_question=True,
        asked_question_not_equal_resolved_uncertainty=True,
        downstream_authority_degraded=degraded,
        no_final_semantic_closure=True,
        reason="g07 converted uncertainty into targeted intervention decisions without closure simulation",
    )
    gate = evaluate_targeted_clarification_downstream_gate(bundle)
    source_lineage = _compose_source_lineage(
        acq_bundle=acq_bundle,
        source_refs=source_refs,
        acq_lineage=acq_lineage,
        frame_lineage=frame_lineage,
        discourse_bundle=discourse_bundle,
        discourse_lineage=discourse_lineage,
    )
    telemetry = build_targeted_clarification_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="g05 uncertainty + g06 framing + l06 proposal/repair/continuation topology drove target-bound intervention outcome",
    )
    partial_known_reason = "; ".join(bundle.ambiguity_reasons) if bundle.ambiguity_reasons else ("; ".join(bundle.low_coverage_reasons) if bundle.low_coverage_reasons else None)
    return TargetedClarificationResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=_result_confidence(bundle),
        partial_known=bool(bundle.low_coverage_mode or bundle.ambiguity_reasons),
        partial_known_reason=partial_known_reason,
        abstain=not gate.accepted,
        abstain_reason=None if gate.accepted else gate.reason,
        no_final_semantic_closure=True,
    )


def targeted_clarification_result_to_payload(result: TargetedClarificationResult) -> dict[str, object]:
    return targeted_clarification_result_snapshot(result)


def persist_targeted_clarification_result_via_f01(
    *,
    result: TargetedClarificationResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("g07-targeted-clarification-uncertainty-intervention",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"targeted-clarification-step-{transition_id}",
            "targeted_clarification_snapshot": targeted_clarification_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_acq_input(inp: SemanticAcquisitionResult | SemanticAcquisitionBundle) -> tuple[SemanticAcquisitionBundle, tuple[str, ...]]:
    if isinstance(inp, SemanticAcquisitionResult):
        return inp.bundle, inp.telemetry.source_lineage
    if isinstance(inp, SemanticAcquisitionBundle):
        return inp, ()
    raise TypeError("build_targeted_clarification requires SemanticAcquisitionResult or SemanticAcquisitionBundle")


def _extract_frame_input(inp: ConceptFramingResult | ConceptFramingBundle) -> tuple[ConceptFramingBundle, tuple[str, ...]]:
    if isinstance(inp, ConceptFramingResult):
        return inp.bundle, inp.telemetry.source_lineage
    if isinstance(inp, ConceptFramingBundle):
        return inp, ()
    raise TypeError("build_targeted_clarification requires ConceptFramingResult or ConceptFramingBundle")


def _extract_discourse_update_input(
    inp: DiscourseUpdateResult | DiscourseUpdateBundle,
) -> tuple[DiscourseUpdateBundle, tuple[str, ...]]:
    if isinstance(inp, DiscourseUpdateResult):
        return inp.bundle, inp.telemetry.source_lineage
    if isinstance(inp, DiscourseUpdateBundle):
        return inp, ()
    raise TypeError(
        "build_targeted_clarification requires DiscourseUpdateResult or DiscourseUpdateBundle for l06 upstream"
    )


def _derive_source_refs(
    *,
    acq_bundle: SemanticAcquisitionBundle,
    frame_bundle: ConceptFramingBundle,
    discourse_bundle: DiscourseUpdateBundle,
) -> _G07SourceRefs:
    return _G07SourceRefs(
        source_acquisition_ref=_derive_g05_bundle_ref(acq_bundle),
        source_acquisition_ref_kind="phase_native_derived_ref",
        source_acquisition_lineage_ref=acq_bundle.source_perspective_chain_ref,
        source_framing_ref=_derive_g06_bundle_ref(frame_bundle),
        source_framing_ref_kind="phase_native_derived_ref",
        source_framing_lineage_ref=frame_bundle.source_acquisition_ref,
        source_discourse_update_ref=discourse_bundle.bundle_ref,
        source_discourse_update_ref_kind="phase_native_derived_ref",
        source_discourse_update_lineage_ref=discourse_bundle.source_modus_lineage_ref,
    )


def _compose_source_lineage(
    *,
    acq_bundle: SemanticAcquisitionBundle,
    source_refs: _G07SourceRefs,
    acq_lineage: tuple[str, ...],
    frame_lineage: tuple[str, ...],
    discourse_bundle: DiscourseUpdateBundle,
    discourse_lineage: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                acq_bundle.source_perspective_chain_ref,
                acq_bundle.source_applicability_ref,
                acq_bundle.source_runtime_graph_ref,
                acq_bundle.source_grounded_ref,
                acq_bundle.source_dictum_ref,
                acq_bundle.source_syntax_ref,
                *((acq_bundle.source_surface_ref,) if acq_bundle.source_surface_ref else ()),
                source_refs.source_acquisition_ref,
                source_refs.source_framing_ref,
                source_refs.source_discourse_update_ref,
                source_refs.source_acquisition_lineage_ref,
                source_refs.source_framing_lineage_ref,
                source_refs.source_discourse_update_lineage_ref,
                *acq_lineage,
                *frame_lineage,
                discourse_bundle.source_modus_ref,
                *discourse_lineage,
            )
        )
    )


def _derive_g05_bundle_ref(acq_bundle: SemanticAcquisitionBundle) -> str:
    head = acq_bundle.acquisition_records[0].acquisition_id if acq_bundle.acquisition_records else "none"
    return f"g05.bundle:{head}:n={len(acq_bundle.acquisition_records)}"


def _derive_g06_bundle_ref(frame_bundle: ConceptFramingBundle) -> str:
    head = frame_bundle.framing_records[0].framing_id if frame_bundle.framing_records else "none"
    return f"g06.bundle:{head}:n={len(frame_bundle.framing_records)}"


def _derive_uncertainty_class(acq: ProvisionalAcquisitionRecord, framing_status: FramingStatus) -> UncertaintyClass:
    unresolved = set(acq.support_conflict_profile.unresolved_slots)
    conflict = set(acq.support_conflict_profile.conflict_reasons)
    if framing_status is FramingStatus.COMPETING_FRAMES:
        return UncertaintyClass.FRAME_COMPETITION
    if framing_status is FramingStatus.BLOCKED_HIGH_IMPACT_FRAME:
        return UncertaintyClass.HIGH_IMPACT_BINDING_RISK
    if framing_status is FramingStatus.CONTEXT_ONLY_FRAME_HINT:
        return UncertaintyClass.CONTEXT_ONLY_UNCERTAINTY
    if {"commitment_owner", "source_scope", "perspective_owner"} & unresolved or {"source_scope_unknown", "commitment_owner_ambiguous", "owner_flattening_risk"} & conflict:
        return UncertaintyClass.OWNER_SCOPE_AMBIGUITY
    if {"temporal_anchor", "perspective_depth"} & unresolved:
        return UncertaintyClass.TEMPORAL_ANCHOR_AMBIGUITY
    if acq.acquisition_status is AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION:
        return UncertaintyClass.REPAIR_TRIGGER_GAP
    return UncertaintyClass.RESIDUAL_UNCERTAINTY


def _forbidden_presuppositions(
    acq: ProvisionalAcquisitionRecord,
    uncertainty_class: UncertaintyClass,
    frame_family: FrameFamily,
    *,
    include_l06_acceptance_boundary: bool,
) -> tuple[str, ...]:
    forbidden: list[str] = ["do_not_assume_resolution_without_answer", "do_not_force_target_identity"]
    unresolved = set(acq.support_conflict_profile.unresolved_slots)
    conflict = set(acq.support_conflict_profile.conflict_reasons)
    if uncertainty_class is UncertaintyClass.OWNER_SCOPE_AMBIGUITY:
        forbidden.extend(["do_not_presuppose_commitment_owner", "do_not_presuppose_source_scope"])
    if uncertainty_class is UncertaintyClass.TEMPORAL_ANCHOR_AMBIGUITY:
        forbidden.append("do_not_presuppose_temporal_anchor")
    if uncertainty_class is UncertaintyClass.FRAME_COMPETITION:
        forbidden.append("do_not_presuppose_single_dominant_frame")
    if uncertainty_class is UncertaintyClass.HIGH_IMPACT_BINDING_RISK:
        forbidden.append("do_not_presuppose_high_impact_frame_is_true")
    if frame_family in {FrameFamily.NORMATIVE, FrameFamily.OBLIGATION_RELEVANT}:
        forbidden.append("do_not_presuppose_obligation_violation")
    if frame_family is FrameFamily.THREAT_RELEVANT:
        forbidden.append("do_not_presuppose_threat_intent")
    if "source_scope" in unresolved or "source_scope_unknown" in conflict:
        forbidden.append("do_not_presuppose_reported_quote_identity")
    if include_l06_acceptance_boundary:
        forbidden.append("do_not_assume_l06_update_accepted")
    return tuple(dict.fromkeys(forbidden))


def _question_spec(
    idx: int,
    target_id: str,
    uncertainty_class: UncertaintyClass,
    frame_family: FrameFamily,
    forbidden: tuple[str, ...],
    l06_repair_refs: tuple[str, ...],
    l06_repair_classes: tuple[str, ...],
) -> MinimalQuestionSpec:
    contrast = {
        UncertaintyClass.OWNER_SCOPE_AMBIGUITY: "owner_binding_A_vs_owner_binding_B",
        UncertaintyClass.TEMPORAL_ANCHOR_AMBIGUITY: "current_anchor_vs_reported_anchor",
        UncertaintyClass.FRAME_COMPETITION: "frame_primary_vs_frame_alternative",
        UncertaintyClass.HIGH_IMPACT_BINDING_RISK: "high_impact_reading_vs_contextual_reading",
        UncertaintyClass.CONTEXT_ONLY_UNCERTAINTY: "context_hint_vs_commitment_reading",
        UncertaintyClass.REPAIR_TRIGGER_GAP: "repair_required_vs_no_repair",
        UncertaintyClass.RESIDUAL_UNCERTAINTY: "provisional_reading_vs_unresolved_gap",
    }[uncertainty_class]
    l06_scope = tuple(f"l06_repair_ref:{repair_id}" for repair_id in l06_repair_refs)
    l06_class_scope = tuple(f"l06_repair_class:{repair_class}" for repair_class in l06_repair_classes)
    return MinimalQuestionSpec(
        spec_id=f"question-spec-{idx}",
        clarification_intent=ClarificationIntent(
            intent_id=f"intent-{idx}",
            target_contrast=contrast,
            allowed_semantic_scope=(
                f"uncertainty_target:{target_id}",
                f"frame_family:{frame_family.value}",
                f"uncertainty_class:{uncertainty_class.value}",
                *l06_scope,
                *l06_class_scope,
            ),
            allowed_answer_form="bounded_choice_or_short_span",
            conceptual_stretch_bound="must stay within linked g05/g06 target and l06-localized repair topology when present",
        ),
        questionability_reason="targeted clarification spec is bounded and answer-injection forbidden",
        forbidden_assumptions=forbidden,
        preferred_answer_forbidden=True,
        realization_contract_marker="clarification_not_equal_realized_question",
    )


def _expected_gain(
    acq: ProvisionalAcquisitionRecord,
    framing_status: FramingStatus,
    uncertainty_class: UncertaintyClass,
) -> ExpectedEvidenceGain:
    unresolved_count = len(acq.support_conflict_profile.unresolved_slots)
    support = acq.support_conflict_profile.support_score
    conflict = acq.support_conflict_profile.conflict_score
    score = 0.24 + min(0.3, 0.06 * unresolved_count) + min(0.22, 0.05 * conflict)
    if framing_status in {FramingStatus.BLOCKED_HIGH_IMPACT_FRAME, FramingStatus.COMPETING_FRAMES}:
        score += 0.15
    if uncertainty_class in {UncertaintyClass.HIGH_IMPACT_BINDING_RISK, UncertaintyClass.OWNER_SCOPE_AMBIGUITY}:
        score += 0.1
    if uncertainty_class is UncertaintyClass.CONTEXT_ONLY_UNCERTAINTY:
        score -= 0.2
    if support >= 3:
        score -= 0.05
    score = max(0.08, min(0.9, round(score, 4)))
    level = "high" if score >= 0.62 else ("medium" if score >= 0.4 else "low")
    return ExpectedEvidenceGain(
        gain_score=score,
        gain_level=level,
        gain_reason="estimated gain from targeted answer over current uncertainty profile",
        impact_scope=("closure", "planning", "memory"),
        worth_cost=score >= 0.35,
    )


def _l06_context_for_uncertainty(
    discourse_bundle: DiscourseUpdateBundle,
    uncertainty_class: UncertaintyClass,
) -> dict[str, object]:
    expected_classes = _expected_repair_classes_for_uncertainty(uncertainty_class)
    repairs = tuple(
        repair
        for repair in discourse_bundle.repair_triggers
        if repair.repair_class in expected_classes
    )
    if uncertainty_class is UncertaintyClass.REPAIR_TRIGGER_GAP and not repairs:
        repairs = tuple(discourse_bundle.repair_triggers)
    if uncertainty_class is UncertaintyClass.CONTEXT_ONLY_UNCERTAINTY:
        repairs = ()

    blocked_from_repairs = (
        uncertainty_class in {UncertaintyClass.REPAIR_TRIGGER_GAP, UncertaintyClass.HIGH_IMPACT_BINDING_RISK}
        and any(repair.guarded_continue_forbidden for repair in repairs)
    )
    guarded_from_repairs = any(repair.guarded_continue_allowed for repair in repairs)
    continuation_blocked_present = any(
        state.continuation_status is ContinuationStatus.BLOCKED_PENDING_REPAIR
        for state in discourse_bundle.continuation_states
    )
    continuation_guarded_present = any(
        state.continuation_status is ContinuationStatus.GUARDED_CONTINUE
        for state in discourse_bundle.continuation_states
    )
    continuation_statuses = tuple(
        state.continuation_status.value for state in discourse_bundle.continuation_states
    )
    blocked_for_target = blocked_from_repairs or (
        not repairs
        and continuation_blocked_present
        and uncertainty_class in {UncertaintyClass.REPAIR_TRIGGER_GAP, UncertaintyClass.HIGH_IMPACT_BINDING_RISK}
    )
    guarded_for_target = guarded_from_repairs or (
        not blocked_for_target and not repairs and continuation_guarded_present
    )
    withheld_for_target = (not repairs) and any(
        state.continuation_status is ContinuationStatus.ABSTAIN_UPDATE_WITHHELD
        for state in discourse_bundle.continuation_states
    )
    target_alignment_required = bool(discourse_bundle.repair_triggers) and uncertainty_class in {
        UncertaintyClass.OWNER_SCOPE_AMBIGUITY,
        UncertaintyClass.TEMPORAL_ANCHOR_AMBIGUITY,
        UncertaintyClass.FRAME_COMPETITION,
        UncertaintyClass.HIGH_IMPACT_BINDING_RISK,
        UncertaintyClass.REPAIR_TRIGGER_GAP,
    }
    target_alignment_ok = (not target_alignment_required) or bool(repairs)
    return {
        "repair_refs": tuple(repair.repair_id for repair in repairs),
        "repair_classes": tuple(repair.repair_class.value for repair in repairs),
        "continuation_statuses": continuation_statuses,
        "blocked_for_target": blocked_for_target,
        "guarded_for_target": guarded_for_target,
        "withheld_for_target": withheld_for_target,
        "target_alignment_required": target_alignment_required,
        "target_alignment_ok": target_alignment_ok,
    }


def _expected_repair_classes_for_uncertainty(
    uncertainty_class: UncertaintyClass,
) -> tuple[RepairClass, ...]:
    if uncertainty_class is UncertaintyClass.OWNER_SCOPE_AMBIGUITY:
        return (
            RepairClass.REFERENCE_REPAIR,
            RepairClass.FORCE_REPAIR,
            RepairClass.SCOPE_REPAIR,
            RepairClass.POLARITY_REPAIR,
            RepairClass.MISSING_ARGUMENT_REPAIR,
        )
    if uncertainty_class is UncertaintyClass.TEMPORAL_ANCHOR_AMBIGUITY:
        return (
            RepairClass.SCOPE_REPAIR,
            RepairClass.POLARITY_REPAIR,
            RepairClass.MISSING_ARGUMENT_REPAIR,
            RepairClass.FORCE_REPAIR,
        )
    if uncertainty_class is UncertaintyClass.FRAME_COMPETITION:
        return (
            RepairClass.FORCE_REPAIR,
            RepairClass.SCOPE_REPAIR,
            RepairClass.POLARITY_REPAIR,
            RepairClass.REFERENCE_REPAIR,
        )
    if uncertainty_class is UncertaintyClass.HIGH_IMPACT_BINDING_RISK:
        return (
            RepairClass.FORCE_REPAIR,
            RepairClass.POLARITY_REPAIR,
            RepairClass.SCOPE_REPAIR,
            RepairClass.MISSING_ARGUMENT_REPAIR,
            RepairClass.TARGET_APPLICABILITY_REPAIR,
        )
    if uncertainty_class is UncertaintyClass.REPAIR_TRIGGER_GAP:
        return (
            RepairClass.REFERENCE_REPAIR,
            RepairClass.FORCE_REPAIR,
            RepairClass.SCOPE_REPAIR,
            RepairClass.POLARITY_REPAIR,
            RepairClass.MISSING_ARGUMENT_REPAIR,
            RepairClass.TARGET_APPLICABILITY_REPAIR,
        )
    return (RepairClass.FORCE_REPAIR, RepairClass.SCOPE_REPAIR)


def _select_status(
    acq: ProvisionalAcquisitionRecord,
    framing_status: FramingStatus,
    uncertainty_class: UncertaintyClass,
    gain: ExpectedEvidenceGain,
    l06_update_proposal_absent: bool,
    *,
    l06_blocked_for_target: bool,
    l06_guarded_for_target: bool,
    l06_withheld_for_target: bool,
    l06_target_alignment_ok: bool,
    l06_target_alignment_required: bool,
) -> tuple[InterventionStatus, tuple[str, ...], bool]:
    unresolved = set(acq.support_conflict_profile.unresolved_slots)
    questionability_blocked = bool(
        (
            {"source_scope", "commitment_owner"} <= unresolved
            and acq.acquisition_status
            in {
                AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION,
                AcquisitionStatus.CONTEXT_ONLY,
                AcquisitionStatus.DISCARDED_AS_INCOHERENT,
            }
        )
        or (
            framing_status is FramingStatus.BLOCKED_HIGH_IMPACT_FRAME
            and l06_update_proposal_absent
            and ("cross_turn_repair" in unresolved or "temporal_anchor" in unresolved)
        )
    )
    if questionability_blocked:
        return (
            InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY,
            ("questionability_blocked_by_unresolved_owner_source_or_repair_basis", "repair_trigger_basis_incomplete"),
            False,
        )
    if l06_target_alignment_required and not l06_target_alignment_ok:
        return (
            InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY,
            ("l06_g07_target_alignment_required", "l06_repair_localization_incompatible"),
            False,
        )
    if l06_blocked_for_target:
        return (
            InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY,
            ("l06_blocked_update_topology", "l06_block_or_guard_must_be_read"),
            False,
        )
    topology_forced = _select_topology_forced_status(
        l06_guarded_for_target=l06_guarded_for_target,
        l06_withheld_for_target=l06_withheld_for_target,
    )
    if topology_forced is not None:
        return topology_forced
    if uncertainty_class is UncertaintyClass.CONTEXT_ONLY_UNCERTAINTY and gain.gain_score < 0.4:
        return (InterventionStatus.CLARIFICATION_NOT_WORTH_COST, ("context_only_uncertainty_low_gain",), True)
    if gain.worth_cost and (
        uncertainty_class in {UncertaintyClass.HIGH_IMPACT_BINDING_RISK, UncertaintyClass.FRAME_COMPETITION}
        or (
            uncertainty_class is UncertaintyClass.OWNER_SCOPE_AMBIGUITY
            and framing_status in {
                FramingStatus.UNDERFRAMED_MEANING,
                FramingStatus.COMPETING_FRAMES,
                FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
            }
        )
    ):
        return (
            InterventionStatus.ASK_NOW,
            ("high_value_targeted_clarification", "ask_now_not_equal_resolution"),
            True,
        )
    if gain.gain_score < 0.28:
        return (InterventionStatus.CLARIFICATION_NOT_WORTH_COST, ("low_evidence_gain",), True)
    if framing_status in {FramingStatus.UNDERFRAMED_MEANING, FramingStatus.COMPETING_FRAMES}:
        return (InterventionStatus.DEFER_UNTIL_NEEDED, ("uncertainty_preserved_with_deferred_targeted_intervention",), True)
    if acq.acquisition_status in {AcquisitionStatus.WEAK_PROVISIONAL, AcquisitionStatus.STABLE_PROVISIONAL}:
        return (InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS, ("nonblocking_uncertainty_guarded_continue",), True)
    return (InterventionStatus.ABSTAIN_WITHOUT_QUESTION, ("abstain_without_forced_question",), True)


def _select_topology_forced_status(
    *,
    l06_guarded_for_target: bool,
    l06_withheld_for_target: bool,
) -> tuple[InterventionStatus, tuple[str, ...], bool] | None:
    if l06_withheld_for_target:
        return (
            InterventionStatus.DEFER_UNTIL_NEEDED,
            ("l06_abstain_update_withheld_topology", "defer_until_needed_must_be_read"),
            True,
        )
    if l06_guarded_for_target:
        return (
            InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS,
            ("l06_guarded_continue_topology", "guarded_continue_not_acceptance"),
            True,
        )
    return None


def _lockouts(
    status: InterventionStatus,
    uncertainty_class: UncertaintyClass,
    high_impact: bool,
    l06_blocked_for_target: bool,
    l06_guarded_for_target: bool,
    l06_withheld_for_target: bool,
) -> tuple[str, ...]:
    lockouts: list[str] = ["narrative_commitment_forbidden", "closure_blocked_until_answer", "memory_uptake_deferred"]
    if uncertainty_class is UncertaintyClass.CONTEXT_ONLY_UNCERTAINTY:
        lockouts.append("appraisal_context_only")
    if uncertainty_class is not UncertaintyClass.CONTEXT_ONLY_UNCERTAINTY and (
        high_impact or uncertainty_class in {UncertaintyClass.HIGH_IMPACT_BINDING_RISK, UncertaintyClass.FRAME_COMPETITION}
    ):
        lockouts.extend(["planning_forbidden_on_current_frame", "safety_escalation_not_authorized_from_current_evidence"])
    if status is InterventionStatus.GUARDED_CONTINUE_WITH_LIMITS:
        lockouts.append("guarded_continue_limits_must_be_read")
    elif status is InterventionStatus.DEFER_UNTIL_NEEDED:
        lockouts.append("defer_until_needed_must_be_read")
    elif status is InterventionStatus.ABSTAIN_WITHOUT_QUESTION:
        lockouts.append("abstain_without_question_must_be_read")
    elif status is InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY:
        lockouts.append("questionability_blocked_requires_repair_basis")
    elif status is InterventionStatus.CLARIFICATION_NOT_WORTH_COST:
        lockouts.append("clarification_not_worth_cost_must_be_read")
    else:
        lockouts.append("ask_now_requires_answer_binding")
    if l06_blocked_for_target:
        lockouts.append("l06_blocked_update_must_be_read")
    if l06_guarded_for_target:
        lockouts.append("l06_guarded_continue_must_be_read")
    if l06_withheld_for_target:
        lockouts.append("l06_abstain_update_withheld_must_be_read")
    return tuple(dict.fromkeys(lockouts))


def _reopen_conditions(acq: ProvisionalAcquisitionRecord, frame_record) -> tuple[str, ...]:
    conditions = [f"g05:{cond.condition_kind.value}:{cond.condition_id}" for cond in acq.revision_conditions]
    conditions.extend(f"g06:{cond.condition_kind.value}:{cond.condition_id}" for cond in frame_record.reframing_conditions)
    if not conditions:
        conditions.append("g07:reopen_on_targeted_answer")
    return tuple(dict.fromkeys(conditions))


def _record_confidence(acq_conf: float, frame_conf: float, status: InterventionStatus, gain: float) -> float:
    value = (acq_conf * 0.45) + (frame_conf * 0.35) + (gain * 0.2)
    if status in {InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY, InterventionStatus.ABSTAIN_WITHOUT_QUESTION}:
        value -= 0.1
    if status is InterventionStatus.CLARIFICATION_NOT_WORTH_COST:
        value -= 0.05
    return max(0.08, min(0.9, round(value, 4)))


def _result_confidence(bundle: InterventionBundle) -> float:
    base = 0.66
    base -= min(0.3, len(bundle.ambiguity_reasons) * 0.03)
    if bundle.low_coverage_mode:
        base -= min(0.34, len(bundle.low_coverage_reasons) * 0.04)
    if not bundle.intervention_records:
        base -= 0.25
    return max(0.08, min(0.9, round(base, 4)))


def _missing_acquisition_record(framing_record_id: str, idx: int) -> InterventionRecord:
    status = InterventionStatus.BLOCKED_DUE_TO_INSUFFICIENT_QUESTIONABILITY
    return InterventionRecord(
        intervention_id=f"intervention-{idx}",
        source_record_ids=(framing_record_id,),
        uncertainty_target_id=f"target:missing-acquisition:{framing_record_id}",
        uncertainty_class=UncertaintyClass.REPAIR_TRIGGER_GAP,
        intervention_status=status,
        ask_policy=AskPolicy(should_ask=False, urgency="low", reason="target binding incomplete"),
        abstain_policy=AbstainPolicy(should_abstain=True, mode=status.value, reason="questionability blocked by missing acquisition basis"),
        guarded_continue_policy=GuardedContinuePolicy(
            should_continue=False,
            required_limits=("closure_blocked_until_answer",),
            reason="cannot continue strongly without g05 target basis",
        ),
        minimal_question_spec=MinimalQuestionSpec(
            spec_id=f"question-spec-missing-{idx}",
            clarification_intent=ClarificationIntent(
                intent_id=f"intent-missing-{idx}",
                target_contrast="missing_acquisition_basis_vs_required_binding",
                allowed_semantic_scope=(f"framing_record:{framing_record_id}",),
                allowed_answer_form="not_askable",
                conceptual_stretch_bound="cannot exceed missing acquisition contract",
            ),
            questionability_reason="questionability blocked because g05 acquisition basis is absent",
            forbidden_assumptions=("do_not_infer_missing_g05_basis",),
            preferred_answer_forbidden=True,
            realization_contract_marker="clarification_not_equal_realized_question",
        ),
        forbidden_presuppositions=("do_not_infer_missing_g05_basis",),
        expected_evidence_gain=ExpectedEvidenceGain(
            gain_score=0.12,
            gain_level="low",
            gain_reason="insufficient target binding due to missing g05 acquisition record",
            impact_scope=("closure",),
            worth_cost=False,
        ),
        downstream_lockouts=(
            "closure_blocked_until_answer",
            "planning_forbidden_on_current_frame",
            "memory_uptake_deferred",
            "questionability_blocked_requires_repair_basis",
            "narrative_commitment_forbidden",
        ),
        l06_repair_binding_refs=(),
        l06_repair_classes=(),
        l06_continuation_statuses=(),
        l06_alignment_ok=False,
        reopen_conditions=("g07:reopen_on_missing_acquisition_rebind",),
        decision=InterventionDecision(
            selected_status=status,
            decision_basis=("missing_g05_basis",),
            blocking_uncertainty=True,
            questionability_sufficient=False,
            cost_worthwhile=False,
        ),
        confidence=0.1,
        provenance="g07 blocked intervention because source acquisition record is absent",
    )


def _abstain_result(
    acq_bundle: SemanticAcquisitionBundle,
    frame_bundle: ConceptFramingBundle,
    discourse_bundle: DiscourseUpdateBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> TargetedClarificationResult:
    source_refs = _derive_source_refs(
        acq_bundle=acq_bundle,
        frame_bundle=frame_bundle,
        discourse_bundle=discourse_bundle,
    )
    l06_update_proposal_absent = not bool(discourse_bundle.update_proposals)
    bundle = InterventionBundle(
        source_acquisition_ref=source_refs.source_acquisition_ref,
        source_acquisition_ref_kind=source_refs.source_acquisition_ref_kind,
        source_acquisition_lineage_ref=source_refs.source_acquisition_lineage_ref,
        source_framing_ref=source_refs.source_framing_ref,
        source_framing_ref_kind=source_refs.source_framing_ref_kind,
        source_framing_lineage_ref=source_refs.source_framing_lineage_ref,
        source_discourse_update_ref=source_refs.source_discourse_update_ref,
        source_discourse_update_ref_kind=source_refs.source_discourse_update_ref_kind,
        source_discourse_update_lineage_ref=source_refs.source_discourse_update_lineage_ref,
        source_perspective_chain_ref=acq_bundle.source_perspective_chain_ref,
        source_applicability_ref=acq_bundle.source_applicability_ref,
        source_runtime_graph_ref=acq_bundle.source_runtime_graph_ref,
        source_grounded_ref=acq_bundle.source_grounded_ref,
        source_dictum_ref=acq_bundle.source_dictum_ref,
        source_syntax_ref=acq_bundle.source_syntax_ref,
        source_surface_ref=acq_bundle.source_surface_ref,
        linked_acquisition_ids=(),
        linked_framing_ids=(),
        linked_update_proposal_ids=tuple(
            proposal.proposal_id for proposal in discourse_bundle.update_proposals
        ),
        linked_repair_ids=tuple(repair.repair_id for repair in discourse_bundle.repair_triggers),
        intervention_records=(),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=tuple(
            dict.fromkeys(
                (
                    "abstain",
                    *(("l06_update_proposal_absent",) if l06_update_proposal_absent else ()),
                    *(("l06_repair_basis_incomplete",) if not discourse_bundle.repair_triggers else ()),
                    "response_realization_contract_absent",
                    "answer_binding_consumer_absent",
                )
            )
        ),
        l06_upstream_bound_here=True,
        l06_repair_basis_bound_here=bool(discourse_bundle.repair_triggers),
        l06_update_proposal_absent=l06_update_proposal_absent,
        l06_repair_localization_must_be_read=bool(discourse_bundle.repair_triggers),
        l06_proposal_requires_acceptance_read=bool(discourse_bundle.update_proposals),
        l06_update_not_accepted=all(
            proposal.acceptance_status is not AcceptanceStatus.ACCEPTED
            for proposal in discourse_bundle.update_proposals
        ),
        intervention_not_discourse_acceptance=True,
        l06_block_or_guard_must_be_read=bool(discourse_bundle.continuation_states),
        l06_continuation_topology_present=bool(discourse_bundle.continuation_states),
        l06_g07_target_alignment_required=bool(discourse_bundle.repair_triggers),
        l06_g07_target_drift_detected=False,
        l06_repair_localization_incompatible=bool(discourse_bundle.repair_triggers),
        repair_trigger_basis_incomplete=True,
        response_realization_contract_absent=True,
        answer_binding_consumer_absent=True,
        answer_binding_ready=False,
        answer_binding_hooks=("bind_answer_to_uncertainty_target", "reopen_linked_acquisition_and_framing_records"),
        intervention_requires_target_binding_read=True,
        downstream_lockouts_must_be_read=True,
        clarification_not_equal_realized_question=True,
        asked_question_not_equal_resolved_uncertainty=True,
        downstream_authority_degraded=True,
        no_final_semantic_closure=True,
        reason="g07 abstained due to insufficient g05/g06 intervention basis",
    )
    gate = evaluate_targeted_clarification_downstream_gate(bundle)
    telemetry = build_targeted_clarification_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="insufficient g05/g06 basis -> g07 abstain",
    )
    return TargetedClarificationResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_semantic_closure=True,
    )
