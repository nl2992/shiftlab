# RPOQ-next research charter

**Branch:** `research/rpoq-s1-fatal-flaw-audit` (isolated from `main`). **Opened:** 2026-10-30. **Start commit:** `ba0298ef`.

**Objective.** Find a credible, reproducible improvement over a strong existing method for budget-constrained, delayed-feedback, sequential monitoring with prediction-powered e-values, and establish when and why it works. Incremental methodology (extension, hybrid, speed-up, robustness, edge case, oracle approximation) is in scope. No claim of publication readiness without evidence.

**Fixed constraints.**
- Historical RPOQ protocols, results and outputs stay unchanged; negative results are never edited.
- The CRSP 2020–2025 test split has been examined many times. It is reusable only for clearly labelled *exploratory* replay. No further tuning of ASI-MIX on it.
- The outcome-reading oracle allocation is a hindsight diagnostic. It is not implementable and not a reachable ceiling.
- Validity is stated per setting; a candidate that fails a setting is reported as invalid there.
- Working style: Ponytail "full" (smallest complete change, reuse repo components, one small test per new piece of logic, `shortcut:` comments).

**Source access limit (blocks parts of Cycle 1).** From this session, `arxiv.org`, `proceedings.mlr.press`, `proceedings.neurips.cc`, `people.bath.ac.uk`, `doi.org` and `openreview.net` do not resolve; only GitHub and PyPI are reachable. Primary papers could therefore **not** be re-read this session. Each source in the matrix carries a status:
- `CODE-READ`: authors' released code read this session.
- `REPO-AUDIT`: relies on this repository's earlier primary-text audit; not re-read now.
- `UNREAD`: no information available to this project; no claim is made about its content.

**Ledger:** [`RESEARCH_LEDGER.md`](RESEARCH_LEDGER.md) (append-only).
