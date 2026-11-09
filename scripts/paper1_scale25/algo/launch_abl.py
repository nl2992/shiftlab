# ruff: noqa
import json
import sys
import s25_runner as rn
import s25_common as sc

if __name__ == "__main__":
    pool = sys.argv[1]
    w = int(sys.argv[2])
    specs = json.load(open(f"specs_abl_{pool}.json"))
    extra = json.load(open("extra_refs.json"))
    rn.run(specs, sc.OUT / f"abl_{pool}", pool, extra=extra, workers=w)
