"""B3: certified policy distillation on small exact instances.

Teacher: exact FCG optimum (raw LP policy before root repair, behavioural) of the decomposed game.
Student: per (t, remaining budget) belief-threshold rule on pi = P(s_t = 1 | released labels):
    promote iff  sign * (pi - theta_P) >= 0 ;  otherwise query iff theta_lo <= pi <= theta_hi.
Fitted by exhaustive threshold search minimising alternative-reach-weighted disagreement with
the teacher's action probabilities.  The student is then certified EXACTLY (alt cost, full causal
null risk, root repair).  We also compute the standard coupling (disagreement) certificate
    R_rob(S) <= R_rob(T) + sup_nu P_nu(D),   |C(S) - C(T)| <= span * P_alt(D)
and compare its tightness and the state space it needs with direct student verification.

Usage: uv run --no-sync python scripts/paper4_continuation/theory_B/b3_distill.py
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from fractions import Fraction as F
from functools import cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from b_common import cell, describe, write_result  # noqa: E402

import shiftlab.paper4.frontier_cuts as fc  # noqa: E402
from shiftlab.paper4.frontier_cuts import (  # noqa: E402
    exact_costs,
    frontier_cut_generation,
    learner_only_game,
    realization_flow,
)

E20 = (F(1, 20), F(19, 20))
CAPTURED: dict = {}
_orig_mix = fc.mix_root_never_promote


def _capturing_mix(game, raw_policy, activation):
    CAPTURED["raw"] = raw_policy
    return _orig_mix(game, raw_policy, activation)


fc.mix_root_never_promote = _capturing_mix
CELLS = [
    ("C1", 5, 2, 1, F(1, 4), E20),
    ("C4", 6, 3, 1, F(1, 4), E20),
    ("C5", 8, 3, 1, F(1, 4), E20),
    ("C2", 5, 2, 1, F(9, 10), (F(1, 10), F(9, 10))),
    ("C3", 6, 3, 1, F(3, 4), E20),
]


def alt_pi(game, history, released):
    belief = game._belief_from_history(history, tuple(released))
    return sum(m for s, _, m in belief if s)


def collect(game, teacher):
    """Info sets with alt reach, features and teacher action probabilities."""
    rows = []

    def visit(history, outcomes, weight, posterior):
        t = len(history) + 1
        if t > game.config.horizon:
            return
        info = game.information(history, outcomes)
        probs = teacher(history, outcomes)
        choices = game.choices(history)
        rem = game.config.budget - sum(q for _, q in history)
        rows.append((t, rem, alt_pi(game, *info), weight, dict(zip(choices, probs, strict=True))))
        state1 = game.model.propagate(posterior, 1)
        pos = game.model.emission(state1)
        for (a, q), pr in zip(choices, probs, strict=True):
            if a or not pr:
                continue
            nh = history + ((a, q),)
            if q:
                for y, py in ((0, 1 - pos), (1, pos)):
                    lik = game.model.emission1 if y else 1 - game.model.emission1
                    visit(nh, outcomes + ((t, y),), weight * pr * py, state1 * lik / py)
            else:
                visit(nh, outcomes, weight * pr, state1)

    visit((), (), F(1), game.model.prior1)
    return rows


def fit_student(rows):
    """Two-stage exhaustive fit: promotion threshold first, then query interval."""
    by = defaultdict(list)
    for t, rem, pi, w, probs in rows:
        by[t, rem].append((pi, w, probs))
    rule = {}
    for key, pts in by.items():
        cands = sorted({p for p, _, _ in pts} | {F(-1), F(2)})
        best = None
        for sign in (1, -1):
            for tp in cands:
                # v3: support distillation -- target is "teacher promotes with positive
                # probability" (a randomised optimum mixes; repair restores alpha later).
                loss = sum(w * ((sign * (pi - tp) >= 0)
                                != any(v > 0 for (a, _), v in probs.items() if a))
                           for pi, w, probs in pts)
                if best is None or loss < best[0]:
                    best = (loss, sign, tp)
        _, sign, tp = best
        rest = [(pi, w, probs) for pi, w, probs in pts if sign * (pi - tp) < 0]
        bq = None
        for lo in cands:
            for hi in cands:
                if hi < lo:
                    continue
                loss = F(0)
                for pi, w, probs in rest:
                    q = 1 if (lo <= pi <= hi and key[1] > 0) else 0
                    # support target for queries as well (randomised root of the teacher)
                    loss += w * (q != (probs.get((0, 1), F(0)) > 0))
                if bq is None or loss < bq[0]:
                    bq = (loss, lo, hi)
        rule[key] = (sign, tp, bq[1], bq[2])
    return rule


def student_policy(game, rule):
    def policy(history, outcomes):
        t = len(history) + 1
        rem = game.config.budget - sum(q for _, q in history)
        info = game.information(history, outcomes)
        choices = game.choices(history)
        sign, tp, lo, hi = rule.get((t, rem), (1, F(2), F(2), F(-1)))
        pi = alt_pi(game, *info)
        if sign * (pi - tp) >= 0:
            act = (1, 0)
        else:
            act = (0, 1 if (lo <= pi <= hi and rem > 0) else 0)
        return tuple(F(c == act) for c in choices)

    return policy


def cost_of(game, costs, policy):
    flow = realization_flow(game, policy)
    return sum(c * x for c, x in zip(costs, flow, strict=True))


def disagreement(game, teacher, student, causal):
    """sup_nu (causal) or alt-law probability that the teacher's realised action differs from
    the student's before promotion (teacher randomisation coupled independently)."""
    cfg = game.config

    @cache
    def visit(history, outcomes, posterior):
        t = len(history) + 1
        if t > cfg.horizon:
            return F(0)
        choices = game.choices(history)
        tp = dict(zip(choices, teacher(history, outcomes), strict=True))
        sp = student(history, outcomes)
        act = choices[sp.index(F(1))]
        agree = tp.get(act, F(0))
        val = 1 - agree
        a, q = act
        if a or not agree:
            return val
        nh = history + (act,)
        state1 = game.model.propagate(posterior, 1) if posterior is not None else None
        if q:
            if causal:
                v0 = visit(nh, outcomes + ((t, 0),), None)
                v1 = visit(nh, outcomes + ((t, 1),), None)
                cont = max(v0, (v0 + v1) / 2)
            else:
                pos = game.model.emission(state1)
                cont = F(0)
                for y, py in ((0, 1 - pos), (1, pos)):
                    lik = game.model.emission1 if y else 1 - game.model.emission1
                    cont += py * visit(nh, outcomes + ((t, y),), state1 * lik / py)
        else:
            cont = visit(nh, outcomes, state1)
        return val + agree * cont

    return visit((), (), None if causal else game.model.prior1)


def main():
    out = {"purpose": "B3 certified distillation: belief-threshold students vs exact teacher",
           "cells": []}
    for cid, T, B, d, tr, em in CELLS:
        t0 = time.perf_counter()
        config, model = cell(T, B, d, tr, em)
        CAPTURED.clear()
        fcg = frontier_cut_generation(config, model)
        game = learner_only_game(config, model)
        costs = exact_costs(game)
        # v2: distil the RAW (pre-repair) teacher component; v1 distilled the root-randomised
        # repaired teacher and every student collapsed to never-promote (recorded in v1 JSON).
        teacher = CAPTURED.get("raw", fcg["policy"])
        v_star = fcg["U"]
        rows = collect(game, teacher)
        rule = fit_student(rows)
        student = student_policy(game, rule)
        c_s = cost_of(game, costs, student)
        r_s = game.null_risk(student)
        never = lambda h, o: tuple(F(c == (0, 0)) for c in game.choices(h))  # noqa: E731
        c_n = cost_of(game, costs, never)
        act = min(F(1), config.alpha / r_s) if r_s else F(1)
        u_s = act * c_s + (1 - act) * c_n
        c_t = cost_of(game, costs, teacher)
        r_t = game.null_risk(teacher)
        p_alt_d = disagreement(game, teacher, student, causal=False)
        p_nu_d = disagreement(game, teacher, student, causal=True)
        span = max(costs) - min(costs)
        rec = {"id": cid, "config": describe(config, model), "Vstar": v_star,
               "teacher_cost": c_t, "teacher_causal_risk": r_t,
               "student_cost": c_s, "student_causal_risk": r_s,
               "student_iid_risk": game.null_risk(student, iid_boundary=True),
               "student_repaired_U": u_s, "student_gap_to_Vstar": u_s - v_star,
               "student_rule_cells": len(rule),
               "coupling_P_alt_D": p_alt_d, "coupling_sup_nu_P_D": p_nu_d,
               "coupling_risk_bound": r_t + p_nu_d,
               "coupling_cost_bound_halfwidth": span * p_alt_d,
               "actual_cost_diff": c_s - c_t,
               "teacher_tree_infosets": len(game.learner.infos),
               "seconds": time.perf_counter() - t0}
        out["cells"].append(rec)
        print(cid, float(v_star), float(u_s), float(r_s), float(r_t), float(p_nu_d),
              float(p_alt_d), float(c_s - c_t), round(rec["seconds"], 1), flush=True)
    write_result("b3_distillation_v4.json", out, Path(__file__))


if __name__ == "__main__":
    main()
