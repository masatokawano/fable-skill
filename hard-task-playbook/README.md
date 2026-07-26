# hard-task-playbook

A [Claude Code skill](https://code.claude.com/docs/en/skills) for **Opus 5**
that captures a working method for hard, multi-step engineering tasks:

1. **Decompose** — establish ground truth before planning, fix the scope
   along with the goal, attack the riskiest assumption first, and cut the
   work into slices that can each be verified on their own.
2. **Verify** — treat your own diff as a claim rather than evidence, reproduce
   bugs before fixing them, and check the observable outcome the user actually
   cares about, once, after the last edit.
3. **Decide what's next** — reconcile each new piece of evidence with your
   mental model, change your hypothesis before retrying, act on anything
   reversible and in scope rather than stopping to ask, delegate only for
   large independent tracks, and stop when the stated end state is met.

The method is distilled from the working style of a more capable model, so
that Opus 5 can stand in for it when it isn't available — including when
running unattended. It is written to apply to any nontrivial engineering
task, not only the obviously large ones.

It is deliberately **not** a "be more careful" prompt. Opus 5 already
verifies and self-corrects unprompted, and telling it to do so again costs
tokens without buying accuracy
([prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)).
The skill aims that effort instead — at the right evidence, the right
scope, and a report worth trusting — and caps the behaviors that otherwise
grow without bound: scope, subagent delegation, and output length.

## Using the skill

The skill lives at [`.claude/skills/hard-task-playbook/SKILL.md`](.claude/skills/hard-task-playbook/SKILL.md).

- **In this project:** Claude Code picks it up automatically; invoke it with
  `/hard-task-playbook` or let the model load it when a task matches the
  description.
- **In another project:** copy the `.claude/skills/hard-task-playbook/`
  directory into that project's `.claude/skills/`.
- **Globally:** copy it into `~/.claude/skills/`.

## Repository contents

| Path | Purpose |
| --- | --- |
| `.claude/skills/hard-task-playbook/SKILL.md` | The skill document itself |
| `CLAUDE.md` | Instructions for coding agents editing this repo |
| `.claude/settings.json` | Shared Claude Code settings |
| `docs/design-rationale.md` | Paper-style design rationale: purpose, mechanisms, literature grounding, and a falsifiable evaluation protocol |
| `docs/design-rationale.ja.md` | Japanese translation of the rationale (English version is normative) |
| `eval/` | Skeleton harness for the evaluation protocol: pre-registration file, implemented statistics and trace coding, run-driver stub |

## Contributing

Read `CLAUDE.md` first — it defines the voice, structure, and verification
steps for changes to the skill.
