# Integrated development run: provenance audit

**Run:** `outputs/shiftguard_unified/integrated_development/pipeline_matched_eventwise_dev_10_v1/`  
**Manifest timestamp:** 2026-10-26 08:28:07 UTC  
**Audit status:** artifact hashes rechecked against the current worktree; the execution-time protocol source is not recoverable from the current protocol file.

## Rechecked artifacts

The manifest's SHA-256 values still match the current files for the runner (`src/shiftlab/dive/integrated_pipeline.py`), `budgeted_promotion.py`, `eprocess.py`, and `decision_harm_experiment.py`. They also match the saved Parquet seed metrics, summary CSV, and paired-contrast CSV. The runner hash is `06ca19f4ff296fdf701e9ece02fcfb8d27541feb33566b8d9f91789d8a9677dc`.

The protocol hash recorded by the manifest is `e8cd66237da83468b0d9bc25193f52bfab0303ccb09aacb6659a59652c331220`. The current `integrated_benchmark_protocol.md` hashes to `15076aae6f5f4b21e332e0e9a9175506187268a259ac787eee5a83e6e7820456`, so it is not the byte-for-byte protocol source used at execution. No protocol snapshot matching the recorded hash is present in the run directory or current worktree. The manifest's original hash is preserved as evidence; it has not been rewritten to match the current draft.

## Interpretation

The run data and executable source artifacts are intact and their recorded hashes verify. Protocol provenance is incomplete: the original protocol bytes cannot be independently inspected from the current files. Consequently, the run remains exploratory development evidence, not a preregistered or confirmatory result. Its reported design should be read from the execution manifest and the matched-development report, while the current protocol remains a changing design draft.

This gap must be closed for the next run by copying the exact frozen protocol into the run output before execution and hashing that copy. The runner should record the snapshot path and its hash; post-run edits should create a new protocol version rather than modifying the snapshot.
