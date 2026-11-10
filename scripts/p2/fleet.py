"""Fleet-level certified promotion pilot (P2 follow-up, 2026-11-10).

A fleet is an ordered sequence of promotion episodes (one incumbent/challenger decision each,
chronological within a source). Episodes run one after another; episode k may use everything
released in episodes < k.

Arms (all on QSG's skeleton: started-mixture e-process on queried disagreement outcomes,
front-loaded acquisition, mirrored discard and rollback tests):

* ``base``  per-episode alpha = .05, uniform grid prior (= QSG).
* ``eb``    the grid prior is a kernel posterior of earlier episodes' estimated edges (fixed at
            episode start, so each component and the mixture remain test supermartingales under
            the episode's conditional null; validity is unchanged).
* ``lond``  online FDR across the fleet with e-LOND (Xu & Ramdas): episode k promotes at level
            alpha_k = alpha * gamma_k * (R_{k-1} + 1), where R_{k-1} counts earlier promoting
            episodes. The episode e-value is e_k = sum_c 2^{-c} E^{(c)}_{tau_c} over promotion cycles,
            each stopped at its crossing or at the episode end; E[e_k] <= 1 by optional stopping and a
            cycle-c crossing of 2^c / alpha_k gives e_k >= 1 / alpha_k. Hence FDR <= alpha across
            the fleet, with arbitrary dependence between episodes.
* ``eb+lond`` both.

Run: python scripts/p2/fleet.py --mode synth|real ... (see main()).
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
for _p in (HERE.parents[0] / "failure_atlas_v2_flq", HERE.parents[0] / "promising_directions/sota",
           HERE.parents[0] / "promising_directions/sota/competitors", HERE.parents[0] / "sota_sprint"):  # fmt: skip
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from qsg import QSG, StartedMixture
from simulator import run_episode
from suite import stream_from_losses

GRID = np.array([0.52, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
T, BUDGET, CQ, CS, ALPHA = 2000, 200, 0.05, 5.0, 0.05


def gamma_seq(n: int) -> np.ndarray:
    """LOND/LORD default spending sequence (Javanmard & Montanari style), normalised to sum 1."""
    j = np.arange(1, n + 1, dtype=float)
    g = np.log(np.maximum(j, 2)) / (j * np.exp(np.sqrt(np.log(np.maximum(j, 2)))))
    return g / g.sum()


class PriorMixture(StartedMixture):
    def __init__(self, side, pi):
        super().__init__(side, GRID)
        self.pi = np.asarray(pi, float) / np.sum(pi)


class FleetQSG(QSG):
    """QSG with a supplied grid prior and episode level alpha_k; records released outcomes."""

    def __init__(self, *, pi_up, pi_dn, alpha_k, rng, name="fleet"):
        self.pi_up, self.pi_dn = pi_up, pi_dn
        self.zs: list[int] = []
        self.evalue = 0.0  # sum_c 2^{-c} E^{(c)} stopped at crossing (diagnostic)
        super().__init__(T, BUDGET, alpha_k, rng=rng, name=name)

    def _new_tests(self):
        if self.deployed == 0:
            self.e_up, self.e_dn = PriorMixture(+1, self.pi_up), PriorMixture(-1, self.pi_dn)
        else:
            self.e_up, self.e_dn = None, PriorMixture(-1, self.pi_dn)

    def observe(self, feedback):
        for fb in feedback:
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d != 0:
                self.zs.append(int(d > 0))
        super().observe(feedback)


def kernel_prior(phats: list[float], eps: float, bw: float = 0.05) -> np.ndarray:
    """Mixture of uniform (weight eps) and a Gaussian kernel posterior over GRID."""
    u = np.full(len(GRID), 1.0 / len(GRID))
    if not phats:
        return u
    k = np.mean([np.exp(-0.5 * ((GRID - p) / bw) ** 2) for p in phats], axis=0)
    if k.sum() <= 0:
        return u
    return eps * u + (1 - eps) * k / k.sum()


def run_fleet(args):
    """One fleet: list of (l0, l1, delay, meta) episodes processed in order, for one arm."""
    episodes, arm, seed, eps = args
    use_eb, use_lond = "eb" in arm, "lond" in arm
    gam = gamma_seq(len(episodes))
    R = 0
    ph_up, ph_dn = [], []
    out = []
    for k, (l0, l1, delay, meta) in enumerate(episodes):
        alpha_k = ALPHA * gam[k] * (R + 1) if use_lond else ALPHA
        alpha_k = min(alpha_k, 0.5)
        pi_up = kernel_prior(ph_up, eps) if use_eb else np.ones(len(GRID))
        pi_dn = kernel_prior(ph_dn, eps) if use_eb else np.ones(len(GRID))
        rng = np.random.default_rng([seed, k, 11])
        pol = FleetQSG(pi_up=pi_up, pi_dn=pi_dn, alpha_k=alpha_k, rng=rng, name=arm)
        losses = np.stack([l0, l1], 1).astype(np.int8)
        preds, labels = stream_from_losses(losses, np.random.default_rng([seed, k, 7]))
        res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=BUDGET,
                          label_price=CQ, switch_cost=CS, trace=True)  # fmt: skip
        dep = np.fromiter((r["deployed_model"] for r in res.records), int, len(res.records))
        promoted = bool(dep.max() > 0)
        R += int(promoted)
        if pol.zs:
            p = (sum(pol.zs) + 1.0) / (len(pol.zs) + 2.0)
            (ph_up if p > 0.5 else ph_dn).append(p if p > 0.5 else 1.0 - p)
        never = float(l0.sum())
        out.append({**meta, "arm": arm, "seed": seed, "k": k, "alpha_k": alpha_k, "net": res.net_cost,
                    "loss": res.prediction_loss, "labels": res.requested_labels,
                    "switches": res.deployment_switches, "promoted": promoted,
                    "db": never - res.prediction_loss - CS * res.deployment_switches})  # fmt: skip
    return out


# ------------------------------------------------------------------------------------- fleets
def synth_fleet(rng, K, pi0, rho=0.0, dis=0.2, delay=100):
    """K episodes; each null (p=.5) w.p. pi0, else challenger edge p ~ U{.55,.6,.65,.7,.8}."""
    eps = []
    for _ in range(K):
        null = rng.random() < pi0
        p = 0.5 if null else float(rng.choice([0.55, 0.6, 0.65, 0.7, 0.8]))
        d = rng.random(T) < dis
        s = np.empty(T, bool)
        s[0] = rng.random() < p
        for t in range(1, T):
            s[t] = s[t - 1] if rng.random() < rho else (rng.random() < p)
        agree_err = rng.random(T) < 0.1
        l0 = np.where(d, s, agree_err).astype(np.int8)
        l1 = np.where(d, ~s, agree_err).astype(np.int8)
        eps.append((l0, l1, delay, {"null": bool(null), "p": p}))
    return eps


def real_fleets(paths):
    fleets = []
    for path in paths:
        z = np.load(path)
        delay = int(z["delay"]) if "delay" in z.files else 100
        src = Path(path).stem
        eps = [(z["l0"][i], z["l1"][i], delay,
                {"source": src, "ep": i, "adv": float((z["l0"][i].astype(float) - z["l1"][i]).mean())})
               for i in range(z["l0"].shape[0])]  # fmt: skip
        fleets.append(eps)
    return fleets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["synth", "real"], required=True)
    ap.add_argument("--arms", default="base,eb,lond,eb+lond")
    ap.add_argument("--fleets", type=int, default=30)
    ap.add_argument("--K", type=int, default=60)
    ap.add_argument("--pi0", default="0.2,0.5,0.8")
    ap.add_argument("--rho", type=float, default=0.0)
    ap.add_argument("--paths", default="")
    ap.add_argument("--eps", type=float, default=0.2)
    ap.add_argument("--seed-base", type=int, default=2026111001)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    arms = a.arms.split(",")
    jobs = []
    if a.mode == "synth":
        for pi0 in (float(x) for x in a.pi0.split(",")):
            for f in range(a.fleets):
                rng = np.random.default_rng([a.seed_base, f, int(pi0 * 1000), int(a.rho * 1000)])
                eps = synth_fleet(rng, a.K, pi0, a.rho)
                for e in eps:
                    e[3].update(pi0=pi0, fleet=f, rho=a.rho)
                jobs += [(eps, arm, a.seed_base + f, a.eps) for arm in arms]
    else:
        for i, eps in enumerate(real_fleets(a.paths.split(","))):
            jobs += [(eps, arm, a.seed_base + i, a.eps) for arm in arms]
    Path(a.out).mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with mp.Pool(a.workers) as pool, open(Path(a.out, "records.jsonl"), "w") as fh:
        for rows in pool.imap_unordered(run_fleet, jobs):
            fh.writelines(json.dumps(r) + "\n" for r in rows)
    Path(a.out, "manifest.json").write_text(
        json.dumps({"argv": sys.argv, "seconds": time.time() - t0})
    )
    print(f"done {len(jobs)} fleet-arms in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
