# HumanOS repository working agreement

Owner instruction recorded 2026-09-07: follow the SDLC and always use the owner's
repository. The owner plans to give the code to Claude and Gemini for later review.

## Repository and preservation

- Develop the existing HumanOS runtime in https://github.com/jhalicea/humanos.
  Use branches/worktrees of this repository; do not create a competing runtime or
  repository. The installed checkout is /Users/jhalicea/humanos.
- This is the code repository, not the canonical personal record store. Preserve
  HumanOS ownership, Mirror's interface role, and the Life Notebook boundaries.
- Inspect git status, existing implementation, tests, and applicable governing
  records before changing behavior. Preserve uncommitted work and rollback points.
- Keep Notebook transcripts/databases, workspace contents, backups, credentials,
  and private test evidence out of Git, including history and PR attachments.

## SDLC for changes

1. State the concrete problem, bounded scope, and observable acceptance criteria.
2. Work on a focused branch. Extend existing components and preserve data formats
   unless a justified migration includes recovery and rollback.
3. Run relevant automated tests and real local checks for affected interactions.
   Use isolated test vaults. Never operate tests on the owner's active Notebook.
4. Review the diff for regressions, authority/scope changes, transcript fidelity,
   idempotency, recovery, and accidental private data before committing/pushing.
5. Push the branch and open a pull request with purpose, exact tested commit,
   commands/results, known limitations, and rollback instructions. Report local
   versus remote state truthfully; commits are not automatically uploads.
6. Resolve review findings, rerun affected checks, and record remaining defects.
   Merge/release within the owner's authorization. Preserve an identifiable
   previous release and verify installed behavior after a release.

Use `python3 -m unittest discover -s tests -v` for the existing automated suite.
Live Ollama checks are separate from tests using simulated model responses.
CI, branch protection, and automatic deployment are not established by this file.

## Independent review

Give reviewers the same immutable commit, requirements, diff, reproduction steps,
and test evidence. Ask for findings tied to files/lines and observable failures.
Track findings and dispositions in the repository. Model agreement is not a test
result; reproduce claims before accepting or dismissing them. The owner will
arrange the planned Claude/Gemini reviews; do not transmit code or personal
records to those services based only on this statement of future intent.
