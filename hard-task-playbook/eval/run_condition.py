#!/usr/bin/env python3
"""Run one task under one condition (protocol §6.3). SKELETON.

What is implemented: condition table, workspace preparation with/without
the skill, headless Claude Code invocation, transcript normalization stub.
What is TODO (requires benchmark + model access, marked inline):
task checkout, grading, and the transcript-format adapter for the harness
version under test.

Usage:
  python3 run_condition.py --condition C2 --task astropy__astropy-12907 --run 1
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL_SRC = HERE.parent / ".claude" / "skills" / "hard-task-playbook"

CONDITIONS = {
    # model ids resolved via protocol.yaml (models.weaker / models.reference)
    "C1": {"model_key": "weaker", "skill": None},
    "C2": {"model_key": "weaker", "skill": "full"},
    "C3": {"model_key": "reference", "skill": None},
    "C4": {"model_key": "reference", "skill": "full"},
    "C5a": {"model_key": "weaker", "skill": "section1_only"},
    "C5b": {"model_key": "weaker", "skill": "section2_only"},
    "C5c": {"model_key": "weaker", "skill": "section3_only"},
    "C5d": {"model_key": "weaker", "skill": "paraphrase"},
}


def load_protocol():
    # Minimal YAML read without a dependency: only the flat keys we need.
    text = (HERE / "protocol.yaml").read_text()
    models = {}
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("weaker:"):
            models["weaker"] = s.split(":", 1)[1].strip()
        elif s.startswith("reference:"):
            models["reference"] = s.split(":", 1)[1].strip()
    return models


def prepare_workspace(task_id: str, skill_variant):
    ws = pathlib.Path(tempfile.mkdtemp(prefix=f"eval-{task_id}-"))
    # TODO(benchmark): check out the SWE-bench task instance's repo at its
    # base commit into `ws` (e.g. via the swebench harness / docker image),
    # and write the issue text to ws/TASK.md as the prompt source.
    skills_dir = ws / ".claude" / "skills" / "hard-task-playbook"
    if skill_variant == "full":
        skills_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SKILL_SRC, skills_dir)
    elif skill_variant is not None:
        # TODO(ablation): materialize section-only / paraphrase variants.
        # Variants must be generated once, committed, and referenced by
        # hash in protocol.yaml before data collection.
        raise NotImplementedError(f"ablation variant {skill_variant}")
    return ws


def run_claude(ws, model, prompt, out_dir):
    """Invoke Claude Code headless; capture the event stream."""
    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--output-format", "stream-json",
        "--permission-mode", "acceptEdits",  # unattended (§6.3)
    ]
    raw = out_dir / "raw_stream.jsonl"
    with open(raw, "w") as f:
        subprocess.run(cmd, cwd=ws, stdout=f, check=True)
    return raw


def normalize_transcript(raw_path, out_path):
    """Adapter: harness stream-json -> the normalized events rubric.py reads.

    TODO(adapter): map the installed Claude Code version's stream-json
    events to {"type": "tool", "name", "input", "ts"} and
    {"type": "assistant_final", "ts"}. Keep ALL raw events on disk; the
    rubric consumes only tool events by design (§6.4).
    """
    raise NotImplementedError("write the adapter for your harness version")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--condition", required=True, choices=CONDITIONS)
    ap.add_argument("--task", required=True)
    ap.add_argument("--run", required=True, type=int)
    args = ap.parse_args()

    spec = CONDITIONS[args.condition]
    models = load_protocol()
    model = models.get(spec["model_key"]) or ""
    if not model or model == "null":
        sys.exit(f"set models.{spec['model_key']} in protocol.yaml first")

    out_dir = HERE / "results" / args.condition / args.task / str(args.run)
    out_dir.mkdir(parents=True, exist_ok=True)
    ws = prepare_workspace(args.task, spec["skill"])
    prompt = (ws / "TASK.md").read_text()  # written by prepare_workspace TODO
    raw = run_claude(ws, model, prompt, out_dir)
    normalize_transcript(raw, out_dir / "transcript.jsonl")

    # TODO(grading): run the benchmark's acceptance tests against `ws` and
    # write {"resolved": bool, "tokens": int, "wall_clock_s": float}.
    (out_dir / "outcome.json").write_text(json.dumps({"resolved": None}))
    print(f"done: {out_dir}")


if __name__ == "__main__":
    main()
