#!/usr/bin/env python3
"""Run EXP-R3-A-001 against local Ollama models with evidence capture.

Research harness only. It does not modify HumanOS authority, canonical state, or
the Constitution. Each model receives only the frozen Pass A instructions and
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
        no_proxy = urllib.request.ProxyHandler({})
        self.opener = urllib.request.build_opener(no_proxy)

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
    candidates = []
    for key, value in info.items():
        if key.endswith(".context_length") or key == "context_length":
            try:
                candidates.append(int(value))
            except (TypeError, ValueError):
                pass
    return max(candidates) if candidates else None


def model_digest(tags: dict, model: str) -> str | None:
    for item in tags.get("models", []):
        if item.get("name") == model or item.get("model") == model:
            return item.get("digest")
    return None


def model_present(tags: dict, model: str) -> bool:
    return any(
        item.get("name") == model or item.get("model") == model
        for item in tags.get("models", [])
    )


def build_input(prompt_text: str, constitution_text: str) -> str:
    return (
        prompt_text.rstrip()
        + "\n\n--- BEGIN RATIFIED CONSTITUTION V0.2 ---\n\n"
        + constitution_text.rstrip()
        + "\n\n--- END RATIFIED CONSTITUTION V0.2 ---\n"
    )


def estimate_tokens(text: str) -> int:
    # Conservative planning estimate only; recorded as an estimate, never as tokenizer truth.
    return max(1, (len(text) + 3) // 4)


def write_json(path: Path, value: dict):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="HumanOS FRIENDS Round 3 local Pass A harness")
    parser.add_argument("--model", action="append", required=True, help="Exact installed Ollama model name; repeat for multiple models")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--constitution", default=DEFAULT_CONSTITUTION)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--seed", type=int, default=424242)
    parser.add_argument("--max-output-tokens", type=int, default=8000)
    parser.add_argument("--min-output-tokens", type=int, default=3000)
    parser.add_argument("--context-cap", type=int, default=131072, help="Do not request a larger Ollama context than this")
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
    prompt_text = prompt_raw.decode("utf-8")
    constitution_text = constitution_raw.decode("utf-8")
    combined = build_input(prompt_text, constitution_text)
    combined_hash = sha256_text(combined)
    input_estimate = estimate_tokens(combined)

    out_dir.mkdir(parents=True, exist_ok=True)
    ollama = Ollama(args.endpoint, args.timeout)

    try:
        tags = ollama.tags()
    except Exception as exc:
        print(f"ERROR: cannot reach local Ollama at {args.endpoint}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3

    inventory = sorted(
        item.get("name") or item.get("model") or "UNKNOWN"
        for item in tags.get("models", [])
    )
    print("Local Ollama inventory:")
    for name in inventory:
        print(f"  - {name}")

    overall = 0
    for model in args.model:
        print(f"\n=== {model} ===")
        slug = slug_model(model)
        run_stamp = dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        run_id = f"R3-A-LOCAL-{slug}-{run_stamp}"
        raw_path = out_dir / f"{run_id}_RAW.md"
        metadata_path = out_dir / f"{run_id}_METADATA.json"

        base_meta = {
            "experiment": "EXP-R3-A-001",
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
            "status": "STARTED",
            "started_at": utc_now(),
        }

        if not model_present(tags, model):
            base_meta.update(
                status="SKIPPED_MODEL_NOT_INSTALLED",
                installed_models=inventory,
                ended_at=utc_now(),
            )
            write_json(metadata_path, base_meta)
            print("SKIP: model not installed")
            overall = max(overall, 1)
            continue

        try:
            show = ollama.show(model)
        except Exception as exc:
            base_meta.update(
                status="FAILED_MODEL_SHOW",
                error=f"{type(exc).__name__}: {exc}",
                ended_at=utc_now(),
            )
            write_json(metadata_path, base_meta)
            print(f"FAIL: could not inspect model: {exc}")
            overall = max(overall, 1)
            continue

        ctx = context_length(show)
        digest = model_digest(tags, model)
        requested_ctx = min(ctx or args.context_cap, args.context_cap)
        available_for_output = requested_ctx - input_estimate - 1024
        num_predict = min(args.max_output_tokens, available_for_output)

        base_meta.update(
            runtime_attested_model=model,
            runtime_attested_digest=digest,
            model_family=show.get("details", {}).get("family"),
            parameter_size=show.get("details", {}).get("parameter_size"),
            quantization_level=show.get("details", {}).get("quantization_level"),
            reported_context_length=ctx,
            requested_num_ctx=requested_ctx,
            planned_num_predict=num_predict,
        )

        if num_predict < args.min_output_tokens:
            base_meta.update(
                status="SKIPPED_INSUFFICIENT_CONTEXT",
                reason=(
                    f"Estimated input {input_estimate} tokens + 1024 safety reserve leaves "
                    f"{available_for_output} output tokens in requested context {requested_ctx}; "
                    f"minimum is {args.min_output_tokens}."
                ),
                ended_at=utc_now(),
            )
            write_json(metadata_path, base_meta)
            print("SKIP: insufficient context for a fair full Pass A response")
            overall = max(overall, 1)
            continue

        began = time.monotonic()
        try:
            result = ollama.chat(
                model,
                combined,
                num_ctx=requested_ctx,
                num_predict=num_predict,
                seed=args.seed,
            )
            elapsed = time.monotonic() - began
            message = result.get("message") or {}
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise RuntimeError("Ollama returned an empty/non-text response")
            raw_bytes = content.encode("utf-8")
            raw_path.write_bytes(raw_bytes)
            base_meta.update(
                status="RAW_FROZEN_LOCAL",
                ended_at=utc_now(),
                elapsed_seconds=round(elapsed, 3),
                response_sha256=sha256_bytes(raw_bytes),
                response_bytes=len(raw_bytes),
                response_lines=content.count("\n") + 1,
                done=result.get("done"),
                done_reason=result.get("done_reason"),
                prompt_eval_count=result.get("prompt_eval_count"),
                eval_count=result.get("eval_count"),
                total_duration_ns=result.get("total_duration"),
                load_duration_ns=result.get("load_duration"),
                prompt_eval_duration_ns=result.get("prompt_eval_duration"),
                eval_duration_ns=result.get("eval_duration"),
                raw_response_path=os.path.relpath(raw_path, root),
            )
            write_json(metadata_path, base_meta)
            print(f"RAW FROZEN: {raw_path}")
            print(f"SHA-256: {base_meta['response_sha256']}")
            print(f"{base_meta['response_bytes']} bytes • {base_meta['response_lines']} lines • {elapsed:.1f}s")
            print(f"done_reason={base_meta['done_reason']} eval_count={base_meta['eval_count']}")
        except Exception as exc:
            elapsed = time.monotonic() - began
            base_meta.update(
                status="FAILED_INFERENCE",
                ended_at=utc_now(),
                elapsed_seconds=round(elapsed, 3),
                error=f"{type(exc).__name__}: {exc}",
            )
            write_json(metadata_path, base_meta)
            print(f"FAIL: {type(exc).__name__}: {exc}")
            overall = max(overall, 1)

    return overall


if __name__ == "__main__":
    raise SystemExit(main())
