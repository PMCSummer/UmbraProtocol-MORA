from __future__ import annotations

import argparse
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
from reviewer.ui import launch_ui


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch local reviewer UI.")
    parser.add_argument("--config", type=Path, default=None, help="Optional config JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = (
        ReviewerPipelineConfig.default()
        if args.config is None
        else ReviewerPipelineConfig.load(args.config)
    )
    return launch_ui(config=config)


if __name__ == "__main__":
    raise SystemExit(main())
