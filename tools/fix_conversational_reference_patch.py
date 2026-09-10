from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path, old, new):
    target = ROOT / path
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one correction anchor, found {count}")
    target.write_text(text.replace(old, new, 1))


# Keep ordinary/recall tasks on permission scope v4. Only a turn that actually
# binds a verified conversational reference needs the new v5 schema.
replace_once(
    "permissions.py",
    "def task_scope(row, workspace, version=5, reference_binding=None):\n",
    "def task_scope(row, workspace, version=4, reference_binding=None):\n",
)
replace_once(
    "engine.py",
    "                         'permissions': task_scope(row, self.tools.workspace, reference_binding=reference_binding),\n",
    "                         'permissions': task_scope(row, self.tools.workspace,\n"
    "                                                   version=5 if reference_binding else 4,\n"
    "                                                   reference_binding=reference_binding),\n",
)

# Bare Escape must cancel immediately rather than blocking while waiting for two
# more bytes. Arrow escape sequences get a short bounded read window.
replace_once(
    "terminal_ui.py",
    "import os\nimport sys\n",
    "import os\nimport select\nimport sys\n",
)
replace_once(
    "terminal_ui.py",
    "            if ch == b\"\\x1b\":\n"
    "                tail = os.read(fd, 2)\n"
    "                if tail == b\"[A\":\n",
    "            if ch == b\"\\x1b\":\n"
    "                ready, _, _ = select.select([fd], [], [], 0.05)\n"
    "                if not ready:\n"
    "                    output.write(\"\\n\")\n"
    "                    output.flush()\n"
    "                    return None\n"
    "                tail = os.read(fd, 2)\n"
    "                if tail == b\"[A\":\n",
)

print("Conversational reference corrections applied.")
