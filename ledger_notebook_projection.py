"""Project verified original ledger turns into the existing Life Notebook.

This is an explicit already-observed import. Ledger adjacency alone never
authorizes pairing across provider or conversation boundaries. Legacy Codex
rollouts may use opaque message IDs; non-Codex observed turns must supply a
shared turn key through the documented role-suffixed source IDs.
"""

from pathlib import Path

from conversation_ledger import read_ledger, verify_ledger
from notebook import Notebook


PROJECTION_VERSION = 1


def _evidence_rows(ledger):
    verify_ledger(ledger)
    return [row for row in read_ledger(ledger)
            if row.get("event_type") != "METADATA_CORRECTION"]


def _pair_matches(human, assistant):
    if (human["source"] != assistant["source"]
            or human["conversation_id"] != assistant["conversation_id"]):
        raise ValueError("Cannot pair messages across source or conversation boundaries")
    # New observed turns carry an explicit stable turn key; legacy Codex
    # rollouts have provider message IDs (u1/a1), not matching turn IDs.
    if human["source"] != "codex-rollout":
        h_id, a_id = human["source_id"], assistant["source_id"]
        if (not h_id.endswith(":HUMAN") or not a_id.endswith(":ASSISTANT")
                or h_id[:-6] != a_id[:-10] or not h_id[:-6]):
            raise ValueError("Observed message pair lacks one matching source turn key")


def _preflight_pairs(rows):
    """Validate whole ledger before any Notebook is opened or mutated."""
    pairs = []
    pending = 0
    human = None
    target_ids = set()
    for row in rows:
        if row["role"] == "HUMAN":
            if human is not None:
                pending += 1
            human = row
        elif row["role"] == "ASSISTANT" and human is not None:
            _pair_matches(human, row)
            # Retain original CAPTURE-... format without a schema migration.
            # A reused message ID across providers/conversations must fail,
            # not be incorrectly counted as already projected.
            tx = "CAPTURE-" + row["source_id"]
            if tx in target_ids:
                raise ValueError("Ambiguous projection transaction ID across ledger turns")
            target_ids.add(tx)
            pairs.append((human, row, tx))
            human = None
        else:
            pending += 1
    if human is not None:
        pending += 1
    return pairs, pending


def _projection_state(human, assistant):
    return {
        "phase": "COMPLETE",
        "final": assistant["text"],
        "final_ordinal": 1,
        "model": "codex-rollout" if human["source"] == "codex-rollout" else "observed-source",
        "projection_version": PROJECTION_VERSION,
        "source": human["source"],
        "conversation_id": human["conversation_id"],
        "human_source_id": human["source_id"],
        "assistant_source_id": assistant["source_id"],
    }


def _existing_exact(book, tx, human, assistant):
    """Fail closed before writes on unknown/stale/foreign projection identity."""
    prior = book.get_transaction(tx)
    if prior is None:
        return False
    expected = _projection_state(human, assistant)
    state = book.task(tx)
    # Historical Notebook projections have no authoritative source/turn
    # identity: never upgrade, overwrite, or assume they belong to this pair.
    if (prior["status"] != "CHECKPOINTED" or prior["input"] != human["text"]
            or state is None or state != expected):
        raise ValueError("Existing projection lacks matching verified source evidence")
    records = book.db.execute(
        "SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,)
    ).fetchall()
    if [(r["role"], r["text"]) for r in records] != [
        ("HUMAN", human["text"]), ("ASSISTANT", assistant["text"])
    ]:
        raise ValueError("Existing projection transcript differs from source evidence")
    identity = book.get_identity(prior["hcid"])
    if identity is None or identity["binding"] != "VERIFIED":
        raise ValueError("Existing projection owner binding is not verified")
    return True


def _project_new(book, tx, human, assistant, *, include_final_phase=False):
    # Caller has already preflighted every existing tx in the full batch.
    identity = book.bind("Jon", human["text"])
    book.start(identity["hcid"], tx, human["text"])
    book.append(tx, 1, "ASSISTANT", assistant["text"])
    state = _projection_state(human, assistant)
    if include_final_phase:
        book.save_task(tx, dict(state, phase="FINAL"))
    book.save_task(tx, state)
    book.checkpoint(tx)
    return identity



def reconcile_one_codex_pair(ledger, notebook_root, human_source_id,
                             assistant_source_id, *, confirm=False):
    """Owner-confirmed, evidence-only completion of an existing partial turn.

    Never create a new transaction, silently rebind a page, invoke a provider,
    or alter the original ledger. Ordinary project_all_pairs stays fail-closed.
    """
    if confirm is not True:
        raise PermissionError("Explicit operator reconciliation confirmation required")
    if (not isinstance(human_source_id, str) or not isinstance(assistant_source_id, str)
            or not human_source_id or not assistant_source_id
            or human_source_id == assistant_source_id):
        raise ValueError("Select two distinct original source record references")
    rows = _evidence_rows(ledger)
    if (len(rows) != 2 or [row["role"] for row in rows] != ["HUMAN", "ASSISTANT"]
            or any(row["source"] != "codex-rollout" for row in rows)):
        raise ValueError("Reconciliation requires exactly one preserved Codex turn")
    pairs, pending = _preflight_pairs(rows)
    if (len(pairs) != 1 or pending != 0
            or [rows[0]["source_id"], rows[1]["source_id"]]
            != [human_source_id, assistant_source_id]):
        raise ValueError("Selected recovery identities do not match ledger evidence")
    human, assistant, tx = pairs[0]
    # Do not permit Notebook(...) to create a vault during reconciliation.
    root = Path(notebook_root)
    if not root.is_dir() or not (root / "runtime" / "notebook.sqlite3").is_file():
        raise ValueError("An existing incomplete Notebook is required")

    book = Notebook(root)
    try:
        book.verify()
        prior = book.get_transaction(tx)
        if prior is None:
            raise ValueError("Refuse to create a new Notebook transaction during recovery")
        if prior["status"] == "CHECKPOINTED":
            _existing_exact(book, tx, human, assistant)
            return {"status": "ALREADY_RECONCILED", "transaction": tx, "appended": 0}
        if prior["status"] != "STARTED" or prior["input"] != human["text"]:
            raise ValueError("Notebook transaction status/input is not safe to reconcile")
        identity = book.get_identity(prior["hcid"])
        if (identity is None or identity["binding"] != "VERIFIED"
                or identity["owner"] != "Jon"
                or not book.digest_matches(identity["opening_hash"], human["text"])):
            raise ValueError("Original Notebook binding is not verified")
        expected_state = _projection_state(human, assistant)
        old_state = book.task(tx)
        if old_state is not None and old_state != expected_state:
            raise ValueError("Existing Notebook task does not match selected evidence")
        transcript = [(r["role"], r["text"]) for r in book.db.execute(
            "SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,)
        )]
        if transcript not in ([
            ("HUMAN", human["text"])
        ], [
            ("HUMAN", human["text"]), ("ASSISTANT", assistant["text"])
        ]):
            raise ValueError("Incomplete Notebook transcript does not match ledger")
        # Append an evidence-only approval marker before attempting completion.
        # Command confirmation is NOT a cryptographic proof of operator identity.
        book.event(tx, "CODEX_RECONCILIATION_CONFIRMED",
                   {"source": "codex-rollout", "operator_confirmation": True})
        if len(transcript) == 1:
            book.append(tx, 1, "ASSISTANT", assistant["text"])
        book.save_task(tx, expected_state)
        book.checkpoint(tx)
        if not _existing_exact(book, tx, human, assistant):
            raise RuntimeError("Reconciled Notebook verification failed")
        return {"status": "MANUALLY_RECONCILED", "transaction": tx,
                "appended": int(len(transcript) == 1)}
    finally:
        book.close()



def project_one_pair(ledger, notebook_root):
    rows = _evidence_rows(ledger)
    if len(rows) < 2 or rows[0]["role"] != "HUMAN" or rows[1]["role"] != "ASSISTANT":
        raise ValueError("ledger must begin with one HUMAN/ASSISTANT pair")
    pairs, _ = _preflight_pairs(rows)
    if not pairs:
        raise ValueError("ledger has no complete matched turn")
    human, assistant, tx = pairs[0]
    book = Notebook(Path(notebook_root))
    try:
        if _existing_exact(book, tx, human, assistant):
            return {"status": "ALREADY_PROJECTED", "tx": tx}
        identity = _project_new(book, tx, human, assistant, include_final_phase=True)
        return {"status": "CHECKPOINTED", "tx": tx, "page": identity["page"]}
    finally:
        book.close()


def project_all_pairs(ledger, notebook_root=None, book=None):
    rows = _evidence_rows(ledger)
    pairs, pending = _preflight_pairs(rows)
    projected = 0
    skipped = 0
    owned = book is None
    book = book or Notebook(Path(notebook_root))
    try:
        # A collision with an existing/legacy record is rejected before
        # creating any identity or partially processing a later pair.
        existing = {_tx: _existing_exact(book, _tx, human, assistant)
                    for human, assistant, _tx in pairs}
        for human, assistant, tx in pairs:
            if existing[tx]:
                skipped += 1
                continue
            _project_new(book, tx, human, assistant)
            projected += 1
        return {"status": "CHECKPOINTED" if not pending else "PENDING",
                "projected": projected, "skipped": skipped, "pending": pending}
    finally:
        if owned:
            book.close()
