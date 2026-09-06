"""Real local backend E2E; independent output and database readback assertions."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid

BASE = Path(__file__).resolve().parent
TX = 'TX-LIVE-' + uuid.uuid4().hex
request = 'Use read_file to read runtime-check.txt. Return its exact Notebook verification phrase and verification code.'
result = subprocess.run([sys.executable, str(BASE / 'server.py'), '--tx', TX,
                         '--context', 'runtime.md', '--message', request],
                        capture_output=True, text=True, timeout=240)
report = {'transaction': TX, 'returncode': result.returncode, 'stdout': result.stdout,
          'stderr': result.stderr, 'input': request, 'source': 'Codex-authorized automated local test'}
path = BASE / 'evidence'
path.mkdir(exist_ok=True)
try:
    assert result.returncode == 0, result.stderr
    root = BASE / 'HumanOS_Vault/runtime'
    db = sqlite3.connect('file:' + str(root / 'notebook.sqlite3') + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    transaction = dict(db.execute('SELECT * FROM transactions WHERE tx=?', (TX,)).fetchone())
    identity = dict(db.execute('SELECT * FROM identities WHERE hcid=?', (transaction['hcid'],)).fetchone())
    transcript = [dict(r) for r in db.execute('SELECT * FROM transcript WHERE tx=? ORDER BY ordinal', (TX,))]
    task = json.loads(db.execute('SELECT state FROM tasks WHERE tx=?', (TX,)).fetchone()[0])
    events = [dict(r) for r in db.execute('SELECT * FROM events WHERE tx=? ORDER BY seq', (TX,))]
    assert transaction['status'] == 'CHECKPOINTED'
    assert transcript[0]['text'] == request and transcript[0]['role'] == 'HUMAN'
    assert transcript[-1]['role'] == 'ASSISTANT'
    assert result.stdout == transcript[-1]['text'] + '\n'
    assert 'continuity belongs to Jon' in result.stdout and 'HOS-LOCAL-62947' in result.stdout
    assert task['phase'] == 'COMPLETE' and task['delivery'] == 'WRITTEN_TO_OUTPUT_STREAM'
    assert task['model'] == 'llama3:latest'
    kinds = [e['kind'] for e in events]
    for k in ('CONTEXT_LOADED', 'MODEL_REQUEST', 'TOOL_REQUEST', 'AUTHORIZATION', 'TOOL_RESULT', 'CHECKPOINT_VERIFIED', 'DELIVERY'):
        assert k in kinds, k
    observations = [json.loads(e['payload']) for e in events if e['kind'] == 'TOOL_RESULT']
    assert any(o['ok'] and 'HOS-LOCAL-62947' in o['stdout'] for o in observations)
    page = json.loads((root / 'pages' / (identity['page'] + '.json')).read_text())
    assert [r for r in page['transcript'] if r['tx'] == TX] == transcript
    assert transaction in json.loads((root / 'active-index.json').read_text())
    assert identity in json.loads((root / 'bindings.json').read_text())
    assert db.execute('SELECT COUNT(*) FROM recovery WHERE tx=? AND closed=0', (TX,)).fetchone()[0] == 0
    for r in transcript:
        assert hashlib.sha256(r['text'].encode()).hexdigest() == r['sha256']
    report.update(status='PASS', page=identity['page'], model=task['model'], model_calls=task['steps'],
                  tool_calls=len(observations), checkpoint=transaction['status'], final_capture='EXACT_OUTPUT_MATCH',
                  event_kinds=kinds)
except BaseException as error:
    report.update(status='FAIL', error=str(error))
    raise
finally:
    (path / (TX + '.json')).write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(report, indent=2, ensure_ascii=False))
