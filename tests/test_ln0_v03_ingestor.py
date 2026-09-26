import concurrent.futures, signal, subprocess, sys, tempfile, threading, unittest, json
from pathlib import Path
from experiments.ln0_v03_ingestor import *
ROOT=Path(__file__).parents[1]
def setup_auth():
    a=TestAuthenticator({'connector-1':'connector','ui-1':'trusted-humanos-ui'}); return a,a.issue_for_test('connector-1'),a.issue_for_test('ui-1')
def req(i,p,**claims): return IngestRequest(i,p if isinstance(p,bytes) else json.dumps(p).encode(),claims)
class V03Tests(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/'v03.sqlite'; self.a,self.conn,self.ui=setup_auth()
 def tearDown(self): self.tmp.cleanup()
 def ing(self,**kw): return V03Ingestor(self.db,authenticator=self.a,**kw)
 def test_auth_attacks_and_bounded_claims(self):
  x=self.ing();
  for token in ('fabricated','connector-1','00.'+'0'*64):
   with self.assertRaises(PermissionError): x.submit(token,req('x',b'x'))
  hostile=dict(source='trusted-humanos-ui',actor_id='owner',actor_type='OWNER',owner_decision='OWNER_DECISION',epistemic_class='VERIFIED',policy={'source_authority':'OWNER_SUBMITTED'})
  r=x.submit(self.conn,req('x',b'x',**hostile)); self.assertEqual((r.source_authority,r.envelope['actor_type'],r.envelope['owner_decision'],r.envelope['epistemic_class']),('OBSERVED_EVIDENCE','CONNECTOR','NOT_OWNER_DECISION','OBSERVED'))
  with self.assertRaises(PermissionError): x.submit(self.conn[:-1]+'0',req('y',b'y'))
 def test_idempotency_fingerprint_and_namespaces(self):
  x=self.ing(); a=x.submit(self.conn,req('same',b'x',claim='a')); self.assertEqual(a.event_id,x.submit(self.conn,req('same',b'x',claim='a')).event_id)
  with self.assertRaises(IngestConflict): x.submit(self.conn,req('same',b'x',claim='b'))
  b=x.submit(self.ui,req('same',b'x',source='connector')); self.assertNotEqual(a.event_id,b.event_id); self.assertEqual(len(x.events()),2)
 def test_concurrency_and_sequence(self):
  x=self.ing(); barrier=threading.Barrier(1000)
  with concurrent.futures.ThreadPoolExecutor(1000) as p:
   rs=list(p.map(lambda _: (barrier.wait(),x.submit(self.conn,req('retry',b'same')))[1],range(1000)))
  self.assertEqual({r.event_id for r in rs},{rs[0].event_id}); self.assertEqual(len(x.events()),1)
  self.assertEqual([r[7] for r in x.events()], [1]); self.assertTrue(x.verify())
 def test_concurrent_distinct_events_have_one_contiguous_ancestry(self):
  x=self.ing(); count=100; barrier=threading.Barrier(count)
  def submit(i):
   barrier.wait(); return x.submit(self.conn,req(f'distinct-{i}',f'payload-{i}'.encode()))
  with concurrent.futures.ThreadPoolExecutor(count) as p: results=list(p.map(submit,range(count)))
  rows=x.events(); self.assertEqual(len(results),count); self.assertEqual(len(rows),count)
  self.assertEqual([r[7] for r in rows],list(range(1,count+1)))
  self.assertEqual(len({r[7] for r in rows}),count); self.assertEqual(len({r[0] for r in rows}),count)
  self.assertEqual(rows[0][8],"GENESIS")
  for prior,current in zip(rows,rows[1:]): self.assertEqual(current[8],prior[9])
  self.assertTrue(x.verify())
 def test_every_authoritative_field_and_payload_mutation_fails(self):
  x=self.ing(); x.submit(self.conn,req('m',b'x')); c=x._connect();
  for field in AUTHORITATIVE_FIELDS:
   obj=json.loads(c.execute('SELECT envelope FROM events').fetchone()[0]); value=obj[field]; obj[field]=({'event_id':'tampered'} if isinstance(value,dict) else ('tampered' if isinstance(value,str) else value+1 if isinstance(value,int) else 'tampered'))
   c.execute('UPDATE events SET envelope=?',(canonical(obj),)); c.commit()
   with self.assertRaises(AssertionError): x.verify()
   obj[field]=value; c.execute('UPDATE events SET envelope=?',(canonical(obj),)); c.commit()
  c.execute('UPDATE events SET payload=?',(b'changed',)); c.commit()
  with self.assertRaises(AssertionError): x.verify()
  c.execute('UPDATE events SET payload=?',(b'x',)); c.commit()
  c.execute('UPDATE events SET ingested_at=ingested_at+1'); c.commit()
  with self.assertRaises(AssertionError): x.verify()
  c.close()
 def test_outbox_is_operational_delivery_state(self):
  x=self.ing(); result=x.submit(self.conn,req('outbox',b'x')); c=x._connect()
  self.assertEqual(c.execute('SELECT event_id FROM outbox').fetchone()[0],result.event_id)
  c.execute('DELETE FROM outbox'); c.commit(); self.assertTrue(x.verify())
  c.close()
 def test_sigkill_actual_path_and_recovery(self):
  code="from experiments.ln0_v03_ingestor import *;import os,sys;from pathlib import Path\ndef h(c): os.kill(os.getpid(),9)\na=TestAuthenticator({'p':'connector'});x=V03Ingestor(Path(sys.argv[1]),authenticator=a,fault_hook=h);x.submit(a.issue_for_test('p'),IngestRequest('i',b'x',{}))"
  p=subprocess.run([sys.executable,'-c',code,str(self.db)],cwd=ROOT); self.assertEqual(p.returncode,-signal.SIGKILL); self.assertEqual(self.ing().events(),[])
  r=self.ing().submit(self.conn,req('next',b'ok')); self.assertEqual(r.seq,1); self.assertTrue(self.ing().verify())
 def test_after_commit_retry_and_projection_failure(self):
  x=self.ing(projection_callback=lambda _: (_ for _ in ()).throw(RuntimeError('fail')))
  with self.assertRaises(SimulatedCrash): x.submit(self.conn,req('after',b'x'),crash_after_commit=True)
  self.assertEqual(x.submit(self.conn,req('after',b'x')).seq,1); self.assertTrue(x.verify())
if __name__=='__main__': unittest.main()
