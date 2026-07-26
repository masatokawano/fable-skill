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

Mechanical codes implemented here: GT, EV (approximate), FR, SL, LP, RV, DG.
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
# Subagent spawns, under the names the harness uses for them.
DELEGATE_TOOLS = {"Agent", "Task"}
# Heuristic: a Bash command counts as a verification run if it invokes a
# test runner or executes project code. Extend per project under test.
VERIFY_MARKERS = ("pytest", "python", "npm test", "npm run", "go test",
                  "cargo test", "make test", "make check", "tox")

MECHANICAL = ["GT", "EV", "FR", "SL_cycles", "SL_max_lines", "LP", "RV", "DG"]
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

    # LP: >=3 consecutive same-shape retries (same tool, same primary
    # target). Only action tools count — repeated reads of one file are a
    # normal pattern, not a retry loop.
    def shape(e):
        inp = e.get("input") or {}
        return (e.get("name"),
                inp.get("file_path") or (inp.get("command", "")[:40]))
    streak, lp = 1, 0
    action_events = [e for e in events if e.get("type") == "tool"
                     and e.get("name") in EDIT_TOOLS | {"Bash"}]
    for prev, cur in zip(action_events, action_events[1:]):
        streak = streak + 1 if shape(prev) == shape(cur) else 1
        if streak >= 3:
            lp = 1

    # RV: redundant verification. A verification run that repeats a command
    # already run since the last edit checks a state nothing has changed.
    rv, seen_since_edit = 0, set()
    for e in events:
        if e.get("type") != "tool":
            continue
        if e.get("name") in EDIT_TOOLS:
            seen_since_edit.clear()
        elif is_verify(e):
            cmd = (e.get("input") or {}).get("command", "")
            if cmd in seen_since_edit:
                rv += 1
            else:
                seen_since_edit.add(cmd)

    # DG: subagent spawns.
    dg = sum(1 for e in events if e.get("type") == "tool"
             and e.get("name") in DELEGATE_TOOLS)

    return {"GT": gt, "EV": ev_code, "FR": fr, "SL_cycles": cycles,
            "SL_max_lines": max_lines, "LP": lp, "RV": rv, "DG": dg}


def self_test():
    def bash(cmd):
        return {"type": "tool", "name": "Bash", "input": {"command": cmd}}

    def edit(path):
        return {"type": "tool", "name": "Edit",
                "input": {"file_path": path, "new_string": "x\ny"}}

    def read(path):
        return {"type": "tool", "name": "Read", "input": {"file_path": path}}

    final = {"type": "assistant_final"}

    # Disciplined trajectory: read -> edit -> test -> claim.
    good = code_mechanical([read("a.py"), edit("a.py"), bash("pytest"), final])
    assert (good["GT"], good["EV"], good["FR"], good["LP"]) == (1, 1, 1, 0), good
    assert good["SL_cycles"] == 1 and good["SL_max_lines"] == 2, good

    # Undisciplined: edit first, no verify, 3 identical Bash retries.
    bad = code_mechanical([edit("b.py"), bash("ls"), bash("ls"), bash("ls"),
                           final])
    assert (bad["GT"], bad["EV"], bad["FR"], bad["LP"]) == (0, 0, 0, 1), bad

    # Repeated reads of one file are NOT a loop; verify-after-claim is not EV.
    r = code_mechanical([read("c.py"), read("c.py"), read("c.py"),
                         edit("c.py"), final, bash("pytest")])
    assert (r["LP"], r["EV"], r["FR"]) == (0, 0, 1), r

    # RV: the second identical test run without an intervening edit is
    # redundant; the same command after an edit is not.
    redundant = code_mechanical([read("f.py"), edit("f.py"), bash("pytest"),
                                 bash("pytest"), bash("pytest"), final])
    assert redundant["RV"] == 2, redundant
    paced = code_mechanical([read("f.py"), edit("f.py"), bash("pytest"),
                             edit("f.py"), bash("pytest"), final])
    assert paced["RV"] == 0, paced

    # DG: subagent spawns are counted, other tools are not.
    delegated = code_mechanical([
        {"type": "tool", "name": "Agent", "input": {"prompt": "investigate"}},
        {"type": "tool", "name": "Task", "input": {"prompt": "verify"}},
        read("g.py"), final])
    assert delegated["DG"] == 2, delegated
    assert code_mechanical([read("g.py"), final])["DG"] == 0

    # Edit-only trajectory: GT=0, FR=0; no-edit trajectory: GT=1, FR=1.
    assert code_mechanical([edit("d.py"), final])["FR"] == 0
    none = code_mechanical([read("e.py"), final])
    assert (none["GT"], none["FR"]) == (1, 1), none
    print("self-test OK")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: rubric.py <results_dir>|--self-test  ->  coded.csv")
    if sys.argv[1] == "--self-test":
        self_test()
        return
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
