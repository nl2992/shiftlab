"""Phase 11 (PROTOCOL.md Addendum J): P8 mSPRT (one-sided mixture SPRT, always-valid A/B test) on the 44-chain T16/32 panel and the Phase 8 replay.

Statistic on queried labels (k wins, j losses), uniform mixing prior on theta in [1/2, 1]:
    Lambda(k, j) = 2 * int_{1/2}^{1} (2 theta)^k (2 (1 - theta))^j d theta   (exact rational; Lambda(0, 0) = 1)
Nonnegative supermartingale under every adaptive null P(Y_t = 1 | history) <= 1/2 (each integrand factor has conditional mean <= 1 for theta >= 1/2).
Query rule = P2's: query every disagreement round until the budget is spent; decisions only while labels arrive (t <= B + 1).
  P8   textbook: promote iff Lambda >= 1/alpha (no calibration).
  P8c  calibrated: promote iff Lambda > tau (randomised on the tie), exact worst-case adaptive risk <= alpha; cheapest feasible
       member of the calibration path (smallest feasible level as in calibrate_threshold_causal, plus every higher level at its
       largest feasible tie probability), exact cost, ties to the smallest level.

Subcommands (all resume-safe):
  panel     44 chains x T in {16,32} x B in {2,3,4} x alpha in {0.05,0.1} -> results/phase11_msprt_panel.jsonl
  unit      Lambda quadrature / supermartingale checks and the exact risk check on every panel row -> results/phase11_msprt_unit.json
  validate  Monte Carlo check of the P8 / P8c executors on 3 replay datasets -> results/phase11_msprt_validation.json
  replay    P7 (recomputed), P8, P8c, never on the Phase 8 windows -> results/phase11_msprt_replay.jsonl
  summary   results/phase11_msprt_summary.md
Usage: PYTHONPATH=src OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/paper4_continuation/rbdp/real_data/run_phase11_msprt.py STAGE [--workers=6] [--chains=N]
"""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_phase8 as p8  # noqa: E402  (also puts iid_failure and src on sys.path)
from iidlib import EPS, Chain, calibrate_threshold, cost, risks  # noqa: E402
from run_phase9 import calibrate_threshold_causal, windows_of, census_ok  # noqa: E402
from runner import get_post  # noqa: E402

RES = p8.RES
PANEL, REPLAY, VALID = RES / "phase11_msprt_panel.jsonl", RES / "phase11_msprt_replay.jsonl", RES / "phase11_msprt_validation.json"
UNIT, LOG, SUMMARY = RES / "phase11_msprt_unit.json", RES / "phase11_msprt_run.log", RES / "phase11_msprt_summary.md"
SEED, ALPHA, T_R, B_R = p8.SEED, p8.ALPHA, p8.T_R, p8.B_R
P7_SETTINGS = [RES / "phase7_baselines_T16_32/settings.jsonl", RES / "phase10_baselines/settings.jsonl", RES / "phase10c_baselines/settings.jsonl"]
CHAIN_FILES = [RES / "phase7_baselines_T16_32/extra_chains.json", RES / "phase10_baselines/extra_chains.json", RES / "phase10c_baselines/extra_chains.json"]
TOL = 1e-12


def log(*a):
    s = time.strftime("%m-%d %H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, "a") as f:
        f.write(s + "\n")


# ---------------------------------------------------------------- statistic
_LAM = {}


def lam_exact(k, j):
    """Exact Lambda(k, j) = 2^(k+j+1) * int_{1/2}^1 theta^k (1-theta)^j dtheta as a Fraction."""
    if (k, j) not in _LAM:
        tot = Fraction(0)
        for i in range(j + 1):
            e = k + i + 1
            tot += math.comb(j, i) * (-1) ** i * (1 - Fraction(1, 2 ** e)) / e
        _LAM[(k, j)] = 2 ** (k + j + 1) * tot
    return _LAM[(k, j)]


def lam(k, j):
    return float(lam_exact(k, j))


class P8Msprt:
    """mSPRT policy: P2's query rule (every round until budget spent, decisions while t <= B + 1), statistic Lambda(k, j).
    Promote iff Lambda > tau + EPS; w.p. theta iff |Lambda - tau| <= EPS."""
    name = "P8_msprt"
    s0 = 0

    def __init__(self, ch, tau, theta):
        self.ch, self.tau, self.theta = ch, tau, theta

    def act(self, t, n, s):
        B = self.ch.B
        if t > B + 1:
            return 0.0, 0.0
        z = lam(s, (B - n) - s)
        kap = 1.0 if n > 0 else 0.0
        if z > self.tau + EPS:
            return 1.0, kap
        if abs(z - self.tau) <= EPS:
            return self.theta, kap
        return 0.0, kap

    def step(self, s, t, n, ev):
        return s + (1 if ev == 1 else 0)

    def param(self):
        return {"tau_lambda": self.tau, "theta": self.theta}


def levels(ch):
    return sorted({round(lam(k, j), 10) for m in range(ch.B + 1) for k in range(m + 1) for j in [m - k]})


def textbook(ch, alpha):
    """Promote iff Lambda >= 1/alpha (tau just below 1/alpha; no Lambda value lies within 1e-6 of it, asserted)."""
    thr = 1.0 / alpha
    assert all(abs(v - thr) > 1e-6 for v in levels(ch)), "Lambda level too close to 1/alpha"
    return P8Msprt(ch, thr - 1e-6, 0.0)


def _theta_max(make, i, lv, ch, alpha, rs):
    if rs(i, 1.0) <= alpha + 1e-15:
        return 1.0
    a, b = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (a + b)
        if rs(i, mid) <= alpha:
            a = mid
        else:
            b = mid
    return a


def calibrate_p8c(ch, alpha, post):
    """Standard causal calibration (smallest feasible level, tie-randomised to alpha) and, for every higher level, the largest
    feasible tie probability; return the cheapest candidate (ties to the standard one). Returns (policy, info)."""
    make = lambda tau, th: P8Msprt(ch, tau, th)  # noqa: E731
    std = calibrate_threshold_causal(make, levels(ch), ch, alpha)
    lv = levels(ch)
    rs = lambda i, th: risks(make(lv[i], th), ch)[1]  # noqa: E731
    i_std = lv.index(round(std.tau, 10))
    cands = [(cost(std, ch, post), i_std, std)]
    for i in range(i_std + 1, len(lv)):
        th = _theta_max(make, i, lv, ch, alpha, rs)
        p = make(lv[i], th)
        if risks(p, ch)[1] <= alpha + TOL:
            cands.append((cost(p, ch, post), i, p))
    best = min(cands, key=lambda c: (c[0] > cands[0][0] - 1e-12 and 1 or 0, c[0]))
    return best[2], dict(cost_standard=cands[0][0], n_candidates=len(cands), chosen_is_standard=best[2] is std)


# ---------------------------------------------------------------- panel
def load_p7rows():
    out = {}
    for f in P7_SETTINGS:
        for line in open(f):
            r = json.loads(line)
            if "policy" in r and r["policy"].startswith("P7"):
                out[(r["chain_id"], r["alpha"], r["B"], r["T"])] = r
    return out


def evaluate(ch, alpha, post):
    out = {}
    tb = textbook(ch, alpha)
    ri, rc = risks(tb, ch)
    out["P8"] = dict(cost=cost(tb, ch, post), risk_causal=rc, risk_iid=ri, calib=tb.param(), max_lambda=max(levels(ch)),
                     reaches_threshold=bool(max(levels(ch)) >= 1.0 / alpha))
    pol, info = calibrate_p8c(ch, alpha, post)
    ri, rc = risks(pol, ch)
    out["P8c"] = dict(cost=cost(pol, ch, post), risk_causal=rc, risk_iid=ri, calib={**pol.param(), **info})
    return out


def panel_one(task):
    chain, T, B, alpha = task
    sp = chain["solver_params"]
    t0 = time.perf_counter()
    ch = Chain(sp["t01"], sp["t10"], sp["e0"], sp["e1"], sp["prior1"], T, B)
    new = evaluate(ch, alpha, get_post(ch))
    return dict(chain_id=chain["id"], T=T, B=B, alpha=alpha, new=new, wall_s=time.perf_counter() - t0)


def all_chains():
    chains = []
    for f in CHAIN_FILES:
        chains += json.load(open(f))
    return chains


def run_panel(workers, nchains=None):
    p7 = load_p7rows()
    chains = all_chains()
    if nchains:
        chains = chains[:nchains]
    done = {(r["chain_id"], r["alpha"], r["B"], r["T"]) for r in map(json.loads, open(PANEL))} if PANEL.exists() else set()
    tasks = [(c, T, B, a) for c in chains for T in (16, 32) for B in (2, 3, 4) for a in (0.05, 0.1) if (c["id"], a, B, T) not in done]
    tasks.sort(key=lambda t: -(t[1] * 10 + t[2]))
    log("panel:", len(tasks), "settings to do;", len(chains), "chains")
    with mp.Pool(workers) as pool, open(PANEL, "a") as fh:
        for n, res in enumerate(pool.imap_unordered(panel_one, tasks), 1):
            r7 = p7[(res["chain_id"], res["alpha"], res["B"], res["T"])]
            rec = dict(setting_id=r7["setting_id"], chain_id=res["chain_id"], T=res["T"], B=res["B"], alpha=res["alpha"], C0=r7["C0"],
                       p7_cost=r7["cost"], p7_risk_causal=r7["risk_causal"], variants=res["new"], wall_s=res["wall_s"])
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            log("panel", n, "/", len(tasks), rec["setting_id"], "P8c-P7 %.3e" % (res["new"]["P8c"]["cost"] - r7["cost"]),
                "P8c risk %.6f" % res["new"]["P8c"]["risk_causal"], "%.1fs" % res["wall_s"])


# ---------------------------------------------------------------- unit checks
def run_unit():
    import itertools
    from scipy import integrate

    out = {}
    err = 0.0
    for k, j in itertools.product(range(6), range(6)):
        q, _ = integrate.quad(lambda th: 2 * (2 * th) ** k * (2 * (1 - th)) ** j, 0.5, 1.0, epsabs=1e-13, epsrel=1e-13)
        err = max(err, abs(q - lam(k, j)))
    out["lambda_quadrature_max_abs_err"] = err
    # supermartingale: E[Lambda(k+Y, j+1-Y)] <= Lambda(k, j) for any p <= 1/2 (affine in p, so check p = 0 and p = 1/2)
    worst = -1e9
    for k, j in itertools.product(range(6), range(6)):
        for p in (0.0, 0.25, 0.5):
            worst = max(worst, p * lam(k + 1, j) + (1 - p) * lam(k, j + 1) - lam(k, j))
    out["supermartingale_max_excess"] = worst
    out["lambda_1_0_B1_to_4"] = {B: float(lam_exact(B, 0)) for B in range(1, 5)}
    rows = [json.loads(line) for line in open(PANEL)]
    out["panel_rows"] = len(rows)
    out["p8c_max_risk_causal_minus_alpha"] = max(r["variants"]["P8c"]["risk_causal"] - r["alpha"] for r in rows)
    out["p8c_violations_at_1e-12"] = sum(r["variants"]["P8c"]["risk_causal"] > r["alpha"] + TOL for r in rows)
    out["passed"] = bool(err < 1e-10 and worst <= 1e-12 and out["p8c_violations_at_1e-12"] == 0 and len(rows) == 528)
    json.dump(out, open(UNIT, "w"), indent=1)
    log("unit:", out)
    assert out["passed"], out


# ---------------------------------------------------------------- executors (Phase 8 Setup restricted to P7 + new policies)
class Setup11(p8.Setup):
    def __init__(self, sp, T=T_R, B=B_R, alpha=ALPHA, c=p8.C_Q, k=p8.K_SW):
        from iidlib import Post
        from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, _Evaluator, _Solver

        self.ch = ch = Chain(sp["t01"], sp["t10"], sp["e0"], sp["e1"], sp["prior1"], T, B, c, k)
        self.alpha, self.T, self.B, self.c, self.k = alpha, T, B, c, k
        self.post = Post(ch)
        self.C0 = ch.C0()
        self.pols, self.exact, self.sol = {}, {}, {}
        sys.setrecursionlimit(max(20000, sys.getrecursionlimit()))
        cfg = RBDPConfig(T=T, B=B, t01=ch.t01, t10=ch.t10, e0=ch.e0, e1=ch.e1, prior1=ch.prior1, c=c, k=k, alpha=alpha,
                         n_beta=201, mode="causal", lattice_exact=True, compute_lower=False)
        s = _Solver(cfg)
        s._build_post()
        s._run_dp(lower=False, keep=True)
        evl = _Evaluator(s)
        lo, _ = s.root_indices()
        cst, rc, ri = evl.pre(1, B, lo, float(s.beta1))
        self.sol["P7"] = (s, evl, lo)
        self.exact["P7"] = dict(cost=cst, risk_causal=rc, risk_iid=ri)
        self.exact["never"] = dict(cost=self.C0, risk_causal=0.0, risk_iid=0.0)
        self._pc, self._pm = {}, {}
        for nm, pol in (("P8", textbook(ch, alpha)), ("P8c", calibrate_p8c(ch, alpha, self.post)[0])):
            ri, rc = risks(pol, ch)
            self.pols[nm] = pol
            self.exact[nm] = dict(cost=cost(pol, ch, self.post), risk_causal=rc, risk_iid=ri)

    def run(self, nm, xs, seed):
        if nm in ("P8", "P8c"):
            return self.run_baseline(self.pols[nm], [int(v) for v in xs], np.random.default_rng(seed))
        return super().run(nm, xs, seed)


NAMES = ["P7", "P8", "P8c", "never"]


def run_validate(n_ds=3, n_sim=20000):
    ok = census_ok()
    ok.sort(key=lambda r: -r["n_fit_rounds"])
    out = []
    for r in ok[:n_ds]:
        t0 = time.perf_counter()
        S = Setup11(r["solver_params"])
        W = p8.simulate_windows(S.ch.__dict__, S.T, n_sim, SEED)
        row = {"id": r["id"], "n_sim": n_sim, "policies": {}}
        for nm in ("P8", "P8c"):
            res = np.array([S.run(nm, W[i], SEED + 1 + i)[0] for i in range(n_sim)])
            m, se = float(res.mean()), float(res.std(ddof=1) / math.sqrt(n_sim))
            ex = S.exact[nm]["cost"]
            row["policies"][nm] = dict(mc_mean=m, se=se, exact=ex, z=(m - ex) / se if se > 0 else 0.0,
                                       within_3se=bool(abs(m - ex) <= 3 * se + 1e-9))
            log("validate", r["id"], nm, "mc %.5f se %.5f exact %.5f z %.2f" % (m, se, ex, row["policies"][nm]["z"]))
        row["wall_s"] = time.perf_counter() - t0
        out.append(row)
    passed = all(p["within_3se"] for row in out for p in row["policies"].values())
    json.dump({"passed": passed, "datasets": out}, open(VALID, "w"), indent=1)
    log("validation passed:", passed)


# ---------------------------------------------------------------- replay
def replay_one(rec):
    windows = windows_of(rec["id"])
    out = {"id": rec["id"], "n_replay_rounds": rec["n_replay_rounds"], "n_windows": len(windows)}
    if not windows:
        out["status"] = "no full window"
        return out
    S = Setup11(rec["solver_params"])
    out["exact"] = S.exact
    cst = {nm: [] for nm in NAMES}
    prom = {nm: [] for nm in NAMES}
    for w, xs in enumerate(windows):
        for nm in NAMES:
            c_, pr = S.run(nm, xs, SEED + w)
            cst[nm].append(c_)
            prom[nm].append(bool(pr))
    out.update(status="replayed", cost=cst, promoted=prom)
    return out


def run_replay(workers):
    done = {json.loads(line)["id"] for line in open(REPLAY)} if REPLAY.exists() else set()
    ids = {json.loads(line)["id"] for line in open(p8.REPLAY)}
    todo = [r for r in census_ok() if r["id"] in ids and r["id"] not in done]
    log("replay:", len(todo), "datasets to do")
    with mp.Pool(workers) as pool, open(REPLAY, "a") as fh:
        for rec in pool.imap_unordered(replay_one, todo):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            log("replay", rec["id"], rec["status"], "windows", rec["n_windows"])


# ---------------------------------------------------------------- summary
def run_summary():
    P = [json.loads(line) for line in open(PANEL)]
    L = ["# Phase 11 summary (PROTOCOL.md Addendum J): P8 mSPRT", ""]
    L += [f"## (1) Safety (exact worst-case adaptive risk)", "",
          f"settings: {len(P)} ({len({r['chain_id'] for r in P})} chains). Violation = risk_causal > alpha (1e-9 slack in the table; 1e-12 for the unit check).", "",
          "| variant | violations at 1e-9 | violations at 1e-12 | max risk_causal / alpha | max risk_iid / alpha |", "|---|---|---|---|---|"]
    for v in ("P8", "P8c"):
        rc = np.array([r["variants"][v]["risk_causal"] / r["alpha"] for r in P])
        ri = np.array([r["variants"][v]["risk_iid"] / r["alpha"] for r in P])
        L.append(f"| {v} | {sum(r['variants'][v]['risk_causal'] > r['alpha'] + 1e-9 for r in P)} | "
                 f"{sum(r['variants'][v]['risk_causal'] > r['alpha'] + TOL for r in P)} | {rc.max():.6f} | {ri.max():.6f} |")
    L += ["", "## (2) Panel cost versus P7 (RB-DP)", "",
          "Delta = P8c cost - P7 cost; tie = |Delta| <= 1e-9 (absolute, as in tally_phase10_baselines.py); 'P7 cheaper' = Delta > 1e-9.", ""]
    for v in ("P8c", "P8"):
        d = np.array([r["variants"][v]["cost"] - r["p7_cost"] for r in P])
        L.append(f"- {v}: P7 cheaper in {int((d > 1e-9).sum())}, tied in {int((np.abs(d) <= 1e-9).sum())}, dearer in {int((d < -1e-9).sum())} of {len(P)}; "
                 f"max Delta {d.max():.4f}, min Delta {d.min():.3e}.")
    L += ["", "Share of P7's value of information (C0 - cost) / (C0 - P7 cost), over settings with C0 - P7 cost > 1e-9:", "",
          "| variant | n | median | q25 | q75 | min | max |", "|---|---|---|---|---|---|---|"]
    for v in ("P8c", "P8"):
        s = np.array([(r["C0"] - r["variants"][v]["cost"]) / (r["C0"] - r["p7_cost"]) for r in P if r["C0"] - r["p7_cost"] > 1e-9])
        L.append(f"| {v} | {len(s)} | {np.median(s):.4f} | {np.percentile(s, 25):.4f} | {np.percentile(s, 75):.4f} | {s.min():.4f} | {s.max():.4f} |")
    nonstd = sum(not r["variants"]["P8c"]["calib"]["chosen_is_standard"] for r in P)
    gain = [r["variants"]["P8c"]["calib"]["cost_standard"] - r["variants"]["P8c"]["cost"] for r in P]
    L += ["", f"P8c: cheapest path member differs from the standard smallest-feasible-level calibration in {nonstd} settings (max cost reduction {max(gain):.3e}).",
          "", "Per-chain (12 settings each): counts of P7 cheaper / tie / dearer vs P8c, median VOI share of P8c.", "",
          "| chain | cheaper | tie | dearer | VOI P8c |", "|---|---|---|---|---|"]
    for cid in sorted({r["chain_id"] for r in P}):
        R = [r for r in P if r["chain_id"] == cid]
        dd = np.array([r["variants"]["P8c"]["cost"] - r["p7_cost"] for r in R])
        s = [(r["C0"] - r["variants"]["P8c"]["cost"]) / (r["C0"] - r["p7_cost"]) for r in R if r["C0"] - r["p7_cost"] > 1e-9]
        L.append(f"| {cid} | {(dd > 1e-9).sum()} | {(np.abs(dd) <= 1e-9).sum()} | {(dd < -1e-9).sum()} | {np.median(s) if s else float('nan'):.3f} |")
    # ---- replay
    rep = [json.loads(line) for line in open(REPLAY)] if REPLAY.exists() else []
    rp = [r for r in rep if r["status"] == "replayed"]
    L += ["", "## (3) Replay (held-out windows; T = 32, B = 4, alpha = 0.1, c = 0.01, k = 0)", "",
          f"datasets: {len(rp)}; windows: {sum(r['n_windows'] for r in rp)}", ""]
    if rp:
        M = np.concatenate([np.array([r["cost"][nm] for nm in NAMES]).T for r in rp])
        Pm = np.concatenate([np.array([r["promoted"][nm] for nm in NAMES]).T for r in rp]).astype(float)
        j7 = NAMES.index("P7")
        mean_ci = p8.boot_ci(M, lambda m: m.mean(axis=0))
        diff_ci = p8.boot_ci(M, lambda m: (m[:, j7][:, None] - m).mean(axis=0))
        L += ["Pooled over windows (window bootstrap, 2000 resamples, seed 20261119). Difference is P7 - X (negative = P7 cheaper):", "",
              "| policy | mean realised cost [95% CI] | P7 - X [95% CI] | promotion rate |", "|---|---|---|---|"]
        for i, nm in enumerate(NAMES):
            dtxt = "-" if nm == "P7" else "%.4f [%.4f, %.4f]" % ((M[:, j7] - M[:, i]).mean(), diff_ci[0, i], diff_ci[1, i])
            L.append(f"| {nm} | {M[:, i].mean():.4f} [{mean_ci[0, i]:.4f}, {mean_ci[1, i]:.4f}] | {dtxt} | {Pm[:, i].mean():.3f} |")
        j8 = NAMES.index("P8c")
        below = ties = above = 0
        for r in rp:
            dlt = np.mean(r["cost"]["P8c"]) - np.mean(r["cost"]["P7"])
            below += dlt > 1e-9
            ties += abs(dlt) <= 1e-9
            above += dlt < -1e-9
        L += ["", f"Datasets where P7's mean realised cost is below P8c: {below} of {len(rp)}; tied (|diff| <= 1e-9): {ties}; P7 above P8c: {above}.",
              f"Exact in-model causal risk / alpha of P8c over datasets: mean {np.mean([r['exact']['P8c']['risk_causal'] for r in rp]) / ALPHA:.3f}, "
              f"max {np.max([r['exact']['P8c']['risk_causal'] for r in rp]) / ALPHA:.3f}."]
    # ---- textbook
    L += ["", "## (4) Does textbook P8 ever promote?", "",
          f"Maximum Lambda reachable (all B labels wins) = (2^(B+1) - 1)/(B+1): B=2: {lam(2, 0):.4f}, B=3: {lam(3, 0):.4f}, B=4: {lam(4, 0):.4f}; "
          f"1/alpha = 10 (alpha = 0.1) and 20 (alpha = 0.05).",
          f"Settings where max Lambda >= 1/alpha: {sum(r['variants']['P8']['reaches_threshold'] for r in P)} of {len(P)}. "
          f"Settings with P8 causal risk > 0: {sum(r['variants']['P8']['risk_causal'] > 0 for r in P)}."]
    never_c = sum(abs(r["variants"]["P8"]["cost"] - (r["C0"] + r["B"] * 0.01)) <= 1e-9 for r in P)
    L.append(f"P8 cost equals C0 + B*c (queries all B labels, never promotes) in {never_c} of {len(P)} settings.")
    if rp:
        L.append(f"Replay (T = 32, B = 4, alpha = 0.1): textbook P8 exact cost mean over datasets {np.mean([r['exact']['P8']['cost'] for r in rp]):.4f}, "
                 f"max exact causal risk {np.max([r['exact']['P8']['risk_causal'] for r in rp]):.3g}; realised promotion rate {Pm[:, NAMES.index('P8')].mean():.3f}.")
    open(SUMMARY, "w").write("\n".join(L) + "\n")
    log("summary written")


if __name__ == "__main__":
    RES.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[1]
    w = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--workers=")), 6))
    nc = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--chains=")), None)
    {"panel": lambda: run_panel(w, nc), "unit": run_unit, "validate": run_validate, "replay": lambda: run_replay(w),
     "summary": run_summary}[stage]()
