"""C2 kill test: exact joint acquisition+switching vs independently optimised acquisition and switching.

Model (belief MDP, exact backward induction, hidden two-state Markov chain h_t in {0,1}; h=1 means the
challenger is better by +Delta per period, h=0 worse by Delta; incumbent per-period cost 1):
  per period t: choose query q (cost cq, at most B in total, one per period) and deployment d in {0,1}
  (1 = challenger), paying switch cost cs when d != previous deployment.  A query returns a binary signal of
  h_t with accuracy a, revealed immediately (delay D=0, before choosing d) or at the start of t+1 (D=1).
Arms (identical information, budget, horizon, costs):
  J    : joint closed-loop optimum (the standard belief-state DP; not a new algorithm)
  S_ol : best OPEN-LOOP query schedule (enumerated exhaustively) + optimal switching best response
  S_us : uncertainty sampling (query iff max(beta,1-beta) < kappa; kappa optimised) + optimal switching
  S_vo : myopic one-step value-of-information rule + optimal switching
  S_nq : no queries, optimal switching on the prior ; S_inc: always incumbent
Output: per-instance net expected cost (lower is better).  Classification label: DEVELOPMENT_ONLY (exact, toy).
"""
import itertools, json, sys
from functools import lru_cache
import numpy as np


def solve(T, Delta, cs, cq, B, rho, a, D, qrule=None, schedule=None):
    """Expected net cost under optimal switching given a query rule (None = optimise queries jointly)."""
    P = np.array([[rho, 1 - rho], [1 - rho, rho]])

    def prop(beta):  # P(h_{t+1}=1)
        return beta * P[1, 1] + (1 - beta) * P[0, 1]

    def post(beta, o):  # P(h=1 | signal o), plus P(o)
        l1 = a if o == 1 else 1 - a
        l0 = (1 - a) if o == 1 else a
        po = beta * l1 + (1 - beta) * l0
        return (beta * l1 / po if po > 0 else beta), po

    def rl(beta, d):  # expected deployment loss at belief beta
        return 1.0 if d == 0 else 1.0 - Delta * (2 * beta - 1)

    @lru_cache(maxsize=None)
    def V(t, dprev, b, beta):
        if t == T:
            return 0.0
        beta = round(beta, 12)
        # allowed query decisions
        if b == 0:
            qs = (0,)
        elif schedule is not None:
            qs = (1,) if (t in schedule) else (0,)
        elif qrule is not None:
            qs = (1,) if qrule(t, dprev, b, beta) else (0,)
        else:
            qs = (0, 1)
        best = np.inf
        for q in qs:
            if D == 0 and q == 1:
                val = cq
                for o in (0, 1):
                    pb, po = post(beta, o)
                    val += po * Wd(t, dprev, b - 1, pb)
            elif D == 0:
                val = Wd(t, dprev, b, beta)
            else:  # D == 1: decide with beta, signal arrives next period
                val = np.inf
                for d in (0, 1):
                    imm = rl(beta, d) + cs * (d != dprev) + cq * q
                    if q == 1:
                        cont = 0.0
                        for o in (0, 1):
                            pb, po = post(beta, o)
                            cont += po * V(t + 1, d, b - 1, prop(pb))
                    else:
                        cont = V(t + 1, d, b, prop(beta))
                    val = min(val, imm + cont)
            best = min(best, val)
        return best

    @lru_cache(maxsize=None)
    def Wd(t, dprev, b, beta):  # D==0: choose d after the (possible) signal
        return min(
            rl(beta, d) + cs * (d != dprev) + V1(t + 1, d, b, prop(beta)) for d in (0, 1)
        )

    def V1(t, d, b, beta):
        return V(t, d, b, round(beta, 12))

    return V(0, 0, B, 0.5)


def vo_rule(T, Delta, cs, cq, rho, a, D):
    """One-step value-of-information query rule (ignores future queries, horizon and remaining budget)."""
    def rule(t, dprev, b, beta):
        # myopic: compare deploying now with / without a signal for this period only
        def rl(bt, d): return 1.0 if d == 0 else 1.0 - Delta * (2 * bt - 1)
        def val(bt): return min(rl(bt, d) + cs * (d != dprev) for d in (0, 1))
        no = val(beta)
        yes = 0.0
        for o in (0, 1):
            l1 = a if o else 1 - a; l0 = (1 - a) if o else a
            po = beta * l1 + (1 - beta) * l0
            yes += po * val(beta * l1 / po)
        return (no - yes > cq) if D == 0 else (no - yes > cq and False)  # with D=1 one-step VOI is zero
    return rule


def instance(T, Delta, cs, cq, B, rho, a, D):
    J = solve(T, Delta, cs, cq, B, rho, a, D)
    # open loop: all schedules with <= B queries
    ol = min(solve(T, Delta, cs, cq, B, rho, a, D, schedule=frozenset(S))
             for k in range(0, B + 1) for S in itertools.combinations(range(T), k))
    us = min(solve(T, Delta, cs, cq, B, rho, a, D, qrule=(lambda t, dp, b, be, k=k: max(be, 1 - be) < k))
             for k in (0.55, 0.65, 0.75, 0.85, 0.95, 1.01))
    vo = solve(T, Delta, cs, cq, B, rho, a, D, qrule=vo_rule(T, Delta, cs, cq, rho, a, D))
    nq = solve(T, Delta, cs, cq, 0, rho, a, D)
    inc = float(T)
    return dict(T=T, Delta=Delta, cs=cs, cq=cq, B=B, rho=rho, a=a, D=D, J=J, S_ol=ol, S_us=us, S_vo=vo, S_nq=nq,
                S_inc=inc)


if __name__ == "__main__":
    rows = []
    T = 8
    for Delta, cs, cq, B, rho, a, D in itertools.product(
        (0.3, 0.6), (0.5, 1.5), (0.02, 0.1), (1, 2, 3), (0.8, 0.95), (0.75, 0.9), (0, 1)
    ):
        rows.append(instance(T, Delta, cs, cq, B, rho, a, D))
    json.dump(rows, open("research/novelty_validation_2026-10-30/outputs/x2_joint_vs_separate_dp.json", "w"), indent=1)
    import pandas as pd
    d = pd.DataFrame(rows)
    d["best_sep"] = d[["S_ol", "S_us", "S_vo", "S_nq", "S_inc"]].min(axis=1)
    d["best_sep_query_rules"] = d[["S_ol", "S_us", "S_vo"]].min(axis=1)
    d["gap"] = d.best_sep - d.J
    d["gap_vs_sep_query"] = d.best_sep_query_rules - d.J
    d["monotone_violation"] = (d.J > d[["S_ol", "S_us", "S_vo", "S_nq", "S_inc"]].min(axis=1) + 1e-9)
    print("instances", len(d), "violations of J<=separate:", int(d.monotone_violation.sum()))
    print("strict gap>1e-6:", int((d.gap > 1e-6).sum()), "gap>0.01:", int((d.gap > .01).sum()),
          "max gap", round(d.gap.max(), 4), "mean gap", round(d.gap.mean(), 4))
    print("relative to total net cost J: mean", round((d.gap / d.J).mean(), 4), "max", round((d.gap / d.J).max(), 4))
    print(d.groupby("D")[["gap"]].agg(["mean", "max"]).round(4))
    print(d.groupby("B")[["gap"]].agg(["mean", "max"]).round(4))
    print("who attains best separate:", d[["S_ol", "S_us", "S_vo", "S_nq", "S_inc"]].idxmin(axis=1).value_counts().to_dict())
    print("J strictly beats NO-query/incumbent (value of any querying) in", int((d[["S_nq", "S_inc"]].min(axis=1) - d.J > 1e-6).sum()))
