from __future__ import annotations

from substrate.n02_identity_drift_reflection.models import (
    N02BaselineReference,
    N02BaselineValidityStatus,
    N02CommitmentHistoryEvent,
    N02ConflictStatus,
    N02CurrentIdentityEvidence,
    N02DriftKind,
    N02DriftLedger,
    N02GateDecision,
    N02IdentityDriftEntry,
    N02IdentitySubstrateChange,
    N02InputBundle,
    N02ReflectionNeedLevel,
    N02Result,
    N02ScopeMarker,
    N02SubstrateChangeKind,
    N02Telemetry,
)


def build_n02_identity_drift_reflection(
    *,
    tick_id: str,
    tick_index: int,
    input_bundle: N02InputBundle | None,
    reflection_enabled: bool = True,
) -> N02Result:
    if not reflection_enabled:
        return _minimal_result(
            bundle_id=f"n02:{tick_id}:bundle:none",
            reason="N02 gate disabled in test fixture",
            restrictions=("n02_disabled", "n02_no_clean_drift_claim"),
        )

    if not isinstance(input_bundle, N02InputBundle):
        return _minimal_result(
            bundle_id=f"n02:{tick_id}:bundle:none",
            reason=(
                "n02 requires typed baseline/current/substrate bundles and does not treat text-only deltas as "
                "identity-drift evidence"
            ),
            restrictions=("insufficient_n02_basis", "n02_no_clean_drift_claim"),
        )

    if not input_bundle.current_references:
        return _minimal_result(
            bundle_id=input_bundle.bundle_id,
            reason="n02 received no current identity references",
            restrictions=("n02_no_current_reference", "n02_no_clean_drift_claim"),
        )

    entries: list[N02IdentityDriftEntry] = []
    no_claim_markers: list[str] = []
    required_restrictions: list[str] = []
    reason_codes: list[str] = []
    stable_count = 0
    bounded_count = 0
    reflection_needed_count = 0
    unresolved_count = 0
    context_split_count = 0
    no_clean_count = 0
    baseline_uncertain_count = 0
    overreflection_guard_count = 0
    text_diff_only_blocked_count = 0
    substrate_ablation_or_missing_count = 0
    downstream_caution_count = 0

    for idx, current in enumerate(input_bundle.current_references):
        baseline = _select_baseline_for_current(
            baselines=input_bundle.baseline_references,
            current=current,
        )
        region_changes = tuple(
            item
            for item in input_bundle.substrate_changes
            if item.region is current.observed_region
            and (item.context_scope == current.context_scope or item.context_scope == "global")
        )
        region_history = tuple(
            item
            for item in input_bundle.commitment_history
            if item.region is current.observed_region
        )

        entry = _evaluate_reference(
            tick_id=tick_id,
            tick_index=tick_index,
            index=idx,
            baseline=baseline,
            current=current,
            region_changes=region_changes,
            region_history=region_history,
            source_lineage=input_bundle.source_lineage,
        )
        entries.append(entry)
        reason_codes.extend(entry.reason_codes)

        if entry.drift_kind is N02DriftKind.STABLE_CONTINUATION:
            stable_count += 1
        if entry.drift_kind is N02DriftKind.BOUNDED_REVISION:
            bounded_count += 1
        if entry.reflection_need_level in {N02ReflectionNeedLevel.MODERATE, N02ReflectionNeedLevel.HIGH}:
            reflection_needed_count += 1
        if entry.drift_kind is N02DriftKind.UNRESOLVED_IDENTITY_TENSION:
            unresolved_count += 1
        if entry.drift_kind is N02DriftKind.CONTEXT_SPLIT_DETECTED:
            context_split_count += 1
        if entry.drift_kind is N02DriftKind.NO_CLEAN_DRIFT_CLAIM:
            no_clean_count += 1
            no_claim_markers.append("n02_no_clean_drift_claim")
        if "baseline_uncertain" in entry.reason_codes:
            baseline_uncertain_count += 1
        if "overreflection_guard_applied" in entry.reason_codes:
            overreflection_guard_count += 1
        if "text_diff_only_not_identity_drift" in entry.reason_codes:
            text_diff_only_blocked_count += 1
        if "substrate_missing_or_ablation" in entry.reason_codes:
            substrate_ablation_or_missing_count += 1
        if entry.downstream_caution:
            downstream_caution_count += 1

    if unresolved_count > 0:
        required_restrictions.append("n02_unresolved_identity_tension_recheck")
    if context_split_count > 0:
        required_restrictions.append("n02_context_split_caution")
    if no_clean_count > 0:
        required_restrictions.append("n02_no_clean_drift_claim")
    if baseline_uncertain_count > 0:
        required_restrictions.append("n02_baseline_uncertain")
    if text_diff_only_blocked_count > 0:
        required_restrictions.append("n02_text_diff_only_blocked")

    reflection_consumer_ready = any(
        item.drift_kind
        in {
            N02DriftKind.STABLE_CONTINUATION,
            N02DriftKind.BOUNDED_REVISION,
            N02DriftKind.GRADUAL_SHIFT,
            N02DriftKind.CONTEXT_SPLIT_DETECTED,
            N02DriftKind.COMMITMENT_EROSION,
            N02DriftKind.CAPABILITY_REVISION_DRIFT,
            N02DriftKind.SELF_BINDING_DRIFT,
        }
        for item in entries
    )
    consistency_consumer_ready = all(
        item.drift_kind not in {N02DriftKind.CONTRADICTION_DRIVEN_FRACTURE}
        for item in entries
    )
    n02_consumer_ready = bool(
        reflection_consumer_ready
        and unresolved_count == 0
        and no_clean_count == 0
    )
    if not n02_consumer_ready:
        required_restrictions.append("n02_consumer_not_ready")
        reason_codes.append("consumer_not_ready")

    telemetry = N02Telemetry(
        baseline_count=len(input_bundle.baseline_references),
        current_reference_count=len(input_bundle.current_references),
        substrate_change_count=len(input_bundle.substrate_changes),
        drift_entry_count=len(entries),
        stable_continuation_count=stable_count,
        bounded_revision_count=bounded_count,
        reflection_needed_count=reflection_needed_count,
        unresolved_identity_tension_count=unresolved_count,
        context_split_count=context_split_count,
        no_clean_drift_count=no_clean_count,
        baseline_uncertain_count=baseline_uncertain_count,
        overreflection_guard_count=overreflection_guard_count,
        text_diff_only_blocked_count=text_diff_only_blocked_count,
        substrate_ablation_or_missing_count=substrate_ablation_or_missing_count,
        downstream_caution_count=downstream_caution_count,
        n02_consumer_ready=n02_consumer_ready,
    )
    gate = N02GateDecision(
        n02_consumer_ready=n02_consumer_ready,
        reflection_consumer_ready=reflection_consumer_ready,
        consistency_consumer_ready=consistency_consumer_ready,
        reflection_needed_count=reflection_needed_count,
        unresolved_identity_tension_count=unresolved_count,
        context_split_count=context_split_count,
        no_clean_drift_count=no_clean_count,
        baseline_uncertain_count=baseline_uncertain_count,
        overreflection_guard_count=overreflection_guard_count,
        text_diff_only_blocked_count=text_diff_only_blocked_count,
        substrate_ablation_or_missing_count=substrate_ablation_or_missing_count,
        downstream_caution_count=downstream_caution_count,
        required_restrictions=tuple(dict.fromkeys(required_restrictions)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        reason="n02 gate preserves bounded drift reflection discipline without commitment rewriting",
    )
    ledger = N02DriftLedger(
        ledger_id=f"n02:{tick_id}:{tick_index}:ledger",
        entries=tuple(entries),
        baseline_refs=input_bundle.baseline_references,
        current_refs=input_bundle.current_references,
        substrate_changes=input_bundle.substrate_changes,
        no_claim_markers=tuple(dict.fromkeys(no_claim_markers)),
        telemetry_summary=(
            f"stable:{stable_count}",
            f"bounded:{bounded_count}",
            f"reflection_needed:{reflection_needed_count}",
            f"unresolved:{unresolved_count}",
            f"context_split:{context_split_count}",
            f"no_clean:{no_clean_count}",
        ),
        provenance=tuple(dict.fromkeys(input_bundle.source_lineage)),
    )
    return N02Result(
        bundle_id=input_bundle.bundle_id,
        drift_entries=tuple(entries),
        ledger=ledger,
        telemetry=telemetry,
        gate=gate,
        scope_marker=N02ScopeMarker(
            scope="frontier_hosted_n02_identity_drift_reflection_slice",
            frontier_only=True,
            narrow_slice_only=True,
            identity_drift_reflection_registry_only=True,
            no_metaphysical_identity_claim=True,
            no_autobiographical_relevance_claim=True,
            no_memory_lifecycle_claim=True,
            no_user_model_claim=True,
            no_commitment_rewrite_claim=True,
            reason=(
                "n02 emits typed identity-drift reflection packets from explicit baseline/current/substrate input "
                "without rewriting commitments or claiming full identity/autobiographical systems"
            ),
        ),
        reason="n02 produced typed identity drift reflection result",
    )


def _evaluate_reference(
    *,
    tick_id: str,
    tick_index: int,
    index: int,
    baseline: N02BaselineReference | None,
    current: N02CurrentIdentityEvidence,
    region_changes: tuple[N02IdentitySubstrateChange, ...],
    region_history: tuple[N02CommitmentHistoryEvent, ...],
    source_lineage: tuple[str, ...],
) -> N02IdentityDriftEntry:
    reason_codes: list[str] = []
    caution: list[str] = []
    drift_kind = N02DriftKind.NO_CLEAN_DRIFT_CLAIM
    reflection_need = N02ReflectionNeedLevel.MODERATE
    continuity_preserved = False
    context_split_scope: str | None = None
    revision_pressure = "low"
    conflict_status = N02ConflictStatus.NO_CONFLICT

    magnitudes = [max(0.0, min(1.0, item.magnitude_hint)) for item in region_changes]
    drift_magnitude = round(max(magnitudes) if magnitudes else 0.0, 4)

    if baseline is None or baseline.validity_status is not N02BaselineValidityStatus.VALID:
        reason_codes.append("baseline_uncertain")
        if baseline is None:
            reason_codes.append("baseline_missing")
        else:
            reason_codes.append(f"baseline_status:{baseline.validity_status.value}")
        caution.append("require_baseline_revalidation")
    elif not region_changes:
        drift_kind = N02DriftKind.STABLE_CONTINUATION
        reflection_need = N02ReflectionNeedLevel.LOW
        continuity_preserved = True
        reason_codes.append("stable_alignment")
    else:
        kinds = {item.change_kind for item in region_changes}
        if kinds == {N02SubstrateChangeKind.TEXTUAL_REPHRASE_ONLY}:
            drift_kind = N02DriftKind.NO_CLEAN_DRIFT_CLAIM
            reflection_need = N02ReflectionNeedLevel.NONE
            continuity_preserved = True
            reason_codes.extend(("text_diff_only_not_identity_drift", "overreflection_guard_applied"))
            caution.append("text_diff_blocked")
        elif (
            kinds == {N02SubstrateChangeKind.SELF_BINDING_NOISY_FLUCTUATION}
            and drift_magnitude < 0.6
        ):
            drift_kind = N02DriftKind.NO_CLEAN_DRIFT_CLAIM
            reflection_need = N02ReflectionNeedLevel.LOW
            continuity_preserved = True
            reason_codes.extend(("noisy_self_binding_fluctuation_only", "overreflection_guard_applied"))
            caution.append("require_additional_self_binding_evidence")
        elif N02SubstrateChangeKind.CONTEXT_SPLIT_SIGNAL in kinds:
            drift_kind = N02DriftKind.CONTEXT_SPLIT_DETECTED
            reflection_need = N02ReflectionNeedLevel.HIGH
            continuity_preserved = True
            context_split_scope = current.context_scope
            reason_codes.append("context_split_detected")
            caution.append("must_not_flatten_context_split_to_global_rupture")
        elif N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION in kinds:
            contradiction_hits = sum(
                1 for item in region_changes if item.change_kind is N02SubstrateChangeKind.CONTRADICTION_ACCUMULATION
            )
            conflict_status = N02ConflictStatus.UNRESOLVED
            if contradiction_hits >= 2 or drift_magnitude >= 0.8:
                drift_kind = N02DriftKind.CONTRADICTION_DRIVEN_FRACTURE
                reflection_need = N02ReflectionNeedLevel.HIGH
                revision_pressure = "high"
                continuity_preserved = False
                reason_codes.append("contradiction_driven_fracture")
            else:
                drift_kind = N02DriftKind.UNRESOLVED_IDENTITY_TENSION
                reflection_need = N02ReflectionNeedLevel.HIGH
                revision_pressure = "high"
                continuity_preserved = False
                reason_codes.append("unresolved_identity_tension")
            caution.append("must_surface_contradiction_before_reuse")
        elif N02SubstrateChangeKind.SELF_BINDING_CORE_SHIFT in kinds and drift_magnitude >= 0.7:
            drift_kind = N02DriftKind.SELF_BINDING_DRIFT
            reflection_need = N02ReflectionNeedLevel.HIGH
            continuity_preserved = False
            revision_pressure = "high"
            reason_codes.append("self_binding_core_shift")
            caution.append("self_binding_requires_revalidation")
        elif N02SubstrateChangeKind.ABRUPT_INCOMPATIBLE_REPLACEMENT in kinds and drift_magnitude >= 0.75:
            broad_support = sum(1 for item in region_changes if item.confidence >= 0.7) >= 2
            if broad_support:
                drift_kind = N02DriftKind.ABRUPT_REORIENTATION
                reflection_need = N02ReflectionNeedLevel.HIGH
                continuity_preserved = False
                revision_pressure = "high"
                reason_codes.append("abrupt_reorientation_with_broad_support")
                caution.append("require_revision_protocol")
            else:
                drift_kind = N02DriftKind.BOUNDED_REVISION
                reflection_need = N02ReflectionNeedLevel.MODERATE
                continuity_preserved = True
                reason_codes.append("abrupt_signal_without_broad_support_capped")
        elif N02SubstrateChangeKind.CAPABILITY_CONTOUR_SHIFT in kinds:
            self_related = any(item.self_related for item in region_changes)
            if self_related:
                drift_kind = N02DriftKind.CAPABILITY_REVISION_DRIFT
                reflection_need = N02ReflectionNeedLevel.MODERATE
                continuity_preserved = True
                reason_codes.append("capability_contour_shift_self_related")
                caution.append("capability_revision_requires_scope_bound")
            else:
                drift_kind = N02DriftKind.BOUNDED_REVISION
                reflection_need = N02ReflectionNeedLevel.LOW
                continuity_preserved = True
                reason_codes.extend(("tool_update_not_identity_drift", "overreflection_guard_applied"))
        elif N02SubstrateChangeKind.COMMITMENT_WEAKENING in kinds:
            weakening_events = sum(
                1
                for item in region_history
                if item.current_status in {"provisional", "contested", "revised", "retired"}
            )
            if weakening_events >= 2:
                drift_kind = N02DriftKind.COMMITMENT_EROSION
                reflection_need = N02ReflectionNeedLevel.HIGH
                continuity_preserved = True
                revision_pressure = "moderate"
                reason_codes.append("commitment_erosion_pattern")
                caution.append("weakened_prior_line_requires_recheck")
            else:
                drift_kind = N02DriftKind.BOUNDED_REVISION
                reflection_need = N02ReflectionNeedLevel.MODERATE
                continuity_preserved = True
                reason_codes.append("single_commitment_weakening_capped")
        elif N02SubstrateChangeKind.REPETITIVE_REVISION in kinds and len(region_changes) >= 2:
            drift_kind = N02DriftKind.GRADUAL_SHIFT
            reflection_need = N02ReflectionNeedLevel.MODERATE
            continuity_preserved = True
            revision_pressure = "moderate"
            reason_codes.append("gradual_shift_accumulation")
        elif N02SubstrateChangeKind.LOCAL_REVISION in kinds or N02SubstrateChangeKind.TOOL_AVAILABILITY_UPDATE_ONLY in kinds:
            drift_kind = N02DriftKind.BOUNDED_REVISION
            reflection_need = N02ReflectionNeedLevel.LOW
            continuity_preserved = True
            reason_codes.append("bounded_local_revision")
            if N02SubstrateChangeKind.TOOL_AVAILABILITY_UPDATE_ONLY in kinds:
                reason_codes.append("overreflection_guard_applied")
        else:
            drift_kind = N02DriftKind.NO_CLEAN_DRIFT_CLAIM
            reflection_need = N02ReflectionNeedLevel.MODERATE
            continuity_preserved = False
            reason_codes.append("substrate_missing_or_ablation")
            caution.append("require_explicit_substrate_basis")

    if not reason_codes:
        reason_codes.append(drift_kind.value)
    confidence = round(
        max(
            0.0,
            min(
                1.0,
                (
                    (baseline.confidence if baseline is not None else 0.45) * 0.4
                    + current.confidence * 0.4
                    + (max((item.confidence for item in region_changes), default=0.5) * 0.2)
                ),
            ),
        ),
        4,
    )
    return N02IdentityDriftEntry(
        drift_id=f"n02:{tick_id}:{tick_index}:drift:{current.current_reference_id}:{index}",
        affected_identity_region=current.observed_region,
        compared_time_scope=current.evidence_window,
        baseline_reference_id=baseline.baseline_id if baseline is not None else None,
        current_reference_id=current.current_reference_id,
        drift_kind=drift_kind,
        drift_magnitude=drift_magnitude,
        continuity_preserved_flag=continuity_preserved,
        conflict_status=conflict_status,
        reflection_need_level=reflection_need,
        revision_pressure=revision_pressure,
        context_split_scope=context_split_scope,
        downstream_caution=tuple(dict.fromkeys(caution)),
        confidence=confidence,
        affected_commitment_ids=current.current_commitment_ids,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        provenance=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *current.provenance,
                    *(baseline.provenance if baseline is not None else ()),
                    current.current_reference_id,
                )
            )
        ),
    )


def _minimal_result(*, bundle_id: str, reason: str, restrictions: tuple[str, ...]) -> N02Result:
    telemetry = N02Telemetry(
        baseline_count=0,
        current_reference_count=0,
        substrate_change_count=0,
        drift_entry_count=0,
        stable_continuation_count=0,
        bounded_revision_count=0,
        reflection_needed_count=0,
        unresolved_identity_tension_count=0,
        context_split_count=0,
        no_clean_drift_count=1,
        baseline_uncertain_count=1,
        overreflection_guard_count=0,
        text_diff_only_blocked_count=0,
        substrate_ablation_or_missing_count=1,
        downstream_caution_count=0,
        n02_consumer_ready=False,
    )
    gate = N02GateDecision(
        n02_consumer_ready=False,
        reflection_consumer_ready=False,
        consistency_consumer_ready=False,
        reflection_needed_count=0,
        unresolved_identity_tension_count=0,
        context_split_count=0,
        no_clean_drift_count=1,
        baseline_uncertain_count=1,
        overreflection_guard_count=0,
        text_diff_only_blocked_count=0,
        substrate_ablation_or_missing_count=1,
        downstream_caution_count=0,
        required_restrictions=restrictions,
        reason_codes=("no_clean_drift_claim",),
        reason=reason,
    )
    ledger = N02DriftLedger(
        ledger_id=f"{bundle_id}:ledger",
        entries=(),
        baseline_refs=(),
        current_refs=(),
        substrate_changes=(),
        no_claim_markers=("n02_no_clean_drift_claim",),
        telemetry_summary=("no_clean:1",),
        provenance=(),
    )
    return N02Result(
        bundle_id=bundle_id,
        drift_entries=(),
        ledger=ledger,
        telemetry=telemetry,
        gate=gate,
        scope_marker=N02ScopeMarker(
            scope="frontier_hosted_n02_identity_drift_reflection_slice",
            frontier_only=True,
            narrow_slice_only=True,
            identity_drift_reflection_registry_only=True,
            no_metaphysical_identity_claim=True,
            no_autobiographical_relevance_claim=True,
            no_memory_lifecycle_claim=True,
            no_user_model_claim=True,
            no_commitment_rewrite_claim=True,
            reason=reason,
        ),
        reason=reason,
    )


def _select_baseline_for_current(
    *,
    baselines: tuple[N02BaselineReference, ...],
    current: N02CurrentIdentityEvidence,
) -> N02BaselineReference | None:
    candidates = tuple(item for item in baselines if item.baseline_kind is current.observed_region)
    if not candidates:
        return None
    ordered = sorted(
        candidates,
        key=lambda item: (
            -_baseline_validity_priority(item.validity_status),
            -(1 if item.time_scope == current.context_scope else 0),
            -item.confidence,
            item.baseline_id,
        ),
    )
    return ordered[0]


def _baseline_validity_priority(status: N02BaselineValidityStatus) -> int:
    if status is N02BaselineValidityStatus.VALID:
        return 5
    if status is N02BaselineValidityStatus.STALE:
        return 3
    if status is N02BaselineValidityStatus.CONTESTED:
        return 2
    if status is N02BaselineValidityStatus.MISSING:
        return 1
    if status is N02BaselineValidityStatus.INVALIDATED:
        return 0
    return -1
