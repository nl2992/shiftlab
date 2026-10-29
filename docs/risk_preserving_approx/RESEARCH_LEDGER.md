# Research ledger (append only)

## 2026-10-29 — Mission adoption and isolated baseline

- Base commit: `ec42a2da9fdf59a6cf26970fb19aa9d5fb8973cc`; toolkit commit: `cfd0c00`.
- Governing objective: risk-preserving approximation of the existing two-law
  budgeted delayed-feedback switching oracle, per the verbatim research brief.
- Git action: fetched origin, confirmed no existing requested branch, created
  the exact requested branch/worktree from origin/main, carried pinned toolkit.
- Hypotheses A/B/C remain research candidates; no novelty or theorem claim made.
- Existing reductions and counterexamples remain reference evidence, including
  posterior aliasing, finite-memory limitations and scalarized POSG representation.
- Work products: brief, initial plan, baseline manifest and branch guidance.
- Tests/experiments: no solver or experiment run at this administrative checkpoint.
  Integrity checks compare Git blobs; prior setup vendor checksums remain pinned.
- Parameters/seeds/results: none allocated or generated. Historical artifacts and
  holdouts are untouched. No new outcome inferred from historical solver anchors.
- Decision: continue problem reconstruction and theorem specification before code.
- Remaining uncertainty: compact risk-relevant state, nonvacuous value error,
  optimization versus verification complexity, and exact prior-art equivalence.

## 2026-10-29 — Working plan

- Added `WORKING_PLAN.md` with the operating contract, ordered research stages,
  candidate-specific checks, exit gates, oracle comparisons and evidence rules.
- Planning only; no new solver execution, experiment, seed allocation or theorem
  claim. Next checkpoint: reconstruct the reference problem and verify available
  small-instance anchors in a branch-local environment.

## 2026-10-29 — Reference verification and theorem target

- Starting commit e04e5ad; base ec42a2da9fdf59a6cf26970fb19aa9d5fb8973cc.
- Created branch-local locked environment with `uv sync --locked --extra dev`.
- Focused tests: 14 passed in 25.47 s. Re-ran registered T=6–8 fixed-budget
  solver protocol to `outputs/risk_preserving_approx/oracle_reproduction_20261029`;
  tracked copy `oracle_reproduction_20261029.json`, SHA-256
  8dfa7dbd6a90a6910b9016720ded1119abe9be87e4a7a80e5d4c702748b1663c.
  T6/T7 reference values and exact recovered risk reproduced; T8 full builder
  reached node cap, so no T8 independent full-oracle certification.
- All 16 baseline reference Git blobs matched the recorded base hashes. No prior
  file, protocol, seed or historical output was changed. No real-data rows or
  reserved holdouts were opened; existing CRSP panel presence was checked only.
- Added problem/theorem specification, initial primary-source comparison and an
  elementary PROVED conditional safety-repair lemma. This lemma is standard
  mixing, not a novel method or proof of a scalable near-optimal planner.
- The alternative-posterior aliasing example is a concrete obstruction to A's
  simplest representation. Compact risk-relevant state, efficient certification
  and a value guarantee remain unresolved; the source equivalence audit remains
  incomplete. No algorithm is selected and no efficacy experiment has run.
- Decision: continue A's structural abstraction screen; independently examine B's
  verification/optimization distinction and then C if the A lemma fails. Existing
  real-data source audits limit CRSP to exploratory retrospective predictive replay;
  success requires an appropriately matched real-data comparison, not a synthetic
  check alone.

## 2026-10-29 — Risk-preserving continuation approximation screen

- Starting commit d5507e3. Read the existing deterministic-FSC risk recursion,
  posterior-aliasing and monotone-event counterexamples, and robust/recursive
  constrained-POMDP source audits. The deterministic FSC verifier does not extend
  unchanged to hidden persistent randomized controller memory.
- Formulated candidate A1 in `CANDIDATE_A1_CONTINUATION_GRID.md`: retain the exact
  pre-promotion robust risk game and approximate only the post-promotion alternative
  DP. Sketched a conservative end-to-end value bound, an exact-risk argument and
  finite-grid size; the proof and source equivalence require further checking.
- The main limitation is material: the pre-promotion tree remains XP in B and the
  grid dimension grows with delay. For T=6,d=1, the coarse bound needs N>=4662
  for 0.01 absolute error, with no demonstrated runtime or memory advantage.
  This is an ordinary composition until a complete reduction proves otherwise.
- No candidate code, experiments, seed allocation, real-data read or superiority
  claim. Decision: audit the coupling/DP proof and compare full complexity; continue
  to B/C if this does not yield a defensible advantage.

## 2026-10-29 — Promotion-dominance structural screen

- Starting revision 169d17e. Registered both diagnostics before execution in
  PROMOTION_DOMINANCE_PROTOCOL_V1.md and PROMOTION_RESTRICTED_ORACLE_PROTOCOL_V1.md.
- Derived a model-specific, exactly safe epsilon-dominance pruning lemma against
  the original full-history oracle. A coupling argument replaces a marked first
  promotion by never promoting, so worst-case null risk cannot increase; the
  conditional alternative cost rises by at most epsilon. Generic POMDP
  branch-and-bound and chance-constrained pruning are established prior art.
- Ran the exact screen: T=5/6/7 passed 170/352/658 lower-bound comparisons. The
  T=6 screen marked 93/236 histories at epsilon 0 and 98/236 at epsilon 1/100.
- Ran restricted oracle at T=6: zeroed 132 or 140 promotion columns respectively;
  both returned 461083/160000 and exact recovered risk 1/10, matching unrestricted.
  Scripts, protocols, source hashes and complete results are tracked in this branch.
- Limitation: the diagnostic builds the full original tree and exact continuation
  cache first; all solves use 1,799 builder nodes. No runtime benefit, novelty,
  synthetic efficacy or real-data result has been established. No seeds or real
  datasets were opened. Next: test early pruning without changing information or
  risk, compare end-to-end cost/resources, and continue B/C if not competitive.
