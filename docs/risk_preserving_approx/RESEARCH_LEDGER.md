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

## 2026-10-29 — Early-pruning prototype and development comparison

- Protocol committed before implementation; source adapter and isolated runner
  are tracked. Focused tests: 6 passed, including hidden pending-label invariance,
  B=0, alpha=0, unavailable labels, delay 2 and reference information-set equality.
- 24 fresh-process runs at T=5–8 returned matched recovered costs and risk 1/10.
  T=6 matched 461083/160000. All run records and source hashes are in
  `early_pruning_development_v1.json`; no real data or seeds used.
- The adapter skipped continuation calls but did not reduce the decision cache or
  builder-node count. Median timings were mixed and noisy; no speedup is established.
- Memory measurement failed: the sampled Windows venv launcher is not the worker
  interpreter. The saved launcher RSS values are invalid as worker memory figures.
- Decision: do not select this adapter as the main algorithm. Continue investigating
  the pre-promotion risk/optimization bottleneck under the original full objective;
  retained source is a development baseline and is not thread-safe outside serial
  process isolation. No synthetic/real baseline win has been established.

## 2026-10-29 — Causal-null constraint-generation diagnostic

- Committed `CAUSAL_CUTS_PROTOCOL_V1.md` before running. Built the existing full
  pre-promotion learner/null trees and solved restricted learner masters with
  exact-form null best-response LPs; independently recovered and risk-evaluated
  each policy. The method is sourced standard cutting-plane/double-oracle
  machinery, not a novelty claim.
- T=5 and T=6 numerically reached reference cost after 26 and 51 cuts; all
  evaluated root-activated policies had exact causal-null risk <=1/10. T=7 hit
  the 64-cut limit with best safe cost 59747/17500 versus reference numerical
  cost 10788127/3200000. Complete iterations and hashes are preserved in
  `causal_cuts_development_v1.json`; executed source is preserved byte-for-byte.
- Total master plus separation solver times exceeded the single reference LP
  solve on the registered small cells; tree construction is unchanged. Timings
  exclude policy recovery and exact verification. No speed, memory, efficacy or
  real-data advantage is established. Numerical master values are not claimed as
  rigorous lower bounds or certified anytime gaps.
- Decision: retain as a baseline; continue toward an implicit risk response or
  stronger structural approximation against the original oracle. No new seeds,
  real-data reads or changes to historical outputs.

## 2026-10-29 — Exact restricted-master certificates

- Registered CAUSAL_CUT_CERT_PROTOCOL_V1.md before running. Reconstructed the
  decomposed economic coefficients in exact fractions, regenerated the T=6/7
  null-cut masters, and saved all cut strategies, rational duals and upper-policy
  behavior in `causal_cut_certificate_t6_v1.json` and `_t7_v1.json`.
- An optimizer-free verifier rebuilt both games and checked null flow, dual signs
  and residual corrections, certificate checksums, and exact recovered-policy
  risk/cost. T=6: 51 cuts, interval [2.881768749998432..., 2.88176875], gap
  1.5678812615e-12. T=7: 64 cuts, interval [3.341548199412250..., 59747/17500],
  gap 0.0725660863021. Root-repaired risk bound is 1/10 in each cell.
- The verifier shares exact coefficient helpers with the generator; it verifies
  the saved certificate but is not an independently coded economic-model solver.
  Numerical master objectives are not treated as certificates.
- Decision: preserve the standard cut generator as a baseline; T=7 is not
  near-optimal enough and the full null tree remains. No computational superiority,
  synthetic efficacy or real-data comparison is established. No data or seeds read.

## 2026-10-29 — Conservative mixture of incumbent policies

- Registered MIXTURE_INCUMBENT_PROTOCOL_V1.md before execution. Re-generated the
  T=7 64-cut candidate sequence; minimized the weighted sum of individual exact
  worst risks and exact costs over safe singleton/pair root mixtures.
- The best mixture was identical to prior root repair: iteration-0 policy weight
  4/35 plus never-promote 31/35, cost 59747/17500, exact combined risk 1/10,
  rigorous gap about 0.072566086302 to the prior verified master lower bound.
  An optimizer-free verifier checked the complete certificate and component metrics.
- No improvement, novelty, runtime or real/synthetic efficacy claim. The summed
  worst-risk bound can be conservative; investigate exact joint null response
  before concluding that all mixtures fail. No data, seed or holdout was opened.

## 2026-10-29 — Joint causal-null mixture of incumbents

- Committed JOINT_MIXTURE_PROTOCOL_V1.md before execution. Reconstructed the
  65 T=7 cut-master candidate policies plus never-promote and solved the standard
  joint null-response mixture LP, preserving hidden root randomization.
- The two-component recovered mixture was the same as the conservative repair:
  weights 31/35 and 4/35; cost 59747/17500; exact full causal-null risk 1/10;
  prior certified lower-bound gap <0.072566086303. Numerical LP residuals were
  <=1.39e-17. No exact mixture-LP dual certificate was generated.
- An optimizer-free verifier rebuilt the mixture, component costs, worst-case
  risk, previous lower certificate and checksums. Generator and verifier share
  economic-model helpers; this is not a second independent model implementation.
- Decision: no benefit from mixture optimization on this candidate set. Retain
  the evidence and move toward a different structural pre-promotion approximation.
  No real data, held-out outcomes or new seeds were accessed.

## 2026-10-29 — Pre-promotion query-cap development comparison

- Registered `PREPROMOTION_CAP_PROTOCOL_V1.md` before the 20-cell screen. The
  adapter caps requests before/on first promotion but retains total B after it;
  a stopped-policy coupling gives a conditional full-oracle value bound. The
  unknown probability in that bound is not a practical general rate. Six focused
  tests passed, including delayed/pending feedback and post-promotion rights.
- All T=5–8/m=0–3 screen cells completed, numerical objectives respected nesting,
  m=B matched the decomposed reference, and recovered policies were exactly
  risk-checked. T=6/8 m=2 matched the full reference's recovered cost; T=7 m=2
  cost 1349103/400000, above the full reference 10788127/3200000.
- Under `FULL_T7_CERT_PROTOCOL_V1.md`, generated an exact full-oracle dual lower
  bound with exact free-column equations. Optimizer-free verifiers checked full
  and m=2 witnesses: full gap <1.564e-12 and m=2 gap <0.001467812502, risk 1/10.
  These checks share model/coefficient helpers and are not an independently
  implemented HMM model. T=8 has no independent full-oracle certificate.
- Under `PRECAP_RESOURCE_PROTOCOL_V1.md`, 30 fresh worker processes completed.
  Median build+solve+evaluation seconds, full vs m=2: T6 0.2326/0.1063; T7
  0.5679/0.2564; T8 1.4668/0.5130. Corrected worker-side peak working-set
  medians and all raw measurements are saved. Single-machine small-cell timing
  is not a complexity proof. No new seeds or real data were accessed.
- Decision: continue as a promising computational tradeoff, not a novelty or
  economic-superiority claim. Complete prior-art audit, stronger baseline and
  registered synthetic comparisons before an eligible real-data development
  replay. Existing failure evidence and holdout restrictions remain intact.
