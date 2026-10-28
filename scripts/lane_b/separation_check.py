"""Lane B B1 numerical check: oblivious versus evidence-responsive label allocation.

Vectorised Monte Carlo over seeds. One shared anytime-valid e-process (the mixture of
fixed-stake betting martingales used by ``PredictableBoundMeanEProcess``, re-implemented
row-wise for speed and checked against the class in the tests) is driven by HT increments
V = G*Z/q - eps with predictable q and bound C/q + eps.

Seed registry: block lane_b_toy_development 100600000-100699999. Cell index
k = ((variant_idx * 2 + delay_idx) * 4 + budget_idx); seed = 100600000 + k*10000 + i with
i in [0, n_seeds) for the shared H/N rows and i in [5000, 5000 + n_null) for null rows.
All rules inside one cell share the same seeds (common random numbers).
"""

from __future__ import annotations

import csv
import sys
import time
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.stats import beta

T = 2000
S0 = 500
L = 300
RHO = 0.05
C = 1.0
EPS = 0.1
MU_HARM = 0.5
MU_BURST_HARMLESS = -0.2
MU_NULL = EPS
STAKES = np.array([0.05, 0.1, 0.2, 0.4, 0.8])
ALPHAS = (0.05, 0.001)
BUDGETS = (40, 60, 80, 120)
DELAYS = (0, 20)
VARIANTS = ("A_agree_in_eprocess", "B_disagree_only", "B2_disagree_only_rho0.2")
VARIANT_RHO = {"A_agree_in_eprocess": 0.05, "B_disagree_only": 0.05, "B2_disagree_only_rho0.2": 0.2}
SEED_BASE = 100600000
CELL_STRIDE = 10000
NULL_OFFSET = 5000
MIX_STEP = 25
BURST_RUN = 3  # a disagreement is burst-type when the current consecutive run is >= 3
SPRT_DELTA = 0.2

DOCS = Path(__file__).resolve().parents[2] / "docs" / "lane_b_burst_allocation"


def p_of_mean(mu: float) -> float:
    return (1 + mu / C) / 2


@dataclass(frozen=True)
class Config:
    rule: str  # fixed, burst, paced, r1, r2
    q: float = 1.0
    b: int = 0
    q_sparse: float = 1.0
    h: float = 10.0

    def label(self) -> str:
        if self.rule == "fixed":
            return f"fixed(q={self.q})"
        if self.rule == "burst":
            return f"burstcap(b={self.b},qs={self.q_sparse})"
        if self.rule == "r2":
            return f"r2(h={self.h:g})"
        return self.rule


def oblivious_configs(budget: int) -> list[Config]:
    cfgs = [Config("fixed", q=q) for q in (0.05, 0.1, 0.25, 0.5, 1.0)]
    for b in sorted({0, budget // 4, budget // 2, budget}):
        for qs in (0.25, 0.5, 1.0):
            cfgs.append(Config("burst", b=b, q_sparse=qs))
    cfgs.append(Config("paced"))
    return cfgs


def responsive_configs() -> list[Config]:
    return [Config("r1")] + [Config("r2", h=h) for h in (3.0, 10.0, 30.0, 100.0)]


def draw_world(seeds: np.ndarray, rho: float = RHO):
    """D, Uz, Ug for each seed (D is zero before S0, burst on [S0, S0+L), sparse after)."""
    n = len(seeds)
    d = np.zeros((n, T), dtype=bool)
    uz = np.empty((n, T))
    ug = np.empty((n, T))
    for i, s in enumerate(seeds):
        rng = np.random.default_rng(int(s))
        sparse = rng.random(T) < rho
        d[i, S0 + L :] = sparse[S0 + L :]
        d[i, S0 : S0 + L] = True
        uz[i] = rng.random(T)
        ug[i] = rng.random(T)
    return d, uz, ug


def mean_path(scenario: str) -> np.ndarray:
    mu = np.full(T, MU_BURST_HARMLESS)
    if scenario == "H":
        mu[S0:] = MU_HARM
    elif scenario == "Htrans":  # corrective check: harm only during the burst
        mu[S0 : S0 + L] = MU_HARM
    elif scenario == "N":
        mu[S0 + L :] = MU_HARM
    elif scenario == "null":
        mu[:] = MU_NULL
    else:
        raise ValueError(scenario)
    return mu


def simulate(
    cfg: Config,
    d_mat: np.ndarray,
    uz: np.ndarray,
    ug: np.ndarray,
    mu: np.ndarray,
    *,
    budget: int,
    delay: int,
    variant: str,
    record: bool = False,
    restart_rows: np.ndarray | None = None,
    monitor: str = "single",
):
    """Run one rule on a stack of rows. mu has shape (rows, T) (mean of Z per row/time)."""
    rows = d_mat.shape[0]
    zmat = np.where(uz < (1 + mu / C) / 2, C, -C)
    thr = np.log(1.0 / np.asarray(ALPHAS))
    logw = np.zeros((rows, len(STAKES)))
    log_k = np.log(len(STAKES))
    alarm_t = np.full((rows, len(ALPHAS)), T, dtype=np.int64)
    labels_at = np.zeros((rows, len(ALPHAS)))
    done = np.zeros((rows, len(ALPHAS)), dtype=bool)
    cum = np.zeros(rows, dtype=np.int64)
    req = np.zeros((rows, T), dtype=bool)
    qrec = np.zeros((rows, T)) if record else None
    run = np.zeros(rows, dtype=np.int64)
    burst_type = np.zeros((rows, T), dtype=bool)
    spent_burst = np.zeros(rows, dtype=np.int64)
    dwin = np.zeros(rows)  # running sum of D over the last 200 events (past only)
    llr = np.zeros(rows)
    stopped = np.zeros(rows, dtype=bool)
    wstat = np.zeros(rows)
    # SPRT between mean eps (H0) and mean MU_HARM (H1) on +-C outcomes
    p0, p1 = p_of_mean(EPS), p_of_mean(MU_HARM)
    l_pos, l_neg = np.log(p1 / p0), np.log((1 - p1) / (1 - p0))
    lo = np.log(SPRT_DELTA / (1 - SPRT_DELTA))
    mixture = monitor == "mixture"
    if mixture:
        n_starts = len(range(0, T, MIX_STEP))
        lcum = np.zeros((rows, len(STAKES)))
        log_a = np.full((rows, len(STAKES)), -np.inf)
        started = 0
    for t in range(T):
        d_t = d_mat[:, t]
        if mixture and t % MIX_STEP == 0:
            # component starting at t: wealth_k(t') = exp(lcum(t') - lcum(t)), weight 1/n_starts
            log_a = np.logaddexp(log_a, -np.log(n_starts) - lcum)
            started += 1
        if restart_rows is not None and t == S0 + L:
            logw[restart_rows] = 0.0  # ORACLE diagnostic only: wipes burst debt in flagged rows
        # labels that arrived strictly before t: event s = t - delay - 1
        s = t - delay - 1
        if s >= 0:
            lab = req[:, s]
            zs = zmat[:, s]
            if cfg.rule == "r1":
                m = lab & burst_type[:, s]
                llr += np.where(m, np.where(zs > 0, l_pos, l_neg), 0.0)
                stopped |= llr <= lo
            elif cfg.rule == "r2":
                wstat += np.where(lab, zs - EPS, 0.0)
        run = np.where(d_t, run + 1, 0)
        bt = d_t & (run >= BURST_RUN)
        burst_type[:, t] = bt
        rem = budget - cum
        if cfg.rule == "fixed":
            q = np.where(d_t, cfg.q, 0.0)
        elif cfg.rule == "burst":
            q = np.where(
                bt, np.where(spent_burst < cfg.b, 1.0, 0.0), np.where(d_t, cfg.q_sparse, 0.0)
            )
        elif cfg.rule == "paced":
            rate = (dwin + 0.5) / (min(t, 200) + 10)
            exp_rem = np.maximum(1.0, rate * (T - t))
            q = np.where(d_t, np.minimum(1.0, rem / exp_rem), 0.0)
        elif cfg.rule == "r1":
            q = np.where(d_t & ~(bt & stopped), 1.0, 0.0)
        else:  # r2
            sample = wstat >= 0
            q = np.where(d_t & sample, 1.0, 0.0)
            wstat += np.where(d_t & ~sample, 1.0 / cfg.h, 0.0)
        q = np.where(rem > 0, q, 0.0)
        g = d_t & (ug[:, t] < q)
        if record:
            qrec[:, t] = q
        req[:, t] = g
        cum += g
        spent_burst += g & bt
        # window of D for paced forecast (past only: update after use)
        dwin += d_t
        if t >= 200:
            dwin -= d_mat[:, t - 200]
        # HT increment and bound
        safe_q = np.where(q > 0, q, 1.0)
        v = np.where(g, zmat[:, t] / safe_q, 0.0) - EPS
        bound = np.where(d_t, np.where(q > 0, C / safe_q, 0.0) + EPS, C + EPS)
        # q_t = 0 events are a predictable skip (stake zero, factor one); they carry no label.
        upd = np.where(d_t, q > 0, variant.startswith("A_"))
        step = np.log1p(STAKES[None, :] * (v / bound)[:, None])
        step = np.where(upd[:, None], step, 0.0)
        logw += step
        if mixture:
            lcum += step
            z = lcum + log_a
            mx = z.max(axis=1)
            log_e = mx + np.log(np.exp(z - mx[:, None]).sum(axis=1)) - log_k
            if started < n_starts:  # unstarted components are constant at one
                log_e = np.logaddexp(log_e, np.log((n_starts - started) / n_starts))
        else:
            mx = logw.max(axis=1)
            log_e = mx + np.log(np.exp(logw - mx[:, None]).sum(axis=1)) - log_k
        hit = (log_e[:, None] >= thr[None, :]) & ~done & (t + delay < T)
        if hit.any():
            alarm_t[hit] = t + delay
            labels_at[hit] = np.broadcast_to(cum[:, None], hit.shape)[hit]
            done |= hit
    labels_at = np.where(done, labels_at, cum[:, None])
    out = {"alarm": alarm_t, "labels": labels_at}
    if record:
        out["q"] = qrec
        out["req"] = req
        out["cum"] = cum
    return out


def clopper_pearson_upper(k: int, n: int, level: float = 0.95) -> float:
    return 1.0 if k >= n else float(beta.ppf(level, k + 1, n - k))


def summarise(res, n: int, n_null: int):
    """Per-alpha metrics from the stacked rows [H(n), N(n), null(n_null)]."""
    out = []
    for ai, alpha in enumerate(ALPHAS):
        a = res["alarm"][:, ai]
        lab = res["labels"][:, ai]
        h, nn, nu = slice(0, n), slice(n, 2 * n), slice(2 * n, 2 * n + n_null)
        row = {"alpha": alpha}
        for name, sl, onset in (("H", h, S0), ("N", nn, S0 + L)):
            row[f"P_{name}"] = float(np.mean(a[sl] < T))
            row[f"delay_{name}"] = float(np.mean(np.maximum(np.minimum(a[sl], T) - onset, 0)))
            row[f"labels_{name}"] = float(np.mean(lab[sl]))
        k = int(np.sum(a[nu] < T))
        row["fa_count"] = k
        row["n_null"] = n_null
        row["fa_upper95"] = clopper_pearson_upper(k, n_null)
        out.append(row)
    return out


def run_cell(args):
    variant, delay, budget, n, n_null, restart = args
    vi, di, bi = VARIANTS.index(variant), DELAYS.index(delay), BUDGETS.index(budget)
    k = (vi * 2 + di) * 4 + bi  # at most 24 cells; stride 10000 keeps blocks disjoint
    base = SEED_BASE + k * CELL_STRIDE
    rho = VARIANT_RHO[variant]
    d1, uz1, ug1 = draw_world(base + np.arange(n), rho)
    d0, uz0, ug0 = draw_world(base + NULL_OFFSET + np.arange(n_null), rho)
    d_mat = np.concatenate([d1, d1, d0])
    uz = np.concatenate([uz1, uz1, uz0])
    ug = np.concatenate([ug1, ug1, ug0])
    mu = np.concatenate(
        [
            np.broadcast_to(mean_path("H"), (n, T)),
            np.broadcast_to(mean_path("N"), (n, T)),
            np.broadcast_to(mean_path("null"), (n_null, T)),
        ]
    )
    rows_out = []
    for cfg in oblivious_configs(budget) + responsive_configs():
        mask = None
        if restart:
            mask = np.zeros(d_mat.shape[0], dtype=bool)
            mask[n : 2 * n] = True  # N rows only
        res = simulate(
            cfg, d_mat, uz, ug, mu, budget=budget, delay=delay, variant=variant, restart_rows=mask
        )
        for r in summarise(res, n, n_null):
            rows_out.append(
                {
                    "variant": variant,
                    "d": delay,
                    "B": budget,
                    "family": "oblivious"
                    if cfg.rule in ("fixed", "burst", "paced")
                    else cfg.rule[:2],
                    "rule": cfg.label(),
                    **r,
                }
            )
    return rows_out


def run_kref(args):
    """Empirical K_alpha: labels to alarm with an unconstrained budget (d=0)."""
    variant, n = args
    base = SEED_BASE + 90000 + 1000 * VARIANTS.index(variant)
    d1, uz1, ug1 = draw_world(base + np.arange(n), VARIANT_RHO[variant])
    out = []
    for scen, cfg in (
        ("H_burst_q1", Config("fixed", q=1.0)),
        ("N_sparse_only_q1", Config("burst", b=0, q_sparse=1.0)),
    ):
        mu = np.broadcast_to(mean_path("H" if scen[0] == "H" else "N"), (n, T))
        res = simulate(cfg, d1, uz1, ug1, mu, budget=10**6, delay=0, variant=variant)
        for ai, alpha in enumerate(ALPHAS):
            ok = res["alarm"][:, ai] < T
            labs = res["labels"][ok, ai]
            out.append(
                {
                    "variant": variant,
                    "scenario": scen,
                    "alpha": alpha,
                    "P_detect": float(ok.mean()),
                    "median_labels": float(np.median(labs)) if labs.size else float("nan"),
                    "p90_labels": float(np.quantile(labs, 0.9)) if labs.size else float("nan"),
                }
            )
    return out


def best(rows, key_fn):
    return min(rows, key=key_fn)


def make_tables(all_rows):
    lines = []
    cols = "| rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |"
    sep = "|---|---|---|---|---|---|---|"
    for variant in VARIANTS:
        for delay in DELAYS:
            for alpha in ALPHAS:
                lines.append(f"\n#### variant {variant}, d={delay}, alpha={alpha}\n")
                lines.append("| B | choice " + cols[1:])
                lines.append("|---|---|" + sep[1:])
                for budget in BUDGETS:
                    sub = [
                        r
                        for r in all_rows
                        if r["variant"] == variant
                        and r["d"] == delay
                        and r["B"] == budget
                        and r["alpha"] == alpha
                    ]
                    obl = [r for r in sub if r["family"] == "oblivious"]
                    r2 = [r for r in sub if r["family"] == "r2"]
                    r1 = [r for r in sub if r["family"] == "r1"]

                    def mm(r):
                        return (-min(r["P_H"], r["P_N"]), (r["delay_H"] + r["delay_N"]) / 2)

                    def dl(r):
                        return ((r["delay_H"] + r["delay_N"]) / 2, -min(r["P_H"], r["P_N"]))

                    picks = [
                        ("obl max-min", best(obl, mm)),
                        ("obl min-delay", best(obl, dl)),
                        ("r1 SPRT", r1[0]),
                        ("r2 DE-CuSum best", best(r2, mm)),
                    ]
                    for name, r in picks:
                        lines.append(
                            f"| {budget} | {name} | {r['rule']} | {r['P_H']:.3f} | {r['P_N']:.3f} | "
                            f"{r['delay_H']:.0f} | {r['delay_N']:.0f} | {r['labels_H']:.0f} | "
                            f"{r['labels_N']:.0f} |"
                        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registered corrective check (LANE_CONTROL tick 3): transient harm in H and the
# all-onset e-detector mixture (starts every MIX_STEP events) as the shared monitor.
# Seeds: old stride m = j % 8 of the development block, gap [1000, 5000) of that stride
# (the first check only used offsets [0, 1000) and [5000, 6000) of strides 0-9, and
# the K_alpha reference at 100690000-100692999), sub-slot j // 8 of width 2000:
# H/N rows at base + [0, 1000), null rows at base + 1000 + [0, 1000).
# ---------------------------------------------------------------------------
CORR_RHOS = (0.05, 0.2)


def corrective_base(rho_idx: int, delay_idx: int, budget_idx: int) -> int:
    j = (rho_idx * 2 + delay_idx) * 4 + budget_idx
    return SEED_BASE + (j % 8) * CELL_STRIDE + 1000 + (j // 8) * 2000


def run_cell_corrective(args):
    rho, delay, budget, n, n_null = args
    base = corrective_base(CORR_RHOS.index(rho), DELAYS.index(delay), BUDGETS.index(budget))
    d1, uz1, ug1 = draw_world(base + np.arange(n), rho)
    d0, uz0, ug0 = draw_world(base + 1000 + np.arange(n_null), rho)
    d_mat = np.concatenate([d1, d1, d0])
    uz = np.concatenate([uz1, uz1, uz0])
    ug = np.concatenate([ug1, ug1, ug0])
    mu = np.concatenate(
        [
            np.broadcast_to(mean_path("Htrans"), (n, T)),
            np.broadcast_to(mean_path("N"), (n, T)),
            np.broadcast_to(mean_path("null"), (n_null, T)),
        ]
    )
    out = []
    for cfg in oblivious_configs(budget) + responsive_configs():
        res = simulate(
            cfg,
            d_mat,
            uz,
            ug,
            mu,
            budget=budget,
            delay=delay,
            variant="B_disagree_only",
            monitor="mixture",
        )
        for r in summarise(res, n, n_null):
            fam = "oblivious" if cfg.rule in ("fixed", "burst", "paced") else cfg.rule[:2]
            out.append(
                {"rho": rho, "d": delay, "B": budget, "family": fam, "rule": cfg.label(), **r}
            )
    return out


def corrective_verdict(rows):
    """Pre-registered: separation FAILS if at every tight B some oblivious rule's min(P_H,P_N)
    is within 0.05 of (or above) the best responsive rule's min(P_H,P_N)."""

    def mp(r):
        return min(r["P_H"], r["P_N"])

    lines = []
    for rho in CORR_RHOS:
        for d in DELAYS:
            for alpha in ALPHAS:
                gaps = []
                for budget in (40, 60, 80):
                    s = [
                        r
                        for r in rows
                        if r["rho"] == rho
                        and r["d"] == d
                        and r["alpha"] == alpha
                        and r["B"] == budget
                    ]
                    bo = max((r for r in s if r["family"] == "oblivious"), key=mp)
                    br = max((r for r in s if r["family"] in ("r1", "r2")), key=mp)
                    gaps.append((budget, mp(bo), bo["rule"], mp(br), br["rule"]))
                fails = all(go >= gr - 0.05 for _, go, _, gr, _ in gaps)
                lines.append((rho, d, alpha, gaps, fails))
    return lines


def main_corrective(n: int, n_null: int):
    t0 = time.time()
    jobs = [(rho, d, b, n, n_null) for rho in CORR_RHOS for d in DELAYS for b in BUDGETS]
    with Pool(6) as pool:
        results = pool.map(run_cell_corrective, jobs)
    rows = [r for res in results for r in res]
    with open(DOCS / "B1_corrective_check_grid.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in r.items()})
    verdict = corrective_verdict(rows)
    head = [f"<!-- AUTO n={n} n_null={n_null} runtime {time.time() - t0:.0f}s -->"]
    head.append(
        "| rho | d | alpha | B | best obl min P (rule) | best responsive min P (rule) | gap |"
    )
    head.append("|---|---|---|---|---|---|---|")
    for rho, d, alpha, gaps, fails in verdict:
        for budget, go, ro, gr, rr in gaps:
            head.append(
                f"| {rho} | {d} | {alpha} | {budget} | {go:.3f} ({ro}) | {gr:.3f} ({rr}) | "
                f"{gr - go:+.3f} |"
            )
        verdict_txt = "separation FAILS" if fails else "separation NOT refuted"
        head.append(f"| {rho} | {d} | {alpha} | all tight B | | | {verdict_txt} |")
    out = list(head)
    out.append("\n### Full tables (every rule)\n")
    for rho in CORR_RHOS:
        for d in DELAYS:
            for alpha in ALPHAS:
                out.append(f"\n#### rho={rho}, d={d}, alpha={alpha}\n")
                out.append(
                    "| B | rule | min P | P_H | P_N | delay_H | delay_N | labels_H | labels_N | "
                    "null FA | exact 95% upper |"
                )
                out.append("|---|---|---|---|---|---|---|---|---|---|---|")
                for r in rows:
                    if (r["rho"], r["d"], r["alpha"]) == (rho, d, alpha):
                        out.append(
                            f"| {r['B']} | {r['rule']} | {min(r['P_H'], r['P_N']):.3f} | "
                            f"{r['P_H']:.3f} | {r['P_N']:.3f} | {r['delay_H']:.0f} | "
                            f"{r['delay_N']:.0f} | {r['labels_H']:.0f} | {r['labels_N']:.0f} | "
                            f"{r['fa_count']}/{r['n_null']} | {r['fa_upper95']:.4f} |"
                        )
    (DOCS / "B1_corrective_check_tables.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(head))
    print("runtime", time.time() - t0)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    n_null = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    t0 = time.time()
    jobs = [(v, d, b, n, n_null, False) for v in VARIANTS for d in DELAYS for b in BUDGETS]
    with Pool(6) as pool:
        results = pool.map(run_cell, jobs)
        krefs = pool.map(run_kref, [(v, n) for v in VARIANTS])
    all_rows = [r for res in results for r in res]
    diag_jobs = [(v, 0, b, n, 0, True) for v in VARIANTS[1:] for b in BUDGETS]
    with Pool(6) as pool:
        diag_rows = [r for res in pool.map(run_cell, diag_jobs) for r in res]
    with open(DOCS / "B1_numerical_check_restart_diag.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "variant",
                "d",
                "B",
                "family",
                "rule",
                "alpha",
                "P_N",
                "delay_N",
                "labels_N",
            ],
        )
        w.writeheader()
        for r in diag_rows:
            w.writerow(
                {k: (f"{r[k]:.5g}" if isinstance(r[k], float) else r[k]) for k in w.fieldnames}
            )
    fields = list(all_rows[0].keys())
    with open(DOCS / "B1_numerical_check_grid.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in r.items()})
    kref_rows = [r for res in krefs for r in res]
    tables = make_tables(all_rows)
    fa = []
    for alpha in ALPHAS:
        sub = [r for r in all_rows if r["alpha"] == alpha]
        worst = max(sub, key=lambda r: r["fa_count"])
        fa.append(
            f"alpha={alpha}: max false-alarm count over {len(sub)} (cell, rule) null runs = "
            f"{worst['fa_count']}/{worst['n_null']} (rate {worst['fa_count'] / worst['n_null']:.4f}; "
            f"{worst['variant']}, d={worst['d']}, B={worst['B']}, {worst['rule']}); "
            f"largest exact 95% upper bound = {max(r['fa_upper95'] for r in sub):.4f}; "
            f"mean rate = {np.mean([r['fa_count'] / r['n_null'] for r in sub]):.5f}"
        )
    kt = [
        "| variant | scenario | alpha | P_detect | median labels | p90 labels |",
        "|---|---|---|---|---|---|",
    ]
    for r in kref_rows:
        kt.append(
            f"| {r['variant']} | {r['scenario']} | {r['alpha']} | {r['P_detect']:.3f} | "
            f"{r['median_labels']:.0f} | {r['p90_labels']:.0f} |"
        )
    body = (
        f"<!-- AUTO-GENERATED TABLES (n={n} H/N seeds, n_null={n_null}); runtime "
        f"{time.time() - t0:.0f}s -->\n"
        "### Empirical K_alpha (unconstrained budget, d=0)\n\n" + "\n".join(kt) + "\n\n"
        "### Null control (mean = eps everywhere)\n\n" + "\n".join(f"- {x}" for x in fa) + "\n\n"
        "### Main tables\n" + tables + "\n"
    )
    (DOCS / "B1_numerical_check_tables.md").write_text(body, encoding="utf-8")
    print(body)
    print("runtime", time.time() - t0)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "corrective":
        main_corrective(
            int(sys.argv[2]) if len(sys.argv) > 2 else 1000,
            int(sys.argv[3]) if len(sys.argv) > 3 else 1000,
        )
    else:
        main()
