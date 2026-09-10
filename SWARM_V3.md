# HumanOS Swarm Runtime v3

Status: candidate implementation. CI verifies routing and governance invariants; actual local Ollama execution remains a host verification step.

## Local-first assignment

For the models previously observed on Jon's Mac:

- coordinator: `llama3:latest`
- worker: `llama3.2:latest`
- verifier: `llama3:latest`

The existing broker manifest remains strict and unchanged: `agent_id`, `model`, `version`, `task`, `capabilities`, `peers`, and `token`. This is intentional. v3 supports different local model names per agent while all agents use the trusted loopback Ollama endpoint. Provider or endpoint fields are not accepted in broker manifests because model-routing metadata must never silently mutate the authorization schema.

`ModelRouter` keeps a narrow adapter seam for future provider-neutral work, but any external/commercial provider configuration requires a separately reviewed schema and must not be smuggled into the broker manifest.

## Verification order

1. Pull the candidate branch on the HumanOS host.
2. Run `python3 verify_swarm_local.py`. This only checks the local Ollama model inventory.
3. Run `python3 -m unittest discover -s tests -v`.
4. Create a fresh signed/attested authorization envelope for an owned lab target. Never reuse fixture authorization or tokens.
5. Run `python3 swarm_runtime.py --config <owner-controlled-config>`.
6. Verify the external Action Ledger and confirm each effect is attributed to the correct agent/model and remained inside the envelope.

A CI pass does not prove step 5 occurred on the Mac. A local preflight pass does not prove a live swarm run succeeded. Record those separately.
