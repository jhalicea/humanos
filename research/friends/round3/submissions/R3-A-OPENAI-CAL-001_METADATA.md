# R3-A-OPENAI-CAL-001 — Run Metadata

**Experiment:** EXP-R3-A-001 — Blind Constitutional Convention
**Pass:** A
**Participant:** OpenAI / GPT-5.6 Sol (self-report)
**Provider:** OpenAI (self-report)
**Runtime-attested identity:** UNKNOWN
**Status:** RAW ATTACHMENT SHA-256 FROZEN / CALIBRATION ONLY
**Date received:** 2026-09-14

## Contamination disclosure

The submitted response explicitly reports that prior HumanOS-related material existed in the ambient conversation context and assigns itself `MEDIUM` contamination risk. It states that it did not seek, retrieve, consult, or rely on that prior material for the review and that it did not view another FRIEND answer.

After the raw response was frozen, the human operator clarified that this run was started in an **Incognito chat**. That UI provenance is recorded, but it does not override the model's own contemporaneous disclosure that prior HumanOS material existed in ambient context. For experiment integrity, the stricter evidence wins: the run remains calibration-only unless a future clean run can demonstrate stronger isolation.

Because Pass A requires clean-room isolation from prior HumanOS material, this run is **not eligible for official blind-panel scoring**. It remains useful as calibration data.

## Input discipline

- Claimed input for the review: `EXP-R3-A-001` and Constitution v0.2 contained in the Pass A packet.
- Expected canonical Pass A SHA-256: `e7bf2101238295da572c17ddcd0b7aeaa83a36270f280782882bc0830e49f96e`
- Human operator provenance after freeze: Incognito chat.
- Participant self-reports: web access NO; repository inspected NO; code executed NO; other HumanOS material present in ambient context YES; no other FRIEND answer viewed.
- Exact runtime-side verification that the participant received the canonical bytes: NOT AVAILABLE.

## Raw response preservation

Original orchestration-chat attachment:

`Pasted markdown(20260914-173501).md`

Observed original attachment size: `87874` bytes

Observed line count: `1595`

Original attachment SHA-256:

`2a4149837a68bf2c5ff5e7fa99277026e62f4939642b71e44c52feb1e0326f1e`

The original attachment and hash are the evidence anchor. The repository companion file `R3-A-OPENAI-CAL-001_RAW.md` records the self-report header and evidence anchor, but is not claimed to be a byte-for-byte copy of the full original attachment.

## Eligibility

**Blind-scoring eligibility:** NO — CALIBRATION ONLY

Reason: despite the operator's Incognito-chat provenance, the participant self-reports prior HumanOS material in ambient context, so perfect clean-room isolation cannot be established under the registered Pass A protocol.

## Analysis hold

Do not use this calibration run to influence remaining official blind participants. It may be compared only after the chosen blind cohort is frozen.
