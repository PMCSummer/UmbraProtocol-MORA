from __future__ import annotations

from substrate.s01_efference_copy import S01EfferenceCopyResult
from substrate.s02_prediction_boundary import (
    S02BoundaryStatus,
    S02PredictionBoundaryResult,
)
from substrate.s03_ownership_weighted_learning import (
    S03OwnershipWeightedLearningResult,
)
from substrate.s04_interoceptive_self_binding.models import (
    S04BindingEntry,
    S04BindingStatus,
    S04CandidateClass,
    S04CandidateSignal,
    S04InteroceptiveSelfBindingResult,
    S04InteroceptiveSelfBindingState,
    S04ScopeMarker,
    S04SelfBindingGateDecision,
    S04Telemetry,
)


def build_s04_interoceptive_self_binding(
    *,
    tick_id: str,
    tick_index: int,
    s01_result: S01EfferenceCopyResult,
    s02_result: S02PredictionBoundaryResult,
    s03_result: S03OwnershipWeightedLearningResult,
    regulation_pressure_level: float,
    regulation_dominant_axis: str,
    c05_revalidation_required: bool,
    context_shift_detected: bool,
    candidate_signals: tuple[S04CandidateSignal, ...] = (),
    observed_internal_channels: tuple[str, ...] = (),
    prior_state: S04InteroceptiveSelfBindingState | None = None,
    source_lineage: tuple[str, ...] = (),
    binding_enabled: bool = True,
) -> S04InteroceptiveSelfBindingResult:
    if not tick_id:
        raise ValueError("tick_id is required")
    if tick_index < 1:
        raise ValueError("tick_index must be >= 1")
    if not isinstance(s01_result, S01EfferenceCopyResult):
        raise TypeError("s01_result must be S01EfferenceCopyResult")
    if not isinstance(s02_result, S02PredictionBoundaryResult):
        raise TypeError("s02_result must be S02PredictionBoundaryResult")
    if not isinstance(s03_result, S03OwnershipWeightedLearningResult):
        raise TypeError("s03_result must be S03OwnershipWeightedLearningResult")

    upstream = _derive_upstream_candidate_signals(
        s01_result=s01_result,
        s02_result=s02_result,
        s03_result=s03_result,
        regulation_pressure_level=regulation_pressure_level,
        regulation_dominant_axis=regulation_dominant_axis,
    )
    observed = _derive_observed_channel_signals(observed_internal_channels)
    merged = _merge_candidate_signals((*upstream, *candidate_signals, *observed))
    candidate_ids = tuple(item.channel_id for item in merged)

    excluded_channels = tuple(
        item.channel_id
        for item in merged
        if item.candidate_class
        in {
            S04CandidateClass.GENERIC_INTERNAL_BOOKKEEPING,
            S04CandidateClass.TRANSIENT_CONTEXT_BOUND,
        }
    )
    privileged = tuple(
        item
        for item in merged
        if item.candidate_class
        in {
            S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
            S04CandidateClass.MIXED_INTERNAL_EXTERNAL,
        }
    )

    if not binding_enabled:
        return _build_disabled_result(
            tick_id=tick_id,
            tick_index=tick_index,
            candidate_channels=candidate_ids,
            excluded_channels=excluded_channels,
            source_lineage=source_lineage,
        )

    prior_map = _prior_entries_by_channel(prior_state)
    entries: list[S04BindingEntry] = []
    stale_drop_count = 0
    rebinding_event = False
    strongest = 0.0
    for signal in privileged:
        prior_entry = prior_map.get(signal.channel_id)
        derived = _derive_support_vector(
            signal=signal,
            s01_result=s01_result,
            s02_result=s02_result,
            s03_result=s03_result,
            regulation_pressure_level=regulation_pressure_level,
            regulation_dominant_axis=regulation_dominant_axis,
            c05_revalidation_required=c05_revalidation_required,
            context_shift_detected=context_shift_detected,
            prior_entry=prior_entry,
        )
        status = _classify_binding_status(
            candidate_class=signal.candidate_class,
            score=derived["binding_strength"],
            regulatory=derived["regulatory_support"],
            continuity=derived["continuity_support"],
            boundary=derived["boundary_support"],
            ownership=derived["ownership_support"],
            coupling=derived["coupling_support"],
            contamination=derived["contamination_level"],
            temporal_validity=derived["temporal_validity"],
        )
        persistence = 1
        if prior_entry is not None:
            persistence = prior_entry.temporal_persistence + 1
            if status in {
                S04BindingStatus.UNBOUND_INTERNAL,
                S04BindingStatus.CONTESTED_BINDING,
            } and prior_entry.binding_status in {
                S04BindingStatus.STRONGLY_SELF_BOUND,
                S04BindingStatus.WEAKLY_SELF_BOUND,
                S04BindingStatus.PROVISIONALLY_BOUND,
            }:
                stale_drop_count += 1
            if status in {
                S04BindingStatus.STRONGLY_SELF_BOUND,
                S04BindingStatus.WEAKLY_SELF_BOUND,
            } and prior_entry.binding_status in {
                S04BindingStatus.UNBOUND_INTERNAL,
                S04BindingStatus.CONTESTED_BINDING,
                S04BindingStatus.PROVISIONALLY_BOUND,
            }:
                rebinding_event = True
        strongest = max(strongest, derived["binding_strength"])
        entries.append(
            S04BindingEntry(
                binding_entry_id=f"s04-binding:{tick_id}:{tick_index}:{signal.channel_id}",
                channel_or_group_id=signal.channel_id,
                binding_status=status,
                binding_strength=derived["binding_strength"],
                binding_basis=(
                    f"regulatory={derived['regulatory_support']:.3f}",
                    f"continuity={derived['continuity_support']:.3f}",
                    f"boundary={derived['boundary_support']:.3f}",
                    f"ownership={derived['ownership_support']:.3f}",
                    f"coupling={derived['coupling_support']:.3f}",
                    f"temporal_validity={derived['temporal_validity']:.3f}",
                    f"contamination={derived['contamination_level']:.3f}",
                ),
                coupling_support=derived["coupling_support"],
                ownership_support=derived["ownership_support"],
                boundary_support=derived["boundary_support"],
                regulatory_support=derived["regulatory_support"],
                continuity_support=derived["continuity_support"],
                temporal_persistence=persistence,
                contamination_level=derived["contamination_level"],
                current_validity=derived["current_validity"],
                provenance="s04.interoceptive_self_binding.status_assignment",
            )
        )

    current_channels = {entry.channel_or_group_id for entry in entries}
    recently_unbound = _recently_unbound_channels(prior_state, current_channels, entries)
    stale_drop_count += _stale_drops_from_absent_prior(prior_state, current_channels)

    core_bound = tuple(
        entry.channel_or_group_id
        for entry in entries
        if entry.binding_status is S04BindingStatus.STRONGLY_SELF_BOUND
    )
    peripheral = tuple(
        entry.channel_or_group_id
        for entry in entries
        if entry.binding_status
        in {
            S04BindingStatus.WEAKLY_SELF_BOUND,
            S04BindingStatus.PROVISIONALLY_BOUND,
        }
    )
    contested = tuple(
        entry.channel_or_group_id
        for entry in entries
        if entry.binding_status
        in {
            S04BindingStatus.CONTESTED_BINDING,
            S04BindingStatus.MIXED_INTERNAL_EXTERNAL_SIGNAL,
        }
    )
    no_stable_core = len(core_bound) == 0
    if no_stable_core:
        entries.append(
            S04BindingEntry(
                binding_entry_id=f"s04-binding:{tick_id}:{tick_index}:no-stable-core",
                channel_or_group_id="self_core",
                binding_status=S04BindingStatus.NO_STABLE_SELF_CORE_CLAIM,
                binding_strength=0.0,
                binding_basis=("no_strongly_self_bound_channels",),
                coupling_support=0.0,
                ownership_support=0.0,
                boundary_support=0.0,
                regulatory_support=0.0,
                continuity_support=0.0,
                temporal_persistence=1,
                contamination_level=0.0,
                current_validity="bounded_no_core_claim",
                provenance="s04.interoceptive_self_binding.no_stable_core_claim",
            )
        )

    contamination_detected = any(item.contamination_level >= 0.6 for item in entries)
    gate = _build_gate(
        core_bound=core_bound,
        contested=contested,
        no_stable_core=no_stable_core,
    )
    state = S04InteroceptiveSelfBindingState(
        binding_id=f"s04-binding:{tick_id}",
        tick_index=tick_index,
        entries=tuple(entries),
        core_bound_channels=core_bound,
        peripheral_or_weakly_bound_channels=peripheral,
        contested_channels=contested,
        recently_unbound_channels=recently_unbound,
        no_stable_self_core_claim=no_stable_core,
        strongest_binding_strength=round(strongest, 3),
        contamination_detected=contamination_detected,
        rebinding_event=rebinding_event,
        stale_binding_drop_count=stale_drop_count,
        candidate_channels=candidate_ids,
        excluded_channels=excluded_channels,
        source_lineage=tuple(
            dict.fromkeys(
                (
                    *source_lineage,
                    *s01_result.state.source_lineage,
                    *s02_result.state.source_lineage,
                    *s03_result.state.source_lineage,
                )
            )
        ),
        last_update_provenance="s04.interoceptive_self_binding.first_runtime_slice",
    )
    telemetry = S04Telemetry(
        binding_id=state.binding_id,
        tick_index=state.tick_index,
        strong_bound_count=len(state.core_bound_channels),
        weak_bound_count=len(
            [
                item
                for item in state.entries
                if item.binding_status is S04BindingStatus.WEAKLY_SELF_BOUND
            ]
        ),
        provisional_count=len(
            [
                item
                for item in state.entries
                if item.binding_status is S04BindingStatus.PROVISIONALLY_BOUND
            ]
        ),
        contested_count=len(state.contested_channels),
        no_stable_core_claim=state.no_stable_self_core_claim,
        strongest_binding_strength=state.strongest_binding_strength,
        contamination_detected=state.contamination_detected,
        rebinding_event=state.rebinding_event,
        stale_binding_drop_count=state.stale_binding_drop_count,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return S04InteroceptiveSelfBindingResult(
        state=state,
        gate=gate,
        scope_marker=_build_scope_marker(),
        telemetry=telemetry,
        reason="s04 bounded interoceptive self-binding ledger update",
    )


def _build_disabled_result(
    *,
    tick_id: str,
    tick_index: int,
    candidate_channels: tuple[str, ...],
    excluded_channels: tuple[str, ...],
    source_lineage: tuple[str, ...],
) -> S04InteroceptiveSelfBindingResult:
    gate = S04SelfBindingGateDecision(
        core_consumer_ready=False,
        contested_consumer_ready=False,
        no_stable_core_consumer_ready=True,
        restrictions=(
            "s04_binding_ledger_contract_must_be_read",
            "s04_binding_disabled_in_ablation_context",
            "s04_no_stable_core_claim_active",
        ),
        reason="s04 binding disabled; no stable self core claim remains active",
    )
    state = S04InteroceptiveSelfBindingState(
        binding_id=f"s04-binding:{tick_id}",
        tick_index=tick_index,
        entries=(
            S04BindingEntry(
                binding_entry_id=f"s04-binding:{tick_id}:{tick_index}:disabled",
                channel_or_group_id="self_core",
                binding_status=S04BindingStatus.NO_STABLE_SELF_CORE_CLAIM,
                binding_strength=0.0,
                binding_basis=("s04_binding_disabled",),
                coupling_support=0.0,
                ownership_support=0.0,
                boundary_support=0.0,
                regulatory_support=0.0,
                continuity_support=0.0,
                temporal_persistence=1,
                contamination_level=0.0,
                current_validity="disabled",
                provenance="s04.interoceptive_self_binding.disabled",
            ),
        ),
        core_bound_channels=(),
        peripheral_or_weakly_bound_channels=(),
        contested_channels=(),
        recently_unbound_channels=(),
        no_stable_self_core_claim=True,
        strongest_binding_strength=0.0,
        contamination_detected=False,
        rebinding_event=False,
        stale_binding_drop_count=0,
        candidate_channels=candidate_channels,
        excluded_channels=excluded_channels,
        source_lineage=source_lineage,
        last_update_provenance="s04.interoceptive_self_binding.disabled",
    )
    telemetry = S04Telemetry(
        binding_id=state.binding_id,
        tick_index=state.tick_index,
        strong_bound_count=0,
        weak_bound_count=0,
        provisional_count=0,
        contested_count=0,
        no_stable_core_claim=True,
        strongest_binding_strength=0.0,
        contamination_detected=False,
        rebinding_event=False,
        stale_binding_drop_count=0,
        restrictions=gate.restrictions,
        reason=gate.reason,
    )
    return S04InteroceptiveSelfBindingResult(
        state=state,
        gate=gate,
        scope_marker=_build_scope_marker(),
        telemetry=telemetry,
        reason="s04 interoceptive self-binding disabled",
    )


def _derive_upstream_candidate_signals(
    *,
    s01_result: S01EfferenceCopyResult,
    s02_result: S02PredictionBoundaryResult,
    s03_result: S03OwnershipWeightedLearningResult,
    regulation_pressure_level: float,
    regulation_dominant_axis: str,
) -> tuple[S04CandidateSignal, ...]:
    boundary_status = s02_result.state.active_boundary_status
    boundary_support = _boundary_support_from_s02(s02_result)
    ownership_support = _ownership_support_from_s03(s03_result)
    regulatory_support = _clamp(regulation_pressure_level / 100.0)

    signals = [
        S04CandidateSignal(
            channel_id=f"regulation_axis:{regulation_dominant_axis}",
            candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
            regulatory_support_hint=regulatory_support,
            continuity_support_hint=0.45,
            boundary_support_hint=boundary_support,
            ownership_support_hint=max(0.2, ownership_support * 0.8),
            coupling_support_hint=0.42,
            temporal_validity_hint=0.76,
            contamination_hint=0.12,
            source_authority="r04.regulation",
            provenance="s04.upstream.regulation_axis",
        ),
        S04CandidateSignal(
            channel_id="prediction_boundary_interoceptive_channel",
            candidate_class=(
                S04CandidateClass.MIXED_INTERNAL_EXTERNAL
                if boundary_status is S02BoundaryStatus.MIXED_SOURCE_BOUNDARY
                else S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY
            ),
            regulatory_support_hint=0.46,
            continuity_support_hint=0.48,
            boundary_support_hint=boundary_support,
            ownership_support_hint=ownership_support,
            coupling_support_hint=0.4,
            temporal_validity_hint=0.72,
            contamination_hint=(
                0.38
                if boundary_status
                in {
                    S02BoundaryStatus.BOUNDARY_UNCERTAIN,
                    S02BoundaryStatus.NO_CLEAN_SEAM_CLAIM,
                    S02BoundaryStatus.SEAM_INVALIDATED_FOR_CONTEXT,
                }
                else 0.18
            ),
            source_authority="s02.prediction_boundary",
            provenance="s04.upstream.boundary_seam",
        ),
        S04CandidateSignal(
            channel_id="ownership_weighted_update_channel",
            candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
            regulatory_support_hint=0.44,
            continuity_support_hint=0.52,
            boundary_support_hint=boundary_support,
            ownership_support_hint=ownership_support,
            coupling_support_hint=0.46,
            temporal_validity_hint=0.74,
            contamination_hint=(
                0.42 if s03_result.state.requested_revalidation else 0.14
            ),
            source_authority="s03.ownership_weighted_learning",
            provenance="s04.upstream.ownership_weighted_learning",
        ),
    ]
    if s01_result.state.strong_self_attribution_allowed:
        signals.append(
            S04CandidateSignal(
                channel_id="efference_self_delta_channel",
                candidate_class=S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY,
                regulatory_support_hint=0.4,
                continuity_support_hint=0.5,
                boundary_support_hint=boundary_support,
                ownership_support_hint=max(0.25, ownership_support * 0.9),
                coupling_support_hint=0.45,
                temporal_validity_hint=0.7,
                contamination_hint=(
                    0.5 if s01_result.state.comparison_blocked_by_contamination else 0.16
                ),
                source_authority="s01.efference_copy",
                provenance="s04.upstream.efference",
            )
        )
    return tuple(signals)


def _derive_observed_channel_signals(
    observed_internal_channels: tuple[str, ...],
) -> tuple[S04CandidateSignal, ...]:
    signals: list[S04CandidateSignal] = []
    for token in observed_internal_channels:
        channel = str(token or "").strip()
        if not channel:
            continue
        normalized = channel.lower()
        if normalized.startswith("mixed:"):
            signals.append(
                S04CandidateSignal(
                    channel_id=channel,
                    candidate_class=S04CandidateClass.MIXED_INTERNAL_EXTERNAL,
                    regulatory_support_hint=0.26,
                    continuity_support_hint=0.3,
                    boundary_support_hint=0.35,
                    ownership_support_hint=0.3,
                    coupling_support_hint=0.25,
                    temporal_validity_hint=0.6,
                    contamination_hint=0.35,
                    source_authority="s04.observed_internal_channel",
                    provenance="s04.observed.mixed",
                )
            )
            continue
        if _is_generic_bookkeeping_channel(normalized):
            signals.append(
                S04CandidateSignal(
                    channel_id=channel,
                    candidate_class=S04CandidateClass.GENERIC_INTERNAL_BOOKKEEPING,
                    regulatory_support_hint=0.05,
                    continuity_support_hint=0.1,
                    boundary_support_hint=0.05,
                    ownership_support_hint=0.05,
                    coupling_support_hint=0.05,
                    temporal_validity_hint=0.4,
                    contamination_hint=0.0,
                    source_authority="s04.observed_internal_channel",
                    provenance="s04.observed.generic",
                )
            )
            continue
        signals.append(
            S04CandidateSignal(
                channel_id=channel,
                candidate_class=S04CandidateClass.TRANSIENT_CONTEXT_BOUND,
                regulatory_support_hint=0.14,
                continuity_support_hint=0.18,
                boundary_support_hint=0.16,
                ownership_support_hint=0.15,
                coupling_support_hint=0.12,
                temporal_validity_hint=0.38,
                contamination_hint=0.16,
                source_authority="s04.observed_internal_channel",
                provenance="s04.observed.transient",
            )
        )
    return tuple(signals)


def _merge_candidate_signals(
    signals: tuple[S04CandidateSignal, ...],
) -> tuple[S04CandidateSignal, ...]:
    merged: dict[str, S04CandidateSignal] = {}
    for item in signals:
        existing = merged.get(item.channel_id)
        if existing is None:
            merged[item.channel_id] = item
            continue
        merged[item.channel_id] = S04CandidateSignal(
            channel_id=item.channel_id,
            candidate_class=_merge_candidate_class(existing.candidate_class, item.candidate_class),
            regulatory_support_hint=max(existing.regulatory_support_hint, item.regulatory_support_hint),
            continuity_support_hint=max(existing.continuity_support_hint, item.continuity_support_hint),
            boundary_support_hint=max(existing.boundary_support_hint, item.boundary_support_hint),
            ownership_support_hint=max(existing.ownership_support_hint, item.ownership_support_hint),
            coupling_support_hint=max(existing.coupling_support_hint, item.coupling_support_hint),
            temporal_validity_hint=max(existing.temporal_validity_hint, item.temporal_validity_hint),
            contamination_hint=max(existing.contamination_hint, item.contamination_hint),
            source_authority=f"{existing.source_authority}|{item.source_authority}",
            provenance=f"{existing.provenance}|{item.provenance}",
        )
    return tuple(merged.values())


def _merge_candidate_class(
    left: S04CandidateClass,
    right: S04CandidateClass,
) -> S04CandidateClass:
    if S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY in {left, right}:
        return S04CandidateClass.PRIVILEGED_INTEROCEPTIVE_REGULATORY
    if S04CandidateClass.MIXED_INTERNAL_EXTERNAL in {left, right}:
        return S04CandidateClass.MIXED_INTERNAL_EXTERNAL
    if S04CandidateClass.GENERIC_INTERNAL_BOOKKEEPING in {left, right}:
        return S04CandidateClass.GENERIC_INTERNAL_BOOKKEEPING
    return S04CandidateClass.TRANSIENT_CONTEXT_BOUND


def _derive_support_vector(
    *,
    signal: S04CandidateSignal,
    s01_result: S01EfferenceCopyResult,
    s02_result: S02PredictionBoundaryResult,
    s03_result: S03OwnershipWeightedLearningResult,
    regulation_pressure_level: float,
    regulation_dominant_axis: str,
    c05_revalidation_required: bool,
    context_shift_detected: bool,
    prior_entry: S04BindingEntry | None,
) -> dict[str, float | str]:
    boundary_support = _clamp(
        (signal.boundary_support_hint * 0.6)
        + (_boundary_support_from_s02(s02_result) * 0.4)
    )
    ownership_support = _clamp(
        (signal.ownership_support_hint * 0.6)
        + (_ownership_support_from_s03(s03_result) * 0.4)
    )
    regulatory_support = _clamp(
        (signal.regulatory_support_hint * 0.65)
        + (
            _regulatory_support_from_context(
            regulation_pressure_level=regulation_pressure_level,
            regulation_dominant_axis=regulation_dominant_axis,
            channel_id=signal.channel_id,
            )
            * 0.35
        )
    )
    continuity_support = signal.continuity_support_hint
    if prior_entry is not None:
        continuity_support = max(
            continuity_support,
            _clamp(0.3 + (prior_entry.temporal_persistence * 0.08)),
        )
    if context_shift_detected:
        continuity_support = _clamp(continuity_support - 0.22)

    temporal_validity = signal.temporal_validity_hint
    if c05_revalidation_required or s03_result.state.requested_revalidation:
        temporal_validity = _clamp(temporal_validity - 0.28)
    if context_shift_detected:
        temporal_validity = _clamp(temporal_validity - 0.18)

    contamination = signal.contamination_hint
    if s01_result.state.comparison_blocked_by_contamination:
        contamination = max(contamination, 0.62)
    if s02_result.state.no_clean_seam_claim:
        contamination = max(contamination, 0.55)
    if s03_result.state.freeze_or_defer_state.value in {
        "freeze_pending_revalidation",
        "block_due_to_conflict",
    }:
        contamination = max(contamination, 0.58)

    coupling = signal.coupling_support_hint
    if regulatory_support >= 0.5 and boundary_support >= 0.45 and ownership_support >= 0.4:
        coupling = max(coupling, 0.46)
    if prior_entry is not None and prior_entry.binding_status in {
        S04BindingStatus.STRONGLY_SELF_BOUND,
        S04BindingStatus.WEAKLY_SELF_BOUND,
    }:
        coupling = max(coupling, _clamp(prior_entry.coupling_support + 0.05))

    base = (
        (regulatory_support * 0.24)
        + (continuity_support * 0.2)
        + (boundary_support * 0.2)
        + (ownership_support * 0.2)
        + (coupling * 0.16)
    )
    binding_strength = _clamp(base * temporal_validity * (1.0 - min(0.85, contamination * 0.6)))
    current_validity = (
        "stale_or_invalidated"
        if temporal_validity < 0.35 or contamination > 0.72
        else "bounded_valid_for_binding"
    )
    return {
        "boundary_support": round(boundary_support, 3),
        "ownership_support": round(ownership_support, 3),
        "regulatory_support": round(regulatory_support, 3),
        "continuity_support": round(continuity_support, 3),
        "temporal_validity": round(temporal_validity, 3),
        "contamination_level": round(contamination, 3),
        "coupling_support": round(coupling, 3),
        "binding_strength": round(binding_strength, 3),
        "current_validity": current_validity,
    }


def _classify_binding_status(
    *,
    candidate_class: S04CandidateClass,
    score: float,
    regulatory: float,
    continuity: float,
    boundary: float,
    ownership: float,
    coupling: float,
    contamination: float,
    temporal_validity: float,
) -> S04BindingStatus:
    if candidate_class is S04CandidateClass.MIXED_INTERNAL_EXTERNAL and score >= 0.3:
        return S04BindingStatus.MIXED_INTERNAL_EXTERNAL_SIGNAL
    if contamination >= 0.72 or temporal_validity < 0.24:
        return (
            S04BindingStatus.CONTESTED_BINDING
            if score >= 0.25
            else S04BindingStatus.UNBOUND_INTERNAL
        )
    if (
        score >= 0.55
        and regulatory >= 0.6
        and continuity >= 0.55
        and boundary >= 0.52
        and ownership >= 0.52
        and coupling >= 0.45
    ):
        return S04BindingStatus.STRONGLY_SELF_BOUND
    if score >= 0.48 and boundary >= 0.38 and ownership >= 0.36:
        return S04BindingStatus.WEAKLY_SELF_BOUND
    if score >= 0.34 and regulatory >= 0.34 and (boundary >= 0.28 or ownership >= 0.28):
        return S04BindingStatus.PROVISIONALLY_BOUND
    if score >= 0.22:
        return S04BindingStatus.CONTESTED_BINDING
    return S04BindingStatus.UNBOUND_INTERNAL


def _build_gate(
    *,
    core_bound: tuple[str, ...],
    contested: tuple[str, ...],
    no_stable_core: bool,
) -> S04SelfBindingGateDecision:
    restrictions = [
        "s04_binding_ledger_contract_must_be_read",
        "s04_generic_internal_vars_must_not_auto_bind",
        "s04_single_signal_must_not_force_strong_core",
        "s04_stale_or_contaminated_binding_must_weaken",
    ]
    core_ready = len(core_bound) > 0 and not no_stable_core
    contested_ready = len(contested) > 0
    if not core_ready:
        restrictions.append("s04_core_consumer_not_ready")
    if no_stable_core:
        restrictions.append("s04_no_stable_core_claim_active")
    return S04SelfBindingGateDecision(
        core_consumer_ready=core_ready,
        contested_consumer_ready=contested_ready,
        no_stable_core_consumer_ready=no_stable_core,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason=(
            "s04 bound privileged interoceptive channels using convergent regulatory/boundary/ownership/continuity support"
        ),
    )


def _build_scope_marker() -> S04ScopeMarker:
    return S04ScopeMarker(
        scope="rt01_contour_only",
        rt01_contour_only=True,
        s04_first_slice_only=True,
        s05_implemented=False,
        full_self_model_implemented=False,
        repo_wide_adoption=False,
        reason="first bounded s04 slice only; no full self model and no s05 rollout",
    )


def _prior_entries_by_channel(
    prior_state: S04InteroceptiveSelfBindingState | None,
) -> dict[str, S04BindingEntry]:
    if not isinstance(prior_state, S04InteroceptiveSelfBindingState):
        return {}
    return {
        item.channel_or_group_id: item
        for item in prior_state.entries
        if item.channel_or_group_id != "self_core"
    }


def _recently_unbound_channels(
    prior_state: S04InteroceptiveSelfBindingState | None,
    current_channels: set[str],
    entries: list[S04BindingEntry],
) -> tuple[str, ...]:
    if not isinstance(prior_state, S04InteroceptiveSelfBindingState):
        return ()
    current_status = {item.channel_or_group_id: item.binding_status for item in entries}
    recently: list[str] = []
    for item in prior_state.entries:
        if item.channel_or_group_id == "self_core":
            continue
        if item.binding_status not in {
            S04BindingStatus.STRONGLY_SELF_BOUND,
            S04BindingStatus.WEAKLY_SELF_BOUND,
            S04BindingStatus.PROVISIONALLY_BOUND,
        }:
            continue
        if item.channel_or_group_id not in current_channels:
            recently.append(item.channel_or_group_id)
            continue
        if current_status.get(item.channel_or_group_id) in {
            S04BindingStatus.UNBOUND_INTERNAL,
            S04BindingStatus.CONTESTED_BINDING,
            S04BindingStatus.MIXED_INTERNAL_EXTERNAL_SIGNAL,
        }:
            recently.append(item.channel_or_group_id)
    return tuple(dict.fromkeys(recently))


def _stale_drops_from_absent_prior(
    prior_state: S04InteroceptiveSelfBindingState | None,
    current_channels: set[str],
) -> int:
    if not isinstance(prior_state, S04InteroceptiveSelfBindingState):
        return 0
    return len(
        [
            item
            for item in prior_state.entries
            if item.channel_or_group_id != "self_core"
            and item.channel_or_group_id not in current_channels
            and item.binding_status
            in {
                S04BindingStatus.STRONGLY_SELF_BOUND,
                S04BindingStatus.WEAKLY_SELF_BOUND,
                S04BindingStatus.PROVISIONALLY_BOUND,
            }
        ]
    )


def _boundary_support_from_s02(s02_result: S02PredictionBoundaryResult) -> float:
    status = s02_result.state.active_boundary_status
    if status is S02BoundaryStatus.INSIDE_SELF_PREDICTIVE_SEAM:
        return 0.82
    if status is S02BoundaryStatus.CONTROLLABLE_BUT_UNRELIABLE:
        return 0.66
    if status is S02BoundaryStatus.MIXED_SOURCE_BOUNDARY:
        return 0.48
    if status is S02BoundaryStatus.PREDICTABLE_BUT_NOT_SELF_DRIVEN:
        return 0.3
    if status is S02BoundaryStatus.EXTERNALLY_DOMINATED_BOUNDARY:
        return 0.18
    return 0.22


def _ownership_support_from_s03(s03_result: S03OwnershipWeightedLearningResult) -> float:
    packet = s03_result.state.packets[-1]
    support = (packet.self_update_weight * 0.65) + (packet.confidence * 0.35)
    if packet.freeze_or_defer_status.value in {
        "freeze_pending_revalidation",
        "block_due_to_conflict",
    }:
        support = max(0.12, support * 0.45)
    return round(_clamp(support), 3)


def _regulatory_support_from_context(
    *,
    regulation_pressure_level: float,
    regulation_dominant_axis: str,
    channel_id: str,
) -> float:
    support = _clamp(regulation_pressure_level / 100.0)
    dominant = str(regulation_dominant_axis or "").strip().lower()
    channel = str(channel_id or "").strip().lower()
    if dominant and dominant in channel:
        support = max(support, 0.58)
    return round(support, 3)


def _is_generic_bookkeeping_channel(normalized_channel: str) -> bool:
    return (
        normalized_channel.startswith("bookkeeping:")
        or normalized_channel.startswith("cache:")
        or normalized_channel.startswith("impl:")
        or normalized_channel.startswith("generic:")
        or "cache" in normalized_channel
        or "counter" in normalized_channel
        or "buffer" in normalized_channel
    )


def _clamp(value: float, *, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))
