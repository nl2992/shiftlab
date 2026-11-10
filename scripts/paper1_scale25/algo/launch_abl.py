# ruff: noqa
import json
import sys

import s25_common as sc
import s25_runner as rn

if __name__ == "__main__":
    pool = sys.argv[1]
    w = int(sys.argv[2])
    specs = json.load(open(f"specs_abl_{pool}.json"))
    rn.run(specs, sc.OUT / f"abl_{pool}", pool, extra=[], workers=w)
