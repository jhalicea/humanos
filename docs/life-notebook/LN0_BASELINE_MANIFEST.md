# LN-0 Current Baseline Manifest

Status: test-only composition remediation requalified; external review resubmission
pending. This manifest is not an LN-0 closure or implementation-readiness decision.

## Qualification baseline

- Branch: `ln0-baseline-qualification`
- Baseline commit: `2d034a235c90ef56d40be4c4d355fe419da5891a`
- Canonical source baseline: `life-notebook-ln0` after V2 closure-contract
  reconciliation.
- Focused qualification command: `python3 tooling/ln0_baseline_qualification.py`
- Broad qualification command: `python3 -m unittest discover -s tests -v`
- Environment assumptions: Python 3.13; target-Mac SQLCipher CLI 4.19.0 as
  recorded in the canonical target evidence. The runner accepts the V-02 interpreter
  through `--v02-python` or `LN0_V02_PYTHON`, otherwise tries the current interpreter
  and fails closed if prerequisites are unavailable. `sqlcipher` must be discoverable
  on the caller's `PATH`. Homebrew and venvs are workstation development tooling
  only, not HumanOS runtime, production, or deployment dependencies.

## Accepted verification packets

Historical rejected candidates remain evidence and are not the current baseline.

| Packet | Purpose / accepted contract | Accepted candidate / revision | Fixture and tests | Canonical SHA-256 | Required focused command / expected result | Acceptance evidence / commit | Dependencies and limitations |
|---|---|---|---|---|---|---|---|
| V-01 | Synthetic current-schema migration preserves exact evidence, identities, provenance, unresolved recovery/privacy records, duplicate-event identity, idempotency, and conflict failure. | Previously accepted V-01 result; accepted artifacts frozen during this LN-0 Baseline Qualification. | `experiments/ln0_migration_spike.py`; `tests/test_ln0_migration_spike.py` | Fixture `f9356c9384b554d21151f7059bf74e0db5b58a2e6cd2710ca08e522dad210986`; tests `20ae7cb4b845e2c1b61c544522da6b4da339afee9d6b6ec97c9dc4ad94187f9e`. These current hashes equal the bytes at accepted CI-tested commit `94be3b4cb34bacad23106044a5afc213d53fcc50`. | `python3 -m unittest tests.test_ln0_migration_spike -v` — PASS expected. | GitHub run `36216014250`, tested commit `94be3b4cb34bacad23106044a5afc213d53fcc50`, four matrix jobs successful. A distinct promotion commit is not identified in the canonical result. | Synthetic fixture only; does not prove every live/owner Notebook edge case, migration duration, or final schema performance. Uses standard Python/SQLite fixture interfaces. |
| V-02 | Encrypted SQLite / SQLCipher feasibility: encrypted create/readback, wrong-key and standard-SQLite rejection, WAL/SHM scanning, crash behavior, encrypted export/restore, and synthetic independent recovery-wrapper round trip. | Revision 2; target Mac proof accepted. | `experiments/ln0_sqlcipher_spike_v2.py`; `tests/test_ln0_sqlcipher_spike_v2.py`; target evidence `docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md` | Spike SHA-256 `8500b07b4ca159ca297a92ac034124427600f27e78c8f5c24320ee9d23139d84`; tracked target-evidence SHA-256 `a335daa5fc99595a60dc0644d25697598ed52c69822fafa441b672a15818c02e`. No canonical frozen hash for the test file. | `python3 tooling/ln0_baseline_qualification.py --v02-python <interpreter>` (or `LN0_V02_PYTHON=<interpreter>`); `sqlcipher` must be on caller `PATH`. Exit 0 / JSON `status=PASS` expected with prerequisites. | GitHub run `36216565273`, job `108333571688`, tested commit `7b83d797c6310ae3d4432bc8e4c733b073b06a66`; target Mac proof in canonical evidence. | macOS 26.6.2 arm64, SQLCipher 4.19.0 community. Does not qualify runtime binding, Keychain, KDF/custody/rotation, rollback-journal mode, temp-file packaging, or production/deployment behavior. Homebrew is tooling only. |
| V-03 | Authenticated Core/Ingestor authority; idempotency and conflicting-key rejection; serialized sequence/hash ancestry; crash and projection behavior. | Attempt 5 PASS WITH FINDINGS / promoted. | `experiments/ln0_v03_ingestor.py`; `tests/test_ln0_v03_ingestor.py` | Fixture `57b3916a316543de8afc928e3784189fc7bf9baccf6ae3ecfb7d73ca14420c50`; tests `b3f1f482c2c8c1f9a751643539bd1bc725b3c41a2ca639dccaae07e95d5771a6`. | `python3 -m unittest tests.test_ln0_v03_ingestor -v` — 8/8 PASS expected. | Promotion commit `c3a52d2eb8eee287c25c77f43ec1eb1449fe97c6`. | Synthetic isolated fixture; no separate persisted payload-store/orphan claim; not production authentication/runtime. |
| V-04 | Attempt 8 authorized erasure, derivative fan-out, deletion receipts/structural chronology, recovery and restore barriers, including embedded-byte matching. | Attempt 8 PASS / promoted; Attempts 1–7 remain rejected historical evidence. | `experiments/ln0_v04_deletion_fanout.py`; `tests/test_ln0_v04_deletion_fanout.py` | Fixture `8f1778684918174ad36e741d14cd902b3eab1a01da7dbb2a07daedc097386c39`; tests `e91c4c487da1acdaca1c1c7742e0d45ddff5657c8f6359c5501fc0be2d8e4e03`. | `python3 -W error::ResourceWarning -m unittest tests.test_ln0_v04_deletion_fanout -v` — 26/26 PASS expected. | Promotion commit `e793aca454c087cb68503cb79871a844eb7bde03`. | Synthetic logical-erasure contract only; no physical SQLite remanence proof; not an integration with V-03 storage. |
| V-05 | Core-controlled explicit hosted disclosure authorization; provider-denied/local-only filtering, initial and ContextRequest recompilation enforcement, no content-based DLP claim. | Pass 4 PASS / externally reviewed and promoted. | `experiments/ln0_v05_context_boundary.py`; `tests/test_ln0_v05_context_boundary.py` | Fixture `7a1aebf8d6556ee8c6380340759794bfd0854df94861b2a3e216bb552a5c7693`; tests `8fc5427ec9502a50f2d585a9830ece9f1dbbccdbd85e377eb0584b05fd794333`. | `python3 -m unittest tests.test_ln0_v05_context_boundary -v` — 31/31 PASS expected. | Promotion commit `5eec801abc498a0325350004b7a816cfac1a5bb8`. | Synthetic provider boundary only. Does not prove automatic plaintext DLP, real provider integration, OS/process isolation, or owner Notebook behavior. |

## Composition qualification evidence (distinct from accepted V proofs)

These are new synthetic composition artifacts; their hashes freeze the current
qualification candidate, not prior V-01–V-05 history.

| Artifact | SHA-256 | Exact command / expected result |
|---|---|---|
| `docs/life-notebook/LN0_COMPOSITION_CONTRACT.md` | `75edcb4c9728bb248b7c0ae48bcb7ad95e055116ee333ced24a08a711677eefa` | Core-named independent-source identity, unconditional restore revalidation, schema-enumerated all-store scan; `git diff --check` |
| `experiments/ln0_composition_harness.py` | `a7f36691448c5ab07234234ed93faadfba15fe8676876a22f83ac2d227c0ac01` | Test-only shared KernelStore; external Core authority binds exemption to exact event/object IDs; every restore replays checkpoints |
| `tests/test_ln0_cross_v_lifecycle.py` | `d2f6b3e07281eabdbbdb42822c38084c5ea444570b4818b299cb0a41608df90c` | `PYTHONPYCACHEPREFIX=/tmp/ln0-qualification-pycache python3 -m unittest tests.test_ln0_cross_v_lifecycle -v` — 15/15 PASS |
| `tests/test_ln0_qualification_runner.py` | `c8bfdcd24e9d6ee82b3d25dd118553603435cb304ea90c62868b8869d6d6fdb8` | `PYTHONPYCACHEPREFIX=/tmp/ln0-qualification-pycache python3 -m unittest tests.test_ln0_qualification_runner -v` — tampered manifest rejected |
| `tooling/ln0_baseline_qualification.py` | Recorded after runner freeze in qualification evidence | `python3 tooling/ln0_baseline_qualification.py --v02-python <interpreter>` (or `LN0_V02_PYTHON`); each V/composition gate independently reported; broad suite once only after focused/adversarial gates pass |

Accepted individual contract evidence is V-01 through V-05 above. Composition
qualification evidence is the contract, test-only shared-store harness, and
cross-V tests above. Production functionality and production SQLCipher binding remain
deferred to LN-1 and mandatory PRE-LN-1 ADRs.

## Target storage evidence

- SQLCipher: 4.19.0 community; target: macOS 26.6.2, arm64; executable:
  `/opt/homebrew/bin/sqlcipher`.
- Canonical proof: `docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md`, SHA-256
  `a335daa5fc99595a60dc0644d25697598ed52c69822fafa441b672a15818c02e`.
- The proof is synthetic and bounded; it does not establish production key custody
  or deployment portability.

### V-01 qualification-era baseline freeze

V-01 was accepted previously. The SHA-256 values above were established during the
LN-0 Baseline Qualification as the canonical current-baseline freeze. They are not
represented as hashes historically recorded at the time of V-01 acceptance. The
current fixture and test files were byte-compared with the corresponding artifacts
at the canonical accepted CI-tested commit `94be3b4cb34bacad23106044a5afc213d53fcc50`.

## Mandatory PRE-LN-1 ADR gates

1. Schema/Integrity ADR: exact deletion-safe payload commitment representation;
   `event_hash` payload coverage; `content_hash` lifecycle; erasure and idempotency /
   duplicate semantics; backup/restore behavior; and V-04 ErasureTag interaction.
   Reviewed acceptance is required before event/payload schema persistence or real
   capture.
2. SQLCipher / key-custody ADR: runtime binding/packaging, key creation and
   wrapping/recovery authority, KDF/Keychain or target equivalent, rotation, backup,
   deletion, WAL and crash behavior. Reviewed acceptance is required before
   production encrypted-kernel implementation.

## Environment-dependent and historical evidence

- Earlier candidate broad runs recorded 657 and 661 tests / 11 skipped / the known
  restricted-sandbox loopback `PermissionError`. This final remediation's one broad
  run recorded 666 tests / 11 skipped / the same sole error. The exact test's existing
  native 1/1 PASS remains valid because its source/hash did not change; it was not
  rerun. Full remediation output is preserved in its runner `/tmp` evidence directory.
- V-01 had no historical pre-qualification fixture/test freeze. The SHA-256 values
  recorded in this manifest were established during qualification as the canonical
  current-baseline freeze after byte comparison with accepted CI-tested artifacts.
  They are qualification-era baseline hashes, not historical acceptance-time evidence.
- Prior rejected V-03 attempts, V-02 rejected runtime-binding candidate, V-04
  Attempts 1–7, and prior V-05 failed/remediation passes remain historical evidence;
  they are not the current accepted baseline.
