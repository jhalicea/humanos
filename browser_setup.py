"""Owner-controlled local setup for the HumanOS Browser Bridge.

This module writes pairing/configuration artifacts outside the repository. It never
opens the Life Notebook, browser profile databases, cookies, credentials, or history.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import stat
import sys
import time
import urllib.parse
import uuid


HOST_NAME = "com.humanos.browser_bridge"
CONFIG_SCHEMA = 1
EXTENSION_PUBLIC_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAt7E2PNU8f8/U4XVaFCUxoHSXuKQ78r9d05O8dCH5QGfyzB0V9n/"
    "N8MMrBzO/F/jjFXGZ29Bv9jXFAqv417Y8DgFrENlhjRfdwoSfPe4QN4V6Ab90/R3tswF/RGSHwUwOX1M4gK+YCZ2SWeQfPdW"
    "IoXW9EZYMxqBNDrseK1lvST5QBmKCYfa65JzmtdIsUrAQHTmGuw6SDW4043uGXn8PKNYc7UQyxBXdYY4LNjqKX5hy9QWyNPR"
    "sNCSBKBLKdgSphHRsZiBkY3IClgzKgO6fFj7dk9yGUifQfHh+9OMoHVQXNd+bJ4t4BqGqnOfZPpVQlr4ByMZlc4RaqOq7ggg"
    "RjQIDAQAB"
)
EXTENSION_ID = "hdmlcfjlepjknagpdebdlnbdlnjoijbn"
BROWSER_CAPABILITIES = ("inspect", "navigate", "click", "type")
SEARCH_PROVIDERS = {
    "duckduckgo": ("duckduckgo.com", "https://duckduckgo.com/?q={query}"),
    "google": ("google.com", "https://www.google.com/search?q={query}"),
}
TARGETS = {
    "darwin": {
        "chrome": "Library/Application Support/Google/Chrome/NativeMessagingHosts",
        # Brave overrides its native-messaging lookup to Chrome's standard
        # user path on macOS (see brave-core BraveMainDelegate).
        "brave": "Library/Application Support/Google/Chrome/NativeMessagingHosts",
        "chromium": "Library/Application Support/Chromium/NativeMessagingHosts",
    },
    "linux": {
        "chrome": ".config/google-chrome/NativeMessagingHosts",
        "brave": ".config/BraveSoftware/Brave-Browser/NativeMessagingHosts",
        "chromium": ".config/chromium/NativeMessagingHosts",
    },
}
DARWIN_APPS = {
    "brave": ("Brave Browser.app",),
    "chrome": ("Google Chrome.app",),
    "chromium": ("Chromium.app",),
}
CONFIG_KEYS = frozenset({
    "schema_version", "target", "extension_id", "socket", "secret", "state",
    "hosts", "capabilities", "max_actions", "max_bytes", "run_ttl_seconds",
    "search_provider",
})


def extension_id_from_key(encoded_key=EXTENSION_PUBLIC_KEY):
    raw = base64.b64decode(encoded_key, validate=True)
    digest = hashlib.sha256(raw).digest()[:16]
    alphabet = "abcdefghijklmnop"
    return "".join(alphabet[(byte >> 4) & 0xF] + alphabet[byte & 0xF] for byte in digest)


def _platform_name(platform=None):
    value = platform or sys.platform
    if value.startswith("darwin"):
        return "darwin"
    if value.startswith("linux"):
        return "linux"
    raise ValueError("Browser setup currently supports macOS and Linux Chromium-family browsers")


def _home(home=None):
    return Path(home or Path.home()).expanduser().resolve()


def control_root(home=None):
    return _home(home) / ".humanos" / "browser"


def config_path(home=None):
    return control_root(home) / "runtime.json"


def manifest_directory(target, home=None, platform=None):
    platform_name = _platform_name(platform)
    if target not in TARGETS[platform_name]:
        raise ValueError("Unsupported browser target: " + str(target))
    return _home(home) / TARGETS[platform_name][target]


def native_manifest_path(target, home=None, platform=None):
    return manifest_directory(target, home, platform) / (HOST_NAME + ".json")


def detect_target(home=None, platform=None):
    platform_name = _platform_name(platform)
    if platform_name == "darwin":
        roots = [Path("/Applications"), _home(home) / "Applications"]
        for target in ("brave", "chrome", "chromium"):
            for app in DARWIN_APPS[target]:
                if any((root / app).exists() for root in roots):
                    return target
    else:
        # Linux installation discovery is intentionally conservative; callers can
        # select an explicit target when browser binaries are not on PATH.
        candidates = {
            "brave": ("brave-browser", "brave"),
            "chrome": ("google-chrome", "google-chrome-stable"),
            "chromium": ("chromium", "chromium-browser"),
        }
        for target in ("brave", "chrome", "chromium"):
            if any(shutil.which(binary) for binary in candidates[target]):
                return target
    raise ValueError("No supported Chromium-family browser detected; choose --browser-target brave|chrome|chromium")


def _validate_host(value):
    if not isinstance(value, str):
        raise ValueError("Browser host must be text")
    host = value.strip().lower().rstrip(".")
    if not host or len(host) > 253 or "/" in host or ":" in host or "*" in host or "@" in host:
        raise ValueError("Browser host must be a plain DNS hostname")
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError("Browser host is not a valid DNS hostname") from error
    labels = ascii_host.split(".")
    label = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
    if len(labels) < 2 or any(not label.fullmatch(item) for item in labels):
        raise ValueError("Browser host must be a valid DNS hostname")
    return ascii_host


def _ensure_private_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise PermissionError("HumanOS browser control path must be a real directory")
    os.chmod(path, 0o700)
    if stat.S_IMODE(path.stat().st_mode) != 0o700:
        raise PermissionError("HumanOS browser control directory must be mode 0700")
    if hasattr(os, "getuid") and path.stat().st_uid != os.getuid():
        raise PermissionError("HumanOS browser control directory must be owner-controlled")
    return path


def _private_file_ok(path, expected_mode=0o600):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        return False
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        return False
    if mode != expected_mode:
        os.chmod(path, expected_mode)
    return not hasattr(os, "getuid") or path.stat().st_uid == os.getuid()


def _atomic_private_write(path, data, mode):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.parent / ("." + path.name + ".pending-" + uuid.uuid4().hex)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(pending, flags, mode)
    try:
        raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        offset = 0
        while offset < len(raw):
            written = os.write(fd, raw[offset:])
            if written <= 0:
                raise OSError("short browser setup write")
            offset += written
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(pending, mode)
    os.replace(pending, path)
    directory = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _outside_repository(path, repo_root):
    path = Path(path).resolve()
    repo = Path(repo_root).resolve()
    if path == repo or path.is_relative_to(repo):
        raise PermissionError("Browser control state must stay outside the HumanOS repository")


def _secret(path):
    path = Path(path)
    if path.exists():
        if not _private_file_ok(path):
            raise PermissionError("Existing browser secret is not an owner-only regular file")
        raw = path.read_bytes()
        if len(raw) != 32:
            raise PermissionError("Existing browser secret is not 32 bytes")
        return raw
    raw = secrets.token_bytes(32)
    _atomic_private_write(path, raw, 0o600)
    return raw


def _launcher_text(python_executable, native_host, socket_path, secret_path):
    python_executable = str(Path(python_executable).resolve())
    native_host = str(Path(native_host).resolve())
    argv = [python_executable, native_host, "--socket", str(socket_path), "--secret", str(secret_path)]
    # The browser passes its origin as argv[1] to this launcher. The launcher
    # intentionally does not forward that untrusted argument; allowed_origins in
    # the browser manifest is the admission boundary.
    command = " ".join(shlex.quote(item) for item in argv)
    return "#!/bin/sh\nexec " + command + "\n"


def _runtime_record(target, root, hosts, search_provider):
    search_host, _ = SEARCH_PROVIDERS[search_provider]
    normalized = sorted(set([_validate_host(search_host), *(_validate_host(h) for h in hosts)]))
    return {
        "schema_version": CONFIG_SCHEMA,
        "target": target,
        "extension_id": EXTENSION_ID,
        "socket": str(root / "bridge.sock"),
        "secret": str(root / "secret.bin"),
        "state": str(root / "state"),
        "hosts": normalized,
        "capabilities": list(BROWSER_CAPABILITIES),
        "max_actions": 100,
        "max_bytes": 1_000_000,
        "run_ttl_seconds": 28_800,
        "search_provider": search_provider,
    }


def setup_browser(repo_root, target="auto", hosts=(), search_provider="duckduckgo",
                  home=None, platform=None, python_executable=None):
    """Create/refresh HumanOS-owned browser pairing artifacts outside Git."""
    repo_root = Path(repo_root).resolve()
    root = control_root(home)
    _outside_repository(root, repo_root)
    _ensure_private_dir(root)
    _ensure_private_dir(root / "state")
    if extension_id_from_key() != EXTENSION_ID:
        raise RuntimeError("Bundled browser extension key does not match the pinned extension ID")
    platform_name = _platform_name(platform)
    if target == "auto":
        target = detect_target(home=home, platform=platform_name)
    if target not in TARGETS[platform_name]:
        raise ValueError("Unsupported browser target: " + str(target))
    if search_provider not in SEARCH_PROVIDERS:
        raise ValueError("Unsupported browser search provider: " + str(search_provider))

    secret_path = root / "secret.bin"
    _secret(secret_path)
    socket_path = root / "bridge.sock"
    launcher = root / "native-host"
    native_host = repo_root / "browser_native_host.py"
    if not native_host.is_file():
        raise FileNotFoundError("HumanOS browser_native_host.py is missing from repository")
    _atomic_private_write(
        launcher,
        _launcher_text(python_executable or sys.executable, native_host, socket_path, secret_path),
        0o700,
    )

    manifest = {
        "name": HOST_NAME,
        "description": "HumanOS Browser Bridge native host",
        "path": str(launcher),
        "type": "stdio",
        "allowed_origins": ["chrome-extension://" + EXTENSION_ID + "/"],
    }
    manifest_path = native_manifest_path(target, home=home, platform=platform_name)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_private_write(manifest_path, json.dumps(manifest, sort_keys=True, indent=2) + "\n", 0o600)

    runtime = _runtime_record(target, root, hosts, search_provider)
    _atomic_private_write(config_path(home), json.dumps(runtime, sort_keys=True, indent=2) + "\n", 0o600)
    return browser_status(repo_root, home=home, platform=platform_name)


def _read_runtime_record(home=None, platform=None):
    path = config_path(home)
    if not path.exists():
        return None
    if not _private_file_ok(path):
        raise PermissionError("Local browser runtime config must be an owner-only regular file")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Local browser runtime config is invalid JSON") from error
    if not isinstance(record, dict) or set(record) != CONFIG_KEYS:
        raise ValueError("Local browser runtime config has unexpected or missing fields")
    if record["schema_version"] != CONFIG_SCHEMA:
        raise ValueError("Unsupported local browser runtime config schema")
    if record["extension_id"] != EXTENSION_ID:
        raise PermissionError("Local browser runtime config extension identity differs from HumanOS")
    platform_name = _platform_name(platform)
    if record["target"] not in TARGETS.get(platform_name, {}):
        raise ValueError("Local browser runtime config target is unsupported on this platform")
    if record["search_provider"] not in SEARCH_PROVIDERS:
        raise ValueError("Local browser runtime config search provider is unsupported")
    if record["capabilities"] != list(BROWSER_CAPABILITIES):
        raise PermissionError("Local browser capability set differs from the supported HumanOS set")
    if type(record["max_actions"]) is not int or not 1 <= record["max_actions"] <= 1000:
        raise ValueError("Local browser action budget is invalid")
    if type(record["max_bytes"]) is not int or not 1 <= record["max_bytes"] <= 1_048_576:
        raise ValueError("Local browser byte budget is invalid")
    if type(record["run_ttl_seconds"]) is not int or not 60 <= record["run_ttl_seconds"] <= 86_400:
        raise ValueError("Local browser authorization window is invalid")
    record["hosts"] = sorted(set(_validate_host(host) for host in record["hosts"]))
    search_host, _ = SEARCH_PROVIDERS[record["search_provider"]]
    if _validate_host(search_host) not in record["hosts"]:
        raise PermissionError("Configured search provider host is outside browser allowlist")
    for name in ("socket", "secret", "state"):
        path_value = Path(record[name])
        if not path_value.is_absolute():
            raise PermissionError("Local browser " + name + " path must be absolute")
    secret_path = Path(record["secret"])
    if not _private_file_ok(secret_path) or len(secret_path.read_bytes()) != 32:
        raise PermissionError("Local browser secret is missing or unsafe")
    state = Path(record["state"])
    _ensure_private_dir(state)
    return record


def load_local_browser_config(home=None, clock=time.time):
    """Return a runtime BrowserBroker config, or None when local pairing is absent."""
    record = _read_runtime_record(home)
    if record is None:
        return None
    _, search_url = SEARCH_PROVIDERS[record["search_provider"]]
    return {
        "envelope": {
            "run_id": "browser-" + uuid.uuid4().hex,
            "authorization": "Owner-configured HumanOS browser bridge HOS-BROWSER-001",
            "expires": int(clock()) + record["run_ttl_seconds"],
            "hosts": record["hosts"],
            "capabilities": record["capabilities"],
            "max_actions": record["max_actions"],
            "max_bytes": record["max_bytes"],
        },
        "state": record["state"],
        "socket": record["socket"],
        "secret": record["secret"],
        "search_url": search_url,
        "target": record["target"],
        "extension_id": record["extension_id"],
    }


def browser_status(repo_root, home=None, platform=None):
    """Read setup facts without opening the Notebook or exposing secret bytes."""
    repo_root = Path(repo_root).resolve()
    platform_name = _platform_name(platform)
    path = config_path(home)
    base = {
        "configured": False,
        "extension_id": EXTENSION_ID,
        "extension_path": str(repo_root / "browser-extension"),
        "config_path": str(path),
    }
    if not path.exists():
        return base
    record = _read_runtime_record(home, platform=platform_name)
    manifest_path = native_manifest_path(record["target"], home=home, platform=platform_name)
    launcher = control_root(home) / "native-host"
    socket_path = Path(record["socket"])
    result = dict(base)
    result.update({
        "configured": True,
        "target": record["target"],
        "hosts": record["hosts"],
        "search_provider": record["search_provider"],
        "manifest_path": str(manifest_path),
        "manifest_installed": manifest_path.is_file() and _private_file_ok(manifest_path),
        "launcher_ready": launcher.is_file() and not launcher.is_symlink() and
                          stat.S_IMODE(launcher.stat().st_mode) == 0o700,
        "secret_ready": _private_file_ok(Path(record["secret"])) and
                        len(Path(record["secret"]).read_bytes()) == 32,
        "socket_present": socket_path.exists() and socket_path.is_socket(),
        "selected_tab_required": True,
    })
    return result


def remove_browser_setup(repo_root, home=None, platform=None):
    """Remove only HumanOS-owned pairing artifacts after an explicit owner command."""
    repo_root = Path(repo_root).resolve()
    _outside_repository(control_root(home), repo_root)
    record = _read_runtime_record(home, platform=platform)
    if record is None:
        return {"removed": False, "reason": "HumanOS browser setup is not configured"}
    manifest_path = native_manifest_path(record["target"], home=home, platform=platform)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_path = str(control_root(home) / "native-host")
        if manifest.get("name") != HOST_NAME or manifest.get("path") != expected_path:
            raise PermissionError("Refusing to remove a native-host manifest not owned by this HumanOS setup")
        manifest_path.unlink()
    root = control_root(home)
    if root.is_symlink() or root.name != "browser" or root.parent.name != ".humanos":
        raise PermissionError("Refusing to remove unexpected browser control directory")
    shutil.rmtree(root)
    return {"removed": True, "manifest_path": str(manifest_path)}
