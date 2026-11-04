# Research direction checkpoint — 2026-11-04

## Current decision

**Do not promote another method from the current sprint to a novel SOTA claim.** The current best supported output is a scoped benchmark and validity–power study, with an empirical real-data component. The SOTA sprint reports `SOTA_NOT_MET` under its full gate: the fresh synthetic late-improvement result is established only for certificate hosts, while credible real late-improvement relevance is absent. The stronger continuation worktree independently records the same limitation for its candidate method and flags a largely incomplete claim audit. Keep these scopes explicit.

## Evidence we can stand behind (within stated scope)

1. **SOTA sprint (current branch).** Amendment 5 confirms that RMM improves late-change cost against Xu on four registered certificate hosts, but its persistent-null promotion rates are high (`rho=.8`: .12–.18; `rho=.95`: about .71) and reversal costs worsen. Amendment 6, combining restart monitoring with the dependence-robust SUI evidence, did not meet its registered gate: real twin-null validity failed on bike_hour and late benefit was partial. See [execution report](REPORT.md), [Amendment 5](validation/amend5_results.md), and [Amendment 6](merge/merge_results.md).
2. **Archived B3 outcomes (full run-pipeline attribution downgraded).** The saved arrays report `WIN` on weather, spam, and Rialto and `SAFE` on all seven streams. Means, paired comparisons and bootstrap endpoints reproduce to 1e-9 from those arrays. Treat them as retrospective descriptive outcomes: weather/spam have only 3/1 episodes, costs and delays are imposed, and the batch comparator assumes exchangeability. The B1 policy source is separately hash-verified at `041bc26`; however, the recorded full-run runner hash (`d2b7e83e…`) differs from the only committed B3 runner available (`2550728b…` at `475bf474`). A 2026-11-04 scan of all 21 local ICML Git repositories and every tracked version of that runner (including LF/CRLF forms) found no match. The archived rows therefore lack verified runner-to-row attribution. G07 remains unsigned and there is no independent statistical sign-off. See the [claim-to-evidence ledger](claim_to_evidence_ledger_2026-11-04.md) and the provenance notice in the [B3 report](../promising_directions/16_REAL_DATA_RESULTS.md).
3. **Versioned challenger idea.** It passed a 1,000-seed IID null diagnostic. Prior charged chronological comparisons used unpurchased evaluation labels to train v2 and are invalidated. A corrected, exposed five-stream screen beats RMM and the front certificate on mean cost but loses to version-aware Model Picker on all five. Keep exploratory tooling only; see the [corrected provenance report](versioned_real_provenance_fixed_results.md) and [candidate record](versioned_challenger_candidate.md).
4. **Other algorithm leads are closed or negative.** Adaptive RMM/SUI merge failed; profile-denominator likelihood candidate did not improve costs and was much slower; Sethi fixed-gap port was screened as too conservative; eventwise contextual scout has broad synthetic evidence but is a standard predictable bounded-factor composition and lacks real-data/deployment validation. Do not re-run these as if new.

## Literature boundary

The existing primary-source audit already covers direct sequential risk monitoring, prediction-powered monitoring, model-selection gates, contextual safe policy control, online active model selection, sequential model confidence sets, change detection, and repeated challenger training. In particular, generic anytime-valid monitoring and restart mixtures are not novelty claims. The exact remaining gap has to exceed existing methods under the same null, dependence, delay, label budget, and economic objective. See [novelty audit](novelty_audit.md) and the repo's [closest prior work](../closest_prior_work.md).

## Promising work to do next

An independent audit rejected a proposed twin-role-swap e-process as an algorithmic lead. Role swapping can yield a valid martingale only when acquisition and stopping are role-symmetric, but that randomization null also makes the statistic directionless for a fixed challenger. Randomizing which model serves each eligible event restores directional power under a sharp null, but that is a standard canary randomized trial; delayed-outcome anytime-valid inference already has direct prior work (Lindon & Kallus, ICML 2026). Do not present either construction as a novel fixed-challenger gate.

The highest-value next step is an evidence-completion package for the P2 validity–power trade-off, rather than another gate or likelihood-bound tweak:

1. Reconcile the current sprint, B3 real-data evidence, and retrospective audit into one claim-to-evidence ledger. Recompute metrics only from archived row-level artifacts; label every result by source branch/commit, seed exposure, data exposure, validity status, and exact estimand.
2. Have an independent reviewer verify the B3 source-to-row path and the conditional-null argument for P3b. Keep the empirical synthetic/real-stream cost result separate from the certification null. Do not call a retrospective conditional-null monitor “marginal-null safe.”
3. If the paper claims the value of anytime certification over batch selection, verify a fixed-sample paired comparator under the same null and identical budget/delay/economic contract. Distinguish P6 versions: the exact 5.3876% boundary-null counterexample concerns an archived repeated `n=25` mean-threshold rule, while B3's current P6 code runs one exact-binomial test after up to 50 labels. The current code is sign-blind, but budget exhaustion can make its terminal count depend on later query availability. The written P3b fixed-delay null does not yet prove validity conditional on that complete selection path; see [`b3_p6_validity_scope_2026-11-04.md`](b3_p6_validity_scope_2026-11-04.md). Deterministic real streams do not instantiate a stochastic null.
4. Run the new method only if a specific theorem-level gap survives this audit. Any new empirical claim requires a new registered protocol, a disjoint seed/data block, and no parameter selection on that block.

**No method lead currently survives.** In particular, the hard-budget, delay-aware acquisition idea is closed as a current lead: the registered A5b+C6 composition lost its frozen cost gate by about `+4.620` per event over the four delayed/late targets, while prior scheduler screens also failed to establish an advantage. Active inference, active testing, and delayed-feedback scheduling are established adjacent areas; another pacing heuristic would not close the gap. The twin-role-swap idea is also closed.

The fresh-seed rollback stress screen also rejects the versioned dual-monitor extension for now: its unreserved policy spent almost the full cap with little rollback sensitivity, while a reserved policy reduced false promotions at the cost of substantial missed improvements and still did not detect degradation. See [the stress screen](versioned_stress_screen_2026-11-04.md). Do not treat rollback as the current method lead.

The registered 30-seed development pilot combining C6 deadline-value acquisition with A5b's
gap-aware Markov SUI evidence also fails its cost gate. Its equal-cell mean paired cost increase
is about `+4.620` per event across the four delayed/late targets, with only one target cell
favoring the treatment. Close this composition without tuning or a validation run; see the
[protocol](a5b_c6_deadline_dev_protocol_2026-11-04.md) and [result](a5b_c6_deadline_dev_results_2026-11-04.md).

This package can make a paper more defensible, but it does not itself create a novel algorithm. A new algorithm is retained only if it beats the strongest valid same-contract baseline on a disjoint confirmation and the result survives an independent result-to-claim review.

## Theory path worth screening before more method work

The current information bound is the only plausible route to a substantive new result, and it is a
theory contribution rather than a method lead. A new decision-value corollary in
[`unknown_persistence_information_bound.md`](unknown_persistence_information_bound.md) proves that
at `rho=1`, under a marginal-null promotion constraint and a common observation channel, no
adaptive-query policy can close a calculable fraction of the gap to a fixed challenger oracle: for
`alpha=.05`, `delta=.05`, `T=2000`, `c_s=5`, the bound is at least 85 deployment-loss units. This
special case is a two-point reduction and may be standard. The next research task is to determine
whether it extends sharply to finite refresh probability and multiple independent episodes under
the registered decision objective. If the extension collapses to standard Le Cam bounds or cannot
be matched to the benchmark's estimand, keep it as a scoped impossibility result and do not restart
algorithm development without a new source-level gap.

## Reproduction pointers

- Current checkout: `git rev-parse HEAD` is `de9aaaa3fa46a16944f5078234b3588a73e80fef`; `origin/main` is the same commit as of 2026-11-04.
- SOTA sprint source and raw outputs: `scripts/sota_sprint/`, `outputs/sota_sprint/` (ignored/local), and `docs/sota_sprint/`.
- Historical B3 code/results: audit worktree `shiftlab-retrospective-audit-2026-11-01`, protocol commit `19f1090`, implementation commit `041bc26`, result commit `475bf47`; artifacts include row-level episode JSONL, paired seed arrays, manifests, and recomputation files.
- The audit worktree's summary is not a clean independent sign-off: `CLAIM_LEDGER_COVERAGE.md` says the bounded ledger covers 33 rows, leaves 9 not yet audited and 24 partial/inconclusive, and G01 remains unsigned.

## Stop / advance rule

- **Advance the evidence package** if every headline result reconciles to raw rows, the source-to-claim audit resolves, and a same-null batch comparator can be validity-calibrated without changing the estimand.
- **Stop method novelty** if the strongest valid batch/active baseline matches the candidate or if no admissible real stream has measurable switching headroom. Retain the benchmark and negative results with precise scope.
- **Advance a new method** only after a written proof delta, a frozen protocol, and a disjoint confirmation all pass. Synthetic significance or a larger search grid alone does not meet this rule.

## Continuation update — 2026-11-04

The current branch has no upstream commits to integrate: after `git fetch origin`, `HEAD` and
`origin/main` both resolve to `de9aaaa3fa46a16944f5078234b3588a73e80fef`. The working tree contains
local research changes; these remain uncommitted and were preserved.

The newly registered gap-conditioned evidence screen is now complete and **neither candidate
passes its advance rule**. `gap_envelope_rho08` is cheaper than the Markov-LR comparator on 11/11
eligible alternative cells (mean paired difference `-0.0347`), but it misses both mandatory
adverse-cost guards. `gap_envelope_rho95` is essentially tied overall (`+0.0035`) and also misses
both guards. The full pointwise null table and raw rows remain in the protocol's output directory;
this result closes the screen, not the underlying broad goal. Do not add adaptive acquisition to
this candidate. See [the frozen protocol](../failure_atlas_gap_envelope_development_protocol_v1.md)
and [the result](../failure_atlas_gap_envelope_development_results_v1.md).

The lower-level primary-source review also confirms that *Which LLM to pick? Online Active Model
Selection for Large Language Models* (arXiv:2610.01592, submitted 2026-10-01) is an important
acquisition baseline: its streaming query rule combines hypothetical loss variance and posterior
entropy, with exponential-weights updates. The paper's objective is identification/regret and its
experiments match average annotation counts; it does not establish pathwise hard-budget delayed
promotion safety. The repository already contains an explicitly adapted `OnlineLLMPicker` and
hard-budget delayed Online LLM Picker and CAMS adapters. Reimplementing those methods, or adding a
generic remaining-budget/deadline heuristic, is therefore not the next contribution. Existing
repository audits already reduce generic deadline-aware acquisition to finite-horizon belief-state
control and enumerate the relevant delayed-feedback precedents.

**Research decision:** no algorithmic lead currently survives the result and novelty audits. Keep
the corrected versioned-challenger result and the gap-envelope result as evidence, not method
claims. The immediate useful work is source-to-claim completion (especially B3 run-source identity)
and an independent result review. Reopen empirical method development only when a source-audited
structural difference or a real stream with observed release times and a matching decision contract
is identified. A new synthetic grid or scheduler-only tweak does not satisfy that condition.

Primary source for the active-selector update: [arXiv:2610.01592](https://arxiv.org/abs/2610.01592).

The 2026-11-04 primary-source search additionally reconfirmed that hard query budgets, active
sampling for valid inference, and delayed-feedback scheduling are established neighboring areas:
[Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html),
[Confidence-Budget Matching](https://proceedings.mlr.press/v139/efroni21a.html), and
[Bayesian Optimization under Stochastic Delayed Feedback](https://proceedings.mlr.press/v162/verma22a.html).
These sources do not settle the project's exact combined contract, but they raise the bar: novelty
would need a verified difference in anytime promotion safety, serial dependence, hard cap, and
arrival deadline together—not just a new budget heuristic.

## Continuation audit — exact-gap SUI transfer, 2026-11-04

The fixed-calendar exact-gap Markov SUI transfer was implemented as a separate Atlas comparator
with a conservative rectangular likelihood bound and conditioned starts. The first registered
screen (20 paired seeds) had zero false promotions across eight null cells but lost to Markov LR
on equal-cell cost (`+0.0102`, paired 95% CI `[+0.0041,+0.0162]`) and had a large mandatory
adverse-cell regression (`+0.2406` vs episode_front). A separately registered sparse-eight-start
screen on disjoint seeds narrowed, but did not reverse, the difference (`+0.0059`, CI
`[+0.0004,+0.0114]` vs Markov LR); its mandatory adverse regression was `+0.2459`. Both screens
fail their frozen advance criteria. Their small null samples do not establish calibration.

**Decision:** close this exact-gap SUI transfer before adding acquisition or tuning the mesh on
either seed block. The fixed uniform-calendar gaps offer no measured advantage over the existing
Markov gate, while the broader gap envelope was already cheaper on the corresponding screen.
Maintain the protocol/results as negative evidence and keep the wide objective open. The method
novelty audit still shows no surviving algorithmic lead; the next useful action remains source-to-
claim completion and an independent result audit, unless a new structural gap or aligned real
stream is found.

Artifacts: [dense-start protocol](../failure_atlas_gap_markov_sui_development_protocol_v1.md),
[dense-start results](../failure_atlas_gap_markov_sui_development_results_v1.md),
[sparse-start protocol](../failure_atlas_gap_markov_sui_sparse_development_protocol_v1.md), and
[sparse-start results](../failure_atlas_gap_markov_sui_sparse_development_results_v1.md).

## Continuation audit — conditional-null and P6 review

A lower-cost independent code review confirms that P3b's written one-shot argument is conditional,
not marginal: it assumes fixed delay, label-independent query randomization, predictable
propensities/bets, and `E[D_t | H_{t+d-1}^{(-t)}] <= 0`, conditioning on all learner-visible side
information through release except the current label. The review also notes that repeated
promote/rollback resets do not inherit one global alpha bound without spending. This does not
change the documented `20.8%` persistent-regime marginal-null failure.

The review corrected a comparator conflation. Current B3 P6 code makes one fixed-sample exact
binomial test at up to 50 released disagreement labels, then never tests again. The 5.3876% exact
counterexample applies to a different archived repeated `n=25` mean-threshold rule. Current query
decisions and the 50-label cap do not inspect label signs. However, budget exhaustion makes the
terminal count depend on episode query/disagreement availability, and the written P3b fixed-delay
null does not establish validity conditional on that complete selection path. The B3 protocol only
states exchangeability; deterministic real streams do not instantiate a stochastic null. See the
[focused P6 scope audit](b3_p6_validity_scope_2026-11-04.md). Keep B3 outcomes descriptive until a
selection/stopping proof under a declared null is supplied and the original runner-to-row provenance
is resolved.

The corresponding claim-ledger row and evidence-package action were corrected. This leaves a
valid-comparator proof and provenance audit as useful evidence work, but it does not create a new
algorithmic lead or reverse the method-screen results.

## Continuation audit — 2026-11-04

A fresh fetch leaves `HEAD` and `origin/main` at `de9aaaa3fa46a16944f5078234b3588a73e80fef`.
The B3 runner recovery check was widened across all 21 local ICML Git repositories and found no
tracked source matching the recorded run SHA, including after checking line-ending variants. This
closes the local recovery avenue. The full research goal remains open. Reopen algorithm development
only against a new, source-audited structural gap or a real stream with observed outcome-release
times and an aligned deployment contract; otherwise continue the P2 result review and report its
scope as empirical benchmark evidence rather than a new algorithm.
