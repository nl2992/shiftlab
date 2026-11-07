"""INDEPENDENT reproduction of PPRM's predictive-risk monitor (Zhang et al., ICML 2026, arXiv 2602.02229).

Written from the paper's equations (not from repo code in src/shiftlab/dive, which is deliberately NOT imported):
  Eq.16 synthetic labels; Eq.17-19 prediction-powered source/batch/running risk estimators;
  Eq.21 source upper bound U0 (betting UCB, Appx A.2, WSR hedged capital over a grid);
  Eq.22 variance process V_t and CM-EB lower CS (Howard et al. 2021; uniform mixing density q on [0,1],
        psi_E(l) = -log(1-l) - l; boundary u(V) found by bisection), Eq.23 alarm 1[L_t > U0 + eps_tol];
  Eq.26/27/28 plug-in reliance eta_t with sliding window L=60 (adaptive) vs fixed eta_t = eta_0 = 1;
  SRM baseline (Eq.9-13): labeled-only, Hoeffding source bound, same CM-EB test side. (Ideal-PPRM baseline of the paper is not implemented.)

Data: SYNTHETIC binary-loss stream (CIFAR10-C / LLM data are external; not downloaded). Hence absolute alarm times are NOT
comparable to the paper; only orderings (PPRM < SRM, adaptive < fixed, Ideal <= PPRM) and false-alarm control are checked.
Usage: python pprm_independent.py <out_json> [reps=100] [T=1500] [seed_offset=0] [q_pred=0.03] [noise=0.01] [--no-nominal]
(q_pred/noise set the synthetic-label predictor quality: it errs on the hardest q_pred fraction plus `noise`; the full-budget
adaptive-vs-fixed reliance sweep varies them. seed_offset gives distinct streams per chunk; raw per-run alarm times are saved so
chunks can be merged.)
"""

import json
import sys

import numpy as np

DELTA_S, DELTA_T, ETA0, ETA_MAX, WIN = 0.05, 0.20, 1.0, 1.0, 60
N_LAB, N_UNL = 1, 15  # per round (paper Sec. 6)
N0 = 500  # source labeled samples (our choice; paper value not extracted)
EPS_TOL = 0.04
Q_PRED, NOISE = 0.03, 0.01
_LAM = (np.arange(400) + 0.5) / 400.0  # midpoint rule on (0,1); q(lambda)=1


def u_boundary(V):
    """u(V) = sup{S : int_0^1 q(l) exp(l S - psi_E(l) V) dl < 1/delta_T}, vectorised bisection over V."""
    V = np.atleast_1d(np.asarray(V, float))
    psi = -np.log1p(-_LAM) - _LAM
    lo, hi = np.zeros_like(V), np.full_like(V, 50.0 + 4 * np.sqrt(V.max() + 1))
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        f = np.exp(
            np.clip(mid[:, None] * _LAM[None, :] - V[:, None] * psi[None, :], -700, 700)
        ).mean(1)
        big = f >= 1.0 / DELTA_T
        hi = np.where(big, mid, hi)
        lo = np.where(big, lo, mid)
    return lo


def lower_cs(x):
    """CM-EB lower CS of the running mean of x in [0,1]: mean_t - u(V_t)/t, V_t = sum (x_s - mean_{s-1})^2."""
    t = np.arange(1, len(x) + 1)
    mean = np.cumsum(x) / t
    prev = np.concatenate([[0.5], mean[:-1]])
    V = np.cumsum((x - prev) ** 2)
    return mean - u_boundary(V) / t


def betting_ucb(z, delta, c=0.5, grid=1000):
    """Upper confidence bound on mean(z), z in [0,1]: smallest m with K^-(m) = prod(1 - lam_i (z_i - m)) >= 1/delta."""
    n = len(z)
    ms = np.linspace(0.0, 1.0, grid + 1)[1:-1]
    i = np.arange(1, n + 1)
    np.concatenate([[0.5], np.cumsum(z)[:-1] / i[:-1]]) if n > 1 else np.array([0.5])
    mu_hat = (0.5 + np.cumsum(z)) / (i + 1)
    var_hat = (0.25 + np.cumsum((z - mu_hat) ** 2)) / (i + 1)
    var_prev = np.concatenate([[0.25], var_hat[:-1]])
    lam = np.sqrt(2 * np.log(2 / delta) / (var_prev * i * np.log1p(i)))
    logK = np.empty(len(ms))
    cap = c / (1 - ms)
    for j, m in enumerate(ms):
        l = np.minimum(lam, cap[j])
        logK[j] = np.log1p(-l * (z - m)).sum()
    ok = np.where(logK >= np.log(1 / delta))[0]
    return ms[ok[0]] if len(ok) else 1.0


def make_stream(rng, T, p_fun, q_pred=None, n=N_LAB, N=N_UNL):
    q_pred = Q_PRED if q_pred is None else q_pred
    """per round: labeled losses u (monitored model wrong), their synthetic-label losses ut, unlabeled ut.
    Monitored model errs w.p. p_fun(t) driven by hardness h; synthetic predictor f_p errs on the hardest ~q_pred
    fraction plus noise (correlated with f). ut = 1[f disagrees with f_p's label] ~ 1[f wrong XOR f_p wrong]."""

    def draw(m, t):
        h = rng.random(m)
        f_wrong = h < p_fun(t)
        fp_wrong = (h < q_pred) | (rng.random(m) < NOISE)
        u = f_wrong.astype(float)
        ut = (f_wrong ^ fp_wrong).astype(float)
        return u, ut

    out = []
    for t in range(T):
        u, ut = draw(n, t)
        _, utU = draw(N, t)
        out.append((u, ut, utU))
    return out


def source_ucb(rng, p0, n0=N0, N=N_UNL, q_pred=None):
    q_pred = Q_PRED if q_pred is None else q_pred
    h = rng.random(n0)
    fw = h < p0
    fpw = (h < q_pred) | (rng.random(n0) < NOISE)
    u, ut = fw.astype(float), (fw ^ fpw).astype(float)
    h2 = rng.random((n0, N))
    fw2 = h2 < p0
    fpw2 = (h2 < q_pred) | (rng.random((n0, N)) < NOISE)
    utU = (fw2 ^ fpw2).astype(float)
    z = ETA0 * utU.mean(1) + u - ETA0 * ut  # Eq.35-style paired values, raw range [-eta, 1+eta]
    zs = (z + ETA_MAX) / (1 + 2 * ETA_MAX)  # g_a rescale
    U_pp = betting_ucb(zs, DELTA_S) * (1 + 2 * ETA_MAX) - ETA_MAX
    U_srm = u.mean() + np.sqrt(np.log(1 / DELTA_S) / (2 * n0))
    return U_pp, U_srm, u.mean()


def eta_adaptive(hist_u, hist_ut, hist_utU):
    if len(hist_u) < 3:
        return ETA0
    u = np.concatenate(hist_u[-WIN:])
    ut = np.concatenate(hist_ut[-WIN:])
    utU = np.concatenate(hist_utU[-WIN:])
    v = utU.var()
    if v <= 1e-12 or u.std() == 0 or ut.std() == 0:
        return ETA0
    cov = np.cov(u, ut)[0, 1]
    return float(np.clip(cov / ((1 + len(u) / len(utU)) * v), 0.0, ETA_MAX))


def run_one(rng, T, p_fun, p0):
    U_pp, U_srm, _ = source_ucb(rng, p0)
    st = make_stream(rng, T, p_fun)
    est = {"srm": [], "pp_fixed": [], "pp_adapt": []}
    hu, hut, huU = [], [], []
    for u, ut, utU in st:
        est["srm"].append(u.mean())
        eta_a = eta_adaptive(hu, hut, huU)
        for key, eta in (("pp_fixed", ETA0), ("pp_adapt", eta_a)):
            est[key].append(eta * utU.mean() + u.mean() - eta * ut.mean())
        hu.append(u)
        hut.append(ut)
        huU.append(utU)
    out = {}
    for key in ("srm", "pp_fixed", "pp_adapt"):
        x = np.array(est[key])
        if key == "srm":
            xs, scale, shift, U = x, 1.0, 0.0, U_srm
        else:
            xs, scale, shift, U = (x + ETA_MAX) / (1 + 2 * ETA_MAX), 1 + 2 * ETA_MAX, -ETA_MAX, U_pp
        L = lower_cs(xs) * scale + shift
        alarm = np.where(L > U + EPS_TOL)[0]
        out[key] = int(alarm[0]) + 1 if len(alarm) else None
    return out


def main():
    global Q_PRED, NOISE
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_json = args[0]
    reps = int(args[1]) if len(args) > 1 else 100
    T = int(args[2]) if len(args) > 2 else 1500
    seed_offset = int(args[3]) if len(args) > 3 else 0
    Q_PRED = float(args[4]) if len(args) > 4 else Q_PRED
    NOISE = float(args[5]) if len(args) > 5 else NOISE
    do_nominal = "--no-nominal" not in flags
    p0 = 0.08
    ramp_start, ramp_end, p_end = 300, 900, 0.30
    drift = lambda t: p0 + (p_end - p0) * np.clip((t - ramp_start) / (ramp_end - ramp_start), 0, 1)
    nominal = lambda t: p0
    # true crossing time of running risk R_bar_t > R0 + eps_tol
    Rbar = np.cumsum([drift(t) for t in range(T)]) / np.arange(1, T + 1)
    cross = int(np.argmax(Rbar > p0 + EPS_TOL)) + 1
    res = {
        "settings": {
            "reps": reps,
            "T": T,
            "p0": p0,
            "ramp": [ramp_start, ramp_end, p_end],
            "eps_tol": EPS_TOL,
            "delta_S": DELTA_S,
            "delta_T": DELTA_T,
            "n_lab": N_LAB,
            "n_unl": N_UNL,
            "n0": N0,
            "eta_max": ETA_MAX,
            "window": WIN,
            "true_crossing_t": cross,
            "seed_offset": seed_offset,
            "q_pred": Q_PRED,
            "noise": NOISE,
        },
        "drift": {},
        "nominal": {},
    }
    for name, pf, store in [("drift", drift, res["drift"])] + (
        [("nominal", nominal, res["nominal"])] if do_nominal else []
    ):
        runs = []
        for r in range(reps):
            runs.append(run_one(np.random.default_rng(1000 + seed_offset + r), T, pf, p0))
            if r % 10 == 0:
                print(name, r, runs[-1], flush=True)
        store["raw_runs"] = runs
        for key in ("srm", "pp_fixed", "pp_adapt"):
            ts = [x[key] for x in runs]
            fired = [t for t in ts if t is not None]
            store[key] = {
                "alarm_rate": len(fired) / reps,
                "mean_alarm_t": float(np.mean(fired)) if fired else None,
                "sd": float(np.std(fired)) if fired else None,
            }
        # paired comparison adaptive vs fixed (runs where both alarmed)
        pairs = [(x["pp_adapt"], x["pp_fixed"]) for x in runs if x["pp_adapt"] and x["pp_fixed"]]
        store["paired_adapt_minus_fixed"] = (
            float(np.mean([a - b for a, b in pairs])) if pairs else None
        )
        pairs = [(x["pp_adapt"], x["srm"]) for x in runs if x["pp_adapt"] and x["srm"]]
        store["paired_adapt_minus_srm"] = (
            float(np.mean([a - b for a, b in pairs])) if pairs else None
        )
    with open(out_json, "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
