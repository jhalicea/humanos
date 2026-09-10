#!/usr/bin/env python3
"""CLI for running the HumanOS Intelligence Naturalization Exam against local Ollama."""
import argparse
import json
import os
from pathlib import Path

from naturalization import run_all_hine, run_hine

BASE = Path(__file__).resolve().parent


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="HumanOS Intelligence Naturalization Exam (HINE)")
    parser.add_argument("--config", default=str(BASE / "config.json"))
    parser.add_argument("--model", help="Override configured model")
    parser.add_argument("--endpoint", help="Override configured local Ollama endpoint")
    parser.add_argument("--output", help="Evidence directory")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--all", action="store_true", help="Discover every locally installed Ollama model, test each, and create a comparison report")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    model = args.model or os.environ.get("HUMANOS_MODEL") or config.get("model", "llama3:latest")
    endpoint = args.endpoint or os.environ.get("HUMANOS_ENDPOINT") or config.get("endpoint", "http://127.0.0.1:11434")
    vault = Path(config.get("vault", "HumanOS_Vault"))
    if not vault.is_absolute():
        vault = (config_path.parent / vault).resolve()
    output = Path(args.output).expanduser().resolve() if args.output else vault / "model_registry" / "exams"

    try:
        if args.all:
            batch, json_path, md_path = run_all_hine(endpoint, output, timeout=args.timeout)
            summary = batch["summary"]
            print("Batch: " + batch["batch_id"])
            print("Discovered: {discovered}  Completed: {completed}  Errors: {errors}".format(**summary))
            print("Quarantined: {quarantined}  Human review required: {human_review_required}".format(**summary))
            print("Naturalized: 0 (promotion always requires explicit human review)")
            print("Evidence: " + str(json_path))
            print("Comparison: " + str(md_path))
            return 2 if summary["quarantined"] or summary["errors"] else 0

        record, path = run_hine(model, endpoint, output, timeout=args.timeout)
    except Exception as error:
        print("HINE RECOVERY REQUIRED: " + type(error).__name__ + ": " + str(error))
        return 1

    summary = record["summary"]
    print("Exam: " + record["exam_id"])
    print("Candidate: " + model)
    print("PASS: {pass}  REVIEW: {review}  FAIL: {fail}".format(**summary))
    print("Critical failure: " + str(summary["critical_failed"]))
    print("Recommendation: " + summary["recommendation"])
    print("Naturalized: False (promotion requires explicit review)")
    print("Evidence: " + str(path))
    return 2 if summary["critical_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
