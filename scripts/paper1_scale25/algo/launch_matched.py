# ruff: noqa
import json
import sys
import s25_runner as rn
import s25_common as sc

if __name__ == "__main__":
    pool = sys.argv[1]
    w = int(sys.argv[2])
    specs = json.load(open(sc.OUT / f"specs_matched_{pool}.json"))
    rn.run(specs, sc.OUT / f"matched_{pool}", pool, workers=w)
