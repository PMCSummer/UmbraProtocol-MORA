from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.baseline_runner import (
    BaselineCompetitionMatrix,
    BaselineCompetitionRun,
    list_baseline_scenarios,
    run_baseline_competition,
    run_baseline_competition_matrix,
)
from experiments.embodied_playground.baselines import build_default_baselines


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P8B baseline competition runner/report demo.")
    parser.add_argument("--list-baselines", action="store_true", help="List available baseline controllers")
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenario matrix ids")
    parser.add_argument("--scenario", default="visible_item_pickup_available", help="Scenario matrix id")
    parser.add_argument("--ticks", type=int, default=2, help="Tick budget")
    parser.add_argument("--drive", action="append", default=[], help="Drive kind (repeatable)")
    parser.add_argument("--include-hidden-oracle", action="store_true", help="Include diagnostic unfair hidden oracle")
    parser.add_argument("--include-direct-bridge", action="store_true", help="Include AP01 bypass diagnostic baseline")
    parser.add_argument("--matrix", action="store_true", help="Run required scenario matrix")
    parser.add_argument("--report", action="store_true", help="Print human-readable comparison report")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument("--seed", type=int, default=7, help="Random baseline seed")
    return parser.parse_args()


def _print_run_summary(run: BaselineCompetitionRun) -> None:
    print(
        f"scenario={run.scenario_id} category={run.adversarial_category.value} "
        f"world_scenario={run.world_scenario_id} ticks={run.tick_budget}"
    )
    print(f"drive_basis={run.drive_basis}")
    print(
        f"mora: subject_tick={run.mora_trace.subject_tick_used} "
        f"acp01={run.mora_trace.acp01_used} "
        f"ap01_published={run.mora_trace.ap01_published_count} "
        f"world_submissions={run.mora_trace.world_submission_count} "
        f"abstentions={run.mora_trace.abstention_count}"
    )
    for trace in run.baseline_traces:
        print(
            f"{trace.controller_id} fairness={trace.fairness_class.value} "
            f"attempts={trace.action_attempts} abstentions={trace.abstentions} "
            f"invalid_actions={trace.invalid_actions} hidden_eval_usage={trace.hidden_eval_usage} "
            f"matched_info={trace.matched_information_status}"
        )
    print(
        f"verdict={run.claim_safe_verdict.value} "
        f"fair_matched={run.fairness_report.matched_information_budget_ok} "
        f"ap01_bypass_count={run.boundary_violation_summary.ap01_bypass_count}"
    )


def _print_run_report(run: BaselineCompetitionRun) -> None:
    print("=== Scenario Summary ===")
    print(f"scenario_id: {run.scenario_id}")
    print(f"adversarial_category: {run.adversarial_category.value}")
    print(f"world_scenario_id: {run.world_scenario_id}")
    print(f"tick_budget: {run.tick_budget}")
    print(f"drive_basis: {run.drive_basis}")
    print(f"expected_mora_behavior: {run.expected_mora_behavior}")
    print(f"expected_baseline_weakness: {run.expected_baseline_weakness}")
    print(f"main_differentiator: {run.main_differentiator}")

    print("=== MORA Summary ===")
    print(f"subject_tick_used: {run.mora_trace.subject_tick_used}")
    print(f"acp01_used: {run.mora_trace.acp01_used}")
    print(f"manual_provider_used: {run.mora_trace.manual_provider_used}")
    print(f"ap01_published_count: {run.mora_trace.ap01_published_count}")
    print(f"world_submission_count: {run.mora_trace.world_submission_count}")
    print(f"effect_feedback_count: {run.mora_trace.effect_feedback_count}")
    print(f"abstention_count: {run.mora_trace.abstention_count}")

    print("=== Baseline Summary ===")
    for trace in run.baseline_traces:
        print(
            f"- {trace.controller_id} ({trace.fairness_class.value}) "
            f"attempts={trace.action_attempts} abstentions={trace.abstentions} "
            f"invalid={trace.invalid_actions} hidden_eval={trace.hidden_eval_usage}"
        )

    print("=== Metrics ===")
    print(
        f"success_rate={run.metric_summary.success_rate:.3f} "
        f"invalid_action_rate={run.metric_summary.invalid_action_rate:.3f} "
        f"abstention_quality={run.metric_summary.abstention_quality:.3f} "
        f"boundary_integrity={run.metric_summary.boundary_integrity:.3f} "
        f"matched_information_score={run.metric_summary.matched_information_score:.3f} "
        f"differentiator_score={run.metric_summary.differentiator_score:.3f} "
        f"fsm_equivalence_risk={run.metric_summary.fsm_equivalence_risk:.3f}"
    )

    print("=== Fairness ===")
    print(f"fair_baselines={list(run.fairness_report.fair_baselines)}")
    print(f"diagnostic_unfair_baselines={list(run.fairness_report.diagnostic_unfair_baselines)}")
    print(f"boundary_violation_baselines={list(run.fairness_report.boundary_violation_baselines)}")
    print(f"excluded_from_fair_comparison={list(run.fairness_report.excluded_from_fair_comparison)}")
    print(f"hidden_oracle_marked_unfair={run.fairness_report.hidden_oracle_marked_unfair}")
    print(f"direct_bridge_marked_bypass={run.fairness_report.direct_bridge_marked_bypass}")

    print("=== Boundary Violations ===")
    print(
        f"ap01_bypass_count={run.boundary_violation_summary.ap01_bypass_count} "
        f"hidden_eval_usage_count={run.boundary_violation_summary.hidden_eval_usage_count} "
        f"scenario_label_usage_count={run.boundary_violation_summary.scenario_label_usage_count} "
        f"request_as_execution_count={run.boundary_violation_summary.request_as_execution_count} "
        f"direct_bridge_success_count={run.boundary_violation_summary.direct_bridge_success_count} "
        f"unfair_baseline_success_count={run.boundary_violation_summary.unfair_baseline_success_count}"
    )

    print("=== Differentiators ===")
    for note in run.differentiator_summary.key_differences:
        print(f"- {note}")
    print("=== MORA vs FSM ===")
    for note in run.differentiator_summary.mora_vs_fsm_notes:
        print(f"- {note}")

    print("=== Claim-safe Conclusion ===")
    print(f"claim_safe_verdict={run.claim_safe_verdict.value}")
    print(run.claim_boundary)


def _print_matrix_report(matrix: BaselineCompetitionMatrix) -> None:
    print("EMBODIED BASELINE COMPETITION MATRIX REPORT (P8B)")
    print("adversarial_categories:")
    for category, scenarios in matrix.grouped_by_adversarial_category.items():
        print(f"- {category}: {list(scenarios)}")
    for run in matrix.scenario_runs:
        print(
            f"\n[{run.scenario_id}] category={run.adversarial_category.value} "
            f"verdict={run.claim_safe_verdict.value}"
        )
        print(
            f"mora ap01_published={run.mora_trace.ap01_published_count} "
            f"world_submissions={run.mora_trace.world_submission_count} "
            f"abstentions={run.mora_trace.abstention_count}"
        )
        print(
            f"fairness matched={run.fairness_report.matched_information_budget_ok} "
            f"hidden_oracle_unfair={run.fairness_report.hidden_oracle_marked_unfair} "
            f"direct_bridge_bypass={run.fairness_report.direct_bridge_marked_bypass}"
        )
        print(
            f"boundary ap01_bypass={run.boundary_violation_summary.ap01_bypass_count} "
            f"hidden_eval={run.boundary_violation_summary.hidden_eval_usage_count}"
        )
        print(
            f"fsm_equivalence_risk={run.metric_summary.fsm_equivalence_risk:.3f} "
            f"mora_vs_fsm_notes={list(run.differentiator_summary.mora_vs_fsm_notes)}"
        )
    print(f"\nclaim_boundary={matrix.claim_boundary}")


def main() -> int:
    args = _parse_args()
    if args.list_baselines:
        controllers = build_default_baselines(
            seed=args.seed,
            include_hidden_oracle=True,
            include_direct_bridge=True,
            include_simple_fsm=True,
        )
        for controller in controllers:
            print(
                f"{controller.controller_id} kind={controller.controller_kind} fairness={controller.fairness_class.value}"
            )
        return 0
    if args.list_scenarios:
        for spec in list_baseline_scenarios():
            print(f"{spec.scenario_id} -> {spec.world_scenario_id} ({spec.scenario_class.value})")
        return 0

    if args.matrix:
        matrix = run_baseline_competition_matrix(
            ticks=max(1, args.ticks),
            seed=args.seed,
            include_hidden_oracle=bool(args.include_hidden_oracle),
            include_direct_bridge=bool(args.include_direct_bridge),
            include_optional=True,
        )
        if args.report:
            _print_matrix_report(matrix)
        if args.json:
            print(json.dumps(asdict(matrix), ensure_ascii=False, indent=2, sort_keys=True))
        if not args.report and not args.json:
            _print_matrix_report(matrix)
        return 0

    run = run_baseline_competition(
        scenario_id=args.scenario,
        ticks=max(1, args.ticks),
        drive_kinds=tuple(args.drive) if args.drive else None,
        seed=args.seed,
        include_hidden_oracle=bool(args.include_hidden_oracle),
        include_direct_bridge=bool(args.include_direct_bridge),
    )

    print("EMBODIED BASELINE COMPETITION DEMO (P8B)")
    _print_run_summary(run)
    if args.report:
        _print_run_report(run)
    if args.json:
        print(json.dumps(asdict(run), ensure_ascii=False, indent=2, sort_keys=True))
    if not args.report and not args.json:
        print(run.claim_boundary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
