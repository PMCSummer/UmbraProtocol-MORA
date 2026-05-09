from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_m01_imprint_demo_smoke() -> None:
    demo = Path("tools/m01_imprint_demo.py")
    for scenario in ("neutral", "strain", "relief", "external_noise", "repeated_pattern"):
        proc = subprocess.run(
            [sys.executable, str(demo), "--scenario", scenario],
            check=False,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0
        output = proc.stdout
        assert "M01 HOMEOSTATIC IMPRINT DEMO" in output
        assert "decision=" in output
        assert "retention_bias=" in output
        assert "no_claim_markers=" in output
