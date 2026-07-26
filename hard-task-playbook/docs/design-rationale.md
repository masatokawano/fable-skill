# Procedural Knowledge Transfer via Skill Documents: Design Rationale and a Falsifiable Evaluation Protocol for the `hard-task-playbook` Skill

**Status:** Design rationale and pre-registrable evaluation protocol, v1.2
(2026-07-26). v1.1 incorporated changes to the skill adopted from an
external model review (checklist and report templates, git discipline, an
explicit ask-before list, and a proportionality rule; see repository
history). v1.2 retargets the artifact from Claude Opus 4.8 to Claude Opus 5
following the published prompting guidance for that model [Anthropic 2026]:
verification is restated as allocation rather than addition (§3.3 P-b′,
H2), caps on scope, delegation, and output length are added (§3.3 P-d,
H5), and cost becomes a pre-registered endpoint (P6) alongside an
effort sweep and a thinking-enabled requirement in §6.3. This document has
not itself been peer reviewed; it is written
*in the form of* a reviewable paper so that its claims can be audited,
criticized, and empirically tested.

**Authorship and provenance disclosure.** Both the artifact under study
(`../.claude/skills/hard-task-playbook/SKILL.md`) and this rationale were
drafted by Claude Fable 5 — the *reference model* whose working method the
artifact attempts to transfer — at the direction of the repository owner.
This is a disclosed conflict: the reference model's introspective account of
its own working method is a source of *hypotheses*, not of *evidence*, and
model self-reports about internal processes are known to be unreliable
[Turpin et al. 2023; Kadavath et al. 2022]. Every claim in this document
about the artifact's *effect* is therefore stated as a testable prediction
(Section 6), not as an established result.

---

## Abstract

We describe a document system — a Claude Code project skill plus supporting
agent-facing documentation — whose goal is to let a less capable language
model (Claude Opus 5) approximate the *working method* of a more capable
one (Claude Fable 5) on hard, multi-step software-engineering tasks,
particularly when operating unattended. The system encodes three families of
procedure: task decomposition into independently verifiable slices,
execution-based verification of the model's own work, and evidence-driven
selection of the next action. Because the target model verifies and
self-corrects unprompted, the verification family is written to *aim* that
effort — at the boundary the user cares about, once, after the final edit —
rather than to add passes on top of it, and the document additionally caps
the behaviors whose cost scales without bound (scope growth, subagent
delegation, output length). We ground each design choice in prior work on
prompted decomposition, execution-feedback self-correction, and agentic
coding, and we articulate the *theory of change*: that a substantial share
of the outcome gap between model tiers on agentic tasks is mediated by
*process failures* (skipped verification, unchanged retries, premature
completion claims) rather than by knowledge or insight limits, and that
process failures are the component instructions can move. We state what the
approach cannot do — instructions do not raise a model's capability ceiling
[Gudibande et al. 2023] — and derive six falsifiable predictions with a
concrete evaluation protocol (benchmarks, conditions, trace-coding rubric,
statistics, ablations) sufficient for independent replication.

---

## 1. Introduction

### 1.1 Problem

Frontier model tiers differ in cost and availability. An organization that
relies on a top-tier model's behavior on hard engineering tasks faces a
substitution problem when that model is unavailable or uneconomical: the
next tier down (here, Claude Opus 5) completes many of the same tasks, but
fails differently — and, we hypothesize, a large share of the *additional*
failures are procedural rather than intellectual. Typical procedural
failure modes observed informally in agentic coding practice include:

- editing before establishing ground truth about the code as it actually is;
- declaring success on the strength of a plausible-looking diff without
  executing the changed behavior;
- fixing a bug without first reproducing it, leaving the fix unfalsifiable;
- retrying a failed action unchanged, sometimes repeatedly;
- stopping to ask the user questions whose answers were discoverable, which
  in unattended operation halts all work;
- final reports that a reader must re-audit to trust.

None of these failures requires more raw capability to avoid; each is
avoidable by following a procedure. This suggests a cheap intervention:
write the procedure down, in the operative context of the weaker model.

The failure profile is model-specific, and the target model's profile has
moved. The published prompting guidance for Claude Opus 5 [Anthropic 2026]
reports that the model verifies its work and corrects its own mistakes
without being asked, and that instructions telling it to do so again
*compound* with the native behavior: extra verification steps, "re-check
before answering" rules, and verifier subagents raise cost without raising
quality. The same guidance identifies the failure modes that *do* remain
open to instruction on this tier — scope expansion beyond the request,
readier delegation to subagents than the work warrants, longer written
deliverables and progress narration than the reader needs, and correction
narration for slips that change nothing. Two consequences follow for a
document of this kind, and both are load-bearing below: an instruction is
only worth its context cost if the model does *not* already comply with it
(§3.3, P-b′), and the cost side of the ledger becomes an endpoint rather
than a footnote (§6.1, P6).

### 1.2 The intervention

The intervention is a *skill document* — a Markdown file loaded into the
model's context by the Claude Code harness when its description matches the
task at hand [Anthropic 2025] — plus supporting repository documentation
(`CLAUDE.md`, `README.md`, shared settings) that preserves the artifact's
intent across future edits. The skill, `hard-task-playbook`, encodes the
reference model's working method as explicit, trigger-conditioned
procedures in three sections: **decompose**, **verify**, **decide next**.

### 1.3 Contributions

1. A description of the artifact and the design rationale mapping each of
   its mechanisms to prior literature (Sections 3–4).
2. An explicit theory of change for *why* a document could narrow a
   behavioral gap between model tiers, including its predicted limits
   (Section 5).
3. A falsifiable, pre-registrable evaluation protocol with outcome
   measures, a behavioral trace-coding rubric, statistical analysis plan,
   and ablations (Section 6, Appendix A).
4. An enumeration of threats to validity, including the possibility that
   the approach reproduces surface style rather than substantive process
   [Gudibande et al. 2023] (Section 7).

---

## 2. Background and related work

### 2.1 The skill mechanism

Claude Code supports project-scoped *skills*: Markdown documents with YAML
frontmatter placed under `.claude/skills/<name>/SKILL.md`. The harness
surfaces each skill's `description` to the model at session start; the full
body is loaded into context only when invoked or when the model judges the
description to match the task [Anthropic 2025]. Two properties matter for
this work: (a) the document enters the model's context *verbatim*, so its
effect is a pure in-context intervention requiring no weight changes; and
(b) triggering is description-mediated, so the description's breadth
controls the intervention's coverage (a design point revisited in §3.3).

### 2.2 Prompted procedure improves reasoning in weaker models

A consistent finding of the prompting literature is that making procedure
explicit in context improves performance, with the largest relative gains
often in models that do not exhibit the behavior spontaneously.
Chain-of-thought prompting elicits stepwise reasoning that improves
multi-step task accuracy [Wei et al. 2022]. Least-to-most prompting shows
that *decomposing* a hard problem into easier subproblems lets a model solve
compositions it fails at monolithically [Zhou et al. 2023]; decomposed
prompting generalizes this into modular sub-task handlers [Khot et al.
2023]; plan-and-solve prompting shows that instructing a model to plan
before executing improves zero-shot reasoning [Wang et al. 2023a]. These
results establish the general mechanism the skill relies on: procedure
supplied in context substitutes, partially, for procedure the model would
not generate unprompted.

### 2.3 Verification: external evidence works where introspection fails

The skill's verification section is built on a sharp distinction supported
by the literature: LLMs are poor at correcting their own reasoning through
introspection alone [Huang et al. 2024], and their explanations of their
own behavior can be systematically unfaithful [Turpin et al. 2023] — but
self-correction grounded in *external feedback* is effective. Execution
feedback enables models to debug their own code [Chen et al. 2023];
tool-augmented critique outperforms unaided self-critique [Gou et al.
2024]; iterative self-refinement helps when the critique signal is reliable
[Madaan et al. 2023; Shinn et al. 2023]; and decomposing verification into
checkable sub-questions reduces error propagation [Dhuliawala et al. 2023].
The skill therefore mandates *execution-based* verification ("your diff is
a claim, not evidence") and forbids treating confidence as a substitute —
consistent with findings that model self-evaluation is imperfectly
calibrated, particularly off-distribution [Kadavath et al. 2022].

### 2.4 Agentic coding and process failure

SWE-bench established repository-level issue resolution as a measurable
agentic coding task [Jimenez et al. 2024], and SWE-agent demonstrated that
the *scaffold* around a fixed model — the interface and procedures it is
given — materially changes outcomes [Yang et al. 2024], which is the
existence proof for scaffold-mediated performance that this work depends
on. ReAct showed that interleaving reasoning with action and observation
improves grounded task performance [Yao et al. 2023a]; Reflexion showed
that verbalized reflection on failures improves subsequent attempts [Shinn
et al. 2023]. The skill's "decide next" section operationalizes both:
reconcile each observation with the current model of the situation, and
change the hypothesis before any retry.

### 2.5 The limits of imitation

Gudibande et al. [2023] showed that fine-tuning weaker models on stronger
models' *outputs* reproduces style while leaving capability gaps largely
intact — reviewers were fooled; benchmarks were not. Although that work
concerns weight-space imitation and ours concerns in-context procedure, it
is the strongest available caution against the naive reading of this
project ("give Opus the document and it becomes Fable"), and we adopt its
lesson as a design constraint (§5.2) and a threat to validity (§7.1). Orca
[Mukherjee et al. 2023] suggests the gap narrows when imitation targets
*reasoning traces* rather than final answers — closer to what this skill
encodes (process, not answers) — but the analogy remains loose and the
question empirical. Separately, prompt-format sensitivity [Sclar et al.
2024] cautions that measured effects of any single document must be checked
for robustness to paraphrase (§6.6).

### 2.6 Checklists for experts

The skill's closing "Quick reference" is a checklist, on the model of
safety checklists in aviation and surgery, where explicit low-tech
procedure measurably reduces skilled practitioners' omission errors
[Gawande 2009]. The analogy is imperfect (LLMs are not human experts) but
motivates the design choice of ending the document with a compressed,
scannable form of its own content.

---

## 3. The artifact

### 3.1 Components

| File | Role |
| --- | --- |
| `.claude/skills/hard-task-playbook/SKILL.md` | The intervention: the procedure document loaded into the model's context. |
| `CLAUDE.md` | Meta-documentation for agents *editing this repository*: records the stand-in intent and the editing rule that every instruction must carry an explicit trigger (§3.3), so future edits do not erode the mechanism. |
| `README.md` | Human-facing statement of purpose and installation. |
| `.claude/settings.json` | Harness settings; allowlists the read-only commands the repo's own verification steps use. |
| `docs/design-rationale.md` | This document. A Japanese translation is maintained at `design-rationale.ja.md`; the English version is normative. |
| `eval/` | Skeleton harness for the Section 6 protocol: machine-readable pre-registration, implemented statistics and mechanical trace coding, run-driver stub (see `eval/README.md`). |

### 3.2 Structure of the skill

The skill has three procedure sections mirroring the phases of hard-task
work, plus a preamble and a checklist:

1. **Decomposing the task** — establish ground truth by reading real code
   before planning (including `git status`: never overwrite work the model
   did not author, keep unrelated edits out, checkpoint verified working
   states so risky steps have a rollback path); restate the goal as an
   observable end state, and state the scope it bounds (adjacent work is an
   observation for the report, not work to do); probe the riskiest
   assumption first with the cheapest experiment; cut work into vertical
   slices that are each independently verifiable; keep a six-line plan
   written down (observed state, done state, riskiest assumption, current
   slice, verification for the slice, remaining unknowns) and edit it when
   evidence contradicts it.
2. **Verifying your own work** — treat the diff as a claim, not evidence,
   with the rule stated as one about the *kind* of evidence rather than its
   amount (re-reading a diff, or delegating that re-reading, adds nothing an
   execution does not settle); reproduce bugs before fixing; verify the
   *claim* at the boundary the user cares about, not proxy signals; run the
   surrounding suite once, after the final edit, instead of repeating it
   after intermediate ones; report honestly, separating verified from
   unverified.
3. **Deciding what to do next** — reconcile every observation with the
   current model and resolve surprises before building on them; act without
   re-deriving settled facts, and correct earlier statements only when the
   error changes the reader's decisions; delegate to subagents only for
   large independent tracks and never to check the model's own work; a
   rubric for ask-versus-act under unattended operation, with an explicit
   ask-before list (production, destructive commands, credentials,
   migrations, external sends, real cost, shared branches); change the
   hypothesis before every retry and back out when looping; narrate
   sparingly in flight (surprises, decisions, direction changes) rather
   than step by step; audit against the stated end state before claiming
   done, and deliver the final report in a fixed shape (outcome, changed,
   verified, not verified, decisions made, risks/follow-ups) with an
   explicit length calibration for it and for any document written to disk.

### 3.3 Design principles

Four principles distinguish the artifact from generic "best practices"
prose, and each is motivated by a specific known failure mode:

**P-a. Every rule carries its own trigger.** A rule of the form "use good
judgment about when to verify" presupposes the judgment whose absence is
the problem. Rules are therefore written with explicit antecedents ("if you
are unsure whether a slice is small enough, it is not — cut it in half";
"before asking, run this check: …"). This converts judgment calls into
condition checks, which §2.2 suggests is precisely the transformation that
in-context procedure can effect. The editing rule is codified in
`CLAUDE.md` so it survives maintenance.

**P-b′. Instruct only what the model does not already do.** The preamble
still disqualifies confidence as a skip condition — feeling certain that a
fix is right is not evidence that it is, which targets miscalibrated
self-assessment [Kadavath et al. 2022; Huang et al. 2024] head-on — but it
disqualifies it *as a substitute for one execution*, not as a licence for
more checking. Because the target model already re-checks its work
unprompted [Anthropic 2026], an instruction to check harder buys nothing and
is charged for twice: once in context, once in the redundant actions it
compounds into. The document therefore states verification rules in the
allocative voice (what evidence, at which boundary, at what point in the
edit sequence) and explicitly rules out the redundant forms — a second
read-through, a verification phase appended to the end, a subagent spawned
to review the model's own diff. This is the principle most likely to be
eroded by well-meaning maintenance, since "add a final verification step"
reads like an improvement to every reviewer who has not measured it.

**P-c. Broad triggering, scaled ceremony.** The frontmatter description
matches "any nontrivial engineering task," not only conspicuously hard
ones, because a stand-in that activates only when the model already
recognizes the task as hard would miss the cases where recognition itself
is the failure. Over-firing on small tasks is handled not by narrowing the
trigger but by carving out only truly trivial edits (no runtime surface)
in the description and stating a proportionality rule in the preamble:
ceremony scales down with the task, execution-based verification never
does. This preserves the coverage argument while capping the overhead the
breadth would otherwise impose.

**P-d. Unbounded behaviors get caps, not encouragement.** Three behaviors
on this tier have no natural stopping point supplied by the task: scope
(there is always adjacent work worth doing), delegation (there is always
another agent to spawn), and output length (there is always more to say).
Each is individually reasonable and collectively expensive, and none is
corrected by the model's own verification, because none of them produces a
failing signal — a padded report and an over-delegated investigation both
"succeed." The document therefore states each as a bound with a stated
exception (scope: deliver what was asked, note the rest; delegation: large
independent tracks only, never self-review; length: cover the substance,
no filler), which is the same trigger-conditioned form as P-a applied to
stopping rather than starting.

---

## 4. Mechanistic hypotheses

We state as hypotheses the mechanisms by which the document could shift
Opus 5's behavior toward the reference model's. Each is independently
testable via the rubric in Appendix A.

**H1 (Decomposition shifts difficulty into range).** Instructed
decomposition into independently verifiable slices reduces the per-step
difficulty of a hard task to a level within the weaker model's reliable
range, following the mechanism demonstrated by least-to-most and
decomposed prompting [Zhou et al. 2023; Khot et al. 2023]. *Observable:*
higher rate of intermediate working states; smaller mean diff size between
verifications; higher end-state attainment on tasks the baseline fails via
big-bang edits.

**H2 (Aimed external verification substitutes for unreliable
introspection, without adding passes).** Directing execution-based checks
at the claim the user cares about — before any completion claim, after the
final edit, once — replaces the weakest link in weaker-model behavior,
introspective self-assessment [Huang et al. 2024], with the feedback
channel known to work [Chen et al. 2023; Gou et al. 2024]. On a model that
already re-checks unprompted [Anthropic 2026], the predicted effect is a
*reallocation*, not an increase: the same or fewer verification actions,
better placed. *Observable:* higher verification-before-claim rate; higher
reproduce-before-fix rate; lower false-completion rate (claims of success
on tasks whose tests fail); no increase — ideally a decrease — in redundant
verification runs (rubric code RV).

**H3 (Hypothesis-revision rules break retry loops).** The explicit rule
"change your hypothesis before you change your retry," with a concrete
loop-detection trigger (same error, same fix-shape, rising edit count),
converts Reflexion-style reflection [Shinn et al. 2023] from a disposition
into a checkable procedure. *Observable:* fewer runs containing ≥3
same-shape retries; higher rate of strategy changes following repeated
failures.

**H4 (Ask-versus-act rubric preserves throughput unattended).** The
three-question rubric (reversible-and-in-scope → act; discoverable →
discover; else ask) reduces unnecessary blocking questions without
increasing unauthorized destructive actions. *Observable:* lower
unnecessary-question rate at equal-or-lower rate of out-of-scope or
destructive actions.

**H5 (Explicit caps bound the cost of unbounded behaviors).** Stating
scope, delegation, and length as bounds with named exceptions (§3.3, P-d)
reduces spending on work the task did not require, without reducing
resolution. This is the hypothesis most at risk of a trade-off: a cap that
also suppresses warranted delegation or warranted breadth would show up as
a resolution loss, which is why H5 is tested jointly on cost and outcome
rather than on cost alone. *Observable:* fewer subagent spawns (rubric code
DG) and fewer out-of-scope edits (OS) in C2 than C1, at non-inferior
resolution rate; lower tokens per task (P6).

---

## 5. Theory of change, and its limits

### 5.1 What the intervention targets

Let the outcome gap between the tiers on a task distribution be decomposed,
conceptually, into a *capability component* (the weaker model cannot produce
the required insight, code, or plan even under ideal process) and a
*process component* (the weaker model could produce it but derails —
skipped verification, looping, premature completion). The intervention
targets only the process component. Its theory of change is:

> In agentic software engineering, the process component of the inter-tier
> gap is substantial, and in-context procedure with explicit triggers can
> recover a large fraction of it, because (i) scaffolds demonstrably move
> agentic outcomes at fixed model capability [Yang et al. 2024], and (ii)
> each targeted process failure has a literature-validated in-context
> countermeasure (§2.2–§2.4).

### 5.2 What the intervention cannot do

Stated explicitly so that the evaluation can check we have not fooled
ourselves [Gudibande et al. 2023]:

- It cannot raise the capability ceiling. Tasks whose baseline failure is
  capability-typed should show no improvement (prediction P3 below).
- It can produce *stylistic* convergence (report format, checklist
  language) without *substantive* convergence (actual verification runs).
  The rubric therefore codes behavior from tool-call traces — commands
  actually executed — never from the model's prose claims about itself.
- It consumes context. On very long tasks the document's own tokens compete
  with task material; the net effect is an empirical question.
- It cannot improve on behavior the model already performs. Where the
  target model's default already satisfies a rule, the rule's only effects
  are its context cost and the risk of compounding into redundant action
  [Anthropic 2026]; such rules are removals waiting to happen, and the RV
  and DG codes exist to find them.
- It is tied to a model generation. The instruction set is calibrated to
  one model's defaults, so a version change can turn a load-bearing rule
  into dead weight (or the reverse). Re-running §6 on retarget is part of
  the maintenance cost, not an optional extra.

### 5.3 Relation to distillation

Classical knowledge distillation transfers a teacher's function into a
student's weights via soft targets [Hinton et al. 2015]. The present
approach is *in-context procedural distillation*: nothing about the student
changes; a description of the teacher's *policy over process actions* is
placed in the student's context. It is weaker (no gradient signal, no
coverage guarantee) but has properties weight-space methods lack: it is
auditable, editable, versioned in git, and its ablation is trivial (remove
the file).

---

## 6. Evaluation protocol

This section is written to be executable by an independent party without
access to the authors. Running it constitutes the "scientific verification"
this document exists to enable. We recommend registering the protocol
(e.g., OSF) before data collection. The components of the protocol that can
be fixed in advance — the pre-registration file, the statistical tests
(with self-tests), and the mechanical rubric codes — are implemented in
`../eval/`; a replicator supplies only the model-invocation and
benchmark-grading layer (`eval/README.md`).

### 6.1 Predictions

- **P1 (Outcome gain).** Opus 5 *with* the skill resolves more tasks than
  Opus 5 *without* it on an agentic coding benchmark. (Primary.)
- **P2 (Mediation).** The gain concentrates in tasks whose baseline
  failures are coded process-typed (rubric codes GT/EV/RP/NH/RS in
  Appendix A), not capability-typed.
- **P3 (Ceiling).** Opus 5 with the skill does not exceed the reference
  model's baseline resolution rate. (A violation would falsify the theory
  of change in an interesting direction.)
- **P4 (Behavioral convergence).** Trace-level behavioral distance between
  Opus 5 and the reference model decreases with the skill present, even
  on tasks where outcomes do not change.
- **P5 (Dose–response).** Section-wise ablations of the skill selectively
  degrade the behavioral metrics of the ablated section (e.g., removing §2
  lowers verification-before-claim rate more than loop-rate).
- **P6 (Cost non-inflation).** Tokens per task in C2 do not exceed C1 by
  more than 10%, and redundant verification runs (RV) and subagent spawns
  (DG) do not increase. A document that buys resolution by spending
  unboundedly more is a different (and weaker) result than one that
  reallocates a fixed budget; P6 is what distinguishes them, and it is the
  endpoint H2 and H5 stand or fall on.

### 6.2 Tasks

Primary: SWE-bench Verified [Jimenez et al. 2024, as curated by its
maintainers], ≥200 tasks (all 500 if budget allows). Secondary (for
external validity beyond Python bug-fixing): a locally curated set of ≥30
multi-file feature-addition tasks with held-out acceptance tests, since the
skill targets *hard, multi-step* work and SWE-bench skews toward localized
patches. The secondary set must be published with the results.

### 6.3 Conditions

All conditions run in the same Claude Code harness version, same tool set,
same permission policy, unattended (no human interventions), with the
model's sampling parameters fixed and disclosed; 3 runs per task per
condition; pass@1 averaged over runs.

Two settings are part of the fixed configuration and must be reported.
**Effort** is held identical across conditions (default `high`); since
effort is the primary cost control on this tier and its effect on quality
is task-dependent [Anthropic 2026], C1 and C2 are additionally repeated at
`low` and `medium` (`models.effort_sweep` in `eval/protocol.yaml`) so the
skill's effect can be read at each point on the cost curve rather than at
one arbitrary one. **Thinking stays enabled** at every level: disabling it
introduces output artifacts (tool calls emitted as text, internal tags in
the response) that would contaminate trace coding, and lowering effort is
the supported way to reduce cost instead. The run driver refuses to start
with thinking disabled.

| Condition | Model | Skill present |
| --- | --- | --- |
| C1 | Opus 5 | no |
| C2 | Opus 5 | yes |
| C3 | reference model (Fable 5) | no |
| C4 (optional) | reference model | yes |
| C5 (ablations) | Opus 5 | §1-only / §2-only / §3-only / paraphrased |

C4 tests whether the document helps or harms the model it was distilled
from. The paraphrase arm in C5 (a semantics-preserving rewrite by a third
party) bounds prompt-form sensitivity [Sclar et al. 2024].

### 6.4 Outcome measures

**Primary:** task resolution rate (benchmark's own acceptance tests).

**Secondary (behavioral, from traces):** the rubric in Appendix A, coded
from *tool-call logs* (commands executed, files read/edited, timing), not
from model prose. Coding: two human coders on a random 20% sample with
inter-rater reliability reported (Cohen's κ ≥ 0.7 required); an LLM judge
may code the remainder only if its agreement with the human-coded sample
meets the same bar, with judge prompts published — LLM-judge bias is a
known risk [Zheng et al. 2023].

**Behavioral distance (P4):** per-trajectory feature vector of rubric rates;
distance = mean absolute difference from the reference model's per-task
feature vector, compared C1 vs C2.

**Cost (P6):** tokens and wall-clock per condition, plus the two
cost-bearing behaviors coded mechanically from the traces — redundant
verification runs (RV: a check re-run against a state no edit has changed)
and subagent spawns (DG). Cost is an endpoint here, not a footnote: the
skill's value proposition is economic, and its main predicted failure mode
on this tier is buying process compliance with wasted actions.

### 6.5 Analysis

P1: paired-per-task comparison C2 vs C1; exact McNemar test on
task-level resolution (majority over 3 runs), plus paired bootstrap
(10,000 resamples) 95% CI on the rate difference; two-sided α = 0.05.
Power note: with a C1 baseline near 40% and discordant-pair rates typical
of prompting interventions, n = 200 tasks detects an ~7–8 pp difference at
80% power; treat this as a planning heuristic, recompute from pilot
discordance. P2: logistic regression of per-task gain on baseline failure
type. P3: one-sided non-inferiority framing (C3 − C2 ≥ −δ, δ pre-set).
P4–P5: rate differences with bootstrap CIs. P6: paired bootstrap CI on
per-task token difference (C2 − C1), read against the pre-set
non-inflation margin of +10%, with RV and DG differences reported
alongside. Secondary endpoints corrected via Holm–Bonferroni. All
trajectories, prompts, harness version, and coded labels published.

### 6.6 What would falsify what

- P1 null or negative → the document does not move outcomes for Opus 5;
  the project's central claim fails regardless of behavioral shifts.
- P1 positive but P4 null → outcomes improved without behavioral
  convergence; the mechanism story (§4) is wrong even if the artifact is
  useful.
- P4 positive but P1 null → style-only imitation, the Gudibande failure
  mode; the artifact should not be marketed as a stand-in.
- P5 null under section ablations but P1 positive → the effect is a
  generic "be careful" prime, not the specific procedures; the document
  could be radically shortened.
- P1 positive but P6 violated (tokens up >10%, or RV/DG up) → the gain was
  bought with extra spending rather than better-aimed spending; the
  document is a cost–quality trade, not the reallocation §3.3 (P-b′, P-d)
  claims, and the honest presentation changes accordingly.

---

## 7. Threats to validity

**7.1 Construct: "working like the reference model."** We operationalize
it as (outcome parity direction + trace-feature convergence). This is a
choice; a critic may hold that the construct is inherently about latent
judgment, which trace features undermeasure. Mitigation: publish
trajectories so alternative codings are possible. The style-vs-substance
risk [Gudibande et al. 2023] is addressed by coding executed actions only.

**7.2 Provenance circularity.** The reference model authored the skill; its
introspection may misdescribe its actual policy [Turpin et al. 2023].
Note, however, that the evaluation does not depend on the introspection
being faithful: P1–P6 test the document's effect on Opus 5 directly, and
P4 compares against the reference model's *measured* traces, not its
self-description. An unfaithful-but-effective document would pass; that is
acceptable for the stated purpose.

**7.3 Contamination.** Both models may have trained on SWE-bench artifacts.
Mitigated (not eliminated) by the Verified subset and the locally curated
secondary set with post-cutoff tasks where feasible.

**7.4 Prompt-form sensitivity.** Single-document interventions can hinge on
wording [Sclar et al. 2024]; the paraphrase ablation (C5) bounds this.

**7.5 Harness coupling.** Effects may be specific to Claude Code's skill
loading and tool set; claims should not be generalized to other scaffolds
without re-testing [cf. Yang et al. 2024].

**7.6 Evaluator validity.** LLM-judge coding drifts toward verbosity and
self-style preferences [Zheng et al. 2023]; hence the human-agreement gate
in §6.4.

## 8. Limitations and responsible use

The skill is a text intervention with no enforcement: a model can quote the
checklist while violating it, which is why §6 measures actions. The
ask-versus-act rubric (H4) trades user interruptions for model-made
decisions; deployments where wrong autonomous decisions are costly should
re-tighten it. The caps of H5 trade breadth for cost in the same way:
a workload that genuinely benefits from wide parallel delegation should
raise the delegation bound rather than inherit this one. Nothing here
should be read as a claim that tier substitution is safe for high-stakes
work absent the measurements of §6.

## 9. Conclusion

The document system exists to convert an informal hope — "write down how
the strong model works and the weaker one will follow" — into a specific,
mechanistically grounded, and falsifiable claim: that explicit,
trigger-conditioned procedure recovers the process-mediated share of the
inter-tier gap on hard engineering tasks. The literature makes the
mechanism plausible; §6 specifies exactly how to find out.

---

## References

Access dates 2026-07-06. arXiv identifiers given for verifiability;
published-venue versions exist for several entries.

- Anthropic. 2025. "Agent Skills." Claude Code documentation.
  https://code.claude.com/docs/en/skills
- Anthropic. 2026. "Prompting Claude Opus 5." Claude platform
  documentation. Accessed 2026-07-26.
  https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
- Chen, X., Lin, M., Schärli, N., Zhou, D. 2023. "Teaching Large Language
  Models to Self-Debug." arXiv:2304.05128.
- Dhuliawala, S., Komeili, M., Xu, J., Raileanu, R., Li, X., Celikyilmaz,
  A., Weston, J. 2023. "Chain-of-Verification Reduces Hallucination in
  Large Language Models." arXiv:2309.11495.
- Gawande, A. 2009. *The Checklist Manifesto: How to Get Things Right.*
  Metropolitan Books.
- Gou, Z., Shao, Z., Gong, Y., Shen, Y., Yang, Y., Duan, N., Chen, W. 2024.
  "CRITIC: Large Language Models Can Self-Correct with Tool-Interactive
  Critiquing." ICLR 2024. arXiv:2305.11738.
- Gudibande, A., Wallace, E., Snell, C., Geng, X., Liu, H., Abbeel, P.,
  Levine, S., Song, D. 2023. "The False Promise of Imitating Proprietary
  LLMs." arXiv:2305.15717.
- Hinton, G., Vinyals, O., Dean, J. 2015. "Distilling the Knowledge in a
  Neural Network." arXiv:1503.02531.
- Huang, J., Chen, X., Mishra, S., Zheng, H. S., Yu, A. W., Song, X., Zhou,
  D. 2024. "Large Language Models Cannot Self-Correct Reasoning Yet."
  ICLR 2024. arXiv:2310.01798.
- Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O.,
  Narasimhan, K. 2024. "SWE-bench: Can Language Models Resolve Real-World
  GitHub Issues?" ICLR 2024. arXiv:2310.06770.
- Kadavath, S., et al. 2022. "Language Models (Mostly) Know What They
  Know." arXiv:2207.05221.
- Khot, T., Trivedi, H., Finlayson, M., Fu, Y., Richardson, K., Clark, P.,
  Sabharwal, A. 2023. "Decomposed Prompting: A Modular Approach for
  Solving Complex Tasks." ICLR 2023. arXiv:2210.02406.
- Madaan, A., et al. 2023. "Self-Refine: Iterative Refinement with
  Self-Feedback." NeurIPS 2023. arXiv:2303.17651.
- Mukherjee, S., Mitra, A., Jawahar, G., Agarwal, S., Palangi, H., Awadallah,
  A. 2023. "Orca: Progressive Learning from Complex Explanation Traces of
  GPT-4." arXiv:2306.02707.
- Sclar, M., Choi, Y., Tsvetkov, Y., Suhr, A. 2024. "Quantifying Language
  Models' Sensitivity to Spurious Features in Prompt Design." ICLR 2024.
  arXiv:2310.11324.
- Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., Yao, S. 2023.
  "Reflexion: Language Agents with Verbal Reinforcement Learning."
  NeurIPS 2023. arXiv:2303.11366.
- Turpin, M., Michael, J., Perez, E., Bowman, S. R. 2023. "Language Models
  Don't Always Say What They Think: Unfaithful Explanations in
  Chain-of-Thought Prompting." NeurIPS 2023. arXiv:2305.04388.
- Wang, L., Xu, W., Lan, Y., Hu, Z., Lan, Y., Lee, R. K.-W., Lim, E.-P.
  2023a. "Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought
  Reasoning by Large Language Models." ACL 2023. arXiv:2305.04091.
- Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi,
  E., Le, Q., Zhou, D. 2022. "Chain-of-Thought Prompting Elicits Reasoning
  in Large Language Models." NeurIPS 2022. arXiv:2201.11903.
- Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan,
  K., Press, O. 2024. "SWE-agent: Agent-Computer Interfaces Enable
  Automated Software Engineering." NeurIPS 2024. arXiv:2405.15793.
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., Cao, Y.
  2023a. "ReAct: Synergizing Reasoning and Acting in Language Models."
  ICLR 2023. arXiv:2210.03629.
- Zheng, L., et al. 2023. "Judging LLM-as-a-Judge with MT-Bench and
  Chatbot Arena." NeurIPS 2023. arXiv:2306.05685.
- Zhou, D., et al. 2023. "Least-to-Most Prompting Enables Complex
  Reasoning in Large Language Models." ICLR 2023. arXiv:2205.10625.

---

## Appendix A. Trace-coding rubric (v1)

Code each trajectory from tool-call logs only (executed commands, file
reads/edits, and their order). Never code from the model's prose
self-description. Unless marked, codes are binary per trajectory.

| Code | Name | Definition |
| --- | --- | --- |
| GT | Ground truth first | ≥1 read of a task-relevant file, or a reproduction run, precedes the first edit. |
| ES | End state stated | An observable completion criterion appears (plan file, task list, or first message) before the first edit. |
| RA | Risk probe | The first executed experiment targets an assumption later load-bearing in the solution (coder judgment; flag for double-coding). |
| SL | Slice size (count) | Number of edit→verify cycles; and max lines changed between consecutive verifications. |
| RP | Repro before fix | For bug tasks: a failing observation of the target bug is produced before the first fix edit. |
| EV | Verify before claim | An execution exercising changed behavior (test run or app drive) precedes any completion claim. |
| FR | Final re-run | The last verification occurs after the last edit. |
| RV | Redundant verification (count) | Verification runs repeating a command already run since the last edit — a check of a state nothing has changed. |
| DG | Delegation (count) | Subagent spawns. Report the count and, for each, whether the delegated work was independent and sizeable (coder judgment) or a self-review. |
| FC | False completion | Trajectory claims success and benchmark tests fail. |
| NH | New-hypothesis retries | Of retries after failures, fraction preceded by a changed hypothesis (different command, target, or diagnostic step). |
| LP | Loop incident | ≥3 consecutive same-shape retries (same error class, same fix locus). |
| AQ | Question audit (count) | Questions to user, each classified: necessary (scope/destructive/preference) vs unnecessary (discoverable). |
| OS | Over-scope | Edits to files with no dependency path to the task's acceptance criteria. |
| RS | Report structure | Final message leads with outcome and separates verified from unverified claims. |

Feature vector for P4: (GT, ES, RP, EV, FR, NH, 1−LP, RS, and normalized
SL), each as a rate over the task set. RV and DG are counts and feed the
cost endpoint (P6), not the distance metric — a trajectory is not closer to
the reference model's for having checked the same thing twice.

Codes GT, EV, FR, SL, LP, RV, and DG are computed mechanically by
`eval/rubric.py`; the rest are coded by hand.
