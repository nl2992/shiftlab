"""Registered causal-cut incumbent root-mixture diagnostic."""

from __future__ import annotations

import hashlib
import json
import time
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from cut_certificate_helpers import exact_costs, exact_payoff, game_for, null_cut
from mixture_incumbent_helpers import candidates_for_pair, component_policy, mixture_policy
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, vstack
from verify_cut_certificate import verify

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/risk_preserving_approx"
TARGET = OUT / "mixture_incumbent_t7_v1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if TARGET.exists():
        raise FileExistsError(f"Refusing to overwrite {TARGET}")
    prior_path = OUT / "causal_cut_certificate_t7_v1.json"
    verify(prior_path)
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    lower = F(prior["certificate"]["lower"])
    game = game_for(7)
    emat, erhs = game.learner.matrix()
    fmat, frhs = game.opponent.matrix()
    costs = exact_costs(game)
    payoff = exact_payoff(game)
    keys = list(payoff)
    a = coo_matrix(
        ([float(payoff[k]) for k in keys], ([k[0] for k in keys], [k[1] for k in keys])),
        shape=(game.learner.count, game.opponent.count),
    ).tocsr()
    objective = np.array([float(x) for x in costs])
    options = {
        "time_limit": 60.0,
        "primal_feasibility_tolerance": 1e-9,
        "dual_feasibility_tolerance": 1e-9,
    }
    safe_policy = component_policy(game, None)
    safe_cost = sum(game.expected_metrics(safe_policy)[:3])
    candidates = [{"risk": F(0), "cost": safe_cost, "records": None, "iteration": -1}]
    best = (safe_cost, 0, 0, F(1))
    old_best = safe_cost
    cuts = []
    signatures = set()
    trace = []
    status = "iteration_limit"
    for iteration in range(65):
        before = time.perf_counter()
        master = linprog(
            objective,
            A_ub=vstack([csr_matrix([list(map(float, c))]) for c in cuts]).tocsr()
            if cuts
            else None,
            b_ub=np.full(len(cuts), float(game.config.alpha)) if cuts else None,
            A_eq=emat,
            b_eq=erhs,
            bounds=(0, None),
            method="highs",
            options=options,
        )
        master_s = time.perf_counter() - before
        if not master.success:
            raise RuntimeError("Master failed: " + master.message)
        before = time.perf_counter()
        response = linprog(
            -(a.T @ master.x),
            A_eq=fmat,
            b_eq=frhs,
            bounds=(0, None),
            method="highs",
            options=options,
        )
        response_s = time.perf_counter() - before
        if not response.success:
            raise RuntimeError("Response failed: " + response.message)
        y = np.rint(response.x)
        if np.max(np.abs(response.x - y)) > 1e-8:
            raise ValueError("Non-integral null response")
        seq = [int(i) for i in np.flatnonzero(y)]
        cut = null_cut(game, payoff, seq)
        numerical_risk = float(np.dot(np.array([float(v) for v in cut]), master.x))
        policy, records = game.recover(master.x)
        risk = game.null_risk(policy)
        if abs(float(risk) - numerical_risk) > 1e-7:
            raise ValueError("Recovered risk differs from best response")
        cost = sum(game.expected_metrics(policy)[:3])
        component = {"risk": risk, "cost": cost, "records": records, "iteration": iteration}
        index = len(candidates)
        if risk <= game.config.alpha and cost < best[0]:
            best = (cost, index, index, F(1))
        for other, previous in enumerate(candidates):
            for weight, value in candidates_for_pair(component, previous, game.config.alpha):
                if value < best[0]:
                    best = (value, index, other, weight)
        candidates.append(component)
        activation = min(F(1), game.config.alpha / risk) if risk else F(1)
        old_best = min(old_best, activation * cost + (1 - activation) * safe_cost)
        if best[0] > old_best:
            raise AssertionError("Mixture failed to contain root-repair baseline")
        trace.append(
            {
                "iteration": iteration,
                "master_numeric": float(master.fun),
                "master_s": master_s,
                "response_s": response_s,
                "candidate_risk": str(risk),
                "candidate_cost": str(cost),
                "mixture_upper": str(best[0]),
                "old_repair_upper": str(old_best),
            }
        )
        if numerical_risk <= float(game.config.alpha) + 1e-9:
            status = "numerical_master_converged"
            break
        signature = tuple(seq)
        if signature in signatures:
            status = "duplicate_response"
            break
        if iteration == 64:
            break
        signatures.add(signature)
        cuts.append(cut)
    upper, i, j, weight = best
    first, second = candidates[i], candidates[j]
    bound = weight * first["risk"] + (1 - weight) * second["risk"]
    combined = mixture_policy(
        game,
        component_policy(game, first["records"]),
        component_policy(game, second["records"]),
        weight,
    )
    actual_risk = game.null_risk(combined)
    actual_cost = sum(game.expected_metrics(combined)[:3])
    if actual_risk > bound or bound > game.config.alpha or actual_cost != upper or lower > upper:
        raise ValueError("Mixture certificate cross-check failed")
    signed = {
        "horizon": 7,
        "first": first,
        "second": second,
        "weight": str(weight),
        "risk_bound": str(bound),
        "actual_risk": str(actual_risk),
        "cost": str(actual_cost),
        "prior_lower": str(lower),
        "gap": str(upper - lower),
        "prior_certificate_sha256": prior["certificate_sha256"],
    }

    def serial(obj):
        if isinstance(obj, F):
            return str(obj)
        raise TypeError(type(obj))

    canonical = json.dumps(signed, sort_keys=True, separators=(",", ":"), default=serial).encode()
    payload = {
        "certificate": signed,
        "certificate_sha256": hashlib.sha256(canonical).hexdigest(),
        "status": status,
        "cuts": len(cuts),
        "trace": trace,
        "source_sha256": sha(Path(__file__)),
        "helper_sha256": sha(ROOT / "scripts/research_risk_approx/mixture_incumbent_helpers.py"),
        "protocol_sha256": sha(OUT / "MIXTURE_INCUMBENT_PROTOCOL_V1.md"),
    }
    TARGET.write_text(json.dumps(payload, indent=2, default=serial) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "cuts": len(cuts),
                "first_iteration": first["iteration"],
                "second_iteration": second["iteration"],
                "weight": str(weight),
                "upper": float(upper),
                "old_upper": float(old_best),
                "actual_risk": float(actual_risk),
                "risk_bound": float(bound),
                "certified_gap": float(upper - lower),
            }
        )
    )


if __name__ == "__main__":
    main()
