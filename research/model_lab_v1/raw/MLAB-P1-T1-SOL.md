# MLAB-P1-T1-SOL — Raw Response

## STATUS

The frozen constitutional test completed on rerun with context capped at 16384. Structure review confirmed all required content.

## VERIFIED

- The initial local Qwen test returned no visible response.
- A tiny neutral smoke test returned OK at context 4096; the full test requested a much larger context allocation.
- The exact frozen task was rerun at context 16384, temperature 0, with the same seed and model tag.
- The rerun produced 25,923 bytes, 425 lines, and 4,958 evaluated output tokens. It stopped normally after 863.5 seconds.
- A literal-heading checker incorrectly classified the answer as partial because headings included “Finding 1” instead of “TRIAL 1.”
- Structure-only review confirmed all 12 trials, all required main sections, and all 11 final-verdict labels.
- The configuration change changed the observed outcome.

## NOT PROVEN

The exact low-level cause remains unproven. The observed outcome change does not establish that mechanism.

## NEXT ACTION

Investigate the exact low-level cause of the changed outcome.
