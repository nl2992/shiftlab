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

## 2026-10-29 — Capped planner versus episode baseline on known HMMs

- Registered CAP_EPISODE_SYNTHETIC_PROTOCOL_V1.md before execution. All six
  previously exposed T=6, B=3, d=2 HMM cells completed. Best of 45 existing
  episode calendar/spending policies was compared with the m=2 capped planner
  and full decomposed oracle at matched model, information, costs and null risk.
- The capped planner beat the selected episode policy on exact expected cost in
  three cells by 0.03854336, 0.053357468 and 0.001212896; three cells tied.
  It remained costlier than the full oracle by 0.016532736, 0.053004739 and
  0.002930624 in the winning cells. Exact recovered-policy null risks were at
  most 1/10. All six historical episode costs were reproduced.
- `cap_episode_synthetic_v1.json` records exact fractions and source hashes;
  focused repository tests: 20 passed. All comparisons are known-model
  development on previously inspected cells, not independent confirmation or
  a certified general approximation result. Stronger published comparators and
  real-data performance are not established. No data or seeds were opened.
- Decision: continue candidate assessment, including source-matched competitors,
  a computable value bound and appropriately frozen real-data development design.

## 2026-10-29 — Strong calendar-opportunity comparison

- Registered CAP_CALENDAR_PROTOCOL_V1.md before execution. All six previously
  exposed HMM cells and 90 adaptive-skip calendar solves completed; exact
  recovered-policy risk and calibrated cost were checked. Focused tests: 17 passed.
- Best model-aware calendar matched the full recovered oracle in all six cells
  and had lower cost than the capped planner in three by 0.016532736, 0.053004739,
  and 0.002930624; remaining three tied. Thus the earlier episode-baseline wins
  do not establish superiority against this stronger comparator. LPs are numerical;
  these are exact evaluations of recovered policies, not class-optimal certificates.
- Results, individual calendar rows and hashes are in
  `cap_calendar_synthetic_v1.json`. This is a single exposed model family; no
  general dominance, runtime advantage against the calendar planner, published
  robust-FSC comparison, independent confirmation or real-data result is claimed.
- Decision: retain the cap as a computational baseline and continue searching
  for a candidate with defensible value/risk guarantees and strong-baseline gains.

## 2026-10-29 — Real paired-loss encoding audit

- Registered REAL_PAIRED_REDUCTION_PROTOCOL_V1.md before data-free algebra checks.
  The initial protocol and first checker incorrectly halved fees and doubled the
  loss/offset; the checker failed. Preserved its source and recorded the correction
  in REAL_PAIRED_REDUCTION_AUDIT_V1.md; corrected 50 exact-fraction cases passed.
- A fresh independent binary encoding of bounded paired-loss differences preserves
  expected decision costs up to a policy-independent common offset under exogenous
  outcomes. Query and switch charges remain unchanged. Under the corresponding
  full-information conditional mean null and appropriate filtration, it preserves
  the one-step binary null. It does not preserve real-valued feedback information,
  pathwise losses, HMM correctness or a null guarantee from empirical calibration.
- Existing cap failed the stronger calendar comparison; no claim of real-data
  superiority or completed G1–G3. No real rows, holdouts or seeds were accessed.
  Continue method/baseline work and develop a frozen real replay only when eligible.


## 2026-10-29 — Candidate A1 finite-grid complexity audit

- Audited the post-promotion denominator-grid proposal against the existing exact
  continuation DP and its stated TV transfer sketch. The grid size is
  `binomial(N+K-1,K-1)` for `K=2^(min(B,d-1)+1)`. At the proposed `N=4662`,
  the T=6,B=3,d=1 loose count is 4,663 beliefs per context and 223,824
  time/budget/deployment context pairs; at d=2 it is 16,909,250,380 beliefs per
  context. Exact integer arithmetic and full values are in
  `candidate_a1_complexity_audit_v1.json`.
- Risk invariance and budget preservation hold conditionally when the pre-promotion
  controller and remaining-rights checks are unchanged. The cost transfer proof
  remains SKETCHED: the reset-model coupling and off-support full-history policy
  comparison are not fully established. Pre-promotion XP growth remains intact, so
  no end-to-end complexity gain is shown. Novelty remains unresolved against
  finite-grid POMDP prior art.
- Decision: no implementation or efficacy run for the current full-simplex grid;
  retain it as a diagnostic and seek a sparse-by-proof representation or method
  that reduces robust pre-promotion search. No data, seeds or holdouts were opened.
  The primary objective remains active; stronger calendar results and prior
  failures remain binding.
- Files: `CANDIDATE_A1_COMPLEXITY_AUDIT_V1.md` and
  `candidate_a1_complexity_audit_v1.json`.


## 2026-10-29 — Candidate B policy-column pricing audit

- Derived the exact deterministic-policy master: minimize alternative cost over a
  root mixture of nonanticipating hard-cap policies, subject to one risk constraint
  per pure causal-null response. Perfect-recall realization equivalence makes this
  the same finite problem as the behavioral sequence form. Restricting null rows
  gives a lower bound; exact pricing and full null separation are both required for
  termination/optimality.
- The existing causal-cut method only restricts null rows; it still materializes
  all learner realization variables. True policy-column generation would require
  minimizing alternative cost plus dual-weighted null risks. This is a hidden-mode
  POMDP pricing problem whose belief must preserve pending outcomes and each null
  response's full-history state. A direct DP retains exponential history growth,
  while no compact reachable-belief bound is known.
- Audited primary-source comparisons to Walraven–Spaan constrained-POMDP column
  generation, Bošanský et al. sequence-form double oracle, and Cubuktepe et al.
  robust FSC synthesis. Generic methods are established; the potentially useful
  distinction would be a strictly cheaper, exact/certified pricing oracle. No such
  result is established.
- Decision: no policy-column implementation until a pricing recursion and state
  count demonstrate actual compression. Candidate B remains unresolved; proceed
  to Candidate C's structural route. No model outcomes, seeds or holdouts accessed.
- Details and citations: `CANDIDATE_B_POLICY_PRICING_AUDIT_V1.md`.


## 2026-10-29 — Candidate C dominance-pruning limit

- Re-audited the proven promotion-dominance pruning rule against its actual build
  path. It removes immediate-promotion choices and continuation calls, but every
  marked information history retains its nonpromotion continuation. That history
  remains available to the learner and is relevant to the full-history causal
  null, so the lemma does not justify merging/removing it.
- Registered evidence across T=5–8 shows skipped promotion calls (68/132/230/370)
  but identical builder-node and continuation-cache counts versus reference;
  resource timings were mixed. The T=5–7 exact screen marked 44/105, 93/236 and
  172/469 histories. This falsifies the measured tree-reduction claim for this
  rule/cells only, not all structural pruning.
- Updated the working-plan state and Candidate C decision. Retain the rule as a
  safe baseline; stop repeating epsilon sweeps on the same exposed family. Any new
  candidate must compact the pre-promotion history representation and preserve
  posterior-alias distinctions under the robust null. No outcomes, seeds or
  holdouts were accessed.
- Details: `CANDIDATE_C_DOMINANCE_LIMIT_V1.md`.


## 2026-10-29 — Aggregate monotonicity fails under public branch revelation

- Registered and exactly checked a T=4, B=3, d=1, two-branch construction. Branch A queries at events 1–3 and promotes on `(Y2,Y3)=01`; branch B skips event 1, queries at events 2–3 and promotes when `Y2=1`. The event-1 query choice reveals the upfront branch to the null before the tested outcomes. Both branches respect the hard cap.
- The average promotion-probability table over `(Y2,Y3)` is `(0,1/2,1/2,1/2)`, coordinatewise monotone with IID risk `3/8`. Exact branchwise causal-null risks are each `1/2`; the null conditions on the public branch, so the mixture's true worst risk is `1/2`, strictly larger than the IID value. The exact-fraction checker, protocol and output are `scripts/research_risk_approx/check_monotone_mixture_risk.py`, `MONOTONE_MIXTURE_RISK_PROTOCOL_V1.md`, and `monotone_mixture_risk_v1.json`.
- This does not contradict the pure deterministic monotone-event lemma or mixtures whose every branch has its own valid monotone certificate. It shows that monotonicity of the *averaged* event is insufficient when the null can observe branch-revealing public actions. Thus null-tree removal requires branchwise monotonicity or a sharper information-conditioned mixture bound.
- Decision: continue investigating monotone-event compression only with branchwise safety semantics; do not remove robust null constraints based on the marginal tape table. No dataset outcomes or seeds were used.


## 2026-10-29 — E-process-gated economic planner baseline

- Implemented the registered fixed-stake, threshold-four promotion gate as an
  exact product-state HMM planner. The state retains economic belief, pending
  queried labels, remaining rights, time and capped wealth; post-promotion
  behavior uses the existing exact delayed-HMM continuation DP.
- The conditional-mean null supermartingale argument proves raw crossing risk at
  most 1/4 under predictable queries and the registered release-order semantics.
  Exact full-history causal-null checks confirmed risk at most 1/4 on all six
  previously exposed development cells. Root activation yielded risk at most
  alpha=1/10; independent exact metrics matched the root mixture componentwise.
- The calibrated planner tied the best registered calendar in three cells and
  lost in three, with no wins. Its exact gaps to the decomposed oracle were
  0, 0, 1/6250, 113637/7812500, 199508757/4882812500, 0 (in registered-cell
  order). This is a required standard-composition baseline, not a novelty claim.
  Small state counts do not establish improved asymptotic complexity.
- Focused check: `uv run --no-sync pytest -q tests/test_eprocess_gated_planner.py`
  (1 passed); Ruff passed. Result provenance: `EPROCESS_GATED_PLANNER_RESULTS_V1.md`
  and `eprocess_gated_planner_synthetic_v1.json`. No new seeds, real outcomes or
  holdouts were accessed.
- Decision: retain as baseline and continue the research search; do not elevate
  this fixed composition to a candidate contribution.


## 2026-10-29 — Strong calendar comparisons at T=7 and T=8

- Registered and ran the T=7, d=1 certified cell against all 42 eligible calendars,
  m=2 pre-promotion cap, decomposed reference and threshold-4 e-process planner.
  The calendar `[1,2,3]` matches the full recovered upper `10788127/3200000`;
  the cap/e-process cost `1349103/400000` is higher by `4697/3200000`. The
  optimizer-free full certificate still brackets V* to <1.57e-12, so this is a
  certified cap suboptimality bound on that cell. The saved certificate verifier passed.
- Registered and ran the T=8, d=1 cell against all 64 calendars. The m=2 cap,
  threshold-4 e-process and decomposed reference all recover exact cost
  `24735833/6400000` at risk 1/10, matching best calendar `[1,2,5]`. Cap builder
  nodes/time were 1,290 / 0.506s versus 5,700 / 1.550s for the decomposed reference
  in this single run. T=8 lacks an independent completed full-sequence certificate;
  do not infer exact unrestricted optimality. Threshold 8 loses by `551/640000`.
- Registered and ran T=8, d=2 over six known HMM cells and 42 calendars per cell.
  Every row completed. The best calendar matched the decomposed recovered reference
  in each cell. The cap lost in four active cells and tied two no-query cells;
  threshold 4/8 gates each tied some cells but lost in others. No method strictly
  beat the calendar cost. The initial result JSON duplicated each mutable cell row
  42 times; duplicates were verified identical and complete, the raw artifact and
  exact executed runner were preserved, and a distinct deduplicated artifact was
  created. The tracked runner was lint-fixed after execution.
- Decision: no G1 novelty or G3 synthetic baseline win. Retain cap as a small-cell
  compute-reduction candidate and the gates as standard baselines. Do not open the
  CRSP replay: the upstream G1–G3 prerequisite remains unmet. Details and hashes:
  `STRONG_CALENDAR_RESULTS_V1.md`, `t7_strong_calendar_v1.json`,
  `t8_strong_calendar_v1.json`, and `t8_delay2_calendar_deduplicated_v1.json`.
  No new seeds, CRSP observations or holdouts were accessed.


## 2026-10-29 — T=8 cap policy rational optimality certificate

- Registered a certificate attempt for the already exposed T=8, B=3, d=1 cell.
  Generated an exact rational dual lower bound for the full first-promotion
  decomposed LP and re-evaluated the m=2 cap policy from saved behavior using
  the exact alternative and full-history null recursions. The optimizer-free
  verifier passed: lower `3.864973906245213...`, upper/cap cost
  `24735833/6400000 = 3.86497390625`, exact cap risk 1/10, bracket width
  `4.7869475491e-12`. This certifies the cap policy to that tolerance of the
  unrestricted optimum under the proved decomposition. It is not a completed
  generic sequence-form builder run or a general approximation theorem.
- The cost also equals the best T=8,d=1 calendar; the cap is not an economic
  win, but has a small single-run solver-time/node reduction against the full
  decomposition. Threshold 8 loses by `551/640000`. Details and reproducible
  certificate: `FULL_T8_DECOMPOSED_CERT_RESULTS_V1.md`, the certificate JSON,
  and `scripts/research_risk_approx/verify_full_t8_decomposed_certificate.py`.
- The T=8,d=2 six-cell screen completed 252/252 calendar runs. The cap never
  strictly beat the best calendar: four losses and two no-query ties. Threshold
  gates also tied or lost, with no strict calendar win. Raw JSON had a repeated
  mutable-row serialization bug; every duplicate group was verified identical,
  raw output and executed source were preserved, and a six-cell deduplicated
  artifact was created. Ruff and focused invariant tests passed.
- Decision: the cap now has a strong instance-specific compute/value certificate,
  but no G1 theorem novelty or G3 economic win over the best calendar. Keep the
  real-data gate closed under the upstream research plan and revise the method
  search. No CRSP rows, new seeds or holdouts were accessed. Full comparisons are
  documented in `STRONG_CALENDAR_RESULTS_V1.md`; source hashes are recorded in
  the JSON artifacts.


## 2026-10-29 — T=8, B=4 adaptive timing screen

- Registered six previously exposed HMM cells at T=8, B=4, d=2 and compared
  the full first-promotion decomposition, m=3 cap, stake-one e-process gates
  at thresholds 4/8/16, and every 57 feasible calendars per cell (342 total).
  All methods and calendar LPs completed with exact independent policy cost/risk
  reconstruction and no failed calendars.
- The unrestricted reference beats the best calendar in both low-persistence
  cells by `6744087/781250000` and `11126044659/976562500000`. The m=3 cap and
  all e-process gates lose to calendars in those cells; restricted methods only
  tie calendars in some other cells. Thus adaptive timing has economic value,
  but the tested restricted candidate classes miss it.
- Result and executed-source provenance: `T8_B4_CALENDAR_RESULTS_V1.md`,
  `t8_b4_calendar_v1.json`, `t8_b4_calendar_executed_source_v1.txt`. Ruff passed.
  No new seeds, real data or holdouts were accessed.
- Decision: reject the fixed m=3 cap and threshold-gate variants as the route to a
  synthetic baseline win. Next strengthen the calendar comparator via a root
  portfolio across schedules/risk frontiers, then seek a candidate that captures
  the verified adaptive timing value while preserving the full null guarantee.
  This result does not pass G1/G3; real-data replay remains closed.


## 2026-10-29 — T=8, B=4 adaptive-value and calendar-portfolio checks

- The registered six-cell T=8,B=4,d=2 grid completed 342/342 calendar runs. In
  the two transition=1/10 cells, the full decomposed adaptive reference strictly
  beats the best calendar by `6744087/781250000` and
  `11126044659/976562500000`. The m=3 cap and e-process thresholds 4/8/16 all
  lose in both cells; they do not capture this adaptive timing value. In the other
  cells calendar was optimal for the recovered reference or the policy chose no queries.
- To strengthen the comparison, registered a finite root-mixture risk frontier on
  the larger-gap cell: 57 calendars at six working alpha values, plus the safe
  policy. Exact pair enumeration selected one component only, `[1,2,3,4]` at
  alpha=1/10. An optimizer-free verifier reconstructed its exact behavior and
  confirmed cost/risk, exact full-history null risk, weighted risk bound and
  minimum over the finite candidate bank. Portfolio cost exactly equaled the best
  single calendar and remained `11126044659/976562500000` above the unrestricted
  reference. The finite-bank result does not rule out all randomized calendar policies.
- Artifacts: `T8_B4_CALENDAR_RESULTS_V1.md`, `t8_b4_calendar_v1.json`,
  `T8_B4_CALENDAR_PORTFOLIO_RESULTS_V1.md`, and
  `t8_b4_calendar_portfolio_v1.json`. No seeds, real rows or holdouts were accessed.
- Decision: the B=4 low-persistence synthetic cell demonstrates an adaptive-value
  opportunity, but all implemented restricted candidates miss it and the finite
  calendar portfolio does not close the gap. Continue G1 search focused on the
  history-dependent timing mechanism; G1/G3 remain open and real-data replay remains held.


## 2026-10-29 — T=8, B=4 policy-shape risk verification

- Reconstructed the two supported promotion paths from the saved full-decomposition
  behavior. After three scheduled queries, the policy waits with probability 3/5
  or queries a fourth with probability 2/5 when the first two released outcomes
  are positive. It promotes at event 5 after three positives on the wait branch,
  or at event 6 after four positives on the fourth-query branch.
- A new optimizer-free verifier independently evaluated the behavioral policy under
  the full history-adaptive endpoint null recursion and the IID fair boundary.
  Both exact risks are 1/10. IID promotion masses by time are 3/40 at event 5 and
  1/40 at event 6. This resolves the apparent 1/8 reading: the event-5 branch is
  weighted by 3/5 and the other 2/5 is held for a fourth observation. The event-5
  query occurs simultaneously with first promotion; its outcome only affects
  post-promotion continuation.
- Verifier source hash: `4bf89a684378afde64588c99fd03ec72a6831b652d182c19a5dade5295ac33e7`;
  verification JSON hash: `7b7e7cfa8ef95652493fb50de55929042b98df946d697910f0785c203592717a`.
  The exact executed verifier source is preserved. Ruff initially reported one
  unused import and formatting issue after execution; those were corrected in the
  tracked runner, and lint/format checks then passed. The output preserves the
  hash of the source that produced it.
- The policy's optimizer-recorded cost is `1666179899873/488281250000`, beating
  the best calendar by `11126044659/976562500000` in the registered cell. The new
  verifier does not independently recompute post-promotion economic continuation.
  This adaptive sample-size split is a descriptive witness, not a novel algorithm;
  randomized sequential testing/alpha spending and delayed futility are explicit
  prior-art obligations. No real data or holdouts were accessed. G1/G3 remain open.


## 2026-10-29 — Candidate B pricing-state counterexample

- Tested whether a fixed active null response's pricing continuation can be
  represented by time, budget, deployment and belief over hidden root/physical
  state alone. Constructed two delay-one histories with the same one positive
  released label, query count, empty pending queue, stationary alternative
  posterior and hidden null-mode belief, but with the query/label at different
  event times. An admissible full-history null response assigns next-query rates
  0 versus 1/2 to these histories. A query-then-positive-only-promotion
  continuation therefore has risks 0 versus 1/2.
- This falsifies belief-only merging for the unrestricted active response family.
  An exact pricing state must include public history or a sufficient automaton for
  each active null strategy. No uniform compact response-memory bound is known;
  the counterexample does not exclude structured response families or a new
  continuation quotient. Keep column generation as an exact reformulation and do
  not implement the invalid compressed DP.
- Artifact: `CANDIDATE_B_PRICING_STATE_COUNTEREXAMPLE_V1.md`. No experiments,
  seeds, real data or holdouts were used. G1/G3 remain open; next require a proof
  of a compact response quotient or move to a distinct Candidate C mechanism.


## 2026-10-29 — Branchwise monotone certificate for the T=8, B=4 witness

- Registered before execution and split the saved full-decomposition behavior at
  its sole randomized pre-promotion information state into deterministic wait and
  fourth-query branches. Exhaustively evaluated all 256 potential-label tapes per
  branch, checked deterministic behavior and the hard cap, and found zero
  coordinatewise promotion-event monotonicity violations.
- Independent exact causal-null recursion and the framework evaluator each give
  robust risks equal to IID fair-tape risks: `1/8` for the three-sample branch and
  `1/16` for the four-sample branch. The public-history mixture weights `3/5` and
  `2/5` produce exact risk `1/10`. Weighted branch costs match the saved policy
  exactly at `1666179899873/488281250000`; this is `11126044659/976562500000`
  below the best fixed calendar and finite calendar portfolio in the cell.
- This is a verified, stronger baseline and risk certificate, but its policies and
  weights were extracted from the exact optimizer. Monotone-event coupling,
  randomized sample-size allocation and delayed group-sequential testing are
  established; there is no efficient generator or value guarantee against the
  unrestricted class. No G1 or G3 claim, seeds, real rows or holdouts.
- Artifacts: `T8_B4_BRANCHWISE_MONOTONE_PROTOCOL_V1.md`,
  `T8_B4_BRANCHWISE_MONOTONE_RESULTS_V1.md`,
  `t8_b4_branchwise_monotone_v1.json`, and
  `verify_t8_b4_branchwise_monotone.py`; executed-source SHA-256
  `1b6432cb88bce49ca2a14d3853b7fa5096d45ee0274b5cd901c10c28476c7d7d`, result
  JSON SHA-256 `aa6f42806ea717bca2b73c00cb57e1af201b9011d9378763f91eda6bcc93465a`.
  Next seek a constructible class with a proved value bound; otherwise close this
  Candidate C branch and advance.


## 2026-10-29 — IID relaxation with exact causal-null certification and repair

- Registered `IID_RELAXATION_CERTIFIED_PIPELINE_PROTOCOL_V1.md` before execution.
  The single fixed T=8/B=4 low-persistence witness used no seeds or real/holdout
  data. The master has the exact alternative continuation objective and learner
  flow constraints, with one IID fair-label null-risk row and no opponent tree.
- The solver returned cost `1666179899873/488281250000`; independent exact IID
  tape recursion matched its realization-flow risk `1/10`. Independent full
  history-adaptive null recursion and the framework verifier both gave `1/10`.
  Repair activation was 1, so exact feasible cost remained equal to the full
  robust reference and below the best calendar/finite calendar portfolio by
  `11126044659/976562500000`.
- Exact rational dual validation with a uniform reduced-cost correction gives
  lower bound
  `33912681199052617326248234060483/9938258388540204617167802375000`; the
  feasible-cost interval is approximately `1.03e-9`. This establishes a useful
  value certificate for this finite witness only, not an approximation theorem.
- Master size was 3,869 learner variables, 1,276 equalities, one risk row and
  zero opponent variables; builder nodes 3,441 versus 17,922 in the reference.
  End-to-end elapsed time was 10.11s versus 5.39s reference solve time, so a
  total-runtime win was not shown. Reference peak RSS was unavailable. Candidate
  screen is mixed and does not pass the preregistered resource-advantage gate.
  Relaxation plus exact repair is standard in form; G1 and G3 remain open.
- Artifacts: `IID_RELAXATION_CERTIFIED_PIPELINE_PROTOCOL_V1.md`,
  `IID_RELAXATION_CERTIFIED_PIPELINE_RESULTS_V1.md`,
  `iid_relaxation_certified_pipeline.py`, and
  `iid_relaxation_certified_pipeline_v1.json`. Ruff passed. Continue only with
  profiling and source-matched prior-art comparison on a preregistered paired
  synthetic test; no real data or holdouts were accessed.


## 2026-10-29 — Candidate B T=10 stress and branchwise certificate

- Registered `IID_RELAXATION_T10_STRESS_PROTOCOL_V1.md` before execution. On
  T=10/B=4/d=2, transition `1/10`, emissions `(1/50,49/50)`, the IID LP used
  13,421 learner variables, 4,868 equalities, one risk row, zero opponent
  variables and 10,813 builder nodes. Exact recovered cost was
  `51237636737353/12207031250000`; exact full-null risk was `1/10`; the exact
  dual/feasible interval width is approximately `1.52e-11`.
- The robust decomposed reference independently returned the same cost and risk
  with 58,806 nodes and 13,790 null variables. It ran in 58.01s; the candidate's
  end-to-end stage took 114.84s. Candidate node count is smaller but runtime and
  process RSS do not improve. Exhaustive robust evaluation of all 163 fixed
  calendars selected `[1,2,3,4]`; candidate cost was lower by exact
  `875921971899/24414062500000` (about `0.03588`). This is a synthetic economic
  win over calendars, not over the oracle, with no compute win.
- The T=10 recovered behavioral policy has exactly one randomized information
  state: after queries 1–3 with labels 1 and 2 released positive, wait w.p. 3/5
  or query at event 4 w.p. 2/5. A corrected independent verifier split it into
  deterministic branches and exhaustively checked 1,024 tapes and 5,120 cover
  edges per branch. Both were monotone with zero violations; exact branch risks
  are `1/8` and `1/16`, and their weighted risk is exactly `1/10`. Costs also
  reproduce the saved candidate exactly. The conditional monotone-coupling
  certificate is proved for this finite policy and declared causal-null family;
  it is not a new optimizer theorem.
- Preserve the first verifier failure: it omitted post-promotion continuation
  and raised a missing-history `KeyError`. The corrected verifier routes
  post-promotion histories through the exact continuation DP and passes. A
  lint-clean rerun to `t10_iid_candidate_branchwise_v3.json` also passes and
  binds the current source hash. Both failed-attempt traces and the partial
  failed JSON remain in the artifact directory.
- Correction: the interim message misstated the T=10 gap as `1.52e-6`; exact
  output is `1.5218859452e-11`. The JSON total elapsed field (`3.534s`) is
  corrupted by timer-variable shadowing. The measured candidate, reference and
  exhaustive-calendar components sum to `548.9616437s`; preserve the original
  output and use `IID_RELAXATION_T10_STRESS_CORRECTION_V1.md`.

## 2026-10-29 — Candidate B paired T=8 synthetic grid

- Registered `IID_RELAXATION_T8_GRID_PROTOCOL_V1.md` before execution and ran
  only the five not-yet-tested frozen-grid cells. Together with the earlier
  sixth-cell run, the IID candidate matches the full robust reference cost in
  all six cells, has exact causal-null risk `0` or `1/10`, and each exact dual
  interval is about `0.84e-12` to `1.26e-12` wide.
- In both low-persistence cells where the reference beats calendars, the
  candidate reproduces that gain; it ties calendars in the four controls. It
  also beats the cap/gate baselines in the adaptive-gain cells. T=8 runtimes are
  9.4–10.4s versus 5.1–5.4s for the robust reference, despite 3,441 versus
  17,922 builder nodes. It is not a compute win. Full per-cell dual flow vectors
  and comparisons are in `iid_relaxation_t8_grid_v1.json`.
- Primary-source comparison confirms the general ingredients are established:
  Khonji et al. (2019), Theorem 5.4/Corollary 5.5, give a fixed-horizon
  chance-constrained POMDP FPTAS for a single known model; Cubuktepe et al.
  (2021) use exact robust verification after approximate uncertain-POMDP
  synthesis. The exact causal-null/two-law reduction is still unresolved, but
  these experiments do not establish a novelty or complexity advantage.
- Candidate B is retained as a useful exact certificate and synthetic comparator,
  not nominated as the lead method. G1 and G2 remain open; G3 is promising on
  deterministic synthetic model cells but is not closed as a methodological
  efficacy gate; G4/real data remain untouched per the plan. No data rows or
  holdouts were opened.
- Artifacts: `IID_RELAXATION_T8_GRID_PROTOCOL_V1.md`,
  `IID_RELAXATION_T8_GRID_RESULTS_V1.md`,
  `IID_RELAXATION_T10_STRESS_RESULTS_V1.md`,
  `T10_IID_CANDIDATE_BRANCHWISE_PROTOCOL_V1.md`,
  `t10_iid_candidate_branchwise_v3.json`, executed-source snapshots, and the
  versioned correction note. Next: test a distinct Candidate C response-state
  quotient against the saved alias and signed-value counterexamples; require a
  two-law value/risk bound before implementation. Do not repeat Candidate B's
  fixed cells or initiate real-data evaluation.

## 2026-10-29 — Candidate C universal response-state quotient lower bound

- Proved a finite distinguishability result for universal quotient states of the
  unrestricted history-adaptive causal-null response family. At event `T-1`,
  `binom(T-2,q)` histories can agree on time, query count, deployment, pending
  queue, alternative belief and physical state while differing in public
  query-time transcript. A single learner randomizes uniformly across those
  calendars; under the null prefix response `p=0`, each all-zero transcript has
  positive probability. For any merged pair, an allowed full-history null can
  assign next-query rates 0 and 1/2. Any common quotient kernel incurs uniform
  conditional-kernel error at least 1/4.
- Proof status: PROVED for the specified strategy-independent quotient of every
  conditional response kernel. The quantifier is `forall quotient, exists null
  response`. The robust continuation risk supremum itself is 1/2 after either
  history, so this is not a robust-risk/value separation, not a lower bound on
  policy-specific approximation, and not a runtime lower bound.
- Reviewed primary sources: Chatterjee, Doyen & Henzinger (2011), Theorem 3.1,
  on belief insufficiency and memory in one-sided partial-observation games;
  Horák et al. (2020), including the belief-insufficiency example in §10 and
  approximate value machinery. The new finite-history argument is elementary
  and no method novelty claim follows.
- Artifacts: `CANDIDATE_C_RESPONSE_QUOTIENT_LOWER_BOUND_V1.md`; updated
  `WORKING_PLAN.md`. Fresh same-family adversarial review confirmed the proof
  under its precise quotient definition and flagged the supremum/value boundary,
  now stated explicitly in the note. No code, seeds, data rows or holdouts were
  accessed.
- Decision: do not implement universal response-state quotienting. Next search
  a policy-side or implicit optimization mechanism retaining the full causal-null
  family; require explicit value/risk/runtime guarantees and a bounded exact-
  oracle comparison before scaling. The overall goal remains open.

## 2026-10-29 — Candidate D active plan

- Updated `WORKING_PLAN.md` to supersede the stale next-step instruction after
  Candidate C's universal response-kernel quotient no-go. Candidate D is now the
  next bounded test: finite-horizon OS-POSG scalarized planning with exact
  causal-null verification and conditional multiplier-bracket recovery.
- Set sequential gates: source/model-match and strategy extraction; theorem and
  source-level prior-art audit; only then a preregistered small exact-oracle
  pilot; continue only on certified risk/value and end-to-end resource advantage.
  Explicit stop rules cover a reduction that restores the full sequence tree,
  inadequate risk endpoint bounds, or loss of compute gains in extraction and
  verification. CRSP and reserved real-data holdouts remain closed through G1–G3.
- No solver run, new seed, data access, remote job or overnight schedule was
  started. Candidate D's recovery lemma remains conditional and is not claimed as
  novel. Next action: finish D1/D2 before any implementation or efficacy run.

## 2026-10-29 — Candidate D finite-horizon model match

- Read the exact hidden-root reduction, the event-order implementations, and the
  primary OS-POSG paper sections on model definition, HSVI, strategy extraction,
  and Theorem 4. The representation matches only after splitting each round into
  learner and null-response microstages; a simultaneous-stage transcription would
  hide the request from the null and change the game.
- Established an exact per-instance finite-horizon embedding via time-augmented
  state, absorbing terminal state, and time-rescaled rewards. This imports the
  discounted OS-POSG strategy theorem conditionally on faithful implementation,
  but does not give a useful complexity bound; reward scaling and controller
  extraction may erase empirical savings. Full learner history, pending-label
  visibility for the null, and alternative post-promotion continuation remain
  mandatory.
- Corrected Candidate D's recovery theorem assumptions: only a risk-zero
  never-promote policy with cost at most T is needed for the multiplier bound;
  the repository does not guarantee every policy has total cost at most T when
  query and switching charges are included. Exact-risk root-mixture recovery
  remains conditional on a bracket and does not establish that HSVI finds one.
- Artifacts: `CANDIDATE_D_MODEL_MATCH_AUDIT_V1.md`, corrected
  `CANDIDATE_D_LAGRANGIAN_OSPOSG_RECOVERY_V1.md`, and updated `WORKING_PLAN.md`.
  No code, experiment, seed, or real data was accessed. D1 passes as a reduction;
  D2 and the end-to-end pilot remain open. Next: inspect a reproducible OS-POSG
  implementation and determine whether a bounded faithful pilot can plausibly
  beat the exact decomposed solver after extraction and robust verification.

## 2026-10-29 — Candidate D implementation feasibility screen

- Inspected the MIT-licensed `HSVIforOSPOSGs.jl` source at commit
  `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`. Its game format can represent
  finite partitions, transitions, observations, actions and bounded rewards,
  but `solve` returns bounds/statistics only; the public solver does not retain
  the learner's theorem-backed strategy gadget/controller needed for exact
  policy certification and multiplier-bracket recovery.
- Julia was absent from the host and was installed per-user as v1.13.3; the
  upstream project declares compatibility with v1.8. `Pkg.instantiate(); Pkg.test()`
  has been launched once. Its main Julia process (PID 32108) and active child
  precompile worker were verified live; CPU time continued advancing. The test
  is not yet terminal, so no pass/fail is claimed and it has not been restarted.
  The ignored checkout is unchanged at the pinned commit.
- D2 finds no novelty delta in the standard Lagrangian/OS-POSG/verification
  composition. Keep one bounded test only as a computational baseline: belief
  search could plausibly reduce the explicit learner tree, but extraction and
  exact verification may remove that gain. Next action: collect the same test's
  terminal result, then implement/test only the finite-horizon gadget adapter;
  preregister ShiftLab efficacy comparisons before executing them.

### Correction to Candidate D implementation feasibility test

- The same `Pkg.instantiate(); Pkg.test()` run recorded in the preceding entry
  has now terminated. It completed 53/54 assertions: the 143-state `peg03`
  solve test failed its 60-second gap threshold (`33.7504833` observed versus
  `<1` expected); the reference-value containment check passed. The Julia
  process is terminal and no restart was made. Full log is retained in the
  ignored `.aris/runs/hsvi-osposg-upstream/upstream_test.log`; package checkout
  remains pinned and clean.
- Update: the package is not validated at its default settings on this host.
  Keep one pilot only as a bounded feasibility check; no ShiftLab test or
  efficacy claim has been run. The required strategy gadget remains absent from
  the package's solve interface.

## 2026-10-29 — Candidate D gadget-extraction toy

- Registered the two-hidden-state probe/guess toy and acceptance thresholds before execution in
  `CANDIDATE_D_GADGET_ADAPTER_PROTOCOL_V1.md`. Implemented the published Algorithm 5 gadget LP
  over the pinned HSVI lower-bound alpha vectors, recursively extracted the learner controller,
  and independently evaluated that controller over the toy transition/reward model.
- All thresholds passed. The exact target is `11/25=0.44`; HSVI's interval was
  `[0.4399999283581686, 0.44000007402989255]`; the extracted three-node controller evaluated to
  `0.44000000000000017`, with max gadget residual `8.38e-10`. Solve/extraction took 12.282/0.100s.
  Source, protocol and ignored-output SHA-256 values and reproduction command are recorded in
  `CANDIDATE_D_GADGET_TOY_RESULTS_V1.md`.
- This validates an extraction adapter on a small known game only. It does not provide an exact
  two-law ShiftLab verifier, a risk-bracketing pair, a resource advantage, or a novelty delta.
  Candidate D remains a baseline-plumbing route; no ShiftLab pilot or real-data run is authorized
  by this result. The overall research goal and G1 remain open.

## 2026-10-29 — Candidate D adversarial gadget toy

- A one-step matching-pennies OS-POSG toy was used to test extraction of a randomized learner
  strategy against an adversarial opponent action. The first fixture failed during parsing because
  its declared dimensions did not match its contents; that failure is retained separately and is
  not counted as a solver result. A corrected isolated v2 fixture was run under the frozen protocol
  `CANDIDATE_D_ADVERSARIAL_GADGET_PROTOCOL_V1.md`.
- The corrected run passed. Exact maximin value is zero; HSVI returned width `1.77e-7`; the
  extracted controller chose each row with probability `1/2` and independently evaluated to
  payoff zero against both pure opponent columns. Gadget residual was zero; runtime was 5.303s.
  Protocol, hashes and boundaries are in `CANDIDATE_D_ADVERSARIAL_GADGET_RESULTS_V1.md`.
- This tests only a one-step adversarial choice. It does not validate history-dependent opponent
  extraction, delayed switching, or the exact two-law risk/cost verifier. No ShiftLab pilot, method
  claim, or novelty gate follows; G1 remains open.

## 2026-10-29 — Scheduled push validation checkpoint

- Re-ran `test_hsvi_adversarial_gadget.jl` with Julia 1.13.3 and the branch-local
  `.aris/runs/hsvi-osposg-upstream` project: passed, solver gap approximately
  `1.77e-7`, independently evaluated security value zero and gadget residual zero.
- Ran `test_hsvi_sequential_adversarial_gadget.jl` with the same project: failed
  in upstream `presolve_LB` (`src/presolve.jl:37`) with `KeyError: (3, 3, 1)`.
  This checkpoint preserves the sequential fixture and script as unfinished work;
  it establishes no sequential extraction guarantee. Investigate the fixture and
  upstream presolve contract before treating it as validation evidence.
