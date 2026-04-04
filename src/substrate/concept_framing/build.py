from __future__ import annotations

from dataclasses import replace

from substrate.concept_framing.models import (
    ConceptFramingBundle,
    ConceptFramingRecord,
    ConceptFramingResult,
    FrameFamily,
    FramingCompetitionLink,
    FramingStatus,
    ReframingCondition,
    ReframingConditionKind,
    VulnerabilityLevel,
    VulnerabilityProfile,
)
from substrate.concept_framing.policy import evaluate_concept_framing_downstream_gate
from substrate.concept_framing.telemetry import (
    build_concept_framing_telemetry,
    concept_framing_result_snapshot,
)
from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.semantic_acquisition.models import (
    AcquisitionStatus,
    RevisionConditionKind,
    SemanticAcquisitionBundle,
    SemanticAcquisitionResult,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g06.validate_typed_inputs",
    "g06.frame_candidate_generation",
    "g06.frame_selection_or_coexistence",
    "g06.vulnerability_audit",
    "g06.reframing_condition_derivation",
    "g06.downstream_gate",
)


def build_concept_framing(
    semantic_acquisition_result_or_bundle: SemanticAcquisitionResult | SemanticAcquisitionBundle,
) -> ConceptFramingResult:
    acquisition_bundle, source_lineage = _extract_acquisition_input(semantic_acquisition_result_or_bundle)
    if not acquisition_bundle.acquisition_records:
        return _abstain_result(
            acquisition_bundle=acquisition_bundle,
            source_lineage=source_lineage,
            reason="semantic acquisition has no records for framing",
        )

    # L06 exists in-repo, but this G06 path is not yet runtime-bound to L06 proposal intake.
    l06_update_proposal_not_bound_here = True
    ambiguity_reasons: list[str] = list(acquisition_bundle.ambiguity_reasons)
    low_coverage_reasons: list[str] = list(acquisition_bundle.low_coverage_reasons)
    low_coverage_reasons.append("l06_update_proposal_not_bound_here")

    records: list[ConceptFramingRecord] = []
    groups: dict[str, list[str]] = {}
    group_signatures: dict[str, set[tuple[str, str, str]]] = {}
    group_index = 0
    framing_index = 0

    for acquisition_record in acquisition_bundle.acquisition_records:
        framing_index += 1
        frame_family, alternatives, high_impact = _derive_frame_family(acquisition_record)
        framing_status = _derive_framing_status(acquisition_record, high_impact)
        vulnerability = _derive_vulnerability_profile(
            acquisition_record=acquisition_record,
            frame_family=frame_family,
            alternatives=alternatives,
            framing_status=framing_status,
        )
        reframing_conditions = _derive_reframing_conditions(acquisition_record, framing_status)
        downstream_cautions = _derive_downstream_cautions(
            framing_status=framing_status,
            high_impact=vulnerability.high_impact,
            l06_update_proposal_not_bound_here=l06_update_proposal_not_bound_here,
        )
        downstream_permissions = _derive_downstream_permissions(
            framing_status=framing_status,
            high_impact=vulnerability.high_impact,
        )

        basis = [
            f"acquisition_status:{acquisition_record.acquisition_status.value}",
            f"support:{acquisition_record.support_conflict_profile.support_score}",
            f"conflict:{acquisition_record.support_conflict_profile.conflict_score}",
            *acquisition_record.support_conflict_profile.support_reasons,
            *acquisition_record.support_conflict_profile.conflict_reasons,
        ]
        unresolved_dependencies = tuple(dict.fromkeys(acquisition_record.support_conflict_profile.unresolved_slots))
        if unresolved_dependencies:
            ambiguity_reasons.append("framing_unresolved_dependencies")
        if framing_status is FramingStatus.COMPETING_FRAMES:
            ambiguity_reasons.append("competing_frames")
        if framing_status is FramingStatus.BLOCKED_HIGH_IMPACT_FRAME:
            ambiguity_reasons.append("blocked_high_impact_frame")

        group_key = acquisition_record.semantic_unit_id or f"prop:{acquisition_record.proposition_id}"
        if group_key not in groups:
            group_index += 1
            groups[group_key] = []
        framing_id = f"frame-{framing_index}"
        competition_id = f"competition-{group_index}"
        groups[group_key].append(framing_id)
        group_signatures.setdefault(group_key, set()).add(
            (frame_family.value, framing_status.value, _competition_signature(acquisition_record))
        )

        record = ConceptFramingRecord(
            framing_id=framing_id,
            acquisition_id=acquisition_record.acquisition_id,
            semantic_unit_id=acquisition_record.semantic_unit_id,
            frame_family=frame_family,
            framing_status=framing_status,
            frame_components=tuple(dict.fromkeys(_frame_components(frame_family, alternatives, acquisition_record))),
            framing_basis=tuple(dict.fromkeys(basis)),
            alternative_framings=alternatives,
            vulnerability_profile=vulnerability,
            unresolved_dependencies=unresolved_dependencies,
            reframing_conditions=reframing_conditions,
            downstream_cautions=downstream_cautions,
            downstream_permissions=downstream_permissions,
            context_anchor=acquisition_record.context_anchor,
            confidence=_estimate_record_confidence(
                acquisition_record.confidence,
                framing_status,
                vulnerability,
            ),
            provenance="g06 concept framing + vulnerability audit from g05 provisional acquisition",
        )
        records.append(record)

    records = _apply_frame_competition(records, groups, group_signatures)
    competition_links = _build_competition_links(records, groups)

    repair_trigger_basis_incomplete = l06_update_proposal_not_bound_here and any(
        record.reframing_conditions for record in records
    )
    if repair_trigger_basis_incomplete:
        low_coverage_reasons.append("repair_trigger_basis_incomplete")

    if not competition_links:
        low_coverage_reasons.append("competition_links_missing")
    if not records:
        low_coverage_reasons.append("framing_records_missing")

    low_coverage_mode = bool(low_coverage_reasons)
    bundle = ConceptFramingBundle(
        source_acquisition_ref=acquisition_bundle.source_perspective_chain_ref,
        source_perspective_chain_ref=acquisition_bundle.source_perspective_chain_ref,
        source_applicability_ref=acquisition_bundle.source_applicability_ref,
        source_runtime_graph_ref=acquisition_bundle.source_runtime_graph_ref,
        source_grounded_ref=acquisition_bundle.source_grounded_ref,
        source_dictum_ref=acquisition_bundle.source_dictum_ref,
        source_syntax_ref=acquisition_bundle.source_syntax_ref,
        source_surface_ref=acquisition_bundle.source_surface_ref,
        linked_acquisition_ids=tuple(record.acquisition_id for record in records),
        linked_proposition_ids=acquisition_bundle.linked_proposition_ids,
        linked_semantic_unit_ids=acquisition_bundle.linked_semantic_unit_ids,
        framing_records=tuple(records),
        competition_links=tuple(competition_links),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        low_coverage_mode=low_coverage_mode,
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        l06_update_proposal_not_bound_here=l06_update_proposal_not_bound_here,
        repair_trigger_basis_incomplete=repair_trigger_basis_incomplete,
        no_final_semantic_closure=True,
        reason="g06 compiled bounded concept framing and vulnerability audit over g05 acquisition",
    )
    gate = evaluate_concept_framing_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                acquisition_bundle.source_perspective_chain_ref,
                acquisition_bundle.source_applicability_ref,
                acquisition_bundle.source_runtime_graph_ref,
                acquisition_bundle.source_grounded_ref,
                acquisition_bundle.source_dictum_ref,
                acquisition_bundle.source_syntax_ref,
                *((acquisition_bundle.source_surface_ref,) if acquisition_bundle.source_surface_ref else ()),
                *source_lineage,
            )
        )
    )
    telemetry = build_concept_framing_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="g05 provisional meanings packaged into bounded concept frames with vulnerability audit",
    )
    confidence = _estimate_result_confidence(bundle)
    partial_known = bool(bundle.low_coverage_mode or bundle.ambiguity_reasons)
    partial_known_reason = (
        "; ".join(bundle.ambiguity_reasons)
        if bundle.ambiguity_reasons
        else ("; ".join(bundle.low_coverage_reasons) if bundle.low_coverage_reasons else None)
    )
    abstain = not gate.accepted
    abstain_reason = None if gate.accepted else gate.reason
    return ConceptFramingResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_final_semantic_closure=True,
    )


def concept_framing_result_to_payload(result: ConceptFramingResult) -> dict[str, object]:
    return concept_framing_result_snapshot(result)


def persist_concept_framing_result_via_f01(
    *,
    result: ConceptFramingResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("g06-concept-framing-vulnerability-audit",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"concept-framing-step-{transition_id}",
            "concept_framing_snapshot": concept_framing_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_acquisition_input(
    semantic_acquisition_result_or_bundle: SemanticAcquisitionResult | SemanticAcquisitionBundle,
) -> tuple[SemanticAcquisitionBundle, tuple[str, ...]]:
    if isinstance(semantic_acquisition_result_or_bundle, SemanticAcquisitionResult):
        return semantic_acquisition_result_or_bundle.bundle, semantic_acquisition_result_or_bundle.telemetry.source_lineage
    if isinstance(semantic_acquisition_result_or_bundle, SemanticAcquisitionBundle):
        return semantic_acquisition_result_or_bundle, ()
    raise TypeError("build_concept_framing requires SemanticAcquisitionResult or SemanticAcquisitionBundle")


def _derive_frame_family(acquisition_record) -> tuple[FrameFamily, tuple[FrameFamily, ...], bool]:
    high_impact_candidates: list[FrameFamily] = []
    non_high_impact_candidates: list[FrameFamily] = []
    conflict = set(acquisition_record.support_conflict_profile.conflict_reasons)
    unresolved = set(acquisition_record.support_conflict_profile.unresolved_slots)

    if "binding_blocked" in conflict:
        high_impact_candidates.append(FrameFamily.OBLIGATION_RELEVANT)
        high_impact_candidates.append(FrameFamily.NORMATIVE)
    if {"source_scope_unknown", "commitment_owner_ambiguous", "owner_flattening_risk"} & conflict:
        high_impact_candidates.append(FrameFamily.IDENTITY_RELEVANT)
    if "cross_turn_repair_pending" in conflict and "source_scope_unknown" in conflict:
        high_impact_candidates.append(FrameFamily.THREAT_RELEVANT)
    if {"commitment_owner", "perspective_owner", "source_scope"} & unresolved:
        high_impact_candidates.append(FrameFamily.DEPENDENCY_RELEVANT)
    if any(item.startswith("assertion_mode:") for item in conflict):
        non_high_impact_candidates.append(FrameFamily.EVALUATIVE)
    if "clarification_required" in conflict and not high_impact_candidates:
        non_high_impact_candidates.append(FrameFamily.EVALUATIVE)

    alternatives = tuple(
        dict.fromkeys(
            (
                FrameFamily.DESCRIPTIVE_LITERAL,
                *high_impact_candidates,
                *non_high_impact_candidates,
            )
        )
    )

    if acquisition_record.acquisition_status is AcquisitionStatus.CONTEXT_ONLY:
        return FrameFamily.EXTERNAL_CONTEXT_ONLY, alternatives, bool(high_impact_candidates)
    if acquisition_record.acquisition_status is AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION and high_impact_candidates:
        return high_impact_candidates[0], alternatives, True
    if acquisition_record.acquisition_status is AcquisitionStatus.DISCARDED_AS_INCOHERENT and high_impact_candidates:
        return high_impact_candidates[0], alternatives, True
    return FrameFamily.DESCRIPTIVE_LITERAL, alternatives, bool(high_impact_candidates)


def _derive_framing_status(acquisition_record, high_impact: bool) -> FramingStatus:
    status = acquisition_record.acquisition_status
    support_score = acquisition_record.support_conflict_profile.support_score
    conflict_pressure = max(
        float(acquisition_record.support_conflict_profile.conflict_score),
        float(len(acquisition_record.support_conflict_profile.conflict_reasons)),
    )
    if status is AcquisitionStatus.STABLE_PROVISIONAL:
        return FramingStatus.DOMINANT_PROVISIONAL_FRAME
    if status is AcquisitionStatus.WEAK_PROVISIONAL:
        if high_impact or conflict_pressure >= 2 or support_score < 1.0:
            return FramingStatus.UNDERFRAMED_MEANING
        return FramingStatus.DOMINANT_PROVISIONAL_FRAME
    if status is AcquisitionStatus.COMPETING_PROVISIONAL:
        return FramingStatus.COMPETING_FRAMES
    if status is AcquisitionStatus.BLOCKED_PENDING_CLARIFICATION:
        if high_impact:
            return FramingStatus.BLOCKED_HIGH_IMPACT_FRAME
        return FramingStatus.UNDERFRAMED_MEANING
    if status is AcquisitionStatus.CONTEXT_ONLY:
        return FramingStatus.CONTEXT_ONLY_FRAME_HINT
    return FramingStatus.DISCARDED_OVERREACH


def _derive_vulnerability_profile(
    *,
    acquisition_record,
    frame_family: FrameFamily,
    alternatives: tuple[FrameFamily, ...],
    framing_status: FramingStatus,
) -> VulnerabilityProfile:
    dimensions: list[str] = []
    fragility: list[str] = []
    impact_radius: list[str] = ["closure"]

    if frame_family in {FrameFamily.NORMATIVE, FrameFamily.OBLIGATION_RELEVANT}:
        dimensions.append("hidden_normative_load")
        impact_radius.extend(["planning", "appraisal"])
    if frame_family is FrameFamily.THREAT_RELEVANT:
        dimensions.append("threat_inflation_risk")
        impact_radius.extend(["planning", "safety"])
    if frame_family in {FrameFamily.IDENTITY_RELEVANT, FrameFamily.DEPENDENCY_RELEVANT}:
        dimensions.append("identity_dependency_overbinding")
        impact_radius.extend(["appraisal", "memory"])
    if frame_family is FrameFamily.EVALUATIVE:
        dimensions.append("evaluative_scope_fragility")

    if framing_status in {FramingStatus.COMPETING_FRAMES, FramingStatus.UNDERFRAMED_MEANING}:
        fragility.append("alternative_frame_pressure")
        impact_radius.append("clarification")
    if framing_status is FramingStatus.BLOCKED_HIGH_IMPACT_FRAME:
        fragility.append("high_impact_frame_blocked")
        impact_radius.extend(["clarification", "planning", "memory"])
    if acquisition_record.support_conflict_profile.unresolved_slots:
        fragility.append("unresolved_dependencies_present")
    if acquisition_record.support_conflict_profile.conflict_reasons:
        fragility.append("conflict_profile_present")
    if acquisition_record.support_conflict_profile.support_score < 1.0:
        fragility.append("support_basis_sparse")
    if acquisition_record.support_conflict_profile.conflict_reasons and not acquisition_record.revision_conditions:
        fragility.append("revision_hooks_missing_under_conflict")
    if len(alternatives) > 1:
        fragility.append("alternative_framings_present")

    distinct = tuple(dict.fromkeys(dimensions))
    high_impact = bool(
        set(distinct)
        & {
            "hidden_normative_load",
            "threat_inflation_risk",
            "identity_dependency_overbinding",
        }
    )
    fragility = tuple(dict.fromkeys(fragility))

    if framing_status in {FramingStatus.BLOCKED_HIGH_IMPACT_FRAME, FramingStatus.DISCARDED_OVERREACH}:
        level = VulnerabilityLevel.HIGH
    elif high_impact or len(fragility) >= 3:
        level = VulnerabilityLevel.ELEVATED
    elif fragility:
        level = VulnerabilityLevel.MODERATE
    else:
        level = VulnerabilityLevel.LOW

    return VulnerabilityProfile(
        vulnerability_level=level,
        dimensions=distinct,
        fragility_reasons=fragility,
        high_impact=high_impact,
        impact_radius=tuple(dict.fromkeys(impact_radius)),
    )


def _derive_reframing_conditions(acquisition_record, framing_status: FramingStatus) -> tuple[ReframingCondition, ...]:
    conditions: list[ReframingCondition] = []
    idx = 0

    def _add(kind: ReframingConditionKind, reason: str, confidence: float) -> None:
        nonlocal idx
        idx += 1
        conditions.append(
            ReframingCondition(
                condition_id=f"reframe-{idx}",
                condition_kind=kind,
                trigger_reason=reason,
                confidence=max(0.08, min(0.9, round(confidence, 4))),
                provenance="g06 reframing condition from g05 revision hook and framing fragility",
            )
        )

    for revision in acquisition_record.revision_conditions:
        if revision.condition_kind is RevisionConditionKind.REOPEN_ON_CLARIFICATION_ANSWER:
            _add(ReframingConditionKind.REOPEN_ON_CLARIFICATION_ANSWER, revision.trigger_reason, revision.confidence)
        elif revision.condition_kind is RevisionConditionKind.REOPEN_ON_CORRECTION:
            _add(ReframingConditionKind.REOPEN_ON_CORRECTION, revision.trigger_reason, revision.confidence)
        elif revision.condition_kind is RevisionConditionKind.REOPEN_ON_QUOTE_REPAIR:
            _add(ReframingConditionKind.REOPEN_ON_QUOTE_REPAIR, revision.trigger_reason, revision.confidence)
        elif revision.condition_kind is RevisionConditionKind.REOPEN_ON_TARGET_REBINDING:
            _add(ReframingConditionKind.REOPEN_ON_TARGET_REBINDING, revision.trigger_reason, revision.confidence)
        elif revision.condition_kind is RevisionConditionKind.REOPEN_ON_TEMPORAL_DISAMBIGUATION:
            _add(ReframingConditionKind.REOPEN_ON_TEMPORAL_DISAMBIGUATION, revision.trigger_reason, revision.confidence)
        elif revision.condition_kind is RevisionConditionKind.REOPEN_ON_STRONGER_BINDING_EVIDENCE:
            _add(ReframingConditionKind.REOPEN_ON_STRONGER_BINDING_EVIDENCE, revision.trigger_reason, revision.confidence)

    if framing_status in {
        FramingStatus.UNDERFRAMED_MEANING,
        FramingStatus.COMPETING_FRAMES,
        FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
    }:
        _add(
            ReframingConditionKind.REOPEN_ON_DISCOURSE_CONTINUATION,
            "frame remains reopenable under next discourse continuation",
            0.5,
        )
    return tuple(conditions)


def _derive_downstream_cautions(
    *,
    framing_status: FramingStatus,
    high_impact: bool,
    l06_update_proposal_not_bound_here: bool,
) -> tuple[str, ...]:
    cautions: list[str] = ["provisional_frame_not_final"]
    if framing_status in {
        FramingStatus.UNDERFRAMED_MEANING,
        FramingStatus.COMPETING_FRAMES,
        FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
    }:
        cautions.append("clarification_worthy_frame")
    if framing_status is FramingStatus.BLOCKED_HIGH_IMPACT_FRAME:
        cautions.append("blocked_high_impact_frame")
    if framing_status is FramingStatus.CONTEXT_ONLY_FRAME_HINT:
        cautions.append("context_only_frame_hint")
    if high_impact:
        cautions.append("high_impact_frame_guard_required")
    if l06_update_proposal_not_bound_here:
        cautions.append("framing_requires_discourse_update_read")
    return tuple(dict.fromkeys(cautions))


def _derive_downstream_permissions(
    *,
    framing_status: FramingStatus,
    high_impact: bool,
) -> tuple[str, ...]:
    permissions: list[str] = ["no_final_semantic_closure"]
    if framing_status is FramingStatus.DOMINANT_PROVISIONAL_FRAME:
        permissions.append("allow_guarded_closure_candidate")
    else:
        permissions.append("closure_must_preserve_frame_uncertainty")
        permissions.append("memory_uptake_blocked")
    if framing_status in {
        FramingStatus.COMPETING_FRAMES,
        FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
        FramingStatus.UNDERFRAMED_MEANING,
        FramingStatus.DISCARDED_OVERREACH,
    }:
        permissions.append("planning_blocked_high_impact_frame")
    if framing_status in {
        FramingStatus.CONTEXT_ONLY_FRAME_HINT,
        FramingStatus.COMPETING_FRAMES,
        FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
        FramingStatus.UNDERFRAMED_MEANING,
    }:
        permissions.append("appraisal_context_only")
    if high_impact:
        permissions.append("safety_escalation_not_authorized_from_frame_only")
    return tuple(dict.fromkeys(permissions))


def _frame_components(frame_family: FrameFamily, alternatives: tuple[FrameFamily, ...], acquisition_record) -> list[str]:
    components = [f"frame_family:{frame_family.value}", f"acquisition_status:{acquisition_record.acquisition_status.value}"]
    components.extend(f"alternative:{family.value}" for family in alternatives if family is not frame_family)
    components.extend(f"support:{reason}" for reason in acquisition_record.support_conflict_profile.support_reasons)
    components.extend(f"conflict:{reason}" for reason in acquisition_record.support_conflict_profile.conflict_reasons)
    return components


def _apply_frame_competition(
    records: list[ConceptFramingRecord],
    groups: dict[str, list[str]],
    group_signatures: dict[str, set[tuple[str, str, str]]],
) -> list[ConceptFramingRecord]:
    by_id = {record.framing_id: record for record in records}
    updated: dict[str, ConceptFramingRecord] = dict(by_id)

    for group_key, members in groups.items():
        signatures = group_signatures.get(group_key, set())
        incompatible = len(signatures) > 1 and len(members) > 1
        for member_id in members:
            record = updated[member_id]
            if incompatible and record.framing_status in {
                FramingStatus.DOMINANT_PROVISIONAL_FRAME,
                FramingStatus.UNDERFRAMED_MEANING,
            }:
                cautions = tuple(dict.fromkeys((*record.downstream_cautions, "competing_frames")))
                permissions = tuple(
                    dict.fromkeys(
                        (
                            *record.downstream_permissions,
                            "closure_must_preserve_frame_uncertainty",
                            "memory_uptake_blocked",
                        )
                    )
                )
                record = replace(
                    record,
                    framing_status=FramingStatus.COMPETING_FRAMES,
                    downstream_cautions=cautions,
                    downstream_permissions=permissions,
                )
            updated[member_id] = record
    return [updated[record.framing_id] for record in records]


def _competition_signature(acquisition_record) -> str:
    conflict = set(acquisition_record.support_conflict_profile.conflict_reasons)
    unresolved = set(acquisition_record.support_conflict_profile.unresolved_slots)
    if {"source_scope_unknown", "commitment_owner_ambiguous", "owner_flattening_risk"} & conflict:
        return "owner_scope_risk"
    if {"binding_blocked"} & conflict:
        return "normative_pressure"
    if {"cross_turn_repair_pending", "bundle_cross_turn_repair_pending"} & conflict:
        return "repair_pressure"
    if {"source_scope", "commitment_owner", "perspective_owner"} & unresolved:
        return "unresolved_binding"
    return "low_conflict"


def _build_competition_links(
    records: list[ConceptFramingRecord],
    groups: dict[str, list[str]],
) -> list[FramingCompetitionLink]:
    links: list[FramingCompetitionLink] = []
    for idx, (_, members) in enumerate(groups.items(), start=1):
        competing: set[str] = set()
        compatible: set[str] = set()
        member_set = tuple(members)
        for record in records:
            if record.framing_id not in member_set:
                continue
            for peer in member_set:
                if peer == record.framing_id:
                    continue
                if record.framing_status is FramingStatus.COMPETING_FRAMES:
                    competing.add(peer)
                else:
                    compatible.add(peer)
        links.append(
            FramingCompetitionLink(
                competition_id=f"competition-{idx}",
                member_framing_ids=member_set,
                competing_framing_ids=tuple(sorted(competing)),
                compatible_framing_ids=tuple(sorted(compatible)),
                confidence=max(0.1, min(0.9, round(0.7 - (0.06 * len(competing)), 4))),
                provenance="g06 framing competition/compatibility linkage",
            )
        )
    return links


def _estimate_record_confidence(base: float, framing_status: FramingStatus, vulnerability: VulnerabilityProfile) -> float:
    value = base
    if framing_status in {
        FramingStatus.UNDERFRAMED_MEANING,
        FramingStatus.COMPETING_FRAMES,
        FramingStatus.BLOCKED_HIGH_IMPACT_FRAME,
        FramingStatus.CONTEXT_ONLY_FRAME_HINT,
    }:
        value -= 0.08
    if vulnerability.vulnerability_level in {VulnerabilityLevel.ELEVATED, VulnerabilityLevel.HIGH}:
        value -= 0.08
    floor = 0.08 if framing_status is FramingStatus.DISCARDED_OVERREACH else 0.22
    return max(floor, min(0.9, round(value, 4)))


def _estimate_result_confidence(bundle: ConceptFramingBundle) -> float:
    base = 0.68
    base -= min(0.3, len(bundle.ambiguity_reasons) * 0.03)
    if bundle.low_coverage_mode:
        base -= min(0.3, len(bundle.low_coverage_reasons) * 0.045)
    if not bundle.framing_records:
        base -= 0.25
    return max(0.08, min(0.9, round(base, 4)))


def _abstain_result(
    *,
    acquisition_bundle: SemanticAcquisitionBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> ConceptFramingResult:
    bundle = ConceptFramingBundle(
        source_acquisition_ref=acquisition_bundle.source_perspective_chain_ref,
        source_perspective_chain_ref=acquisition_bundle.source_perspective_chain_ref,
        source_applicability_ref=acquisition_bundle.source_applicability_ref,
        source_runtime_graph_ref=acquisition_bundle.source_runtime_graph_ref,
        source_grounded_ref=acquisition_bundle.source_grounded_ref,
        source_dictum_ref=acquisition_bundle.source_dictum_ref,
        source_syntax_ref=acquisition_bundle.source_syntax_ref,
        source_surface_ref=acquisition_bundle.source_surface_ref,
        linked_acquisition_ids=(),
        linked_proposition_ids=acquisition_bundle.linked_proposition_ids,
        linked_semantic_unit_ids=acquisition_bundle.linked_semantic_unit_ids,
        framing_records=(),
        competition_links=(),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=("abstain", "l06_update_proposal_not_bound_here"),
        l06_update_proposal_not_bound_here=True,
        repair_trigger_basis_incomplete=True,
        no_final_semantic_closure=True,
        reason="g06 abstained due to insufficient g05 acquisition basis",
    )
    gate = evaluate_concept_framing_downstream_gate(bundle)
    telemetry = build_concept_framing_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="insufficient g05 acquisition -> g06 abstain",
    )
    return ConceptFramingResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_final_semantic_closure=True,
    )
