# Stage 0 summary (T0.1–T0.8)

**Recorded 2026-10-28.** All eight Stage 0 tasks in `IMPLEMENTATION_READINESS_GATE.md` are done. Each
was committed separately on `research/phase-progress-2026-10-27`, and local `main` was fast-forwarded
after each commit. Nothing was pushed. No new seeds were used, no data was downloaded, and no frozen
evaluation was rerun. T0.5 replayed a 20-seed CPU subset in a temporary directory, for verification
only.

| Task | Deliverable | Commit | Outcome |
|---|---|---|---|
| T0.1 seed registry | `configs/seed_registry.yaml`, `src/shiftlab/seed_registry.py`, `tests/test_seed_registry.py` | `596c06b` | 247 blocks. **103 overlapping pairs:** 2 known, plus **101 previously undisclosed** (50 same-offset prefix or rerun pairs, 51 cross-study reuses), now disclosed. `allocate()` returns the lowest free aligned block in [1e8, 2³¹). |
| T0.2 E1 verifier | `scripts/stage0_e1_verify.py`, `T0.2_e1_verification.md`, `e1_verification.json` | `6c9a39b` | 63 checks: 62 PASS, 0 FAIL, 1 INFO. 32/32 artifact hashes match. Independent of `shiftlab`. |
| T0.3 Lemma L test | `tests/test_lemma_l_propensity_invariance.py` | `0a31348` | 7 pass. HT wealth at ε = 0 is propensity-free on the production code. ε > 0, PPI and empirical Bernstein are shown to differ. |
| T0.4 errata | `ERRATA.md` | `f4108d7` | 10 entries. No historical file edited. |
| T0.5 Target-Scout drift | `T0.5_target_scout_equivalence.md` | `c3008a0` | **EQUIVALENT on a subset.** The change adds logging keys and typing; 78,400 fields matched exactly. The CUDA path and the full grid were not rerun. |
| T0.6 WP4 re-hash | `scripts/verify_wp4_freeze.py`, `tests/test_wp4_freeze_portable.py` | `d9292e7` | 7/7 files match. `orientation_replay.py` was frozen over its CRLF bytes, so an LF-only check would have failed on a fresh checkout. The verifier now accepts the raw, LF and CRLF forms. |
| T0.7 validity table | `VALIDITY_TABLE.md` | `71106b2` | 26 arms. Reviewed by Codex (xhigh, read-only); every finding was lead-verified and applied. 18 open obligations. |
| T0.8 Lemma write-up | `LEMMA_L.md` | `cce969f` | Statement, proof, local ε bound, and an applicability table linked to the tests. |

## Consequences for the claim matrix (apply when the manuscript is drafted)

1. **K8 wording.** WP4's "68/68 cells at 0/1,000" holds only at the **primary ε = 0.1**. At ε = 0,
   53 of 68 cells have zero alarms, and the maximum is 28/1,000; this level is descriptive. The 0.72%
   all-cell bound applies only to the 68 primary cells. (T0.2)
2. **K6 and H4 metric.** The H4 numbers (+664.64, …, −1,148.46) are **expected (oracle) net gain**, not
   realised gain. For example, q1_fallback's realised deployment gain under boundary harm is 273.39.
   Name the metric wherever these numbers are quoted. (T0.2)
3. **Q2 is not a full-cost net-benefit certificate.** The integrated scout-and-certification step
   tests `E[I_t(g_t − s) | F_{t−1}] ≤ 0`, with the switch rate charged only on selected contexts. Any
   statement that Q2 "certifies net benefit after switching cost" must be withdrawn or the increment
   changed. This bears on E3/H-B3 design (P2 must state which estimand the certify arm targets).
   (T0.7, Codex FATAL to that interpretation)
4. **The PPE gated alias aliases gated PPI, not gated HT.** It uses a single 0.9 stake and has the
   highest S2 alarm count in the panel (151/16,000; upper bound 1.953%, still ≤ 5%). (T0.7)
5. **The PPRM calibration figure was misattributed.** The 0/2,000 belongs to the paired-cost block
   monitors. PPRM targets predictive risk and has no charter-null guarantee. (T0.7)
6. **Composition (Q1→Q2→Q3).** A union bound is valid if each later stage is conditionally valid. That
   is not yet proved, so "not controlled; not claimed" stands. (T0.7)
7. **Seed reuse.** The 51 cross-study overlaps mean some calibration and confirmation blocks share
   generator seeds with other studies. Studies that are reported together must say so. **E2–E4 must take
   fresh blocks from `allocate()` and register them before running.** (T0.1)

None of these changes a headline number, and none triggers an abandonment condition. No E1 failure is
validity-critical.

## Gate status

- **Stage 0: complete.**
- **Stage 1 (P1–P4 protocol freezes) is now unblocked.** Each freeze needs a protocol doc, a SHA-256 freeze
  record and a Codex protocol review before Stage 2 runs.
- **P2 must also handle item 3 above,** and P1–P3 must take seeds from the registry.
- **User blockers U1–U4 are unchanged:** CUDA-scale E3 approval, the deferred EIA pull, a GitLab mirror,
  and push authorisation.
