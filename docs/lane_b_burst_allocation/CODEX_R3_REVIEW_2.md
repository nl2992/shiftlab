# Codex pre-freeze recheck (R3 round 2) and validity-note review

`codex exec --sandbox read-only`, high, worktree `2994f54`, 2026-10-29 22:2x local. Verbatim:

**OPSD: DO-NOT-FREEZE. Binance: FREEZE-WITH-NOTES. Validity note: INCORRECT.**

Reviewed `51d3ffb` plus current amendments through `2994f54`. No edits or `data/` reads. Tests inspected, not rerun: no Python installation is available.

**Part 1 — prior blockers**

| Blocking item | Assessment | Evidence |
|---|---|---|
| OPSD forecast clock | **RESOLVED** under the declared snapshot/publication assumptions. Berlin local days and D−1 10:00 local replace UTC blocks. | [opsd_reserve.py:130](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:130) |
| OPSD free outcome information | **PARTIAL.** Calendar-only `x`, hidden predictions/`tau`, and default hour-07 removal fix the direct disclosures. A DST exception remains below. | [opsd_reserve.py:237](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:237), [opsd_reserve.py:296](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:296) |
| OPSD future selection and split embargo | **PARTIAL.** Missing actuals retain scheduled actions; boundary labels are purged. However, future archived timestamp irregularities still veto the policy pair without a decision-time availability justification. | [opsd_reserve.py:255](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:255), [opsd_reserve.py:109](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:109), [opsd_reserve.py:364](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:364) |
| Binance free previous-loss reconstruction | **RESOLVED for the amended contract.** Return features removed; actions explicitly remain public. | [binance_momentum.py:143](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/binance_momentum.py:143) |
| Binance accounting/formula | **RESOLVED.** Exact clipped loss; imposed switch cost follows `fee`; standalone turnover is diagnostic. | [binance_momentum.py:34](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/binance_momentum.py:34), [binance_momentum.py:117](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/binance_momentum.py:117) |
| Binance timestamp precision | **RESOLVED.** Nanoseconds retained; decisions use the following hour boundary. | [binance_momentum.py:87](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/binance_momentum.py:87), [binance_momentum.py:141](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/binance_momentum.py:141) |

The holdout CSV-parser issue is also **RESOLVED**: [opsd_reserve.py:95](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:95).

**New OPSD blocker:** on autumn DST Sunday, the 23:00 delivery slot minus **48 elapsed hours** is Saturday 00:00 local. Thus Saturday’s load can affect Sunday’s candidate action at Saturday 10:00, before Saturday’s daily label releases Sunday 01:00. Dropping hour-07 does not establish the lead decision’s promised boundary. Fix the lag alignment/availability mask or explicitly amend that promise. [opsd_reserve.py:282](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/opsd_reserve.py:282), [R1_task_specs.md:446](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/docs/lane_b_burst_allocation/R1_task_specs.md:446).

The **label-limited auditor contract is honest and adequate for a narrowed audit-budget benchmark**, provided every method receives identical public actions and the null conditions on that channel. It budgets purchased feedback, while policies consume unrestricted public histories. The collision audit establishes neither full-stream non-reconstructability nor absence of useful free outcome information; unique OPSD keys provide no such evidence. [__init__.py:230](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/__init__.py:230).

Binance freeze notes: retain that interpretation, imposed costs/idealized execution, and descriptive-only real-stream claims. No calibrated false-promotion or profitability claim follows.

**Part 2 — validity table**

| Claim | Assessment |
|---|---|
| Fixed delay / Binance d=1 | **Qualified correct; derivation misstated.** Unqueried events update immediately, so wealth is not literally a shifted prefix. For `ε≥0`, their extra factors are ≤1, giving domination by the chronological prefix. This requires a null valid under the full chronological history/current context—not merely released-label history. |
| Outcome-independent out-of-order delay | **Incorrect generally.** Event-time conditional means do not imply release-order conditional means. Fixing bounds/stakes before release does not repair this. |
| Missing at random | **Qualified correct** for the conditional-mean calculation, with MAR and query randomization relative to the same sufficient filtration, `ε≥0`, and a justified update order. Missing means increment `−ε`, not “skip update.” Removing negative observations can increase wealth; “only remove positive evidence” is false pathwise. |
| Informative delay/missingness not covered | **Correct.** |

Implementation: [baselines_v2.py:72](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/contract/baselines_v2.py:72), [baselines_v2.py:81](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/contract/baselines_v2.py:81), [harness_v2.py:151](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/contract/harness_v2.py:151).

Concrete counterexample to the general reordering claim: `q=C=1, ε=0`; generate up to twenty blocks of eight fair ±1 increments, setting subsequent increments to zero after the first all-positive block. The chronological null holds. Deterministic reverse releases expose that successful block before preceding losses: the implemented stake mixture reaches **26.576**, with probability at least **0.07529 > α=0.05**.

Finally, OPSD’s delivered labels actually have **fixed d=2**. The apparent offset 1 comes from `searchsorted` returning the horizon sentinel for an unreleased terminal label, not calendar-driven variable delay. [__init__.py:189](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/src/shiftlab/real_tasks/__init__.py:189), [test_real_tasks.py:205](C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/tests/test_real_tasks.py:205).
