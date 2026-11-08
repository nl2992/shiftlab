# QSG methods search (2026-11-07)

Working area for the four-contribution methods programme: Failure Atlas → method → synthetic
validation → real-data validation. Branch `research/qsg-methods-search-2026-11-07`, cut from
`main@9f62583a`.

- [development_protocol.md](development_protocol.md): the D0–D4 screens as registered, with their outcomes.
- [development_results.md](development_results.md): numbers and diagnoses.
- [synthetic_confirmation_protocol.md](synthetic_confirmation_protocol.md) (locked at `10ba0237`)
  and [synthetic_confirmation.md](synthetic_confirmation.md): **C3 PASS**.
- [candidate_ledger.md](candidate_ledger.md): every candidate and the decision on it.
- [sota_comparator_matrix.md](sota_comparator_matrix.md): comparators by mechanism.
- [publication_decision.md](publication_decision.md): status of each contribution.

Code lives in `scripts/qsg_methods_search/`; the method itself is `eqs_d.py`. Every registry plugs
into the Atlas v2 runner through `--extra`. Set
`PYTHONPATH="scripts/qsg_methods_search;scripts/failure_atlas_v2_flq"` and `OPENBLAS_NUM_THREADS=1`.

**Newer context read before starting.** More recent work sits on two branches.
- `origin/claude/shiftlab-methods-strategy-dba13e`: the SOTA fidelity pass, which closed tracks
  A and B and the pacing direction.
- `origin/codex/scoped-method-research-results-2026-11-06`: the gated adaptive-range
  predictability fix, corrected replays, and the HuffPost case study (verdict:
  `BENCHMARK_OR_CASE_STUDY_ONLY`).

This work does not rely on any of the superseded adaptive-range tables.

## Next-method cycle (2026-11-07 continuation)

[NEXT_METHOD_PLAN.md](NEXT_METHOD_PLAN.md) · [NEXT_METHOD_LEDGER.md](NEXT_METHOD_LEDGER.md) · [NEXT_METHOD_RESULTS.md](NEXT_METHOD_RESULTS.md) · [NEXT_METHOD_NOVELTY.md](NEXT_METHOD_NOVELTY.md) · [NEXT_METHOD_C3.md](NEXT_METHOD_C3.md) · [NEXT_METHOD_C4.md](NEXT_METHOD_C4.md) · [FINAL_PUBLICATION_DECISION.md](FINAL_PUBLICATION_DECISION.md). Verdict: INCOMPLETE; no candidate beat tuned fixed-discount Wald.
