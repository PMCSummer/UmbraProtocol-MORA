from __future__ import annotations

from collections import defaultdict

from substrate.a01_internal_affordance_ontology_cleanup.models import (
    A01AffordanceAliasRecord,
    A01AffordanceClass,
    A01CanonicalAffordanceEntry,
    A01CanonicalOntologyResult,
    A01CanonicalOntologySnapshot,
    A01CanonicalizationStatus,
    A01ContestedCanonicalization,
    A01DownstreamReadinessStatus,
    A01GranularityConflict,
    A01MergeDecision,
    A01MergeRelationType,
    A01OntologyCleanupLedger,
    A01OntologyGateDecision,
    A01ParentChildRelation,
    A01RawAffordanceCandidate,
    A01RawAffordanceCandidateSet,
    A01ScopeMarker,
    A01SplitDecision,
    A01SplitRelationType,
    A01Telemetry,
    A01ValidityStatus,
    A01ValidityStatusRecord,
)
from substrate.s04_interoceptive_self_binding import S04InteroceptiveSelfBindingResult
from substrate.s05_multi_cause_attribution_factorization import S05MultiCauseAttributionResult


def build_a01_internal_affordance_ontology_cleanup(
    *,
    tick_id: str,
    tick_index: int,
    raw_candidate_set: A01RawAffordanceCandidateSet | None,
    c04_execution_mode_claim: str,
    c05_validity_action: str,
    s04_result: S04InteroceptiveSelfBindingResult,
    s05_result: S05MultiCauseAttributionResult,
    source_lineage: tuple[str, ...],
    cleanup_enabled: bool = True,
) -> A01CanonicalOntologyResult:
    if not cleanup_enabled:
        return _build_minimal_result(
            reason="a01 cleanup disabled in ablation context",
            restrictions=("a01_disabled", "canonical_ontology_not_evaluated"),
        )
    if not isinstance(s04_result, S04InteroceptiveSelfBindingResult):
        raise TypeError("a01 requires S04InteroceptiveSelfBindingResult")
    if not isinstance(s05_result, S05MultiCauseAttributionResult):
        raise TypeError("a01 requires S05MultiCauseAttributionResult")

    candidate_set = (
        raw_candidate_set if isinstance(raw_candidate_set, A01RawAffordanceCandidateSet) else None
    )
    if candidate_set is None:
        return _build_minimal_result(
            reason=(
                "a01 frontier slice requires explicit typed raw affordance candidates; "
                "string-only dedup is intentionally forbidden"
            ),
            restrictions=("insufficient_a01_basis", "legacy_label_bypass_forbidden"),
        )
    if not candidate_set.candidates:
        return _build_minimal_result(
            reason="a01 received empty affordance candidate set",
            restrictions=("no_raw_affordance_candidates",),
        )

    contamination_heavy = bool(
        s05_result.state.contamination_present
        or s05_result.state.unexplained_residual >= 0.55
        or s05_result.state.underdetermined_split
    )
    self_core_unstable = bool(s04_result.state.no_stable_self_core_claim)
    validity_revalidation_mode = c05_validity_action in {
        "run_selective_revalidation",
        "run_bounded_revalidation",
        "suspend_until_revalidation_basis",
        "halt_reuse_and_rebuild_scope",
    }

    by_label: dict[str, list[A01RawAffordanceCandidate]] = defaultdict(list)
    for candidate in candidate_set.candidates:
        by_label[_norm_label(candidate.local_label)].append(candidate)

    canonical_entries: list[A01CanonicalAffordanceEntry] = []
    alias_records: list[A01AffordanceAliasRecord] = []
    merge_decisions: list[A01MergeDecision] = []
    split_decisions: list[A01SplitDecision] = []
    contested_records: list[A01ContestedCanonicalization] = []
    granularity_conflicts: list[A01GranularityConflict] = []
    validity_records: list[A01ValidityStatusRecord] = []
    parent_child_relations: list[A01ParentChildRelation] = []

    class_conflict_count = 0
    same_label_diff_precondition_count = 0
    legacy_label_bypass_detected = any(item.legacy_local_label_only for item in candidate_set.candidates)

    for group_index, group in enumerate(by_label.values(), start=1):
        kept = group[0]
        group_candidate_refs = tuple(item.candidate_id for item in group)

        class_conflict = len({item.affordance_class for item in group}) > 1
        if class_conflict:
            class_conflict_count += 1
            contested_records.append(
                A01ContestedCanonicalization(
                    contested_id=f"a01:{tick_id}:{tick_index}:{group_index}:class_conflict",
                    candidate_refs=group_candidate_refs,
                    contested_reason="same label maps to different affordance classes",
                    unresolved=True,
                )
            )
            split_decisions.append(
                A01SplitDecision(
                    decision_id=f"a01:{tick_id}:{tick_index}:{group_index}:split:class",
                    relation_type=A01SplitRelationType.CLASS_BOUNDARY_SPLIT,
                    source_candidate_refs=group_candidate_refs,
                    produced_affordance_ids=tuple(
                        f"a01:{tick_id}:affordance:{item.candidate_id}" for item in group
                    ),
                    reason="same label with class conflict forced split discipline",
                )
            )
            for candidate in group:
                canonical_entries.append(
                    _entry_from_candidate(
                        tick_id=tick_id,
                        candidate=candidate,
                        suffix=candidate.candidate_id,
                        validity=A01ValidityStatus.CONTESTED,
                        canonicalization_status=A01CanonicalizationStatus.CONTESTED,
                        parent_affordance_id=None,
                        child_affordance_ids=(),
                    )
                )
            continue

        same_preconditions = len({_precondition_key(item) for item in group}) == 1
        same_effect_scope = len({_effect_key(item) for item in group}) == 1
        same_controllability = len({item.controllability.controllability_class for item in group}) == 1
        same_channels = len({item.target_channels for item in group}) == 1
        same_outcome_different_control = same_effect_scope and not same_controllability
        same_label_diff_preconditions = not same_preconditions
        granularity_levels = {item.granularity_level for item in group}

        if same_label_diff_preconditions:
            same_label_diff_precondition_count += 1
            split_decisions.append(
                A01SplitDecision(
                    decision_id=f"a01:{tick_id}:{tick_index}:{group_index}:split:precondition",
                    relation_type=A01SplitRelationType.PRECONDITION_SPLIT,
                    source_candidate_refs=group_candidate_refs,
                    produced_affordance_ids=tuple(
                        f"a01:{tick_id}:affordance:{item.candidate_id}" for item in group
                    ),
                    reason="same label with different preconditions must not merge",
                )
            )
            contested_records.append(
                A01ContestedCanonicalization(
                    contested_id=f"a01:{tick_id}:{tick_index}:{group_index}:precondition_conflict",
                    candidate_refs=group_candidate_refs,
                    contested_reason="same label candidates have different precondition profiles",
                    unresolved=True,
                )
            )
            for candidate in group:
                canonical_entries.append(
                    _entry_from_candidate(
                        tick_id=tick_id,
                        candidate=candidate,
                        suffix=candidate.candidate_id,
                        validity=A01ValidityStatus.CONTESTED,
                        canonicalization_status=A01CanonicalizationStatus.CONTESTED,
                        parent_affordance_id=None,
                        child_affordance_ids=(),
                    )
                )
            continue

        if same_outcome_different_control:
            split_decisions.append(
                A01SplitDecision(
                    decision_id=f"a01:{tick_id}:{tick_index}:{group_index}:split:control",
                    relation_type=A01SplitRelationType.CONTROLLABILITY_SPLIT,
                    source_candidate_refs=group_candidate_refs,
                    produced_affordance_ids=tuple(
                        f"a01:{tick_id}:affordance:{item.candidate_id}" for item in group
                    ),
                    reason="same outcome with different controllability remains distinct",
                )
            )
            for candidate in group:
                canonical_entries.append(
                    _entry_from_candidate(
                        tick_id=tick_id,
                        candidate=candidate,
                        suffix=candidate.candidate_id,
                        validity=A01ValidityStatus.NARROWED,
                        canonicalization_status=A01CanonicalizationStatus.CANONICALIZED,
                        parent_affordance_id=None,
                        child_affordance_ids=(),
                    )
                )
            continue

        if len(granularity_levels) > 1 and len(group) > 1:
            granularity_conflicts.append(
                A01GranularityConflict(
                    conflict_id=f"a01:{tick_id}:{tick_index}:{group_index}:granularity_conflict",
                    candidate_refs=group_candidate_refs,
                    parent_child_possible=True,
                    reason="same-label candidates differ in granularity and require parent-child handling",
                )
            )
            ordered = sorted(group, key=lambda item: item.granularity_level)
            parent = ordered[0]
            children = tuple(ordered[1:])
            parent_id = f"a01:{tick_id}:affordance:{parent.candidate_id}"
            child_ids = tuple(f"a01:{tick_id}:affordance:{item.candidate_id}" for item in children)
            canonical_entries.append(
                _entry_from_candidate(
                    tick_id=tick_id,
                    candidate=parent,
                    suffix=parent.candidate_id,
                    validity=A01ValidityStatus.NARROWED,
                    canonicalization_status=A01CanonicalizationStatus.CANONICALIZED,
                    parent_affordance_id=None,
                    child_affordance_ids=child_ids,
                )
            )
            for child in children:
                child_id = f"a01:{tick_id}:affordance:{child.candidate_id}"
                canonical_entries.append(
                    _entry_from_candidate(
                        tick_id=tick_id,
                        candidate=child,
                        suffix=child.candidate_id,
                        validity=A01ValidityStatus.NARROWED,
                        canonicalization_status=A01CanonicalizationStatus.CANONICALIZED,
                        parent_affordance_id=parent_id,
                        child_affordance_ids=(),
                    )
                )
                parent_child_relations.append(
                    A01ParentChildRelation(
                        relation_id=f"a01:{tick_id}:{tick_index}:{group_index}:parent_child:{child.candidate_id}",
                        parent_affordance_id=parent_id,
                        child_affordance_id=child_id,
                        reason="coarse/fine granularity relation preserved",
                    )
                )
            continue

        if len(group) > 1 and same_preconditions and same_effect_scope and same_controllability and same_channels:
            canonical_id = f"a01:{tick_id}:affordance:{kept.candidate_id}"
            merged_refs = tuple(item.candidate_id for item in group[1:])
            merge_decisions.append(
                A01MergeDecision(
                    decision_id=f"a01:{tick_id}:{tick_index}:{group_index}:merge",
                    relation_type=A01MergeRelationType.TRUE_ALIAS,
                    kept_candidate_ref=kept.candidate_id,
                    merged_candidate_refs=merged_refs,
                    canonical_affordance_id=canonical_id,
                    reason="true alias collapse over same class/preconditions/effect/controllability",
                )
            )
            for merged in group[1:]:
                alias_records.append(
                    A01AffordanceAliasRecord(
                        alias_id=f"a01:{tick_id}:{tick_index}:{group_index}:alias:{merged.candidate_id}",
                        canonical_affordance_id=canonical_id,
                        alias_label=merged.local_label,
                        source_candidate_ref=merged.candidate_id,
                        relation_type=A01MergeRelationType.TRUE_ALIAS,
                    )
                )
            canonical_entries.append(
                _entry_from_candidate(
                    tick_id=tick_id,
                    candidate=kept,
                    suffix=kept.candidate_id,
                    validity=A01ValidityStatus.VALID,
                    canonicalization_status=A01CanonicalizationStatus.CANONICALIZED,
                    parent_affordance_id=None,
                    child_affordance_ids=(),
                    merged_aliases=tuple(item.local_label for item in group[1:]),
                    merged_provenance=tuple(item.provenance for item in group[1:]),
                )
            )
            continue

        canonical_entries.append(
            _entry_from_candidate(
                tick_id=tick_id,
                candidate=kept,
                suffix=kept.candidate_id,
                validity=A01ValidityStatus.VALID,
                canonicalization_status=A01CanonicalizationStatus.CANONICALIZED,
                parent_affordance_id=None,
                child_affordance_ids=(),
            )
        )

    adjusted_entries: list[A01CanonicalAffordanceEntry] = []
    for entry in canonical_entries:
        status, codes = _resolve_validity_status(
            entry=entry,
            contamination_heavy=contamination_heavy,
            self_core_unstable=self_core_unstable,
            validity_revalidation_mode=validity_revalidation_mode,
            c04_execution_mode_claim=c04_execution_mode_claim,
        )
        adjusted_entries.append(
            A01CanonicalAffordanceEntry(
                affordance_id=entry.affordance_id,
                canonical_label=entry.canonical_label,
                affordance_class=entry.affordance_class,
                aliases=entry.aliases,
                provenance_refs=entry.provenance_refs,
                validity_status=status,
                canonicalization_status=(
                    A01CanonicalizationStatus.CONTESTED
                    if status is A01ValidityStatus.CONTESTED
                    else A01CanonicalizationStatus.DEPRECATED
                    if status is A01ValidityStatus.DEPRECATED
                    else A01CanonicalizationStatus.UNAVAILABLE
                    if status is A01ValidityStatus.UNAVAILABLE
                    else entry.canonicalization_status
                ),
                preconditions=entry.preconditions,
                effect_scope=entry.effect_scope,
                target_channels=entry.target_channels,
                controllability=entry.controllability,
                observation_expectation=entry.observation_expectation,
                incompatibilities=entry.incompatibilities,
                interruption_semantics=entry.interruption_semantics,
                ownership_relevance=entry.ownership_relevance,
                self_world_relevance=entry.self_world_relevance,
                parent_affordance_id=entry.parent_affordance_id,
                child_affordance_ids=entry.child_affordance_ids,
            )
        )
        validity_records.append(
            A01ValidityStatusRecord(
                affordance_id=entry.affordance_id,
                status=status,
                reason_codes=codes,
            )
        )

    ledger = A01OntologyCleanupLedger(
        ledger_id=f"a01:{tick_id}:ontology_ledger",
        merge_decisions=tuple(merge_decisions),
        split_decisions=tuple(split_decisions),
        alias_records=tuple(alias_records),
        parent_child_relations=tuple(parent_child_relations),
        contested=tuple(contested_records),
        granularity_conflicts=tuple(granularity_conflicts),
        validity_records=tuple(validity_records),
        same_label_diff_precondition_count=same_label_diff_precondition_count,
        class_conflict_count=class_conflict_count,
        legacy_label_bypass_detected=legacy_label_bypass_detected,
        reason="a01 ontology cleanup ledger preserves merge/split/contested decisions as first-class artifacts",
    )
    snapshot = A01CanonicalOntologySnapshot(
        snapshot_id=f"a01:{tick_id}:canonical_snapshot",
        canonical_entries=tuple(adjusted_entries),
        ledger=ledger,
        reason="a01 canonical ontology snapshot for frontier slice",
    )
    gate = _build_gate(snapshot)
    telemetry = _build_telemetry(
        snapshot=snapshot,
        gate=gate,
        raw_candidate_count=len(candidate_set.candidates),
    )
    scope = A01ScopeMarker(
        scope="frontier_hosted_a01_ontology_cleanup_slice",
        frontier_only=True,
        narrow_slice_only=True,
        ontology_cleanup_not_planner_selection=True,
        no_hidden_planner_selection_authority=True,
        no_map_wide_migration_claim=True,
        no_world_ontology_completeness_claim=True,
        no_affordance_discovery_claim=True,
        reason="a01 canonicalizes typed affordance candidates for narrow frontier slice only",
    )
    return A01CanonicalOntologyResult(
        ontology_snapshot=snapshot,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason="a01 produced canonical affordance ontology with contested/deprecated pathways",
    )


def _build_gate(snapshot: A01CanonicalOntologySnapshot) -> A01OntologyGateDecision:
    entries = snapshot.canonical_entries
    canonical_ready = bool(entries)
    contested_ready = bool(snapshot.ledger.contested)
    deprecated_ready = any(
        item.validity_status in {A01ValidityStatus.DEPRECATED, A01ValidityStatus.NARROWED, A01ValidityStatus.UNAVAILABLE}
        for item in entries
    )
    restrictions: list[str] = []
    status = A01DownstreamReadinessStatus.READY
    if not canonical_ready:
        restrictions.append("a01_canonical_affordance_consumer_not_ready")
        status = A01DownstreamReadinessStatus.BLOCKED
    if snapshot.ledger.legacy_label_bypass_detected:
        restrictions.append("a01_legacy_label_bypass_forbidden")
        if status is A01DownstreamReadinessStatus.READY:
            status = A01DownstreamReadinessStatus.DEGRADED
    if snapshot.ledger.class_conflict_count > 0 or snapshot.ledger.same_label_diff_precondition_count > 0:
        restrictions.append("a01_contested_canonicalization_present")
        if status is A01DownstreamReadinessStatus.READY:
            status = A01DownstreamReadinessStatus.DEGRADED
    if any(
        entry.validity_status in {A01ValidityStatus.DEPRECATED, A01ValidityStatus.UNAVAILABLE}
        for entry in entries
    ):
        restrictions.append("a01_deprecated_affordance_present")
        if status is A01DownstreamReadinessStatus.READY:
            status = A01DownstreamReadinessStatus.DEGRADED
    return A01OntologyGateDecision(
        canonical_affordance_consumer_ready=canonical_ready,
        contested_affordance_consumer_ready=contested_ready,
        deprecated_affordance_consumer_ready=deprecated_ready,
        downstream_readiness_status=status,
        restrictions=tuple(dict.fromkeys(restrictions)),
        reason="a01 gate exposes canonical/contested/deprecated consumer readiness",
    )


def _build_telemetry(
    *,
    snapshot: A01CanonicalOntologySnapshot,
    gate: A01OntologyGateDecision,
    raw_candidate_count: int,
) -> A01Telemetry:
    entries = snapshot.canonical_entries
    ledger = snapshot.ledger
    return A01Telemetry(
        raw_candidate_count=raw_candidate_count,
        canonical_entry_count=len(entries),
        merged_alias_group_count=len(ledger.merge_decisions),
        split_decision_count=len(ledger.split_decisions),
        contested_entry_count=len(ledger.contested),
        deprecated_entry_count=sum(
            int(
                item.validity_status
                in {A01ValidityStatus.DEPRECATED, A01ValidityStatus.UNAVAILABLE}
            )
            for item in entries
        ),
        parent_child_relation_count=len(ledger.parent_child_relations),
        same_label_diff_precondition_count=ledger.same_label_diff_precondition_count,
        class_conflict_count=ledger.class_conflict_count,
        legacy_label_bypass_detected=ledger.legacy_label_bypass_detected,
        downstream_consumer_ready=gate.canonical_affordance_consumer_ready,
    )


def _entry_from_candidate(
    *,
    tick_id: str,
    candidate: A01RawAffordanceCandidate,
    suffix: str,
    validity: A01ValidityStatus,
    canonicalization_status: A01CanonicalizationStatus,
    parent_affordance_id: str | None,
    child_affordance_ids: tuple[str, ...],
    merged_aliases: tuple[str, ...] = (),
    merged_provenance: tuple[str, ...] = (),
) -> A01CanonicalAffordanceEntry:
    affordance_id = candidate.canonical_id_hint or f"a01:{tick_id}:affordance:{suffix}"
    alias_labels = tuple(dict.fromkeys((*candidate.aliases, *merged_aliases)))
    provenance_refs = tuple(dict.fromkeys((candidate.provenance, *merged_provenance)))
    return A01CanonicalAffordanceEntry(
        affordance_id=affordance_id,
        canonical_label=_norm_label(candidate.local_label),
        affordance_class=candidate.affordance_class,
        aliases=alias_labels,
        provenance_refs=provenance_refs,
        validity_status=validity,
        canonicalization_status=canonicalization_status,
        preconditions=candidate.preconditions,
        effect_scope=candidate.effect_scope,
        target_channels=candidate.target_channels,
        controllability=candidate.controllability,
        observation_expectation=candidate.observation_expectation,
        incompatibilities=candidate.incompatibilities,
        interruption_semantics=candidate.interruption_semantics,
        ownership_relevance=candidate.ownership_relevance,
        self_world_relevance=candidate.self_world_relevance,
        parent_affordance_id=parent_affordance_id,
        child_affordance_ids=child_affordance_ids,
    )


def _resolve_validity_status(
    *,
    entry: A01CanonicalAffordanceEntry,
    contamination_heavy: bool,
    self_core_unstable: bool,
    validity_revalidation_mode: bool,
    c04_execution_mode_claim: str,
) -> tuple[A01ValidityStatus, tuple[str, ...]]:
    reason_codes: list[str] = []
    status = entry.validity_status

    if any("disabled_effector" in req for req in entry.preconditions.requirements):
        reason_codes.append("disabled_effector")
        status = A01ValidityStatus.UNAVAILABLE
    if any("invalid_assumption" in req for req in entry.preconditions.requirements):
        reason_codes.append("invalid_assumption")
        if status is not A01ValidityStatus.UNAVAILABLE:
            status = A01ValidityStatus.DEPRECATED
    if validity_revalidation_mode:
        reason_codes.append("c05_revalidation_mode")
        if status is A01ValidityStatus.VALID:
            status = A01ValidityStatus.NARROWED
    if contamination_heavy and entry.controllability.controllability_class.value in {
        "self_controlled",
        "shared_controlled",
    }:
        reason_codes.append("s05_contaminated_controllability")
        status = A01ValidityStatus.CONTESTED
    if self_core_unstable and entry.ownership_relevance.value in {
        "self_relevant",
        "mixed_relevant",
    }:
        reason_codes.append("s04_no_stable_self_core")
        status = A01ValidityStatus.CONTESTED
    if c04_execution_mode_claim in {"halt_execution", "hold_safe_idle"} and entry.affordance_class in {
        A01AffordanceClass.WORLD_DIRECTED_ACTION,
        A01AffordanceClass.COMMUNICATION_OUTPUT,
    }:
        reason_codes.append("c04_mode_constrains_world_action")
        if status is A01ValidityStatus.VALID:
            status = A01ValidityStatus.NARROWED
    if status is A01ValidityStatus.VALID:
        reason_codes.append("validity_ok")
    return status, tuple(dict.fromkeys(reason_codes))


def _build_minimal_result(
    *, reason: str, restrictions: tuple[str, ...]
) -> A01CanonicalOntologyResult:
    ledger = A01OntologyCleanupLedger(
        ledger_id="a01:minimal:ledger",
        merge_decisions=(),
        split_decisions=(),
        alias_records=(),
        parent_child_relations=(),
        contested=(),
        granularity_conflicts=(),
        validity_records=(),
        same_label_diff_precondition_count=0,
        class_conflict_count=0,
        legacy_label_bypass_detected=False,
        reason=reason,
    )
    snapshot = A01CanonicalOntologySnapshot(
        snapshot_id="a01:minimal:snapshot",
        canonical_entries=(),
        ledger=ledger,
        reason=reason,
    )
    gate = A01OntologyGateDecision(
        canonical_affordance_consumer_ready=False,
        contested_affordance_consumer_ready=False,
        deprecated_affordance_consumer_ready=False,
        downstream_readiness_status=A01DownstreamReadinessStatus.BLOCKED,
        restrictions=restrictions,
        reason=reason,
    )
    telemetry = A01Telemetry(
        raw_candidate_count=0,
        canonical_entry_count=0,
        merged_alias_group_count=0,
        split_decision_count=0,
        contested_entry_count=0,
        deprecated_entry_count=0,
        parent_child_relation_count=0,
        same_label_diff_precondition_count=0,
        class_conflict_count=0,
        legacy_label_bypass_detected=False,
        downstream_consumer_ready=False,
    )
    scope = A01ScopeMarker(
        scope="frontier_hosted_a01_ontology_cleanup_slice",
        frontier_only=True,
        narrow_slice_only=True,
        ontology_cleanup_not_planner_selection=True,
        no_hidden_planner_selection_authority=True,
        no_map_wide_migration_claim=True,
        no_world_ontology_completeness_claim=True,
        no_affordance_discovery_claim=True,
        reason="a01 minimal fallback scope",
    )
    return A01CanonicalOntologyResult(
        ontology_snapshot=snapshot,
        gate=gate,
        scope_marker=scope,
        telemetry=telemetry,
        reason=reason,
    )


def _norm_label(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _precondition_key(candidate: A01RawAffordanceCandidate) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(sorted(candidate.preconditions.requirements)),
        tuple(sorted(candidate.preconditions.temporal_constraints)),
    )


def _effect_key(candidate: A01RawAffordanceCandidate) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (
        tuple(sorted(candidate.effect_scope.primary_outcomes)),
        tuple(sorted(candidate.effect_scope.side_effect_channels)),
    )
