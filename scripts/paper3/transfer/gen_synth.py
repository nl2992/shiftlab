from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from shiftlab.paper3.transfer import synth

SYN = Path("outputs/paper3/transfer/synth_losses.npz")


def mk(a):
    return synth.make_stream(*a)


if __name__ == "__main__":
    specs = [(f, i) for f in synth.FAMILIES for i in range(6)]
    with ProcessPoolExecutor(10) as ex:
        res = list(ex.map(mk, specs))
    np.savez_compressed(
        SYN,
        **{f"{f}_{i}_l0": r[0] for (f, i), r in zip(specs, res)},
        **{f"{f}_{i}_l1": r[1] for (f, i), r in zip(specs, res)},
        **{f"{f}_{i}_d": np.array(r[2]) for (f, i), r in zip(specs, res)},
    )
    print("ok")
