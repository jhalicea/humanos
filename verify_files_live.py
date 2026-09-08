"""Opt-in local-model acceptance using only temporary, synthetic user files.

Run with ``python3 verify_files_live.py``. Model/endpoint come from config.json
and the same environment overrides as HumanOSRuntime. No personal vault is used.
The two affirmative approvals are synthetic test input, never standing consent.
"""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from server import HumanOSRuntime


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    base = Path(__file__).resolve().parent
    config = json.loads((base / 'config.json').read_text())
    passed = []
    active = None
    with tempfile.TemporaryDirectory(prefix='humanos-files-live-') as folder:
        root = Path(folder)
        workspace = root / 'workspace'
        workspace.mkdir()
        fixtures = {
            'runtime-check.txt': b'Verification phrase: continuity belongs to Jon.\nVerification code: HOS-LOCAL-62947.\n',
            'duplicate-a.bin': b'\x00synthetic duplicate fixture\xff',
            'duplicate-b.bin': b'\x00synthetic duplicate fixture\xff',
            'Existing/keep.txt': b'Existing content must never be overwritten.\n',
        }
        for name, content in fixtures.items():
            target = workspace / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        runtime = HumanOSRuntime(config=dict(config, vault=str(root / 'vault'),
                                            workspace=str(workspace), core=str(base / 'core')))
        book = runtime.book
        identity = book.bind('Jon', 'Isolated synthetic file acceptance')

        def tool_results(tx):
            return [json.loads(row['payload']) for row in book.db.execute(
                "SELECT payload FROM events WHERE tx=? AND kind='TOOL_RESULT' ORDER BY seq", (tx,))]

        def structured_result(tx):
            results = tool_results(tx)
            check(results and results[-1]['ok'], 'Expected successful structured tool observation')
            return json.loads(results[-1]['stdout'])

        def approve(prompt):
            # Mimic input() displaying its prompt while providing test-owned input.
            print(prompt, end='', flush=True)
            return 'yes'

        def turn(name, text, approval=False, failed=False):
            nonlocal active
            active = name
            tx = 'TX-FILES-LIVE-' + name
            runtime.agent.authorize = lambda request: runtime.authorize(tx, request)
            approval_output = io.StringIO()
            with patch('sys.stdin.isatty', return_value=approval), \
                    patch('builtins.input', side_effect=approve), redirect_stdout(approval_output):
                final = runtime.agent.run(tx, identity['hcid'], text)
            output = io.StringIO()
            runtime.deliver(tx, final, output)
            state = book.task(tx)
            transcript = [dict(row) for row in book.db.execute(
                'SELECT * FROM transcript WHERE tx=? ORDER BY ordinal', (tx,))]
            check(transcript[0]['role'] == 'HUMAN' and transcript[0]['text'] == text,
                  'Exact human input did not survive capture')
            check(transcript[-1]['role'] == 'ASSISTANT' and transcript[-1]['text'] == final,
                  'Final assistant transcript differs')
            check(output.getvalue().encode() == (transcript[-1]['text'] + '\n').encode(),
                  'Delivered final differs byte-for-byte from saved final')
            check(book.get_transaction(tx)['status'] == 'CHECKPOINTED', 'Notebook not checkpointed')
            check(state['delivery'] == 'WRITTEN_TO_OUTPUT_STREAM', 'Delivery not confirmed')
            check(bool(state.get('failure_finalized')) == failed, 'Unexpected task outcome: ' + final)
            for entry in transcript:
                check(hashlib.sha256(entry['text'].encode()).hexdigest() == entry['sha256'],
                      'Transcript hash mismatch')
            if approval:
                check(len(transcript) == 4, 'Expected input, exact approval prompt, yes, and final')
                check(transcript[1]['role'] == 'ASSISTANT' and transcript[2]['text'] == 'yes',
                      'Approval conversation not captured')
                check(approval_output.getvalue() == transcript[1]['text'] + '\n',
                      'Approval prompt output differs from capture')
                decisions = [json.loads(row['payload']) for row in book.db.execute(
                    "SELECT payload FROM events WHERE tx=? AND kind='AUTHORIZATION'", (tx,))]
                check(any(item['allowed'] for item in decisions), 'Human approval not audited')
            else:
                check(not approval_output.getvalue(), 'Unexpected human approval request')
            book.verify()
            return tx, final

        def finish(name):
            passed.append(name)
            calls = book.task('TX-FILES-LIVE-' + name)['steps']
            print(name + ': PASS (' + str(calls) + ' model calls)', flush=True)

        try:
            print('Local backend: ' + runtime.model + ' at ' + runtime.ollama_url, flush=True)
            for name, text in [('greeting', 'hi'), ('conversation', "how's everything?")]:
                tx, final = turn(name, text)
                check(book.task(tx)['steps'] > 0 and final.strip(), 'Expected real model conversation')
                finish(name)
            for name, text in [('capabilities', 'can you organize files?'),
                               ('capability-followup', 'why not? what do you need to do that?')]:
                tx, final = turn(name, text)
                check('organize' in final.casefold() and 'plan' in final.casefold(), final)
                check(any(result['ok'] for result in tool_results(tx)), 'Capabilities were guessed')
                finish(name)
            for name, text in [('source-location', 'ok can you read the file where this instance is running?'),
                               ('source-correction', "that doesn't make sense how are you a file interface but can't read a file read server.py")]:
                tx, final = turn(name, text)
                check('class HumanOSRuntime' in final and 'server.py' in final, final)
                check(any(result['ok'] for result in tool_results(tx)), 'Source read was not executed')
                finish(name)
            tx, final = turn('missing-file', '/read missing.txt', failed=True)
            check('missing.txt' in final and not (workspace / 'missing.txt').exists(), final)
            finish('missing-file')
            tx, final = turn('after-failure', 'hello again')
            check(book.task(tx)['steps'] > 0 and final.strip(), 'Conversation did not continue')
            finish('after-failure')
            tx, final = turn('model-file-loop', 'Read runtime-check.txt and tell me its verification phrase and code.')
            check('continuity belongs to Jon' in final and 'HOS-LOCAL-62947' in final, final)
            check(book.task(tx)['steps'] >= 2, 'Expected model, tool observation, then model continuation')
            check(any(result['ok'] and 'HOS-LOCAL-62947' in result['stdout'] for result in tool_results(tx)),
                  'Expected successful real workspace read')
            finish('model-file-loop')
            tx, final = turn('scan', '/files')
            report = structured_result(tx)
            check(not report['truncated'], 'Fixture scan unexpectedly truncated')
            check(set(fixtures) <= {entry['path'] for entry in report['entries']}, 'Fixture files missing from scan')
            finish('scan')
            tx, final = turn('duplicates', '/duplicates')
            report = structured_result(tx)
            check(not report['incomplete'], 'Fixture duplicate report incomplete')
            check(any(set(group['files']) == {'duplicate-a.bin', 'duplicate-b.bin'} for group in report['groups']),
                  'Exact binary duplicate pair not reported')
            check(all((workspace / name).read_bytes() == content for name, content in fixtures.items()),
                  'Read-only duplicate inspection changed files')
            finish('duplicates')
            tx, final = turn('preview', '/organize')
            plan = structured_result(tx)
            check(plan['status'] == 'PREVIEW' and len(plan['moves']) == 3, 'Unexpected organization preview')
            check(all((workspace / name).read_bytes() == content for name, content in fixtures.items()),
                  'Preview mutated file contents or paths')
            finish('preview')
            tx, final = turn('apply', '/apply ' + plan['plan_id'], approval=True)
            check(structured_result(tx)['status'] == 'APPLIED', 'Plan not applied')
            for move in plan['moves']:
                check(not (workspace / move['source']).exists(), 'Source path unexpectedly retained')
                check((workspace / move['destination']).read_bytes() == fixtures[move['source']], 'Moved bytes differ')
            check((workspace / 'Existing/keep.txt').read_bytes() == fixtures['Existing/keep.txt'], 'Existing file overwritten')
            check(sum(1 for path in workspace.rglob('*') if path.is_file()) == len(fixtures), 'File loss or duplication')
            finish('apply')
            tx, final = turn('undo', '/undo ' + plan['plan_id'], approval=True)
            check(structured_result(tx)['status'] == 'UNDONE', 'Plan not undone')
            check(all((workspace / name).read_bytes() == content for name, content in fixtures.items()), 'Undo failed to restore originals')
            check(sum(1 for path in workspace.rglob('*') if path.is_file()) == len(fixtures), 'Undo lost or duplicated files')
            finish('undo')
            book.verify()
            check(book.delivery_pending() == [], 'Unconfirmed output remains')
            print(str(len(passed)) + '/14 live turns passed, 0 failed; exact final output, approval capture, '
                  'Notebook readback, real model tool loop, file preservation and undo verified.', flush=True)
        except BaseException as error:
            # This isolated vault contains only the synthetic inputs above.
            tx = 'TX-FILES-LIVE-' + str(active)
            evidence = [dict(row) for row in book.db.execute(
                "SELECT kind,payload FROM events WHERE tx=? AND kind IN ('MODEL_RESPONSE','MODEL_RESPONSE_REJECTED','TOOL_RESULT')",
                (tx,))]
            print(json.dumps({'passed': len(passed), 'failed': 1, 'failed_case': active,
                              'error': str(error), 'events': evidence}, indent=2), flush=True)
            raise
        finally:
            book.close()


if __name__ == '__main__':
    main()
