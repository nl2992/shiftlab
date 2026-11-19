"""Phase 9 (PROTOCOL.md Addendum I): three causal-safe baselines (P3c, P4c, P5r) on the T16/32 panel and on the Phase 8 replay.

Subcommands (all resume-safe):
  panel     35 chains x T in {16,32} x B in {2,3,4} x alpha in {0.05,0.1} -> results/phase9_panel.jsonl
  validate  Monte Carlo check of the new executors on 3 replay datasets -> results/phase9_validation.json
  check8    recomputed P1-P7 window costs vs results/phase8_replay.jsonl on 3 datasets -> results/phase9_check8.json
  replay    all policies (P1-P7 recomputed + P3c, P4c, P5r) on the Phase 8 windows -> results/phase9_replay.jsonl
  summary   results/phase9_summary.md
Usage: PYTHONPATH=src OPENBLAS_NUM_THREADS=1 uv run --no-sync python scripts/paper4_continuation/rbdp/real_data/run_phase9.py STAGE [--workers=6] [--chains=N]

P5r deflated level: the IID-mode solver (lattice_exact needs a rational alpha) is re-solved on the candidate grid
alpha' in {alpha * p / q : 1 <= p <= q <= 8} (Farey sequence of order 8, 22 points, small denominators keep the exact lattice
N = d * 2^B small); the largest grid point whose solver causal risk is <= alpha + 1e-12 is found by bisection over the sorted grid.
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
from iidlib import P3Filter, P4Voi, _belief_levels, cost, risks  # noqa: E402
from iidlib import Chain  # noqa: E402
from runner import get_post, solver_policy  # noqa: E402

RES = p8.RES
P7DIR = RES / "phase7_baselines_T16_32"
PANEL, REPLAY, VALID = RES / "phase9_panel.jsonl", RES / "phase9_replay.jsonl", RES / "phase9_validation.json"
CHECK8, LOG, SUMMARY = RES / "phase9_check8.json", RES / "phase9_run.log", RES / "phase9_summary.md"
SEED, ALPHA, T_R, B_R = p8.SEED, p8.ALPHA, p8.T_R, p8.B_R
OLD = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
NEW = ["P3c", "P4c", "P5r"]
SAFE = ["P1", "P2", "P6", "P3c", "P4c", "P5r"]
NAMES = {"P1_fixed_sample": "P1", "P2_count_sprt": "P2", "P3_hmm_filter": "P3", "P4_myopic_voi": "P4",
         "P5_iid_optimal_pomdp": "P5", "P6_eprocess_gate": "P6", "P7_rbdp_causal": "P7"}
TOL_RISK = 1e-12


def log(*a):
    s = time.strftime("%m-%d %H:%M:%S ") + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, "a") as f:
        f.write(s + "\n")


# ---------------------------------------------------------------- calibration on the exact causal risk
def calibrate_threshold_causal(make, levels, ch, alpha, n_theta=200):
    """calibrate_threshold of iidlib with the exact causal risk (risks(...)[1]) in place of the IID risk."""
    lv = list(levels)
    rs = lambda i, th: risks(make(lv[i], th), ch)[1]  # noqa: E731
    lo, hi = 0, len(lv) - 1  # causal risk at the top level is 0 <= alpha
    if rs(lo, 0.0) <= alpha + 1e-15:
        hi = lo
    else:
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if rs(mid, 0.0) <= alpha + 1e-15:
                hi = mid
            else:
                lo = mid
    i = hi
    r0 = rs(i, 0.0)
    if abs(r0 - alpha) < 1e-13 or r0 > alpha:
        return make(lv[i], 0.0)
    a, b = 0.0, 1.0
    for _ in range(n_theta):
        mid = 0.5 * (a + b)
        if rs(i, mid) <= alpha:
            a = mid
        else:
            b = mid
    return make(lv[i], a)


def calibrate_p3c(ch, alpha):
    return calibrate_threshold_causal(lambda tau, th: P3Filter(ch, tau, th), _belief_levels(P3Filter, ch), ch, alpha)


def calibrate_p4c(ch, alpha):
    return calibrate_threshold_causal(lambda tau, th: P4Voi(ch, tau, th), _belief_levels(P4Voi, ch), ch, alpha)


# ---------------------------------------------------------------- P5r
def farey_grid(alpha, order=8):
    a = Fraction(alpha).limit_denominator(100000)
    pts = sorted({Fraction(p, q) for q in range(1, order + 1) for p in range(1, q + 1)})
    return [(float(a * f), float(f)) for f in pts]


def p5r_plan(ch, alpha):
    """Cheaper of (a) deflated IID-mode solve and (b) mixing with never-promote; exact in-model values from the solver."""
    C0 = ch.C0()
    cache = {}

    def S(al):
        if al not in cache:
            cache[al] = solver_policy(ch, al, "iid")
        return cache[al]

    s5 = S(alpha)
    rc5, ri5, u5 = s5["risk_causal"], s5["risk_iid"], s5["U"]
    a = min(1.0, alpha / rc5) if rc5 > 0 else 1.0
    mix = dict(cost=a * u5 + (1 - a) * C0, risk_causal=a * rc5, risk_iid=a * ri5, a=a)
    grid = [g for g, _ in farey_grid(alpha)]
    grid[-1] = alpha
    feas = lambda s: s["risk_causal"] <= alpha + TOL_RISK  # noqa: E731
    if feas(s5):
        ap, sd, nsolve = alpha, s5, 1
    else:  # bisection over sorted grid for the largest feasible alpha' (risk is nondecreasing in alpha')
        lo, hi, nsolve = -1, len(grid) - 1, 1  # grid[hi] infeasible, grid[lo] (virtual) feasible
        sd = None
        while hi - lo > 1:
            mid = (lo + hi) // 2
            s = S(grid[mid])
            nsolve += 1
            if feas(s):
                lo, sd = mid, s
            else:
                hi = mid
        ap = grid[lo] if lo >= 0 else 0.0
    if sd is None:  # no alpha' > 0 on the grid is safe: deflation degenerates to never promoting
        defl = dict(cost=C0, risk_causal=0.0, risk_iid=0.0)
    else:
        defl = dict(cost=sd["U"], risk_causal=sd["risk_causal"], risk_iid=sd["risk_iid"])
    choice = "deflated" if defl["cost"] <= mix["cost"] else "mixing"
    ch_ = defl if choice == "deflated" else mix
    return dict(choice=choice, alpha_prime=ap, a=a, cost=ch_["cost"], risk_causal=ch_["risk_causal"], risk_iid=ch_["risk_iid"],
                cost_deflated=defl["cost"], cost_mixing=mix["cost"], risk_causal_p5=rc5, n_solves=nsolve)


# ---------------------------------------------------------------- panel
def load_p7rows():
    out = {}
    for line in open(P7DIR / "settings.jsonl"):
        r = json.loads(line)
        if "policy" not in r:
            continue
        out.setdefault((r["chain_id"], r["alpha"], r["B"], r["T"]), {})[NAMES[r["policy"]]] = r
    return out


def panel_one(task):
    chain, T, B, alpha = task
    sp = chain["solver_params"]
    t0 = time.perf_counter()
    ch = Chain(sp["t01"], sp["t10"], sp["e0"], sp["e1"], sp["prior1"], T, B)
    post = get_post(ch)
    new = {}
    for nm, cal in (("P3c", calibrate_p3c), ("P4c", calibrate_p4c)):
        pol = cal(ch, alpha)
        ri, rc = risks(pol, ch)
        new[nm] = dict(cost=cost(pol, ch, post), risk_causal=rc, risk_iid=ri, calib=pol.param())
    pl = p5r_plan(ch, alpha)
    new["P5r"] = dict(cost=pl["cost"], risk_causal=pl["risk_causal"], risk_iid=pl["risk_iid"],
                      calib={k: pl[k] for k in ("choice", "alpha_prime", "a", "cost_deflated", "cost_mixing", "risk_causal_p5", "n_solves")})
    return dict(chain_id=chain["id"], T=T, B=B, alpha=alpha, new=new, wall_s=time.perf_counter() - t0)


def run_panel(workers, nchains=None):
    old = load_p7rows()
    chains = json.load(open(P7DIR / "extra_chains.json"))
    if nchains:
        chains = chains[:nchains]
    done = {(r["chain_id"], r["alpha"], r["B"], r["T"]) for r in map(json.loads, open(PANEL))} if PANEL.exists() else set()
    tasks = [(c, T, B, a) for c in chains for T in (16, 32) for B in (2, 3, 4) for a in (0.05, 0.1)
             if (c["id"], a, B, T) not in done]
    tasks.sort(key=lambda t: -(t[1] * 10 + t[2]))  # longest cells first
    log("panel:", len(tasks), "settings to do")
    with mp.Pool(workers) as pool, open(PANEL, "a") as fh:
        for n, res in enumerate(pool.imap_unordered(panel_one, tasks), 1):
            key = (res["chain_id"], res["alpha"], res["B"], res["T"])
            rows = old[key]
            pol = {nm: dict(cost=rows[nm]["cost"], risk_causal=rows[nm]["risk_causal"], risk_iid=rows[nm]["risk_iid"]) for nm in OLD}
            pol.update(res["new"])
            C0 = rows["P7"]["C0"]
            best = min(SAFE, key=lambda nm: pol[nm]["cost"])
            rec = dict(setting_id=rows["P7"]["setting_id"], chain_id=res["chain_id"], T=res["T"], B=res["B"], alpha=res["alpha"],
                       C0=C0, policies=pol, best_safe=pol[best]["cost"], best_safe_policy=best,
                       p7_cost=pol["P7"]["cost"], delta=pol[best]["cost"] - pol["P7"]["cost"], wall_s=res["wall_s"])
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            log("panel", n, "/", len(tasks), rec["setting_id"], "delta %.3e" % rec["delta"], "best", best,
                "P5r", res["new"]["P5r"]["calib"]["choice"], "%.0fs" % res["wall_s"])


# ---------------------------------------------------------------- executors (Phase 8 Setup + the three new policies)
class Setup9(p8.Setup):
    def __init__(self, sp, T=T_R, B=B_R, alpha=ALPHA, c=p8.C_Q, k=p8.K_SW):
        from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, _Evaluator, _Solver

        super().__init__(sp, T, B, alpha, c, k)
        ch = self.ch
        for nm, cal in (("P3c", calibrate_p3c), ("P4c", calibrate_p4c)):
            pol = cal(ch, alpha)
            ri, rc = risks(pol, ch)
            self.pols[nm] = pol
            self.exact[nm] = dict(cost=cost(pol, ch, self.post), risk_causal=rc, risk_iid=ri)
        pl = p5r_plan(ch, alpha)
        self.p5r = pl
        self.exact["P5r"] = dict(cost=pl["cost"], risk_causal=pl["risk_causal"], risk_iid=pl["risk_iid"], **{
            k_: pl[k_] for k_ in ("choice", "alpha_prime", "a")})
        if pl["choice"] == "deflated" and pl["alpha_prime"] > 0:
            if pl["alpha_prime"] == alpha:
                self.sol["P5d"] = self.sol["P5"]
            else:
                cfg = RBDPConfig(T=T, B=B, t01=ch.t01, t10=ch.t10, e0=ch.e0, e1=ch.e1, prior1=ch.prior1, c=c, k=k,
                                 alpha=pl["alpha_prime"], n_beta=201, mode="iid", lattice_exact=True, compute_lower=False)
                s = _Solver(cfg)
                s._build_post()
                s._run_dp(lower=False, keep=True)
                evl = _Evaluator(s)
                lo, _ = s.root_indices()
                cst, rc, ri = evl.pre(1, B, lo, float(s.beta1))
                self.sol["P5d"] = (s, evl, lo)
                self.exact["P5r"]["pre_cost"], self.exact["P5r"]["pre_risk_causal"] = cst, rc

    def run(self, nm, xs, seed):
        if nm in ("P3c", "P4c"):
            rng = np.random.default_rng(seed)
            return self.run_baseline(self.pols[nm], [int(v) for v in xs], rng)
        if nm == "P5r":
            rng = np.random.default_rng(seed)
            xs = [int(v) for v in xs]
            pl = self.p5r
            if pl["choice"] == "mixing":
                if rng.random() >= pl["a"]:
                    return float(sum(xs[: self.T])), False
                return self.run_solver("P5", xs, rng)
            if pl["alpha_prime"] <= 0:
                return float(sum(xs[: self.T])), False
            return self.run_solver("P5d", xs, rng)
        return super().run(nm, xs, seed)


ALL = OLD + NEW


def census_ok():
    cen = [json.loads(line) for line in open(p8.CENSUS)]
    return [r for r in cen if r["status"] == "evaluated" and r["n_replay_rounds"] >= p8.MIN_REPLAY]


def windows_of(cid):
    d, n = next((dd, nn) for c, dd, nn in p8.dataset_list() if c == cid)
    _, re_ = p8.split_episodes(p8.episodes_of(d, n))
    return [e[i * T_R:(i + 1) * T_R] for e in re_ for i in range(len(e) // T_R)]


def run_validate(n_ds=3, n_sim=20000):
    ok = census_ok()
    ok.sort(key=lambda r: -r["n_fit_rounds"])
    out = []
    for r in ok[:n_ds]:
        t0 = time.perf_counter()
        S = Setup9(r["solver_params"])
        W = p8.simulate_windows(S.ch.__dict__, S.T, n_sim, SEED)
        row = {"id": r["id"], "n_sim": n_sim, "p5r_choice": S.p5r["choice"], "alpha_prime": S.p5r["alpha_prime"], "policies": {}}
        for nm in NEW:
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
    cid = rec["id"]
    windows = windows_of(cid)
    out = {"id": cid, "n_replay_rounds": rec["n_replay_rounds"], "n_windows": len(windows)}
    if not windows:
        out["status"] = "no full window"
        return out
    S = Setup9(rec["solver_params"])
    out["exact"] = S.exact
    names = ALL + ["never"]
    cst = {nm: [] for nm in names}
    prom = {nm: [] for nm in names}
    for w, xs in enumerate(windows):
        for nm in names:
            c_, pr = S.run(nm, xs, SEED + w)
            cst[nm].append(c_)
            prom[nm].append(bool(pr))
    out.update(status="replayed", cost=cst, promoted=prom)
    return out


def run_check8(n_ds=3):
    old = {json.loads(l)["id"]: json.loads(l) for l in open(p8.REPLAY)}
    ok = [r for r in census_ok() if r["id"] in old and old[r["id"]]["status"] == "replayed"]
    ok.sort(key=lambda r: r["n_windows"] if "n_windows" in r else old[r["id"]]["n_windows"])
    res = []
    for r in ok[:n_ds]:  # the three smallest datasets (fewest windows)
        new = replay_one(r)
        o = old[r["id"]]
        eq = {nm: bool(new["cost"][nm] == o["cost"][nm] and new["promoted"][nm] == o["promoted"][nm]) for nm in OLD + ["never"]}
        maxdiff = {nm: float(np.max(np.abs(np.array(new["cost"][nm]) - np.array(o["cost"][nm])))) for nm in OLD + ["never"]}
        res.append(dict(id=r["id"], n_windows=new["n_windows"], exactly_equal=eq, max_abs_diff=maxdiff))
        log("check8", r["id"], "windows", new["n_windows"], "all equal:", all(eq.values()), "max diff", max(maxdiff.values()))
    json.dump({"all_equal": all(all(x["exactly_equal"].values()) for x in res), "datasets": res}, open(CHECK8, "w"), indent=1)


def run_replay(workers):
    done = {json.loads(line)["id"] for line in open(REPLAY)} if REPLAY.exists() else set()
    ids = {json.loads(line)["id"] for line in open(p8.REPLAY)}
    todo = [r for r in census_ok() if r["id"] in ids and r["id"] not in done]
    todo.sort(key=lambda r: -1)  # file order
    log("replay:", len(todo), "datasets to do")
    with mp.Pool(workers) as pool, open(REPLAY, "a") as fh:
        for rec in pool.imap_unordered(replay_one, todo):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            log("replay", rec["id"], rec["status"], "windows", rec["n_windows"])


# ---------------------------------------------------------------- summary
def run_summary():
    L = ["# Phase 9 summary (PROTOCOL.md Addendum I)", ""]
    P = [json.loads(line) for line in open(PANEL)]
    L += ["## (i) T16/32 panel (exact, in-model)", "",
          f"settings: {len(P)} ({len({r['chain_id'] for r in P})} chains). Delta = (cheapest of P1, P2, P6, P3c, P4c, P5r) - P7 cost; "
          "tie = |Delta| <= 1e-9; 'P7 cheaper' = Delta > 1e-9. P5r deflation uses the Farey-grid bisection described in the script header.", ""]
    d = np.array([r["delta"] for r in P])
    L.append(f"P7 cheaper than best safe baseline: {int((d > 1e-9).sum())}; tie: {int((np.abs(d) <= 1e-9).sum())}; "
             f"P7 dearer: {int((d < -1e-9).sum())}.")
    dn = d[d < -1e-9]
    if len(dn):
        L.append(f"Dearer cases: min Delta {dn.min():.3e} (in-model optimality violated beyond 1e-9).")
    L += ["", "Sanity: P7 cost <= new safe baseline cost + 1e-6 (in-model optimality):"]
    for nm in NEW + ["P1", "P2", "P6"]:
        bad = [(r["setting_id"], r["policies"]["P7"]["cost"] - r["policies"][nm]["cost"]) for r in P
               if r["policies"]["P7"]["cost"] > r["policies"][nm]["cost"] + 1e-6]
        L.append(f"- {nm}: {len(bad)} violations" + (" e.g. " + "; ".join(f"{s} ({x:.2e})" for s, x in bad[:5]) if bad else ""))
    L += ["", "Causal-risk violations (risk_causal > alpha + 1e-9):", "", "| policy | violations |", "|---|---|"]
    for nm in OLD + NEW:
        L.append(f"| {nm} | {sum(r['policies'][nm]['risk_causal'] > r['alpha'] + 1e-9 for r in P)} |")
    L += ["", "VOI share (C0 - cost) / (C0 - P7 cost), over settings with C0 - P7 cost > 1e-9:", "", "| policy | n | median | q25 | q75 | min |",
          "|---|---|---|---|---|---|"]
    for nm in NEW + ["P1", "P2", "P6"]:
        v = np.array([(r["C0"] - r["policies"][nm]["cost"]) / (r["C0"] - r["p7_cost"]) for r in P if r["C0"] - r["p7_cost"] > 1e-9])
        L.append(f"| {nm} | {len(v)} | {np.median(v):.4f} | {np.percentile(v, 25):.4f} | {np.percentile(v, 75):.4f} | {v.min():.4f} |")
    ch5 = {}
    for r in P:
        c = r["policies"]["P5r"]["calib"]["choice"]
        ch5[c] = ch5.get(c, 0) + 1
    L += ["", f"P5r repair chosen: {ch5}", ""]
    L += ["", "Per-chain (12 settings each): counts of P7 cheaper / tie / dearer, median VOI share of P3c / P4c / P5r, max Delta.", "",
          "| chain | cheaper | tie | dearer | VOI P3c | VOI P4c | VOI P5r | max Delta |", "|---|---|---|---|---|---|---|---|"]
    for cid in sorted({r["chain_id"] for r in P}):
        R = [r for r in P if r["chain_id"] == cid]
        dd = np.array([r["delta"] for r in R])
        med = []
        for nm in NEW:
            v = [(r["C0"] - r["policies"][nm]["cost"]) / (r["C0"] - r["p7_cost"]) for r in R if r["C0"] - r["p7_cost"] > 1e-9]
            med.append(f"{np.median(v):.3f}" if v else "n/a")
        L.append(f"| {cid} | {(dd > 1e-9).sum()} | {(np.abs(dd) <= 1e-9).sum()} | {(dd < -1e-9).sum()} | {' | '.join(med)} | {dd.max():.4f} |")
    # ---- replay
    rep = [json.loads(line) for line in open(REPLAY)] if REPLAY.exists() else []
    rp = [r for r in rep if r["status"] == "replayed"]
    L += ["", "## (ii) Replay (held-out windows; cell T = 32, B = 4, alpha = 0.1; all policies recomputed in this run)", "",
          f"datasets: {len(rp)}; windows: {sum(r['n_windows'] for r in rp)}", ""]
    if rp:
        names = ALL + ["never"]
        M = np.concatenate([np.array([r["cost"][nm] for nm in names]).T for r in rp])
        Pm = np.concatenate([np.array([r["promoted"][nm] for nm in names]).T for r in rp]).astype(float)
        j7 = names.index("P7")
        mean_ci = p8.boot_ci(M, lambda m: m.mean(axis=0))
        diff_ci = p8.boot_ci(M, lambda m: (m[:, j7][:, None] - m).mean(axis=0))
        exa = {nm: [r["exact"][nm]["risk_causal"] for r in rp] for nm in ALL + ["never"]}
        L += ["Pooled over windows (window bootstrap, 2000 resamples, seed 20261119). Difference column is P7 - X (negative = P7 cheaper):", "",
              "| policy | mean realised cost [95% CI] | P7 - X [95% CI] | promotion rate | causal risk / alpha (mean over datasets; max) |",
              "|---|---|---|---|---|"]
        for i, nm in enumerate(names):
            dtxt = "-" if nm == "P7" else "%.4f [%.4f, %.4f]" % ((M[:, j7] - M[:, i]).mean(), diff_ci[0, i], diff_ci[1, i])
            L.append(f"| {nm} | {M[:, i].mean():.4f} [{mean_ci[0, i]:.4f}, {mean_ci[1, i]:.4f}] | {dtxt} | {Pm[:, i].mean():.3f} | "
                     f"{np.mean(exa[nm]) / ALPHA:.3f}; {np.max(exa[nm]) / ALPHA:.3f} |")
        # per-dataset: P7 below every safe baseline
        si = [names.index(p) for p in SAFE]
        below = ties = above = 0
        rows = []
        for r in rp:
            m = np.array([r["cost"][nm] for nm in names]).T.mean(axis=0)
            bs = min(si, key=lambda i: m[i])
            dlt = m[bs] - m[j7]
            below += dlt > 1e-9
            ties += abs(dlt) <= 1e-9
            above += dlt < -1e-9
            rows.append((r["id"], r["n_windows"], names[bs], dlt, m))
        L += ["", f"Datasets where P7's mean realised cost is below every safe baseline (P1, P2, P6, P3c, P4c, P5r): {below} of {len(rp)}; "
              f"tied (|diff| <= 1e-9): {ties}; P7 above the best safe baseline: {above}.", "",
              "Per-dataset mean realised cost:", "", "| dataset | windows | best safe | best safe - P7 | " + " | ".join(names) + " |",
              "|" + "---|" * (len(names) + 4)]
        for cid, nw, bsn, dlt, m in rows:
            L.append(f"| {cid} | {nw} | {bsn} | {dlt:.4f} | " + " | ".join(f"{v:.3f}" for v in m) + " |")
        pl = {}
        for r in rp:
            k_ = r["exact"]["P5r"]["choice"]
            pl[k_] = pl.get(k_, 0) + 1
        L += ["", f"P5r repair chosen per dataset (exact, fitted model): {pl}"]
    open(SUMMARY, "w").write("\n".join(L) + "\n")
    log("summary written")


if __name__ == "__main__":
    RES.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[1]
    w = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--workers=")), 6))
    nc = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--chains=")), None)
    {"panel": lambda: run_panel(w, nc), "validate": run_validate, "check8": run_check8, "replay": lambda: run_replay(w),
     "summary": run_summary}[stage]()
