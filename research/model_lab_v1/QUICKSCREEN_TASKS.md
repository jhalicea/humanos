# HumanOS Model Lab v1 — Phase 1 Quick Screen

**Status:** FROZEN TASK PACK v1.0

Run each task exactly as written in a fresh session. Do not append model-specific hints.

---

## TASK 1 — Worker Precision

You are given the following messy project update. Turn it into a compact operational status report.

SOURCE:
- We tried a local Qwen constitutional test. At first the model returned no visible response.
- A tiny neutral smoke test returned OK when context was 4096.
- The full test had requested a much larger context allocation.
- We reran the exact frozen task with context capped at 16384, temperature 0, same seed, and the same model tag.
- The rerun produced 25,923 bytes, 425 lines, 4,958 evaluated output tokens, stopped normally, and took 863.5 seconds.
- A literal-heading checker incorrectly called the answer partial because the model used headings such as Finding 1 instead of TRIAL 1.
- A structure-only review confirmed all 12 required trials, all required main sections, and all 11 final-verdict labels.
- We can prove the configuration change changed the observed outcome. We cannot yet prove the exact low-level cause.

OUTPUT REQUIREMENTS:
- Maximum 180 words.
- Include exactly these headings: STATUS, VERIFIED, NOT PROVEN, NEXT ACTION.
- Do not add facts not present in SOURCE.
- Distinguish observation from inference.

---

## TASK 2 — Engineering Judgment

A local-first personal AI system has these properties:
- SQLite stores canonical state locally.
- Models are replaceable and cannot authorize their own permissions.
- A capability broker controls filesystem, browser, network, and external-app access.
- The system currently has a Python runtime and a growing test suite.
- The owner wants better reliability but does not want microservices or infrastructure for its own sake.
- One engineer proposes rewriting the authoritative kernel in Rust immediately.
- Another proposes staying entirely in Python forever.

Your job is to recommend a decision for the next 90 days.

OUTPUT REQUIREMENTS:
- Maximum 450 words.
- Choose one: REWRITE NOW, STAY PYTHON, or HYBRID INCREMENTAL.
- Give the 3 strongest reasons for your choice.
- Name the single strongest argument against your choice.
- Define one measurable trigger that would justify revisiting the decision.
- Do not hedge with “it depends” as the final answer.

---

## TASK 3 — Working-With-Jon Fit

You are helping a technically experienced builder who learns best by building real systems, dislikes unnecessary theory, wants evidence before claims, and gets frustrated when documentation is described as implementation. He wants to learn AI automation while improving his own software at the same time.

He says:

“I want to learn webhooks, polling, n8n, Make, APIs, queues, retries, auth, and agent workflows, but I do not want another generic course. I also have a messy email inbox and HumanOS already has an Inbox concept. What should I do first?”

OUTPUT REQUIREMENTS:
- Maximum 500 words.
- Give a concrete first 7-day build plan.
- The plan must produce one working HumanOS capability by Day 7.
- Include one oral-interview question, one debugging/failure exercise, and one measurable acceptance test.
- Tell him what NOT to learn yet.
- Be decisive, practical, and avoid motivational filler.

---

## End of frozen Phase 1 task pack

Do not modify these prompts after the first model is run. If a defect is discovered, create v1.1 and preserve v1.0.