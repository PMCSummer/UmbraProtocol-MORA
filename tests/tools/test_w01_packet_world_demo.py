from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_w01_packet_world_demo_smoke_present_and_contradictory() -> None:
    demo = Path("tools/w01_packet_world_demo.py")
    for scenario in ("present", "contradictory"):
        proc = subprocess.run(
            [sys.executable, str(demo), "--scenario", scenario],
            check=False,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        output = proc.stdout
        assert "W01 ADMISSION" in output
        assert "non_mature_object_claim" in output
