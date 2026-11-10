"""Build the J table: for every development / synthetic stream, mean J over 2 seeds of all 144
configs on every episode, two cost scenarios, plus the reference-policy released-label log.
Sealed streams are never loaded (streams.load raises). Resumable: skips existing files."""

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from shiftlab.paper3.transfer import sim, streams, synth

OUT = Path("outputs/paper3/transfer/jtable")
N_SYNTH = 6


def job(spec):
    name, fam, kind = spec
    f = OUT / f"{name}.npz"
    if f.exists():
        return name, 0.0
    t0 = time.time()
    if kind == "real":
        st = streams.load(name)
        l0, l1, delay = st.l0, st.l1, st.delay
    else:
        l0, l1, delay = synth.make_stream(fam, int(name.rsplit("_", 1)[1]))
    res = {}
    for sc, costs in sim.SCENARIOS.items():
        Js, labs, sws = [], [], []
        for seed in (0, 1):
            o = sim.simulate(
                l0,
                l1,
                delay,
                costs,
                seed=seed,
                log_cfg=sim.REF_CFG if sc == "primary" and seed == 0 else None,
            )
            Js.append(o["J"])
            labs.append(o["labels"])
            sws.append(o["switches"])
            if "rel" in o:
                res["rel"], res["req"] = o["rel"], o["req"]
        res[f"J_{sc}"] = np.mean(Js, 0).astype(np.float32)
        res[f"labels_{sc}"] = np.mean(labs, 0).astype(np.float32)
        res[f"sw_{sc}"] = np.mean(sws, 0).astype(np.float32)
    res["never"] = sim.never_switch_J(l0).astype(np.float32)
    res["dis"] = (l0 != l1).astype(np.int8)
    np.savez_compressed(f, delay=delay, family=fam, **res)
    return name, time.time() - t0


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    specs = [(n, streams.REGISTRY[n][1], "real") for n in streams.dev_streams()]
    specs += [(f"{fam}_{i}", fam, "synth") for fam in synth.FAMILIES for i in range(N_SYNTH)]
    with ProcessPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 8) as ex:
        for name, dt in ex.map(job, specs):
            print(name, round(dt, 1), flush=True)
