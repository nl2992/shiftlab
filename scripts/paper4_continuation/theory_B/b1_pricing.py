"""B1: exact multi-mode pricing DP with state counting, and policy-column generation.

Pricing problem for multipliers lam = (lam_iid, lam_1..lam_k) >= 0 and active pure
causal-null rows nu_1..nu_k (endpoint strategies keyed by full generated history):

    min_{deterministic learner policy p}  C_alt(p) + lam_iid R_iid(p) + sum_i lam_i R_nu_i(p)

This is a single-agent POMDP with a hidden root mode in {alt, iid, nu_1..nu_k}.  The
DP below runs over the public learner tree but memoises on a *candidate pricing key*:

    key = (t, remaining budget, alt belief over (regime, pending outcomes),
           rho = iid weight / alt weight,
           for each nu_i: {(pending generated outcomes, residual signature of nu_i, weight/alt)})

The residual signature is the Myhill-Nerode class of nu_i's future behaviour (hash-consed
subtree of its choices), i.e. the minimal automaton state of nu_i.  The script verifies
exactness of the merge (memoised value == un-memoised tree value) and counts distinct keys,
which is the state count a key-level DP would need.  The tree is a measuring device only.
"""

from __future__ import annotations

from fractions import Fraction as F

from b_common import HALF, initial_belief, positive, release


class Pricing:
    def __init__(self, game, nus=(), restrict_calendar=False, key_mode="full"):
        self.game = game
        self.cfg = game.config
        self.nus = list(nus)
        self.restrict = restrict_calendar
        self.key_mode = key_mode  # "full" | "alt_only" (belief-only key, used to show aliasing)
        self._sig_memo = [dict() for _ in self.nus]
        self._intern: dict = {}

    # ---------- residual signature of a null strategy (minimal automaton state) ----------
    def signature(self, i, history, outcomes):
        memo = self._sig_memo[i]
        key = (history, outcomes)
        if key in memo:
            return memo[key]
        t = len(history) + 1
        if t > self.cfg.horizon:
            sig = self._intern.setdefault(("end",), len(self._intern))
            memo[key] = sig
            return sig
        parts = []
        nu = self.nus[i]
        for a, q in self.game.choices(history):
            if a:
                parts.append(None)
                continue
            nh = history + ((a, q),)
            if q:
                p = nu.get((history, outcomes), HALF)
                parts.append((p, self.signature(i, nh, outcomes + ((t, 0),)),
                              self.signature(i, nh, outcomes + ((t, 1),))))
            else:
                parts.append(self.signature(i, nh, outcomes))
        tup = ("node", t, tuple(parts))
        sig = self._intern.setdefault(tup, len(self._intern))
        memo[key] = sig
        return sig

    def choices(self, history, rem):
        out = self.game.choices(history)
        if self.restrict:  # calendar: query whenever budget remains
            out = tuple(c for c in out if c[1] == (1 if rem else 0))
        return out

    def key(self, t, rem, belief, rho, nuw, history, released):
        if self.key_mode == "alt_only":
            return (t, rem, belief)
        parts = []
        for i, w in enumerate(nuw):
            parts.append(frozenset(
                (cfg, self.signature(i, history, tuple(sorted(released + cfg))), m)
                for cfg, m in w.items() if m))
        return (t, rem, belief, rho, tuple(parts))

    # ---------- the DP ----------
    def solve(self, lam, memoise=True):
        """Return (vector per alt unit at root, number of distinct keys, policy dict key->choice)."""
        self.lam = lam
        self.memo = {}
        self.policy = {}
        self.memoise = memoise
        self.calls = 0
        k = len(self.nus)
        vec = self._decide(1, self.cfg.budget, initial_belief(self.game), F(1),
                           tuple({(): F(1)} for _ in range(k)), (), ())
        return vec, len(self.memo), self.policy

    def _value(self, vec):
        return vec[0] + sum(l * r for l, r in zip(self.lam, vec[1:], strict=True))

    def _decide(self, t, rem, belief, rho, nuw, history, released):
        self.calls += 1
        key = self.key(t, rem, belief, rho, nuw, history, released)
        if self.memoise and key in self.memo:
            return self.memo[key]
        g, cfg = self.game, self.cfg
        best = None
        for a, q in self.choices(history, rem):
            if a:
                vec = (g._promote_value(t, rem, belief, q), rho,
                       *(sum(w.values(), F(0)) for w in nuw))
            else:
                stage = positive(g, belief) + cfg.query_cost * q
                vec = [stage] + [F(0)] * (1 + len(nuw))
                if t < cfg.horizon:
                    cont = self._advance(t, rem, belief, rho, nuw, history, released, q)
                    vec = [x + y for x, y in zip(vec, cont, strict=True)]
                vec = tuple(vec)
            if best is None or self._value(vec) < self._value(best[0]):
                best = (vec, (a, q))
        self.memo.setdefault(key, best[0])
        if key in self.policy and self.policy[key] != best[1] and self.memoise is False:
            pass
        self.policy.setdefault(key, best[1])
        return best[0]

    def _advance(self, t, rem, belief, rho, nuw, history, released, q):
        g = self.game
        nh = history + ((0, q),)
        nb = g._transition_belief(t, belief, q)
        new_nuw = []
        for i, w in enumerate(nuw):
            if not q:
                new_nuw.append(w)
                continue
            nw: dict = {}
            for cfg_, m in w.items():
                full = tuple(sorted(released + cfg_))
                p = self.nus[i].get((history, full), HALF)
                for y, py in ((0, 1 - p), (1, p)):
                    if py and m:
                        c2 = tuple(sorted(cfg_ + ((t, y),)))
                        nw[c2] = nw.get(c2, F(0)) + m * py
            new_nuw.append(nw)
        rel = release(g, t + 1, nb)
        if rel is None:
            return self._decide(t + 1, rem - q, nb, rho, tuple(new_nuw), nh, released)
        d, branches = rel
        d -= self.cfg.delay  # query event of the released label
        total = [F(0)] * (2 + len(nuw))
        for y, m_alt, bel in branches:
            w_next = []
            for w in new_nuw:
                nw = {}
                for cfg_, m in w.items():
                    if (d, y) in cfg_:
                        c2 = tuple(i for i in cfg_ if i != (d, y))
                        nw[c2] = nw.get(c2, F(0)) + m / m_alt
                w_next.append(nw)
            child = self._decide(t + 1, rem - q, bel, rho * HALF / m_alt, tuple(w_next), nh,
                                 released + ((d, y),))
            total = [x + m_alt * c for x, c in zip(total, child, strict=True)]
        return total

    # ---------- extract the column as a policy on learner information ----------
    def column(self):
        """Map every learner information set to the DP choice at its key (tree walk)."""
        g = self.game
        pol = {}

        def walk(t, rem, belief, rho, nuw, history, released):
            if t > self.cfg.horizon:
                return
            key = self.key(t, rem, belief, rho, nuw, history, released)
            choice = self.policy[key]
            pol[history, released] = choice
            a, q = choice
            if a:
                return
            if t >= self.cfg.horizon:
                return
            # replicate _advance bookkeeping
            nh = history + ((0, q),)
            nb = g._transition_belief(t, belief, q)
            new_nuw = []
            for i, w in enumerate(nuw):
                if not q:
                    new_nuw.append(w)
                    continue
                nw = {}
                for cfg_, m in w.items():
                    p = self.nus[i].get((history, tuple(sorted(released + cfg_))), HALF)
                    for y, py in ((0, 1 - p), (1, p)):
                        if py and m:
                            c2 = tuple(sorted(cfg_ + ((t, y),)))
                            nw[c2] = nw.get(c2, F(0)) + m * py
                new_nuw.append(nw)
            rel = release(g, t + 1, nb)
            if rel is None:
                walk(t + 1, rem - q, nb, rho, tuple(new_nuw), nh, released)
                return
            d, branches = rel
            d -= self.cfg.delay
            for y, m_alt, bel in branches:
                w_next = []
                for w in new_nuw:
                    nw = {}
                    for cfg_, m in w.items():
                        if (d, y) in cfg_:
                            c2 = tuple(i for i in cfg_ if i != (d, y))
                            nw[c2] = nw.get(c2, F(0)) + m / m_alt
                    w_next.append(nw)
                walk(t + 1, rem - q, bel, rho * HALF / m_alt, tuple(w_next), nh,
                     released + ((d, y),))

        walk(1, self.cfg.budget, initial_belief(g), F(1),
             tuple({(): F(1)} for _ in self.nus), (), ())
        return pol


def column_metrics(game, pol, nu=None):
    """Exact (alt cost, promotion probability under null nu (None = IID p=1/2))."""
    cfg = game.config

    def risk(history, outcomes):
        t = len(history) + 1
        if t > cfg.horizon:
            return F(0)
        info = game.information(history, outcomes)
        a, q = pol.get(info, (0, 0))
        if a:
            return F(1)
        nh = history + ((0, q),)
        if not q:
            return risk(nh, outcomes)
        p = HALF if nu is None else nu.get((history, outcomes), HALF)
        return (1 - p) * risk(nh, outcomes + ((t, 0),)) + p * risk(nh, outcomes + ((t, 1),))

    return risk((), ())


def mixture_robust_risk(game, cols, weights):
    """Exact sup over full-history causal nulls of the root mixture's first-promotion prob.

    The null sees public actions and every generated outcome but not the root coin.
    Returns (risk, endpoint best-response strategy keyed by (history, outcomes))."""
    cfg = game.config
    strategy = {}
    memo = {}

    def visit(history, outcomes, alive):
        key = (history, outcomes, alive)
        if key in memo:
            return memo[key]
        t = len(history) + 1
        if t > cfg.horizon or not alive:
            return F(0)
        info = game.information(history, outcomes)
        groups: dict = {}
        for j in alive:
            groups.setdefault(cols[j].get(info, (0, 0)), []).append(j)
        val = F(0)
        for (a, q), members in groups.items():
            fs = frozenset(members)
            if a:
                val += sum(weights[j] for j in members)
                continue
            nh = history + ((0, q),)
            if q:
                v0 = visit(nh, outcomes + ((t, 0),), fs)
                v1 = visit(nh, outcomes + ((t, 1),), fs)
                if v0 > v1:
                    strategy[history, outcomes] = F(0)
                    val += v0
                else:
                    strategy[history, outcomes] = HALF
                    val += (v0 + v1) / 2
            else:
                val += visit(nh, outcomes, fs)
        memo[key] = val
        return val

    r = visit((), (), frozenset(range(len(cols))))
    return r, strategy
