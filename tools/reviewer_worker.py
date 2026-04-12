from __future__ import annotations

import argparse
import json
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
from reviewer.pipeline import LocalStatelessReviewerPipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one stateless reviewer worker slice."
    )
    parser.add_argument("--config", type=Path, default=None, help="Optional config path.")
    parser.add_argument("--seed", type=int, required=True, help="Seed for generated case.")
    parser.add_argument("--theme", type=str, default=None, help="Optional theme filter.")
    parser.add_argument(
        "--tier",
        type=str,
        default="tier1",
        choices=("tier1", "tier2", "tier3"),
        help="Single tier to execute.",
    )
    parser.add_argument("--json", dest="json_output", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = (
        ReviewerPipelineConfig.default()
        if args.config is None
        else ReviewerPipelineConfig.load(args.config)
    )
    for tier_name, tier_cfg in config.tiers.items():
        tier_cfg.enabled = tier_name == args.tier
    config.generation.base_seed = args.seed
    config.generation.max_cases_per_cycle = 1

    pipeline = LocalStatelessReviewerPipeline(config=config)
    summary = pipeline.run_cycle(case_count=1, themes=[args.theme] if args.theme else None)
    if args.json_output:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        for key, value in summary.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
