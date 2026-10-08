import ast
import pathlib
import re
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON_EXCLUDE_DIRS = {"tests", ".git", ".venv", "venv", "__pycache__"}
JAVASCRIPT_SUFFIXES = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
BODYFIX_MODULE_PREFIXES = ("bodyfix", "bodyfixos", "body_fix")


def _iter_source_files():
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = set(path.relative_to(REPO_ROOT).parts)
        if relative_parts & {".git", ".venv", "venv", "__pycache__"}:
            continue
        if path.suffix == ".py" and "tests" not in relative_parts:
            yield path
        elif path.suffix in JAVASCRIPT_SUFFIXES:
            yield path


def _python_bodyfix_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.lower().startswith(BODYFIX_MODULE_PREFIXES):
                    findings.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.lower().startswith(BODYFIX_MODULE_PREFIXES):
                findings.append((node.lineno, node.module))
    return findings


def _javascript_bodyfix_imports(path):
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?:from\s+|import\s*\(|require\s*\()\s*['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    findings = []
    for match in pattern.finditer(text):
        module = match.group(1)
        normalized = module.lower().replace("-", "").replace("_", "")
        if "bodyfixos" in normalized or normalized.startswith("bodyfix"):
            line = text.count("\n", 0, match.start()) + 1
            findings.append((line, module))
    return findings


class CrossProductBoundaryTests(unittest.TestCase):
    def test_humanos_source_does_not_import_bodyfixos(self):
        findings = []
        for path in _iter_source_files():
            try:
                if path.suffix == ".py":
                    imports = _python_bodyfix_imports(path)
                else:
                    imports = _javascript_bodyfix_imports(path)
            except (SyntaxError, UnicodeDecodeError) as exc:
                self.fail(f"Could not inspect {path.relative_to(REPO_ROOT)}: {exc}")

            for line, module in imports:
                findings.append(
                    f"{path.relative_to(REPO_ROOT)}:{line} imports {module!r}"
                )

        self.assertEqual(
            findings,
            [],
            "HumanOS and BodyFixOS are independent products. Direct BodyFixOS source "
            "imports are prohibited; use a separately approved external connector "
            "contract instead. Findings:\n" + "\n".join(findings),
        )


if __name__ == "__main__":
    unittest.main()
