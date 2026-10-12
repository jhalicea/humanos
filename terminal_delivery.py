"""Bounded, fail-closed contract for owner-facing shell instructions.

This checks text before it reaches the terminal delivery sink. It does not execute
the proposed command. Unsupported shell forms require a new, reviewed contract.
"""
import re
import shlex
import sys
from pathlib import PurePosixPath


POLICY = ("Terminal instructions for Jon must be one bash copyblock. Use absolute "
          "paths independent of cwd, include all setup and stop guards, and no "
          "placeholders or manual edits. Only read-only commands supported by the "
          "HumanOS terminal delivery validator and the reviewed synthetic smoke "
          "may be proposed; unsupported shell "
          "actions need explicit review before delivery.")
POLICY_ID = 'terminal-delivery-v1'
APPROVED_SYNTHETIC_SCRIPTS = frozenset({
    '/Users/jhalicea/Developer/10_Repos/humanos/scripts/smoke_codex_import.py',
})
APPROVED_REPO = '/Users/jhalicea/Developer/10_Repos/humanos'
_FENCE = re.compile(r"```([^\n]*)\n(.*?)\n```", re.S)
_COMMAND = re.compile(
    r"(?:^|[`])\s*(?:python3|python|/usr/bin/env|cd|git|bash|sh|zsh|pytest|pip|curl|rm|mv|cp|sudo|chmod|chown|make|export|brew|npm|uv)\b|"
    r"(?:^|[`])\s*humanos\s+--|"
    r"(?:^|[`])\s*(?:\./|/Users/|/usr/bin/|/bin/)|"
    r"\b(?:run|execute|paste|type)\s+(?:python3|python|git|cd|/usr/bin/|/bin/|\./)", re.M | re.I)
_PLACEHOLDER = re.compile(r"<[^>]+>|\{\{.*?\}\}|\b(?:TODO|REPLACE_ME|YOUR_PATH)\b", re.I)


class TerminalDeliveryError(ValueError):
    pass


def _absolute_file(value):
    return (value.startswith('/') and not value.startswith('//') and
            all(part not in ('.', '..') for part in PurePosixPath(value).parts))


def validate_terminal_delivery(response):
    """Return response unchanged, or reject executable guidance before delivery.

    Supported grammar: set -e; one or more literal test -f/-d absolute guards;
    one reviewed absolute Python smoke, repo listing, or Git status command.
    No shell expansion, redirection, chaining, writes, or branch mutation.
    """
    if not isinstance(response, str):
        raise TerminalDeliveryError('terminal response must be text')
    fences = list(_FENCE.finditer(response))
    shell_fences = [match for match in fences if match.group(1).strip().lower() in ('bash', 'sh', 'zsh', 'shell')]
    if not shell_fences and not _COMMAND.search(response):
        return response
    if len(fences) != 1 or len(shell_fences) != 1:
        raise TerminalDeliveryError('terminal instructions require exactly one bash copyblock')
    block = shell_fences[0]
    if block.group(1).strip().lower() != 'bash':
        raise TerminalDeliveryError('terminal copyblock must be labeled bash')
    outside = response[:block.start()] + response[block.end():]
    if _COMMAND.search(outside) or _PLACEHOLDER.search(response):
        raise TerminalDeliveryError('terminal guidance outside copyblock or placeholder')
    lines = [line.strip() for line in block.group(2).splitlines() if line.strip()]
    if len(lines) < 3 or lines[0] != 'set -e':
        raise TerminalDeliveryError('copyblock needs set -e, absolute guard and command')
    guards = set()
    for line in lines[1:-1]:
        try:
            tokens = shlex.split(line, posix=True)
        except ValueError as error:
            raise TerminalDeliveryError('invalid guard syntax') from error
        if (len(tokens) != 3 or tokens[0] != 'test' or tokens[1] not in ('-f', '-d') or
                not _absolute_file(tokens[2]) or line != ' '.join(tokens)):
            raise TerminalDeliveryError('only literal test -f/-d absolute-path guards are supported')
        guards.add((tokens[1], tokens[2]))
    line = lines[-1]
    try:
        tokens = shlex.split(line, posix=True)
    except ValueError as error:
        raise TerminalDeliveryError('invalid invocation syntax') from error
    if line != ' '.join(tokens):
        raise TerminalDeliveryError('shell quoting or operators are unsupported')
    if tokens[:2] == ['/usr/bin/env', 'python3'] and len(tokens) == 3:
        if tokens[2] not in APPROVED_SYNTHETIC_SCRIPTS or guards != {('-f', tokens[2])}:
            raise TerminalDeliveryError('script is unsupported or missing its file guard')
    elif tokens == ['/bin/ls', APPROVED_REPO]:
        if guards != {('-d', APPROVED_REPO)}:
            raise TerminalDeliveryError('repository listing needs its directory guard')
    elif tokens == ['/usr/bin/git', '-C', APPROVED_REPO, 'status', '--short']:
        if guards != {('-d', APPROVED_REPO)}:
            raise TerminalDeliveryError('Git status needs its directory guard')
    else:
        raise TerminalDeliveryError('unsupported terminal action')
    return response


def main():
    """External handoff filter: emit only a validated response from stdin."""
    candidate = sys.stdin.read()
    try:
        sys.stdout.write(validate_terminal_delivery(candidate))
    except TerminalDeliveryError as error:
        print('Terminal delivery rejected: ' + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
