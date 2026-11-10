"""D3 GPU: structured vs generic GRU controller, leave-family-out folds, bounded training time."""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from shiftlab.paper3.transfer import data, gru, sim, streams, synth
from shiftlab.paper3.transfer import methods as M

OUT = Path("outputs/paper3/transfer")
LEDGER = Path("papers/paper3_cost_aware_adaptation/2026_programme/ledger/transfer.jsonl")
SYN = OUT / "synth_losses.npz"
dev = "cuda"
NEVAL = 30


def synth_pool():
    z = np.load(SYN)
    return {
        f"{f}_{i}": (z[f"{f}_{i}_l0"], z[f"{f}_{i}_l1"], int(z[f"{f}_{i}_d"]))
        for f in synth.FAMILIES
        for i in range(6)
    }


def ledger(rec):
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def make_sampler(pool):
    """Equal-stream weighting: pick a stream uniformly, then an episode uniformly."""
    L0 = torch.cat([torch.tensor(a, device=dev, dtype=torch.int8) for a, _, _ in pool])
    L1 = torch.cat([torch.tensor(b, device=dev, dtype=torch.int8) for _, b, _ in pool])
    sid = np.concatenate([np.full(a.shape[0], i) for i, (a, _, _) in enumerate(pool)])
    dl = torch.tensor(np.concatenate([np.full(a.shape[0], d) for a, _, d in pool]), device=dev)
    cnt = np.bincount(sid)
    p = 1.0 / (cnt[sid] * len(cnt))
    pt = torch.tensor(p / p.sum(), device=dev, dtype=torch.float32)
    g = torch.Generator(device=dev)
    g.manual_seed(0)

    def sampler(B):
        idx = torch.multinomial(pt, B, replacement=True, generator=g)
        return L0[idx].int(), L1[idx].int(), dl[idx]

    return sampler


def evaluate(ctrl, st, recs_row, seed=0):
    ne = recs_row.n_early
    sl = slice(ne, min(recs_row.K, ne + NEVAL))
    l0 = torch.tensor(st.l0[sl], device=dev).int()
    l1 = torch.tensor(st.l1[sl], device=dev).int()
    d = torch.full((l0.shape[0],), st.delay, device=dev)
    g = torch.Generator(device=dev)
    g.manual_seed(seed)
    Js = []
    for k in range(2):
        _, _, _, J, _lab, _sws = gru.rollout(ctrl, l0, l1, d, greedy_switch=True, gen=g)
        Js.append(J.cpu().numpy())
    return np.mean(Js, 0).mean(), sl


def main(folds, seconds, tag):
    recs = data.load_all()
    real = {r.name: r for r in recs.values() if r.real}
    syn_pool = synth_pool()
    rows = []
    for fold in folds:
        test = [r for r in real.values() if r.family == fold]
        trn = [n for n, r in real.items() if r.family != fold]
        pool = [(lambda s: (s.l0, s.l1, s.delay))(streams.load(n)) for n in trn] + list(  # noqa: PLC3002
            syn_pool.values()
        )
        sampler = make_sampler(pool)
        sts = {r.name: streams.load(r.name) for r in test}
        ctx = M.build_ctx([r for r in real.values() if r.family != fold], [], "all")
        for variant in ("structured", "generic"):
            torch.manual_seed(0)
            ctrl = gru.Controller(variant == "structured").to(dev)
            # untrained reference (sanity: structured init is ~ Wald-gain follower)
            torch.cuda.reset_peak_memory_stats()
            t0 = time.time()
            log = lambda it, j: print(fold, variant, it, round(j, 1), flush=True)  # noqa: B023 (called in-loop)
            it, hist = gru.train(ctrl, sampler, seconds, log=log)
            wall = time.time() - t0
            peak = torch.cuda.max_memory_allocated() / 2**20
            ck = OUT / "ckpt"
            ck.mkdir(exist_ok=True)
            torch.save(ctrl.state_dict(), ck / f"{tag}_{fold}_{variant}.pt")
            for r in test:
                J, sl = evaluate(ctrl, sts[r.name], r)
                gf = M.global_fixed(ctx, "primary")
                ps = M.per_stream_tuning(r, "primary")
                Jt = r.J["primary"][sl]
                rows.append(
                    {
                        "tag": tag,
                        "fold": fold,
                        "stream": r.name,
                        "variant": variant,
                        "J": J,
                        "J_global_fixed": float(Jt[:, gf].mean()),
                        "J_per_stream_tuned": float(Jt[:, ps].mean()),
                        "J_ref_wald": float(Jt[:, sim.REF_CFG].mean()),
                        "iters": it,
                        "train_s": wall,
                        "peak_mb": peak,
                        "first10": float(np.mean(hist[:10])),
                        "last10": float(np.mean(hist[-10:])),
                    }
                )
            ledger(
                {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "stage": "D3",
                    "tag": tag,
                    "fold": fold,
                    "variant": variant,
                    "iters": it,
                    "train_seconds": wall,
                    "peak_gpu_mb": peak,
                    "train_J_first10": float(np.mean(hist[:10])),
                    "train_J_last10": float(np.mean(hist[-10:])),
                    "status": "dev_exploratory_only",
                    "validity": "none claimed",
                }
            )
            pd.DataFrame(rows).to_csv(OUT / f"d3_results_{tag}.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[3].split(","), float(sys.argv[2]), sys.argv[1])
