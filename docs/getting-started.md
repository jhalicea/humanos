# Getting Started

## Current scope

HumanOS Runtime 0.1 is an early local runtime built around Python, SQLite, a terminal-facing Mirror interface, and local Ollama inference. It is not a general operating-system sandbox or a fully autonomous agent platform.

## Requirements

- Python 3.9 or newer
- A local Ollama installation and available model
- A dedicated HumanOS workspace containing only files the operator authorizes the runtime to access

## Run

From the repository root:

```bash
python3 server.py
```

Run the test suite:

```bash
python3 -m unittest discover -s tests -v
```

## Safe first session

1. Start HumanOS without connecting private directories.
2. Inspect the displayed session identifier and capability list.
3. Use a small synthetic text file for the first read operation.
4. Confirm that write operations require explicit authorization.
5. Stop the process with Ctrl-C and verify that the session can be inspected after restart.

See the root README for current commands and recovery behavior tied to this release branch.
