"""H5 confirmation: open the sealed group civic_records_sealed ONCE (guard lifted only here via open_sealed=True),
verify sha256 against the group hash registered in 03D, build the J table for the 4 sealed streams with the
unchanged simulator (same code path as scripts/paper3/transfer/build_jtable.py), and evaluate frozen
D2-MLP + OOD fallback vs global fixed (trained on all 33 real dev streams + synthetic, scope 'all', primary scenario)."""

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import OUT as COUT
from _common import ledger

from shiftlab.paper3.transfer import data, sim, streams
from shiftlab.paper3.transfer import methods as M
from shiftlab.paper3.transfer.data import SRec

OUT = COUT / "h5"
REG_GROUP = "f37dc40f3bdea96f1e2e54baa212c8a2391fec1ca37f0368108bd8504c7ae460"


def jtable(name):
    st = streams.load(
        name, open_sealed=True
    )  # authorised by registration 04_EXPERIMENT_PROTOCOL.md (H5)
    res = {}
    for sc, costs in sim.SCENARIOS.items():
        Js, labs = [], []
        for seed in (0, 1):
            o = sim.simulate(
                st.l0,
                st.l1,
                st.delay,
                costs,
                seed=seed,
                log_cfg=sim.REF_CFG if sc == "primary" and seed == 0 else None,
            )
            Js.append(o["J"])
            labs.append(o["labels"])
            if "rel" in o:
                res["rel"] = o["rel"]
        res[f"J_{sc}"] = np.mean(Js, 0).astype(np.float32)
        res[f"labels_{sc}"] = np.mean(labs, 0).astype(np.float32)
    res["never"] = sim.never_switch_J(st.l0).astype(np.float32)
    res["dis"] = (st.l0 != st.l1).astype(np.int8)
    f = OUT / "jtable"
    f.mkdir(exist_ok=True)
    np.savez_compressed(f / f"{name}.npz", delay=st.delay, family=streams.REGISTRY[name][1], **res)
    K = res["J_primary"].shape[0]
    fam = streams.REGISTRY[name][1]
    return SRec(
        name,
        fam,
        fam,
        True,
        int(st.delay),
        K,
        max(2, int(np.ceil(streams.EARLY_FRAC * K))),
        {s: res[f"J_{s}"].astype(float) for s in sim.SCENARIOS},
        {s: res[f"labels_{s}"].astype(float) for s in sim.SCENARIOS},
        res["rel"],
        res["dis"],
        res["never"].astype(float),
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    # 1. hashes BEFORE any evaluation
    sh = streams.seal_hash()
    files = {
        n: hashlib.sha256(streams.path_of(n).read_bytes()).hexdigest()
        for n in streams.SEALED_STREAMS
    }
    match = sh["group_sha256"] == REG_GROUP
    hrec = {
        "group_sha256_computed": sh["group_sha256"],
        "group_sha256_registered": REG_GROUP,
        "match": match,
        "array_sha256": sh["streams"],
        "file_sha256": files,
    }
    (OUT / "hash_check.json").write_text(json.dumps(hrec, indent=1))
    ledger("H5", "sealed_open_hash_check", {"streams": streams.SEALED_STREAMS}, hrec)
    print("hash match:", match, flush=True)
    if not match:
        print("ABORT: group hash mismatch; H5 NOT RUN")
        sys.exit(2)
    # 2. train frozen recommenders on dev only
    recs = data.load_all()
    real = [r for r in recs.values() if r.real]
    syn = [r for r in recs.values() if not r.real]
    ctx = M.build_ctx(real, syn, "all")
    M.fit_mlp(ctx)
    ood = M.OOD(ctx)
    gf = M.global_fixed(ctx, "primary")
    # 3. evaluate
    rows = []
    for n in streams.SEALED_STREAMS:
        r = jtable(n)
        x = data.embed(r, 0, r.n_early, sim.SCENARIOS["primary"])
        ev = r.J["primary"][r.n_early :].mean(0)
        th = int(M.predict(ctx, "mlp", x).argmin())
        is_ood, dist = ood.is_ood(x)
        th_f = gf if is_ood else th
        ps = M.per_stream_tuning(r, "primary")
        rows.append(
            {
                "stream": n,
                "family": r.family,
                "K": r.K,
                "n_early": r.n_early,
                "ood": bool(is_ood),
                "ood_dist": float(dist),
                "ood_thr": ood.thr,
                "theta_mlp": th,
                "theta_fallback": th_f,
                "theta_global": gf,
                "theta_per_stream": ps,
                "J_global_fixed": float(ev[gf]),
                "J_mlp": float(ev[th]),
                "J_mlp_ood": float(ev[th_f]),
                "J_per_stream_tuned": float(ev[ps]),
                "J_hindsight_UNATTAINABLE": float(ev.min()),
                "J_never": float(r.never[r.n_early :].mean()),
                "dJ_mlp_ood_vs_gf": float(ev[th_f] - ev[gf]),
                "dJ_mlp_vs_gf": float(ev[th] - ev[gf]),
            }
        )
        print(rows[-1], flush=True)
    jg = float(np.mean([x["J_global_fixed"] for x in rows]))
    md = float(np.mean([x["dJ_mlp_ood_vs_gf"] for x in rows]))
    res = {
        "rows": rows,
        "mean_J_global_fixed": jg,
        "mean_dJ_mlp_ood_vs_gf": md,
        "rel_pct": 100 * md / jg,
        "mean_dJ_mlp_vs_gf": float(np.mean([x["dJ_mlp_vs_gf"] for x in rows])),
        "mean_dJ_per_stream_vs_gf": float(
            np.mean([x["J_per_stream_tuned"] - x["J_global_fixed"] for x in rows])
        ),
        "threshold": -0.01 * jg,
        "H5_SUPPORTED": bool(md >= -0.01 * jg),
        "global_fixed_theta": int(gf),
        "grid_theta": [float(v) for v in sim.GRID[gf]],
    }
    (OUT / "summary.json").write_text(json.dumps(res, indent=1))
    ledger(
        "H5",
        "confirm_run",
        {"streams": streams.SEALED_STREAMS, "scenario": "primary", "scope": "all"},
        res,
        time.time() - t0,
    )
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main()
