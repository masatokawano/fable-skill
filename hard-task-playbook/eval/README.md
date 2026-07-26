# Evaluation harness (skeleton)

Executable companion to `../docs/design-rationale.md` §6. Running the full
protocol requires model access and a benchmark harness; this directory
provides the pieces that can be fixed in advance — the pre-registration
file, the trace-coding implementation, and the statistical analysis — so
that an independent party fills in only the model-invocation layer.

## Status of each component

| File | Status |
| --- | --- |
| `protocol.yaml` | Complete. Machine-readable pre-registration of predictions, conditions, endpoints, and analysis parameters. Freeze (commit) before data collection. |
| `analyze.py` | **Implemented and self-tested.** Exact McNemar, paired bootstrap CI, Holm–Bonferroni. Run `python3 analyze.py --self-test`. |
| `rubric.py` | Partially implemented. Mechanical codes (GT, EV, FR, SL, LP, RV, DG) are computed from tool-call logs; judgment codes (RA, RP, NH, AQ, RS, OS, ES) emit `NEEDS_CODER` rows for the human/LLM coding pass. Run `python3 rubric.py --self-test`. |
| `run_condition.py` | Skeleton. Prepares a workspace with/without the skill and invokes Claude Code headless; the SWE-bench task setup and grading integration are marked `TODO`. |
| `templates/coding_sheet.csv` | Column template for human coders (Appendix A codes). |

## Workflow (protocol §6)

1. **Freeze the protocol.** Review `protocol.yaml`, set the reference-model
   ID, commit. Optionally register the commit hash externally (e.g. OSF).
2. **Run conditions.** For each condition × task × run:
   `python3 run_condition.py --condition C2 --task <id> --run 1`
   → writes `results/<condition>/<task>/<run>/transcript.jsonl` and
   `outcome.json` (resolved: true/false from the benchmark's tests).
   Effort is read from `protocol.yaml` and held fixed across conditions;
   for the pre-registered sweep (`models.effort_sweep`) pass `--effort
   <level>`, which writes to `results/<condition>@<level>/…` so the sweep
   arms stay separable from the primary comparison. Thinking stays enabled
   at every level — the driver refuses to run otherwise.
3. **Code traces.** `python3 rubric.py results/` → `coded.csv` with
   mechanical codes filled and `NEEDS_CODER` placeholders. Two human coders
   complete a random 20% sample (use `templates/coding_sheet.csv`); report
   Cohen's κ; an LLM judge may complete the rest only if it matches the
   human sample at κ ≥ 0.7 (judge prompt must be published).
4. **Analyze.** Build `resolutions.csv` (task_id, c1, c2 as 0/1
   majority-over-runs) and run
   `python3 analyze.py resolutions.csv --secondary coded.csv`.
5. **Publish** trajectories, labels, harness version, and this directory.

## Interpretation

Map results to the falsification table in `../docs/design-rationale.md`
§6.6 — including the null results. A null P1 is a publishable outcome of
this protocol, not a failure of it.
