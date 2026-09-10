"""Content-light audit summaries for append-only HumanOS events.

Governed payloads may live in transcript/task/file-plan stores. The immutable events
ledger keeps only identifiers, bounded metadata and keyed proofs of those payloads.
"""
import json

FORBIDDEN_AUDIT_KEYS = frozenset({
    'text', 'content', 'stdout', 'final', 'proposal', 'messages', 'input',
    'excerpt', 'summary', 'rationale',
})


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def byte_count(value):
    material = value if isinstance(value, str) else encode(value)
    return len(material.encode('utf-8'))


def protected_digest(book, value):
    material = value if isinstance(value, str) else encode(value)
    return book.content_digest(material)


def assert_content_light(value, path='payload'):
    """Reject raw content-bearing keys anywhere in a newly appended audit event."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_AUDIT_KEYS:
                raise ValueError('Content-bearing audit field is forbidden: ' + path + '.' + key)
            assert_content_light(item, path + '.' + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_content_light(item, path + '[' + str(index) + ']')
    return True


def request_summary(book, request):
    """Bind the exact request without persisting content-bearing arguments."""
    result = {
        'request_digest': protected_digest(book, request),
        'request_bytes': byte_count(request),
    }
    if not isinstance(request, dict):
        return result
    for key in ('name', 'path', 'source', 'destination', 'plan_id', 'tab_id', 'offset'):
        value = request.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            if key in request:
                result[key] = value
    if 'content' in request:
        result['content_digest'] = protected_digest(book, request['content'])
        result['content_bytes'] = byte_count(request['content'])
    return result


def context_summary(book, packet):
    records = []
    for record in packet.get('records', []) if isinstance(packet, dict) else []:
        if not isinstance(record, dict):
            continue
        item = {}
        for key in ('source', 'evidence'):
            if key in record:
                item[key] = record[key]
        if isinstance(record.get('text'), str):
            item['content_digest'] = protected_digest(book, record['text'])
            item['content_bytes'] = byte_count(record['text'])
        elif isinstance(record.get('sha256'), str):
            item['legacy_hash_digest'] = protected_digest(book, record['sha256'])
        records.append(item)
    recent = []
    for row in packet.get('recent_transcript_sources', []) if isinstance(packet, dict) else []:
        if not isinstance(row, dict):
            continue
        item = {key: row[key] for key in ('seq', 'tx', 'role') if key in row}
        stored = row.get('sha256') or row.get('content_digest')
        if isinstance(stored, str):
            item['record_digest'] = protected_digest(book, stored)
        recent.append(item)
    result = {
        'packet_digest': protected_digest(book, packet),
        'packet_bytes': byte_count(packet),
        'records': records,
        'recent_transcript_sources': recent,
    }
    if isinstance(packet, dict):
        if 'missing' in packet:
            result['missing'] = packet['missing']
        if 'exclusions' in packet:
            result['exclusions'] = packet['exclusions']
    return result


def model_response_summary(book, model, proposal):
    result = {
        'model': model,
        'response_kind': ('final' if isinstance(proposal, dict) and 'final' in proposal else
                          'tool' if isinstance(proposal, dict) and 'tool' in proposal else 'invalid'),
        'response_digest': protected_digest(book, proposal),
        'response_bytes': byte_count(proposal),
    }
    if isinstance(proposal, dict) and isinstance(proposal.get('tool'), dict):
        result['tool_request'] = request_summary(book, proposal['tool'])
    return result


def exception_summary(book, error):
    text = str(error)
    return {
        'error_type': type(error).__name__,
        'error_digest': protected_digest(book, text),
        'error_bytes': byte_count(text),
    }


def observation_summary(book, request, observation):
    result = {
        'tool': request.get('name') if isinstance(request, dict) else None,
        'result_digest': protected_digest(book, observation),
        'result_bytes': byte_count(observation),
    }
    if isinstance(observation, dict):
        for key in ('ok', 'authorization', 'source', 'truncated', 'next_offset', 'total_bytes'):
            if key in observation:
                result[key] = observation[key]
        stdout = observation.get('stdout')
        if isinstance(stdout, str):
            result['stdout_digest'] = protected_digest(book, stdout)
            result['stdout_bytes'] = byte_count(stdout)
        stderr = observation.get('stderr')
        if isinstance(stderr, str) and stderr:
            result['error_type'] = stderr.split(':', 1)[0][:120]
            result['error_digest'] = protected_digest(book, stderr)
            result['error_bytes'] = byte_count(stderr)
        if isinstance(observation.get('sha256'), str):
            result['legacy_content_hash_digest'] = protected_digest(book, observation['sha256'])
        if isinstance(observation.get('content_digest'), str):
            result['content_digest'] = observation['content_digest']
        artifacts = observation.get('artifacts')
        if isinstance(artifacts, list):
            result['artifacts'] = [
                {
                    **({'path': item['path']} if isinstance(item, dict) and 'path' in item else {}),
                    'artifact_digest': protected_digest(book, item),
                }
                for item in artifacts
            ]
    if isinstance(request, dict):
        for key in ('path', 'source', 'destination', 'plan_id', 'tab_id', 'offset'):
            if key in request:
                result.setdefault(key, request[key])
    return result


def plan_summary(book, plan):
    return {
        'plan_id': plan['plan_id'],
        'plan_digest': protected_digest(book, plan),
        'move_count': len(plan.get('moves', [])),
        'workspace': plan.get('workspace', {}).get('path'),
        'has_metadata': bool(plan.get('metadata')),
    }


def state_summary(book, plan_id, state):
    inflight = state.get('inflight') if isinstance(state, dict) else None
    marker = None
    if isinstance(inflight, dict):
        marker = {key: inflight[key] for key in ('index', 'undo') if key in inflight}
    return {
        'plan_id': plan_id,
        'state_digest': protected_digest(book, state),
        'status': state.get('status') if isinstance(state, dict) else None,
        'completed_count': len(state.get('completed', [])) if isinstance(state, dict) else 0,
        'undone_count': len(state.get('undone', [])) if isinstance(state, dict) else 0,
        'inflight': marker,
        'has_error': bool(state.get('error')) if isinstance(state, dict) else False,
    }


def classification_request_summary(book, source, proof, excerpt, method, model):
    result = {
        'source': source,
        'source_proof_digest': protected_digest(book, proof),
        'source_bytes': proof.get('size') if isinstance(proof, dict) else None,
        'method': method,
        'model': model,
    }
    if isinstance(excerpt, str) and excerpt:
        result['excerpt_digest'] = protected_digest(book, excerpt)
        result['excerpt_bytes'] = byte_count(excerpt)
    return result


def classification_response_summary(book, request_audit, decision):
    return {
        **request_audit,
        'decision_digest': protected_digest(book, decision),
        'decision_bytes': byte_count(decision),
        'destination_folder': decision.get('destination_folder') if isinstance(decision, dict) else None,
        'confidence': decision.get('confidence') if isinstance(decision, dict) else None,
    }
