# Phase C pivot memo (2026-10-29)

## What failed and why

- **RLS (recurrence-locked switching) is dead** (`C2_rls_narrowed_theory.md`).
  - The duration-aware MLE forecaster has exactly RLS's likelihood, estimate, planner and gate.
  - The only difference is query design, which is standard Bayesian experimental design.
  - Thompson sampling on the same posterior matches or beats RLS in all 12 primary-budget cells.
  - RLS's edge at exploratory budgets (4–20% of oracle gain at B ≥ 120) is better-tuned standard
    design.
  - The only provable floor of order SΔ·min(σ,d) is against a jitter-aware oracle, so it cannot
    separate RLS from any forecaster.
- **Other C0 candidates.** Harm-budgeted provisional deployment was discarded by constant-sum
  symmetry, and split-clock switching needs an information structure the frozen tasks lack.
- **Structural reason (C0 binding constraints, consistent with Lane A's G1 record).**
  - With one shared label stream at a fixed delay, acquisition reduces to timing.
  - Generic timing rules are already prior art.
  - Risk is fixed at the first promotion, after which the problem is a closed single-law delayed
    POMDP.
  - On this information structure, Lane A and Lane B together have now closed:
    - VOI and rollout;
    - risk-budget states;
    - futility stopping;
    - delayed-belief POMDPs;
    - belief compression;
    - e-detector restarts;
    - two-phase costed bandits;
    - state sensing;
    - recurrence forecasting.

## Recommendation: change the information structure, not the mechanism

These are ranked by plausibility of a non-composition theorem plus real data to test it.

1. **Delay-heterogeneous label channels (split-clock).**
   - **Structure:** a fast, biased surrogate label (cheap, short delay) alongside a slow gold label
     (costly, long delay).
   - **Algorithmic question:** allocate the budget across channels and use the fast channel for
     rollback, which needs no alpha-certification, while the slow channel drives certified
     promotion.
   - **Target:** a gain of order Δ·(d_gold − d_fast) per reversal over single-channel methods.
   - **Main risk:** reduction to controlled sensing with delay-shifted costs, or to the repo's
     delayed-PPI work. Audit those first.
   - **Real data candidate:** OPSD has a natural fast channel. The day-ahead forecast error of the
     ENTSO-E forecast, or intraday actuals released hourly, can serve as a surrogate before the
     day's full label. This needs a new task spec and freeze.
2. **Many candidates sharing one queried label (selection among K).** One query reveals all K
   candidates' losses on a disagreement set that changes with K. The question is acquisition and
   switching when certification has to cover a growing candidate set (multiplicity grows, the
   cost per label does not). Main risk: best-arm identification under full information, and
   AnyRank / OCS (already in the prior-art matrix).
3. **Selective labels (outcome observed only for the deployed action).** This is genuine bandit
   coupling of information and deployment, which is where switching has real exploration value.
   Main risk: Lane A's audits and the matrix's G1 verdict (Waudby-Smith et al., Lindon–Kallus) mark
   bandit-feedback harm monitoring as covered. It needs a sharper residual.

## Exit applied

The phase C exit rule fired: every candidate failed C0/C1 on the current information structure.
The Lane B algorithm loop is stopped (cron deleted). Resuming means choosing one of the pivots
above, which changes the task contract (a new task spec and freeze) and is a goal-level decision.

## Update 2026-10-29: phase D (split-clock) also exits

`D2_split_clock_mechanism.md`:
- **Search.** The targeted search (including a proper read of Ao et al. 2601.21471) found no published
  method covering the full target.
- **Composition.** The adaptive split-clock rule still decomposes into a per-phase index, a
  change-detection CUSUM on the surrogate, a gold backstop, scout/confirm, and a betting e-process.
- **Impossibility (proved).** With a bias shift `b ≥ 2βΔ`, no rule rolls back before `d_g` without
  spending its false-rollback budget.
- **Monte Carlo.** The plain two-phase composition wins 8 of 9 cells. The fast channel helps rollback
  only at sign agreement 0.8 with no bias shift, and never at Binance's 0.563.
- **Real data.** Neither real task has an informative fast channel: OPSD 0.069 and Binance 0.563
  against the 0.6 floor.

## Cumulative assessment (Lanes A and B, 2026-10-28/29)

Across three Lane B candidate families (burst allocation, recurrence locking, split clock) and
Lane A's G1 record, every mechanism on this two-policy, common-label, delayed, hard-budget,
causal-null contract decomposes into standard sequential design, change detection, planning or
futility pieces. Separations, where they exist, are between compositions, or against oracles that
cannot separate learners.

Remaining information structures, which are untested and goal-level choices:
1. **Many candidates sharing one queried label**, where certification multiplicity grows while
   label cost does not.
2. **Selective (bandit) labels**, observed only for the deployed policy, which is genuine
   exploration–deployment coupling.
3. **Retrospective gold audits of past rounds selected on fast labels** (Ao-style auditing with
   delay and reversibility). This has high composition risk because of Ao et al. and delayed PPI.
