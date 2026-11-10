# Paper 3 — next actions

## 1. The discriminating experiment: payback certificates on real streams (not yet written)
H2 (repeated-look hurdles certify the wrong sign at .64–.86 on a synthetic flat null) is the
strongest confirmed finding, but it is synthetic. The next experiment tests whether it matters
on real streams. If B0-style hurdles do not lose realised payback on real data, the benchmark
paper loses its anchor and Paper 3 should stop.

Design (register before running; dev = the 23 exposed c4 streams, confirmation = the 4 sealed
streams already opened once for H5 are NOT fresh, so a new real batch is required):
- For each episode, run B0a/B0w/B0b/B1/B2 as promotion rules on the paired-loss stream.
- Score the realised net payback over the next h rounds after each certification, ex post and
  evaluator-side. Uncertified = 0.
- Primary: realised net payback per episode (B2 − best B0), stream-cluster CI. Secondary: the
  fraction of certifications with negative realised payback.

Code to write: `scripts/paper3/payback/run_real.py`, reusing `src/shiftlab/paper3/payback/certificates.py`
and the c4 loader in `src/shiftlab/paper3/transfer/`. Command once written:

```bash
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 ../shift-research-starter/.venv/Scripts/python.exe scripts/paper3/payback/run_real.py --data ../shift-research-starter/data/c4_sealed --h 50,100 --alpha 0.1 --out outputs/paper3/payback/real_dev
```

## 2. Required before any submission
- New real batch: ≥8 unexposed streams in ≥3 families, registered and sealed (D's
  `civic_records_sealed` is now opened).
- A synthetic grid where acquisition pays (never_switch is not optimal), then re-test H3.
- Native author code where public (WISE-ATTA GitHub; Drift2Act/RAR if released); otherwise keep
  the adapter labels.
- Fix the T1/T2/T3b gaps listed in 06_PROOF_AUDIT_B.md; restate T2 as known-τ.
- Install PaperBanana or record a decision on figure tooling.
- Cross-model review (codex or gemini) of claims and proofs.
