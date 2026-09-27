"""V-04 Attempt 8 isolated deletion-contract fixture; not production code."""
from __future__ import annotations
import hashlib, hmac, json, secrets, sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DELETED="DELETED_PAYLOAD_V04__do-not-leak"; OBSERVED_EVIDENCE="OBSERVED_EVIDENCE"; OWNER_RATIFIED="OWNER_RATIFIED"
_RANK={OBSERVED_EVIDENCE:1,OWNER_RATIFIED:2}; INTERNAL_EXECUTOR="humanos:deletion-worker"
RECEIPT_COLUMNS=("receipt_sequence","deletion_id","deletion_event_id","target_event_id","target_payload_object_id","notebook_page_id","page_position","block_id","original_event_type","occurred_at","captured_at","ingested_at","operation","erased_scope","requested_by","authorized_by","executed_by","requested_at","authorized_at","committed_at","completed_at","policy_version","fanout_status","affected_artifact_count","recomputed_artifact_count","invalidated_artifact_count","failed_artifact_count","restore_replay_required","restore_tombstone_status","verification_status","verification_method","verified_at","previous_receipt_hash","receipt_hash")
HASH_FIELDS=tuple(x for x in RECEIPT_COLUMNS if x!="receipt_hash")
class FanoutFailure(RuntimeError): pass
class RestoreNotReady(RuntimeError): pass
class AuthorizationError(PermissionError): pass
def _now(): return datetime.now(timezone.utc).isoformat(timespec="microseconds")

@dataclass(frozen=True)
class ReceiptCheckpoint:
 receipt_count:int; receipt_head_hash:str; last_receipt_sequence:int

@dataclass(frozen=True)
class ErasureCheckpoint:
 deletion_id:str; match_length:int; erasure_tag:str; permitted_event_ids:tuple[str,...]

class KernelCheckpointBoundary:
 """Synthetic encrypted-kernel/key boundary; neither secret nor state is in Notebook DB."""
 def __init__(self,erasure_secret=None,*,receipt_checkpoints=(),erasure_checkpoints=()):
  self.__erasure_secret=erasure_secret or secrets.token_bytes(32)
  if not isinstance(self.__erasure_secret,bytes) or len(self.__erasure_secret)<16: raise ValueError("kernel erasure secret must be at least 128 bits")
  self._checkpoints=list(receipt_checkpoints); self._erasures={x.deletion_id:x for x in erasure_checkpoints}
 def record(self,checkpoint):
  prior=self.expected()
  if checkpoint.receipt_count!=(prior.receipt_count+1 if prior else 1) or checkpoint.last_receipt_sequence!=checkpoint.receipt_count: raise RestoreNotReady("kernel checkpoint sequence invalid")
  self._checkpoints.append(checkpoint)
 def expected(self): return self._checkpoints[-1] if self._checkpoints else None
 def rollback(self,checkpoint):
  if self._checkpoints and self._checkpoints[-1]==checkpoint: self._checkpoints.pop()
 def _deletion_key(self,deletion_id):
  return hmac.new(self.__erasure_secret,b"V04 deletion key\0"+deletion_id.encode(),hashlib.sha256).digest()
 def _tag(self,deletion_id,canonical_deleted_bytes):
  return hmac.new(self._deletion_key(deletion_id),canonical_deleted_bytes,hashlib.sha256).hexdigest()
 def register_erasure(self,deletion_id,canonical_deleted_bytes,permitted_event_ids=()):
  if not canonical_deleted_bytes: raise ValueError("erased canonical bytes must be non-empty")
  checkpoint=ErasureCheckpoint(deletion_id,len(canonical_deleted_bytes),self._tag(deletion_id,canonical_deleted_bytes),tuple(permitted_event_ids))
  prior=self._erasures.get(deletion_id)
  if prior and prior!=checkpoint: raise RestoreNotReady("kernel erasure checkpoint conflict")
  self._erasures[deletion_id]=checkpoint
  return checkpoint
 def erasure(self,deletion_id): return self._erasures.get(deletion_id)
 def matches_erased_content(self,deletion_id,candidate):
  checkpoint=self.erasure(deletion_id)
  if not checkpoint or len(candidate)<checkpoint.match_length: return False
  return any(hmac.compare_digest(checkpoint.erasure_tag,self._tag(deletion_id,candidate[start:start+checkpoint.match_length])) for start in range(len(candidate)-checkpoint.match_length+1))
 def restart_state(self): return tuple(self._checkpoints),tuple(self._erasures.values())

@dataclass(frozen=True)
class ResolvedPrincipal:
 principal_id:str; principal_type:str; deletion_permissions:tuple[str,...]; may_request_erase:bool; may_authorize_erase:bool

class TestDeletionAuthenticator:
 def __init__(self):
  self._tokens={
   "cred-owner-v1":ResolvedPrincipal("owner","OWNER",("REQUEST_ERASE","AUTHORIZE_ERASE"),True,True),
   "cred-worker-v1":ResolvedPrincipal("worker","WORKER",(),False,False),
   "cred-connector-v1":ResolvedPrincipal("connector","CONNECTOR",("REQUEST_ERASE",),True,False)}
 def authenticate(self,token):
  if not isinstance(token,str) or not token: raise AuthorizationError("authenticated principal required")
  if token not in self._tokens: raise AuthorizationError("unknown credential")
  return self._tokens[token]
 def resolve_principal_id(self,principal_id):
  matches=[principal for principal in self._tokens.values() if principal.principal_id==principal_id]
  if len(matches)!=1: raise AuthorizationError("unknown resolved principal")
  return matches[0]

class V04Fixture:
 def __init__(self,path:Path,*,clock=None,object_id_factory=None,authenticator=None,kernel_checkpoint=None,completion_barrier=None):
  self.path=Path(path); self.fail_kind=None; self._restore_state="LIVE"; self._clock=clock or _now; self._oid=object_id_factory or (lambda:"PO-"+secrets.token_hex(16)); self._auth=authenticator or TestDeletionAuthenticator(); self._kernel_checkpoint=kernel_checkpoint or KernelCheckpointBoundary(); self._completion_barrier=completion_barrier; self._init()
 @contextmanager
 def _db(self):
  c=sqlite3.connect(self.path)
  try: yield c; c.commit()
  except Exception: c.rollback(); raise
  finally: c.close()
 @property
 def kernel_checkpoint(self): return self._kernel_checkpoint
 def db(self):
  self._require_live()
  return sqlite3.connect(self.path)
 def _init(self):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  with self._db() as c: c.executescript('''
  CREATE TABLE IF NOT EXISTS payload_objects(payload_object_id TEXT PRIMARY KEY,object_commitment TEXT UNIQUE NOT NULL,storage_status TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,payload_object_id TEXT UNIQUE NOT NULL,payload BLOB,object_commitment TEXT NOT NULL,topic TEXT NOT NULL,authority TEXT NOT NULL,notebook_page_id TEXT NOT NULL,page_position INTEGER NOT NULL,block_id TEXT NOT NULL,original_event_type TEXT NOT NULL,occurred_at TEXT NOT NULL,captured_at TEXT NOT NULL,ingested_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS tombstones(deletion_id TEXT NOT NULL,source_id TEXT NOT NULL,target_payload_object_id TEXT NOT NULL,erased_scope TEXT NOT NULL,committed_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,kind TEXT NOT NULL,partition TEXT NOT NULL,body BLOB,source_event_ids TEXT NOT NULL,required_authority TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'LIVE');
  CREATE TABLE IF NOT EXISTS fanout_results(deletion_id TEXT NOT NULL,artifact_id TEXT NOT NULL,outcome TEXT NOT NULL,PRIMARY KEY(deletion_id,artifact_id));
  CREATE TABLE IF NOT EXISTS audit_events(id INTEGER PRIMARY KEY AUTOINCREMENT,deletion_id TEXT NOT NULL,event_type TEXT NOT NULL,target_event_id TEXT NOT NULL,requested_by TEXT NOT NULL,authorized_by TEXT NOT NULL,executed_by TEXT NOT NULL,at TEXT NOT NULL,erased_scope TEXT NOT NULL,policy_version TEXT NOT NULL,fanout_status TEXT NOT NULL,UNIQUE(deletion_id,event_type));
  CREATE TABLE IF NOT EXISTS deletion_receipts(receipt_sequence INTEGER NOT NULL,deletion_id TEXT NOT NULL,deletion_event_id INTEGER NOT NULL,target_event_id TEXT NOT NULL,target_payload_object_id TEXT NOT NULL,notebook_page_id TEXT NOT NULL,page_position INTEGER NOT NULL,block_id TEXT NOT NULL,original_event_type TEXT NOT NULL,occurred_at TEXT NOT NULL,captured_at TEXT NOT NULL,ingested_at TEXT NOT NULL,operation TEXT NOT NULL,erased_scope TEXT NOT NULL,requested_by TEXT NOT NULL,authorized_by TEXT NOT NULL,executed_by TEXT NOT NULL,requested_at TEXT NOT NULL,authorized_at TEXT NOT NULL,committed_at TEXT NOT NULL,completed_at TEXT NOT NULL,policy_version TEXT NOT NULL,fanout_status TEXT NOT NULL,affected_artifact_count INTEGER NOT NULL,recomputed_artifact_count INTEGER NOT NULL,invalidated_artifact_count INTEGER NOT NULL,failed_artifact_count INTEGER NOT NULL,restore_replay_required INTEGER NOT NULL,restore_tombstone_status TEXT NOT NULL,verification_status TEXT NOT NULL,verification_method TEXT NOT NULL,verified_at TEXT NOT NULL,previous_receipt_hash TEXT NOT NULL,receipt_hash TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS receipt_chain_anchors(anchor_sequence INTEGER PRIMARY KEY,receipt_count INTEGER NOT NULL,receipt_head_hash TEXT NOT NULL,last_receipt_sequence INTEGER NOT NULL,anchored_at TEXT NOT NULL);
  CREATE TRIGGER IF NOT EXISTS receipts_no_update BEFORE UPDATE ON deletion_receipts BEGIN SELECT RAISE(ABORT,'receipt immutable'); END;
  CREATE TRIGGER IF NOT EXISTS receipts_no_delete BEFORE DELETE ON deletion_receipts BEGIN SELECT RAISE(ABORT,'receipt append-only'); END;
  CREATE TRIGGER IF NOT EXISTS anchors_no_update BEFORE UPDATE ON receipt_chain_anchors BEGIN SELECT RAISE(ABORT,'anchor immutable'); END;
  CREATE TRIGGER IF NOT EXISTS anchors_no_delete BEFORE DELETE ON receipt_chain_anchors BEGIN SELECT RAISE(ABORT,'anchor append-only'); END;
  CREATE TRIGGER IF NOT EXISTS lineage_insert BEFORE INSERT ON artifacts BEGIN SELECT CASE WHEN json_valid(NEW.source_event_ids)=0 OR json_type(NEW.source_event_ids)!='array' OR json_array_length(NEW.source_event_ids)=0 OR (SELECT COUNT(*) FROM json_each(NEW.source_event_ids) WHERE type!='text' OR length(value)=0)!=0 OR (SELECT COUNT(*) FROM json_each(NEW.source_event_ids))!=(SELECT COUNT(DISTINCT value) FROM json_each(NEW.source_event_ids)) OR (SELECT COUNT(*) FROM json_each(NEW.source_event_ids) j WHERE NOT EXISTS(SELECT 1 FROM events e WHERE e.id=j.value))!=0 THEN RAISE(ABORT,'invalid artifact lineage') END; END;
  CREATE TRIGGER IF NOT EXISTS lineage_update BEFORE UPDATE OF source_event_ids ON artifacts BEGIN SELECT CASE WHEN json_valid(NEW.source_event_ids)=0 OR json_type(NEW.source_event_ids)!='array' OR json_array_length(NEW.source_event_ids)=0 OR (SELECT COUNT(*) FROM json_each(NEW.source_event_ids) WHERE type!='text' OR length(value)=0)!=0 OR (SELECT COUNT(*) FROM json_each(NEW.source_event_ids))!=(SELECT COUNT(DISTINCT value) FROM json_each(NEW.source_event_ids)) OR (SELECT COUNT(*) FROM json_each(NEW.source_event_ids) j WHERE NOT EXISTS(SELECT 1 FROM events e WHERE e.id=j.value))!=0 THEN RAISE(ABORT,'invalid artifact lineage') END; END;''')
 def event(self,eid,payload,*,authority=OBSERVED_EVIDENCE,topic="topic",payload_object_id=None,notebook_page_id="PAGE-1",page_position=1,block_id=None,original_event_type="NOTE",occurred_at=None,captured_at=None,ingested_at=None):
  if authority not in _RANK: raise ValueError("unrecognized authority")
  raw=payload.encode() if isinstance(payload,str) else payload; oid=payload_object_id or self._oid(); commitment=hashlib.sha256(("opaque-object:"+oid).encode()).hexdigest(); times=[occurred_at or self._clock(),captured_at or self._clock(),ingested_at or self._clock()]
  with self._db() as c: c.execute("INSERT INTO payload_objects VALUES (?,?,?)",(oid,commitment,"AVAILABLE")); c.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,oid,raw,commitment,topic,authority,notebook_page_id,page_position,block_id or "BLOCK-"+eid,original_event_type,*times))
  return oid
 def artifact(self,aid,kind,body,lineage,*,required_authority=OBSERVED_EVIDENCE,partition="p1"):
  if required_authority not in _RANK or not isinstance(lineage,list) or not lineage or len(set(lineage))!=len(lineage): raise ValueError("invalid artifact contract")
  raw=body.encode() if isinstance(body,str) else body
  if raw is not None and any(self._kernel_checkpoint.matches_erased_content(did,raw) for did in self._kernel_checkpoint._erasures): raise RestoreNotReady("write policy rejects erased content")
  with self._db() as c:
   if any(not isinstance(x,str) or not x or not c.execute("SELECT 1 FROM events WHERE id=?",(x,)).fetchone() for x in lineage): raise ValueError("invalid lineage event")
   c.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)",(aid,kind,partition,body,json.dumps(lineage),required_authority,"LIVE"))
 @staticmethod
 def _deletion_id(source): return "DEL-"+source
 def _audit_in(self,c,did,kind,source,actors,at,status):
  c.execute("INSERT OR IGNORE INTO audit_events(deletion_id,event_type,target_event_id,requested_by,authorized_by,executed_by,at,erased_scope,policy_version,fanout_status) VALUES (?,?,?,?,?,?,?,?,?,?)",(did,kind,source,*actors,at,"payload-only","V04-1",status)); return c.execute("SELECT id FROM audit_events WHERE deletion_id=? AND event_type=?",(did,kind)).fetchone()[0]
 def _audit(self,*args):
  with self._db() as c: return self._audit_in(c,*args)
 def tombstone(self,source,*,deletion_id,actors,committed_at):
  with self._db() as c:
   event=c.execute("SELECT payload_object_id FROM events WHERE id=?",(source,)).fetchone()
   if not event: raise KeyError(source)
   old=c.execute("SELECT source_id,target_payload_object_id FROM tombstones WHERE deletion_id=?",(deletion_id,)).fetchall()
   if old and old!=[(source,event[0])]: raise RestoreNotReady("tombstone identity conflict")
   if not old: c.execute("INSERT INTO tombstones VALUES (?,?,?,?,?)",(deletion_id,source,event[0],"payload-only",committed_at))
   c.execute("UPDATE events SET payload=NULL WHERE id=?",(source,)); c.execute("UPDATE payload_objects SET storage_status='ERASED' WHERE payload_object_id=?",(event[0],))
  self._audit(deletion_id,"PAYLOAD.TOMBSTONE",source,actors,committed_at,"TOMBSTONED")
 def _resolve(self,source,did,*,retry=False):
  with self._db() as c:
   if c.execute("SELECT COUNT(*) FROM tombstones WHERE source_id=?",(source,)).fetchone()[0]!=1: raise RestoreNotReady("exactly one tombstone required")
   for aid,kind,raw,required in c.execute("SELECT id,kind,source_event_ids,required_authority FROM artifacts").fetchall():
    lineage=json.loads(raw)
    if source not in lineage: continue
    if self.fail_kind==kind and not retry:
     c.execute("UPDATE artifacts SET status='RECOVERY_REQUIRED' WHERE id=?",(aid,)); c.execute("INSERT OR REPLACE INTO fanout_results VALUES (?,?,?)",(did,aid,"FAILED")); c.commit(); raise FanoutFailure(kind)
    remaining=[x for x in lineage if c.execute("SELECT payload FROM events WHERE id=?",(x,)).fetchone()[0] is not None]; ranks=[_RANK[c.execute("SELECT authority FROM events WHERE id=?",(x,)).fetchone()[0]] for x in remaining]
    if not remaining or max(ranks,default=0)<_RANK[required]: c.execute("UPDATE artifacts SET body=NULL,status='DELETED' WHERE id=?",(aid,)); outcome="INVALIDATED"
    else: c.execute("UPDATE artifacts SET source_event_ids=?,body=?,status='LIVE' WHERE id=?",(json.dumps(remaining),"recomputed:"+','.join(remaining),aid)); outcome="RECOMPUTED"
    c.execute("INSERT OR REPLACE INTO fanout_results VALUES (?,?,?)",(did,aid,outcome))
 def resolve(self,source,*,retry=False): self._resolve(source,self._deletion_id(source),retry=retry)
 def _authorize(self,requester_token,authorizer_token):
  requester=self._auth.authenticate(requester_token); authorizer=self._auth.authenticate(authorizer_token)
  if not requester.may_request_erase: raise AuthorizationError("requester lacks erase permission")
  if not authorizer.may_authorize_erase: raise AuthorizationError("authorizer lacks erase authority")
  return requester,authorizer
 def _validate_resolved_actors(self,actors):
  if len(actors)!=3 or actors[2]!=INTERNAL_EXECUTOR: raise AuthorizationError("invalid deletion executor")
  requester=self._auth.resolve_principal_id(actors[0]); authorizer=self._auth.resolve_principal_id(actors[1])
  if not requester.may_request_erase or not authorizer.may_authorize_erase: raise AuthorizationError("resolved principals lack erase authority")
 def _prepare_scan(self,source,did):
  with self._db() as c:
   row=c.execute("SELECT payload FROM events WHERE id=?",(source,)).fetchone()
   if not row or row[0] is None: return
   raw=row[0] if isinstance(row[0],bytes) else str(row[0]).encode(); permitted=tuple(x[0] for x in c.execute("SELECT id FROM events WHERE id<>? AND payload=?",(source,raw)))
  self._kernel_checkpoint.register_erasure(did,raw,permitted)
 def orchestrate_delete(self,source,*,requester_token,authorizer_token,**claims):
  if claims: raise AuthorizationError("caller principal claims are not authority")
  requester,authorizer=self._authorize(requester_token,authorizer_token); did=self._deletion_id(source)
  with self._db() as c:
   completed=c.execute("SELECT COUNT(*) FROM deletion_receipts WHERE deletion_id=?",(did,)).fetchone()[0]==1
  if completed:
   self.verify_receipt_chain()
   return True
  actors=(requester.principal_id,authorizer.principal_id,INTERNAL_EXECUTOR); self._prepare_scan(source,did); self._audit(did,"ERASE.REQUESTED",source,actors,self._clock(),"REQUESTED"); self._audit(did,"AUTHORIZATION.COMMITTED",source,actors,self._clock(),"AUTHORIZED"); self.tombstone(source,deletion_id=did,actors=actors,committed_at=self._clock())
  try: self._resolve(source,did)
  except FanoutFailure: self._audit(did,"ERASE.RECOVERY_REQUIRED",source,actors,self._clock(),"RECOVERY_REQUIRED"); return False
  try: self._complete(source,did,actors)
  except RestoreNotReady:
   self._audit(did,"ERASE.RECOVERY_REQUIRED",source,actors,self._clock(),"RECOVERY_REQUIRED")
   raise
  return True
 def recover(self,source):
  did=self._deletion_id(source)
  with self._db() as c:
   completed=c.execute("SELECT COUNT(*) FROM deletion_receipts WHERE deletion_id=?",(did,)).fetchone()[0]==1
   row=c.execute("SELECT requested_by,authorized_by FROM audit_events WHERE deletion_id=? AND event_type='ERASE.REQUESTED'",(did,)).fetchone()
  if completed:
   self.verify_receipt_chain()
   return True
  if not row: raise RestoreNotReady("missing authenticated deletion request")
  actors=(row[0],row[1],INTERNAL_EXECUTOR); self._validate_resolved_actors(actors); self._resolve(source,did,retry=True); self._complete(source,did,actors); return True
 def _digest(self,e): return hashlib.sha256(json.dumps({k:e[k] for k in HASH_FIELDS},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 def _verify_erasure_in(self,c,source,did):
  payload=c.execute("SELECT payload FROM events WHERE id=?",(source,)).fetchone(); unresolved=c.execute("SELECT COUNT(*) FROM artifacts WHERE status='RECOVERY_REQUIRED' OR (body IS NOT NULL AND EXISTS(SELECT 1 FROM json_each(artifacts.source_event_ids) WHERE value=?))",(source,)).fetchone()[0]
  if not payload or payload[0] is not None or unresolved: raise RestoreNotReady("erasure verification failed")
  checkpoint=self._kernel_checkpoint.erasure(did)
  if not checkpoint: raise RestoreNotReady("missing authoritative erasure tag")
  if self._search_erasure_tag_in(c,did,checkpoint.permitted_event_ids): raise RestoreNotReady("forbidden content remains in persistent store")
 def _verify_chain_in(self,c):
  rows=c.execute("SELECT "+','.join(RECEIPT_COLUMNS)+" FROM deletion_receipts ORDER BY receipt_sequence").fetchall(); anchors=c.execute("SELECT anchor_sequence,receipt_count,receipt_head_hash,last_receipt_sequence FROM receipt_chain_anchors ORDER BY anchor_sequence").fetchall(); completed=c.execute("SELECT COUNT(*) FROM audit_events WHERE event_type='ERASE.COMPLETED'").fetchone()[0]
  expected=self._kernel_checkpoint.expected()
  if not rows:
   if anchors or completed or expected: raise RestoreNotReady("receipt chain missing")
   return True
  if len(anchors)!=len(rows) or completed!=len(rows): raise RestoreNotReady("receipt chain lifecycle mismatch")
  previous="GENESIS"
  for seq,row in enumerate(rows,1):
   e=dict(zip(RECEIPT_COLUMNS,row)); anchor=anchors[seq-1]
   if e["receipt_sequence"]!=seq or e["previous_receipt_hash"]!=previous or e["receipt_hash"]!=self._digest(e): raise RestoreNotReady("receipt chain invalid")
   if anchor[:4]!=(seq,seq,e["receipt_hash"],seq): raise RestoreNotReady("authoritative receipt anchor mismatch")
   previous=e["receipt_hash"]
  if not expected or (expected.receipt_count,expected.receipt_head_hash,expected.last_receipt_sequence)!=(len(rows),previous,len(rows)): raise RestoreNotReady("kernel receipt checkpoint mismatch")
  return True
 def verify_receipt_chain(self):
  with self._db() as c: return self._verify_chain_in(c)
 def _complete(self,source,did,actors):
  self._validate_resolved_actors(actors)
  c=sqlite3.connect(self.path,isolation_level=None,timeout=0.25); checkpoint=None
  try:
   c.execute("BEGIN EXCLUSIVE")
   if c.execute("SELECT COUNT(*) FROM deletion_receipts WHERE deletion_id=?",(did,)).fetchone()[0]==1:
    c.commit(); return
   self._verify_erasure_in(c,source,did)
   if self._completion_barrier: self._completion_barrier()
   tombs=c.execute("SELECT source_id,target_payload_object_id,committed_at FROM tombstones WHERE deletion_id=?",(did,)).fetchall(); event=c.execute("SELECT payload_object_id,notebook_page_id,page_position,block_id,original_event_type,occurred_at,captured_at,ingested_at FROM events WHERE id=?",(source,)).fetchone()
   if len(tombs)!=1 or tombs[0][0]!=source or not event or tombs[0][1]!=event[0]: raise RestoreNotReady("exactly one coherent tombstone required")
   life=dict(c.execute("SELECT event_type,at FROM audit_events WHERE deletion_id=?",(did,))); counts=dict(c.execute("SELECT outcome,COUNT(*) FROM fanout_results WHERE deletion_id=? GROUP BY outcome",(did,))); failed=counts.get("FAILED",0)
   if failed: raise RestoreNotReady("unresolved derivatives")
   prior=c.execute("SELECT receipt_sequence,receipt_hash FROM deletion_receipts ORDER BY receipt_sequence DESC LIMIT 1").fetchone(); seq=prior[0]+1 if prior else 1; completed=self._clock(); verified=self._clock(); event_id=c.execute("SELECT COALESCE(MAX(id),0)+1 FROM audit_events").fetchone()[0]
   vals=(seq,did,event_id,source,*event,"ERASE","payload-only",*actors,life["ERASE.REQUESTED"],life["AUTHORIZATION.COMMITTED"],tombs[0][2],completed,"V04-1","VERIFIED",sum(counts.values()),counts.get("RECOMPUTED",0),counts.get("INVALIDATED",0),failed,1,"ACTIVE","VERIFIED","persistent-forbidden-content-scan",verified,prior[1] if prior else "GENESIS",None); e=dict(zip(RECEIPT_COLUMNS,vals)); e["receipt_hash"]=self._digest(e)
   c.execute("INSERT INTO deletion_receipts VALUES ("+','.join('?'*len(RECEIPT_COLUMNS))+")",tuple(e[x] for x in RECEIPT_COLUMNS)); c.execute("INSERT INTO receipt_chain_anchors VALUES (?,?,?,?,?)",(seq,seq,e["receipt_hash"],seq,self._clock())); completed_id=self._audit_in(c,did,"ERASE.COMPLETED",source,actors,completed,"VERIFIED")
   if completed_id!=event_id: raise RestoreNotReady("completion identity mismatch")
   checkpoint=ReceiptCheckpoint(seq,e["receipt_hash"],seq); self._kernel_checkpoint.record(checkpoint); c.commit()
  except Exception:
   c.rollback()
   if checkpoint: self._kernel_checkpoint.rollback(checkpoint)
   raise
  finally: c.close()
  self.verify_receipt_chain()
 def _require_live(self):
  if self._restore_state!="LIVE": raise RestoreNotReady("RESTORE_NOT_READY")
 def _read(self,sql,args=()):
  self._require_live()
  with self._db() as c: return c.execute(sql,args).fetchall()
 def read_event(self,eid): return self._read("SELECT id,payload FROM events WHERE id=?",(eid,))
 def read_artifact(self,aid): return self._read("SELECT body,status FROM artifacts WHERE id=?",(aid,))
 def search(self,token): return bool(self._read("SELECT id FROM artifacts WHERE body LIKE ?",('%'+token+'%',)))
 fts_lookup=search; vector_lookup=search; graph_retrieve=read_artifact; page_retrieve=read_artifact; cache_retrieve=read_artifact
 def search_persistent(self,token,*,permitted_event_ids=()):
  self._require_live()
  needle=token.encode() if isinstance(token,str) else token
  with self._db() as c: return self._search_bytes_in(c,needle,permitted_event_ids)
 def _search_bytes_in(self,c,needle,permitted_event_ids=()):
  for table, in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
    cols=[x[1] for x in c.execute("PRAGMA table_info("+table+")")]
    for row in c.execute("SELECT "+','.join(cols)+" FROM "+table):
     record=dict(zip(cols,row))
     for col,value in record.items():
      if table=="events" and col=="payload" and record.get("id") in permitted_event_ids: continue
      if value is not None and needle in (value if isinstance(value,bytes) else str(value).encode()): return True
  return False
 def _search_erasure_tag_in(self,c,did,permitted_event_ids=()):
  for table, in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
   cols=[x[1] for x in c.execute("PRAGMA table_info("+table+")")]
   for row in c.execute("SELECT "+','.join(cols)+" FROM "+table):
    record=dict(zip(cols,row))
    for col,value in record.items():
     if value is None: continue
     candidate=value if isinstance(value,bytes) else str(value).encode()
     if table=="events" and col=="payload" and record.get("id") in permitted_event_ids:
      checkpoint=self._kernel_checkpoint.erasure(did)
      if checkpoint and len(candidate)==checkpoint.match_length and self._kernel_checkpoint.matches_erased_content(did,candidate): continue
     if self._kernel_checkpoint.matches_erased_content(did,candidate): return True
  return False
 def backup_to(self,target):
  dst=sqlite3.connect(target)
  try:
   with self._db() as src: src.backup(dst)
  finally: dst.close()
 def restore_predelete(self,snapshot):
  restored=V04Fixture(self.path,clock=self._clock,object_id_factory=self._oid,authenticator=self._auth,kernel_checkpoint=self._kernel_checkpoint,completion_barrier=self._completion_barrier); src=sqlite3.connect(snapshot)
  try:
   with restored._db() as dst: src.backup(dst)
  finally: src.close()
  restored._restore_state="RESTORING"; return restored
 def _import(self,table,records):
  if self._restore_state!="RESTORING": raise RestoreNotReady("invalid restore state")
  with self._db() as c:
   for row in records: c.execute("INSERT INTO "+table+" VALUES ("+','.join('?'*len(row))+")",row)
 def import_tombstones(self,rows): self._import("tombstones",rows)
 def import_audit_events(self,rows): self._import("audit_events",rows)
 def import_deletion_receipts(self,rows): self._import("deletion_receipts",rows)
 def import_receipt_anchors(self,rows): self._import("receipt_chain_anchors",rows)
 def receipt(self,did): return self._read("SELECT * FROM deletion_receipts WHERE deletion_id=?",(did,))
 def receipt_dict(self,did):
  rows=self.receipt(did); return dict(zip(RECEIPT_COLUMNS,rows[0])) if rows else None
 def deletion_proof(self,did):
  r=self.receipt_dict(did); return {"Deletion":"COMPLETED","Authorized":"YES","Fan-out":"VERIFIED","Unresolved derivatives":r["failed_artifact_count"],"Restore tombstone":"ACTIVE","Original content":"unavailable by design"}
 def _reconcile(self):
  with self._db() as c:
   ids={x[0] for x in c.execute("SELECT deletion_id FROM tombstones UNION SELECT deletion_id FROM deletion_receipts UNION SELECT deletion_id FROM audit_events")}; states=[]
   for did in ids:
    tombs=c.execute("SELECT source_id,target_payload_object_id FROM tombstones WHERE deletion_id=?",(did,)).fetchall(); receipts=c.execute("SELECT target_event_id,target_payload_object_id,requested_by,authorized_by,executed_by FROM deletion_receipts WHERE deletion_id=?",(did,)).fetchall(); life=c.execute("SELECT event_type,target_event_id,requested_by,authorized_by,executed_by FROM audit_events WHERE deletion_id=?",(did,)).fetchall(); completed=[x for x in life if x[0]=="ERASE.COMPLETED"]; recovery=[x for x in life if x[0]=="ERASE.RECOVERY_REQUIRED"]
    if receipts and not tombs: raise RestoreNotReady("receipt without tombstone")
    if len(tombs)!=1: raise RestoreNotReady("exactly one tombstone required")
    if len(receipts)>1 or len(completed)>1: raise RestoreNotReady("duplicate deletion evidence")
    source,oid=tombs[0]
    required={"ERASE.REQUESTED","AUTHORIZATION.COMMITTED","PAYLOAD.TOMBSTONE"}; kinds={x[0] for x in life}
    if not required.issubset(kinds) or any(x[1]!=source for x in life): raise RestoreNotReady("deletion lifecycle mismatch")
    actor_sets={(x[2],x[3],x[4]) for x in life}
    if len(actor_sets)!=1: raise RestoreNotReady("deletion lifecycle principal mismatch")
    actors=next(iter(actor_sets)); self._validate_resolved_actors(actors)
    if receipts:
     if len(completed)!=1 or receipts[0][:2]!=(source,oid) or receipts[0][2:]!=actors: raise RestoreNotReady("completed deletion identity mismatch")
     states.append((did,source,"COMPLETED"))
    elif recovery and not completed: states.append((did,source,"RECOVERY_REQUIRED"))
    else: raise RestoreNotReady("incomplete deletion lifecycle invalid")
   return states
 def activate_after_replay(self):
  if self._restore_state!="RESTORING": raise RestoreNotReady("invalid restore state")
  # checkpoint -> ledger reconciliation -> tombstone replay -> fan-out -> tag scan -> unresolved==0 -> LIVE
  self.verify_receipt_chain(); states=self._reconcile()
  for did,source,state in states:
   with self._db() as c: oid=c.execute("SELECT target_payload_object_id FROM tombstones WHERE deletion_id=?",(did,)).fetchone()[0]; c.execute("UPDATE events SET payload=NULL WHERE id=?",(source,)); c.execute("UPDATE payload_objects SET storage_status='ERASED' WHERE payload_object_id=?",(oid,))
   self._resolve(source,did,retry=True)
   if state=="RECOVERY_REQUIRED": self.recover(source)
  self.verify_receipt_chain(); self._reconcile()
  with self._db() as c:
   for did,source,_state in states: self._verify_erasure_in(c,source,did)
   bad=c.execute("SELECT COUNT(*) FROM tombstones t JOIN events e ON e.id=t.source_id WHERE e.payload IS NOT NULL").fetchone()[0]+c.execute("SELECT COUNT(*) FROM artifacts WHERE status='RECOVERY_REQUIRED'").fetchone()[0]
  if bad: raise RestoreNotReady("recovery required")
  self._restore_state="LIVE"
