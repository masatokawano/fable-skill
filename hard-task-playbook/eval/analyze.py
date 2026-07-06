#!/usr/bin/env python3
"""Statistical analysis for the hard-task-playbook evaluation (protocol §6.5).

Implements the pre-registered tests:
  - exact two-sided McNemar test on paired task resolutions (P1)
  - paired bootstrap 95% CI on the resolution-rate difference (P1)
  - behavioral-endpoint comparisons on rubric codes with Holm-Bonferroni
    correction (the rate machinery behind P4/P5), via --secondary

Primary input: a CSV with header `task_id,c1,c2` where c1/c2 are 0/1
task-level resolutions (majority over runs) for conditions C1 (no skill)
and C2 (skill). Secondary input: the coded.csv written by rubric.py.

Usage:
  python3 analyze.py resolutions.csv [--secondary coded.csv]
  python3 analyze.py --self-test
"""
import argparse
import csv
import math
import random
from collections import defaultdict

BOOTSTRAP_ITERS = 10_000
ALPHA = 0.05
SEED = 20260706

# Binary rubric codes compared C2 vs C1, with the direction the skill is
# predicted to move them (design-rationale.md §4): +1 = should rise.
SECONDARY_CODES = {"GT": +1, "EV": +1, "FR": +1, "LP": -1}


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value.

    b = discordant pairs resolved only in C1; c = resolved only in C2.
    Under H0 the discordant pairs are Binomial(b+c, 0.5).
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def _bootstrap_diffs(pairs, iters=BOOTSTRAP_ITERS, seed=SEED):
    """Sorted resampled means of (b - a) over task pairs."""
    rng = random.Random(seed)
    n = len(pairs)
    if n == 0:
        raise ValueError("no pairs")
    diffs = []
    for _ in range(iters):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        diffs.append(sum(b - a for a, b in s) / n)
    diffs.sort()
    return diffs


def _ci_from_diffs(diffs, alpha=ALPHA):
    n = len(diffs)
    lo = diffs[int((alpha / 2) * n)]
    hi = diffs[min(n - 1, int((1 - alpha / 2) * n))]
    return lo, hi


def paired_bootstrap_ci(pairs, iters=BOOTSTRAP_ITERS, alpha=ALPHA, seed=SEED):
    """Percentile CI for mean(b - a) over tasks, resampling tasks."""
    return _ci_from_diffs(_bootstrap_diffs(pairs, iters, seed), alpha)


def bootstrap_p_two_sided(diffs):
    """Approximate two-sided p from resampled diffs (sign test at 0).

    Floored at 2/iters: the resolution limit of the resample count.
    """
    n = len(diffs)
    frac_le = sum(1 for d in diffs if d <= 0) / n
    frac_ge = sum(1 for d in diffs if d >= 0) / n
    return min(1.0, max(2 * min(frac_le, frac_ge), 2 / n))


def holm_bonferroni(pvalues, alpha=ALPHA):
    """Return list of booleans: rejected (significant) per hypothesis."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    rejected = [False] * m
    for rank, i in enumerate(order):
        if pvalues[i] <= alpha / (m - rank):
            rejected[i] = True
        else:
            break
    return rejected


def load_pairs(path):
    with open(path, newline="") as f:
        return [(int(r["c1"]), int(r["c2"])) for r in csv.DictReader(f)]


def analyze(pairs):
    n = len(pairs)
    r1 = sum(c1 for c1, _ in pairs) / n
    r2 = sum(c2 for _, c2 in pairs) / n
    b = sum(1 for c1, c2 in pairs if c1 == 1 and c2 == 0)
    c = sum(1 for c1, c2 in pairs if c1 == 0 and c2 == 1)
    return {
        "n_tasks": n,
        "rate_C1": r1,
        "rate_C2": r2,
        "difference": r2 - r1,
        "discordant_C1_only": b,
        "discordant_C2_only": c,
        "mcnemar_p_two_sided": mcnemar_exact(b, c),
        "bootstrap_95ci": paired_bootstrap_ci(pairs),
    }


def pairs_by_code(rows, cond_a="C1", cond_b="C2"):
    """From coded.csv rows: per rubric code, per-task rate pairs (a, b).

    A task contributes to a code only if it has runs in both conditions
    with a numeric value for that code (NEEDS_CODER rows are skipped).
    """
    out = {}
    for code in SECONDARY_CODES:
        per = defaultdict(lambda: {cond_a: [], cond_b: []})
        for r in rows:
            cond = r.get("condition")
            val = r.get(code, "")
            if cond in (cond_a, cond_b) and val not in ("", "NEEDS_CODER", None):
                per[r["task_id"]][cond].append(int(val))
        pairs = [(sum(d[cond_a]) / len(d[cond_a]), sum(d[cond_b]) / len(d[cond_b]))
                 for d in per.values() if d[cond_a] and d[cond_b]]
        out[code] = pairs
    return out


def analyze_secondary(rows):
    """Rate difference C2-C1 per rubric code, bootstrap CI/p, Holm family."""
    results = {}
    for code, pairs in pairs_by_code(rows).items():
        if not pairs:
            continue
        diffs = _bootstrap_diffs(pairs)
        results[code] = {
            "n_tasks": len(pairs),
            "difference": sum(b - a for a, b in pairs) / len(pairs),
            "bootstrap_95ci": _ci_from_diffs(diffs),
            "p_approx": bootstrap_p_two_sided(diffs),
            "predicted_sign": "+" if SECONDARY_CODES[code] > 0 else "-",
        }
    codes = list(results)
    rejected = holm_bonferroni([results[c]["p_approx"] for c in codes])
    for code, rej in zip(codes, rejected):
        r = results[code]
        r["holm_significant"] = rej
        r["direction_consistent"] = (r["difference"] * SECONDARY_CODES[code]) > 0
    return results


def self_test():
    # McNemar against hand-computed values.
    assert mcnemar_exact(0, 0) == 1.0
    # b=5, c=15: two-sided p = 2 * P(X <= 5), X ~ Bin(20, .5) = 0.041389...
    assert abs(mcnemar_exact(5, 15) - 0.0414) < 5e-4
    assert mcnemar_exact(10, 10) == 1.0
    assert mcnemar_exact(3, 9) == mcnemar_exact(9, 3)  # symmetry

    # Bootstrap: degenerate pairs give a zero-width CI.
    assert paired_bootstrap_ci([(0, 1)] * 50) == (1.0, 1.0)
    assert paired_bootstrap_ci([(1, 1)] * 50) == (0.0, 0.0)
    # A clear effect: CI excludes 0; deterministic under fixed seed.
    pairs = [(0, 1)] * 30 + [(1, 1)] * 40 + [(0, 0)] * 125 + [(1, 0)] * 5
    lo, hi = paired_bootstrap_ci(pairs)
    assert lo > 0, (lo, hi)
    assert paired_bootstrap_ci(pairs) == paired_bootstrap_ci(pairs)

    # Holm-Bonferroni: textbook case.
    # sorted: .005 (α/4 ✓), .01 (α/3 ✓), .03 (α/2 ✗ stop)
    assert holm_bonferroni([0.01, 0.04, 0.03, 0.005]) == \
        [True, False, False, True]
    assert holm_bonferroni([0.5, 0.9]) == [False, False]

    # Primary end-to-end on the synthetic set.
    res = analyze(pairs)
    assert res["n_tasks"] == 200
    assert abs(res["difference"] - 0.125) < 1e-9
    assert res["mcnemar_p_two_sided"] < 0.001

    # Secondary: synthetic coded rows. GT improves strongly in C2, LP drops,
    # FR is null; EV left NEEDS_CODER to check exclusion handling.
    rows = []
    for t in range(40):
        for cond, gt, lp, fr in (("C1", 0, 1, 1), ("C2", 1, 0, 1)):
            rows.append({"condition": cond, "task_id": f"t{t}", "run": "1",
                         "GT": str(gt if t < 36 else 1 - gt), "LP": str(lp),
                         "FR": str(fr), "EV": "NEEDS_CODER"})
    sec = analyze_secondary(rows)
    assert "EV" not in sec                     # NEEDS_CODER rows excluded
    assert sec["GT"]["holm_significant"] and sec["GT"]["direction_consistent"]
    assert sec["LP"]["holm_significant"] and sec["LP"]["direction_consistent"]
    assert sec["LP"]["difference"] == -1.0
    assert not sec["FR"]["holm_significant"]   # null endpoint stays null
    assert abs(sec["FR"]["difference"]) < 1e-9
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("resolutions", nargs="?", help="CSV: task_id,c1,c2")
    ap.add_argument("--secondary", help="coded.csv from rubric.py")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.resolutions:
        ap.error("provide a resolutions CSV or --self-test")

    res = analyze(load_pairs(args.resolutions))
    print("== P1 (primary): resolution rate, C2 vs C1 ==")
    for k, v in res.items():
        print(f"{k}: {v}")
    lo, _ = res["bootstrap_95ci"]
    verdict = ("P1 supported"
               if res["mcnemar_p_two_sided"] < ALPHA and lo > 0
               else "P1 not supported")
    print(f"verdict: {verdict} (alpha={ALPHA}; see design-rationale.md §6.6)")

    if args.secondary:
        with open(args.secondary, newline="") as f:
            sec = analyze_secondary(list(csv.DictReader(f)))
        print("\n== Secondary (behavioral codes, Holm-corrected family) ==")
        for code, r in sec.items():
            print(f"{code}: diff={r['difference']:+.3f} "
                  f"ci95=({r['bootstrap_95ci'][0]:+.3f},"
                  f"{r['bootstrap_95ci'][1]:+.3f}) p~{r['p_approx']:.4f} "
                  f"holm={'*' if r['holm_significant'] else 'ns'} "
                  f"predicted={r['predicted_sign']} "
                  f"consistent={r['direction_consistent']}")


if __name__ == "__main__":
    main()
