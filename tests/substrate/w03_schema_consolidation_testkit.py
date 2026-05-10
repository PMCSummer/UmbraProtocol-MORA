from __future__ import annotations

from dataclasses import dataclass

from substrate.w02_regularity_extraction import W02InputBundle, build_w02_regularity_extraction
from substrate.w03_schema_consolidation import (
    W03InputBundle,
    W03ResultBundle,
    build_w03_schema_consolidation,
)


@dataclass(frozen=True, slots=True)
class W03HarnessCase:
    case_id: str
    w03_input: W03InputBundle | None
    enforcement_enabled: bool = True


@dataclass(frozen=True, slots=True)
class W03HarnessRun:
    w03_result: W03ResultBundle


def build_w03_harness_case(case: W03HarnessCase) -> W03HarnessRun:
    result = build_w03_schema_consolidation(
        tick_id=f"tests.w03:{case.case_id}",
        tick_index=1,
        input_bundle=case.w03_input,
        enforcement_enabled=case.enforcement_enabled,
    )
    return W03HarnessRun(w03_result=result)


def w03_input_from_w02(
    *,
    case_id: str,
    w02_input: W02InputBundle,
    tick_index: int = 1,
    source_lineage: tuple[str, ...] = (),
) -> W03InputBundle:
    w02_result = build_w02_regularity_extraction(
        tick_id=f"tests.w03:{case_id}:w02",
        tick_index=tick_index,
        input_bundle=w02_input,
        enforcement_enabled=True,
    )
    return W03InputBundle(
        bundle_id=f"{case_id}:w03:bundle",
        source_lineage=source_lineage or ("tests.w03", case_id),
        w02_regularity_records=w02_result.regularity_records,
        w02_permission_packets=w02_result.downstream_permission_packets,
        w02_contradiction_ledger=w02_result.contradiction_ledger,
        reason=case_id,
    )
