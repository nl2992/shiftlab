# ruff: noqa
import json
import sys

import s25_common as sc
import s25_runner as rn

if __name__ == "__main__":
    pool = sys.argv[1]
    w = int(sys.argv[2])
    rn.run(
        [],
        sc.OUT / f"refgrid_{pool}",
        pool,
        extra=json.load(open("extra_refs.json")),
        split="even",
        seeds=tuple(range(5)),
        workers=w,
    )
