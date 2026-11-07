"""Paper 3 pacing minimax screen: uniform vs truncated uniform vs evidence-gated burst pacing.

Protocol (locked before running): docs/sota_fidelity/pacing_minimax_protocol.md.

    uv run python scripts/sota_fidelity/pacing_minimax.py calibrate --out DIR
    uv run python scripts/sota_fidelity/pacing_minimax.py tune --out DIR
    uv run python scripts/sota_fidelity/pacing_minimax.py test --out DIR
    uv run python scripts/sota_fidelity/pacing_minimax.py analyze --out DIR
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
T, B, DIS, CQ, CS, ALPHA = 2000, 200, 0.2, 0.05, 5.0, 0.05
P0, P1 = 0.4, 0.7
G = DIS * (2 * P1 - 1)  # 0.08
G_DESIGN = 0.08
LAMBDAS = np.arange(1, 11) * 0.05
ONSETS = list(range(0, 2000, 100))
DELAYS = [100, 10]
SEED_CAL, SEED_DEV, SEED_TEST = 2026120813, 2026120811, 2026120812
N_CAL, N_DEV, N_TEST = 200_000, 200, 1000
BURST_GRID = [(r, h) for r in (0.25, 0.5, 0.75) for h in (math.log(2), math.log(5), math.log(10))]
NULL_BOUND = 0.0936


def calibrate_threshold(n_seq: int, seed: int, chunk: int = 50_000) -> float:
    """(1-alpha) quantile of max_{n<=B} R_n under IID D with p=1/2."""
    rng = np.random.default_rng(seed)
    maxes = []
    for i in range(0, n_seq, chunk):
        m = min(chunk, n_seq - i)
        sr = np.zeros((m, len(LAMBDAS)))
        mx = np.zeros(m)
        for _ in range(B):
            d = np.where(rng.random(m) < 0.5, 1.0, -1.0)
            sr = (1.0 + sr) * (1.0 + LAMBDAS[None, :] * d[:, None])
            mx = np.maximum(mx, sr.mean(axis=1))
        maxes.append(mx)
    return float(np.quantile(np.concatenate(maxes), 1 - ALPHA, method="higher"))


def pacer_spec(name: str, delay: int):
    if name == "U":
        return dict(horizon=T, r=1.0, h=math.inf)
    if name == "TU":
        return dict(horizon=int(round(T - (delay + CS / G_DESIGN))), r=1.0, h=math.inf)
    if name.startswith("BURST"):
        r, h = BURST_GRID[int(name.split("_")[1])]
        return dict(horizon=T, r=r, h=h)
    raise KeyError(name)


def simulate(name: str, onset: int, delay: int, n: int, seed_base: int, A: float, p_pre=P0, p_post=P1):
    """Returns per-seed arrays: net cost relative to never switching, requests, promoted, promote time."""
    spec = pacer_spec(name, delay)
    rng = np.random.default_rng([seed_base, onset, delay])  # shared across pacers (paired)
    u_dis, u_sign, u_req = rng.random((n, T)), rng.random((n, T)), rng.random((n, T))
    p = np.where(np.arange(T) < onset, p_pre, p_post)
    dis = u_dis < DIS
    D = np.where(u_sign < p[None, :], 1.0, -1.0)
    req = np.zeros((n, T), bool)
    sr = np.zeros((n, len(LAMBDAS)))
    logR = np.full(n, -np.inf)
    remaining = np.full(n, B)
    dep = np.zeros(n, bool)
    t_prom = np.full(n, -1)
    loss = np.zeros(n)
    for t in range(T):
        if t >= delay:  # release labels requested at t - delay
            rel = req[:, t - delay] & ~dep
            if rel.any():
                d = D[rel, t - delay]
                sr[rel] = (1.0 + sr[rel]) * (1.0 + LAMBDAS[None, :] * d[:, None])
                R = sr[rel].mean(axis=1)
                logR[rel] = np.log(R)
                new = np.zeros(n, bool)
                new[np.flatnonzero(rel)[R >= A]] = True
                dep |= new
                t_prom[new] = t
        loss += np.where(dep & dis[:, t], -D[:, t], 0.0)
        if t < spec["horizon"]:
            base = remaining / (DIS * (spec["horizon"] - t))
            q = np.where(logR >= spec["h"], 1.0, spec["r"] * base)
            q = np.clip(q, 0.0, 1.0)
            ask = dis[:, t] & (u_req[:, t] < q) & (remaining > 0) & ~dep
            req[:, t] = ask
            remaining -= ask
    nreq = B - remaining
    net = loss + CQ * nreq + CS * dep
    return net, nreq, dep, t_prom


def oracle(onset: int) -> float:
    return min(0.0, CS - G * (T - onset))


def run_panel(out: Path, kind: str):
    A = json.loads((out / "calibration.json").read_text())["A"]
    if kind == "dev":
        names, n, base = ["U", "TU"] + [f"BURST_{i}" for i in range(len(BURST_GRID))], N_DEV, SEED_DEV
    else:
        names, n, base = ["U", "TU"] + [f"BURST_{i}" for i in range(len(BURST_GRID))], N_TEST, SEED_TEST
    arrays = {}
    for delay in DELAYS:
        for name in names:
            for onset in ONSETS:
                net, nreq, dep, tp = simulate(name, onset, delay, n, base, A)
                key = f"{name}|{delay}|{onset}"
                arrays[key + "|regret"] = net - oracle(onset)
                arrays[key + "|labels"] = nreq
                arrays[key + "|promoted"] = dep
            # null check: no change, p = 1/2 throughout (least favourable)
            if kind == "test":
                _, _, dep, _ = simulate(name, T, delay, 1000, base + 7, A, p_pre=0.5, p_post=0.5)
                arrays[f"{name}|{delay}|null|promoted"] = dep
            print(kind, delay, name, flush=True)
    np.savez_compressed(out / f"{kind}.npz", **arrays)
    _manifest(out, kind, {"A": A, "n": n, "seed_base": base, "pacers": names})


def _manifest(out, kind, extra):
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                                cwd=ROOT).stdout.strip())
    (out / f"manifest_{kind}.json").write_text(json.dumps({"git_head": sha, "worktree_dirty": dirty, **extra}, indent=1))


def worst(z, name, delay, idx=None):
    m = [z[f"{name}|{delay}|{o}|regret"] if idx is None else z[f"{name}|{delay}|{o}|regret"][idx] for o in ONSETS]
    means = np.array([x.mean() for x in m])
    return float(means.max()), int(ONSETS[int(means.argmax())]), means


def tune(out: Path):
    run_panel(out, "dev")
    z = np.load(out / "dev.npz")
    sel = {}
    for delay in DELAYS:
        scores = {i: worst(z, f"BURST_{i}", delay)[0] for i in range(len(BURST_GRID))}
        best = min(scores, key=scores.get)
        sel[str(delay)] = {"selected": f"BURST_{best}", "r": BURST_GRID[best][0], "h": BURST_GRID[best][1],
                           "dev_worst_case": scores, "dev_U": worst(z, "U", delay)[0],
                           "dev_TU": worst(z, "TU", delay)[0]}
    (out / "selection.json").write_text(json.dumps(sel, indent=1))
    print(json.dumps(sel, indent=1))


def _wilson_hi(k, n, zc=1.96):
    p = k / n
    return float((p + zc * zc / (2 * n) + zc * math.sqrt(p * (1 - p) / n + zc * zc / (4 * n * n))) / (1 + zc * zc / n))


def analyze(out: Path):
    z = np.load(out / "test.npz")
    sel = json.loads((out / "selection.json").read_text())
    rng = np.random.default_rng(SEED_TEST + 99)
    res = {"calibration": json.loads((out / "calibration.json").read_text()), "selection": sel, "cells": {}}
    for delay in DELAYS:
        burst = sel[str(delay)]["selected"]
        cell = {}
        wU, oU, mU = worst(z, "U", delay)
        for name in ["U", "TU", burst] + [f"BURST_{i}" for i in range(len(BURST_GRID)) if f"BURST_{i}" != burst]:
            w, o, means = worst(z, name, delay)
            boots = []
            for _ in range(2000):
                idx = rng.integers(0, N_TEST, N_TEST)
                bu, bp = worst(z, "U", delay, idx)[0], worst(z, name, delay, idx)[0]
                boots.append((bu - bp) / bu)
            nul = z[f"{name}|{delay}|null|promoted"]
            avg = float(np.mean(means))
            miss = {o2: float(1 - z[f"{name}|{delay}|{o2}|promoted"].mean()) for o2 in ONSETS}
            cell[name] = {
                "worst_case_regret": w, "worst_onset": o, "avg_regret": avg,
                "rel_gain_vs_U": (wU - w) / wU, "rel_gain_ci95": [float(np.quantile(boots, .025)), float(np.quantile(boots, .975))],
                "per_onset_mean_regret": dict(zip(map(str, ONSETS), map(float, means))),
                "miss_rate": miss,
                "mean_labels": float(np.mean([z[f"{name}|{delay}|{o2}|labels"].mean() for o2 in ONSETS])),
                "null_promotion_rate": float(nul.mean()), "null_wilson_hi": _wilson_hi(int(nul.sum()), len(nul)),
            }
        res["cells"][str(delay)] = cell
    c = res["cells"]["100"]
    b = sel["100"]["selected"]
    valid = lambda k: c[k]["null_wilson_hi"] <= NULL_BOUND
    clears = lambda k: valid(k) and c[k]["rel_gain_vs_U"] >= 0.10 and c[k]["rel_gain_ci95"][0] > 0
    burst_beats_tu = c[b]["worst_case_regret"] <= 0.9 * c["TU"]["worst_case_regret"]
    if clears(b) and burst_beats_tu:
        verdict = "CONTINUE"
    elif clears("TU") and not clears(b):
        verdict = "STOP (TU-only: record Lemma A as hygiene)"
    elif clears(b):
        verdict = "STOP (BURST clears U but not TU by 10%)"
    else:
        verdict = "STOP"
    res["decision"] = {"cell": 100, "TU_clears": clears("TU"), "BURST_clears_U": clears(b),
                       "BURST_beats_TU_by_10pct": burst_beats_tu, "verdict": verdict}
    res["manifests"] = {k: json.loads((out / f"manifest_{k}.json").read_text()) for k in ("dev", "test")}
    (ROOT / "docs/sota_fidelity/pacing_minimax_results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["decision"], indent=1))
    for d, cell in res["cells"].items():
        for k, v in cell.items():
            print(f"d={d:>3} {k:9s} W={v['worst_case_regret']:6.2f}@{v['worst_onset']:<4d} avg={v['avg_regret']:6.2f} "
                  f"gain={v['rel_gain_vs_U']:+.3f} [{v['rel_gain_ci95'][0]:+.3f},{v['rel_gain_ci95'][1]:+.3f}] "
                  f"labels={v['mean_labels']:.0f} null={v['null_promotion_rate']:.3f}/{v['null_wilson_hi']:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["calibrate", "tune", "test", "analyze"])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.cmd == "calibrate":
        A = calibrate_threshold(N_CAL, SEED_CAL)
        (a.out / "calibration.json").write_text(json.dumps({"A": A, "n_seq": N_CAL, "seed": SEED_CAL}))
        print("A =", A)
    elif a.cmd == "tune":
        tune(a.out)
    elif a.cmd == "test":
        run_panel(a.out, "test")
    else:
        analyze(a.out)


if __name__ == "__main__":
    main()
