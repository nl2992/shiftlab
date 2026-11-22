# RB-DP code supplement (anonymised)

Exact risk-budget dynamic programme for causal-null-safe promotion, with the tests, the exact-rational constant audits
and the experiment scripts behind the paper's tables.

```
src/shiftlab/paper4/   risk_budget_dp.py (reference solver, delay 1), risk_budget_dp_fast.py (vectorised),
                       risk_budget_dp_d2.py (delay 2), frontier_cuts*.py (certified exact reference)
src/shiftlab/dive/     game and regime-model definitions used by the reference
theory_C/gamma_lib.py  exact premium cells used by the tests
tests/                 108 tests: sandwich [L, U] against the exact reference, fast-vs-reference agreement, delay 2
audits/                constant_audit.py, b4_/b5_constant_audit.py: exact rational enumeration for Theorem 3(3), B = 3-6
experiments/           E1-E4 runners, white-noise control, real-stream fit and evaluation
```

Run the tests (about 75 s):

```
pip install numpy scipy pytest
PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m pytest tests -q
```

Run an audit: `python audits/constant_audit.py` (output committed beside it as `*.txt`).

The experiment scripts read result and data paths from the full repository layout; they are included for inspection and
for the exact procedures, not as a self-contained rerun of the real-data panel.
