"""Run the separately registered sparse-start screen using the frozen shared harness."""

from __future__ import annotations

import run_atlas_gap_markov_sui_development_v1 as screen

screen.PROTOCOL = "docs/failure_atlas_gap_markov_sui_sparse_development_protocol_v1.md"
screen.OUT = screen.ROOT / "outputs/failure_atlas_gap_markov_sui_sparse_dev"
screen.SEEDS = tuple(range(720020, 720040))

if __name__ == "__main__":
    screen.main()
