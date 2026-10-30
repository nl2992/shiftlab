"""Event-level prediction-powered betting engine for the mandate-gap-closure study.

One loop over events, vectorised over independent seeds. Differences from the earlier cumsum-based
``sota_search.detectors.pp_fix`` (which stays untouched and is reproduced bit-for-bit by
``Cfg(cap_mode="x", release="legacy", unq_delay=True)``):

* explicit per-event label arrival times (random / outcome-dependent / bursty delays);
* two release rules for the wealth: ``prefix`` (in-order release; valid for any delay mechanism by
  Ville on the event-indexed martingale) and ``arrived`` (naive subset of arrived factors; can be invalid
  under outcome-dependent delay);
* ``cap_mode="sup"``: the bet cap uses only predictable quantities (no current covariate), the repair of
  the validity defect documented in ``docs/sota_gap_closure/01_VALIDITY_AND_INFORMATION_AUDIT.md``;
* hard pathwise query budget with requests charged when issued and inactive events after exhaustion;
* reliability-adaptive proxy weight theta_t (S03), growth/variance/mixture/paced allocation (S04-S06).

Everything used to form q_t, theta_t, lambda_t is a function of covariates up to t and of labels whose
arrival time is < t. Evaluator-side truth never enters.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import numpy as np

ALPHA = 0.05
LOG_THR = float(np.log(1.0 / ALPHA))
K_BINS = 8
FN, FP = 5.0, 1.0


@dataclass(frozen=True)
class Cfg:
    risk: str = "brier"  # channel of the monitored risk: 'brier' or 'cost'
    frac: float = 0.10  # expected query rate (per event)
    tol: float = 0.0
    gamma: float = 1.0  # bet-moment discount (1 = full history)
    gate_w: int | None = None  # HG decision-cost gate window
    cap_mode: str = "sup"  # 'x' (legacy, depends on current covariate) | 'sup' (predictable repair)
    release: str = "prefix"  # 'prefix' | 'arrived' | 'legacy'
    unq_delay: bool = False  # legacy: unqueried events also wait ``delay`` steps
    cap: float = 0.5
    force_bet: bool = False  # audit only: always bet the maximal admissible lambda
    pace_floor: float = 0.25  # propensity floor of pacing rules as a fraction of frac (v1 of S06 used 0.25; v2 uses 0.5)
    lrv: bool = False  # F2: scale the Kelly denominator by a Bartlett long-run-variance inflation (heuristic, dependence)
    lrv_lags: int = 10
    qmin: float = 0.0  # lower bound of q_t used by the sup cap (0 -> frac for non-uniform q)
    # S03 reliability-adaptive proxy weight
    rel: str | None = None  # None | 'hard' | 'soft' | 'unc'
    rel_window: int = 64
    rel_smooth: float = 0.95
    rel_fallback: str = "uniform"  # 'none' | 'uniform' | 'conservative_bet'
    rel_score: str = "skill"  # 'skill' | 'bias'
    # S04-S06 allocation
    alloc: str = "uniform"  # uniform|variance|growth|growth_harm|growth_look|mix
    mix: tuple = (1.0, 0.0, 0.0)  # (uniform, variance, growth) shares
    mix_mode: str = "fixed"  # fixed | validation | adaptive | conservative
    oracle_alt: bool = (
        False  # growth model uses true P(y=1|x) (ORACLE, evaluator info) if stream has it
    )
    budget: int | None = None  # hard cap B on queries per path (None: expected-budget contract)
    pacing: str = "none"  # none|const|remaining|info_value|reserve|two_stage|growth_pace

    def tag(self) -> dict:
        return asdict(self)


def _chan(stream: dict, risk: str):
    if risk == "brier":
        return (
            stream["brier"],
            stream["proxy_brier"],
            stream["r0"]["brier"],
            stream["pmax"]["brier"],
        )
    return stream["loss"], stream["proxy_cost"], stream["r0"]["cost"], stream["pmax"]["cost"]


def ensure_stream(sim: dict, r0: dict | None = None) -> dict:
    """Fill defaults for a legacy G1/G2 simulation dict (proxies from the deployed model's score)."""
    from shiftlab.sota_search import detectors as det  # local import: legacy module
    from shiftlab.sota_search import generators as g

    if "proxy_brier" in sim:
        return sim
    p = sim["p"]
    act = (p >= g.TAU).astype(float)
    fam = sim["world"].family
    sim["proxy_brier"] = p * (1 - p)
    sim["proxy_cost"] = act * (1 - p) * g.FP_COST + (1 - act) * p * g.FN_COST
    sim["score"] = p
    sim["pi_true_fn"] = None
    mom = det.source_moments(fam)
    sim["r0"] = r0 or {"brier": mom["brier"][0], "cost": mom["loss"][0]}
    sim["pmax"] = {"brier": 0.25, "cost": g.FN_COST / 6.0}
    return sim


def _bins(proxy: np.ndarray, pmax: float) -> np.ndarray:
    return np.minimum((proxy / max(pmax, 1e-12) * K_BINS).astype(np.int64), K_BINS - 1)


def run(stream: dict, cfg: Cfg, delay: int | np.ndarray = 5, qseed: int = 0) -> dict:
    """Run the e-process on a batch of independent streams. Returns per-seed arrays.

    ``delay`` is either an int (fixed label delay) or an (S, T) int array of per-event delays.
    Query randomness is a common-random-number matrix U (qseed): arms with equal q_t query identical events.
    """
    t_start = time.perf_counter()
    r, prox, r0, pmax = _chan(stream, cfg.risk)
    S, T = r.shape
    rT, pT = np.ascontiguousarray(r.T), np.ascontiguousarray(prox.T)
    need_cost = cfg.gate_w is not None or cfg.alloc == "growth_harm"
    if need_cost:
        rcT = np.ascontiguousarray(stream["loss"].T)
        pcT = np.ascontiguousarray(stream["proxy_cost"].T)
        r0c = stream["r0"]["cost"]
    U = np.random.default_rng(10_000 + qseed).random((T, S))
    D = (
        np.broadcast_to(np.asarray(delay), (S, T)).T
        if np.ndim(delay)
        else np.full((T, S), int(delay))
    )
    D = np.ascontiguousarray(D).astype(np.int64)
    d_fixed = int(delay) if not np.ndim(delay) else 0
    yT = np.ascontiguousarray(stream["y"].T) if "y" in stream else None
    scoreT = np.ascontiguousarray(stream["score"].T)
    grp_arr = stream.get(
        "group", stream["x"][..., 2] > 1.0 if stream["x"].shape[-1] > 2 else np.zeros((S, T), bool)
    )
    grpT = np.ascontiguousarray(grp_arr.T)
    lab_rare = np.zeros(S)
    pi_g = np.full(S, 0.2)
    pi_true = stream.get("pi_true")  # (S,T) true P(y=1|x) for oracle growth only
    piT = np.ascontiguousarray(pi_true.T) if (pi_true is not None and cfg.oracle_alt) else None

    qbase = (
        cfg.qmin if cfg.qmin > 0 else cfg.frac * (cfg.pace_floor if cfg.pacing != "none" else 0.25)
    )  # floor of non-uniform rules
    if cfg.alloc == "uniform" and cfg.pacing in ("none", "const"):
        qmin_eff = cfg.frac  # constant propensity: the exact floor
    elif cfg.alloc == "mix" and cfg.pacing == "none":
        u_min = max(cfg.mix[0], 0.5) if cfg.mix_mode == "conservative" else cfg.mix[0]
        qmin_eff = u_min * cfg.frac + (1.0 - u_min) * qbase
    else:
        qmin_eff = qbase
    qfloor = qbase

    NB = T + int(D.max()) + 3
    z = lambda: np.zeros((NB, S))
    BX, BX2, BN = z(), z(), z()  # moment buckets (by arrival time)
    BG = z() if cfg.gate_w else None
    rel_on = cfg.rel is not None
    if rel_on or cfg.alloc != "uniform" or cfg.pacing != "none":
        BL = {k: z() for k in ("w", "wr", "wp", "wrp", "wpp", "wrr", "n")}
    else:
        BL = None
    var_on = cfg.alloc != "uniform" or cfg.pacing in ("info_value", "reserve", "growth_pace")
    if var_on:
        BV = np.zeros((NB, K_BINS, S))
        BW = np.zeros((NB, K_BINS, S))
        BY = np.zeros((NB, K_BINS, S))
    BP = z()  # pending counter: +1 at issue, -1 at arrival (differences by bucket)
    Wrel = z()  # prefix-release log-factor buckets

    logW = np.zeros(S)
    lw_path = np.zeros((S, T), dtype=np.float32)
    rel_prev = np.zeros(S, dtype=np.int64)
    c1, c2, cn = np.zeros(S), np.zeros(S), np.zeros(S)
    g1, gn = np.zeros(S), np.zeros(S)
    gg = 1.0 - 1.0 / cfg.gate_w if cfg.gate_w else 1.0
    spent = np.zeros(S, dtype=np.int64)
    n_pending = np.zeros(S)
    pend_sum, pend_max = np.zeros(S), np.zeros(S)
    arr_last = np.zeros(S)
    arr_sum, arr_cnt = np.zeros(S), np.zeros(S)
    first = np.full(S, T, dtype=np.int64)
    exhaust_t = np.full(S, T, dtype=np.int64)
    # reliability state
    gam_r = 1.0 - 1.0 / cfg.rel_window
    rs = {k: np.zeros(S) for k in ("w", "wr", "wp", "wrp", "wpp", "wrr", "n")}
    th_s = np.ones(S)
    skill_s = np.ones(S)
    # variance / growth state
    gam_v = 0.995
    vV, vW, vY = np.zeros((K_BINS, S)), np.zeros((K_BINS, S)), np.zeros((K_BINS, S))
    ew_score = np.full(S, np.nan)
    ew_cost_exc = np.zeros(S)
    ar = np.arange(S)

    KL = cfg.lrv_lags
    lag_buf, c_lag = np.zeros((KL, S)), np.zeros((KL, S))
    wk = (1.0 - np.arange(1, KL + 1) / (KL + 1.0))[:, None]
    for t in range(T):
        # ----- absorb arrivals strictly before t into moment / reliability / variance states
        if t > 0:
            a = t - 1
            c1 = (cfg.gamma ** BN[a]) * c1 + BX[a] if cfg.gamma < 1 else c1 + BX[a]
            c2 = (cfg.gamma ** BN[a]) * c2 + BX2[a] if cfg.gamma < 1 else c2 + BX2[a]
            cn = (cfg.gamma ** BN[a]) * cn + BN[a] if cfg.gamma < 1 else cn + BN[a]
            if cfg.gate_w:
                g1 = (gg ** BN[a]) * g1 + BG[a]
                gn = (gg ** BN[a]) * gn + BN[a]
            if BL is not None:
                kk = BL["n"][a]
                disc = gam_r**kk
                for k, v in rs.items():
                    rs[k] = disc * v + BL[k][a]
            if var_on:
                vV = gam_v * vV + BV[a]
                vW = gam_v * vW + BW[a]
                vY = gam_v * vY + BY[a]
            n_pending = n_pending + BP[a]
            if cfg.lrv:
                xn, has = BX[a], BN[a] > 0
                c_lag = (cfg.gamma if cfg.gamma < 1 else 1.0) * c_lag + np.where(
                    has, xn * lag_buf, 0.0
                )
                lag_buf = np.where(has, np.vstack([xn, lag_buf[:-1]]), lag_buf)
        # ----- predictable bet quantities
        mean = c1 / (cn + 1.0)
        second = c2 / (cn + 1.0)
        if cfg.lrv:
            vif = np.clip(
                (second + 2.0 * (wk * c_lag).sum(0) / (cn + 1.0)) / np.maximum(second, 1e-12),
                1.0,
                20.0,
            )
            second = second * vif
        lam_raw = np.where(second > 0, np.maximum(mean, 0.0) / np.maximum(second, 1e-12), 0.0)
        # reliability weight theta_t
        theta = np.ones(S)
        bet_scale = np.ones(S)
        if rel_on:
            sw = np.maximum(rs["w"], 1e-9)
            mr, mp = rs["wr"] / sw, rs["wp"] / sw
            var_p = np.maximum(rs["wpp"] / sw - mp**2, 1e-12)
            var_r = np.maximum(rs["wrr"] / sw - mr**2, 1e-12)
            cov = rs["wrp"] / sw - mr * mp
            mse = rs["wrr"] / sw - 2 * rs["wrp"] / sw + rs["wpp"] / sw
            skill_raw = 1.0 - mse / var_r
            th_raw = np.clip(cov / var_p, 0.0, 1.0)
            ok_n = rs["n"] >= 8
            skill_s = np.where(
                ok_n, cfg.rel_smooth * skill_s + (1 - cfg.rel_smooth) * skill_raw, 1.0
            )
            th_s = np.where(ok_n, cfg.rel_smooth * th_s + (1 - cfg.rel_smooth) * th_raw, 1.0)
            if cfg.rel_score == "skill":
                unreliable = ok_n & (skill_s <= 0.0)
            else:
                bias = np.abs(mr - mp) / np.sqrt(var_r)
                unreliable = ok_n & (bias > 0.5)
            if cfg.rel == "hard":
                th_gate = np.ones(S)
            elif cfg.rel == "soft":
                th_gate = th_s
            else:  # 'unc'
                th_gate = th_s * rs["n"] / (rs["n"] + 20.0)
                th_gate = np.where(ok_n, th_gate, 1.0)
            fb_theta = 1.0 if cfg.rel_fallback == "none" else 0.0
            theta = np.where(unreliable, fb_theta, th_gate)
            if cfg.rel_fallback == "conservative_bet":
                bet_scale = np.where(unreliable, 0.5, 1.0)
        # ----- query probability
        pt = pT[t]
        sc = scoreT[t]
        b_idx = _bins(pt, pmax) if var_on else None
        q = np.full(S, cfg.frac)
        if var_on:
            nb = 5.0
            vbar = np.where(vW.sum(0) > 0, vV.sum(0) / np.maximum(vW.sum(0), 1e-9), 0.25 * 0.25)
            vb = (vV[b_idx, ar] + nb * vbar) / (vW[b_idx, ar] + nb)
            s_var = np.sqrt(np.maximum(vb, 1e-12))
            s_g = s_var
            if (
                cfg.alloc.startswith("growth")
                or cfg.alloc in ("mix", "bal_growth")
                or cfg.pacing == "growth_pace"
            ):
                s_g = _growth_score(
                    cfg,
                    pt,
                    b_idx,
                    vY,
                    vW,
                    ar,
                    lam_raw,
                    pmax,
                    r0,
                    sc,
                    piT[t] if piT is not None else None,
                    cfg.risk,
                )
                if cfg.alloc in ("growth_harm",):
                    s_g = s_g * (1.0 + 4.0 * np.maximum(ew_cost_exc, 0.0))
                if cfg.alloc == "growth_look":
                    urg = np.exp(-np.maximum(LOG_THR - logW, 0.0) / 1.0)
                    s_g = s_g * (0.5 + urg)
            ref = {"variance": s_var, "mix": s_var}.get(cfg.alloc, s_g)
            if cfg.pacing in ("info_value", "reserve", "growth_pace") and cfg.alloc == "uniform":
                ref = s_g if cfg.pacing == "growth_pace" else s_var
            ew_score = np.where(np.isnan(ew_score), ref, ew_score)
            rel_sc = ref / np.maximum(ew_score, 1e-12)
            q_one = np.clip(cfg.frac * rel_sc, qfloor, 1.0)
            if cfg.alloc == "mix":
                qv = np.clip(
                    cfg.frac * (s_var / np.maximum(_upd_ew(ew_score, s_var, 0), 1e-12)), qfloor, 1.0
                )
                qg = np.clip(
                    cfg.frac * (s_g / np.maximum(_upd_ew(ew_score, s_g, 0), 1e-12)), qfloor, 1.0
                )
                u_, v_, g_ = cfg.mix
                if cfg.mix_mode == "adaptive":
                    ntot = vW.sum(0)
                    conf = ntot / (ntot + 50.0)
                    v_, g_ = v_ * conf, g_ * conf
                    u_ = 1.0 - v_ - g_
                elif cfg.mix_mode == "conservative":
                    u_ = max(u_, 0.5)
                    s_ = v_ + g_
                    v_, g_ = (v_ / s_ * (1 - u_), g_ / s_ * (1 - u_)) if s_ > 0 else (0.0, 0.0)
                q_one = u_ * cfg.frac + v_ * qv + g_ * qg
            if cfg.alloc in ("balanced", "bal_growth"):
                w_g = np.where(
                    grpT[t], 1.0 / np.maximum(pi_g, 0.01), 1.0 / np.maximum(1.0 - pi_g, 0.01)
                )
                q_bal = np.clip(
                    cfg.frac * w_g / 2.0, qfloor, 1.0
                )  # equal expected label counts per group
                q_one = (
                    q_bal
                    if cfg.alloc == "balanced"
                    else 0.5 * q_bal
                    + 0.5 * np.clip(cfg.frac * s_g / np.maximum(ew_score, 1e-12), qfloor, 1.0)
                )
                pi_g = 0.995 * pi_g + 0.005 * grpT[t]
            if cfg.alloc != "uniform":
                q = q_one
            ew_score = 0.995 * ew_score + 0.005 * ref
        # budget pacing
        if cfg.budget is not None or cfg.pacing != "none":
            B = cfg.budget if cfg.budget is not None else round(cfg.frac * T)
            rem = np.maximum(B - spent, 0)
            left = max(T - t, 1)
            base = rem / left
            p = cfg.pacing
            if p == "const":
                q = np.full(S, B / T)
            elif p == "remaining":
                q = np.clip(base, 0.0, 1.0)
            elif p == "info_value" or p == "growth_pace":
                q = np.clip(
                    base * (q / max(cfg.frac, 1e-9) if cfg.alloc != "uniform" else rel_sc), 0.0, 1.0
                )
            elif p == "reserve":
                hi_m, lo_m = (3.0, 0.25) if cfg.pace_floor < 0.5 else (2.0, cfg.pace_floor)
                q_hi, q_lo = np.minimum(1.0, hi_m * base), lo_m * base
                q = np.where(rel_sc >= 1.0, q_hi, q_lo)
            elif p == "two_stage":
                frac_t = t / T
                tgt_spent = 0.3 * B if frac_t < 0.25 else B
                need = (tgt_spent - spent) / max((0.25 * T - t) if frac_t < 0.25 else left, 1)
                q = np.clip(need, 0.0, 1.0)
            if cfg.budget is not None:
                q = np.where(spent < cfg.budget, q, 0.0)
        if cfg.pacing != "none" or cfg.alloc != "uniform":
            # inclusion probability is either 0 (inactive event) or at least qmin_eff, so the sup cap is valid
            q = np.where(q > 0, np.maximum(q, qmin_eff), 0.0)
        # ----- query decision with common random numbers (inclusion prob = q, charged at issue)
        active = q > 0
        Q = (U[t] < q) & active
        if cfg.budget is not None:
            Q = Q & (spent < cfg.budget)
            newly = Q & (spent + 1 >= cfg.budget)
            exhaust_t = np.where(newly & (exhaust_t == T), t, exhaust_t)
        spent = spent + Q
        lab_rare += Q & grpT[t]
        qs = np.where(active, q, 1.0)
        # ----- increment
        rt = rT[t]
        X = theta * pt + (Q / qs) * (rt - theta * pt) - r0 - cfg.tol
        X = np.where(active, X, 0.0)
        if cfg.cap_mode == "x":
            bound = theta * pt * (1.0 / qs - 1.0) + r0 + cfg.tol
        else:
            bound = theta * pmax * (1.0 / max(qmin_eff, 1e-9) - 1.0) + r0 + cfg.tol
        bound = np.maximum(bound, 1e-9)
        lam = (
            cfg.cap / bound if cfg.force_bet else np.minimum(lam_raw, cfg.cap / bound)
        ) * bet_scale
        if cfg.gate_w:
            gmean = g1 / (gn + 1.0)
            lam = lam * (gmean > 0)
        lam = np.where(active, lam, 0.0)
        logf = np.log1p(lam * X)
        # ----- arrival times
        queried_delay = D[t]
        if cfg.unq_delay:
            arr = t + queried_delay
        else:
            arr = t + np.where(Q, queried_delay, 0)
        arr = np.minimum(arr, NB - 2)
        # moments bucket (arrival time of this event's increment)
        BX[arr, ar] += X
        BX2[arr, ar] += X * X
        BN[arr, ar] += 1.0
        if cfg.gate_w:
            Xc = pcT[t] + (Q / qs) * (rcT[t] - pcT[t]) - r0c - cfg.tol
            BG[arr, ar] += np.where(active, Xc, 0.0)
        if BL is not None and Q.any():
            w = np.where(Q, 1.0 / qs, 0.0)
            e = rt
            for k, v in (
                ("w", w),
                ("wr", w * e),
                ("wp", w * pt),
                ("wrp", w * e * pt),
                ("wpp", w * pt * pt),
                ("wrr", w * e * e),
                ("n", Q.astype(float)),
            ):
                BL[k][arr, ar] += v
        if var_on and Q.any():
            w = np.where(Q, 1.0 / qs, 0.0)
            BV[arr, b_idx, ar] += w * (rt - pt) ** 2
            BW[arr, b_idx, ar] += w
            if yT is not None:
                BY[arr, b_idx, ar] += w * yT[t]
        if cfg.gate_w or cfg.alloc == "growth_harm":
            ew_cost_exc = 0.99 * ew_cost_exc + 0.01 * (pcT[t] + (Q / qs) * (rcT[t] - pcT[t]) - r0c)
        # pending bookkeeping: +1 now, -1 at arrival
        BP[arr, ar] -= Q.astype(float) * (arr > t)
        n_pending = n_pending + Q * (arr > t)
        pend_sum += n_pending
        pend_max = np.maximum(pend_max, n_pending)
        arr_sum += np.where(Q, arr - t, 0)
        arr_cnt += Q
        arr_last = np.maximum(arr_last, np.where(Q, arr, 0))
        # ----- wealth release
        if cfg.release == "legacy":
            rel = np.minimum(t + d_fixed, NB - 2) * np.ones(S, dtype=np.int64)
        elif cfg.release == "arrived":
            rel = arr
        else:  # prefix
            rel = np.maximum(rel_prev, arr)
            rel_prev = rel
        Wrel[np.minimum(rel, NB - 2), ar] += logf
        logW = logW + Wrel[t]
        lw_path[:, t] = logW
        hit = (logW >= LOG_THR) & (first == T)
        first = np.where(hit, t, first)

    return {
        "alarm": first,
        "labels": spent,
        "logW": lw_path,
        "mean_pending": pend_sum / T,
        "max_pending": pend_max,
        "mean_label_delay": arr_sum / np.maximum(arr_cnt, 1),
        "last_label_arrival": arr_last,
        "exhaust_t": exhaust_t,
        "labels_rare": lab_rare,
        "runtime_s": time.perf_counter() - t_start,
    }


def run_mixture(stream: dict, cfgs: list, delay=5, qseed: int = 0) -> dict:
    """Equal-weight mixture of e-processes sharing one query matrix: an average of test supermartingales is one."""
    runs = [run(stream, c, delay=delay, qseed=qseed) for c in cfgs]
    W = np.mean([np.exp(r["logW"].astype(float)) for r in runs], 0)
    logW = np.log(np.maximum(W, 1e-300))
    hit = logW >= LOG_THR
    alarm = np.where(hit.any(1), hit.argmax(1), logW.shape[1])
    return {**runs[0], "logW": logW, "alarm": alarm, "runtime_s": sum(r["runtime_s"] for r in runs)}


def _upd_ew(ew, s, _):
    return 0.995 * ew + 0.005 * s


def _growth_score(cfg, pt, b_idx, vY, vW, ar, lam_raw, pmax, r0, score, pi_oracle, risk):
    """Value of labelling the current event: log-growth at q=1 minus at q=frac, two-point loss model.

    The conditional label law P(y=1|x) is estimated from resolved labels (bins of the proxy), shrunk toward
    the deployed model's own score. With ``oracle_alt`` the true law is used (evaluator information; used only
    to measure the cost of estimating the alternative).
    """
    n0 = 5.0
    if pi_oracle is not None:
        pi = pi_oracle
    else:
        pi = (vY[b_idx, ar] + n0 * score) / (vW[b_idx, ar] + n0)
    pi = np.clip(pi, 1e-3, 1 - 1e-3)
    if risk == "cost":
        act = (score >= FP / (FP + FN)).astype(float)
        a0, a1 = act * FP, (1 - act) * FN  # loss if y=0 / y=1
    else:
        a0, a1 = score**2, (1 - score) ** 2
    lam = np.maximum(
        lam_raw, 0.25 * cfg.cap / max(pmax * (1.0 / max(cfg.frac, 1e-9) - 1.0) + r0, 1e-9)
    )

    def growth(qv):
        x0 = pt - r0 - cfg.tol
        out = 0.0
        for prob, a in ((1 - pi, a0), (pi, a1)):
            x1 = pt + (a - pt) / qv - r0 - cfg.tol
            out = out + prob * (
                qv * np.log1p(np.maximum(lam * x1, -0.9))
                + (1 - qv) * np.log1p(np.maximum(lam * x0, -0.9))
            )
        return out

    gain = growth(1.0) - growth(cfg.frac)
    return np.sqrt(np.maximum(gain, 1e-12))


def alarm_stats(alarm: np.ndarray, truth: dict, T: int) -> dict:
    """Per-seed false-alarm / detection / cumulative-harm records against evaluator-side truth.

    truth['harm'] is (T,) or (S, T); a step is harmful when ``harm >= truth['thr']``.
    """
    S = len(alarm)
    harm = np.broadcast_to(truth["harm"], (S, T))
    harmful = harm >= truth.get("thr", 0.10)
    anyh = harmful.any(1)
    first_harm = np.where(anyh, harmful.argmax(1), T)
    fired = alarm < T
    cum = np.cumsum(np.maximum(harm, 0.0), 1)
    idx = np.minimum(alarm, T - 1)
    return {
        "first_harm": first_harm,
        "false_alarm": fired & (alarm < first_harm),
        "detected": fired & (alarm >= first_harm) & anyh,
        "harm_before": cum[np.arange(S), idx],
        "delay": np.where(fired & (alarm >= first_harm) & anyh, alarm - first_harm, -1),
    }
