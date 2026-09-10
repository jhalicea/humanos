# HumanOS Swarm Runtime v3

Status: candidate implementation. CI verifies routing and governance invariants; actual local Ollama execution remains a host verification step.

## Local-first assignment

For the models previously observed on Jon's Mac:

- coordinator: `llama3:latest` (Llama 3 8B)
- worker: `llama3.2:latest` (Llama 3.2 3B)
- verifier: `llama3:latest`

Each agent may select its own model in its broker manifest using `provider: ollama`, `model`, and optionally a loopback `endpoint`. Remote Ollama endpoints are rejected. Other providers require an explicitly installed adapter factory; provider choice never grants authority.

## Verification order

1. Pull the candidate branch on the HumanOS host.
2. Run `python3 verify_swarm_local.py`. This only checks the local Ollama model inventory.
3. Run `python3 -m unittest discover -s tests -v`.
4. Create a fresh signed/attested authorization envelope for an owned lab target. Never reuse fixture authorization or tokens.
5. Run `python3 swarm_runtime.py --config <owner-controlled-config>`.
6. Verify the external Action Ledger and confirm each effect is attributed to the correct agent/model and remained inside the envelope.

A CI pass does not prove step 5 occurred on the Mac. A local preflight pass does not prove a live swarm run succeeded. Record those separately.
