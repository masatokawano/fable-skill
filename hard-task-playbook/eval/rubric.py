#!/usr/bin/env python3
"""Trace coding for the hard-task-playbook evaluation (Appendix A rubric).

Codes each trajectory from tool-call logs ONLY — never from the model's
prose self-description (design-rationale.md §5.2, §6.4).

Input: one transcript per run at results/<cond>/<task>/<run>/transcript.jsonl,
where each line is a JSON object. This module consumes tool events in the
normalized form produced by `run_condition.py`:

    {"type": "tool", "name": "Bash"|"Read"|"Edit"|"Write"|...,
     "input": {...}, "output_excerpt": "...", "ts": <float>}

and completion-claim markers:

    {"type": "assistant_final", "ts": <float>}

Mechanical codes implemented here: GT, EV (approximate), FR, SL, LP.
Judgment codes (ES, RA, RP, NH, AQ, OS, RS, FC) are emitted as NEEDS_CODER
for the human/LLM coding pass; FC additionally needs outcome.json.

Adapter note: if the harness transcript format changes, only
`iter_events()` should need updating.
"""
import csv
import json
import pathlib
import sys

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}
READ_TOOLS = {"Read", "Grep", "Glob"}
# Heuristic: a Bash command counts as a verification run if it invokes a
# test runner or executes project code. Extend per project under test.
VERIFY_MARKERS = ("pytest", "python", "npm test", "npm run", "go test",
                  "cargo test", "make test", "make check", "tox")

MECHANICAL = ["GT", "EV", "FR", "SL_cycles", "SL_max_lines", "LP"]
JUDGMENT = ["ES", "RA", "RP", "NH", "AQ_necessary", "AQ_unnecessary",
            "OS", "RS", "FC"]


def iter_events(transcript_path):
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def is_verify(ev):
    if ev.get("name") != "Bash":
        return False
    cmd = (ev.get("input") or {}).get("command", "")
    return any(m in cmd for m in VERIFY_MARKERS)


def code_mechanical(events):
    """Compute GT, EV, FR, SL, LP from a normalized event list."""
    first_edit_i = next((i for i, e in enumerate(events)
                         if e.get("type") == "tool" and e.get("name") in EDIT_TOOLS),
                        None)
    reads_before = any(e.get("type") == "tool" and
                       (e.get("name") in READ_TOOLS or is_verify(e))
                       for e in events[:first_edit_i or 0])
    gt = 1 if (first_edit_i is None or reads_before) else 0

    final_i = next((i for i, e in enumerate(events)
                    if e.get("type") == "assistant_final"), len(events))
    ev_code = 1 if any(is_verify(e) for e in events[:final_i]) else 0

    last_edit_i = max((i for i, e in enumerate(events)
                       if e.get("type") == "tool" and e.get("name") in EDIT_TOOLS),
                      default=None)
    last_verify_i = max((i for i, e in enumerate(events) if is_verify(e)),
                        default=None)
    fr = 1 if (last_edit_i is None or
               (last_verify_i is not None and last_verify_i > last_edit_i)) else 0

    # SL: edit->verify cycles, and max edited lines between verifications.
    cycles, cur_lines, max_lines, dirty = 0, 0, 0, False
    for e in events:
        if e.get("type") != "tool":
            continue
        if e.get("name") in EDIT_TOOLS:
            dirty = True
            text = (e.get("input") or {}).get("new_string") or \
                   (e.get("input") or {}).get("content") or ""
            cur_lines += text.count("\n") + 1
        elif is_verify(e) and dirty:
            cycles += 1
            max_lines = max(max_lines, cur_lines)
            cur_lines, dirty = 0, False

    # LP: >=3 consecutive same-shape retries (same tool, same primary target).
    def shape(e):
        inp = e.get("input") or {}
        return (e.get("name"),
                inp.get("file_path") or (inp.get("command", "")[:40]))
    streak, lp = 1, 0
    tool_events = [e for e in events if e.get("type") == "tool"]
    for prev, cur in zip(tool_events, tool_events[1:]):
        streak = streak + 1 if shape(prev) == shape(cur) else 1
        if streak >= 3:
            lp = 1
    return {"GT": gt, "EV": ev_code, "FR": fr, "SL_cycles": cycles,
            "SL_max_lines": max_lines, "LP": lp}


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: rubric.py <results_dir>  ->  coded.csv")
    root = pathlib.Path(sys.argv[1])
    rows = []
    for t in sorted(root.glob("*/*/*/transcript.jsonl")):
        cond, task, run = t.parts[-4], t.parts[-3], t.parts[-2]
        row = {"condition": cond, "task_id": task, "run": run}
        row.update(code_mechanical(list(iter_events(t))))
        row.update({c: "NEEDS_CODER" for c in JUDGMENT})
        rows.append(row)
    if not rows:
        sys.exit(f"no transcripts under {root}")
    out = pathlib.Path("coded.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "task_id", "run"]
                           + MECHANICAL + JUDGMENT)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out} ({len(rows)} trajectories); "
          f"judgment codes await the coding pass (see eval/README.md step 3)")


if __name__ == "__main__":
    main()
