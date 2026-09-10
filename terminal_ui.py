"""Small dependency-free terminal chooser for HumanOS."""
import os
import select
import sys


def _numbered_choice(items, prompt, input_fn=input, output=None):
    output = output or sys.stderr
    output.write(prompt + "\n")
    for index, item in enumerate(items, 1):
        output.write(f"  {index}. {item}\n")
    output.flush()
    try:
        value = input_fn("Choose number (blank cancels): ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not value:
        return None
    try:
        index = int(value) - 1
    except ValueError:
        return None
    return items[index] if 0 <= index < len(items) else None


def choose_reference(items, prompt="Which file do you mean?", stdin=None, output=None):
    stdin = stdin or sys.stdin
    output = output or sys.stderr
    items = list(items)
    if not items:
        return None
    if len(items) == 1:
        return items[0]
    if not getattr(stdin, "isatty", lambda: False)():
        return None
    if os.name != "posix":
        return _numbered_choice(items, prompt, output=output)

    import termios
    import tty

    fd = stdin.fileno()
    old = termios.tcgetattr(fd)
    selected = 0
    total_lines = len(items) + 2

    def draw(first=False):
        if not first:
            output.write(f"\x1b[{total_lines}A")
        output.write(prompt + "\x1b[K\n")
        for index, item in enumerate(items):
            marker = "❯" if index == selected else " "
            output.write(f" {marker} {item}\x1b[K\n")
        output.write("↑/↓ move • Enter select • Esc cancel\x1b[K\n")
        output.flush()

    try:
        tty.setraw(fd)
        draw(first=True)
        while True:
            ch = os.read(fd, 1)
            if ch in (b"\r", b"\n"):
                output.write("\n")
                output.flush()
                return items[selected]
            if ch == b"\x03":
                raise KeyboardInterrupt
            if ch == b"\x1b":
                ready, _, _ = select.select([fd], [], [], 0.05)
                if not ready:
                    output.write("\n")
                    output.flush()
                    return None
                tail = os.read(fd, 2)
                if tail == b"[A":
                    selected = (selected - 1) % len(items)
                    draw()
                    continue
                if tail == b"[B":
                    selected = (selected + 1) % len(items)
                    draw()
                    continue
                output.write("\n")
                output.flush()
                return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
