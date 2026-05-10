from __future__ import annotations

from dataclasses import dataclass

from substrate.n02_identity_drift_reflection import (
    N02BaselineReference,
    N02BaselineValidityStatus,
    N02CommitmentHistoryEvent,
    N02CurrentIdentityEvidence,
    N02IdentityRegionKind,
    N02IdentitySubstrateChange,
    N02InputBundle,
    N02Result,
    N02SubstrateChangeKind,
    build_n02_identity_drift_reflection,
)


@dataclass(frozen=True, slots=True)
class N02HarnessCase:
    case_id: str
    input_bundle: N02InputBundle | None
    reflection_enabled: bool = True


@dataclass(frozen=True, slots=True)
class N02HarnessRun:
    n02_result: N02Result


def n02_baseline(
    *,
    baseline_id: str,
    baseline_kind: N02IdentityRegionKind = N02IdentityRegionKind.SELF_DESCRIPTION,
    time_scope: str = "context:analysis",
    source_commitment_ids: tuple[str, ...] = ("commitment:baseline",),
    source_region_ids: tuple[str, ...] = ("region:self",),
    validity_status: N02BaselineValidityStatus = N02BaselineValidityStatus.VALID,
    confidence: float = 0.85,
    provenance: tuple[str, ...] = ("tests.n02.baseline",),
) -> N02BaselineReference:
    return N02BaselineReference(
        baseline_id=baseline_id,
        baseline_kind=baseline_kind,
        time_scope=time_scope,
        source_commitment_ids=source_commitment_ids,
        source_region_ids=source_region_ids,
        validity_status=validity_status,
        confidence=confidence,
        provenance=provenance,
    )


def n02_current(
    *,
    current_reference_id: str,
    observed_region: N02IdentityRegionKind = N02IdentityRegionKind.SELF_DESCRIPTION,
    current_commitment_ids: tuple[str, ...] = ("commitment:current",),
    current_self_binding_refs: tuple[str, ...] = (),
    capability_or_affordance_refs: tuple[str, ...] = (),
    context_scope: str = "context:analysis",
    evidence_window: str = "window:now",
    confidence: float = 0.82,
    provenance: tuple[str, ...] = ("tests.n02.current",),
) -> N02CurrentIdentityEvidence:
    return N02CurrentIdentityEvidence(
        current_reference_id=current_reference_id,
        observed_region=observed_region,
        current_commitment_ids=current_commitment_ids,
        current_self_binding_refs=current_self_binding_refs,
        capability_or_affordance_refs=capability_or_affordance_refs,
        context_scope=context_scope,
        evidence_window=evidence_window,
        confidence=confidence,
        provenance=provenance,
    )


def n02_change(
    *,
    change_id: str,
    region: N02IdentityRegionKind = N02IdentityRegionKind.SELF_DESCRIPTION,
    change_kind: N02SubstrateChangeKind = N02SubstrateChangeKind.LOCAL_REVISION,
    magnitude_hint: float = 0.35,
    affected_commitment_ids: tuple[str, ...] = ("commitment:current",),
    affected_capability_refs: tuple[str, ...] = (),
    affected_self_binding_refs: tuple[str, ...] = (),
    context_scope: str = "context:analysis",
    temporal_pattern: str = "single",
    confidence: float = 0.8,
    self_related: bool = True,
    provenance: tuple[str, ...] = ("tests.n02.change",),
) -> N02IdentitySubstrateChange:
    return N02IdentitySubstrateChange(
        change_id=change_id,
        region=region,
        change_kind=change_kind,
        magnitude_hint=magnitude_hint,
        affected_commitment_ids=affected_commitment_ids,
        affected_capability_refs=affected_capability_refs,
        affected_self_binding_refs=affected_self_binding_refs,
        context_scope=context_scope,
        temporal_pattern=temporal_pattern,
        confidence=confidence,
        self_related=self_related,
        provenance=provenance,
    )


def n02_history(
    *,
    event_id: str,
    commitment_id: str = "commitment:current",
    region: N02IdentityRegionKind = N02IdentityRegionKind.SELF_DESCRIPTION,
    event_kind: str = "status_change",
    previous_status: str = "confirmed",
    current_status: str = "provisional",
    context_scope: str = "context:analysis",
    confidence: float = 0.8,
    provenance: tuple[str, ...] = ("tests.n02.history",),
) -> N02CommitmentHistoryEvent:
    return N02CommitmentHistoryEvent(
        event_id=event_id,
        commitment_id=commitment_id,
        region=region,
        event_kind=event_kind,
        previous_status=previous_status,
        current_status=current_status,
        context_scope=context_scope,
        confidence=confidence,
        provenance=provenance,
    )


def n02_bundle(
    *,
    bundle_id: str,
    baselines: tuple[N02BaselineReference, ...],
    currents: tuple[N02CurrentIdentityEvidence, ...],
    changes: tuple[N02IdentitySubstrateChange, ...] = (),
    history: tuple[N02CommitmentHistoryEvent, ...] = (),
    source_lineage: tuple[str, ...] = (),
    reason: str = "tests.n02 bundle",
) -> N02InputBundle:
    return N02InputBundle(
        bundle_id=bundle_id,
        baseline_references=baselines,
        current_references=currents,
        substrate_changes=changes,
        commitment_history=history,
        source_lineage=source_lineage,
        reason=reason,
    )


def build_n02_harness_case(case: N02HarnessCase) -> N02HarnessRun:
    result = build_n02_identity_drift_reflection(
        tick_id=f"tests.n02:{case.case_id}",
        tick_index=1,
        input_bundle=case.input_bundle,
        reflection_enabled=case.reflection_enabled,
    )
    return N02HarnessRun(n02_result=result)
