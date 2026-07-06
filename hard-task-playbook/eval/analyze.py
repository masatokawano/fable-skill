#!/usr/bin/env python3
"""Statistical analysis for the hard-task-playbook evaluation (protocol §6.5).

Implements the pre-registered tests:
  - exact two-sided McNemar test on paired task resolutions (P1)
  - paired bootstrap 95% CI on the resolution-rate difference (P1)
  - Holm-Bonferroni correction for the secondary-endpoint family

Input: a CSV with header `task_id,c1,c2` where c1/c2 are 0/1 task-level
resolutions (majority over runs) for conditions C1 (no skill) and C2 (skill).

Usage:
  python3 analyze.py resolutions.csv
  python3 analyze.py --self-test
"""
import argparse
import csv
import math
import random
import sys

BOOTSTRAP_ITERS = 10_000
ALPHA = 0.05


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


def paired_bootstrap_ci(pairs, iters=BOOTSTRAP_ITERS, alpha=ALPHA, seed=20260706):
    """Percentile CI for mean(c2 - c1) over tasks, resampling tasks."""
    rng = random.Random(seed)
    n = len(pairs)
    if n == 0:
        raise ValueError("no pairs")
    diffs = []
    for _ in range(iters):
        s = [pairs[rng.randrange(n)] for _ in range(n)]
        diffs.append(sum(c2 - c1 for c1, c2 in s) / n)
    diffs.sort()
    lo = diffs[int((alpha / 2) * iters)]
    hi = diffs[min(iters - 1, int((1 - alpha / 2) * iters))]
    return lo, hi


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
    pairs = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            pairs.append((int(row["c1"]), int(row["c2"])))
    return pairs


def analyze(pairs):
    n = len(pairs)
    r1 = sum(c1 for c1, _ in pairs) / n
    r2 = sum(c2 for _, c2 in pairs) / n
    b = sum(1 for c1, c2 in pairs if c1 == 1 and c2 == 0)
    c = sum(1 for c1, c2 in pairs if c1 == 0 and c2 == 1)
    p = mcnemar_exact(b, c)
    lo, hi = paired_bootstrap_ci(pairs)
    return {
        "n_tasks": n,
        "rate_C1": r1,
        "rate_C2": r2,
        "difference": r2 - r1,
        "discordant_C1_only": b,
        "discordant_C2_only": c,
        "mcnemar_p_two_sided": p,
        "bootstrap_95ci": (lo, hi),
    }


def self_test():
    # McNemar against hand-computed values.
    assert mcnemar_exact(0, 0) == 1.0
    # b=5, c=15: two-sided p = 2 * P(X <= 5), X ~ Bin(20, .5) = 0.041389...
    p = mcnemar_exact(5, 15)
    assert abs(p - 0.0414) < 5e-4, p
    assert mcnemar_exact(10, 10) == 1.0
    # Symmetry.
    assert mcnemar_exact(3, 9) == mcnemar_exact(9, 3)

    # Bootstrap: all-equal pairs give a zero-width CI at 0.
    lo, hi = paired_bootstrap_ci([(0, 1)] * 50)
    assert lo == hi == 1.0
    lo, hi = paired_bootstrap_ci([(1, 1)] * 50)
    assert lo == hi == 0.0
    # A clear effect: CI excludes 0.
    pairs = [(0, 1)] * 30 + [(1, 1)] * 40 + [(0, 0)] * 125 + [(1, 0)] * 5
    lo, hi = paired_bootstrap_ci(pairs)
    assert lo > 0, (lo, hi)
    # Determinism under fixed seed.
    assert paired_bootstrap_ci(pairs) == paired_bootstrap_ci(pairs)

    # Holm-Bonferroni: textbook case.
    rej = holm_bonferroni([0.01, 0.04, 0.03, 0.005], alpha=0.05)
    # sorted: .005 (α/4=.0125 ✓), .01 (α/3=.0167 ✓), .03 (α/2=.025 ✗ stop)
    assert rej == [True, False, False, True], rej
    assert holm_bonferroni([0.5, 0.9]) == [False, False]

    # End-to-end on the synthetic set.
    res = analyze(pairs)
    assert res["n_tasks"] == 200
    assert abs(res["difference"] - 0.125) < 1e-9
    assert res["mcnemar_p_two_sided"] < 0.001
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("resolutions", nargs="?", help="CSV: task_id,c1,c2")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.resolutions:
        ap.error("provide a resolutions CSV or --self-test")
    res = analyze(load_pairs(args.resolutions))
    for k, v in res.items():
        print(f"{k}: {v}")
    lo, hi = res["bootstrap_95ci"]
    verdict = "P1 supported" if res["mcnemar_p_two_sided"] < ALPHA and lo > 0 else \
              "P1 not supported"
    print(f"verdict: {verdict} (alpha={ALPHA}; see design-rationale.md §6.6)")


if __name__ == "__main__":
    main()
