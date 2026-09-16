# Developer Environment

HumanOS is designed so the repository and CLI remain the source of truth for development behavior. Editors and AI assistants are interfaces over that environment, not runtime dependencies or authority sources.

## Canonical IDE: VS Code

VS Code is the canonical HumanOS development IDE.

It is the reference environment for:

- Python editing and interpreter selection;
- debugging;
- test discovery and execution;
- integrated terminal work;
- Git and GitHub review workflows;
- future documented workspace settings and onboarding.

Choosing one canonical IDE gives HumanOS a stable reference for setup instructions, debugging procedures, screenshots, contributor guidance, and future bootstrap verification.

### Canonical does not mean required

HumanOS must continue to build, test, inspect, and recover from the command line. A contributor must not need VS Code in order to run the runtime or test suite.

The intended relationship is:

```text
Git repository + CLI + tests = canonical development behavior
VS Code                     = canonical development interface
```

## Supported secondary editor: Zed

Zed is a supported secondary editor.

Good uses include:

- fast repository browsing;
- focused edits;
- reading documentation and diffs;
- scratch work;
- experiments with editor integrations and local-model assistance.

Zed-specific configuration must not become required for HumanOS to function. If behavior differs between editors, the CLI and repository tests are authoritative.

## Python development standard

The initial development standard uses:

- official CPython;
- Python 3.13 as the canonical local development target;
- Python's built-in `venv` for local isolation;
- `python -m pip` when package installation is required.

HumanOS must not replace or modify Apple's system Python as part of normal development setup.

The project may evaluate tools such as `uv`, `pyenv`, Homebrew, Poetry, or Conda later, but none is currently a canonical HumanOS dependency. Any adoption should be a deliberate supply-chain and reproducibility decision rather than an incidental workaround.

## Source control and review

HumanOS development uses Git and GitHub with the repository SDLC:

1. define the problem and acceptance criteria;
2. create a focused branch;
3. implement the smallest bounded change;
4. run relevant tests and local checks;
5. review the diff and evidence;
6. use a pull request for review;
7. resolve findings and rerun affected checks;
8. merge or release only with owner authorization.

## Local AI development

Local execution is the default development direction.

Runtime 0.1 currently uses Ollama behind the model boundary. Ollama is treated as a current adapter/runtime, not as the identity of HumanOS and not as a permanent dependency.

Future local runtimes may include other adapters such as llama.cpp or MLX, provided they satisfy HumanOS governance, qualification, provenance, and recovery requirements.

No Ollama cloud account or other cloud-model account is required by this developer-environment standard.

## Cloud providers

Cloud-model development and provider credentials are outside Developer Environment v0.1. They require separate privacy, data-residency, provider, credential, logging, and authorization decisions.

A cloud provider must never become implicitly trusted because an editor, plugin, or desktop application makes it convenient to connect.

## Planned workstation layout

The target developer experience is intentionally simple:

```text
HumanOS Developer Workstation
├── VS Code                 canonical IDE
├── Zed                     supported secondary editor
├── zsh                     terminal shell
├── Git + GitHub            source control / review
├── official CPython 3.13   canonical local Python target
├── venv                    Python isolation
├── HumanOS test suite      behavioral evidence
└── local model runtime     replaceable adapter boundary
```

## Planned follow-up work

The following are planned, not yet claimed as implemented by this document:

- a minimal VS Code HumanOS profile;
- a documented minimum extension set;
- a bootstrap helper for a new development machine;
- a deterministic developer-environment verification command;
- dependency/version locking decisions;
- local-model inventory and qualification tooling;
- provider-neutral local-model adapters beyond the current Ollama boundary.

Each executable addition must follow the HumanOS SDLC and be tested before documentation describes it as working.
