from __future__ import annotations

from dataclasses import dataclass

from substrate.ab02_hypothesis_seed import (
    AB2HypothesisSeedInput,
    AB2HypothesisSeedResult,
    build_ab2_hypothesis_seeds,
)

from .ab1_event_digest_probe import run_ab1_probe_case


@dataclass(frozen=True, slots=True)
class AB2ProbeCase:
    case_id: str
    description: str


def list_ab2_probe_cases() -> tuple[AB2ProbeCase, ...]:
    return (
        AB2ProbeCase("blocked_movement_effect", "AB1 blocked movement digest -> AB2 competing seeds"),
        AB2ProbeCase("pickup_inventory_delta", "AB1 inventory delta mismatch digest -> AB2 competing seeds"),
        AB2ProbeCase("effect_mismatch", "AB1 expected/observed mismatch digest -> AB2 competing seeds"),
        AB2ProbeCase("hidden_eval_only", "hidden/eval basis -> AB2 blocks seed generation"),
        AB2ProbeCase("no_event_digest", "no event digest -> no AB2 seeds"),
    )


def run_ab2_probe_case(case_id: str) -> AB2HypothesisSeedResult:
    if case_id == "blocked_movement_effect":
        ab1_result = run_ab1_probe_case("blocked_movement_effect")
        return build_ab2_hypothesis_seeds(
            AB2HypothesisSeedInput(
                tick_ref="ab2:probe:blocked_movement_effect",
                event_digests=ab1_result.digests,
                source_refs=("probe:ab1:blocked_movement_effect",),
                observation_refs=("obs:blocked:public",),
                residue_refs=("residue:blocked:public",),
                effect_refs=("effect:blocked:public",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab2_probe.blocked_movement_effect",
            )
        )
    if case_id == "pickup_inventory_delta":
        ab1_result = run_ab1_probe_case("pickup_inventory_delta")
        return build_ab2_hypothesis_seeds(
            AB2HypothesisSeedInput(
                tick_ref="ab2:probe:pickup_inventory_delta",
                event_digests=ab1_result.digests,
                source_refs=("probe:ab1:pickup_inventory_delta",),
                observation_refs=("obs:pickup:public",),
                residue_refs=(),
                effect_refs=("effect:pickup:public",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab2_probe.pickup_inventory_delta",
            )
        )
    if case_id == "effect_mismatch":
        ab1_result = run_ab1_probe_case("effect_mismatch")
        return build_ab2_hypothesis_seeds(
            AB2HypothesisSeedInput(
                tick_ref="ab2:probe:effect_mismatch",
                event_digests=ab1_result.digests,
                source_refs=("probe:ab1:effect_mismatch",),
                observation_refs=("obs:mismatch:public",),
                residue_refs=("residue:mismatch:public",),
                effect_refs=("effect:mismatch:public",),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab2_probe.effect_mismatch",
            )
        )
    if case_id == "hidden_eval_only":
        ab1_result = run_ab1_probe_case("hidden_eval_only")
        return build_ab2_hypothesis_seeds(
            AB2HypothesisSeedInput(
                tick_ref="ab2:probe:hidden_eval_only",
                event_digests=ab1_result.digests,
                source_refs=("probe:hidden_eval_only",),
                observation_refs=("obs:hidden_eval",),
                residue_refs=("residue:hidden_eval",),
                effect_refs=("effect:hidden_eval",),
                public_only=True,
                hidden_eval_excluded=False,
                scenario_label_excluded=True,
                source="ab2_probe.hidden_eval_only",
            )
        )
    if case_id == "no_event_digest":
        return build_ab2_hypothesis_seeds(
            AB2HypothesisSeedInput(
                tick_ref="ab2:probe:no_event_digest",
                event_digests=(),
                source_refs=("probe:no_event_digest",),
                observation_refs=("obs:no_event",),
                residue_refs=(),
                effect_refs=(),
                public_only=True,
                hidden_eval_excluded=True,
                scenario_label_excluded=True,
                source="ab2_probe.no_event_digest",
            )
        )
    raise ValueError(f"Unknown AB2 probe case: {case_id}")
