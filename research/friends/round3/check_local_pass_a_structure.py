#!/usr/bin/env python3
"""Structure-only checker for EXP-R3-A-001 local outputs.

This checker intentionally avoids substantive analysis. It recognizes semantically
valid section-label variants such as 'Finding 1: Sovereignty Paradox' instead of
requiring the literal string 'TRIAL 1'. It prints structure only.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TRIAL_TITLES = [
    "SOVEREIGNTY PARADOX",
    "CONSENT COLLAPSE",
    "RIGHTS COLLIDE",
    "CONSTITUTIONAL CAPTURE",
    "PATERNALISM TRAP",
    "MANIPULATION BY THE HELPFUL SYSTEM",
    "TRUTH VS PRIVACY VS MEMORY",
    "THE SYSTEM IS WRONG",
    "THIRD PARTIES ENTER THE SYSTEM",
    "INCAPACITY, DEATH, SUCCESSION",
    "MODEL SUBORDINATION COULD BE TOO STRONG",
    "TRANSFORMATIVE AI STRESS TEST",
]

MAIN_SECTION_VARIANTS = {
    "TRY TO KILL THE CONSTITUTION": ["TRY TO KILL THE CONSTITUTION", "SELECTED CONSTITUTIONAL IDEAS TO KILL"],
    "PROPOSE THE MINIMUM CHANGE SET": ["PROPOSE THE MINIMUM CHANGE SET", "PROPOSED MINIMUM CHANGE SET"],
    "SCORE THE CONSTITUTION": ["SCORE THE CONSTITUTION"],
    "THE ONE EXPERIMENT": ["THE ONE EXPERIMENT"],
    "FINAL VERDICT": ["FINAL VERDICT"],
}

FINAL_LABELS = [
    "STRONGEST CONSTITUTIONAL IDEA",
    "MOST DANGEROUS CONSTITUTIONAL ASSUMPTION",
    "BIGGEST MISSING RIGHT",
    "BIGGEST MISSING DUTY",
    "MOST IMPORTANT RIGHTS COLLISION",
    "ONE CLAUSE I WOULD REMOVE OR REWRITE",
    "ONE AMENDMENT I WOULD PROPOSE IMMEDIATELY",
    "ONE THING THAT SHOULD NOT BE CONSTITUTIONALIZED",
    "TRANSFORMATIVE-AI VERDICT",
    "WHAT WOULD CHANGE MY MIND",
    "MESSAGE TO THE OTHER FRIENDS",
]


def norm(line: str) -> str:
    line = re.sub(r"^\s*#{1,6}\s*", "", line)
    line = re.sub(r"^\s*\d+[.)]\s*", "", line)
    return re.sub(r"\s+", " ", line.strip().upper())


def contains_any(lines, variants):
    return any(any(v in line for v in variants) for line in lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()

    p = Path(args.path)
    text = p.read_text(encoding="utf-8")
    lines = [norm(x) for x in text.splitlines() if x.strip()]

    print("FILE:", p)
    print("\nTRIAL / FINDING COVERAGE")
    all_ok = True
    for i, title in enumerate(TRIAL_TITLES, 1):
        variants = [f"TRIAL {i}", f"FINDING {i}", title]
        ok = contains_any(lines, variants)
        print(f"{i:2}: {'OK' if ok else 'MISSING'} — {title.title()}")
        all_ok &= ok

    print("\nMAIN SECTIONS")
    for canonical, variants in MAIN_SECTION_VARIANTS.items():
        ok = contains_any(lines, variants)
        print(f"{'OK' if ok else 'MISSING'} — {canonical}")
        all_ok &= ok

    print("\nFINAL VERDICT LABELS")
    final_ok = True
    for label in FINAL_LABELS:
        ok = contains_any(lines, [label])
        print(f"{'OK' if ok else 'MISSING'} — {label}")
        final_ok &= ok

    print("\nSTRUCTURAL RESULT:", "COMPLETE" if all_ok and final_ok else "INCOMPLETE_OR_NEEDS_REVIEW")
    return 0 if all_ok and final_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
