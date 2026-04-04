from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from substrate.grounded_semantic.models import (
    GroundedSemanticBundle,
    GroundedSemanticResult,
    OperatorKind,
    SourceAnchorKind,
)
from substrate.grounded_semantic.policy import evaluate_grounded_semantic_downstream_gate


class GroundedSourceMode(str, Enum):
    DIRECT_ASSERTION = "direct_assertion"
    QUOTED_CONTENT = "quoted_content"
    REPORTED_CONTENT = "reported_content"
    MIXED = "mixed"
    UNSPECIFIED = "unspecified"


class GroundedAuthorityLevel(str, Enum):
    SCAFFOLD_ONLY = "scaffold_only"
    DEGRADED_SCAFFOLD_ONLY = "degraded_scaffold_only"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class GroundedDownstreamContractView:
    source_mode: GroundedSourceMode
    negation_present: bool
    interrogation_or_modality_present: bool
    dictum_modus_split_present: bool
    uncertainty_elevated: bool
    low_coverage_mode: bool
    normative_l05_l06_route_active: bool
    legacy_surface_cue_fallback_used: bool
    l06_blocked_update_present: bool
    l06_guarded_continue_present: bool
    authority_level: GroundedAuthorityLevel
    usable_for_distinction: bool
    can_distinguish_source_handling: bool
    can_distinguish_operator_handling: bool
    restrictions: tuple[str, ...]
    reason: str


def derive_grounded_downstream_contract(
    grounded_result_or_bundle: GroundedSemanticResult | GroundedSemanticBundle,
) -> GroundedDownstreamContractView:
    if isinstance(grounded_result_or_bundle, GroundedSemanticResult):
        bundle = grounded_result_or_bundle.bundle
    elif isinstance(grounded_result_or_bundle, GroundedSemanticBundle):
        bundle = grounded_result_or_bundle
    else:
        raise TypeError(
            "derive_grounded_downstream_contract requires GroundedSemanticResult/GroundedSemanticBundle"
        )

    gate = evaluate_grounded_semantic_downstream_gate(bundle)
    operator_kinds = {carrier.operator_kind for carrier in bundle.operator_carriers}
    anchor_kinds = {anchor.anchor_kind for anchor in bundle.source_anchors}

    quote_signals = (
        SourceAnchorKind.QUOTE_BOUNDARY in anchor_kinds
        or OperatorKind.QUOTATION in operator_kinds
    )
    report_signals = SourceAnchorKind.REPORTED_SPEECH in anchor_kinds
    if quote_signals and report_signals:
        source_mode = GroundedSourceMode.MIXED
    elif quote_signals:
        source_mode = GroundedSourceMode.QUOTED_CONTENT
    elif report_signals:
        source_mode = GroundedSourceMode.REPORTED_CONTENT
    elif bundle.source_anchors:
        source_mode = GroundedSourceMode.DIRECT_ASSERTION
    else:
        source_mode = GroundedSourceMode.UNSPECIFIED

    negation_present = OperatorKind.NEGATION in operator_kinds
    interrogation_or_modality_present = bool(
        operator_kinds.intersection(
            {
                OperatorKind.INTERROGATION,
                OperatorKind.MODALITY,
                OperatorKind.DISCOURSE_PARTICLE,
            }
        )
    )
    dictum_modus_split_present = bool(bundle.dictum_carriers and bundle.modus_carriers)
    uncertainty_elevated = bool(bundle.uncertainty_markers)
    low_coverage_mode = bundle.low_coverage_mode

    degraded = bool(
        low_coverage_mode
        or "downstream_authority_degraded" in gate.restrictions
        or not bundle.operator_carriers
        or not bundle.source_anchors
        or bundle.legacy_surface_cue_fallback_used
        or bundle.l06_blocked_update_present
        or bundle.l06_guarded_continue_present
    )

    if not gate.accepted:
        authority_level = GroundedAuthorityLevel.BLOCKED
    elif degraded:
        authority_level = GroundedAuthorityLevel.DEGRADED_SCAFFOLD_ONLY
    else:
        authority_level = GroundedAuthorityLevel.SCAFFOLD_ONLY

    can_distinguish_source_handling = source_mode is not GroundedSourceMode.UNSPECIFIED
    can_distinguish_operator_handling = bool(bundle.operator_carriers)
    usable_for_distinction = bool(
        gate.accepted
        and authority_level is GroundedAuthorityLevel.SCAFFOLD_ONLY
        and can_distinguish_source_handling
        and can_distinguish_operator_handling
    )
    reason = (
        "g01 contract view emits scaffold-bounded distinction surface"
        if gate.accepted
        else "g01 contract view blocked by gate"
    )
    return GroundedDownstreamContractView(
        source_mode=source_mode,
        negation_present=negation_present,
        interrogation_or_modality_present=interrogation_or_modality_present,
        dictum_modus_split_present=dictum_modus_split_present,
        uncertainty_elevated=uncertainty_elevated,
        low_coverage_mode=low_coverage_mode,
        normative_l05_l06_route_active=bundle.normative_l05_l06_route_active,
        legacy_surface_cue_fallback_used=bundle.legacy_surface_cue_fallback_used,
        l06_blocked_update_present=bundle.l06_blocked_update_present,
        l06_guarded_continue_present=bundle.l06_guarded_continue_present,
        authority_level=authority_level,
        usable_for_distinction=usable_for_distinction,
        can_distinguish_source_handling=can_distinguish_source_handling,
        can_distinguish_operator_handling=can_distinguish_operator_handling,
        restrictions=gate.restrictions,
        reason=reason,
    )
