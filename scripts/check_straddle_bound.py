"""Numeric checks for docs/failure_atlas_straddle_theory_v1.md (read-only; imports from src).

Part A (deterministic): stylised straddle schedule under the proposition's model (clear after tau
released labels; pending cap P; pace cap burst + floor(2 B t / T); keepalive K after clear).
Compares measured t*, wasted labels W and labels saved against the closed forms and against the
uniform calendar, and prints the break-even delay d*.

Part B (Monte Carlo): validity of the queried-and-released-label started-mixture e-process under the
boundary null with straddle-type predictable queries and delay d, plus two deliberate violations
(outcome reacts to the query; query peeks at the current outcome). Development-grade, not confirmatory.

Run: PYTHONPATH=src python scripts/check_straddle_bound.py [--reps N]
"""

from __future__ import annotations

import argparse
import math
import sys

import numpy as np

from shiftlab.dive.eprocess import VectorizedStartedMixtureEProcess

T, B, P, BURST_FRAC, KEEP_MULT = 1000, 50, 2, 0.1, 4.0


def uniform_times(d: int) -> list[int]:
    last = T - d
    return sorted({max(1, math.ceil(j * last / B)) for j in range(1, B + 1)})


def straddle_schedule(d: int, tau: int):
    """Deterministic stylised straddle: returns (t_clear, W, used_total, issue_rounds)."""
    burst = max(1, math.ceil(BURST_FRAC * B))
    keepalive = max(d + 1, math.ceil(KEEP_MULT * T / B))
    pending: list[int] = []  # issue rounds
    issued: list[int] = []
    released = 0
    clear_at = None
    W = None
    last_q = 0
    for t in range(1, T + 1):
        while pending and pending[0] + d <= t:  # release first
            pending.pop(0)
            released += 1
            if released == tau and clear_at is None:
                clear_at = t
                W = len(pending)  # in flight at the moment the call becomes clear
        used = len(issued)
        undecided = clear_at is None
        keep = t - last_q >= keepalive
        cap = burst + math.floor(2 * B * t / T)
        if (undecided or keep) and used < cap and len(pending) < P and used < B and t + d <= T:
            pending.append(t)
            issued.append(t)
            last_q = t
    return clear_at, W, len(issued), issued


def part_a() -> None:
    print(f"== Part A: deterministic stylised schedule (T={T}, B={B}, P={P}) ==")
    print(
        f"break-even delay d* = P*T/(B+P) (latency channel, pending-limited vs uniform) = {P * T / (B + P):.1f}"
    )
    print(f"pace-cap rate 2B/T = {2 * B / T:.3f}, uniform rate (T-d)^-1 B ~ {B / T:.3f}")
    hdr = "tau  d   t*_str  t*_unif  dLat(unif-str)  W  minPd-1  used_str  saved_vs_unif  closed_form_saved"
    print(hdr)
    for tau in (5, 10, 20):
        for d in (1, 10, 25, 38, 50):
            tc, W, used, _ = straddle_schedule(d, tau)
            uni = uniform_times(d)
            t_unif = uni[tau - 1] + d  # tau-th uniform label released
            if tc is None:
                print(f"{tau:3d} {d:3d}  never clears within horizon")
                continue
            K = max(d + 1, math.ceil(KEEP_MULT * T / B))
            Lh = T - d
            k_alive = (Lh - tc) // K
            closed = B - (tau + W + k_alive)  # uniform spends B; straddle tau + W + keepalives
            saved = len(uni) - used
            assert W <= min(P, d - 1) if d > 1 else W == 0, (tau, d, W)
            print(
                f"{tau:3d} {d:3d}  {tc:6d}  {t_unif:7d}  {t_unif - tc:14d}  {W:2d}  {min(P, d - 1):7d}  {used:8d}  {saved:13d}  {closed:17d}"
            )


def run_null(d: int, rng: np.random.Generator, mode: str, alpha: float = 0.1) -> bool:
    """One run; returns True if the e-process ever crosses 1/alpha. Boundary null E[X]=0, |X|<=1."""
    proc = VectorizedStartedMixtureEProcess(bound=1.0, alpha=alpha, starts=(0, 1, 2, 4, 8, 16, 32))
    burst = max(1, math.ceil(BURST_FRAC * B))
    keepalive = max(d + 1, math.ceil(KEEP_MULT * T / B))
    due: dict[int, list[float]] = {}
    pending = used = last_q = 0
    recent: list[float] = []
    for t in range(1, T + 1):
        for x in due.pop(t, ()):  # released labels, in round order
            pending -= 1
            proc.update(x)
            recent.append(x)
            if proc.alarm:
                return True
        undecided = (
            len(recent) < 3 or float(np.mean(recent[-5:])) < 0.3
        )  # function of released labels only
        keep = t - last_q >= keepalive
        cap = burst + math.floor(2 * B * t / T)
        q = (undecided or keep) and used < min(cap, B) and pending < P and t + d <= T
        if mode == "peek":  # violation: query decision looks at the outcome of round t
            x_peek = 1.0 if rng.random() < 0.5 else -1.0
            q = q and x_peek > 0
            x = x_peek
        else:
            x = 1.0 if rng.random() < 0.5 else -1.0
        if mode == "reactive" and q:  # violation: outcome distribution shifts when queried
            x = 1.0 if rng.random() < 0.7 else -1.0
        if q:
            used += 1
            pending += 1
            last_q = t
            due.setdefault(t + d, []).append(x)
    return False


def part_b(reps: int) -> None:
    print(
        f"\n== Part B: any-crossing rate at alpha=0.1, {reps} reps per cell (SD ~ {math.sqrt(0.09 / reps):.3f} at p=0.1) =="
    )
    for mode, label in (
        ("valid", "predictable q (valid)"),
        ("reactive", "VIOLATION: outcome reacts to query"),
        ("peek", "VIOLATION: q peeks at X_t"),
    ):
        for d in (1, 10, 50):
            rng = np.random.default_rng(
                [mode == "valid", d, 12345, {"valid": 0, "reactive": 1, "peek": 2}[mode]]
            )
            rate = np.mean([run_null(d, rng, mode) for _ in range(reps)])
            print(f"{label:38s} d={d:3d}  crossing rate = {rate:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=1500)
    a = ap.parse_args()
    part_a()
    part_b(a.reps)
    sys.exit(0)
