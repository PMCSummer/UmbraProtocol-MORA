from __future__ import annotations

from .models import (
    AB3FrontierHypothesisRecord,
    AB3FrontierInput,
    AB3SupportBucket,
    AB3Telemetry,
)


def build_ab3_telemetry(
    *,
    candidate_input: AB3FrontierInput,
    hypotheses: tuple[AB3FrontierHypothesisRecord, ...],
    unsafe_basis_count: int,
) -> AB3Telemetry:
    return AB3Telemetry(
        tick_ref=candidate_input.tick_ref,
        hypothesis_count=len(hypotheses),
        unresolved_conflict_count=sum(1 for item in hypotheses if item.conflicts_with),
        missing_evidence_count=sum(len(item.missing_evidence) for item in hypotheses),
        discriminating_test_count=sum(1 for item in hypotheses if item.discriminated_by),
        supported_count=sum(1 for item in hypotheses if item.support_bucket is AB3SupportBucket.SUPPORTED),
        provisional_count=sum(1 for item in hypotheses if item.support_bucket is AB3SupportBucket.PROVISIONAL),
        weak_count=sum(1 for item in hypotheses if item.support_bucket is AB3SupportBucket.WEAK),
        contradicted_count=sum(1 for item in hypotheses if item.support_bucket is AB3SupportBucket.CONTRADICTED),
        blocked_count=sum(1 for item in hypotheses if item.support_bucket is AB3SupportBucket.UNSUPPORTED),
        unsafe_basis_count=unsafe_basis_count,
    )
