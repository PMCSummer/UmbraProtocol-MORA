from __future__ import annotations

from dataclasses import dataclass

from substrate.w02_regularity_extraction import (
    W02InputBundle,
    W02PresenceMode,
    W02RegularityCandidateType,
    W02ResultBundle,
    W02TraceRef,
    build_w02_regularity_extraction,
)


@dataclass(frozen=True, slots=True)
class W02HarnessCase:
    case_id: str
    input_bundle: W02InputBundle | None
    enforcement_enabled: bool = True


@dataclass(frozen=True, slots=True)
class W02HarnessRun:
    w02_result: W02ResultBundle


def w02_trace(
    *,
    trace_id: str,
    sequence_index: int,
    entity_id: str = "entity:a",
    source_authority: str = "trusted_world_provider",
    presence_mode: W02PresenceMode = W02PresenceMode.PRESENT,
    admission_state: str = "admitted",
    confidence_band: str = "high",
    provenance_ref: tuple[str, ...] = ("tests.w02.trace",),
    action_ref: str | None = "action:a",
    effect_ref: str | None = "effect:a",
    structural_signature: str | None = "shape:cube",
    kind_label: str | None = "kind:block",
    role_label: str | None = "role:anchor",
    provider_label: str | None = "provider:a",
    contradiction_markers: tuple[str, ...] = (),
    is_duplicate_packet: bool = False,
    provider_bias_marker: bool = False,
    text_artifact_marker: bool = False,
    revoked: bool = False,
    candidate_type: W02RegularityCandidateType = W02RegularityCandidateType.INSTANCE,
) -> W02TraceRef:
    return W02TraceRef(
        trace_id=trace_id,
        sequence_index=sequence_index,
        entity_id=entity_id,
        source_authority=source_authority,
        presence_mode=presence_mode,
        admission_state=admission_state,
        confidence_band=confidence_band,
        provenance_ref=provenance_ref,
        action_ref=action_ref,
        effect_ref=effect_ref,
        structural_signature=structural_signature,
        kind_label=kind_label,
        role_label=role_label,
        provider_label=provider_label,
        contradiction_markers=contradiction_markers,
        is_duplicate_packet=is_duplicate_packet,
        provider_bias_marker=provider_bias_marker,
        text_artifact_marker=text_artifact_marker,
        revoked=revoked,
        candidate_type=candidate_type,
    )


def w02_bundle(
    *,
    bundle_id: str,
    traces: tuple[W02TraceRef, ...],
    source_lineage: tuple[str, ...] = (),
    reason: str = "tests.w02 bundle",
) -> W02InputBundle:
    return W02InputBundle(
        bundle_id=bundle_id,
        traces=traces,
        source_lineage=source_lineage,
        reason=reason,
    )


def build_w02_harness_case(case: W02HarnessCase) -> W02HarnessRun:
    result = build_w02_regularity_extraction(
        tick_id=f"tests.w02:{case.case_id}",
        tick_index=1,
        input_bundle=case.input_bundle,
        enforcement_enabled=case.enforcement_enabled,
    )
    return W02HarnessRun(w02_result=result)
