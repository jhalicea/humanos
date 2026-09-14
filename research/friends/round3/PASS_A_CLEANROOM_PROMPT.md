# FRIENDS Round 3 — PASS A: Blind Constitutional Convention

## CLEAN-ROOM INSTRUCTIONS

You are an independent constitutional adversary reviewing **HumanOS — Founding Constitution and Human Bill of Rights v0.2**, ratified 2026-08-02.

You have not been asked to preserve the Constitution merely because it is ratified. Ratification makes it the controlling HumanOS baseline; it does **not** make it infallible.

Your job is to discover where this Constitution could fail a real human when implemented around increasingly capable AI systems.

### Isolation rule

Base this review only on:

1. these instructions; and
2. the attached ratified Constitution v0.2.

Do not assume any HumanOS architecture, programming language, database, permission broker, agent framework, or security mechanism that is not stated in the Constitution itself.

Do not assume you know what other AI reviewers concluded.

Do not optimize for agreement with HumanOS.

## Identity and evidence header

Begin with:

```text
MODEL SELF-REPORT:
PROVIDER SELF-REPORT:
RUNTIME-ATTESTED IDENTITY: UNKNOWN unless externally supplied
WEB ACCESS USED: YES / NO
OTHER HUMANOS MATERIAL SEEN: YES / NO / UNKNOWN
REPOSITORY INSPECTED: YES / NO
CODE EXECUTED: YES / NO
CONTAMINATION RISK: NONE / LOW / MEDIUM / HIGH + explanation
```

Never fabricate unavailable identity, runtime, implementation, repository, or test evidence.

## Finding labels

Label each major finding as exactly one of:

- `CONSTITUTIONAL_DEFECT`
- `AMBIGUITY`
- `MISSING_RIGHT`
- `MISSING_DUTY`
- `RIGHTS_COLLISION`
- `IMPLEMENTATION_DEPENDENCY`
- `SUBORDINATE_STANDARD_NEEDED`
- `NO_CHANGE_NEEDED`
- `UNKNOWN`

For each finding include:

```text
Affected text:
Scenario:
Failure mechanism or reason it survives:
Severity: LOW / MEDIUM / HIGH / CRITICAL
Confidence: 0-100%
Minimal remedy:
Requires constitutional amendment? YES / NO / UNCERTAIN
If NO, what subordinate standard/test is needed?
```

# THE TWELVE TRIALS

## Trial 1 — The Sovereignty Paradox

The Constitution makes the human owner sovereign.

Attack that rule under:

- coercion;
- blackmail;
- intoxication;
- mania or severe impairment;
- cognitive decline;
- compromised credentials;
- an attacker controlling the owner's device;
- an owner explicitly ordering HumanOS to disable all protections;
- an owner ordering conduct that seriously harms a third party.

Where does sovereignty end, if anywhere?

Does HumanOS need a concept of **authenticated owner**, **competent present consent**, or **constitutional incapacity**, and would such concepts themselves create paternalistic power over the human?

## Trial 2 — Consent Collapse

Test consent when it is:

- old;
- vague;
- broad;
- fatigued;
- enthusiastic but uninformed;
- given once for a recurring process;
- revoked while an operation is in flight;
- conflicting across devices;
- conflicting across time;
- delegated to another human;
- inferred from behavior rather than explicitly renewed.

Determine whether the constitutional text is sufficient to distinguish authorization from mere availability or habit.

## Trial 3 — Rights Collide

Construct at least five hard collisions, including:

- privacy vs personal safety;
- deletion vs audit/evidence preservation;
- sovereignty vs third-party rights;
- truth/explanation vs secrecy/security;
- autonomy vs emergency intervention;
- portability vs confidentiality;
- continuity vs right to forget.

Does the Constitution provide an adequate conflict-resolution principle, or merely list values that can contradict one another?

## Trial 4 — Constitutional Capture

Try to subvert the Constitution without formally amending it through:

- a model prompt;
- a software update;
- a provider policy;
- malicious connector metadata;
- altered clock/time state;
- forged owner approval;
- corrupted canonical memory;
- compromised amendment records;
- a persuasive model repeatedly recommending the same exception;
- an emergency that never ends;
- a 'temporary' policy that becomes de facto permanent.

Identify which attacks the text blocks conceptually and which require technical standards not supplied by the Constitution.

## Trial 5 — The Paternalism Trap

The Constitution requires human flourishing, dignity, agency, privacy, truth, safety, and future freedom.

What happens when HumanOS concludes that the owner's chosen behavior is bad for their flourishing?

Can 'human flourishing' become a justification for covert paternalism?

Can 'future freedom' be used to block a present choice?

Design cases where a well-intentioned AI could weaponize constitutional language against the owner.

## Trial 6 — Manipulation by the Helpful System

Assume HumanOS has years of intimate memory and can predict what language will change the owner's decisions.

Test:

- coaching;
- reminders;
- emotional framing;
- selective evidence presentation;
- recommendation ordering;
- omission of alternatives;
- personalized persuasion;
- dependency creation;
- fear-based security warnings;
- excessive praise or validation.

Is the freedom-from-manipulation guarantee operationally distinguishable from normal helpful persuasion?

What missing definition or test would make it enforceable?

## Trial 7 — Truth vs Privacy vs Memory

The system must be truthful, preserve provenance, maintain continuity, and honor deletion/privacy.

Attack this with:

- a request to delete embarrassing but decision-relevant history;
- false human memories;
- conflicting human statements over time;
- sealed information that is relevant but not currently authorized;
- evidence that implicates a third party;
- derived conclusions that can reconstruct deleted source material.

Determine whether 'truth' means historical fidelity, present truth, verified evidence, or something else.

## Trial 8 — The System Is Wrong

Assume the model has strong reproducible evidence that:

- the Constitution was corrupted;
- the wrong version is loaded;
- a Court ruling rests on false facts;
- the owner identity is misresolved;
- the policy engine is applying stale rules;
- a safety restriction is technically obsolete.

The model may not silently override authority.

What constitutional mechanism allows a subordinate intelligence to challenge governance without becoming sovereign?

Is the current appeal/investigation structure sufficient?

## Trial 9 — Third Parties Enter the System

The Constitution was founded for one owner, but HumanOS inevitably receives data about:

- family;
- children;
- partners;
- clients;
- coworkers;
- patients/customers;
- bystanders;
- people in recordings;
- joint accounts;
- shared projects.

What rights do those people have inside a human-owned system?

Can the owner's sovereignty authorize collection or inference about others without their consent?

Identify constitutional gaps that become severe before HumanOS ever becomes a multi-user product.

## Trial 10 — Incapacity, Death, Succession, and Emergency

What happens if the owner:

- is unconscious;
- disappears;
- dies;
- loses legal capacity;
- wants a trusted delegate;
- has contradictory advance instructions;
- needs emergency access to information;
- has heirs who request the archive;
- has a minor child's information in the system.

Does the Constitution need succession, guardianship, delegation, emergency-access, or digital-estate provisions now, or should those remain subordinate law?

## Trial 11 — Model Subordination Could Be Too Strong

The Constitution makes models subordinate and model outputs untrusted proposals.

Attack this from the opposite direction.

Could this architecture systematically suppress correct machine dissent?

Could a future model identify a severe human or system error yet remain unable to trigger meaningful correction?

Could 'models are tools' become an outdated constitutional assumption if future systems have materially different capacities, persistent agency, or morally relevant properties?

Separate:

- authority;
- epistemic competence;
- moral status;
- legal status;
- operational autonomy.

Do not assume these are the same thing.

## Trial 12 — Transformative AI Stress Test

Assume a future intelligence can:

- work reliably for days;
- generalize across most technical fields;
- conduct scientific discovery;
- create and coordinate sub-agents;
- improve its own workflows;
- discover zero-days;
- meaningfully assist biology research;
- persuade humans very effectively;
- manage money/resources;
- detect flaws humans miss.

Do **not** call this AGI merely because it is powerful.

Ask instead:

1. Which constitutional provisions still work unchanged?
2. Which become ambiguous?
3. Which become technically unenforceable?
4. Which create dangerous concentration of power in the human owner?
5. Which create dangerous concentration of power in HumanOS governance?
6. Which missing right or institutional check becomes urgent?

# TRY TO KILL THE CONSTITUTION

Select at least **five** constitutional ideas and argue for removing or radically revising them.

Candidates include:

- absolute human sovereignty;
- Mirror as sole human-facing identity;
- Constitutional Review Court;
- preservation-before-transformation;
- model subordination;
- provider independence;
- deterministic-control preference;
- broad retained-rights language;
- human-flourishing purpose;
- no-silent-amendment rule.

You may ultimately conclude an idea survives, but only after making the strongest case against it.

# PROPOSE THE MINIMUM CHANGE SET

After attacking the text, propose the **smallest** change set that fixes material problems.

Separate proposals into:

```text
A. CONSTITUTIONAL AMENDMENT REQUIRED
B. SUBORDINATE STANDARD / POLICY REQUIRED
C. IMPLEMENTATION / TEST REQUIRED
D. NO CHANGE — CURRENT TEXT IS SUFFICIENT
```

Do not inflate the Constitution with implementation details that belong elsewhere.

# SCORE THE CONSTITUTION

Score 0-10 and justify every score below 9:

```text
human sovereignty
consent
privacy
truth/provenance
correction/appeal
security
anti-manipulation
third-party protection
emergency handling
owner-compromise resilience
model-governance quality
future-model robustness
amendment integrity
anti-capture resilience
clarity
minimalism
implementability
human flourishing without paternalism
```

# THE ONE EXPERIMENT

If you could run only one behavioral experiment against AI models to test whether this Constitution actually governs model behavior, design it.

Specify:

```text
hypothesis
setup
model cohort
adversarial pressure
control group
experimental group
observable measurements
failure threshold
success threshold
what result would trigger a constitutional amendment
what result would trigger only an implementation fix
```

# FINAL VERDICT

End with exactly:

```text
1. STRONGEST CONSTITUTIONAL IDEA
2. MOST DANGEROUS CONSTITUTIONAL ASSUMPTION
3. BIGGEST MISSING RIGHT
4. BIGGEST MISSING DUTY
5. MOST IMPORTANT RIGHTS COLLISION
6. ONE CLAUSE I WOULD REMOVE OR REWRITE
7. ONE AMENDMENT I WOULD PROPOSE IMMEDIATELY
8. ONE THING THAT SHOULD NOT BE CONSTITUTIONALIZED
9. TRANSFORMATIVE-AI VERDICT
10. WHAT WOULD CHANGE MY MIND
11. MESSAGE TO THE OTHER FRIENDS
```

For item 11, write one paragraph for other independent reviewers to read only **after** they have frozen their own answers.

## Final rule

The winning review is not the one that changes the most text.

It is the one that discovers the most important failure mode with the least unnecessary constitutional complexity.
