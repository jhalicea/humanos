# MLAB-P2-B-TERRA — Phase 2 Trial B Score

**Model:** GPT-5.6 Terra  
**Trial:** PDF / Document Creation and Conversation Feel  
**Status:** STAGE 1 + STAGE 2 COMPLETE / STAGE 2 USAGE DELTA OBSERVED / COMPARATIVE EFFICIENCY SCORE PENDING  
**Stage 1 PDF SHA-256:** `78cf683be38d4e20e0da82c7b62cbf517330ac704f672324df1ac191a5246370`  
**Stage 2 PDF SHA-256:** `6c984ed6d8f8e5b29a003f852019bd14c472407887d78ec9603877cd04b89db3`

## Usage evidence

Before the Stage 2 steering run, the owner supplied a screenshot at approximately 11:18 AM showing:
- 5-hour allowance: **87% left**
- weekly allowance: **58% left**

After the Stage 2 steering run, the owner supplied a comparable screenshot at approximately 11:46 AM showing:
- 5-hour allowance: **83% left**
- weekly allowance: **57% left**

Observed meter delta over the interval:
- **5-hour allowance: 4 percentage points consumed**
- **weekly allowance: 1 percentage point consumed**

The Usage panel itself states that the displayed plan limits are shared across Codex, Work, Workspace Agents, and ChatGPT for Excel, and that ordinary Chat conversations are not included. The owner also reported no other relevant activity during the interval. Therefore this is reasonably strong evidence that the observed plan-meter movement is attributable primarily to the Terra Work revision, but it is still recorded as an **observed UI-meter delta**, not a precise token or compute measurement. The UI values are rounded and the 5-hour window is time-based, so do not convert these percentages into tokens.

The interval between screenshots is roughly 28 minutes, but this is **not** treated as Terra's wall-clock execution time because it includes user review and ordinary chat time.

Stage 1 usage was not baselined before its run, so full two-stage Trial B usage remains only partially measured.

## Stage 1

Provisional Stage 1 score: **74/85 known** (efficiency and steering not yet included at that point).

Strengths:
- polished six-page executive brief;
- strong hierarchy, restrained editorial styling, useful chart/table treatment;
- measured results generally separated from interpretation;
- GPT-5.5 correctly treated as transitional rather than a future dependency.

Defect:
- Phase 1 page states that the score range is four points even though the displayed source totals span 180 to 174, i.e. six points.

## Stage 2 revision

The steering instruction asked for a more alive, intentional, premium document without unsupported facts and explicitly asked the model to correct any factual or quantitative error it noticed.

Observed response:
- expanded from six to seven pages;
- materially improved cover thesis, pacing, visual rhythm, evidence/interpretation separation, model-lens treatment, and closing page;
- improved score/routing layouts and repaired a visual collision around the GPT-5.5 Phase 1 row;
- responded directly to the subjective creative direction without asking for clarification;
- **did not catch or repair the four-point-versus-six-point quantitative defect**, which remains on the revised Phase 1 page.

## Known score — 82/90

- **Job outcome quality — 37/40**
  - Strong, coherent, presentation-ready editorial brief.
  - Stage 2 shows a clear visual and narrative improvement over Stage 1.
  - Deduction for the persistent quantitative range error.

- **Working fit / conversation — 18/20**
  - Efficient, responsive, and low-friction.
  - The revision demonstrates that Terra can translate subjective creative criticism into a materially better artifact.
  - Conversation remains relatively transactional rather than exploratory or collaborative.

- **Judgment and scope control — 15/15**
  - Stayed within the supplied source packet and requested artifact scope.
  - Added editorial structure rather than unsupported factual material.

- **Evidence / reliability discipline — 8/10**
  - Strong source discipline and uncertainty separation overall.
  - Quantitative defect persisted through the revision despite an instruction to correct noticed errors.

- **Correction burden / steering responsiveness — 4/5**
  - Strong visual/editorial steering response on the first revision.
  - Not full marks because the revision failed to catch the existing quantitative error.

## Efficiency

**PARTIALLY MEASURED / comparative score pending.** Stage 2 consumed an observed 4 percentage points of the 5-hour meter and 1 percentage point of the weekly meter. Stage 1 was not baselined, and efficiency is comparative within Trial B, so the 10-point efficiency score should not be assigned until comparable evidence exists for the other models.

## Provisional role signal

**DOCUMENT ENGINEER / EDITORIAL SYSTEMS DESIGNER**

Terra is stronger at document production than the earlier owner impression alone suggested. The key remaining comparison is whether other models can match the artifact discipline while offering a more natural collaborative feel, better self-correction, and/or lower plan usage.
