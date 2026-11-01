# Baseline and branch manifest

**Branch:** `research/shiftlab-sota-synthetic-search-2026-10-29` (independent worktree `../shiftlab-sota-search`), cut from `research/rpoq-s1-fatal-flaw-audit`.
**Starting SHA:** `0b1ce996431763d50b8c22e21dd3eece7c2dcf04` (`docs(rpoq_next): source scan via web search; Candidate A prior art found; conclusions revised`).
**Not touched:** `main`, `research/rpoq-s1-fatal-flaw-audit` (still at the starting SHA), historical outputs, protocols, verdicts, and any real-data file. **Scope: synthetic data only.** The CRSP panel pulled earlier in the parent session (outside Git) is not read in this phase.

## CI at the start
CI ("CPU checks", ruff, ruff format, mypy, full pytest, environment validation) on the starting SHA completed **success**. The Ruff findings from the earlier failing run (RUF046, C408, UP031, SIM115, PLC0206) had already been repaired on the parent branch, behavior-neutral; no historical result was regenerated.

## Historical-artifact integrity check
`results.json` in `outputs/rpoq_s6_crsp_headroom_v1`, `rpoq_s6b_crsp_asivs_v1`, `rpoq_s6c_crsp_mix_v1` match their recorded checksums. `runs.csv` in each fails `sha256sum -c` on the committed LF copy but **matches exactly once CRLF line endings are restored** (verified for all three): Python's `csv` writer emitted CRLF, Git normalized to LF on commit. This is a line-ending artifact, not content change. Recorded here so nobody mistakes it for corruption. Historical files were not modified.

## Workspace
`docs/sota_synthetic_search/`, `src/shiftlab/sota_search/`, `scripts/sota_search/`, `configs/sota_search/`, `tests/sota_search/`, `outputs/sota_search/`. New code reuses `shiftlab.monitoring` (RBF MMD, CUSUM) and the repo's prediction-powered e-value module where applicable.

## Resource budget (declared before any run)
Total compute for this phase: at most about 6 CPU-hours on this container; storage for new outputs at most 1 GB (raw per-seed arrays stored compactly; the experiment database holds every run). Individual batches must stop cleanly at their declared limit.
