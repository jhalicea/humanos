#!/usr/bin/env python3
"""Synthetic-only owner-host rehearsal for exact Codex recovery kill points.

Runs the repository's synthetic import smoke and the dedicated interruption/
reconciliation tests. Source and Notebook test fixtures use TemporaryDirectory;
this script never discovers real Codex sessions or an existing owner vault.
"""
import os
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
TEST = REPO / "tests" / "test_codex_import_interruption.py"
IMPORT_SMOKE = REPO / "scripts" / "smoke_codex_import.py"


def must(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(args):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(args, cwd=REPO, env=env, capture_output=True,
                          text=True, check=False, timeout=120)


def main():
    must(TEST.is_file() and IMPORT_SMOKE.is_file() and (REPO / "humanos.py").is_file(),
         "HumanOS synthetic acceptance files missing")
    first = run([sys.executable, str(IMPORT_SMOKE)])
    must(first.returncode == 0 and "synthetic Codex import smoke: PASS" in first.stdout,
         "Original Codex import synthetic smoke failed:\n" + first.stderr)
    second = run([sys.executable, "-m", "unittest", "discover",
                  "-s", str(REPO / "tests"), "-p",
                  "test_codex_import_interruption.py", "-v"])
    match = re.search(r"Ran (\d+) tests in", second.stderr)
    must(second.returncode == 0 and match is not None and int(match.group(1)) == 10
         and re.search(r"^OK$", second.stderr, re.MULTILINE),
         "Codex recovery interruption tests failed:\n" + second.stderr)
    print("synthetic Codex import smoke: PASS")
    print("synthetic Codex recovery and reconciliation: 10/10 PASS")
    print("SYNTHETIC OWNER-HOST REHEARSAL: PASS")


if __name__ == "__main__":
    main()
