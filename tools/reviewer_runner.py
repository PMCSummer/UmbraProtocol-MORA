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
        "--json",
        dest="json_output",
        action="store_true",
        help="Print summaries as JSON.",
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
    pipeline = LocalStatelessReviewerPipeline(config=config)

    def _stop_handler(_sig, _frame) -> None:  # noqa: ANN001
        pipeline.stop()

    signal.signal(signal.SIGINT, _stop_handler)
    signal.signal(signal.SIGTERM, _stop_handler)

    themes = None
    if args.themes:
        themes = [item.strip() for item in args.themes.split(",") if item.strip()]

    if args.continuous:
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
