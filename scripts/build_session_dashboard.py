#!/usr/bin/env python3
"""CLI wrapper for the session dashboard skill script."""

from __future__ import annotations

import runpy
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "session-dashboard"
    / "scripts"
    / "build_session_dashboard.py"
)


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
