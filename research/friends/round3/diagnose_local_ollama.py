#!/usr/bin/env python3
"""Non-HumanOS smoke diagnostics for local Ollama model compatibility.

This script does NOT run EXP-R3-A-001. It sends only a tiny neutral prompt so we can
separate model/runtime/template failures from failures caused by the long Pass A
packet. Hidden thinking text is never printed or stored.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "http://127.0.0.1:11434"
DEFAULT_OUT_DIR = "research/friends/round3/local_runs"
SMOKE_PROMPT = "Return exactly the word OK and nothing else."


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "model"


def validate_endpoint(endpoint: str) -> str:
    p = urllib.parse.urlparse(endpoint)
    if p.scheme != "http" or p.hostname not in {"127.0.0.1", "localhost", "::1"} or p.username or p.password:
        raise ValueError("Only a local loopback Ollama endpoint is allowed")
    return endpoint.rstrip("/")


class Ollama:
    def __init__(self, endpoint: str, timeout: int):
        self.endpoint = validate_endpoint(endpoint)
        self.timeout = timeout
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def json(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.endpoint + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=self.timeout) as response:
            return json.loads(response.read())

    def tags(self):
        return self.json("GET", "/api/tags")

    def show(self, model: str):
        return self.json("POST", "/api/show", {"model": model})

    def chat(self, model: str):
        return self.json("POST", "/api/chat", {
            "model": model,
            "messages": [{"role": "user", "content": SMOKE_PROMPT}],
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "seed": 424242, "num_predict": 32, "num_ctx": 4096},
        })

    def generate(self, model: str):
        return self.json("POST", "/api/generate", {
            "model": model,
            "prompt": SMOKE_PROMPT,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "seed": 424242, "num_predict": 32, "num_ctx": 4096},
        })


def context_length(show: dict):
    values = []
    for key, value in (show.get("model_info") or {}).items():
        if key.endswith(".context_length") or key == "context_length":
            try:
                values.append(int(value))
            except (TypeError, ValueError):
                pass
    return max(values) if values else None


def hidden_thinking_summary(message: dict):
    thinking = message.get("thinking")
    return {
        "thinking_field_present": isinstance(thinking, str) and bool(thinking),
        "thinking_char_count": len(thinking) if isinstance(thinking, str) else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Smoke-test local Ollama model response compatibility")
    ap.add_argument("--model", action="append", required=True)
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    root = Path.cwd().resolve()
    out_dir = (root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ollama = Ollama(args.endpoint, args.timeout)
    tags = ollama.tags()
    installed = {item.get("name") or item.get("model") for item in tags.get("models", [])}

    for model in args.model:
        print(f"\n=== DIAGNOSTIC {model} ===")
        stamp = dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        path = out_dir / f"DIAG-{slug(model)}-{stamp}.json"
        record = {
            "diagnostic_only": True,
            "experiment": "NOT_EXP-R3-A-001",
            "model": model,
            "endpoint": args.endpoint,
            "prompt": SMOKE_PROMPT,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        if model not in installed:
            record["status"] = "MODEL_NOT_INSTALLED"
            path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
            print("NOT INSTALLED")
            continue

        try:
            show = ollama.show(model)
            record["model_family"] = (show.get("details") or {}).get("family")
            record["parameter_size"] = (show.get("details") or {}).get("parameter_size")
            record["quantization_level"] = (show.get("details") or {}).get("quantization_level")
            record["reported_context_length"] = context_length(show)
            print("family=", record["model_family"], "parameters=", record["parameter_size"],
                  "quant=", record["quantization_level"], "context=", record["reported_context_length"])
        except Exception as exc:
            record["show_error"] = f"{type(exc).__name__}: {exc}"
            print("SHOW ERROR:", record["show_error"])

        try:
            chat = ollama.chat(model)
            msg = chat.get("message") or {}
            content = msg.get("content")
            record["chat"] = {
                "top_level_keys": sorted(chat.keys()),
                "message_keys": sorted(msg.keys()),
                "visible_content": content if isinstance(content, str) else None,
                "done": chat.get("done"),
                "done_reason": chat.get("done_reason"),
                "eval_count": chat.get("eval_count"),
                **hidden_thinking_summary(msg),
            }
            print("CHAT visible=", repr(record["chat"]["visible_content"]),
                  "done_reason=", record["chat"]["done_reason"], "eval_count=", record["chat"]["eval_count"])
        except Exception as exc:
            record["chat_error"] = f"{type(exc).__name__}: {exc}"
            print("CHAT ERROR:", record["chat_error"])

        try:
            gen = ollama.generate(model)
            response = gen.get("response")
            record["generate"] = {
                "top_level_keys": sorted(gen.keys()),
                "visible_response": response if isinstance(response, str) else None,
                "done": gen.get("done"),
                "done_reason": gen.get("done_reason"),
                "eval_count": gen.get("eval_count"),
                "thinking_field_present": isinstance(gen.get("thinking"), str) and bool(gen.get("thinking")),
                "thinking_char_count": len(gen.get("thinking")) if isinstance(gen.get("thinking"), str) else 0,
            }
            print("GENERATE visible=", repr(record["generate"]["visible_response"]),
                  "done_reason=", record["generate"]["done_reason"], "eval_count=", record["generate"]["eval_count"])
        except Exception as exc:
            record["generate_error"] = f"{type(exc).__name__}: {exc}"
            print("GENERATE ERROR:", record["generate_error"])

        record["status"] = "COMPLETE_DIAGNOSTIC"
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("saved:", path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
