# 00. Reproducibility audit
- Registries are append-only SQLite (`runs` table with configuration hash). Summaries are CSV. The G1/G2 held-out outputs and the CRSP replay are single-run, seed-block-fixed.
- Earlier note: historical `runs.csv` checksums from the RPOQ phase only match after CRLF restoration (line-ending normalisation); this branch does not touch them.
- Per-seed alarm indicators were **not** saved in the held-out runs (only per-world summaries): Goal 3's paired inference cannot be recomputed from files and requires re-running the frozen configs with the same seeds (deterministic by construction; to be verified by reproducing the summary numbers exactly before using the new files).
- Runs in this branch that touch code: `detectors.py` gains an optional `uniform_cap` flag (default False, behaviour unchanged; existing identity tests still pass).
