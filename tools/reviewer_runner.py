from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reviewer.config import ReviewerPipelineConfig
from reviewer.night_run import NightRunController
from reviewer.pipeline import LocalStatelessReviewerPipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local stateless LLM reviewer pipeline runner."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional JSON config path. If omitted, built-in defaults are used.",
    )
    parser.add_argument(
        "--write-default-config",
        type=Path,
        default=None,
        help="Write default config JSON and exit.",
    )
    parser.add_argument(
        "--case-count",
        type=int,
        default=None,
        help="Override cases per cycle.",
    )
    parser.add_argument(
        "--themes",
        type=str,
        default=None,
        help="Comma-separated theme filters.",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run cycles continuously until interrupted.",
    )
    parser.add_argument(
        "--diagnostic-mode",
        action="store_true",
        help="Enable per-call diagnostics artifact writing.",
    )
    parser.add_argument(
        "--sequential-diagnostics",
        action="store_true",
        help="Run one-tier single-worker sequential diagnostics cycle.",
    )
    parser.add_argument(
        "--tier",
        type=str,
        default="tier1",
        choices=("tier1", "tier2", "tier3"),
        help="Tier for sequential diagnostics mode.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print summaries as JSON.",
    )
    parser.add_argument(
        "--night-run-mode",
        choices=("batch", "long", "resume"),
        default=None,
        help="Run long unattended tier1 sweep mode.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional run id for night-run mode. Required for resume.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Override max cases for night-run mode.",
    )
    parser.add_argument(
        "--max-duration-seconds",
        type=int,
        default=None,
        help="Override max wall-clock duration for night-run mode.",
    )
    parser.add_argument(
        "--scheduler-mode",
        choices=("balanced_round_robin", "weighted"),
        default=None,
        help="Override family scheduler mode for night-run mode.",
    )
    parser.add_argument(
        "--family-weights-json",
        type=str,
        default=None,
        help="JSON object with per-family weights.",
    )
    parser.add_argument(
        "--family-quotas-json",
        type=str,
        default=None,
        help="JSON object with per-family quotas.",
    )
    parser.add_argument(
        "--family-min-share-json",
        type=str,
        default=None,
        help="JSON object with per-family min share.",
    )
    parser.add_argument(
        "--family-max-share-json",
        type=str,
        default=None,
        help="JSON object with per-family max share.",
    )
    parser.add_argument(
        "--warmup-cases",
        type=int,
        default=None,
        help="Override warm-up case count for night-run mode.",
    )
    parser.add_argument(
        "--disable-warmup",
        action="store_true",
        help="Disable warm-up phase for night-run mode.",
    )
    return parser


def _load_config(path: Path | None) -> ReviewerPipelineConfig:
    if path is None:
        return ReviewerPipelineConfig.default()
    return ReviewerPipelineConfig.load(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.write_default_config is not None:
        ReviewerPipelineConfig.default().save(args.write_default_config)
        return 0

    config = _load_config(args.config)
    if args.diagnostic_mode:
        config.diagnostic_mode = True
    if args.scheduler_mode is not None:
        config.night_run.scheduler.mode = args.scheduler_mode
    if args.family_weights_json:
        config.night_run.scheduler.family_weights = dict(json.loads(args.family_weights_json))
    if args.family_quotas_json:
        config.night_run.scheduler.family_quotas = {
            str(key): int(value)
            for key, value in dict(json.loads(args.family_quotas_json)).items()
        }
    if args.family_min_share_json:
        config.night_run.scheduler.family_min_share = {
            str(key): float(value)
            for key, value in dict(json.loads(args.family_min_share_json)).items()
        }
    if args.family_max_share_json:
        config.night_run.scheduler.family_max_share = {
            str(key): float(value)
            for key, value in dict(json.loads(args.family_max_share_json)).items()
        }
    if args.warmup_cases is not None:
        config.night_run.warmup.case_count = int(args.warmup_cases)
    if args.disable_warmup:
        config.night_run.warmup.enabled = False
    pipeline = LocalStatelessReviewerPipeline(config=config)

    def _stop_handler(_sig, _frame) -> None:  # noqa: ANN001
        pipeline.stop()

    signal.signal(signal.SIGINT, _stop_handler)
    signal.signal(signal.SIGTERM, _stop_handler)

    themes = None
    if args.themes:
        themes = [item.strip() for item in args.themes.split(",") if item.strip()]

    if args.night_run_mode is not None:
        controller = NightRunController(pipeline=pipeline, config=config)
        summary = controller.run(
            mode=("long" if args.night_run_mode == "resume" else args.night_run_mode),
            run_id=args.run_id,
            max_cases=args.max_cases,
            max_duration_seconds=args.max_duration_seconds,
            themes=themes,
            resume=(args.night_run_mode == "resume"),
        )
    elif args.sequential_diagnostics:
        summary = pipeline.run_sequential_diagnostics(
            tier_name=args.tier,
            case_count=args.case_count or 1,
            themes=themes,
        )
    elif args.continuous:
        pipeline.run_forever()
        summary = pipeline.latest_status()
    else:
        summary = pipeline.run_cycle(case_count=args.case_count, themes=themes)

    if args.json_output:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        for key, value in summary.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
