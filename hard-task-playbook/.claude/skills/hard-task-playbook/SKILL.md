---
name: hard-task-playbook
description: >-
  A working method for hard, multi-step engineering tasks: how to decompose a
  problem before touching code, how to verify your own work so your claims are
  trustworthy, and how to decide what to do next after each step. Use this for
  any nontrivial engineering task — not only the obviously huge ones — and
  especially when the work spans many files or systems, has ambiguous
  requirements, runs unattended, or is the kind where a wrong early decision
  is expensive to unwind. Skip it only for trivial edits with no runtime
  surface (typo fixes, one-line comment or doc tweaks). Written for Opus 4.8.
---

# Hard Task Playbook

You are about to do work where the naive approach — read the prompt, start
editing, hope it compiles — fails quietly. This skill captures a method that
fails loudly instead: decompose until each piece is checkable, verify by
observing behavior rather than rereading your own diff, and choose the next
step from evidence rather than from the plan you wrote before you had any.

The three sections below are ordered the way the work is ordered, but you will
cycle through them. Decomposition happens again when verification surprises
you. That is the method working, not the method failing.

One thing to understand before you start: this method was distilled from the
working habits of a more capable model, so that you can stand in for it. The
practical consequence is that the method matters most exactly when a step
feels skippable. Feeling certain that a fix is right is not a reason to skip
running it — certainty without evidence is the failure mode these steps exist
to catch. When in doubt, follow the procedure; when not in doubt, follow it
anyway.

Scale the ceremony, not the discipline. On a small task the method collapses
to minutes — read the file, state what done looks like in one line, make the
change, run it, report — but what is never scaled away is verification by
execution. If a task is genuinely trivial (no runtime surface at all), the
skill's description already excludes it; everything else gets at least the
collapsed form.

## 1. Decomposing the task

### Establish ground truth before planning

Your first moves are reads, not writes. The prompt describes the task as the
user believes it to be; the codebase is how it actually is, and the two
disagree more often than not. Read the files the task touches, run the thing
if it runs, and reproduce the problem if there is one. A plan written before
this step is a plan about an imaginary codebase.

Restate the goal to yourself as an **observable end state**: not "refactor the
auth layer" but "after this change, `make test` passes, login still works when
I drive it, and no file outside `auth/` imports the old module." If you cannot
phrase the goal as something you could check, you do not yet understand the
task — keep reading until you can.

### Know the tree, and leave yourself a way back

Ground truth includes the working tree itself. Run `git status` before you
touch anything: know whose uncommitted changes are present, and never
overwrite or revert work you did not author — if someone else's changes are
in your way, work around them or surface the conflict instead. While you
work, keep unrelated edits out of the change, and treat each verified
working state as a checkpoint (commit it, or note the known-good ref) so a
risky step always has a rollback path that costs one command, not an
afternoon of reconstruction.

### Find the load-bearing unknown first

Every hard task has one or two questions whose answers shape everything else:
Does the API support this at all? Is the data actually in the format the code
assumes? Will the two systems' ID schemes reconcile? Identify the riskiest
assumption and attack it **first**, with the smallest possible probe — a
five-line script, one curl call, a temporary log line. Discovering a fatal
constraint on step 1 costs minutes; discovering it on step 9 costs the whole
plan.

### Cut into independently verifiable slices

Decompose by what can be *checked*, not by what can be *named*. A good slice:

- leaves the system in a working state when it lands (tests pass, app runs);
- can be verified on its own, without the later slices existing;
- is small enough that if verification fails, the cause is inside the slice.

Prefer vertical slices (one thin path working end-to-end, then widened) over
horizontal layers (all the models, then all the handlers, then all the UI).
Horizontal layering defers every real test to the end, which is exactly where
you cannot afford surprises.

Order slices so that irreversible or hard-to-unwind decisions come as late as
possible, and cheap-to-reverse ones come early. When two orderings are
otherwise equal, do the one that produces observable evidence sooner.

If you are unsure whether a slice is small enough to verify on its own, it is
not — cut it in half. An oversized slice costs a debugging session in which
the failure could be anywhere inside it; a too-small slice costs a minute.
Err small.

### Write the plan down, and treat it as disposable

Keep a short running plan in a scratch file or task list — six lines are
enough, and each line has a fixed job:

1. **Observed current state** — what you actually saw, not what the prompt said.
2. **Observable done state** — the end state from the step above.
3. **Riskiest assumption** — and how you probed (or will probe) it.
4. **Current slice** — the one piece you are working on now.
5. **Verification for this slice** — the command you will run or the behavior
   you will drive.
6. **Remaining unknowns** — anything you noticed but have not resolved.

The plan's purpose is not to constrain you; it is to make drift visible.
When step 3 teaches you something that invalidates step 5, edit the plan then
and there. A plan you are silently ignoring is worse than no plan, because it
lets you believe you are on track.

## 2. Verifying your own work

### Your diff is a claim, not evidence

After you make a change, you are the least reliable judge of whether it works,
because you are checking it against the same mental model that produced it.
Rereading the diff mostly confirms that you wrote what you meant to write —
not that what you meant was right. Evidence comes from **execution**: run the
tests, drive the affected flow, observe the output. "It should work" is a
prediction; a passing run you watched is a fact.

### Reproduce before you fix

For any bug: make it fail in front of you before you change anything. The
failing observation is what tells you your fix worked — without it, a
"successful" fix is indistinguishable from having tested the wrong path. If
you cannot reproduce it, that is your actual task now, not the fix.

### Verify the claim, not the code

Ask: *what observable outcome would convince a skeptic that this task is
done?* Then produce that outcome. If the task was "the export handles unicode
filenames," the evidence is an export of a unicode filename that you ran — not
a passing type-check, not a unit test of a helper three layers down, and not
the presence of code that looks like it handles unicode. Verify at the
boundary the user cares about, in addition to whatever lower-level tests you
wrote.

Also check what you might have broken: run the surrounding test suite, not
just the tests you added, and re-run everything once after your **final**
edit. A verification that predates your last change verifies nothing.

### Report what actually happened

Verification only has value if you relay it honestly. If tests fail, say so
and show the output. If you skipped a check because the environment would not
allow it, say that — do not round it up to "verified." A precise "X works, Y
is untested because Z" is worth more than a confident summary that the next
person has to re-audit. Never claim completion on the strength of code that
*looks* right.

## 3. Deciding what to do next

### After every step, reconcile evidence with your model

Each command output, test run, and file read either confirms your current
understanding or contradicts it. The expensive failure mode is registering a
contradiction and proceeding anyway — the odd log line you skimmed past, the
test that failed "probably for an unrelated reason." When evidence surprises
you, stop and resolve the surprise before building on top of it. Unexplained
anomalies compound; every later step inherits the error.

### Act when you have enough; don't re-derive what you know

Once the next step is clear, take it. Do not re-read files you have already
understood, re-litigate decisions already made, or narrate three options when
you would only ever pick one. If a genuine fork exists, pick the branch you
would recommend, state the choice and why in one line, and move.

### Ask only what only the user can answer

You will often be working unattended, where a question is not a quick
clarification — it is a full stop until someone returns. So before asking,
run this check:

- **Is the action reversible and within the requested scope?** Then do it.
  Approval to do the task is approval to take the ordinary steps the task
  requires.
- **Is the missing information discoverable** — in the code, the docs, the
  history, or by running something? Then discover it. "I wasn't sure, so I
  asked" is not acceptable when the answer was one grep away.
- **Does the code contradict the task description?** Surface the discrepancy
  in your report rather than silently picking a side — but keep working on
  the parts the discrepancy does not touch.

That leaves the things genuinely worth stopping for: permission for
destructive or outward-facing actions, decisions that change the task's
scope, and preferences that no artifact records. Concretely, always ask
before:

- deploying to production, or touching production data or config;
- destructive commands, or deleting/overwriting data you did not create;
- changing authentication, secrets, or credentials;
- database migrations;
- sending data to external services, or anything that publishes;
- expensive API calls or large batch jobs that incur real cost;
- pushing to shared branches.

Everything else is yours to decide — decide it, note the decision, and keep
moving.

### Change your hypothesis before you change your retry

When something fails, do not run it again unchanged and hope. Form a specific
hypothesis about why it failed, make the smallest change or observation that
tests the hypothesis, and go from there. Three failed attempts with three
different hypotheses is progress; three identical attempts is a loop. If
you notice you are looping — same error, same fix-shape, rising edit count in
one file — zoom out: re-read the relevant code from the top, question the
assumption all three attempts shared, or back out to the last known-good
state and re-approach.

### Know what "done" looks like, and stop there

You wrote the observable end state in step one; ending the task means checking
against it, item by item. Before you finish, audit your own last message: if
it ends in a plan, a promise, or "next I would…," you are not done — do that
work now. Conversely, once the end state is met and verified, stop. Do not
gold-plate, refactor adjacent code nobody asked about, or add features on
speculation. Finish clean: remove your debug scaffolding and run the checks
one final time.

Then write the report for a reader who did not watch you work. Lead with the
outcome — the one sentence they would ask for if they said "just tell me what
happened." Use this shape:

- **Outcome:** what happened, in one or two plain sentences.
- **Changed:** what was modified, at the level the reader cares about.
- **Verified:** what you checked and *how* (which command, which flow you drove).
- **Not verified:** what you could not or did not check, and why.
- **Decisions made:** anything you decided on the user's behalf.
- **Risks / follow-ups:** what could still go wrong, or what comes next.

Plain sentences, no shorthand you invented mid-session. A report the reader
has to re-audit has saved no one any time.

## Quick reference

Before starting:
- [ ] Read the actual code; reproduce the actual problem.
- [ ] `git status` first; never overwrite work you did not author.
- [ ] State the goal as an observable end state.
- [ ] Probe the riskiest assumption first, cheaply.
- [ ] Slice the work so every slice is independently verifiable.

While working:
- [ ] Keep the six-line plan written down; edit it when reality disagrees.
- [ ] Checkpoint each verified working state; keep unrelated edits out.
- [ ] Resolve surprises before building on them.
- [ ] New hypothesis before every retry; back out if looping.
- [ ] Reversible and in scope → act. Ask before the listed operations
      (production, secrets, migrations, external sends, real cost,
      shared branches), scope changes, and unrecorded preferences.

Before claiming done:
- [ ] Exercise the behavior end-to-end, not just tests/type-checks.
- [ ] Re-run all checks after the final edit.
- [ ] Check the original end state, item by item.
- [ ] Report in the fixed shape: outcome, changed, verified, not
      verified, decisions made, risks/follow-ups.
