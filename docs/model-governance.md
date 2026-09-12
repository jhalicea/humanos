# Model Governance

HumanOS treats every language-model output as a proposal until it is checked against evidence, permissions, and acceptance criteria.

## Principles

- Models are replaceable cognitive runtimes, not HumanOS itself.
- Context is selected deliberately; unrelated private records are not dumped into prompts.
- Provider and model identity should be recorded when exposed.
- Claims about work are verified through files, tests, commits, and runtime behavior.
- Consequential external actions remain under human authority.
- Failures, disagreements, and corrections are useful evaluation data.

## Current implementation boundary

Runtime 0.1 implements local Ollama inference behind a model protocol. Provider portability is an architectural boundary, not a claim that hosted providers are already integrated.

Future evaluation work includes repeatable task suites, capability grading, failure taxonomies, and comparable usage records where providers expose sufficient data.
