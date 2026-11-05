"""WP2 paired runner: screen.py's pairing and seeding plus deployment-path economics.

It reproduces ``screen._job`` exactly (same loss stream, same stream_rng, same ``build_suite`` seeds,
so ``net`` is identical to a screen.py run with the same regime name and seed base) and adds, from the
deployment trace, the WP2 quantities of docs/sprint2/wp2/protocol.md:

* ``promos``: for every promotion (0 -> 1 transition) at event tau, the realised paired challenger
  advantage mean(l0 - l1) over [tau, tau+H) for H in {100, 500, rest}, and its rest-of-episode sum;
* ``db``: deployment benefit vs never-switch = sum(l0) - realised loss - c_s * switches;
* ``harm``: J(policy) - J(never-switch) = net - sum(l0) (never-switch buys no labels);
* ``ep_adv``: the episode's realised mean advantage; ``pre_adv`` the realised advantage before tau.

Loss sources, beyond screen.py's names (which keep screen.py's seeding):
  ``file:<path.npz>[:<seed-name>]``  rows l0/l1 of any npz (e.g. data/sprint_twin_losses_v2).

Delay override: ``--delay-mult m`` multiplies the registered delay (FRESH/REAL delays, or the
synthetic regime's) and rounds to an integer >= 1. Records carry ``delay`` and ``delay_mult``.

    uv run python scripts/sota_sprint/wp2_run.py --sources file:data/sprint_twin_losses_v2/twin2_metro.npz:twin2_metro \
        --policies A5b,D2 --seeds 1 --seed-base 2026110701 --workers 2 --out outputs/sprint2/WP2/demo
"""

from __future__ import annotations

import argparse
import json
import re
import multiprocessing as mp
import time
from pathlib import Path

import numpy as np

import screen  # noqa: F401  (sets sys.path and registers W_*/O_* regimes)
from bench import CONTRACT, parse_regime
from screen import _delay, _git_rev, _h, _loss_file
from simulator import run_episode
from suite import build_suite, stream_from_losses

import fam_f  # noqa: F401  (registers WP2_* regimes)

HORIZONS = (100, 500)


def _source(src: str):
    """-> (kind, seed_name, path or None)."""
    if src.startswith("file:"):
        parts = src[5:].split(":")
        path = Path(parts[0])
        return "real", (parts[1] if len(parts) > 1 else path.stem), path
    try:
        parse_regime(src)
        return "synthetic", src, None
    except KeyError:
        return "real", src, _loss_file(src)


def _base_delay(seed_name: str, kind: str) -> int:
    if kind == "synthetic":
        return parse_regime(seed_name)[0].delay
    for pre in ("twin2_", "twin_"):
        seed_name = seed_name.removeprefix(pre)
    return _delay(re.sub(r"_T\d+$", "", seed_name.split("@")[0]))


def promo_stats(l0: np.ndarray, l1: np.ndarray, dep: np.ndarray, cs: float) -> list[dict]:
    d = l0.astype(float) - l1
    T = len(d)
    up = np.flatnonzero(np.diff(np.r_[0, dep]) == 1)
    out = []
    for tau in up:
        row = {"t": int(tau), "pre_adv": float(d[:tau].mean()) if tau else 0.0,
               "rest_n": int(T - tau), "rest_sum": float(d[tau:].sum()),
               "adv_rest": float(d[tau:].mean())}
        for H in HORIZONS:
            seg = d[tau:tau + H]
            row[f"adv_{H}"] = float(seg.mean())
            row[f"n_{H}"] = int(len(seg))
        row["ei"] = int(row["rest_sum"] - cs <= 0)  # hold-to-end net benefit <= 0 after switch cost
        out.append(row)
    return out


def _job(args):
    kind, seed_name, path, ep, seed, seed_base, names, alpha, dmult = args
    from registry import EXTRA

    if kind == "synthetic":
        R, b = parse_regime(seed_name)
        budget = b or CONTRACT["budget"]
        losses = R.sample(np.random.default_rng(np.random.SeedSequence(
            [seed_base, _h(R.name), seed])))
        base_delay = R.delay
        split = -1
    else:
        z = np.load(path)
        losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
        budget = CONTRACT["budget"]
        base_delay = _base_delay(seed_name, kind)
        split = int(z["split"][ep]) if "split" in z.files else -1
    delay = max(1, int(round(base_delay * dmult)))
    l0, l1 = losses[:, 0], losses[:, 1]
    cs, cq = CONTRACT["cs"], CONTRACT["cq"]
    rows = []
    run_ep = ep * 100_000 + seed
    for pol in build_suite(losses.shape[0], budget, cs, cq, alpha, delay, run_ep,
                           seed_base + _h(seed_name) % 1000, names=names, extra=EXTRA):
        stream_rng = np.random.default_rng([seed_base, _h(seed_name), ep, seed, 7])
        preds, labels = stream_from_losses(losses, stream_rng)
        t0 = time.perf_counter()
        res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                          label_price=cq, switch_cost=cs, trace=True)
        rt = time.perf_counter() - t0
        if res.requested_labels > budget:
            raise AssertionError(f"{pol.name} exceeded budget")
        dep = np.fromiter((r["deployed_model"] for r in res.records), int, len(res.records))
        promos = promo_stats(l0, l1, dep, cs)
        never = float(l0.sum())
        rows.append({
            "kind": kind, "regime": seed_name, "source": path, "split": split, "ep": ep, "seed": seed, "policy": pol.name,
            "alpha": alpha, "delay": delay, "delay_mult": dmult, "budget": budget,
            "T": int(len(l0)), "net": res.net_cost, "loss": res.prediction_loss,
            "labels": res.requested_labels, "switches": res.deployment_switches,
            "ever_promote": int(bool(promos)), "first_deploy": promos[0]["t"] if promos else -1,
            "n_promotions": len(promos),
            "n_rollbacks": int((np.diff(np.r_[0, dep]) == -1).sum()), "final": int(dep[-1]),
            "ep_adv": float((l0.astype(float) - l1).mean()),
            "db": never - res.prediction_loss - cs * res.deployment_switches,
            "harm": res.net_cost - never, "promos": promos, "runtime_s": round(rt, 4)})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--policies", required=True)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--seed-base", type=int, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--alpha", type=float, default=CONTRACT["alpha"])
    ap.add_argument("--delay-mult", type=float, default=1.0)
    ap.add_argument("--episodes", default="", help="optional 'start:stop' row slice for file sources")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    names = [x for x in a.policies.split(",") if x]
    from registry import EXTRA, IMPORT_ERRORS

    jobs = []
    for src in a.sources.split(","):
        kind, seed_name, path = _source(src)
        if kind == "synthetic":
            jobs += [(kind, seed_name, None, 0, s, a.seed_base, names, a.alpha, a.delay_mult)
                     for s in range(a.seeds)]
        else:
            K = np.load(path)["l0"].shape[0]
            rng = range(K)
            if a.episodes:
                lo, hi = (int(x) for x in a.episodes.split(":"))
                rng = range(lo, min(hi, K))
            jobs += [(kind, seed_name, str(path), e, s, a.seed_base, names, a.alpha, a.delay_mult)
                     for e in rng for s in range(a.seeds)]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for rows in pool.imap_unordered(_job, jobs, chunksize=2):
            for row in rows:
                f.write(json.dumps(row) + "\n")
    (out / "manifest.json").write_text(json.dumps(
        {"argv": vars(a), "contract": {**CONTRACT, "alpha": a.alpha}, "git": _git_rev(),
         "import_errors": IMPORT_ERRORS, "n_jobs": len(jobs), "seconds": round(time.time() - t0, 1),
         "unknown_policies": [n for n in names if n not in EXTRA]}, indent=2) + "\n")
    print(f"done {len(jobs)} jobs in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
