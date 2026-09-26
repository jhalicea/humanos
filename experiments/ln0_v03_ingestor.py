"""V-03 isolated Ingestor fixture; not production runtime code.

The events table persists authoritative event columns, including ingested_at,
and payload bytes; the one AUTHORITATIVE_FIELDS definition drives the canonical
envelope. The outbox is non-authoritative operational delivery state.
"""
from __future__ import annotations
import hashlib, hmac, json, secrets, sqlite3, time
from dataclasses import dataclass
from pathlib import Path
class IngestConflict(ValueError): pass
class SimulatedCrash(RuntimeError): pass
@dataclass(frozen=True)
class SourcePolicy:
    source_authority: str; actor_id: str; actor_type: str; epistemic_class: str; sensitivity_class: str; delegation_lane: str; provider_class: str
@dataclass(frozen=True)
class ResolvedPrincipal: principal_id: str; source_class: str; policy: SourcePolicy
POLICIES={"connector":SourcePolicy("OBSERVED_EVIDENCE","connector","CONNECTOR","OBSERVED","STANDARD","NONE","EXTERNAL"),"trusted-humanos-ui":SourcePolicy("OWNER_SUBMITTED","humanos-ui","HUMAN","ASSERTED","STANDARD","OWNER","LOCAL")}
@dataclass(frozen=True)
class IngestRequest: ingestion_id: str; payload_bytes: bytes; claims: dict
@dataclass(frozen=True)
class Commit: event_id: str; seq: int; event_hash: str; payload_hash: str; source_authority: str; owner_decision: str; epistemic_status: str; envelope: dict
class TestAuthenticator:
    """Test stand-in for OS transport authentication; callers receive opaque tokens."""
    def __init__(self, principals, *, secret=None): self._secret=secret or secrets.token_bytes(32); self._principals=dict(principals)
    def issue_for_test(self, principal_id):
        body=principal_id.encode(); return body.hex()+"."+hmac.new(self._secret,body,hashlib.sha256).hexdigest()
    def authenticate(self, token):
        if not isinstance(token,str) or "." not in token: raise PermissionError("unauthenticated token")
        encoded,signature=token.split(".",1)
        try: body=bytes.fromhex(encoded); principal_id=body.decode()
        except (ValueError,UnicodeDecodeError): raise PermissionError("malformed token")
        if not hmac.compare_digest(signature,hmac.new(self._secret,body,hashlib.sha256).hexdigest()) or principal_id not in self._principals: raise PermissionError("invalid token")
        source_class=self._principals[principal_id]; return ResolvedPrincipal(principal_id,source_class,POLICIES[source_class])
def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def digest(raw): return hashlib.sha256(raw).hexdigest()
AUTHORITATIVE_FIELDS=("schema_version","event_id","sequence","effective_source_id","actor_id","actor_type","event_type","epistemic_class","sensitivity_class","delegation_lane","provider_class","source_authority","owner_decision","ingestion_id","correlation_id","causation_id","payload_hash","previous_event_hash","submission_fingerprint","ingested_at")
class V03Ingestor:
    def __init__(self,path:Path,*,authenticator,projection_callback=None,fault_hook=None): self.path=Path(path); self.authenticator=authenticator; self.projection_callback=projection_callback; self.fault_hook=fault_hook; self._init_db()
    def _connect(self):
        c=sqlite3.connect(self.path,timeout=30,isolation_level=None); c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA busy_timeout=30000"); return c
    def _init_db(self):
        self.path.parent.mkdir(parents=True,exist_ok=True); c=self._connect()
        try: c.executescript("CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,effective_source_id TEXT NOT NULL,ingestion_id TEXT NOT NULL,envelope BLOB NOT NULL,payload BLOB NOT NULL,payload_hash TEXT NOT NULL,submission_fingerprint TEXT NOT NULL,seq INTEGER UNIQUE NOT NULL,prev_event_hash TEXT,event_hash TEXT UNIQUE NOT NULL,source_authority TEXT NOT NULL,owner_decision TEXT NOT NULL,epistemic_status TEXT NOT NULL,ingested_at REAL NOT NULL,UNIQUE(effective_source_id,ingestion_id)); CREATE TABLE IF NOT EXISTS outbox(event_id TEXT PRIMARY KEY REFERENCES events(event_id));")
        finally: c.close()
    def submit(self,token:str,request:IngestRequest,*,crash_after_commit=False):
        principal=self.authenticator.authenticate(token); policy=principal.policy; source_id=principal.principal_id; payload=bytes(request.payload_bytes); ph=digest(payload); fp=digest(canonical({"ingestion_id":request.ingestion_id,"payload_bytes":payload.hex(),"claims":request.claims})); c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE"); row=c.execute("SELECT event_id,seq,event_hash,payload_hash,source_authority,owner_decision,epistemic_status,envelope,submission_fingerprint FROM events WHERE effective_source_id=? AND ingestion_id=?",(source_id,request.ingestion_id)).fetchone()
            if row:
                if row[8]!=fp: c.rollback(); raise IngestConflict("idempotency key reused with different semantic request")
                c.commit(); return Commit(*row[:7],json.loads(row[7]))
            prior=c.execute("SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone(); seq=prior[0]+1 if prior else 1; prev=prior[1] if prior else "GENESIS"; eid=digest((source_id+"\0"+request.ingestion_id).encode()); decision="NOT_OWNER_DECISION"
            ingested_at=time.time(); env={"schema_version":"v03-test-1","event_id":eid,"sequence":seq,"effective_source_id":source_id,"actor_id":policy.actor_id,"actor_type":policy.actor_type,"event_type":"INGESTED","epistemic_class":policy.epistemic_class,"sensitivity_class":policy.sensitivity_class,"delegation_lane":policy.delegation_lane,"provider_class":policy.provider_class,"source_authority":policy.source_authority,"owner_decision":decision,"ingestion_id":request.ingestion_id,"correlation_id":None,"causation_id":None,"payload_hash":ph,"previous_event_hash":prev,"submission_fingerprint":fp,"ingested_at":ingested_at}; eh=digest(canonical(env))
            c.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,source_id,request.ingestion_id,canonical(env),payload,ph,fp,seq,prev,eh,policy.source_authority,decision,policy.epistemic_class,ingested_at)); c.execute("INSERT INTO outbox VALUES (?)",(eid,))
            if self.fault_hook: self.fault_hook(c)
            c.commit(); result=Commit(eid,seq,eh,ph,policy.source_authority,decision,policy.epistemic_class,env)
            if crash_after_commit: raise SimulatedCrash("crash after commit before acknowledgement")
        finally: c.close()
        if self.projection_callback:
            try: self.projection_callback(result)
            except Exception: pass
        return result
    def events(self):
        c=self._connect()
        try: return c.execute("SELECT event_id,effective_source_id,ingestion_id,envelope,payload,payload_hash,submission_fingerprint,seq,prev_event_hash,event_hash,source_authority,owner_decision,epistemic_status,ingested_at FROM events ORDER BY seq").fetchall()
        finally: c.close()
    def verify(self):
        previous="GENESIS"; expected=1
        for row in self.events():
            eid,sid,iid,env,payload,ph,fp,seq,prev,eh,authority,decision,status,_=row; obj=json.loads(env)
            if seq!=expected: raise AssertionError("sequence mismatch")
            if digest(payload)!=ph: raise AssertionError("payload hash mismatch")
            if set(obj)!=set(AUTHORITATIVE_FIELDS): raise AssertionError("authoritative envelope incomplete")
            expected_values={"event_id":eid,"effective_source_id":sid,"ingestion_id":iid,"payload_hash":ph,"submission_fingerprint":fp,"sequence":seq,"previous_event_hash":prev,"source_authority":authority,"owner_decision":decision,"epistemic_class":status,"ingested_at":row[13]}
            if any(obj[k]!=v for k,v in expected_values.items()): raise AssertionError("persisted field mismatch")
            if prev!=previous: raise AssertionError("previous hash mismatch")
            if digest(canonical(obj))!=eh: raise AssertionError("event hash mismatch")
            previous=eh; expected+=1
        return True
