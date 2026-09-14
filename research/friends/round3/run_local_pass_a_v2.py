#!/usr/bin/env python3
"""Run EXP-R3-A-001 against local Ollama models with stronger evidence capture.

V2 preserves the original v1 harness as experiment history. Changes:
- explicitly disables model 'thinking' output when the Ollama runtime supports it;
- never stores hidden thinking text, only whether such a field was present and its length;
- records response/message keys on empty-visible-response failures;
- preserves partial visible outputs instead of calling every non-empty answer complete;
- checks required Pass A sections before marking a local run complete.

Research harness only. It does not modify HumanOS authority, canonical state, or
Constitutional text. Each model receives only the frozen Pass A instructions and
ratified Constitution text from the checked-out research branch.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "http://127.0.0.1:11434"
DEFAULT_PROMPT = "research/friends/round3/PASS_A_CLEANROOM_PROMPT.md"
DEFAULT_CONSTITUTION = "core/constitution.md"
DEFAULT_OUT_DIR = "research/friends/round3/local_runs"

REQUIRED_MARKERS = [
    "TRIAL 1", "TRIAL 2", "TRIAL 3", "TRIAL 4", "TRIAL 5", "TRIAL 6",
    "TRIAL 7", "TRIAL 8", "TRIAL 9", "TRIAL 10", "TRIAL 11", "TRIAL 12",
    "TRY TO KILL THE CONSTITUTION",
    "PROPOSE THE MINIMUM CHANGE SET",
    "SCORE THE CONSTITUTION",
    "THE ONE EXPERIMENT",
    "FINAL VERDICT",
    "STRONGEST CONSTITUTIONAL IDEA",
    "MESSAGE TO THE OTHER FRIENDS",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def slug_model(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "model"


def validate_loopback_endpoint(endpoint: str) -> str:
    parsed = urllib.parse.urlparse(endpoint)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Only a local loopback HTTP Ollama endpoint is allowed")
    return endpoint.rstrip("/")


class Ollama:
    def __init__(self, endpoint: str, timeout: int):
        self.endpoint = validate_loopback_endpoint(endpoint)
        self.timeout = timeout
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _json(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with self.opener.open(req, timeout=self.timeout) as response:
            raw = response.read()
        return json.loads(raw)

    def tags(self):
        return self._json("GET", "/api/tags")

    def show(self, model: str):
        return self._json("POST", "/api/show", {"model": model})

    def chat(self, model: str, content: str, *, num_ctx: int, num_predict: int, seed: int):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
                "seed": seed,
                "num_ctx": num_ctx,
                "num_predict": num_predict,
            },
        }
        return self._json("POST", "/api/chat", payload)


def context_length(show: dict) -> int | None:
    info = show.get("model_info") or {}
    values = []
    for key, value in info.items():
        if key.endswith(".context_length") or key == "context_length":
            try:
                values.append(int(value))
            except (TypeError, ValueError):
                pass
    return max(values) if values else None


def model_digest(tags: dict, model: str) -> str | None:
    for item in tags.get("models", []):
        if item.get("name") == model or item.get("model") == model:
            return item.get("digest")
    return None


def model_present(tags: dict, model: str) -> bool:
    return any(item.get("name") == model or item.get("model") == model for item in tags.get("models", []))


def build_input(prompt_text: str, constitution_text: str) -> str:
    return (
        prompt_text.rstrip()
        + "\n\n--- BEGIN RATIFIED CONSTITUTION V0.2 ---\n\n"
        + constitution_text.rstrip()
        + "\n\n--- END RATIFIED CONSTITUTION V0.2 ---\n"
    )


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def write_json(path: Path, value: dict):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compliance(content: str) -> tuple[list[str], list[str]]:
    upper = content.upper()
    found = [marker for marker in REQUIRED_MARKERS if marker in upper]
    missing = [marker for marker in REQUIRED_MARKERS if marker not in upper]
    return found, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="HumanOS FRIENDS Round 3 local Pass A harness v2")
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--constitution", default=DEFAULT_CONSTITUTION)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--max-output-tokens", type=int, default=12000)
    parser.add_argument("--min-output-tokens", type=int, default=5000)
    parser.add_argument("--context-cap", type=int, default=131072)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    prompt_path = (root / args.prompt).resolve()
    constitution_path = (root / args.constitution).resolve()
    out_dir = (root / args.out_dir).resolve()

    for path in (prompt_path, constitution_path):
        if not path.is_file():
            print(f"ERROR: required input not found: {path}", file=sys.stderr)
            return 2

    prompt_raw = prompt_path.read_bytes()
    constitution_raw = constitution_path.read_bytes()
    combined = build_input(prompt_raw.decode("utf-8"), constitution_raw.decode("utf-8"))
    combined_hash = sha256_text(combined)
    input_estimate = estimate_tokens(combined)

    out_dir.mkdir(parents=True, exist_ok=True)
    ollama = Ollama(args.endpoint, args.timeout)

    try:
        tags = ollama.tags()
    except Exception as exc:
        print(f"ERROR: cannot reach local Ollama at {args.endpoint}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    inventory = sorted(item.get("name") or item.get("model") or "UNKNOWN" for item in tags.get("models", []))
    print("Local Ollama inventory:")
    for name in inventory:
        print(f"  - {name}")

    overall = 0
    for model in args.model:
        print(f"\n=== {model} ===")
        slug = slug_model(model)
        run_stamp = dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        run_id = f"R3-A-LOCAL-V2-{slug}-{run_stamp}"
        raw_path = out_dir / f"{run_id}_RAW.md"
        metadata_path = out_dir / f"{run_id}_METADATA.json"

        meta = {
            "experiment": "EXP-R3-A-001",
            "harness_version": "2",
            "pass": "A",
            "run_id": run_id,
            "model_requested": model,
            "provider": "LOCAL_OLLAMA",
            "endpoint": args.endpoint,
            "prompt_path": os.path.relpath(prompt_path, root),
            "prompt_sha256": sha256_bytes(prompt_raw),
            "constitution_path": os.path.relpath(constitution_path, root),
            "constitution_sha256": sha256_bytes(constitution_raw),
            "combined_input_sha256": combined_hash,
            "combined_input_bytes": len(combined.encode("utf-8")),
            "estimated_input_tokens_chars_div_4": input_estimate,
            "seed": args.seed,
            "temperature": 0,
            "think_requested": False,
            "status": "STARTED",
            "started_at": utc_now(),
        }

        if not model_present(tags, model):
            meta.update(status="SKIPPED_MODEL_NOT_INSTALLED", installed_models=inventory, ended_at=utc_now())
            write_json(metadata_path, meta)
            print("SKIP: model not installed")
            overall = max(overall, 1)
            continue

        try:
            show = ollama.show(model)
        except Exception as exc:
            meta.update(status="FAILED_MODEL_SHOW", error=f"{type(exc).__name__}: {exc}", ended_at=utc_now())
            write_json(metadata_path, meta)
            print(f"FAIL: could not inspect model: {exc}")
            overall = max(overall, 1)
            continue

        ctx = context_length(show)
        requested_ctx = min(ctx or args.context_cap, args.context_cap)
        available_for_output = requested_ctx - input_estimate - 1024
        num_predict = min(args.max_output_tokens, available_for_output)
        meta.update(
            runtime_attested_model=model,
            runtime_attested_digest=model_digest(tags, model),
            model_family=show.get("details", {}).get("family"),
            parameter_size=show.get("details", {}).get("parameter_size"),
            quantization_level=show.get("details", {}).get("quantization_level"),
            reported_context_length=ctx,
            requested_num_ctx=requested_ctx,
            planned_num_predict=num_predict,
        )

        if num_predict < args.min_output_tokens:
            meta.update(
                status="SKIPPED_INSUFFICIENT_CONTEXT",
                reason=(f"Estimated input {input_estimate} + reserve 1024 leaves {available_for_output} output tokens "
                        f"in requested context {requested_ctx}; v2 minimum is {args.min_output_tokens}."),
                ended_at=utc_now(),
            )
            write_json(metadata_path, meta)
            print("SKIP: insufficient context for a fair full Pass A response")
            overall = max(overall, 1)
            continue

        began = time.monotonic()
        try:
            result = ollama.chat(model, combined, num_ctx=requested_ctx, num_predict=num_predict, seed=args.seed)
            elapsed = time.monotonic() - began
            message = result.get("message") or {}
            content = message.get("content")
            thinking = message.get("thinking")
            meta.update(
                response_top_level_keys=sorted(result.keys()),
                response_message_keys=sorted(message.keys()),
                hidden_thinking_field_present=isinstance(thinking, str) and bool(thinking),
                hidden_thinking_char_count=len(thinking) if isinstance(thinking, str) else 0,
                done=result.get("done"),
                done_reason=result.get("done_reason"),
                prompt_eval_count=result.get("prompt_eval_count"),
                eval_count=result.get("eval_count"),
                total_duration_ns=result.get("total_duration"),
                load_duration_ns=result.get("load_duration"),
                prompt_eval_duration_ns=result.get("prompt_eval_duration"),
                eval_duration_ns=result.get("eval_duration"),
                elapsed_seconds=round(elapsed, 3),
            )
            if not isinstance(content, str) or not content.strip():
                meta.update(status="FAILED_EMPTY_VISIBLE_RESPONSE", ended_at=utc_now())
                write_json(metadata_path, meta)
                print("FAIL: Ollama returned no visible text response")
                print(f"message_keys={meta['response_message_keys']} done_reason={meta['done_reason']} eval_count={meta['eval_count']}")
                overall = max(overall, 1)
                continue

            raw_bytes = content.encode("utf-8")
            raw_path.write_bytes(raw_bytes)
            found, missing = compliance(content)
            status = "RAW_FROZEN_LOCAL" if not missing else "RAW_FROZEN_LOCAL_PARTIAL"
            meta.update(
                status=status,
                ended_at=utc_now(),
                response_sha256=sha256_bytes(raw_bytes),
                response_bytes=len(raw_bytes),
                response_lines=content.count("\n") + 1,
                raw_response_path=os.path.relpath(raw_path, root),
                required_markers_found=found,
                required_markers_missing=missing,
            )
            write_json(metadata_path, meta)
            print(f"{status}: {raw_path}")
            print(f"SHA-256: {meta['response_sha256']}")
            print(f"{meta['response_bytes']} bytes • {meta['response_lines']} lines • {elapsed:.1f}s")
            print(f"done_reason={meta['done_reason']} eval_count={meta['eval_count']}")
            if missing:
                print("MISSING REQUIRED SECTIONS:")
                for marker in missing:
                    print(f"  - {marker}")
                overall = max(overall, 1)
        except Exception as exc:
            elapsed = time.monotonic() - began
            meta.update(status="FAILED_INFERENCE", ended_at=utc_now(), elapsed_seconds=round(elapsed, 3), error=f"{type(exc).__name__}: {exc}")
            write_json(metadata_path, meta)
            print(f"FAIL: {type(exc).__name__}: {exc}")
            overall = max(overall, 1)

    return overall


if __name__ == "__main__":
    raise SystemExit(main())
