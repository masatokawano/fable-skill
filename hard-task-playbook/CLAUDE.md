# CLAUDE.md

Guidance for coding agents (Claude Code) working in this repository.

## What this project is

This project packages the **hard-task-playbook** skill: a methodology document
for Opus 4.8 describing how to decompose hard tasks, verify one's own work,
and decide what to do next. There is no application code — the deliverable is
the skill and its documentation.

## Layout

```
hard-task-playbook/
├── CLAUDE.md                                  # this file
├── README.md                                  # human-facing overview
└── .claude/
    ├── settings.json                          # shared Claude Code settings
    └── skills/
        └── hard-task-playbook/
            └── SKILL.md                       # the skill itself
```

The skill lives at `.claude/skills/hard-task-playbook/SKILL.md`, which is the
standard Claude Code project-skill location — Claude Code discovers it
automatically when a session starts in this directory, and it can be invoked
as `/hard-task-playbook`.

## Conventions for editing the skill

- **Frontmatter is load-bearing.** `SKILL.md` must start with YAML frontmatter
  containing `name` and `description`. `name` must match the directory name
  (`hard-task-playbook`). The `description` is what the model uses to decide
  when to load the skill, so keep it a concrete statement of *when to use it*,
  not a slogan.
- **Voice:** second-person imperative, addressed to the model running the
  skill ("Read the files the task touches"), not third-person description.
- **Keep it self-contained.** No links to external URLs or other repo files —
  the skill must make sense when injected into a fresh context on its own.
- **Prose over bullets** for the reasoning; bullets only for genuinely
  enumerable checklists. The Quick reference section at the end is the only
  checklist-dense part and should stay that way.
- **Wrap prose at ~80 columns** to match the existing files.
- Keep the three-part structure (decompose → verify → decide next). New
  material should be folded into one of those sections rather than added as a
  fourth top-level section, unless the methodology itself genuinely grows a
  new phase.

## Verifying changes

There is no build or test suite. Verification for this repo means:

1. Frontmatter parses as YAML and has non-empty `name` and `description`
   (a quick check: `head -20 SKILL.md` and eyeball the `---` fences, or parse
   it with `python3 -c "import yaml,sys; print(yaml.safe_load(sys.stdin.read().split('---')[1]))" < SKILL.md`).
2. `name` in frontmatter still equals the skill directory name.
3. The Markdown renders sanely (headings nest, code fences are closed).
4. Re-read the changed section aloud from the perspective of a model
   mid-task: is every instruction actionable without extra context?

## Git

- Do not commit editor droppings or scratch files; use the session scratchpad
  for temporary work.
- Commit messages: one line summarizing the *methodological* change (e.g.
  "Tighten retry guidance in decide-next section"), not the mechanical edit.
