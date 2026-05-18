from __future__ import annotations

from dataclasses import dataclass, replace

from substrate.ab03_hypothesis_frontier import (
    AB3FrontierInput,
    AB3FrontierResult,
    build_ab3_hypothesis_frontier,
)

from .ab2_hypothesis_seed_probe import run_ab2_probe_case


@dataclass(frozen=True, slots=True)
class AB3ProbeCase:
    case_id: str
    description: str


def list_ab3_probe_cases() -> tuple[AB3ProbeCase, ...]:
    return (
        AB3ProbeCase("blocked_movement_effect", "AB2 blocked movement seeds -> AB3 frontier"),
        AB3ProbeCase("effect_mismatch", "AB2 effect mismatch seeds -> AB3 frontier"),
        AB3ProbeCase("inventory_delta", "AB2 inventory delta seeds -> AB3 frontier"),
        AB3ProbeCase("ambiguous_evidence", "conflicting/disconfirming evidence keeps frontier open"),
        AB3ProbeCase("hidden_eval_only", "hidden/eval-only basis blocks frontier"),
        AB3ProbeCase("single_hypothesis_ambiguous", "single live hypothesis under ambiguity blocks frontier"),
    )


def run_ab3_probe_case(case_id: str) -> AB3FrontierResult:
    if case_id == "blocked_movement_effect":
        seed_result = run_ab2_probe_case("blocked_movement_effect")
        return build_ab3_hypothesis_frontier(
            AB3FrontierInput(
                tick_ref="ab3:probe:blocked_movement_effect",
                seed_set=seed_result.seed_set,
                source_refs=("probe:ab2:blocked_movement_effect",),
                observation_refs=("obs:blocked:public",),
                residue_refs=("residue:blocked:public",),
                effect_refs=("effect:blocked:public",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab3_probe.blocked_movement_effect",
            )
        )
    if case_id == "effect_mismatch":
        seed_result = run_ab2_probe_case("effect_mismatch")
        return build_ab3_hypothesis_frontier(
            AB3FrontierInput(
                tick_ref="ab3:probe:effect_mismatch",
                seed_set=seed_result.seed_set,
                source_refs=("probe:ab2:effect_mismatch",),
                observation_refs=("obs:mismatch:public",),
                residue_refs=("residue:mismatch:public",),
                effect_refs=("effect:mismatch:public",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab3_probe.effect_mismatch",
            )
        )
    if case_id == "inventory_delta":
        seed_result = run_ab2_probe_case("pickup_inventory_delta")
        return build_ab3_hypothesis_frontier(
            AB3FrontierInput(
                tick_ref="ab3:probe:inventory_delta",
                seed_set=seed_result.seed_set,
                source_refs=("probe:ab2:inventory_delta",),
                observation_refs=("obs:inventory:public",),
                residue_refs=(),
                effect_refs=("effect:inventory:public",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab3_probe.inventory_delta",
            )
        )
    if case_id == "ambiguous_evidence":
        seed_result = run_ab2_probe_case("effect_mismatch")
        return build_ab3_hypothesis_frontier(
            AB3FrontierInput(
                tick_ref="ab3:probe:ambiguous_evidence",
                seed_set=seed_result.seed_set,
                source_refs=("probe:ab2:ambiguous_evidence",),
                observation_refs=("obs:ambiguous:public",),
                residue_refs=("residue:ambiguous:public",),
                effect_refs=("effect:ambiguous:public",),
                disconfirming_evidence_refs=("ab1:ab1:probe:effect_mismatch:effect_mismatch",),
                ambiguous_evidence=True,
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab3_probe.ambiguous_evidence",
            )
        )
    if case_id == "hidden_eval_only":
        seed_result = run_ab2_probe_case("hidden_eval_only")
        return build_ab3_hypothesis_frontier(
            AB3FrontierInput(
                tick_ref="ab3:probe:hidden_eval_only",
                seed_set=seed_result.seed_set,
                source_refs=("probe:hidden_eval_only",),
                observation_refs=("obs:hidden_eval",),
                residue_refs=("residue:hidden_eval",),
                effect_refs=("effect:hidden_eval",),
                public_only=True,
                hidden_eval_excluded=False,
                scenario_label_excluded=True,
                source="ab3_probe.hidden_eval_only",
            )
        )
    if case_id == "single_hypothesis_ambiguous":
        seed_result = run_ab2_probe_case("effect_mismatch")
        if seed_result.seed_set is None:
            raise ValueError("single_hypothesis_ambiguous requires AB2 seed_set")
        first = next(iter(seed_result.seed_set.hypotheses), None)
        if first is None:
            raise ValueError("single_hypothesis_ambiguous requires at least one AB2 hypothesis")
        single_seed_set = replace(seed_result.seed_set, hypotheses=(first,))
        return build_ab3_hypothesis_frontier(
            AB3FrontierInput(
                tick_ref="ab3:probe:single_hypothesis_ambiguous",
                seed_set=single_seed_set,
                source_refs=("probe:ab2:single_hypothesis",),
                observation_refs=("obs:single:public",),
                residue_refs=("residue:single:public",),
                effect_refs=("effect:single:public",),
                ambiguous_evidence=True,
                require_competing_hypotheses=True,
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab3_probe.single_hypothesis_ambiguous",
            )
        )
    raise ValueError(f"Unknown AB3 probe case: {case_id}")
