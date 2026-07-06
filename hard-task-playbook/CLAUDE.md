# CLAUDE.md

Guidance for coding agents (Claude Code) working in this repository.

## What this project is

This project packages the **hard-task-playbook** skill: a methodology document
for Opus 4.8 describing how to decompose hard tasks, verify one's own work,
and decide what to do next. There is no application code — the deliverable is
the skill and its documentation.

**Why it exists:** the skill distills the working method of a more capable
model so that Opus 4.8 can stand in for it when it is unavailable — including
running unattended. Preserve that intent when editing: every instruction must
be executable as a procedure, without assuming the judgment the stronger
model would supply. If a rule only works when the reader "knows when it
applies," rewrite it with an explicit trigger or check.

## Layout

```
hard-task-playbook/
├── CLAUDE.md                                  # this file
├── README.md                                  # human-facing overview
├── docs/
│   ├── design-rationale.md                    # paper-style rationale + evaluation protocol (normative)
│   └── design-rationale.ja.md                 # Japanese translation (follows the English version)
├── eval/                                      # evaluation-protocol harness (see eval/README.md)
│   ├── protocol.yaml                          # machine-readable pre-registration
│   ├── analyze.py                             # implemented statistics (has --self-test)
│   ├── rubric.py                              # trace coding: mechanical codes implemented
│   ├── run_condition.py                       # run driver (skeleton; TODOs marked)
│   └── templates/coding_sheet.csv             # human-coder template
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
- **Keep the rationale in sync.** `docs/design-rationale.md` describes the
  skill's structure (§3.2), design principles (§3.3), and per-mechanism
  hypotheses (§4). If you add, remove, or restructure a procedure in
  SKILL.md, update the corresponding rationale sections — and the Appendix A
  rubric if the change affects what should be measured. Do not add citations
  to the rationale unless you have verified they exist.
- **Translation follows English.** `docs/design-rationale.ja.md` is a
  translation; the English file is normative. Edit English first, then
  mirror the change into the translation (references stay English-only).
- **Rubric changes propagate to code.** Appendix A is implemented in
  `eval/rubric.py` and `eval/templates/coding_sheet.csv`; changing a code's
  definition requires updating both, and `eval/protocol.yaml` if endpoints
  change. After touching `eval/*.py`, run `python3 eval/analyze.py
  --self-test` and the synthetic-transcript check described in
  `eval/README.md`.

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
