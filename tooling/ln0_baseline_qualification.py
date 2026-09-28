#!/usr/bin/env python3
"""Deterministic orchestrator for accepted LN-0 contracts and composition evidence.

Does not implement any V contract. Full command output is preserved under /tmp;
the runner prints compact per-gate outcomes and never hides unavailable gates.
"""
from __future__ import annotations

import hashlib
import argparse
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/life-notebook/LN0_BASELINE_MANIFEST.md"
EXPECTED_MANIFEST_SHA256 = "573bda53f6a427f3ca793b067e54c789da58a8b38863e3dfd4ea42810717670d"
ARTIFACT_HASHES = {
    "experiments/ln0_migration_spike.py": "f9356c9384b554d21151f7059bf74e0db5b58a2e6cd2710ca08e522dad210986",
    "tests/test_ln0_migration_spike.py": "20ae7cb4b845e2c1b61c544522da6b4da339afee9d6b6ec97c9dc4ad94187f9e",
    "experiments/ln0_sqlcipher_spike_v2.py": "8500b07b4ca159ca297a92ac034124427600f27e78c8f5c24320ee9d23139d84",
    "docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md": "a335daa5fc99595a60dc0644d25697598ed52c69822fafa441b672a15818c02e",
    "experiments/ln0_v03_ingestor.py": "57b3916a316543de8afc928e3784189fc7bf9baccf6ae3ecfb7d73ca14420c50",
    "tests/test_ln0_v03_ingestor.py": "b3f1f482c2c8c1f9a751643539bd1bc725b3c41a2ca639dccaae07e95d5771a6",
    "experiments/ln0_v04_deletion_fanout.py": "8f1778684918174ad36e741d14cd902b3eab1a01da7dbb2a07daedc097386c39",
    "tests/test_ln0_v04_deletion_fanout.py": "e91c4c487da1acdaca1c1c7742e0d45ddff5657c8f6359c5501fc0be2d8e4e03",
    "experiments/ln0_v05_context_boundary.py": "7a1aebf8d6556ee8c6380340759794bfd0854df94861b2a3e216bb552a5c7693",
    "tests/test_ln0_v05_context_boundary.py": "8fc5427ec9502a50f2d585a9830ece9f1dbbccdbd85e377eb0584b05fd794333",
    "docs/life-notebook/LN0_COMPOSITION_CONTRACT.md": "75edcb4c9728bb248b7c0ae48bcb7ad95e055116ee333ced24a08a711677eefa",
    "experiments/ln0_composition_harness.py": "a7f36691448c5ab07234234ed93faadfba15fe8676876a22f83ac2d227c0ac01",
    "tests/test_ln0_cross_v_lifecycle.py": "d2f6b3e07281eabdbbdb42822c38084c5ea444570b4818b299cb0a41608df90c",
    "tests/test_ln0_qualification_runner.py": "c8bfdcd24e9d6ee82b3d25dd118553603435cb304ea90c62868b8869d6d6fdb8",
}


@dataclass
class Gate:
    name: str
    command: list[str]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def matches_sha256(path: Path, expected: str) -> bool:
    try:
        return sha256_file(path) == expected
    except OSError:
        return False


def verify_manifest_hash(path: Path, expected: str) -> tuple[bool, str]:
    actual = sha256_file(path)
    return actual == expected, actual


def _gates(python: str, v02_python: str) -> list[Gate]:
    return [
        Gate("V-01 focused", [python, "-m", "unittest", "tests.test_ln0_migration_spike", "-v"]),
        Gate("V-02 target SQLCipher proof", [v02_python, "experiments/ln0_sqlcipher_spike_v2.py"]),
        Gate("V-03 focused", [python, "-m", "unittest", "tests.test_ln0_v03_ingestor", "-v"]),
        Gate("V-04 Attempt 8 focused", [python, "-W", "error::ResourceWarning", "-m", "unittest", "tests.test_ln0_v04_deletion_fanout", "-v"]),
        Gate("V-05 Pass 4 focused", [python, "-m", "unittest", "tests.test_ln0_v05_context_boundary", "-v"]),
        Gate("composition lifecycle", [python, "-m", "unittest", "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_cross_v_lifecycle_shared_store_stale_context_erasure_and_restore", "-v"]),
        Gate("composition adversarial", [python, "-m", "unittest",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_old_packet_rejected_when_provider_or_privacy_authority_changes",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_migration_capability_and_owner_erase_authority_fail_closed",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_packet_issuer_provider_one_shot_and_expiry_are_core_checked",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_context_request_is_single_use_and_provider_bound",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_connector_claims_cannot_authorize_or_classify_for_hosting",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_migration_hosted_claim_is_not_authorization_and_core_grant_is",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_lineage_drives_transformed_derivative_fanout",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_unlineaged_erased_bytes_fail_closed_even_after_lineage_fanout",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_unidentified_exact_duplicate_payload_is_not_exempt",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_core_named_independent_exact_payload_cell_may_survive",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_core_named_independent_embedded_copy_is_not_exempt",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_restore_rechecks_erased_receipt_and_stays_quarantined_on_resurrection",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_all_store_scan_covers_auxiliary_content_field",
             "tests.test_ln0_cross_v_lifecycle.LN0CrossVCompositionTests.test_sqlcipher_snapshot_scans_serialized_kernel_state", "-v"]),
        Gate("manifest-tamper adversarial", [python, "-m", "unittest", "tests.test_ln0_qualification_runner", "-v"]),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--v02-python", default=os.environ.get("LN0_V02_PYTHON") or sys.executable,
        help="Python interpreter with the accepted V-02 proof prerequisites; also configurable via LN0_V02_PYTHON (default: current interpreter)",
    )
    args = parser.parse_args()
    python = sys.executable
    v02_python = args.v02_python
    report_dir = Path(tempfile.mkdtemp(prefix="ln0-baseline-qualification-"))
    print(f"Full command output: {report_dir}")
    failures = 0

    print("[hashes] verifying canonical frozen artifacts and manifest declarations")
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    for relative, expected in ARTIFACT_HASHES.items():
        path = ROOT / relative
        declared = expected in manifest_text
        actual = sha256_file(path) if path.is_file() else "MISSING"
        passed = declared and actual == expected
        print(f"  {'PASS' if passed else 'FAIL'} {relative}: {actual}; declared={declared}")
        failures += not passed
    if EXPECTED_MANIFEST_SHA256:
        passed, actual = verify_manifest_hash(MANIFEST, EXPECTED_MANIFEST_SHA256)
        print(f"  {'PASS' if passed else 'FAIL'} manifest SHA-256: {actual}")
        failures += not passed
    else:
        print("  INCOMPLETE manifest self-hash constant not frozen yet")
        failures += 1

    for index, gate in enumerate(_gates(python, v02_python), 1):
        env = dict(os.environ)
        env["PYTHONPYCACHEPREFIX"] = str(report_dir / "pycache")
        try:
            result = subprocess.run(gate.command, cwd=ROOT, env=env, text=True,
                                    capture_output=True, timeout=1800, check=False)
            output = result.stdout + result.stderr
            (report_dir / f"{index:02d}-gate.txt").write_text(
                f"COMMAND: {gate.command!r}\nEXIT: {result.returncode}\n\n{output}",
                encoding="utf-8")
            status = "PASS" if result.returncode == 0 else "FAIL"
            failures += result.returncode != 0
            tail = [line for line in output.splitlines() if line.strip()][-3:]
            print(f"[{status}] {gate.name} (exit {result.returncode})")
            for line in tail:
                print(f"  {line[:240]}")
        except (OSError, subprocess.TimeoutExpired) as error:
            (report_dir / f"{index:02d}-gate.txt").write_text(
                f"COMMAND: {gate.command!r}\nUNAVAILABLE: {error!r}\n", encoding="utf-8")
            print(f"[UNAVAILABLE] {gate.name}: {error}")
            failures += 1

    if failures:
        print(f"QUALIFICATION FOCUSED GATES: FAIL/INCOMPLETE ({failures} gate issue(s))")
        print("Broad suite not run: all focused and adversarial gates must pass first.")
        return 1

    # Exactly one broad run per frozen qualification invocation.
    command = [python, "-m", "unittest", "discover", "-s", "tests", "-v"]
    env = dict(os.environ)
    env["PYTHONPYCACHEPREFIX"] = str(report_dir / "pycache")
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True,
                            timeout=3600, check=False)
    output = result.stdout + result.stderr
    (report_dir / "99-broad-suite.txt").write_text(
        f"COMMAND: {command!r}\nEXIT: {result.returncode}\n\n{output}", encoding="utf-8")
    tail = [line for line in output.splitlines() if line.strip()][-12:]
    print(f"[{'PASS' if result.returncode == 0 else 'FAIL'}] broad suite (exit {result.returncode})")
    for line in tail:
        print(f"  {line[:240]}")
    print("If the sole broad error is test_swarm.SwarmTests.test_live_loopback_and_attribution,")
    print("run that exact test once in native host context; never convert it to a skip here.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
