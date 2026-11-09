"""Stage 2 step 2: constrained Bayesian optimisation over Stage2Policy configurations (even episodes).

  python stage2_bo.py [--n-init 20] [--n-iter 60] [--workers 16]

Objective: equal-dataset mean J (minimise). Outcome constraint: dL/T <= +0.1 pp versus the fixed new
reference (read from stage2/ref_summary.json). Optimiser: BoTorch qLogNoisyExpectedImprovement with
the constraint on a ModelListGP (one SingleTaskGP per outcome). Initial design: scrambled Sobol with a
fixed seed. Every evaluation is appended to bo/evals.jsonl (resumable: rerun the same command) and
its per-episode seed-means are saved to bo/evals/eval_XXX.csv.gz.
Only evaluator-independent reads: the reference per-episode table is read for the *score*, never by a policy.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_eval as ev
import stage2_space as sps
import trace_run as tr

OUT = tr.ROOT / "outputs/paper1_eqsdp/stage2"
BO = OUT / "bo"
T = 2000
LIM_PP = 0.1
SOBOL_SEED = 20261108


def ref_table() -> pd.DataFrame:
    name = json.loads((OUT / "ref_summary.json").read_text())["new_reference"]
    e = pd.read_csv(OUT / "ref_episode.csv")
    e = e[e.policy == name].set_index(["stream", "ep"]).sort_index()
    return e[["net", "loss"]].rename(columns={"net": "net_ref", "loss": "loss_ref"})


def score(e: pd.DataFrame, ref: pd.DataFrame) -> dict:
    m = e.set_index(["stream", "ep"]).join(ref, how="inner")
    assert len(m) == len(ref) == len(e)
    g = m.groupby("stream")
    return {
        "J": float(g.net.mean().mean()),
        "dJ": float((g.net.mean() - g.net_ref.mean()).mean()),
        "dL_pp": float(100 * (g.loss.mean() - g.loss_ref.mean()).mean() / T),
        "labels": float(g.labels.mean().mean()),
        "switches": float(g.switches.mean().mean()),
    }


def read_log() -> list[dict]:
    p = BO / "evals.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def propose(hist: list[dict], it: int) -> np.ndarray:
    import torch
    from botorch.acquisition.logei import qLogNoisyExpectedImprovement
    from botorch.acquisition.objective import GenericMCObjective
    from botorch.fit import fit_gpytorch_mll
    from botorch.models import ModelListGP, SingleTaskGP
    from botorch.models.transforms.outcome import Standardize
    from botorch.optim import optimize_acqf
    from botorch.sampling.normal import SobolQMCNormalSampler
    from gpytorch.mlls import SumMarginalLogLikelihood

    torch.manual_seed(1000 + it)
    X = torch.tensor([h["u"] for h in hist], dtype=torch.double)
    J = torch.tensor([[h["J"]] for h in hist], dtype=torch.double)
    C = torch.tensor([[h["dL_pp"] - LIM_PP] for h in hist], dtype=torch.double)
    models = [SingleTaskGP(X, Y, outcome_transform=Standardize(m=1)) for Y in (J, C)]
    model = ModelListGP(*models)
    fit_gpytorch_mll(SumMarginalLogLikelihood(model.likelihood, model))
    acq = qLogNoisyExpectedImprovement(
        model=model,
        X_baseline=X,
        sampler=SobolQMCNormalSampler(torch.Size([256]), seed=it),
        objective=GenericMCObjective(lambda Z, X=None: -Z[..., 0]),
        constraints=[lambda Z: Z[..., 1]],
        prune_baseline=True,
    )
    bounds = torch.stack([torch.zeros(sps.DIM), torch.ones(sps.DIM)]).double()
    cand, _ = optimize_acqf(acq, bounds=bounds, q=1, num_restarts=10, raw_samples=512)
    return cand.detach().numpy()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-init", type=int, default=20)
    ap.add_argument("--n-iter", type=int, default=60)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    (BO / "evals").mkdir(parents=True, exist_ok=True)
    from scipy.stats import qmc

    sobol = qmc.Sobol(sps.DIM, scramble=True, seed=SOBOL_SEED).random(a.n_init)
    ref = ref_table()
    evaluator = ev.Evaluator(workers=a.workers)
    cache = {}
    hist = read_log()
    for h in hist:
        cache[json.dumps(h["cfg"], sort_keys=True)] = h
    total = a.n_init + a.n_iter
    try:
        while len(hist) < total:
            i = len(hist)
            t_prop = time.perf_counter()
            kind = "sobol" if i < a.n_init else "bo"
            u = sobol[i] if kind == "sobol" else propose(hist, i)
            cfg = sps.to_cfg(u)
            t_prop = time.perf_counter() - t_prop
            key = json.dumps(cfg, sort_keys=True)
            if key in cache:  # identical mapped configuration already evaluated
                rec = {
                    **cache[key],
                    "i": i,
                    "u": [float(x) for x in u],
                    "kind": kind,
                    "dup_of": cache[key]["i"],
                    "eval_secs": 0.0,
                }
            else:
                name = f"s2bo_{i:03d}"
                _, e, secs = evaluator.evaluate({name: cfg})
                e[e.policy == name].to_csv(BO / "evals" / f"eval_{i:03d}.csv.gz", index=False)
                s = score(e[e.policy == name], ref)
                rec = {
                    "i": i, "kind": kind, "u": [float(x) for x in u], "cfg": cfg, **s,
                    "feasible": s["dL_pp"] <= LIM_PP, "eval_secs": secs, "propose_secs": t_prop,
                }  # fmt: skip
                cache[key] = rec
            with open(BO / "evals.jsonl", "a") as f:
                f.write(json.dumps(rec) + "\n")
            hist.append(rec)
            feas = [h for h in hist if h["feasible"]]
            best = min(feas, key=lambda h: h["J"]) if feas else None
            (BO / "status.json").write_text(
                json.dumps(
                    {"done": len(hist), "total": total, "time": time.ctime(),
                     "best_feasible_i": best["i"] if best else None,
                     "best_feasible_J": best["J"] if best else None,
                     "n_feasible": len(feas)}
                )
            )  # fmt: skip
    finally:
        evaluator.close()
    (BO / "DONE").write_text("done")


if __name__ == "__main__":
    main()
