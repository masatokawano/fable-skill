# hard-task-playbook

A [Claude Code skill](https://code.claude.com/docs/en/skills) for **Opus 4.8**
that captures a working method for hard, multi-step engineering tasks:

1. **Decompose** — establish ground truth before planning, attack the riskiest
   assumption first, and cut the work into slices that can each be verified on
   their own.
2. **Verify** — treat your own diff as a claim rather than evidence, reproduce
   bugs before fixing them, and check the observable outcome the user actually
   cares about.
3. **Decide what's next** — reconcile each new piece of evidence with your
   mental model, change your hypothesis before retrying, act on anything
   reversible and in scope rather than stopping to ask, and stop when the
   stated end state is met.

The method is distilled from the working style of a more capable model, so
that Opus 4.8 can stand in for it when it isn't available — including when
running unattended. It is written to apply to any nontrivial engineering
task, not only the obviously large ones.

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

## Contributing

Read `CLAUDE.md` first — it defines the voice, structure, and verification
steps for changes to the skill.
