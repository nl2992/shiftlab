"""D3: recurrent sequential controller over the masked observable history (GPU).

Batched torch simulator of the same contract as ``sim.py`` (release -> act -> acquire; delay >= 1;
pending labels count against the budget at request time). Each step the controller sees only:
disagreement bit, the paired outcome released now (if any), time fraction, remaining budget
fraction, pending count, deployed model, delay/T, and (structured variant only) discounted
evidence statistics. Rewards are the negative economic cost. Trained by REINFORCE (rollout under
no_grad, then a teacher-forced cuDNN pass for the log-probabilities).

Variants
- structured: evidence features (discounted p-hat / log n at lam .9 and .98, the Wald-LCB gain minus
  c_s at lam .97 gamma .2 used as an input) + hard budget reservation cap on the query probability
  (cap = min(1, 2*rem / expected remaining disagreements)); switch head bias initialised negative.
- generic: same GRU width and head sizes, raw observables only, no reservation cap (the simulator
  merely refuses over-budget requests).
No validity claim is made for either.
"""

from __future__ import annotations

import time

import numpy as np
import torch
from scipy.stats import norm
from torch import nn

from .sim import PRIMARY, Costs

P_MIN, PRIOR_RATE, PRIOR_W = 0.05, 0.25, 20.0
F_GENERIC, F_STRUCT = 7, 13
Z20 = float(norm.ppf(0.2))


class Controller(nn.Module):
    def __init__(self, structured: bool, hidden: int = 48):
        super().__init__()
        self.structured = structured
        self.gru = nn.GRU(F_STRUCT if structured else F_GENERIC, hidden, batch_first=True)
        self.q = nn.Linear(hidden, 1)
        self.s = nn.Linear(hidden, 1)
        nn.init.constant_(self.s.bias, -4.0)
        nn.init.constant_(self.q.bias, 0.0)

    def heads(self, h):
        return self.q(h).squeeze(-1), self.s(h).squeeze(-1)


@torch.no_grad()
def rollout(
    ctrl, l0, l1, delay, costs: Costs = PRIMARY, greedy_switch=False, gen=None, device="cuda"
):
    """l0,l1: (B,T) int tensors on device, delay: (B,) long. Returns X, A, R, J (per-episode)."""
    B, T = l0.shape
    dev = l0.device
    F = F_STRUCT if ctrl.structured else F_GENERIC
    X = torch.zeros(B, T, F, device=dev)
    A = torch.zeros(B, T, 2, device=dev)
    R = torch.zeros(B, T, device=dev)
    dis = l0 != l1
    D = (l0 - l1).float()
    req = torch.zeros(B, T, device=dev)
    rem = torch.full((B,), float(costs.B), device=dev)
    dep = torch.zeros(B, device=dev)
    nd = torch.zeros(B, device=dev)
    ev = torch.zeros(B, 6, device=dev)  # n9,k9,n98,k98,n97,k97
    h = None
    ar = torch.arange(B, device=dev)
    pend = torch.zeros(B, device=dev)
    labels = torch.zeros(B, device=dev)
    sws = torch.zeros(B, device=dev)
    loss_tot = torch.zeros(B, device=dev)
    dlT = delay.float() / T
    for t in range(T):
        s = t - delay
        ok = s >= 0
        si = s.clamp(min=0)
        r = (req[ar, si] > 0) & ok
        rf = r.float()
        d = D[ar, si]
        pos = (d > 0).float()
        for j, lam in enumerate((0.9, 0.98, 0.97)):
            ev[:, 2 * j] = torch.where(r, lam * ev[:, 2 * j] + 1, ev[:, 2 * j])
            ev[:, 2 * j + 1] = torch.where(r, lam * ev[:, 2 * j + 1] + pos, ev[:, 2 * j + 1])
        pend = pend - rf
        dist = dis[:, t].float()
        base = [dist, rf * d, rf, torch.full((B,), t / T, device=dev), rem / costs.B, dep, dlT]
        if ctrl.structured:
            feats = []
            for j in (0, 1):
                n, k = ev[:, 2 * j], ev[:, 2 * j + 1]
                feats += [
                    torch.where(n > 0, (k + 0.5) / (n + 1), torch.full_like(n, 0.5)),
                    torch.log1p(n) / 5,
                ]
            n, k = ev[:, 4], ev[:, 5]
            p = (k + 0.5) / (n + 1)
            se = torch.sqrt(p * (1 - p) / (n + 1))
            qlo = torch.where(dep == 0, (p + Z20 * se), (p - Z20 * se)).clamp(0, 1)
            adv = torch.where(dep == 0, 2 * qlo - 1, 1 - 2 * qlo)
            rate = (nd + PRIOR_RATE * PRIOR_W) / (t + PRIOR_W)
            g = (adv * rate * (T - t) - costs.cs) / 10.0
            feats += [g.clamp(-10, 10), pend / 20.0]
            base += feats
        x = torch.stack(base, 1)
        X[:, t] = x
        out, h = ctrl.gru(x[:, None, :], h)
        lq, ls = ctrl.heads(out[:, 0])
        if ctrl.structured:
            ls = ls + 3.0 * g.clamp(-10, 10)  # evidence-gain skip connection
        ps = torch.sigmoid(ls)
        pq = torch.sigmoid(lq)
        if ctrl.structured:
            exp_left = ((nd + PRIOR_RATE * PRIOR_W) / (t + PRIOR_W) * (T - t)).clamp(min=1e-9)
            pq = torch.minimum(pq, (2.0 * rem / exp_left).clamp(P_MIN, 1.0))
        if greedy_switch:
            sw = (ps > 0.5).float()
        else:
            sw = (torch.rand(B, device=dev, generator=gen) < ps).float()
        dep = (dep + sw) % 2
        sws += sw
        lt = torch.where(dep == 0, l0[:, t], l1[:, t]).float()
        loss_tot += lt
        elig = (dist > 0) & (rem > 0)
        qa = (torch.rand(B, device=dev, generator=gen) < pq).float() * elig.float()
        rem = rem - qa
        req[:, t] = qa
        pend = pend + qa
        labels += qa
        nd = nd + dist
        A[:, t, 0] = qa
        A[:, t, 1] = sw
        R[:, t] = -(lt + costs.cq * qa + costs.cs * sw) / 50.0
    J = loss_tot + costs.cq * labels + costs.cs * sws
    return X, A, R, J, labels, sws


def train_loss(ctrl, X, A, R):
    out, _ = ctrl.gru(X)
    lq, ls = ctrl.heads(out)
    if ctrl.structured:
        ls = ls + 3.0 * X[:, :, 11].clamp(-10, 10)
    lpq = -nn.functional.binary_cross_entropy_with_logits(lq, A[:, :, 0], reduction="none")
    lps = -nn.functional.binary_cross_entropy_with_logits(ls, A[:, :, 1], reduction="none")
    G = torch.flip(torch.cumsum(torch.flip(R, [1]), 1), [1])
    adv = G - G.mean(0, keepdim=True)
    adv = adv / (adv.std() + 1e-6)
    # query log-prob only counts where a decision existed (disagreement event): X[:,:,0]==1
    mask_q = X[:, :, 0]
    loss = -((lpq * mask_q + lps) * adv).mean()
    ent = -(
        torch.sigmoid(ls) * nn.functional.logsigmoid(ls)
        + (1 - torch.sigmoid(ls)) * nn.functional.logsigmoid(-ls)
    ).mean()
    return loss - 1e-3 * ent


def train(ctrl, sampler, seconds: float, lr=5e-3, batch=768, log=None, device="cuda"):
    opt = torch.optim.Adam(ctrl.parameters(), lr=lr)
    t0 = time.time()
    it = 0
    hist = []
    while time.time() - t0 < seconds:
        l0, l1, delay = sampler(batch)
        X, A, R, J, _, _ = rollout(ctrl, l0, l1, delay, device=device)
        loss = train_loss(ctrl, X, A, R)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(ctrl.parameters(), 1.0)
        opt.step()
        hist.append(float(J.mean()))
        it += 1
        if log and it % 10 == 0:
            log(it, float(np.mean(hist[-10:])))
    return it, hist
