# Track C: PAVE+ (delay-aware acquisition)

Full record: branch `research/methods-recovery-2026-11-07`,
`docs/methods_recovery/40_PAVE_PLUS_FEASIBILITY.md` (commit `25f0bc95`).
Code: `scripts/methods_recovery/pave_plus_feasibility.py`.

**Prior evidence (GAVE-R WP5).** Delay-gated PAVE (PAVE iff d ≥ 2T/(B+2)) was 4.4% cheaper than
DSS/uniform acquisition in 9 long-delay cells (d=50).

**Bounded feasibility (this cycle).**
- Evidence fixed (DSS shell); only acquisition varies.
- Simple rules: S1 deadline cutoff, S2 fixed pending cap, S3 front-loaded pacing, S4 = S1+S2.
  Each was tuned on 20 fresh tuning seeds per cell (block 101500000).
- Evaluation: 60 fresh seeds per cell (block 101600000) on 9 d=50 cells, 9 d=100 cells and 6
  d=10 controls. All blocks were registered before running.

| contrast (% of uniform J/T, paired bootstrap 95% CI) | d=50 (primary) | d=100 | all 18 gate-on |
|---|---|---|---|
| PAVE − best simple rule (S1, m=50) | −2.02 [−3.24, −0.78] | −1.65 [−2.70, −0.60] | −1.83 [−2.67, −1.02] |
| best simple rule − uniform | −1.43 [−2.60, −0.21] | −0.14 [−1.09, +0.80] | −0.78 [−1.57, −0.01] |
| PAVE − `episode_front` | **+0.01 [−1.24, +1.30]** | +0.57 [−0.45, +1.57] | +0.29 [−0.52, +1.10] |

**Verdict: STOP.**
- PAVE's long-delay gain is fully matched by the existing front-loading baseline
  `episode_front`, which meets directive §6.7.
- A pending cap adds nothing.
- A deadline cutoff captures about 41% of the d=50 gain.
- The PAVE gain sits in 4–5 cells, and PAVE loses to uniform in others.

There is no defensible PAVE+ algorithm to advance.
