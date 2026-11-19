"""Phase 8 (PROTOCOL.md Addendum H): census of all 114 promotion datasets and held-out replay of P1-P7.

Stages (each resume-safe):
  census    fit on the fit set (multi-episode wrapper around fit.py), evaluator cells (evaluate.py) -> phase8_census.jsonl
  validate  Monte Carlo check of the step-by-step executors against the exact evaluators -> phase8_validation.json
  replay    P1-P7 on non-overlapping T=32 windows of the held-out sequence -> phase8_replay.jsonl
  summary   tables and bootstrap CIs -> phase8_summary.md
Usage: PYTHONPATH=src uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_phase8.py STAGE [--workers 4]

Realised cost of a window (written to the summary as well): per step t with real label x_t (x_t = 1 when the challenger wins the
disagreement round): cost x_t when the incumbent is kept, 1 - x_t when the challenger is in use, + c per label query, + k per
switch (k = 0), exactly the solver's cost model with the real label in place of the predicted probability pos(beta_t) /
1 - pos(beta_t). Queries reveal x_t to the policy before its next decision (delay 1); the policy's belief starts each window at
the stationary-prior belief beta_1 of the fitted model. Promotion cost uses the solver's own post-promotion continuation
(greedy on its J tables), with real labels used for belief updates after queries.
"""

from __future__ import annotations

import json
import math
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/paper4_continuation/rbdp/iid_failure"))
sys.path.insert(0, str(ROOT / "src"))
import evaluate as ev  # noqa: E402  (sets single-thread env vars)
import fit as ft  # noqa: E402

RES = ROOT / "docs/paper4_continuation/rbdp/real_data/results"
PROMO = ROOT / "data/raw/real_chains/promotion"
CENSUS, REPLAY, VALID = RES / "phase8_census.jsonl", RES / "phase8_replay.jsonl", RES / "phase8_validation.json"
LOG, SUMMARY = RES / "phase8_run.log", RES / "phase8_summary.md"
SEED = 20261119
MIN_FIT, MIN_REPLAY = 200, 200
T_R, B_R, ALPHA, C_Q, K_SW = 32, 4, 0.1, 0.01, 0.0
FIT_CAP_S = 100.0


def log(*a):
    s = time.strftime("%m-%d %H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, "a") as f:
        f.write(s + "\n")


# ---------------------------------------------------------------- data
def dataset_list():
    order = [("atlas_v2_losses", n) for n in "airlines bank criteo elec2 openml_ldpa rialto spam uci_occupancy weather".split()]
    order += [("sprint_fresh_losses", n) for n in "appliances beijing_pm25 bike_hour household_power metro".split()]
    order += [("screen100_losses", p.stem) for p in sorted((PROMO / "screen100_losses").glob("*.npz"))]
    return [(f"{d.replace('_losses', '')}/{n}", d, n) for d, n in order]


def episodes_of(d, n):
    z = np.load(PROMO / d / f"{n}.npz")
    l0, l1 = np.atleast_2d(z["l0"]), np.atleast_2d(z["l1"])
    return [((a == 1) & (b == 0))[a != b].astype(int) for a, b in zip(l0, l1)]


def split_episodes(eps):
    """Fit set: first ceil(E/2) episodes (single episode: first half of its rounds); replay set: the rest."""
    if len(eps) == 1:
        h = len(eps[0]) // 2
        return [eps[0][:h]], [eps[0][h:]]
    h = math.ceil(len(eps) / 2)
    return eps[:h], eps[h:]


# ---------------------------------------------------------------- multi-episode fit (thin wrapper over fit.py)
def fit_multi(eps, seed=ft.SEED, n_restarts=ft.N_RESTARTS, deadline=None):
    """fit.py's EM / polish / ordering, with the likelihood summed over episodes and the chain restarted at each episode
    (fit.py's forward pass and E-step are used per episode, unchanged)."""
    from scipy.optimize import minimize

    eps = [np.asarray(e, int) for e in eps if len(e)]
    ll_of = lambda p: float(sum(ft.forward(e, *p)[0] for e in eps))  # noqa: E731

    def em(p0, max_iter=1500, tol=1e-9):
        p, prev = ft._clip(p0), -np.inf
        for _ in range(max_iter):
            tot, xi, g, gx = 0.0, np.zeros((2, 2)), np.zeros(2), np.zeros(2)
            for e in eps:
                ll, gamma, xi_e = ft._estep(e, p)
                tot += ll
                xi += xi_e
                g += gamma.sum(axis=0)
                gx += (gamma * e[:, None]).sum(axis=0)
            t01 = xi[0, 1] / max(xi[0].sum(), 1e-300)
            t10 = xi[1, 0] / max(xi[1].sum(), 1e-300)
            p = ft._clip((t01, t10, gx[0] / max(g[0], 1e-300), gx[1] / max(g[1], 1e-300)))
            if abs(tot - prev) < tol or (deadline is not None and time.perf_counter() > deadline):
                break
            prev = tot
        return p, ll_of(p)

    rng = np.random.default_rng(seed)
    best, capped, done = None, False, 0
    for _ in range(n_restarts):
        if deadline is not None and done and time.perf_counter() > deadline:
            capped = True
            break
        p0 = (rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.5), rng.uniform(0.5, 0.95))
        p, ll = em(p0)
        done += 1
        if best is None or ll > best[1]:
            best = (p, ll)
    p_em, ll_em = best
    r = minimize(lambda q: -ll_of(tuple(q)), np.array(p_em), method="L-BFGS-B", bounds=[(ft.EPS, 1 - ft.EPS)] * 4)
    q = ft._clip(r.x)
    ll_q = ll_of(q)
    p, ll = (q, ll_q) if ll_q > ll_em else (p_em, ll_em)
    t01, t10, e0, e1 = ft._order(p)
    return dict(t01=t01, t10=t10, e0=e0, e1=e1, loglik=ll, n=int(sum(len(e) for e in eps)), n_episodes=len(eps),
                stationary1=ft.stationary1(t01, t10), time_cap_hit=capped, n_restarts_done=done)


def pooled_r1(eps):
    a = np.concatenate([e[:-1] for e in eps if len(e) > 1]) if any(len(e) > 1 for e in eps) else np.zeros(0)
    b = np.concatenate([e[1:] for e in eps if len(e) > 1]) if any(len(e) > 1 for e in eps) else np.zeros(0)
    return float(np.corrcoef(a, b)[0, 1]) if len(a) > 2 and a.std() > 0 and b.std() > 0 else None


# ---------------------------------------------------------------- census
def census_one(item):
    cid, d, n = item
    t0 = time.perf_counter()
    eps = episodes_of(d, n)
    fe, re_ = split_episodes(eps)
    nfit, nrep = int(sum(map(len, fe))), int(sum(map(len, re_)))
    rec = {"id": cid, "n_episodes": len(eps), "n_fit_episodes": len(fe), "n_fit_rounds": nfit, "n_replay_rounds": nrep,
           "fit_mean": float(np.concatenate(fe).mean()) if nfit else None, "fit_r1": pooled_r1(fe)}
    if nfit < MIN_FIT:
        rec["status"] = "too few fit rounds"
        return rec
    f = fit_multi(fe, deadline=time.perf_counter() + FIT_CAP_S)
    rec["fit"] = f
    if not (f["e0"] < 0.5 < f["e1"]):
        rec["status"] = "fit not evaluable (emissions do not straddle 1/2)"
        return rec
    sp = ft.solver_params(f)
    rec["solver_params"] = sp
    cells = ev.eval_chain(sp, delay1=True, delay2=False, log=lambda *_: None)
    rec["cells"] = [{k: c.get(k) for k in ("T", "B", "status", "C0", "U_causal", "U_iid", "Gamma", "rho_Gamma",
                                            "risk_causal_of_iid_policy", "risk_causal_of_causal_policy")} for c in cells]
    for c in rec["cells"]:
        if c["status"] == "ok":
            c["VOI"] = c["C0"] - c["U_iid"]
    ok = [c for c in rec["cells"] if c["status"] == "ok"]
    rec["status"] = "evaluated" if ok else "no cell solved"
    rec["wall_s"] = time.perf_counter() - t0
    return rec


def run_census(workers):
    done = {json.loads(line)["id"] for line in open(CENSUS)} if CENSUS.exists() else set()
    todo = [it for it in dataset_list() if it[0] not in done]
    log("census:", len(todo), "datasets to do")
    with mp.Pool(workers) as pool, open(CENSUS, "a") as fh:
        for rec in pool.imap_unordered(census_one, todo):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            best = max((c["rho_Gamma"] for c in rec.get("cells", []) if c["status"] == "ok"), default=None)
            log("census", rec["id"], rec["status"], "n_fit", rec["n_fit_rounds"], "best rho", best)


# ---------------------------------------------------------------- executors
class Setup:
    """Calibrated panel and step-by-step executors for one fitted chain, cell (T, B), alpha, c, k."""

    def __init__(self, sp, T=T_R, B=B_R, alpha=ALPHA, c=C_Q, k=K_SW):
        from iidlib import (Chain, GatePolicy, Post, calibrate_p1, calibrate_p2, calibrate_p3, calibrate_p4, cost, policy6,
                            risks)
        from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, _Evaluator, _Solver

        self.ch = ch = Chain(sp["t01"], sp["t10"], sp["e0"], sp["e1"], sp["prior1"], T, B, c, k)
        self.alpha, self.T, self.B, self.c, self.k = alpha, T, B, c, k
        self.post = Post(ch)
        self.pols, self.exact = {}, {}
        for nm, cal in (("P1", calibrate_p1), ("P2", calibrate_p2), ("P3", calibrate_p3), ("P4", calibrate_p4)):
            pol = cal(ch, alpha)
            ri, rc = risks(pol, ch)
            self.pols[nm] = pol
            self.exact[nm] = dict(cost=cost(pol, ch, self.post), risk_causal=rc, risk_iid=ri)
        g = policy6(ch, self.post, alpha)
        self.gate = GatePolicy(ch, self.post, g["th"])
        self.act6 = g["activation"]
        self.exact["P6"] = dict(cost=g["cost"], risk_causal=g["risk_causal"], risk_iid=g["risk_iid"])
        self.C0 = ch.C0()
        self.sol = {}
        sys.setrecursionlimit(max(20000, sys.getrecursionlimit()))
        for nm, mode in (("P5", "iid"), ("P7", "causal")):
            cfg = RBDPConfig(T=T, B=B, t01=ch.t01, t10=ch.t10, e0=ch.e0, e1=ch.e1, prior1=ch.prior1, c=c, k=k, alpha=alpha,
                             n_beta=201, mode=mode, lattice_exact=True, compute_lower=False)
            s = _Solver(cfg)
            s._build_post()
            s._run_dp(lower=False, keep=True)
            evl = _Evaluator(s)
            lo, _ = s.root_indices()
            cst, rc, ri = evl.pre(1, B, lo, float(s.beta1))
            self.sol[nm] = (s, evl, lo)
            self.exact[nm] = dict(cost=cst, risk_causal=rc, risk_iid=ri)
        self.exact["never"] = dict(cost=self.C0, risk_causal=0.0, risk_iid=0.0)
        self._pc, self._pm = {}, {}

    # ---- shared post-promotion continuation (greedy on the solver's J tables, real labels for beliefs)
    def _post_choice(self, pev, t, a, n, b):
        key = (id(pev), t, a, n, round(b, 12))
        h = self._pc.get(key)
        if h is None:
            from shiftlab.paper4.risk_budget_dp_fast import _Maps

            mp_ = _Maps(pev.s, np.array([b]))
            a2, q = pev._post_choice(t, a, n, mp_)
            h = (a2, q, float(mp_.b0[0]), float(mp_.b1[0]), float(mp_.bn[0]))
            self._pc[key] = h
        return h

    def post_loop(self, pev, t, a, n, b, xs):
        T, c, k = self.T, self.c, self.k
        cst = 0.0
        while t <= T:
            a2, q, b0, b1, bn = self._post_choice(pev, t, a, n, b)
            x = xs[t - 1]
            cst += (x if a2 == 0 else 1 - x) + c * q + k * (a2 != a)
            if t < T:
                if q:
                    n -= 1
                    b = b1 if x else b0
                else:
                    b = bn
            a = a2
            t += 1
        return cst

    def promote(self, pev, t, n, b, xs):
        key = ("p", id(pev), t, n, round(b, 12))
        h = self._pm.get(key)
        if h is None:
            from shiftlab.paper4.risk_budget_dp_fast import _Maps

            mp_ = _Maps(pev.s, np.array([b]))
            _, pq = pev.s._promote_cost(n, mp_, pev.s.J[t + 1])
            h = (int(pq[0]), float(mp_.b0[0]), float(mp_.b1[0]), float(mp_.bn[0]))
            self._pm[key] = h
        q, b0, b1, bn = h
        x = xs[t - 1]
        cst = self.k + (1 - x) + self.c * q
        if t < self.T:
            if q:
                cst += self.post_loop(pev, t + 1, 1, n - 1, b1 if x else b0, xs)
            else:
                cst += self.post_loop(pev, t + 1, 1, n, bn, xs)
        return cst

    # ---- policy executors: return (realised cost, promoted?)
    def run_baseline(self, pol, xs, rng):
        ch, T, c = self.ch, self.T, self.c
        b, n, s, cst = ch.beta1(), ch.B, pol.s0, 0.0
        pev = self.post.ev
        for t in range(1, T + 1):
            pi, kap = pol.act(t, n, s)
            if pi >= 1 or (pi > 0 and rng.random() < pi):
                return cst + self.promote(pev, t, n, b, xs), True
            q = kap >= 1 or (kap > 0 and rng.random() < kap)
            x = xs[t - 1]
            cst += x + (c if q else 0.0)
            _, _, b0, b1, bn = ch.branches(b)
            if q:
                s = pol.step(s, t, n, int(x))
                n -= 1
                b = b1 if x else b0
            else:
                s = pol.step(s, t, n, "n")
                b = bn
        return cst, False

    def run_p6(self, xs, rng):
        if rng.random() >= self.act6:
            return float(np.sum(xs[: self.T])), False
        return self.run_baseline(self.gate, xs, rng)

    def run_solver(self, nm, xs, rng):
        s, evl, lo = self.sol[nm]
        T, c, N = self.T, self.c, s.N
        t, n, b, j, cst = 1, self.B, float(s.beta1), lo, 0.0
        while t <= T:
            dec = evl._decide(t, n, b)
            va, vb = int(dec["pv"][j]), int(dec["nv"][j])
            v = va if va == vb else (vb if rng.random() < (j - va) / (vb - va) else va)
            x = xs[t - 1]
            if v == N and dec["promote_n"]:
                return cst + self.promote(evl, t, n, b, xs), True
            m = dec["mp"]
            if dec["q"] is not None and bool(dec["q"][v]):
                i0 = int(dec["w0"][v])
                i1 = min(N, 2 * v - i0)
                cst += x + c
                n -= 1
                b, j = (float(m.b1[0]), i1) if x else (float(m.b0[0]), i0)
            else:
                cst += x
                b, j = float(m.bn[0]), v
            t += 1
        return cst, False

    def run(self, nm, xs, seed):
        rng = np.random.default_rng(seed)
        xs = [int(v) for v in xs]
        if nm == "never":
            return float(sum(xs[: self.T])), False
        if nm in ("P1", "P2", "P3", "P4"):
            return self.run_baseline(self.pols[nm], xs, rng)
        if nm == "P6":
            return self.run_p6(xs, rng)
        return self.run_solver(nm, xs, rng)


POLS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]


def simulate_windows(sp, T, n, seed):
    rng = np.random.default_rng(seed)
    out = np.zeros((n, T), int)
    for i in range(n):
        s = int(rng.random() < sp["prior1"])
        for t in range(T):
            out[i, t] = int(rng.random() < (sp["e1"] if s else sp["e0"]))
            s = int(rng.random() < ((1 - sp["t10"]) if s else sp["t01"]))
    return out


# ---------------------------------------------------------------- validation
def run_validate(n_ds=3, n_sim=20000):
    cen = [json.loads(line) for line in open(CENSUS)]
    ok = [r for r in cen if r["status"] == "evaluated" and r["n_replay_rounds"] >= MIN_REPLAY]
    ok.sort(key=lambda r: -r["n_fit_rounds"])
    out = []
    for r in ok[:n_ds]:
        t0 = time.perf_counter()
        S = Setup(r["solver_params"])
        W = simulate_windows(S.ch.__dict__, S.T, n_sim, SEED)
        row = {"id": r["id"], "n_sim": n_sim, "policies": {}}
        for nm in POLS:
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
    return passed


# ---------------------------------------------------------------- replay
def replay_one(rec):
    cid = rec["id"]
    d, n = next((dd, nn) for c, dd, nn in dataset_list() if c == cid)
    fe, re_ = split_episodes(episodes_of(d, n))
    windows = []
    for e in re_:
        for i in range(len(e) // T_R):
            windows.append(e[i * T_R:(i + 1) * T_R])
    out = {"id": cid, "n_replay_rounds": rec["n_replay_rounds"], "n_windows": len(windows)}
    if not windows:
        out["status"] = "no full window"
        return out
    S = Setup(rec["solver_params"])
    out["exact"] = S.exact
    cost = {nm: [] for nm in POLS + ["never"]}
    prom = {nm: [] for nm in POLS + ["never"]}
    for w, xs in enumerate(windows):
        for nm in POLS + ["never"]:
            cst, pr = S.run(nm, xs, SEED + w)
            cost[nm].append(cst)
            prom[nm].append(bool(pr))
    out.update(status="replayed", cost=cost, promoted=prom)
    return out


def run_replay(workers):
    if not VALID.exists() or not json.load(open(VALID))["passed"]:
        log("refusing to replay: executor validation missing or failed")
        return
    done = {json.loads(line)["id"] for line in open(REPLAY)} if REPLAY.exists() else set()
    cen = [json.loads(line) for line in open(CENSUS)]
    todo = [r for r in cen if r["status"] == "evaluated" and r["n_replay_rounds"] >= MIN_REPLAY and r["id"] not in done]
    log("replay:", len(todo), "datasets to do")
    with mp.Pool(workers) as pool, open(REPLAY, "a") as fh:
        for rec in pool.imap_unordered(replay_one, todo):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            log("replay", rec["id"], rec["status"], "windows", rec["n_windows"])


# ---------------------------------------------------------------- summary
def boot_ci(mat, stat, n_boot=2000, seed=SEED):
    """mat: [W, K] per-window values; stat: function of the resampled matrix -> value array. Window bootstrap."""
    rng = np.random.default_rng(seed)
    W = mat.shape[0]
    vals = np.array([stat(mat[rng.integers(0, W, W)]) for _ in range(n_boot)])
    return np.percentile(vals, [2.5, 97.5], axis=0)


def q5(a):
    a = np.asarray([v for v in a if v is not None and np.isfinite(v)], float)
    return "n=%d min %.4g | q10 %.4g | q25 %.4g | median %.4g | q75 %.4g | q90 %.4g | max %.4g" % (
        len(a), a.min(), *np.percentile(a, [10, 25, 50, 75, 90]), a.max()) if len(a) else "n=0"


def run_summary():
    cen = [json.loads(line) for line in open(CENSUS)]
    rep = [json.loads(line) for line in open(REPLAY)] if REPLAY.exists() else []
    L = ["# Phase 8 summary (PROTOCOL.md Addendum H)", ""]
    L.append("Realised cost: per step with real label x_t, cost x_t if the incumbent is kept, 1 - x_t if the challenger is in use, "
             "+ c = 0.01 per label query, + k = 0 per switch; the solver's cost model with real labels in place of predicted "
             "probabilities. Windows: T = 32 consecutive disagreement rounds of one replay episode; belief restarts at beta_1 each window.")
    L.append("")
    st = {}
    for r in cen:
        st[r["status"]] = st.get(r["status"], 0) + 1
    L += ["## Census (fit set only)", "", f"datasets: {len(cen)}; by status: {st}", ""]
    ev_ = [r for r in cen if r["status"] == "evaluated"]
    best = []
    for r in ev_:
        ok = [c for c in r["cells"] if c["status"] == "ok"]
        b = max(ok, key=lambda c: c["rho_Gamma"])
        best.append((r["id"], b))
    L.append(f"evaluated datasets: {len(ev_)}; with best-cell rho_Gamma > 1e-3: {sum(b['rho_Gamma'] > 1e-3 for _, b in best)}; "
             f"with best-cell rho_Gamma > 0.05: {sum(b['rho_Gamma'] > 0.05 for _, b in best)}")
    L += ["", "Per-dataset best-rho cell:", "", "- rho_Gamma: " + q5([b["rho_Gamma"] for _, b in best]),
          "- Gamma: " + q5([b["Gamma"] for _, b in best]), "- VOI: " + q5([b["VOI"] for _, b in best]),
          "- IID-policy causal risk: " + q5([b["risk_causal_of_iid_policy"] for _, b in best])]
    for (T, B) in ((32, 4), (32, 3), (16, 4)):
        cs = [c for r in ev_ for c in r["cells"] if c["status"] == "ok" and (c["T"], c["B"]) == (T, B)]
        L += ["", f"Cell T={T}, B={B} ({len(cs)} datasets):", "- rho_Gamma: " + q5([c["rho_Gamma"] for c in cs]),
              "- Gamma: " + q5([c["Gamma"] for c in cs]), "- VOI: " + q5([c["VOI"] for c in cs]),
              "- IID-policy causal risk: " + q5([c["risk_causal_of_iid_policy"] for c in cs]),
              f"- rho_Gamma > 1e-3: {sum(c['rho_Gamma'] > 1e-3 for c in cs)}"]
    cs = [c for r in ev_ for c in r["cells"] if c["status"] == "ok"]
    L += ["", f"All cells pooled ({len(cs)}):", "- rho_Gamma: " + q5([c["rho_Gamma"] for c in cs]),
          f"- rho_Gamma > 1e-3: {sum(c['rho_Gamma'] > 1e-3 for c in cs)}"]
    L += ["", "| dataset | n_fit | fit r1 | t01 t10 e0 e1 | best cell | rho_Gamma | Gamma | VOI | IID-policy risk |", "|" + "---|" * 9]
    for r in ev_:
        ok = [c for c in r["cells"] if c["status"] == "ok"]
        b = max(ok, key=lambda c: c["rho_Gamma"])
        f = r["fit"]
        r1 = r["fit_r1"]
        L.append(f"| {r['id']} | {r['n_fit_rounds']} | {r1:+.3f} | {f['t01']:.2f} {f['t10']:.2f} {f['e0']:.2f} {f['e1']:.2f} | "
                 f"T{b['T']}B{b['B']} | {b['rho_Gamma']:.4f} | {b['Gamma']:.4f} | {b['VOI']:.3f} | {b['risk_causal_of_iid_policy']:.3f} |")
    # ---- replay
    rp = [r for r in rep if r["status"] == "replayed"]
    L += ["", "## Replay (held-out windows)", "", f"datasets replayed: {len(rp)}; windows: {sum(r['n_windows'] for r in rp)}", ""]
    if rp:
        names = POLS + ["never"]
        M = np.concatenate([np.array([r["cost"][nm] for nm in names]).T for r in rp])  # [W, 8]
        Pm = np.concatenate([np.array([r["promoted"][nm] for nm in names]).T for r in rp]).astype(float)
        j7, jn = names.index("P7"), names.index("never")

        def voi_share(m):
            v = m[:, jn][:, None] - m
            return v.mean(axis=0) / v[:, j7].mean() if v[:, j7].mean() != 0 else np.full(m.shape[1], np.nan)

        mean_ci = boot_ci(M, lambda m: m.mean(axis=0))
        share_ci = boot_ci(M, voi_share)
        sh = voi_share(M)
        exa = {nm: float(np.mean([r["exact"][nm]["risk_causal"] for r in rp])) for nm in names}
        L += ["Pooled over all windows (bootstrap over windows, 2000 resamples, seed 20261119):", "",
              "| policy | mean realised cost [95% CI] | realised VOI share vs P7 [95% CI] | promotion rate | causal risk / alpha (mean over datasets, fitted model) |",
              "|---|---|---|---|---|"]
        for i, nm in enumerate(names):
            L.append(f"| {nm} | {M[:, i].mean():.4f} [{mean_ci[0, i]:.4f}, {mean_ci[1, i]:.4f}] | {sh[i]:.3f} [{share_ci[0, i]:.3f}, {share_ci[1, i]:.3f}] | "
                     f"{Pm[:, i].mean():.3f} | {exa[nm] / ALPHA:.3f} |")
        # P7 advantage over best safe baseline (P1, P2, P6) per dataset
        adv = []
        safe = [names.index(p) for p in ("P1", "P2", "P6")]
        for r in rp:
            m = np.array([r["cost"][nm] for nm in names]).T
            means = m.mean(axis=0)
            bs = min(safe, key=lambda i: means[i])
            d = m[:, bs] - m[:, j7]
            lo, hi = boot_ci(d[:, None], lambda x: x.mean(axis=0), 1000)
            adv.append((r["id"], float(means[bs] - means[j7]), names[bs], r["n_windows"], float(lo[0]), float(hi[0])))
        adv.sort(key=lambda a: -a[1])
        L += ["", "Datasets with the largest realised P7 advantage over the best safe baseline (P1/P2/P6; cost difference, positive = P7 cheaper):", "",
              "| dataset | windows | best safe | advantage | 95% CI |", "|---|---|---|---|---|"]
        for a in adv[:10]:
            L.append(f"| {a[0]} | {a[3]} | {a[2]} | {a[1]:.4f} | [{a[4]:.4f}, {a[5]:.4f}] |")
        L += ["", f"P7 cheaper than best safe baseline on {sum(a[1] > 0 for a in adv)} of {len(adv)} datasets; pooled mean advantage "
              f"{np.mean([a[1] for a in adv]):.4f}.", "", "Per-dataset mean realised cost:", "",
              "| dataset | windows | " + " | ".join(names) + " |", "|" + "---|" * (len(names) + 2)]
        for r in rp:
            m = np.array([r["cost"][nm] for nm in names]).T.mean(axis=0)
            L.append(f"| {r['id']} | {r['n_windows']} | " + " | ".join(f"{v:.3f}" for v in m) + " |")
    open(SUMMARY, "w").write("\n".join(L) + "\n")
    log("summary written")


if __name__ == "__main__":
    RES.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[1]
    w = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--workers=")), 4))
    {"census": lambda: run_census(w), "validate": run_validate, "replay": lambda: run_replay(w), "summary": run_summary}[stage]()
