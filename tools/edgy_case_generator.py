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

from reviewer.case_generator import SeededCaseGenerator


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate seeded edgy runtime-trace case(s)."
    )
    parser.add_argument("--seed", type=int, required=True, help="Base seed.")
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of cases to generate from consecutive seeds.",
    )
    parser.add_argument(
        "--theme",
        default=None,
        help="Optional scenario family filter.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for generated trace files.",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Print generated case records as JSON.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    generator = SeededCaseGenerator()
    cases = []
    for offset in range(max(1, args.count)):
        case = generator.generate_case(
            seed=args.seed + offset,
            theme=args.theme,
            traces_output_dir=args.output_dir,
        )
        cases.append(case)

    if args.json_output:
        print(
            json.dumps(
                [
                    {
                        "case_id": case.case_id,
                        "seed": case.seed,
                        "theme": case.theme,
                        "scenario_family": case.scenario_family,
                        "trace_path": case.trace_path,
                        "generation_params": case.generation_params,
                    }
                    for case in cases
                ],
                ensure_ascii=False,
            )
        )
    else:
        for case in cases:
            print(f"case_id={case.case_id}")
            print(f"seed={case.seed}")
            print(f"theme={case.theme}")
            print(f"trace_path={case.trace_path}")
            print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
