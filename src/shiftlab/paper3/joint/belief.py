"""Online belief over a 2-regime hidden-Markov model of the paired outcome, PolicyView-only.

Main simulator: at a disagreement round the challenger is correct w.p. p_s (state s in {L,H});
a label at such a round is the binary outcome Z=+1/-1. A grid of hypotheses (pL<pH, symmetric
switching hazard) is filtered exactly in closed form (2-state chain propagated by eigenvalue
power), giving a posterior over regime means and hazard (Bayesian model averaging).
Known-model mode (tiny exact check) takes the oracle's HMM with 4 pair outcomes.
Nothing here touches tapes or truth: inputs are ProblemSpec and PolicyView objects only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..contracts import PolicyView, ProblemSpec

P_FINE = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
HZ_FINE = (0.0005, 0.004, 0.015, 0.05)
P_GRID = (0.3, 0.5, 0.7, 0.9)  # coarse grid used by table-based policies (cache size)
HZ_GRID = (0.001, 0.008, 0.04)


@dataclass(frozen=True)
class Model:
    """Single-hypothesis model. P[s, o]: outcome distribution per state; Zo[o]: value of Z."""

    a: float  # P(L->H)
    b: float  # P(H->L)
    P: np.ndarray  # (2, O)
    Zo: np.ndarray  # (O,)
    r: float  # disagreement (informative-round) rate
    pi0: float

    @property
    def lam(self):
        return 1.0 - self.a - self.b

    @property
    def pinf(self):
        s = self.a + self.b
        return self.a / s if s > 0 else 0.5

    @property
    def gain(self):  # expected Z per round in state L/H (>0 favours challenger)
        z = self.P @ self.Zo
        return self.r * z[0], self.r * z[1]


class BeliefCore:
    """mode 'fit': grid of hypotheses learned online; mode 'known': a given Model (tiny check)."""

    def __init__(
        self,
        known: dict | None = None,
        hz_grid=HZ_GRID,
        p_grid=P_GRID,
        persist: float = 0.0,
        pi0: float = 0.5,
    ):
        self.known = known
        if known is None:
            pairs = [(lo, hi) for i, lo in enumerate(p_grid) for hi in p_grid[i + 1 :]]
            hyp = [(lo, hi, h) for (lo, hi) in pairs for h in hz_grid]
            self.pL, self.pH, self.hz = (np.array(c, float) for c in zip(*hyp, strict=True))
            self.a = self.b = self.hz
            O = 2
            self.PL = np.stack([self.pL, 1 - self.pL], 1)
            self.PH = np.stack([self.pH, 1 - self.pH], 1)
            self.Zo = np.array([1.0, -1.0])
            self.pi0 = np.full(len(self.hz), float(pi0))
            # hazard prior tilt toward persistence: weight ~ (hz/hz_min)^-persist
            self.logprior = -persist * np.log(self.hz / self.hz.min())
        else:
            O = 4
            tr = known["trans"]
            self.a = np.array([float(tr[0][1])])
            self.b = np.array([float(tr[1][0])])
            m0, m1 = known["m0"], known["m1"]
            P = np.zeros((2, 4))
            for s in (0, 1):
                for o, (x, y) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
                    P[s, o] = (m0[s] if x else 1 - m0[s]) * (m1[s] if y else 1 - m1[s])
            self.PL, self.PH = P[0][None], P[1][None]
            self.Zo = np.array([0.0, -1.0, 1.0, 0.0])
            self.pi0 = np.array([float(known["prior1"])])
            self.logprior = np.zeros(1)
        self.O, self.H = O, len(self.a)
        self.lam = 1.0 - self.a - self.b
        self.pinf = np.where(self.a + self.b > 0, self.a / np.maximum(self.a + self.b, 1e-12), 0.5)

    # ------------------------------------------------------------------ lifecycle
    def reset(self, spec: ProblemSpec):
        self.T = spec.T
        self.obs: list[tuple[int, int]] = []
        self.pending: list[int] = []  # own request times not yet released
        self.delays: list[int] = []
        self.n_dis = 0
        self.pi_last = self.pi0.copy()
        self.t_last = 1
        self.ll = self.logprior.copy()
        self.d_known = spec.delay_known
        self.new_obs = False
        self.t = 0

    def out_index(self, lab) -> int | None:
        if self.known is not None:
            return int(lab.ell0) * 2 + int(lab.ell1)
        z = lab.ell0 - lab.ell1
        return 0 if z > 0 else (1 if z < 0 else None)

    def ingest(self, view: PolicyView):
        self.t = view.t
        self.n_dis += int(view.event.disagree)
        self.new_obs = False
        for lab in view.released:
            self.delays.append(lab.t_release - lab.t_request)
            if lab.t_request in self.pending:
                self.pending.remove(lab.t_request)
            o = self.out_index(lab)
            if o is not None:
                self.obs.append((lab.t_request, o))
                self.new_obs = True
        if self.new_obs:
            self._refit()

    def note_query(self, t: int):
        self.pending.append(t)

    def _refit(self):
        pi, tl, ll = self.pi0.copy(), 1, self.logprior.copy()
        for u, o in sorted(self.obs):
            pu = self.pinf + (pi - self.pinf) * self.lam ** (u - tl)
            lik = pu * self.PH[:, o] + (1 - pu) * self.PL[:, o]
            ll += np.log(np.maximum(lik, 1e-300))
            pi = pu * self.PH[:, o] / np.maximum(lik, 1e-300)
            tl = u
        self.pi_last, self.t_last, self.ll = pi, tl, ll

    # ------------------------------------------------------------------ queries
    def weights(self) -> np.ndarray:
        w = np.exp(self.ll - self.ll.max())
        return w / w.sum()

    def pi_at(self, t: int) -> np.ndarray:
        return self.pinf + (self.pi_last - self.pinf) * self.lam ** max(t - self.t_last, 0)

    def r_hat(self) -> float:
        if self.known is not None:
            return 1.0
        return (self.n_dis + 5.0) / (self.t + 20.0)

    def d_hat(self) -> int:
        if self.d_known is not None:
            return int(self.d_known)
        if len(self.delays) < 3:
            return 5
        return int(max(1, round(float(np.mean(self.delays)))))

    def model(self, h: int) -> Model:
        P = np.stack([self.PL[h], self.PH[h]])
        r = self.r_hat()
        if self.known is None:  # quantise: keeps the value-table cache small
            r = max(0.04, round(r / 0.04) * 0.04)
        return Model(float(self.a[h]), float(self.b[h]), P, self.Zo, r, float(self.pi0[h]))

    def top(self, m: int):
        w = self.weights()
        idx = np.argsort(-w)[:m]
        idx = idx[w[idx] >= 0.01 * w[idx[0]]]
        ww = w[idx] / w[idx].sum()
        return idx, ww
