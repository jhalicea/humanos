"""Real process exit/restart with deterministic models; no network or user data."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from notebook import Notebook


BASE = Path(__file__).resolve().parents[1]
CHILD = r'''
import os,sys,json
from pathlib import Path
from engine import Agent,Tools
from notebook import Notebook
from server import HumanOSRuntime
folder,scenario,stage=sys.argv[1:]
root=Path(folder)
book=Notebook(root/'vault')
pending=book.recover()
tools=Tools(root/'workspace')
if stage=='first':
    identity=book.bind('Jon','isolated crash acceptance')
    text='read allowed.txt' if scenario=='permissions' else 'create result.txt'
    book.start(identity['hcid'],'acceptance',text)
    (root/'workspace'/'allowed.txt').write_text('allowed evidence')
    (root/'workspace'/'secret.txt').write_text('NEVER_EXPOSE')
class Model:
    name='deterministic-process-model'
    calls=0
    def invoke(self,messages,timeout):
        self.calls+=1
        if scenario=='permissions':
            if stage=='first': os._exit(71)
            if self.calls==1: return {'tool':{'name':'read_file','path':'secret.txt'}}
            if self.calls==2: return {'tool':{'name':'read_file','path':'allowed.txt'}}
            return {'final':'allowed evidence'}
        if stage=='second': raise AssertionError('Completed or uncertain write must not invoke model')
        if self.calls==1: return {'tool':{'name':'create_file','path':'result.txt','content':'created exactly once'}}
        return {'final':'Exact final. Correction retained. 🧭'}
agent=Agent(book,Model(),tools,root/'core',authorize=(lambda r: True) if stage=='first' else None)
if scenario=='write' and stage=='first':
    original=book.event
    def event(tx,kind,payload):
        if kind=='TOOL_RESULT': os._exit(72)
        return original(tx,kind,payload)
    book.event=event
try:
    final=agent.run('acceptance')
except RuntimeError as error:
    if scenario=='write' and stage=='second' and 'unknown outcome' in str(error):
        print('SAFE_STOP: '+str(error))
        book.close();sys.exit(0)
    raise
if scenario=='delivery' and stage=='first':
    book.prepare_delivery('acceptance',final)
    os._exit(73)
runtime=object.__new__(HumanOSRuntime)
runtime.book=book
runtime.deliver('acceptance',final)
book.verify()
book.close()
'''


class ProcessRecoveryTests(unittest.TestCase):
    def invoke(self, folder, scenario, stage):
        return subprocess.run([sys.executable, '-c', CHILD, folder, scenario, stage],
                              cwd=str(BASE), capture_output=True, text=True, timeout=30)

    def test_restarted_task_retains_scope_without_original_callback(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.invoke(folder, 'permissions', 'first').returncode, 71)
            resumed = self.invoke(folder, 'permissions', 'second')
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(resumed.stdout, 'allowed evidence\n')
            book = Notebook(Path(folder) / 'vault')
            try:
                results = [json.loads(r[0]) for r in book.db.execute("SELECT payload FROM events WHERE kind='TOOL_RESULT'")]
                self.assertEqual(results[0]['authorization'], 'DENIED')
                self.assertNotIn('NEVER_EXPOSE', json.dumps(results))
                self.assertEqual(book.task('acceptance')['delivery'], 'WRITTEN_TO_OUTPUT_STREAM')
                book.verify()
            finally:
                book.close()

    def test_process_death_after_write_never_repeats_write(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.invoke(folder, 'write', 'first').returncode, 72)
            artifact = Path(folder) / 'workspace' / 'result.txt'
            before = artifact.stat()
            resumed = self.invoke(folder, 'write', 'second')
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertIn('SAFE_STOP', resumed.stdout)
            self.assertEqual(artifact.read_text(), 'created exactly once')
            self.assertEqual(artifact.stat().st_mtime_ns, before.st_mtime_ns)

    def test_process_death_during_output_replays_exact_final_only(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.invoke(folder, 'delivery', 'first').returncode, 73)
            artifact = Path(folder) / 'workspace' / 'result.txt'
            before = artifact.stat().st_mtime_ns
            resumed = self.invoke(folder, 'delivery', 'second')
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(resumed.stdout, 'Exact final. Correction retained. 🧭\n')
            self.assertEqual(artifact.stat().st_mtime_ns, before)
            book = Notebook(Path(folder) / 'vault')
            try:
                self.assertEqual(book.message_count('acceptance'), 2)
                self.assertEqual(book.task('acceptance')['delivery_attempts'], 2)
                self.assertEqual(book.recover(), [])
                self.assertEqual(book.db.execute("SELECT COUNT(*) FROM events WHERE kind='TOOL_RESULT'").fetchone()[0], 1)
            finally:
                book.close()
