"""Check (b): independent exact optimum of the budgeted promotion game (delay 1) by LP over the learner's
FULL sequence-form tree (pre- and post-promotion decisions, no first-promotion decomposition, no belief
or risk-budget state), compared with RB-DP (risk_budget_dp_fast, lattice_exact=True).

Method E (enumeration): one explicit risk row per reduced deterministic null (p in {0,1/2} at each
  reachable query node), used when the number of reduced nulls is <= 40000.
Method D (dual): the null's best response over p in [0,1/2] written as its sequence-form LP dual
  (von Stengel); used on every cell.
IID: single row with p = 1/2 everywhere.
"""
from __future__ import annotations

import json
import sys
import time
from fractions import Fraction as F

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, csr_matrix, hstack, vstack

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import Cell  # noqa: E402


class Tree:
    def __init__(self, cell: Cell):
        self.cell = cell
        self.nseq = 1  # sequence 0 = empty
        self.infos = []  # (parent_seq, children seqs)
        self.cost = {}
        self.first_promo = []  # (seq, pre-promotion public path of (q, y) with q=1 only labels)
        self._build((), 0, F(1), cell.beta1, 0, cell.B, True, ())

    def _build(self, hist, parent, altp, b, old, n, prepromo, labels):
        c = self.cell
        t = len(hist) + 1
        if t > c.T:
            return
        choices = [(a, q) for a in (0, 1) for q in ((0, 1) if n else (0,))]
        kids = list(range(self.nseq, self.nseq + len(choices)))
        self.nseq += len(choices)
        self.infos.append((parent, kids))
        p = c.pos(b)
        for (a, q), s in zip(choices, kids):
            stage = (p if a == 0 else 1 - p) + c.c * q + c.k * (a != old)
            self.cost[s] = altp * stage
            if prepromo and a == 1:
                self.first_promo.append((s, labels))
            pp = prepromo and a == 0
            if q:
                for y, py in ((0, 1 - p), (1, p)):
                    lab = labels + (((t, y),) if pp else ())
                    self._build(hist + ((a, q, y),), s, altp * py, c.prop(c.post(b, y)), a, n - 1, pp, lab)
            else:
                self._build(hist + ((a, q, None),), s, altp, c.prop(b), a, n, pp, labels)

    def flow(self):
        rows, cols, vals = [0], [0], [1.0]
        for i, (par, kids) in enumerate(self.infos, start=1):
            rows += [i] * (1 + len(kids))
            cols += [par] + kids
            vals += [-1.0] + [1.0] * len(kids)
        E = coo_matrix((vals, (rows, cols)), shape=(len(self.infos) + 1, self.nseq)).tocsr()
        e = np.zeros(E.shape[0])
        e[0] = 1
        return E, e


def public_query_nodes(cell: Cell):
    """Pre-promotion public nodes where a query can be made: (labels so far as ((time,y),...), t)."""
    # A pre-promotion public node is determined by the query times and labels so far; the learner's
    # history also records no-query steps, so identify node by full step list.
    out = []

    def walk(steps):
        t = len(steps) + 1
        if t > cell.T:
            return
        nq = sum(1 for s in steps if s is not None)
        if nq < cell.B:
            out.append(steps)
            walk(steps + (0,))
            walk(steps + (1,))
        walk(steps + (None,))

    walk(())
    return out


def risk_coeff_for_null(tree: Tree, pfun):
    """pfun(node_steps) -> p. Returns dict seq -> P_null(labels on path)."""
    coef = {}
    for s, labels in tree.first_promo:
        pr = F(1)
        # reconstruct the public step list prefix at each query: needs the step structure; labels are
        # (time, y); the public steps before time t are: label at query times, None elsewhere.
        qt = dict(labels)
        for (t, y) in labels:
            steps = tuple(qt.get(u) for u in range(1, t))
            p = pfun(steps)
            pr *= p if y else 1 - p
            if pr == 0:
                break
        if pr:
            coef[s] = coef.get(s, 0) + float(pr)
    return coef


def reduced_nulls(cell: Cell, limit: int):
    """All reduced deterministic nulls as dicts node->p, or None if more than limit."""

    def strategies(steps):
        t = len(steps) + 1
        if t > cell.T:
            return [dict()]
        nq = sum(1 for s in steps if s is not None)
        base = strategies(steps + (None,))
        if nq >= cell.B:
            return base
        s0 = strategies(steps + (0,))
        s1 = strategies(steps + (1,))
        opts = [{**d, steps: F(0)} for d in s0]
        opts += [{**a, **b, steps: F(1, 2)} for a in s0 for b in s1]
        if len(base) * len(opts) > limit:
            raise OverflowError
        return [{**a, **b} for a in base for b in opts]

    try:
        return strategies(())
    except OverflowError:
        return None


def solve_lp(tree: Tree, risk_rows, alpha, dual=None):
    E, e = tree.flow()
    nx = tree.nseq
    obj = np.zeros(nx)
    for s, v in tree.cost.items():
        obj[s] = float(v)
    if dual is None:
        R = np.zeros((len(risk_rows), nx))
        for i, row in enumerate(risk_rows):
            for s, v in row.items():
                R[i, s] = v
        R = np.unique(np.round(R, 15), axis=0)
        res = linprog(obj, A_ub=R, b_ub=np.full(R.shape[0], float(alpha)), A_eq=E, b_eq=e,
                      bounds=[(0, None)] * nx, method="highs",
                      options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10})
        assert res.success, res.message
        return res.fun, R.shape[0]
    A, Fm, ny = dual  # A: (nx, ny) payoff, Fm: null flow matrix
    nv = Fm.shape[0]
    c = np.r_[obj, np.zeros(nv)]
    # A^T x - F^T v <= 0 ; v_0 <= alpha
    top = hstack([A.T, -Fm.T])
    bot = hstack([csr_matrix((1, nx)), csr_matrix(([1.0], ([0], [0])), shape=(1, nv))])
    Aub = vstack([top, bot]).tocsr()
    bub = np.r_[np.zeros(ny), float(alpha)]
    Aeq = hstack([E, csr_matrix((E.shape[0], nv))]).tocsr()
    res = linprog(c, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=e,
                  bounds=[(0, None)] * nx + [(None, None)] * nv, method="highs",
                  options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10})
    assert res.success, res.message
    return res.fun, ny


def null_sequence_form(tree: Tree, cell: Cell):
    """Null sequences: (node, p) for p in {0, 1/2}; mixtures give every p in [0, 1/2]."""
    seqs = {}
    infos = []
    count = 1

    # parent_of must also be defined for no-query successors: fill lazily
    def walk2(steps, ptuple, par):
        nonlocal count
        t = len(steps) + 1
        if t > cell.T:
            return
        nq = sum(1 for s in steps if s is not None)
        walk2(steps + (None,), ptuple, par)
        if nq < cell.B:
            kids = []
            for p in (F(0), F(1, 2)):
                seqs[(steps, ptuple + (p,))] = count
                kids.append(count)
                count += 1
            infos.append((par, kids))
            for p, k in zip((F(0), F(1, 2)), kids):
                for y in ((0,) if p == 0 else (0, 1)):
                    walk2(steps + (y,), ptuple + (p,), k)

    walk2((), (), 0)
    ny = count
    rows, cols, vals = [0], [0], [1.0]
    for i, (par, kids) in enumerate(infos, start=1):
        rows += [i] * 3
        cols += [par] + kids
        vals += [-1.0, 1.0, 1.0]
    Fm = coo_matrix((vals, (rows, cols)), shape=(len(infos) + 1, ny)).tocsr()
    # payoff: first-promotion learner seq s with labels; for every p-tuple consistent with labels
    ar, ac, av = [], [], []
    for s, labels in tree.first_promo:
        qt = dict(labels)
        if not labels:
            ar.append(s); ac.append(0); av.append(1.0)
            continue
        # enumerate p tuples along the path's query nodes
        L = len(labels)
        for bits in range(2**L):
            ps = tuple(F(1, 2) if (bits >> i) & 1 else F(0) for i in range(L))
            pr = F(1)
            for (t, y), p in zip(labels, ps):
                pr *= p if y else 1 - p
            if pr == 0:
                continue
            tlast, ylast = labels[-1]
            steps = tuple(qt.get(u) for u in range(1, tlast))
            key = (steps, ps)
            ar.append(s); ac.append(seqs[key]); av.append(float(pr))
    A = coo_matrix((av, (ar, ac)), shape=(tree.nseq, ny)).tocsr()
    return A, Fm, ny


def exact_values(cell: Cell, enum_limit=40000):
    tree = Tree(cell)
    out = {"learner_seqs": tree.nseq}
    iid_row = risk_coeff_for_null(tree, lambda steps: F(1, 2))
    out["V_iid"], _ = solve_lp(tree, [iid_row], cell.alpha)
    dual = null_sequence_form(tree, cell)
    out["V_causal_dual"], out["null_seqs"] = solve_lp(tree, None, cell.alpha, dual=dual)
    nulls = reduced_nulls(cell, enum_limit)
    if nulls is not None:
        rows = [risk_coeff_for_null(tree, lambda st, d=d: d.get(st, F(0))) for d in nulls]
        out["V_causal_enum"], out["n_null_rows"] = solve_lp(tree, rows, cell.alpha)
        out["n_reduced_nulls"] = len(nulls)
    return out


def rbdp(cell: Cell, mode: str):
    from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, solve

    cfg = RBDPConfig(T=cell.T, B=cell.B, t01=float(cell.t01), t10=float(cell.t10), e0=float(cell.e0),
                     e1=float(cell.e1), prior1=float(cell.prior), c=float(cell.c), k=float(cell.k),
                     alpha=float(cell.alpha), mode=mode, n_beta=201, lattice_exact=True)
    r = solve(cfg)
    return {"L": r["L"], "U": r["U"], "risk_causal": r["risk_causal"], "risk_iid": r["risk_iid"]}


CELLS = {
    "anti9_T5B2_a.1": Cell(5, 2, F(9, 10), F(9, 10), F(1, 10), F(9, 10), alpha=F(1, 10)),
    "anti9_T5B2_a.2": Cell(5, 2, F(9, 10), F(9, 10), F(1, 10), F(9, 10), alpha=F(1, 5)),
    "anti9_T4B2_ck": Cell(4, 2, F(9, 10), F(9, 10), F(1, 10), F(9, 10), c=F(1, 100), k=F(1, 20), alpha=F(1, 10)),
    "asym_T4B2_a1/7": Cell(4, 2, F(2, 5), F(1, 20), F(1, 10), F(3, 5), prior=F(0), alpha=F(1, 7)),
    "t.75_T5B1_a3/20": Cell(5, 1, F(3, 4), F(3, 4), F(1, 5), F(4, 5), c=F(1, 100), k=F(1, 10), alpha=F(3, 20)),
    "anti_T3B2_a1/3": Cell(3, 2, F(4, 5), F(7, 10), F(1, 5), F(4, 5), prior=F(1, 3), c=F(1, 50), alpha=F(1, 3)),
    "antiasym_T5B2_a1/7": Cell(5, 2, F(17, 20), F(13, 20), F(3, 20), F(4, 5), prior=F(1, 3), c=F(1, 100),
                               k=F(1, 20), alpha=F(1, 7)),
    "persist_T5B2_a.1": Cell(5, 2, F(1, 4), F(1, 4), F(1, 10), F(9, 10), c=F(1, 200), k=F(1, 20), alpha=F(1, 10)),
    "anti9_T6B1_a.1": Cell(6, 1, F(9, 10), F(9, 10), F(1, 10), F(9, 10), alpha=F(1, 10)),
    "anti9_T4B3_a.2": Cell(4, 3, F(9, 10), F(9, 10), F(1, 10), F(9, 10), c=F(1, 100), alpha=F(1, 5)),
}

if __name__ == "__main__":
    results = {}
    for name, cell in CELLS.items():
        t0 = time.time()
        ex = exact_values(cell)
        rc, ri = rbdp(cell, "causal"), rbdp(cell, "iid")
        rec = {"exact": ex, "rbdp_causal": rc, "rbdp_iid": ri, "secs": time.time() - t0}
        rec["dU_causal"] = rc["U"] - ex["V_causal_dual"]
        rec["dL_causal"] = rc["L"] - ex["V_causal_dual"]
        rec["dU_iid"] = ri["U"] - ex["V_iid"]
        rec["dL_iid"] = ri["L"] - ex["V_iid"]
        rec["gamma_lp"] = ex["V_causal_dual"] - ex["V_iid"]
        if "V_causal_enum" in ex:
            rec["enum_minus_dual"] = ex["V_causal_enum"] - ex["V_causal_dual"]
        results[name] = rec
        print(name, json.dumps({k: (v if not isinstance(v, float) else float(f"{v:.3e}") if abs(v) < 1e-3 else round(v, 12))
                                for k, v in rec.items() if k not in ("exact", "rbdp_causal", "rbdp_iid")}))
        print("   exact", ex)
        print("   rbdp causal", rc, " iid", ri)
        sys.stdout.flush()
    with open(__file__.rsplit("/", 1)[0] + "/check_b_results.json", "w") as fh:
        json.dump(results, fh, indent=1, default=str)
