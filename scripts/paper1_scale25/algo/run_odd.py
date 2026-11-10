# ruff: noqa
"""Odd-episode select-check for the even-selected v2 candidates (and any reference that exists only on even)."""

import json
import sys

import s25_common as sc
import s25_refs as rf
import s25_runner as rn

if __name__ == "__main__":
    w = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    sel = json.load(open(sc.OUT / "tables" / "v2_selected.json"))
    allspecs = {s["name"]: s for s in json.load(open(sc.OUT / "specs_v2.json"))}
    specs = [allspecs[n] for n in sel["selected"] if n in allspecs]
    need = {sel["rstar"], *sel["per_window_ref"].values()}
    extra = sorted(n for n in need if n in rf.EXTRA)  # refs that were only run on even episodes
    for pool in ("nine", "fresh"):
        rn.run(
            specs,
            sc.OUT / f"v2_odd_{pool}",
            pool,
            extra=extra,
            split="odd",
            seeds=tuple(range(10)),
            workers=w,
        )
