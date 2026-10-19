"""Locked small simulation grid, not a confirmatory scientific study."""

from shiftlab.benchmark import run
from shiftlab.core.config import Config

for paper in [1, 2, 3]:
    for shift in ["none", "benign", "concept", "variance"]:
        print(run(Config(paper=paper, shift=shift)), flush=True)
