from __future__ import annotations

from dataclasses import dataclass, replace

from substrate.ab04_epistemic_candidate_basis import (
    AB4EpistemicBasisInput,
    AB4EpistemicBasisResult,
    build_ab4_epistemic_candidate_basis,
)

from .ab3_hypothesis_frontier_probe import run_ab3_probe_case


@dataclass(frozen=True, slots=True)
class AB4ProbeCase:
    case_id: str
    description: str


@dataclass(frozen=True, slots=True)
class AB4ProbeRun:
    case_id: str
    result: AB4EpistemicBasisResult
    route_supported: bool
    routed_ap01_publication_count: int
    routed_world_submission_count: int


def list_ab4_probe_cases() -> tuple[AB4ProbeCase, ...]:
    return (
        AB4ProbeCase("open_frontier_inspect", "open frontier yields inspect/check-consistency basis"),
        AB4ProbeCase("ambiguous_frontier_wait", "ambiguous frontier yields wait/reobserve basis"),
        AB4ProbeCase("hidden_eval_only", "hidden/eval frontier rejected"),
        AB4ProbeCase("no_frontier", "no frontier means no epistemic basis"),
        AB4ProbeCase("no_discriminating_test", "frontier without discriminating tests is not AB4-ready"),
    )


def run_ab4_probe_case(
    case_id: str,
    *,
    route_through_acp01: bool = False,
    suppress_ap01: bool = False,
) -> AB4ProbeRun:
    if case_id == "open_frontier_inspect":
        ab3 = run_ab3_probe_case("blocked_movement_effect")
        result = build_ab4_epistemic_candidate_basis(
            AB4EpistemicBasisInput(
                tick_ref="ab4:probe:open_frontier_inspect",
                frontier=ab3.frontier,
                source_refs=("probe:ab3:blocked_movement_effect",),
                observation_refs=("obs:ab4:open",),
                residue_refs=("residue:ab4:open",),
                effect_refs=("effect:ab4:open",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                allow_numeric_eig=False,
                source="ab4_probe.open_frontier_inspect",
            )
        )
        return _probe_result(case_id, result, route_through_acp01=route_through_acp01, suppress_ap01=suppress_ap01)
    if case_id == "ambiguous_frontier_wait":
        ab3 = run_ab3_probe_case("ambiguous_evidence")
        result = build_ab4_epistemic_candidate_basis(
            AB4EpistemicBasisInput(
                tick_ref="ab4:probe:ambiguous_frontier_wait",
                frontier=ab3.frontier,
                source_refs=("probe:ab3:ambiguous_evidence",),
                observation_refs=("obs:ab4:ambiguous",),
                residue_refs=("residue:ab4:ambiguous",),
                effect_refs=("effect:ab4:ambiguous",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                allow_numeric_eig=False,
                source="ab4_probe.ambiguous_frontier_wait",
            )
        )
        return _probe_result(case_id, result, route_through_acp01=route_through_acp01, suppress_ap01=suppress_ap01)
    if case_id == "hidden_eval_only":
        ab3 = run_ab3_probe_case("hidden_eval_only")
        result = build_ab4_epistemic_candidate_basis(
            AB4EpistemicBasisInput(
                tick_ref="ab4:probe:hidden_eval_only",
                frontier=ab3.frontier,
                source_refs=("probe:ab3:hidden_eval_only",),
                observation_refs=("obs:ab4:hidden",),
                residue_refs=("residue:ab4:hidden",),
                effect_refs=("effect:ab4:hidden",),
                public_only=True,
                hidden_eval_excluded=False,
                scenario_label_excluded=True,
                allow_numeric_eig=False,
                source="ab4_probe.hidden_eval_only",
            )
        )
        return _probe_result(case_id, result, route_through_acp01=route_through_acp01, suppress_ap01=suppress_ap01)
    if case_id == "no_frontier":
        result = build_ab4_epistemic_candidate_basis(
            AB4EpistemicBasisInput(
                tick_ref="ab4:probe:no_frontier",
                frontier=None,
                source_refs=("probe:no_frontier",),
                observation_refs=("obs:ab4:none",),
                residue_refs=(),
                effect_refs=(),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                allow_numeric_eig=False,
                source="ab4_probe.no_frontier",
            )
        )
        return _probe_result(case_id, result, route_through_acp01=route_through_acp01, suppress_ap01=suppress_ap01)
    if case_id == "no_discriminating_test":
        ab3 = run_ab3_probe_case("effect_mismatch")
        assert ab3.frontier is not None
        frontier = replace(ab3.frontier, discriminating_tests=())
        result = build_ab4_epistemic_candidate_basis(
            AB4EpistemicBasisInput(
                tick_ref="ab4:probe:no_discriminating_test",
                frontier=frontier,
                source_refs=("probe:ab3:no_discriminating_test",),
                observation_refs=("obs:ab4:no_test",),
                residue_refs=("residue:ab4:no_test",),
                effect_refs=("effect:ab4:no_test",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                allow_numeric_eig=False,
                source="ab4_probe.no_discriminating_test",
            )
        )
        return _probe_result(case_id, result, route_through_acp01=route_through_acp01, suppress_ap01=suppress_ap01)
    raise ValueError(f"Unknown AB4 probe case: {case_id}")


def _probe_result(
    case_id: str,
    result: AB4EpistemicBasisResult,
    *,
    route_through_acp01: bool,
    suppress_ap01: bool,
) -> AB4ProbeRun:
    # AB4 probe keeps authority boundaries strict: no direct ACP01/AP01/world routing side effects.
    _ = route_through_acp01, suppress_ap01
    return AB4ProbeRun(
        case_id=case_id,
        result=result,
        route_supported=False,
        routed_ap01_publication_count=0,
        routed_world_submission_count=0,
    )
