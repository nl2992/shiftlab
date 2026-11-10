"""A4: collect (features, a, q, cost-to-go) on TRAIN seeds only, fit an MLP on GPU, export numpy."""

import os
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(__file__))
from multiprocessing import Pool

import numpy as np
from common import OUT, ledger, log

from shiftlab.paper3.joint import harness as H
from shiftlab.paper3.joint.learned import NFEAT, Recorder
from shiftlab.paper3.joint.policies import QVOI, DualPrice
from shiftlab.paper3.simulation import generate_tape, load_regimes, make_spec, run_policy

_REG = None


def _init():
    global _REG
    _REG = load_regimes()


def _task(args):
    rid, seed, beh, T = args
    reg = _REG[rid]
    tape, _ = generate_tape(reg, seed, T)
    spec = make_spec(reg, T)
    inner = QVOI(voi_mult=3.0) if beh == "A1" else DualPrice(eta=0.2)
    rec_pol = Recorder(inner, eps=0.12)
    rec = run_policy(rec_pol, tape, spec, seed + 17)
    k, cq = reg.costs.k, reg.costs.c_q
    prev = np.r_[0, rec.a[:-1]]
    step = tape.ell[np.arange(T), rec.a] - tape.ell[:, 0] + k * (rec.a != prev) + cq * rec.q
    togo = np.cumsum(step[::-1])[::-1]
    X, Y = [], []
    for t, f in rec_pol.feats.items():
        X.append(np.r_[f, rec.a[t - 1], rec.q[t - 1]])
        Y.append(togo[t - 1])
    return np.array(X), np.array(Y), rid


def main():
    T = H.T_DEFAULT
    sl = H.seeds(H.TRAIN_SEEDS)
    assert (
        min(sl) >= H.seeds_for("dev", 1, 1000)[0]
        and not set(sl) & set(H.seeds(H.EVAL_SEEDS))
        and not set(sl) & set(H.seeds(H.TUNE_SEEDS))
    )
    tasks = [(rid, s, b, T) for rid in H.regime_ids() for s in sl for b in ("A1", "A3")]
    t0 = time.time()
    with Pool(int(os.environ.get("NW", 14)), initializer=_init) as p:  # noqa: PLW1508
        res = p.map(_task, tasks, chunksize=4)
    X = np.concatenate([r[0] for r in res])
    Y = np.concatenate([r[1] for r in res])
    log(f"collected {len(Y)} samples from {len(tasks)} runs in {time.time() - t0:.0f}s")
    import torch

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    mu, sd = X.mean(0), X.std(0) + 1e-6
    ymu, ysd = Y.mean(), Y.std() + 1e-6
    rng = np.random.default_rng(0)
    perm = rng.permutation(len(Y))
    nv = len(Y) // 10
    va, tr = perm[:nv], perm[nv:]
    Xt = torch.tensor((X - mu) / sd, dtype=torch.float32, device=dev)
    Yt = torch.tensor((Y - ymu) / ysd, dtype=torch.float32, device=dev)[:, None]
    net = torch.nn.Sequential(
        torch.nn.Linear(NFEAT + 2, 64),
        torch.nn.ReLU(),
        torch.nn.Linear(64, 64),
        torch.nn.ReLU(),
        torch.nn.Linear(64, 1),
    ).to(dev)
    opt = torch.optim.Adam(net.parameters(), 2e-3, weight_decay=1e-5)
    best, bstate = 1e9, None
    tri = torch.tensor(tr, device=dev)
    for ep in range(60):
        sh = tri[torch.randperm(len(tri), device=dev)]
        for i in range(0, len(sh), 2048):
            b = sh[i : i + 2048]
            loss = torch.nn.functional.mse_loss(net(Xt[b]), Yt[b])
            opt.zero_grad()
            loss.backward()
            opt.step()
        with torch.no_grad():
            v = torch.nn.functional.mse_loss(net(Xt[va]), Yt[va]).item()
        if v < best:
            best, bstate = v, {k: x.clone() for k, x in net.state_dict().items()}
    net.load_state_dict(bstate)
    sdict = {k: x.cpu().numpy() for k, x in net.state_dict().items()}
    (OUT / "a4").mkdir(parents=True, exist_ok=True)
    np.savez(
        OUT / "a4" / "q_net.npz",
        mu=mu,
        sd=sd,
        ymu=ymu,
        ysd=ysd,
        w1=sdict["0.weight"].T,
        b1=sdict["0.bias"],
        w2=sdict["2.weight"].T,
        b2=sdict["2.bias"],
        w3=sdict["4.weight"].T,
        b3=sdict["4.bias"],
    )
    log(f"val mse (standardised) {best:.4f}; var explained {1 - best:.3f}; device {dev}")
    ledger(
        "a4_train",
        {
            "train_seeds": [sl[0], sl[-1]],
            "n_samples": len(Y),
            "device": dev,
            "behaviour": "A1(voi_mult=3)+A3(eta=.2), eps=0.12 forced",
        },
        {"val_mse_std": float(best)},
        time.time() - t0,
    )


if __name__ == "__main__":
    main()
