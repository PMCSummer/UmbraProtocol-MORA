from __future__ import annotations

import argparse
from pathlib import Path

from substrate.simple_trace import run_tick_and_write_simple_trace


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate simple per-tick JSONL trace."
    )
    parser.add_argument("--case-id", required=True, help="subject tick case id")
    parser.add_argument("--energy", required=True, type=float)
    parser.add_argument("--cognitive", required=True, type=float)
    parser.add_argument("--safety", required=True, type=float)
    parser.add_argument(
        "--unresolved-preference",
        required=True,
        type=str,
        help="true/false",
    )
    parser.add_argument(
        "--route-class",
        default="production_contour",
        help="runtime route class (default production_contour)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="output directory for per-tick jsonl trace",
    )
    return parser


def _parse_bool(raw: str) -> bool:
    lower = raw.strip().lower()
    if lower in {"true", "1", "yes", "y"}:
        return True
    if lower in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean literal: {raw}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_tick_and_write_simple_trace(
        case_id=args.case_id,
        energy=args.energy,
        cognitive=args.cognitive,
        safety=args.safety,
        unresolved_preference=_parse_bool(args.unresolved_preference),
        route_class=args.route_class,
        output_root=Path(args.output_dir),
    )
    print(f"tick_id={result['tick_id']}")
    print(f"trace_path={result['trace_path']}")
    print(f"event_count={result['event_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
