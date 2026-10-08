#!/usr/bin/env python3
"""Opt-in, text-only OpenAI API runner behind HumanOS's durable BudgetGovernor.

CLI NEVER makes an API call unless --authorize-api-charges is supplied.
Separate OpenAI API billing applies; not a control over Codex Desktop.
"""
import argparse
import os
from pathlib import Path
import sys

from bounded_responses import ReplanRequired, ResponsesTransport, execute
from budget_governor import BudgetLimits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Exact OpenAI Responses API model ID")
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--instructions-file", type=Path)
    parser.add_argument("--ledger", required=True, type=Path,
                        help="Absolute private ~/.humanos/private/.../*.json")
    parser.add_argument("--budget-total", required=True, type=int,
                        help="Total conservative token reservations for this task")
    parser.add_argument("--output-cap", required=True, type=int,
                        help="Provider-enforced max output including reasoning tokens")
    parser.add_argument("--context-cap", type=int, default=8000)
    parser.add_argument("--calls-cap", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true",
                        help="Offline validation; no network access or ledger writes")
    parser.add_argument("--authorize-api-charges", action="store_true",
                        help="Required explicit authorization before any API call")
    args = parser.parse_args()
    try:
        limits = BudgetLimits(max_calls=args.calls_cap,
                              max_total_tokens=args.budget_total,
                              max_context_tokens=args.context_cap,
                              max_output_tokens=args.output_cap)
        if args.output_cap < 16:
            raise ValueError("Responses API output cap minimum is 16")
        if not args.ledger.is_absolute():
            raise ValueError("ledger must be an absolute private path")
        if not args.prompt_file.is_file():
            raise ValueError("prompt file does not exist")
        prompt = args.prompt_file.read_text(encoding="utf-8")
        instructions = (args.instructions_file.read_text(encoding="utf-8")
                        if args.instructions_file else "")
        # Offline preflight performs all local input checks without opening a
        # network connection or mutating the ledger.
        from bounded_responses import _validate_inputs, _validate_private_path
        _validate_inputs(args.model, prompt, instructions, args.output_cap, limits)
        _validate_private_path(args.ledger)
        if args.dry_run:
            print("DRY_RUN_ONLY: no API calls and no ledger writes.")
            print("Model:", args.model, "effort: low")
            print("Max reservations:", args.budget_total, "tokens;",
                  "single-call output ceiling:", args.output_cap)
            print("Input will be counted by the provider before dispatch.")
            print("Ledger:", args.ledger)
            return 0
        if not args.authorize_api_charges:
            raise ReplanRequired("API_CHARGES_NOT_AUTHORIZED; use --dry-run first")
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ReplanRequired("OPENAI_API_KEY_NOT_SET; no paid request sent")
        answer = execute(ledger_path=args.ledger, model=args.model,
                         prompt=prompt, instructions=instructions,
                         output_cap=args.output_cap, limits=limits,
                         transport=ResponsesTransport(key))
        print("STATUS:", answer["status"], "; reserved task tokens:",
              answer["reserved_total_tokens"], "of", args.budget_total)
        print("USAGE:", answer["usage"]["input_tokens"], "input,",
              answer["usage"]["output_tokens"], "output")
        if answer["status"] != "completed":
            print("WARNING: incomplete result; do not auto-retry.",
                  file=sys.stderr)
        print(answer["text"])
        return 0
    except (ValueError, OSError, PermissionError, ReplanRequired) as exc:
        print("STOP -> REPLAN_REQUIRED:", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
