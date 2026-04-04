from __future__ import annotations

from dataclasses import replace

import pytest

from substrate.concept_framing.models import FramingStatus, VulnerabilityLevel
from substrate.targeted_clarification import build_targeted_clarification


@pytest.mark.parametrize(
    ("ablation_id", "ablate"),
    (
        (
            "remove_framing_vulnerability_inputs",
                lambda ctx: (
                    ctx.acquisition,
                    replace(
                        ctx.framing.bundle,
                        framing_records=tuple(
                            replace(
                                record,
                                framing_status=FramingStatus.CONTEXT_ONLY_FRAME_HINT,
                                vulnerability_profile=replace(
                                    record.vulnerability_profile,
                                    high_impact=False,
                                    vulnerability_level=VulnerabilityLevel.LOW,
                                    fragility_reasons=(),
                            ),
                        )
                        for record in ctx.framing.bundle.framing_records
                    ),
                ),
            ),
        ),
        (
            "remove_unresolved_slot_structure",
            lambda ctx: (
                replace(
                    ctx.acquisition.bundle,
                    acquisition_records=tuple(
                        replace(
                            record,
                            support_conflict_profile=replace(
                                record.support_conflict_profile,
                                unresolved_slots=(),
                                conflict_reasons=(),
                                conflict_score=0.0,
                            ),
                        )
                        for record in ctx.acquisition.bundle.acquisition_records
                    ),
                ),
                ctx.framing,
            ),
        ),
        (
            "remove_provenance_linkage",
            lambda ctx: (
                replace(ctx.acquisition.bundle, source_perspective_chain_ref="unknown-acq-ref"),
                replace(ctx.framing.bundle, source_perspective_chain_ref="unknown-frame-ref"),
                ),
            ),
            (
                "remove_target_binding_cues",
                lambda ctx: (
                    ctx.acquisition,
                    replace(
                        ctx.framing.bundle,
                        framing_records=tuple(
                            replace(record, acquisition_id=f"missing-{record.acquisition_id}")
                            for record in ctx.framing.bundle.framing_records
                        ),
                    ),
                ),
            ),
        ),
    )
def test_ablation_changes_intervention_outcome_or_degraded_surface(ablation_id: str, ablate, g07_factory) -> None:
    ctx = g07_factory('he said "you are not tired?"', f"g07-ablation-{ablation_id}")
    baseline = build_targeted_clarification(ctx.acquisition, ctx.framing)
    acq, frame = ablate(ctx)
    degraded = build_targeted_clarification(acq, frame)

    baseline_sig = {
        (
            record.intervention_status.value,
            record.uncertainty_class.value,
            tuple(sorted(record.downstream_lockouts)),
        )
        for record in baseline.bundle.intervention_records
    }
    degraded_sig = {
        (
            record.intervention_status.value,
            record.uncertainty_class.value,
            tuple(sorted(record.downstream_lockouts)),
        )
        for record in degraded.bundle.intervention_records
    }
    assert (
        baseline_sig != degraded_sig
        or baseline.bundle.low_coverage_reasons != degraded.bundle.low_coverage_reasons
        or baseline.bundle.ambiguity_reasons != degraded.bundle.ambiguity_reasons
        or {record.uncertainty_target_id for record in baseline.bundle.intervention_records}
        != {record.uncertainty_target_id for record in degraded.bundle.intervention_records}
    )
