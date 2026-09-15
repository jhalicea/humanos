# MLAB-P1-T1-LUNA — Raw Response

**Model:** GPT-5.6 Luna
**Surface:** Work
**Effort:** Light
**Speed mode:** normal/default as shown before run
**Status:** RAW FROZEN

---

STATUS

The local Qwen constitutional test now completes successfully under the capped configuration. The earlier no-response result did not recur.

VERIFIED

- Neutral smoke test returned OK at context 4096.
- Exact frozen task rerun with context capped at 16384, temperature 0, same seed, and same model tag.
- Output: 25,923 bytes, 425 lines, 4,958 evaluated output tokens.
- Stopped normally after 863.5 seconds.
- Structure review confirmed all 12 required trials, required main sections, and all 11 final-verdict labels.
- The configuration change altered the observed outcome.

NOT PROVEN

The exact low-level cause of the initial no-response result is not established. The literal-heading checker’s “partial” result was incorrect because equivalent headings such as “Finding 1” were used instead of “TRIAL 1.”

NEXT ACTION

Use the structure-only review as the validity check and investigate the low-level cause separately.
