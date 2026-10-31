"""Numeric check for docs/failure_atlas_onset_multiplicity_bound_v1.md (exploratory, CPU only).

Part A: evaluates the change-of-measure bound (Theorem 1 of the doc) for the Failure Atlas
family-1 cells and compares it with the analytic label requirement of the started-mixture gates.
Part B: Monte Carlo toy (NOT an atlas run): validity and detection of (i) a started mixture with
a given start spacing and (ii) a context-triggered Kelly bettor, under harmful and neutral off.

Usage: python scripts/check_onset_multiplicity_bound.py [--paths 20000] [--seed 1]
"""

from __future__ import annotations

import argparse
import math

import numpy as np

H = 0.1
Q0 = (1 + H) / 2  # 0.55 boundary-null success probability
Q1 = 0.9
ALPHA = 0.1
STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)  # repository DEFAULT_STAKES (fractions of the bound)


def kl(p: float, q: float) -> float:
    s = 0.0
    if p > 0:
        s += p * math.log(p / q)
    if p < 1:
        s += (1 - p) * math.log((1 - p) / (1 - q))
    return s


def beta(budget: float, r: float) -> float:
    """sup{p >= r : kl(p||r) <= budget} (bisection); 1.0 if the whole range is allowed."""
    if kl(1.0 - 1e-15, r) <= budget:
        return 1.0
    lo, hi = r, 1.0 - 1e-15
    for _ in range(200):
        mid = (lo + hi) / 2
        if kl(mid, r) <= budget:
            lo = mid
        else:
            hi = mid
    return lo


def n_lb(N: int, alpha: float, k_info: float, p_target: float, pre: float = 0.0) -> int | None:
    """Smallest n whose bound allows average detection probability >= p_target.

    m(n) = floor(N / n) disjoint windows of length n (rho = 1). Budget = n*k_info + pre.
    Returns None if even n = N does not allow it (cannot happen for p_target < 1 at n = N, m = 1
    unless the horizon is too short).
    """
    for n in range(1, N + 1):
        m = N // n
        r = min(alpha / m, 1.0 - 1e-12)
        # detection prob P <= alpha + (window-event prob), so P >= p_target needs window prob >= p_target - alpha
        if beta(n * k_info + pre, r) >= p_target - alpha:
            return n
    return None


def expected_lb(N: int, alpha: float, K: float) -> tuple[float, int]:
    """Theorem 2: max over window length n_w of sum_{n<=n_w} (1-alpha-(nK+ln2)/ln(m/alpha))_+ ."""
    best = (0.0, 0)
    for nw in range(1, N + 1):
        m = N // nw
        if m < 1 or m <= alpha:
            continue
        lam = math.log(m / alpha)
        v = sum(max(0.0, 1 - alpha - (n * K + math.log(2)) / lam) for n in range(1, nw + 1))
        if v > best[0]:
            best = (v, nw)
    return best


def part_a() -> None:
    K0 = kl(Q1, Q0)
    print(f"q0={Q0:.3f} q1={Q1} alpha={ALPHA}  KL(q1||q0)={K0:.4f} nats/label")
    print(
        f"KL(q1||0.5)={kl(Q1, 0.5):.4f}  KL(q1||0.1)={kl(Q1, 0.1):.4f}  KL(0.5||q0)={kl(0.5, Q0):.5f}"
        f"  KL(0.1||q0)={kl(0.1, Q0):.4f}"
    )
    print("\nKnown-onset floor (single Q_k, rigorous quantile form), p=0.9:")
    p = 0.9 - ALPHA  # window-event probability needed for detection prob 0.9
    print(
        f"  exact: n >= kl({p:.1f}||alpha)/K0 = {kl(p, ALPHA) / K0:.2f} labels;"
        f" log form (p ln(1/alpha) - ln2)/K0 = {(p * math.log(1 / ALPHA) - math.log(2)) / K0:.2f};"
        f" growth heuristic ln(1/alpha)/K0 = {math.log(1 / ALPHA) / K0:.2f}"
    )
    print(
        "\nTable A: packing bound n_LB (labels after onset) for average detection prob p (neutral-ish off,"
        " reference q0, pre-onset penalty ignored = off exactly at q0):"
    )
    print(
        "  N   starts  stakes  analytic(started, front)  nLB(p=.5)  nLB(p=.9)  ln(N/nLB.9)  ln(#starts)"
    )
    for N in (50, 100, 250):
        step = max(1, N // 32)
        starts = len(range(0, max(1, N), step))
        logs = math.log(1 / ALPHA) + math.log(starts) + math.log(len(STAKES))
        # best-grid-stake growth = analytic g of the ledger (Kelly stake not on grid -> slightly less)
        g = max(Q1 * math.log1p(v * 0.9 / 1.1) + (1 - Q1) * math.log1p(-v) for v in STAKES)
        an = logs / g
        n5 = n_lb(N, ALPHA, K0, 0.5)
        n9 = n_lb(N, ALPHA, K0, 0.9)
        print(
            f"  {N:3d} {starts:6d} {len(STAKES):6d}  {an:22.1f}  {n5:9d} {n9:10d}  "
            f"{math.log(N / n9):10.2f}  {math.log(starts):9.2f}"
        )
    print("\nTheorem 2 expected-count lower bound, averaged over onsets (value, argmax n_w):")
    for N in (50, 100, 250):
        v, nw = expected_lb(N, ALPHA, K0)
        print(f"  N={N}: >= {v:.2f} labels at n_w={nw}")
    print("\nTable B: harmful off (q_off=0.1). Rigorous reference choices for the packing bound:")
    for qref in (0.1, 0.3, Q0):
        print(
            f"  reference q'={qref:.2f}: KL(q1||q')={kl(Q1, qref):.3f}/label,"
            f" pre-onset KL(q_off||q')={kl(0.1, qref):.3f}/label"
        )
    for N in (50, 100, 250):
        n9 = n_lb(N, ALPHA, kl(Q1, 0.1), 0.9)
        print(
            f"  N={N}: with q'=q_off the packing bound is n >= {n9} labels (detection prob .9); the"
            f" single-onset floor is {kl(0.8, ALPHA) / K0:.1f}, so the packing bound adds nothing here."
        )
    print(
        "\nTable C: window-count effect. Rigorous bound on avg window-event prob P(tau in W) beta(n K0; alpha/m(n)), N=50:"
    )
    for n in (5, 10, 15, 20, 26):
        m = 50 // n
        print(
            f"  n={n:2d} m={m:2d}  p_bar <= {beta(n * K0, ALPHA / m):.3f}"
            f"   (with all 50 starts counted as m: {beta(n * K0, ALPHA / 50):.3f})"
        )
    print(
        "\nHeuristic model for start-grid spacing D (labels): E[labels] ~ (ln(1/a)+ln(N/D)+ln5)/g + (D-1)/2"
    )
    g = max(Q1 * math.log1p(v * 0.9 / 1.1) + (1 - Q1) * math.log1p(-v) for v in STAKES)
    for N in (50, 100, 250):
        row = []
        for D in (1, 2, 4, 7, 10, 15, 25):
            if D <= N:
                row.append(
                    (
                        D,
                        (math.log(1 / ALPHA) + math.log(max(1, N // D)) + math.log(5)) / g
                        + (D - 1) / 2,
                    )
                )
        best = min(row, key=lambda t: t[1])
        print(f"  N={N}: " + " ".join(f"D={d}:{v:.1f}" for d, v in row) + f"  -> best D={best[0]}")


def run_gates(paths: int, seed: int, N: int, k: int, q_off: float, spacing: int, trig_r: int):
    rng = np.random.default_rng(seed)
    q = np.where(np.arange(1, N + 1) < k, q_off, Q1)
    X = (rng.random((paths, N)) < q[None, :]).astype(np.int8)
    thr = math.log(1 / ALPHA)

    # started mixture: components (start, stake), equal weights, promote at 1/alpha
    starts = list(range(1, N + 1, spacing))
    logw = np.zeros((paths, len(starts), len(STAKES)))
    lam = np.array(STAKES)
    t_mix = np.full(paths, 10**9)
    for t in range(1, N + 1):
        active = np.array([s <= t for s in starts])[None, :, None]
        x = X[:, t - 1][:, None, None]
        inc = np.where(x == 1, np.log1p(lam * 0.9 / 1.1), np.log1p(-lam))[:, :, :] * np.ones(
            (1, len(starts), 1)
        )
        logw += np.where(active, inc, 0.0)
        # mixture over components that have started (fresh components contribute 1 until start)
        lm = np.logaddexp.reduce(logw.reshape(paths, -1), axis=1) - math.log(
            len(starts) * len(STAKES)
        )
        hit = (lm >= thr) & (t_mix > t)
        t_mix[hit] = t

    # context-triggered Kelly bettor
    lam_t = 0.778
    logW = np.zeros(paths)
    t_trig = np.full(paths, 10**9)
    for t in range(1, N + 1):
        if t > trig_r:
            on = X[:, t - 1 - trig_r : t - 1].all(axis=1)
            x = X[:, t - 1]
            inc = np.where(x == 1, math.log1p(lam_t * 0.9 / 1.1), math.log1p(-lam_t))
            logW += np.where(on, inc, 0.0)
        hit = (logW >= thr) & (t_trig > t)
        t_trig[hit] = t
    return t_mix, t_trig


def part_b(paths: int, seed: int) -> None:
    N = 50
    print(f"\nPart B toy Monte Carlo: N={N} labels, alpha={ALPHA}, paths={paths}")
    print("Validity (iid null at the boundary q0): P(promote by N)")
    for spacing in (1, 7):
        tm, tt = run_gates(paths, seed, N, k=N + 1, q_off=Q0, spacing=spacing, trig_r=3)
        print(
            f"  started spacing {spacing}: {np.mean(tm <= N):.4f}    trigger r=3: {np.mean(tt <= N):.4f}"
        )
    for q_off, name in ((0.1, "harmful q_off=0.1"), (0.5, "neutral q_off=0.5")):
        for k in (41, 21):
            print(
                f"\n{name}, onset k={k} (post-onset labels available: {N - k + 1}); P(promoted within n post-onset labels)"
            )
            ns = [5, 10, 15, 20, 30]
            ns = [n for n in ns if k + n - 1 <= N]
            print(
                "  gate                        "
                + " ".join(f"n={n:<3d}" for n in ns)
                + "  P(false pre-onset)"
            )
            for label, spacing, r in (("started all 50 starts", 1, 3), ("started spacing 7", 7, 3)):
                tm, _ = run_gates(paths, seed + 1, N, k, q_off, spacing, r)
                pre = np.mean(tm < k)
                print(
                    f"  {label:26s} "
                    + " ".join(f"{np.mean(tm <= k + n - 1):.2f} " for n in ns)
                    + f"   {pre:.3f}"
                )
            for r in (2, 3, 4):
                _, tt = run_gates(paths, seed + 2, N, k, q_off, 7, r)
                pre = np.mean(tt < k)
                print(
                    f"  trigger bettor r={r}          "
                    + " ".join(f"{np.mean(tt <= k + n - 1):.2f} " for n in ns)
                    + f"   {pre:.3f}"
                )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    part_a()
    part_b(a.paths, a.seed)
