from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from substrate.simple_trace import run_tick_and_write_simple_trace


@dataclass(slots=True)
class CliConfig:
    case_id: str
    energy: float
    cognitive: float
    safety: float
    unresolved_preference: bool
    route_class: str
    output_dir: Path
    json_output: bool


def _parse_bool(raw: str) -> bool:
    value = raw.strip().lower()
    if value in {"true", "1", "yes", "y", "on"}:
        return True
    if value in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(
        f"Invalid boolean value: {raw!r}. Use true/false."
    )


def _finite_float(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid float: {raw!r}") from exc

    if not math.isfinite(value):
        raise argparse.ArgumentTypeError(f"Non-finite float is not allowed: {raw!r}")
    return value


def _resolve_unresolved_preference(args: argparse.Namespace) -> bool:
    # Новый удобный CLI:
    #   --prefer-unresolved
    #   --no-prefer-unresolved
    #
    # Legacy-совместимость:
    #   --unresolved-preference true|false
    if args.prefer_unresolved is not None:
        return args.prefer_unresolved
    if args.unresolved_preference is not None:
        return args.unresolved_preference
    raise argparse.ArgumentTypeError(
        "You must specify one of: "
        "--prefer-unresolved / --no-prefer-unresolved "
        "or legacy --unresolved-preference true|false"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a simple per-tick JSONL trace.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--case-id", required=True, help="Subject tick case id.")
    parser.add_argument("--energy", required=True, type=_finite_float, help="Energy value.")
    parser.add_argument(
        "--cognitive",
        required=True,
        type=_finite_float,
        help="Cognitive value.",
    )
    parser.add_argument("--safety", required=True, type=_finite_float, help="Safety value.")

    unresolved_group = parser.add_mutually_exclusive_group(required=False)
    unresolved_group.add_argument(
        "--prefer-unresolved",
        dest="prefer_unresolved",
        action="store_true",
        help="Enable unresolved preference.",
    )
    unresolved_group.add_argument(
        "--no-prefer-unresolved",
        dest="prefer_unresolved",
        action="store_false",
        help="Disable unresolved preference.",
    )
    unresolved_group.add_argument(
        "--unresolved-preference",
        type=_parse_bool,
        help="Legacy compatibility: true/false.",
    )
    parser.set_defaults(prefer_unresolved=None, unresolved_preference=None)

    parser.add_argument(
        "--route-class",
        default="production_contour",
        help="Runtime route class.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Output directory for per-tick JSONL trace.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print result as JSON instead of plain text.",
    )
    return parser


def _parse_args(argv: Sequence[str] | None = None) -> CliConfig:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        unresolved_preference = _resolve_unresolved_preference(args)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    return CliConfig(
        case_id=args.case_id,
        energy=args.energy,
        cognitive=args.cognitive,
        safety=args.safety,
        unresolved_preference=unresolved_preference,
        route_class=args.route_class,
        output_dir=output_dir,
        json_output=args.json_output,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = _parse_args(argv)

        result = run_tick_and_write_simple_trace(
            case_id=config.case_id,
            energy=config.energy,
            cognitive=config.cognitive,
            safety=config.safety,
            unresolved_preference=config.unresolved_preference,
            route_class=config.route_class,
            output_root=config.output_dir,
        )

        if config.json_output:
            print(
                json.dumps(
                    {
                        "tick_id": result["tick_id"],
                        "trace_path": str(result["trace_path"]),
                        "event_count": result["event_count"],
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(f"tick_id={result['tick_id']}")
            print(f"trace_path={result['trace_path']}")
            print(f"event_count={result['event_count']}")

        return 0

    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())