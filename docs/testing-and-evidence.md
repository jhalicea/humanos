# Testing and Evidence

HumanOS uses tests and runtime readback to determine what works. Documentation and model agreement are not substitutes for execution evidence.

## Verification priorities

- Normal behavior
- Permission denial and malformed input
- Restart and recovery
- Duplicate or repeated requests
- Interrupted output delivery
- File-boundary enforcement
- Integrity and projection consistency
- Regression behavior across existing capabilities

## Evidence hierarchy

1. Reproducible runtime behavior
2. Passing tests tied to an acceptance criterion
3. Reviewed repository diff and commit history
4. Structured logs and preserved artifacts
5. Documentation
6. Model or human proposal

Test counts change as the repository evolves. Refer to the current branch and CI results rather than copying an old number into long-lived documentation.
