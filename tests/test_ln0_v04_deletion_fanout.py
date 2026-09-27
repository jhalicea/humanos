import hashlib, inspect, json, sqlite3, tempfile, threading, unittest
from pathlib import Path
from experiments.ln0_v04_deletion_fanout import *

class Clock:
 def __init__(self): self.tick=0
 def __call__(self): self.tick+=1; return f"2026-09-26T13:43:{self.tick:02d}.000000+00:00"

class V04Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.n=0
  def oid(): self.n+=1; return f"PO-{self.n:03d}"
  self.f=V04Fixture(Path(self.t.name)/"live.sqlite",clock=Clock(),object_id_factory=oid); f=self.f
  f.event("E1",DELETED,notebook_page_id="PAGE-JOURNAL",page_position=7,block_id="BLOCK-7",original_event_type="NOTE.CREATED",occurred_at="2026-09-26T13:43:00+00:00",captured_at="2026-09-26T13:43:01+00:00",ingested_at="2026-09-26T13:43:02+00:00")
  f.event("E2","SURVIVING_E2",page_position=8); f.event("E1-copy",DELETED,page_position=9); f.event("E3","ratified",authority=OWNER_RATIFIED,page_position=10)
  for kind in ("timeline","page","summary","fts","vector","graph","binary","cache","context"): f.artifact(kind,kind,DELETED,["E1"])
  f.artifact("multi","summary","claim",["E1","E2"]); f.artifact("arbitrary","not-state","ratified",["E3"],required_authority=OWNER_RATIFIED); f.artifact("named-state","state","ordinary",["E2","E3"],required_authority=OWNER_RATIFIED); f.artifact("other","page","SURVIVING_E2",["E2"],partition="p2")
 def tearDown(self): self.t.cleanup()
 def row(self,aid):
  with self.f._db() as c: return c.execute("SELECT body,status,source_event_ids FROM artifacts WHERE id=?",(aid,)).fetchone()
 def delete(self): return self.f.orchestrate_delete("E1",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1")
 def retained(self):
  with self.f._db() as c: return (c.execute("SELECT * FROM tombstones").fetchall(),c.execute("SELECT * FROM audit_events").fetchall(),c.execute("SELECT * FROM deletion_receipts").fetchall(),c.execute("SELECT * FROM receipt_chain_anchors").fetchall())
 def test_storage_authority_and_lineage_remain_generic(self):
  with self.f._db() as c:
   for raw in ("NULL","'[]'","'not-json'","'[\"UNKNOWN\"]'","'[\"E1\",\"E1\"]'"):
    with self.assertRaises(sqlite3.DatabaseError): c.execute("INSERT INTO artifacts VALUES ('bad'+?,'x','p','x',"+raw+",'OBSERVED_EVIDENCE','LIVE')",(raw,))
   with self.assertRaises(sqlite3.DatabaseError): c.execute("UPDATE artifacts SET source_event_ids='[]' WHERE id='multi'")
  self.f.artifact("renamed","anything","x",["E3"],required_authority=OWNER_RATIFIED); actors=("jon","jon","worker"); self.f.tombstone("E3",deletion_id="DEL-E3",actors=actors,committed_at="2026-09-26T14:00:00+00:00"); self.f.resolve("E3"); self.assertEqual(self.row("renamed")[1],"DELETED"); self.assertEqual(self.row("named-state")[1],"DELETED")
 def test_measured_fanout_counts_and_identity_isolation(self):
  self.f.artifact("derivative-copy","summary",DELETED,["E1"]); self.f.artifact("derivative-bytes","cache","SURVIVING_E2",["E2"]); self.assertTrue(self.delete())
  for kind in ("timeline","page","summary","fts","vector","graph","binary","cache","context","derivative-copy"): self.assertEqual(self.row(kind)[1],"DELETED")
  self.assertEqual(self.row("multi")[2],'["E2"]'); self.assertEqual(self.row("other")[1],"LIVE"); r=self.f.receipt_dict("DEL-E1"); self.assertEqual((r["affected_artifact_count"],r["invalidated_artifact_count"],r["recomputed_artifact_count"],r["failed_artifact_count"]),(11,10,1,0)); self.assertFalse(self.f.search_persistent(DELETED,permitted_event_ids=("E1-copy",)))
 def test_low_entropy_plaintext_and_ordinary_hash_absent(self):
  secret=b"synthetic-kernel-secret-for-test"; boundary=KernelCheckpointBoundary(secret); f=V04Fixture(Path(self.t.name)/"low.sqlite",kernel_checkpoint=boundary,clock=Clock()); f.event("LOW","Jon",page_position=11); f.artifact("low-cache","cache",b"Jon",["LOW"]); self.assertTrue(f.orchestrate_delete("LOW",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1")); digest=hashlib.sha256(b"Jon").hexdigest(); checkpoint=boundary.erasure("DEL-LOW"); tag=checkpoint.erasure_tag; self.assertEqual((checkpoint.deletion_id,checkpoint.match_length),("DEL-LOW",3)); self.assertNotEqual(tag,digest); self.assertNotEqual(tag,hashlib.sha256(b"DEL-LOW"+b"Jon").hexdigest()); self.assertNotIn(b"Jon",repr(checkpoint).encode()); self.assertFalse(f.search_persistent("Jon")); self.assertFalse(f.search_persistent(digest)); self.assertFalse(f.search_persistent(tag))
  with f._db() as c:
   self.assertNotIn("payload_hash",[x[1] for x in c.execute("PRAGMA table_info(events)")]); self.assertNotIn(secret,c.serialize())
  self.assertNotIn("Jon",json.dumps(f.receipt_dict("DEL-LOW"))); self.assertNotIn(secret.hex(),json.dumps(f.receipt_dict("DEL-LOW"))); self.assertTrue(f.verify_receipt_chain())

 def test_erasure_tag_sliding_window_edges_repeats_and_binary(self):
  boundary=KernelCheckpointBoundary(b"window-secret-key-material-v04"); checkpoint=boundary.register_erasure("DEL-WINDOW",b"SECRET")
  self.assertEqual(checkpoint.match_length,6)
  for candidate in (b"SECRET",b"SECRET-SUFFIX",b"PREFIX-SECRET",b"PREFIX-SECRET-SUFFIX",b"SECRET+SECRET",b"\x00PREFIX-SECRET-SUFFIX\xff"):
   with self.subTest(candidate=candidate): self.assertTrue(boundary.matches_erased_content("DEL-WINDOW",candidate))
  for candidate in (b"",b"SECRE",b"PREFIX-SUFFIX"):
   with self.subTest(candidate=candidate): self.assertFalse(boundary.matches_erased_content("DEL-WINDOW",candidate))

 def test_completion_rejects_embedded_forbidden_bytes_in_unrelated_artifact(self):
  self.f.artifact("unrelated-embedded","cache",b"PREFIX-"+DELETED.encode()+b"-SUFFIX",["E2"])
  with self.assertRaises(RestoreNotReady): self.delete()
  with self.f._db() as c:
   self.assertEqual(c.execute("SELECT COUNT(*) FROM deletion_receipts WHERE deletion_id='DEL-E1'").fetchone()[0],0)
   self.assertEqual(c.execute("SELECT COUNT(*) FROM audit_events WHERE deletion_id='DEL-E1' AND event_type='ERASE.COMPLETED'").fetchone()[0],0)
   self.assertEqual(c.execute("SELECT COUNT(*) FROM audit_events WHERE deletion_id='DEL-E1' AND event_type='ERASE.RECOVERY_REQUIRED'").fetchone()[0],1)

 def test_restore_detects_embedded_old_backup_copy_before_live(self):
  secret=b"embedded-restore-secret-v04"; boundary=KernelCheckpointBoundary(secret); f=V04Fixture(Path(self.t.name)/"embedded-live.sqlite",kernel_checkpoint=boundary,clock=Clock()); f.event("E1",DELETED); f.event("E2","other"); f.artifact("unrelated-embedded","binary",b"PREFIX-"+DELETED.encode()+b"-SUFFIX",["E2"]); pre=Path(self.t.name)/"embedded-pre.sqlite"; f.backup_to(pre)
  with f._db() as c: c.execute("DELETE FROM artifacts WHERE id='unrelated-embedded'")
  self.assertTrue(f.orchestrate_delete("E1",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1"))
  with f._db() as c: tombs,audits,receipts,anchors=c.execute("SELECT * FROM tombstones").fetchall(),c.execute("SELECT * FROM audit_events").fetchall(),c.execute("SELECT * FROM deletion_receipts").fetchall(),c.execute("SELECT * FROM receipt_chain_anchors").fetchall()
  receipt_state,erasure_state=boundary.restart_state(); restarted=KernelCheckpointBoundary(secret,receipt_checkpoints=receipt_state,erasure_checkpoints=erasure_state); base=V04Fixture(Path(self.t.name)/"embedded-restored.sqlite",kernel_checkpoint=restarted,clock=Clock()); r=base.restore_predelete(pre); r.import_tombstones(tombs); r.import_audit_events(audits); r.import_deletion_receipts(receipts); r.import_receipt_anchors(anchors)
  with self.assertRaises(RestoreNotReady): r.activate_after_replay()
  for public_read in (lambda:r.read_event("E1"),lambda:r.read_artifact("unrelated-embedded"),lambda:r.search_persistent(DELETED)):
   with self.assertRaises(RestoreNotReady): public_read()
  with r._db() as c: c.execute("DELETE FROM artifacts WHERE id='unrelated-embedded'")
  r.activate_after_replay(); self.assertIsNone(r.read_event("E1")[0][1])

 def test_independent_source_exemption_is_exact_cell_only(self):
  self.f._prepare_scan("E1","DEL-E1")
  with self.f._db() as c: c.execute("UPDATE events SET payload=? WHERE id='E1-copy'",(b"PREFIX-"+DELETED.encode()+b"-SUFFIX",))
  with self.assertRaises(RestoreNotReady): self.delete()

 def test_restore_detects_unlineaged_predelete_backup_copy_after_restart(self):
  secret=b"restart-secret-key-material-v04"; boundary=KernelCheckpointBoundary(secret); f=V04Fixture(Path(self.t.name)/"attack-live.sqlite",kernel_checkpoint=boundary,clock=Clock()); f.event("E1",DELETED); f.event("E2","other"); f.artifact("unrelated-copy","cache",DELETED,["E2"]); pre=Path(self.t.name)/"attack-pre.sqlite"; f.backup_to(pre)
  with f._db() as c: c.execute("DELETE FROM artifacts WHERE id='unrelated-copy'")
  self.assertTrue(f.orchestrate_delete("E1",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1"))
  with f._db() as c: tombs,audits,receipts,anchors=c.execute("SELECT * FROM tombstones").fetchall(),c.execute("SELECT * FROM audit_events").fetchall(),c.execute("SELECT * FROM deletion_receipts").fetchall(),c.execute("SELECT * FROM receipt_chain_anchors").fetchall()
  receipt_state,erasure_state=boundary.restart_state(); restarted=KernelCheckpointBoundary(secret,receipt_checkpoints=receipt_state,erasure_checkpoints=erasure_state); base=V04Fixture(Path(self.t.name)/"attack-restored.sqlite",kernel_checkpoint=restarted,clock=Clock()); r=base.restore_predelete(pre); r.import_tombstones(tombs); r.import_audit_events(audits); r.import_deletion_receipts(receipts); r.import_receipt_anchors(anchors)
  with self.assertRaises(RestoreNotReady): r.activate_after_replay()
  for public_read in (lambda:r.read_event("E1"),lambda:r.read_artifact("unrelated-copy"),lambda:r.search_persistent(DELETED)):
   with self.assertRaises(RestoreNotReady): public_read()
  with r._db() as c: c.execute("DELETE FROM artifacts WHERE id='unrelated-copy'")
  r.activate_after_replay(); self.assertIsNone(r.read_event("E1")[0][1])

 def test_every_public_content_path_fails_closed_while_restoring(self):
  pre=Path(self.t.name)/"public-paths.sqlite"; self.f.backup_to(pre); r=self.f.restore_predelete(pre)
  classifications={
   "activate_after_replay":"CONTROL","artifact":"WRITE","backup_to":"CONTROL","cache_retrieve":"CONTENT","db":"CONTENT","deletion_proof":"METADATA","event":"WRITE","fts_lookup":"CONTENT","graph_retrieve":"CONTENT","import_audit_events":"CONTROL","import_deletion_receipts":"CONTROL","import_receipt_anchors":"CONTROL","import_tombstones":"CONTROL","orchestrate_delete":"CONTROL","page_retrieve":"CONTENT","read_artifact":"CONTENT","read_event":"CONTENT","receipt":"METADATA","receipt_dict":"METADATA","recover":"CONTROL","resolve":"CONTROL","restore_predelete":"CONTROL","search":"CONTENT","search_persistent":"CONTENT","tombstone":"CONTROL","vector_lookup":"CONTENT","verify_receipt_chain":"METADATA"}
  public={name for name,member in inspect.getmembers(V04Fixture,inspect.isfunction) if not name.startswith("_")}; self.assertEqual(public,set(classifications))
  calls={"db":lambda:r.db(),"read_event":lambda:r.read_event("E1"),"read_artifact":lambda:r.read_artifact("page"),"search":lambda:r.search("x"),"fts_lookup":lambda:r.fts_lookup("x"),"vector_lookup":lambda:r.vector_lookup("x"),"graph_retrieve":lambda:r.graph_retrieve("page"),"page_retrieve":lambda:r.page_retrieve("page"),"cache_retrieve":lambda:r.cache_retrieve("page"),"search_persistent":lambda:r.search_persistent(DELETED)}
  self.assertEqual(set(calls),{name for name,kind in classifications.items() if kind=="CONTENT"})
  for call in calls.values():
   with self.assertRaises(RestoreNotReady): call()

 def test_completion_scan_and_evidence_are_atomic_against_second_writer(self):
  scanned=threading.Event(); release=threading.Event()
  def barrier(): scanned.set(); self.assertTrue(release.wait(2))
  self.f._completion_barrier=barrier; result=[]
  worker=threading.Thread(target=lambda:result.append(self.delete())); worker.start(); self.assertTrue(scanned.wait(2)); competing=sqlite3.connect(self.f.path,timeout=0.05)
  try:
   with self.assertRaises(sqlite3.OperationalError): competing.execute("INSERT INTO artifacts VALUES ('late','cache','p1',?, '[\"E2\"]','OBSERVED_EVIDENCE','LIVE')",(DELETED,))
  finally: competing.close(); release.set(); worker.join(2)
  self.assertEqual(result,[True]); self.assertFalse(worker.is_alive())
  with self.assertRaises(RestoreNotReady): self.f.artifact("post-completion","cache",DELETED,["E2"])
 def test_principals_chronology_and_position_survive(self):
  self.assertTrue(self.delete()); r=self.f.receipt_dict("DEL-E1"); self.assertEqual((r["requested_by"],r["authorized_by"],r["executed_by"]),("owner","owner",INTERNAL_EXECUTOR)); self.assertNotEqual(r["executed_by"],r["authorized_by"]); self.assertEqual((r["notebook_page_id"],r["page_position"],r["block_id"],r["original_event_type"]),("PAGE-JOURNAL",7,"BLOCK-7","NOTE.CREATED")); self.assertEqual(r["occurred_at"],"2026-09-26T13:43:00+00:00"); self.assertIsNone(self.f.read_event("E1")[0][1]); self.assertEqual(f"13:43 — [CONTENT ERASED] — {r['deletion_id']}","13:43 — [CONTENT ERASED] — DEL-E1")
 def test_failure_recovery_and_completed_retry_are_idempotent(self):
  self.f.fail_kind="page"; self.assertFalse(self.delete()); self.assertEqual(self.row("page")[1],"RECOVERY_REQUIRED"); self.assertEqual(self.f.receipt("DEL-E1"),[]); self.assertTrue(self.f.recover("E1")); first=self.f.receipt("DEL-E1"); self.assertTrue(self.f.recover("E1")); self.assertTrue(self.delete()); self.assertEqual(self.f.receipt("DEL-E1"),first)
  with self.f._db() as c:
   self.assertEqual(c.execute("SELECT COUNT(*) FROM audit_events WHERE deletion_id='DEL-E1' AND event_type='ERASE.COMPLETED'").fetchone()[0],1); self.assertEqual(c.execute("SELECT COUNT(*) FROM tombstones WHERE deletion_id='DEL-E1'").fetchone()[0],1); self.assertEqual(c.execute("SELECT COUNT(*) FROM deletion_receipts WHERE deletion_id='DEL-E1'").fetchone()[0],1)
 def test_receipt_chain_detects_mutation_and_chain_damage(self):
  self.assertTrue(self.delete()); self.f.event("E4","SECOND_PAYLOAD_V04",page_position=12); self.f.artifact("second-page","page","SECOND_PAYLOAD_V04",["E4"]); self.assertTrue(self.f.orchestrate_delete("E4",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1")); self.assertTrue(self.f.verify_receipt_chain()); altered=Path(self.t.name)/"altered.sqlite"; self.f.backup_to(altered); c=sqlite3.connect(altered)
  try: c.execute("DROP TRIGGER receipts_no_update"); c.execute("UPDATE deletion_receipts SET authorized_by='mallory' WHERE deletion_id='DEL-E1'"); c.commit()
  finally: c.close()
  with self.assertRaises(RestoreNotReady): V04Fixture(altered).verify_receipt_chain()
  with self.f._db() as c:
   with self.assertRaises(sqlite3.DatabaseError): c.execute("UPDATE deletion_receipts SET erased_scope='changed' WHERE deletion_id='DEL-E1'")
  for name,sql in (("deleted","DELETE FROM deletion_receipts WHERE deletion_id='DEL-E1'"),("reordered","UPDATE deletion_receipts SET receipt_sequence=9 WHERE deletion_id='DEL-E1'"),("inserted","UPDATE deletion_receipts SET receipt_sequence=3 WHERE deletion_id='DEL-E4'")):
   path=Path(self.t.name)/(name+".sqlite"); self.f.backup_to(path); c=sqlite3.connect(path)
   try: c.execute("DROP TRIGGER receipts_no_update"); c.execute("DROP TRIGGER receipts_no_delete"); c.execute(sql); c.commit()
   finally: c.close()
   with self.assertRaises(RestoreNotReady): V04Fixture(path).verify_receipt_chain()
 def test_restore_verifies_then_replays_before_live(self):
  pre=Path(self.t.name)/"pre.sqlite"; self.f.backup_to(pre); self.assertTrue(self.delete()); tombs,audits,receipts,anchors=self.retained(); r=self.f.restore_predelete(pre)
  for read in (lambda:r.read_event("E1"),lambda:r.read_artifact("page"),lambda:r.search("x"),lambda:r.fts_lookup("x"),lambda:r.vector_lookup("x"),lambda:r.graph_retrieve("page"),lambda:r.page_retrieve("page"),lambda:r.cache_retrieve("page")):
   with self.assertRaises(RestoreNotReady): read()
  r.import_tombstones(tombs); r.import_audit_events(audits); r.import_deletion_receipts(receipts); r.import_receipt_anchors(anchors); r.activate_after_replay(); self.assertIsNone(r.read_event("E1")[0][1]); self.assertEqual(r.read_artifact("page")[0][1],"DELETED"); self.assertTrue(r.verify_receipt_chain())
 def test_restore_denies_modified_receipt(self):
  pre=Path(self.t.name)/"pre-bad.sqlite"; self.f.backup_to(pre); self.assertTrue(self.delete()); tombs,audits,receipts,anchors=self.retained(); changed=list(receipts[0]); changed[RECEIPT_COLUMNS.index("executed_by")]="intruder"; r=self.f.restore_predelete(pre); r.import_tombstones(tombs); r.import_audit_events(audits); r.import_deletion_receipts([tuple(changed)]); r.import_receipt_anchors(anchors)
  with self.assertRaises(RestoreNotReady): r.activate_after_replay()
  with self.assertRaises(RestoreNotReady): r.read_event("E1")
 def test_scanner_all_stores_and_no_semantic_descriptor(self):
  self.assertTrue(self.delete()); self.assertFalse(self.f.search_persistent(DELETED,permitted_event_ids=("E1-copy",))); self.assertFalse(self.f.search_persistent("relationship note")); r=self.f.receipt_dict("DEL-E1"); self.assertNotIn(DELETED,json.dumps(r)); self.assertEqual(self.f.deletion_proof("DEL-E1")["Original content"],"unavailable by design")

 def test_completion_rejects_forbidden_bytes_with_unrelated_lineage(self):
  self.f.artifact("unrelated-copy","cache",DELETED,["E2"])
  with self.assertRaises(RestoreNotReady): self.delete()
  with self.f._db() as c:
   self.assertEqual(c.execute("SELECT COUNT(*) FROM deletion_receipts WHERE deletion_id='DEL-E1'").fetchone()[0],0)
   self.assertEqual(c.execute("SELECT COUNT(*) FROM audit_events WHERE deletion_id='DEL-E1' AND event_type='ERASE.COMPLETED'").fetchone()[0],0)
  self.assertTrue(self.f.search_persistent(DELETED,permitted_event_ids=("E1-copy",)))

 def test_authorization_is_resolved_by_humanos_policy(self):
  for requester,authorizer in (("","cred-owner-v1"),("cred-owner-v1",""),("owner","cred-owner-v1"),("unknown","cred-owner-v1"),("cred-worker-v1","cred-owner-v1"),("cred-owner-v1","cred-worker-v1"),("cred-owner-v1","cred-connector-v1")):
   with self.assertRaises(AuthorizationError): self.f.orchestrate_delete("E1",requester_token=requester,authorizer_token=authorizer)
  with self.assertRaises(AuthorizationError): self.f.orchestrate_delete("E1",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1",authorized_by="owner")
  self.assertTrue(self.delete()); receipt=self.f.receipt_dict("DEL-E1"); self.assertEqual((receipt["requested_by"],receipt["authorized_by"],receipt["executed_by"]),("owner","owner",INTERNAL_EXECUTOR))

 def test_restore_missing_tombstone_and_identity_mismatch_fail_closed(self):
  pre=Path(self.t.name)/"pre-missing.sqlite"; self.f.backup_to(pre); self.assertTrue(self.delete()); tombs,audits,receipts,anchors=self.retained()
  for mode in ("missing","mismatch","duplicate"):
   r=self.f.restore_predelete(pre); imported=[] if mode=="missing" else list(tombs)
   if mode=="mismatch": imported[0]=tuple(list(imported[0])[:2]+["PO-WRONG"]+list(imported[0])[3:])
   if mode=="duplicate": imported.append(imported[0])
   r.import_tombstones(imported); r.import_audit_events(audits); r.import_deletion_receipts(receipts); r.import_receipt_anchors(anchors)
   with self.assertRaises(RestoreNotReady): r.activate_after_replay()
   with self.assertRaises(RestoreNotReady): r.read_event("E1")

 def test_unknown_receipt_and_missing_completion_evidence_fail_closed(self):
  pre=Path(self.t.name)/"pre-unknown.sqlite"; self.f.backup_to(pre); self.assertTrue(self.delete()); tombs,audits,receipts,anchors=self.retained()
  changed=list(receipts[0]); changed[RECEIPT_COLUMNS.index("deletion_id")]="DEL-UNKNOWN"; changed[RECEIPT_COLUMNS.index("receipt_hash")]=self.f._digest(dict(zip(RECEIPT_COLUMNS,changed)))
  for evidence in ("unknown","no-completion"):
   r=self.f.restore_predelete(pre); r.import_tombstones(tombs); selected=[x for x in audits if not (evidence=="no-completion" and x[2]=="ERASE.COMPLETED")]; r.import_audit_events(selected); r.import_deletion_receipts([tuple(changed)] if evidence=="unknown" else receipts); r.import_receipt_anchors(anchors)
   with self.assertRaises(RestoreNotReady): r.activate_after_replay()

 def test_duplicate_receipt_completion_without_receipt_and_lifecycle_mismatch_fail_closed(self):
  pre=Path(self.t.name)/"pre-ledger.sqlite"; self.f.backup_to(pre); self.assertTrue(self.delete()); tombs,audits,receipts,anchors=self.retained()
  cases=[]
  cases.append((receipts+receipts,audits,anchors))
  cases.append(([],audits,[]))
  changed=list(audits); row=list(changed[0]); row[3]="E2"; changed[0]=tuple(row); cases.append((receipts,changed,anchors))
  for imported_receipts,imported_audits,imported_anchors in cases:
   r=self.f.restore_predelete(pre); r.import_tombstones(tombs); r.import_audit_events(imported_audits); r.import_deletion_receipts(imported_receipts); r.import_receipt_anchors(imported_anchors)
   with self.assertRaises(RestoreNotReady): r.activate_after_replay()
   with self.assertRaises(RestoreNotReady): r.read_event("E1")

 def test_interrupted_restore_rejects_fabricated_resolved_principal(self):
  pre=Path(self.t.name)/"pre-principal.sqlite"; self.f.backup_to(pre); self.f.fail_kind="page"; self.assertFalse(self.delete()); tombs,audits,receipts,anchors=self.retained(); changed=[]
  for audit in audits:
   row=list(audit); row[4]="fabricated-owner"; changed.append(tuple(row))
  r=self.f.restore_predelete(pre); r.import_tombstones(tombs); r.import_audit_events(changed)
  with self.assertRaises(AuthorizationError): r.activate_after_replay()
  with self.assertRaises(RestoreNotReady): r.read_event("E1")

 def test_receipt_anchor_detects_tail_empty_and_anchor_tampering(self):
  self.assertTrue(self.delete()); self.f.event("E4","SECOND_PAYLOAD_V04",page_position=12); self.f.artifact("second-page","page","SECOND_PAYLOAD_V04",["E4"]); self.assertTrue(self.f.orchestrate_delete("E4",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1"))
  cases=("DELETE FROM deletion_receipts","DELETE FROM deletion_receipts WHERE receipt_sequence=2","DELETE FROM receipt_chain_anchors","DELETE FROM receipt_chain_anchors WHERE anchor_sequence=2","UPDATE receipt_chain_anchors SET receipt_count=99 WHERE anchor_sequence=2","UPDATE receipt_chain_anchors SET receipt_head_hash='bad' WHERE anchor_sequence=2","UPDATE receipt_chain_anchors SET last_receipt_sequence=99 WHERE anchor_sequence=2")
  for number,sql in enumerate(cases):
   path=Path(self.t.name)/f"anchor-{number}.sqlite"; self.f.backup_to(path); c=sqlite3.connect(path)
   try: c.execute("DROP TRIGGER receipts_no_delete"); c.execute("DROP TRIGGER anchors_no_delete"); c.execute("DROP TRIGGER anchors_no_update"); c.execute(sql); c.commit()
   finally: c.close()
   with self.assertRaises(RestoreNotReady): V04Fixture(path).verify_receipt_chain()
  with self.f._db() as c:
   with self.assertRaises(sqlite3.DatabaseError): c.execute("DELETE FROM receipt_chain_anchors")
   with self.assertRaises(sqlite3.DatabaseError): c.execute("UPDATE receipt_chain_anchors SET receipt_count=0")

 def test_kernel_checkpoint_detects_coordinated_database_truncation(self):
  self.assertTrue(self.delete()); self.f.event("E4","SECOND_PAYLOAD_V04",page_position=12); self.f.artifact("second-page","page","SECOND_PAYLOAD_V04",["E4"]); self.assertTrue(self.f.orchestrate_delete("E4",requester_token="cred-owner-v1",authorizer_token="cred-owner-v1"))
  path=Path(self.t.name)/"coordinated-truncation.sqlite"; self.f.backup_to(path); c=sqlite3.connect(path)
  try:
   c.execute("DROP TRIGGER receipts_no_delete"); c.execute("DROP TRIGGER anchors_no_delete")
   c.execute("DELETE FROM deletion_receipts WHERE receipt_sequence=2"); c.execute("DELETE FROM receipt_chain_anchors WHERE anchor_sequence=2"); c.execute("DELETE FROM audit_events WHERE deletion_id='DEL-E4' AND event_type='ERASE.COMPLETED'"); c.commit()
  finally: c.close()
  attacked=V04Fixture(path,kernel_checkpoint=self.f.kernel_checkpoint)
  with self.assertRaises(RestoreNotReady): attacked.verify_receipt_chain()

 def test_public_database_access_is_quarantined_during_restore(self):
  pre=Path(self.t.name)/"pre-db-quarantine.sqlite"; self.f.backup_to(pre); self.assertTrue(self.delete()); r=self.f.restore_predelete(pre)
  with self.assertRaises(RestoreNotReady): r.db()
  with self.assertRaises(RestoreNotReady): r.read_event("E1")

 def test_interrupted_restore_recovers_before_live(self):
  pre=Path(self.t.name)/"pre-interrupted.sqlite"; self.f.backup_to(pre); self.f.fail_kind="page"; self.assertFalse(self.delete()); tombs,audits,receipts,anchors=self.retained(); self.assertEqual(receipts,[]); self.assertEqual(anchors,[])
  r=self.f.restore_predelete(pre); r.import_tombstones(tombs); r.import_audit_events(audits)
  with self.assertRaises(RestoreNotReady): r.read_event("E1")
  r.activate_after_replay(); self.assertIsNone(r.read_event("E1")[0][1]); self.assertEqual(len(r.receipt("DEL-E1")),1); self.assertTrue(r.verify_receipt_chain())

if __name__=="__main__": unittest.main()
