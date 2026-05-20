from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    base_dir = Path(__file__).resolve().parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    from roadmap_tracker.cli import main as cli_main

    return int(cli_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
