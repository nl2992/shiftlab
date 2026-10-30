# 00. Baseline manifest (HG validation and novelty plan)

- Continuation branch/worktree: `research/hg-validation-and-novelty-2026-10-30`, branched from the current synthetic-search HEAD **bb740578c2b0cdd64db70fe7587a8de2d3791d70** (also pushed on `research/shiftlab-sota-synthetic-search-2026-10-29`). No uncommitted work at branch time.
- SHA-256 of source, configs, result summaries, SQLite registries, previous docs and the CRSP replay outputs: `outputs/hg_validation/baseline_sha256.txt`. Nothing under `outputs/sota_search/` or `docs/sota_synthetic_search/` is modified by this branch.
- Lint: `ruff check` clean. Tests: `tests/sota_search` 12 passed.
- Exposed pools (NOT new confirmation): dev pool (19 worlds, seeds 1000+), G1 held-out (seeds 5000+, labels 5500+, spent once), G2 held-out (seeds 7000+, labels 7500+, spent once), CRSP replay (2020–2025 test period, exposed also in earlier RPOQ work). Any new confirmation needs new seed blocks (≥ 20000) and generator structures not used so far.
