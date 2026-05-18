from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.embodied_playground.ablation_runner import (
    list_ablation_specs,
    list_causal_necessity_scenarios,
    run_causal_necessity_case,
    run_causal_necessity_matrix,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P9 strict no-auto-builder causal necessity demo.")
    parser.add_argument("--list-ablations", action="store_true")
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--scenario", default="visible_item_pickup_available")
    parser.add_argument("--ablation", default="no_acp01")
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--ticks", type=int, default=2)
    parser.add_argument("--drive", default=None)
    return parser.parse_args()


def _print_case_report(payload: dict[str, object]) -> None:
    print("CAUSAL NECESSITY REPORT (P9)")
    print(f"scenario={payload['scenario_id']} mode={payload['mode']}")
    baseline = payload["baseline_trace"]
    ablated = payload["ablation_traces"][0]
    strict = payload["strict_trace"]
    print(
        "baseline: "
        f"ap01_published={baseline['ap01_published_count']} "
        f"world_submissions={baseline['world_submission_count']} "
        f"effect_feedback={baseline['effect_feedback_count']}"
    )
    print(
        "ablated: "
        f"id={ablated['ablation_id']} "
        f"ap01_published={ablated['ap01_published_count']} "
        f"world_submissions={ablated['world_submission_count']} "
        f"degradation_observed={ablated['degradation_observed']}"
    )
    print(
        "strict: "
        f"enabled={strict['strict_mode_enabled']} "
        f"auto_builder_detected={strict['auto_builder_detected']} "
        f"valid_basis_flow={strict['valid_basis_flow']}"
    )
    print(f"observed_degradations={payload['observed_degradations']}")
    print(f"falsifier_results={payload['falsifier_results']}")
    print(f"claim_safe_verdict={payload['claim_safe_verdict']}")
    print(payload["claim_boundary"])


def _print_matrix_report(matrix_payload: list[dict[str, object]]) -> None:
    print("CAUSAL NECESSITY MATRIX REPORT (P9)")
    for run in matrix_payload:
        ablated = run["ablation_traces"][0]
        strict = run["strict_trace"]
        print(
            f"[{run['scenario_id']} / {ablated['ablation_id']}] "
            f"degradation={ablated['degradation_observed']} "
            f"strict_valid={strict['valid_basis_flow']} "
            f"verdict={run['claim_safe_verdict']}"
        )
    print("P9 supports causal-load-bearing evidence only; not consciousness or general autonomy proof.")


def main() -> int:
    args = _parse_args()
    if args.list_ablations:
        for spec in list_ablation_specs():
            print(f"{spec.ablation_id} kind={spec.ablation_kind.value} seam={spec.seam_id}")
        return 0
    if args.list_scenarios:
        for scenario in list_causal_necessity_scenarios():
            print(scenario)
        return 0

    if args.matrix:
        runs = run_causal_necessity_matrix(ticks=max(1, args.ticks), strict_mode=bool(args.strict))
        payload = [asdict(item) for item in runs]
        if args.report:
            _print_matrix_report(payload)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        if not args.report and not args.json:
            _print_matrix_report(payload)
        return 0

    run = run_causal_necessity_case(
        scenario_id=args.scenario,
        ablation_id=args.ablation,
        ticks=max(1, args.ticks),
        drive_kind=args.drive,
        strict_mode=bool(args.strict),
    )
    payload = asdict(run)
    if args.report:
        _print_case_report(payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if not args.report and not args.json:
        _print_case_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
