from __future__ import annotations

from dataclasses import replace

from substrate.contracts import (
    RuntimeState,
    TransitionKind,
    TransitionRequest,
    TransitionResult,
    WriterIdentity,
)
from substrate.runtime_semantic_graph.models import (
    CertaintyClass,
    PolarityClass,
    RuntimeGraphBundle,
    RuntimeGraphResult,
)
from substrate.scope_attribution.models import (
    ApplicabilityBundle,
    ApplicabilityClass,
    ApplicabilityRecord,
    ApplicabilityResult,
    CommitmentLevel,
    PermissionMapping,
    SelfApplicabilityStatus,
    SourceScopeClass,
    TargetScopeClass,
)
from substrate.scope_attribution.policy import evaluate_applicability_downstream_gate
from substrate.scope_attribution.telemetry import (
    applicability_result_snapshot,
    build_applicability_telemetry,
)
from substrate.transition import execute_transition

ATTEMPTED_PATHS: tuple[str, ...] = (
    "g03.validate_typed_inputs",
    "g03.source_scope_attribution",
    "g03.target_scope_attribution",
    "g03.applicability_classification",
    "g03.permission_mapping",
    "g03.ambiguity_preservation",
    "g03.downstream_gate",
)

_SELF_FORMS = {
    "i", "me", "my", "myself", "we", "us", "our", "ourselves",
    "я", "меня", "мне", "мой", "мы", "нас", "нам", "наш", "себя",
}
_USER_FORMS = {
    "you", "your", "yourself", "yourselves", "u",
    "ты", "тебя", "тебе", "твой", "вы", "вас", "вам", "ваш",
}
_THIRD_FORMS = {
    "he", "she", "they", "him", "her", "them", "his", "hers", "their",
    "он", "она", "они", "его", "ее", "её", "их",
}


def build_scope_attribution(
    runtime_graph_result_or_bundle: RuntimeGraphResult | RuntimeGraphBundle,
) -> ApplicabilityResult:
    runtime_bundle, source_lineage = _extract_runtime_graph_input(runtime_graph_result_or_bundle)
    if not runtime_bundle.proposition_candidates:
        return _abstain_result(
            runtime_bundle=runtime_bundle,
            source_lineage=source_lineage,
            reason="runtime graph has no proposition candidates",
        )

    semantic_units = {unit.semantic_unit_id: unit for unit in runtime_bundle.semantic_units}
    bindings = {binding.binding_id: binding for binding in runtime_bundle.role_bindings}

    records: list[ApplicabilityRecord] = []
    mappings: list[PermissionMapping] = []
    ambiguity_reasons: list[str] = list(runtime_bundle.ambiguity_reasons)
    low_coverage_reasons: list[str] = list(runtime_bundle.low_coverage_reasons)
    record_index = 0

    for candidate in runtime_bundle.proposition_candidates:
        record_index += 1
        frame = semantic_units.get(candidate.frame_node_id)
        candidate_bindings = [bindings[binding_id] for binding_id in candidate.role_binding_ids if binding_id in bindings]

        source_scope = _derive_source_scope(candidate.certainty_class, runtime_bundle.low_coverage_mode)
        target_scope = _derive_target_scope(candidate_bindings, frame.predicate if frame else None)
        has_conditional_edge = any(
            edge.target_node_id == candidate.frame_node_id and edge.edge_kind == "operator_scope:conditional"
            for edge in runtime_bundle.graph_edges
        )
        commitment = _derive_commitment_level(
            candidate.certainty_class,
            candidate.polarity,
            has_conditional_edge=has_conditional_edge,
        )
        applicability = _derive_applicability_class(source_scope, target_scope, commitment)
        self_status = _derive_self_status(applicability, target_scope)
        permissions = _derive_permissions(applicability, self_status, commitment, target_scope)

        confidence = _estimate_record_confidence(candidate.confidence, candidate.unresolved, runtime_bundle.low_coverage_mode)
        if target_scope in {TargetScopeClass.MIXED, TargetScopeClass.UNRESOLVED}:
            ambiguity_reasons.append("ambiguous_addressee")
            if target_scope is TargetScopeClass.UNRESOLVED:
                ambiguity_reasons.append("unresolved_self_reference")
        if source_scope in {SourceScopeClass.MIXED, SourceScopeClass.UNRESOLVED}:
            ambiguity_reasons.append("source_target_collision")
        if source_scope is SourceScopeClass.QUOTED and target_scope is TargetScopeClass.SELF_DIRECTED:
            ambiguity_reasons.append("quoted_self_projection")
        if source_scope is SourceScopeClass.HYPOTHETICAL and target_scope is TargetScopeClass.SELF_DIRECTED:
            ambiguity_reasons.append("conditional_self_branch")

        record = ApplicabilityRecord(
            attribution_id=f"attr-{record_index}",
            semantic_unit_id=frame.semantic_unit_id if frame else None,
            proposition_id=candidate.proposition_id,
            source_scope_class=source_scope,
            target_scope_class=target_scope,
            applicability_class=applicability,
            commitment_level=commitment,
            self_applicability_status=self_status,
            downstream_permissions=permissions,
            confidence=confidence,
            provenance="g03 applicability attribution from g02 runtime graph candidate",
        )
        records.append(record)
        mappings.append(
            PermissionMapping(
                proposition_id=candidate.proposition_id,
                permissions=permissions,
                blocked_reasons=tuple(
                    reason for reason in (
                        "self_update_blocked" if "block_self_state_update" in permissions else "",
                        "clarification_recommended" if "recommend_clarification" in permissions else "",
                        "narrative_deferred" if "defer_narrative_binding" in permissions else "",
                    ) if reason
                ),
                confidence=confidence,
            )
        )

    directed_targets = {
        record.target_scope_class
        for record in records
        if record.target_scope_class in {
            TargetScopeClass.SELF_DIRECTED,
            TargetScopeClass.USER_DIRECTED,
            TargetScopeClass.THIRD_PARTY_DIRECTED,
        }
    }
    if len(directed_targets) > 1:
        ambiguity_reasons.append("source_target_collision")
        adjusted_records: list[ApplicabilityRecord] = []
        adjusted_mappings: list[PermissionMapping] = []
        for record in records:
            adjusted_permissions = _force_conservative_permissions(record.downstream_permissions)
            adjusted_records.append(
                replace(
                    record,
                    applicability_class=(
                        ApplicabilityClass.MIXED_APPLICABILITY
                        if record.applicability_class in {
                            ApplicabilityClass.SELF_APPLICABLE,
                            ApplicabilityClass.USER_APPLICABLE,
                            ApplicabilityClass.THIRD_PARTY_APPLICABLE,
                        }
                        else record.applicability_class
                    ),
                    self_applicability_status=(
                        SelfApplicabilityStatus.UNRESOLVED_SELF_REFERENCE
                        if record.target_scope_class in {
                            TargetScopeClass.SELF_DIRECTED,
                            TargetScopeClass.USER_DIRECTED,
                            TargetScopeClass.MIXED,
                        }
                        else record.self_applicability_status
                    ),
                    downstream_permissions=adjusted_permissions,
                )
            )
            adjusted_mappings.append(
                PermissionMapping(
                    proposition_id=record.proposition_id,
                    permissions=adjusted_permissions,
                    blocked_reasons=tuple(
                        reason for reason in (
                            "self_update_blocked" if "block_self_state_update" in adjusted_permissions else "",
                            "clarification_recommended" if "recommend_clarification" in adjusted_permissions else "",
                            "narrative_deferred" if "defer_narrative_binding" in adjusted_permissions else "",
                        ) if reason
                    ),
                    confidence=record.confidence,
                )
            )
        records = adjusted_records
        mappings = adjusted_mappings

    if ambiguity_reasons:
        records = [
            replace(
                record,
                downstream_permissions=(
                    _force_conservative_permissions(record.downstream_permissions)
                    if (
                        "allow_self_appraisal" in record.downstream_permissions
                        and (
                            record.applicability_class in {
                                ApplicabilityClass.MIXED_APPLICABILITY,
                                ApplicabilityClass.UNRESOLVED_APPLICABILITY,
                                ApplicabilityClass.HYPOTHETICAL_NONCOMMITTING,
                                ApplicabilityClass.DENIED_NONUPDATING,
                                ApplicabilityClass.QUOTED_EXTERNAL,
                                ApplicabilityClass.REPORTED_EXTERNAL,
                            }
                            or record.self_applicability_status is SelfApplicabilityStatus.UNRESOLVED_SELF_REFERENCE
                        )
                    )
                    else record.downstream_permissions
                ),
            )
            for record in records
        ]
        mappings = _permission_mappings_from_records(records)

    if not records:
        low_coverage_reasons.append("applicability_records_missing")
    if not mappings:
        low_coverage_reasons.append("permission_mappings_missing")
    if runtime_bundle.low_coverage_mode:
        low_coverage_reasons.append("runtime_graph_low_coverage")

    low_coverage_mode = bool(low_coverage_reasons)
    bundle = ApplicabilityBundle(
        source_runtime_graph_ref=runtime_bundle.source_grounded_ref,
        source_grounded_ref=runtime_bundle.source_grounded_ref,
        source_dictum_ref=runtime_bundle.source_dictum_ref,
        source_syntax_ref=runtime_bundle.source_syntax_ref,
        source_surface_ref=runtime_bundle.source_surface_ref,
        linked_proposition_ids=tuple(candidate.proposition_id for candidate in runtime_bundle.proposition_candidates),
        linked_semantic_unit_ids=tuple(unit.semantic_unit_id for unit in runtime_bundle.semantic_units),
        records=tuple(records),
        permission_mappings=tuple(mappings),
        ambiguity_reasons=tuple(dict.fromkeys(ambiguity_reasons)),
        low_coverage_mode=low_coverage_mode,
        low_coverage_reasons=tuple(dict.fromkeys(low_coverage_reasons)),
        no_truth_upgrade=True,
        reason="g03 scope attribution compiled bounded self-applicability and permission filters",
    )
    gate = evaluate_applicability_downstream_gate(bundle)
    source_lineage = tuple(
        dict.fromkeys(
            (
                runtime_bundle.source_grounded_ref,
                runtime_bundle.source_dictum_ref,
                runtime_bundle.source_syntax_ref,
                *((runtime_bundle.source_surface_ref,) if runtime_bundle.source_surface_ref else ()),
                *source_lineage,
            )
        )
    )
    telemetry = build_applicability_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="g02 runtime graph compiled into bounded source/target applicability permissions",
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
    return ApplicabilityResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=confidence,
        partial_known=partial_known,
        partial_known_reason=partial_known_reason,
        abstain=abstain,
        abstain_reason=abstain_reason,
        no_truth_upgrade=True,
    )


def applicability_result_to_payload(result: ApplicabilityResult) -> dict[str, object]:
    return applicability_result_snapshot(result)


def persist_applicability_result_via_f01(
    *,
    result: ApplicabilityResult,
    runtime_state: RuntimeState,
    transition_id: str,
    requested_at: str,
    cause_chain: tuple[str, ...] = ("g03-scope-attribution-self-applicability-filter",),
) -> TransitionResult:
    request = TransitionRequest(
        transition_id=transition_id,
        transition_kind=TransitionKind.APPLY_INTERNAL_EVENT,
        writer=WriterIdentity.TRANSITION_ENGINE,
        cause_chain=cause_chain,
        requested_at=requested_at,
        event_id=f"ev-{transition_id}",
        event_payload={
            "turn_id": f"scope-attribution-step-{transition_id}",
            "scope_attribution_snapshot": applicability_result_to_payload(result),
        },
    )
    return execute_transition(request, runtime_state)


def _extract_runtime_graph_input(
    runtime_graph_result_or_bundle: RuntimeGraphResult | RuntimeGraphBundle,
) -> tuple[RuntimeGraphBundle, tuple[str, ...]]:
    if isinstance(runtime_graph_result_or_bundle, RuntimeGraphResult):
        return runtime_graph_result_or_bundle.bundle, runtime_graph_result_or_bundle.telemetry.source_lineage
    if isinstance(runtime_graph_result_or_bundle, RuntimeGraphBundle):
        return runtime_graph_result_or_bundle, ()
    raise TypeError("build_scope_attribution requires RuntimeGraphResult or RuntimeGraphBundle")


def _derive_source_scope(certainty: CertaintyClass, low_coverage: bool) -> SourceScopeClass:
    if certainty is CertaintyClass.QUOTED:
        return SourceScopeClass.QUOTED
    if certainty is CertaintyClass.REPORTED:
        return SourceScopeClass.REPORTED
    if certainty is CertaintyClass.INTERROGATIVE:
        return SourceScopeClass.QUESTIONED
    if certainty is CertaintyClass.HYPOTHETICAL:
        return SourceScopeClass.HYPOTHETICAL
    if certainty is CertaintyClass.UNCERTAIN:
        return SourceScopeClass.DIRECT_ASSERTION if not low_coverage else SourceScopeClass.MIXED
    return SourceScopeClass.DIRECT_ASSERTION


def _derive_target_scope(bindings, predicate: str | None) -> TargetScopeClass:
    forms = {(_normalize_form(binding.target_lexeme_hint or "")) for binding in bindings if binding.target_lexeme_hint}
    if predicate:
        forms.add(_normalize_form(predicate))
    has_self = any(form in _SELF_FORMS for form in forms)
    has_user = any(form in _USER_FORMS for form in forms)
    has_third = any(form in _THIRD_FORMS for form in forms)
    directed_count = sum((has_self, has_user, has_third))
    if directed_count >= 2:
        return TargetScopeClass.MIXED
    if has_self:
        return TargetScopeClass.SELF_DIRECTED
    if has_user:
        return TargetScopeClass.USER_DIRECTED
    if has_third:
        return TargetScopeClass.THIRD_PARTY_DIRECTED
    if forms:
        return TargetScopeClass.WORLD_DIRECTED
    return TargetScopeClass.UNRESOLVED


def _derive_commitment_level(
    certainty: CertaintyClass,
    polarity: PolarityClass,
    *,
    has_conditional_edge: bool,
) -> CommitmentLevel:
    if certainty is CertaintyClass.INTERROGATIVE:
        return CommitmentLevel.QUESTIONED
    if certainty is CertaintyClass.HYPOTHETICAL or has_conditional_edge:
        return CommitmentLevel.HYPOTHETICAL
    if certainty in {CertaintyClass.REPORTED, CertaintyClass.QUOTED}:
        return CommitmentLevel.EXTERNAL_REPORTED
    if polarity is PolarityClass.NEGATED:
        return CommitmentLevel.DENIED
    return CommitmentLevel.ASSERTIVE_BOUNDED


def _derive_applicability_class(
    source_scope: SourceScopeClass,
    target_scope: TargetScopeClass,
    commitment: CommitmentLevel,
) -> ApplicabilityClass:
    if target_scope is TargetScopeClass.MIXED:
        return ApplicabilityClass.MIXED_APPLICABILITY
    if target_scope is TargetScopeClass.UNRESOLVED:
        return ApplicabilityClass.UNRESOLVED_APPLICABILITY
    if source_scope is SourceScopeClass.QUOTED:
        return ApplicabilityClass.QUOTED_EXTERNAL
    if source_scope is SourceScopeClass.REPORTED:
        return ApplicabilityClass.REPORTED_EXTERNAL
    if commitment in {CommitmentLevel.HYPOTHETICAL, CommitmentLevel.QUESTIONED}:
        return ApplicabilityClass.HYPOTHETICAL_NONCOMMITTING
    if commitment is CommitmentLevel.DENIED:
        return ApplicabilityClass.DENIED_NONUPDATING
    if target_scope is TargetScopeClass.SELF_DIRECTED:
        return ApplicabilityClass.SELF_APPLICABLE
    if target_scope is TargetScopeClass.USER_DIRECTED:
        return ApplicabilityClass.USER_APPLICABLE
    if target_scope is TargetScopeClass.THIRD_PARTY_DIRECTED:
        return ApplicabilityClass.THIRD_PARTY_APPLICABLE
    return ApplicabilityClass.WORLD_DESCRIPTIVE


def _derive_self_status(
    applicability: ApplicabilityClass,
    target_scope: TargetScopeClass,
) -> SelfApplicabilityStatus:
    if applicability is ApplicabilityClass.SELF_APPLICABLE:
        return SelfApplicabilityStatus.SELF_APPLICABLE
    if target_scope is TargetScopeClass.SELF_DIRECTED:
        return SelfApplicabilityStatus.SELF_MENTIONED_BLOCKED
    if target_scope in {TargetScopeClass.UNRESOLVED, TargetScopeClass.MIXED}:
        return SelfApplicabilityStatus.UNRESOLVED_SELF_REFERENCE
    return SelfApplicabilityStatus.NOT_SELF_TARGETED


def _derive_permissions(
    applicability: ApplicabilityClass,
    self_status: SelfApplicabilityStatus,
    commitment: CommitmentLevel,
    target_scope: TargetScopeClass,
) -> tuple[str, ...]:
    permissions: list[str] = ["keep_as_context_only", "no_truth_upgrade"]
    if applicability is ApplicabilityClass.SELF_APPLICABLE and commitment is CommitmentLevel.ASSERTIVE_BOUNDED:
        permissions.append("allow_self_appraisal")
    else:
        permissions.append("block_self_state_update")

    if applicability in {
        ApplicabilityClass.USER_APPLICABLE,
        ApplicabilityClass.THIRD_PARTY_APPLICABLE,
        ApplicabilityClass.WORLD_DESCRIPTIVE,
        ApplicabilityClass.QUOTED_EXTERNAL,
        ApplicabilityClass.REPORTED_EXTERNAL,
    }:
        permissions.append("allow_external_model_update")
    else:
        permissions.append("defer_narrative_binding")

    if applicability in {
        ApplicabilityClass.MIXED_APPLICABILITY,
        ApplicabilityClass.UNRESOLVED_APPLICABILITY,
        ApplicabilityClass.HYPOTHETICAL_NONCOMMITTING,
        ApplicabilityClass.DENIED_NONUPDATING,
    } or self_status is SelfApplicabilityStatus.UNRESOLVED_SELF_REFERENCE:
        permissions.append("recommend_clarification")

    if commitment in {CommitmentLevel.EXTERNAL_REPORTED, CommitmentLevel.HYPOTHETICAL, CommitmentLevel.QUESTIONED}:
        permissions.append("defer_narrative_binding")

    if target_scope is TargetScopeClass.DISCOURSE_DIRECTED:
        permissions.append("defer_narrative_binding")

    return tuple(dict.fromkeys(permissions))


def _force_conservative_permissions(permissions: tuple[str, ...]) -> tuple[str, ...]:
    adjusted = [perm for perm in permissions if perm != "allow_self_appraisal"]
    adjusted.extend(
        [
            "block_self_state_update",
            "defer_narrative_binding",
            "recommend_clarification",
        ]
    )
    return tuple(dict.fromkeys(adjusted))


def _permission_mappings_from_records(records: list[ApplicabilityRecord] | tuple[ApplicabilityRecord, ...]) -> list[PermissionMapping]:
    mappings: list[PermissionMapping] = []
    for record in records:
        mappings.append(
            PermissionMapping(
                proposition_id=record.proposition_id,
                permissions=record.downstream_permissions,
                blocked_reasons=tuple(
                    reason for reason in (
                        "self_update_blocked" if "block_self_state_update" in record.downstream_permissions else "",
                        "clarification_recommended" if "recommend_clarification" in record.downstream_permissions else "",
                        "narrative_deferred" if "defer_narrative_binding" in record.downstream_permissions else "",
                    ) if reason
                ),
                confidence=record.confidence,
            )
        )
    return mappings


def _estimate_record_confidence(base: float, unresolved: bool, low_coverage: bool) -> float:
    value = base
    if unresolved:
        value -= 0.18
    if low_coverage:
        value -= 0.12
    return max(0.1, min(0.9, round(value, 4)))


def _estimate_result_confidence(bundle: ApplicabilityBundle) -> float:
    base = 0.74
    if bundle.low_coverage_mode:
        base -= min(0.28, len(bundle.low_coverage_reasons) * 0.05)
    base -= min(0.25, len(bundle.ambiguity_reasons) * 0.02)
    if not bundle.records:
        base -= 0.25
    return max(0.08, min(0.92, round(base, 4)))


def _normalize_form(value: str) -> str:
    return value.strip().lower()


def _abstain_result(
    *,
    runtime_bundle: RuntimeGraphBundle,
    source_lineage: tuple[str, ...],
    reason: str,
) -> ApplicabilityResult:
    bundle = ApplicabilityBundle(
        source_runtime_graph_ref=runtime_bundle.source_grounded_ref,
        source_grounded_ref=runtime_bundle.source_grounded_ref,
        source_dictum_ref=runtime_bundle.source_dictum_ref,
        source_syntax_ref=runtime_bundle.source_syntax_ref,
        source_surface_ref=runtime_bundle.source_surface_ref,
        linked_proposition_ids=tuple(candidate.proposition_id for candidate in runtime_bundle.proposition_candidates),
        linked_semantic_unit_ids=tuple(unit.semantic_unit_id for unit in runtime_bundle.semantic_units),
        records=(),
        permission_mappings=(),
        ambiguity_reasons=(reason,),
        low_coverage_mode=True,
        low_coverage_reasons=("abstain",),
        no_truth_upgrade=True,
        reason="g03 abstained due to insufficient g02 runtime graph basis",
    )
    gate = evaluate_applicability_downstream_gate(bundle)
    telemetry = build_applicability_telemetry(
        bundle=bundle,
        source_lineage=source_lineage,
        attempted_paths=ATTEMPTED_PATHS,
        downstream_gate=gate,
        causal_basis="insufficient g02 graph -> g03 abstain",
    )
    return ApplicabilityResult(
        bundle=bundle,
        telemetry=telemetry,
        confidence=0.08,
        partial_known=True,
        partial_known_reason=reason,
        abstain=True,
        abstain_reason=reason,
        no_truth_upgrade=True,
    )
