# 03A Joint action-conditioned value of information: design and protocol (written before the runs)

Owner: algorithms lead A. Code: `src/shiftlab/paper3/joint/`, scripts `scripts/paper3/joint/`,
outputs `outputs/paper3/joint/`, ledger `ledger/joint.jsonl`. Core files are untouched. Novelty
status (memo A): ALREADY_COVERED as a generic constrained POMDP. The only open question is whether a
*tractable controller* has an **attributable** gain (an ablation that removes the gain) or a
guarantee. Nothing below is claimed novel; A0 is an explicit textbook baseline.

## Information discipline
Every policy sees only `ProblemSpec` and `PolicyView`: released labels with request/release times,
the pre-label disagreement flag, previous action, label budget and pending count. It tracks its own
request times (the pending queue) from its own decisions. No tape, regime, change point, or
potential outcome is read. A label at a non-disagreement round has Z=0 known in advance, so it is
never requested. The delay is the declared constant when `delay_known` exists, otherwise the mean of
observed release lags (prior 5).

## Shared belief model (`belief.py`)
2-regime hidden-Markov model of the disagreement-round success probability p (challenger correct).
Hypotheses: pairs (pL<pH) from a grid x symmetric switching hazard (table-based policies: 4 p
levels {.3,.5,.7,.9} x 3 hazards = 18; A0: 8 levels x 4 hazards = 112), exact closed-form filtering
(eigen-power propagation), out-of-order release handled by refit from the stored observation list,
posterior weights by marginal likelihood (Bayesian model averaging over regime means and hazard).
This is deliberately misspecified for ramps, seasonal paths and multi-level steps.
Disagreement rate r is learned online. Known-model mode (tiny exact check) takes the oracle HMM.

## Methods
- **A0 BeliefMPC**: receding horizon. Candidates (a,q) in {0,1}^2; Monte-Carlo rollouts (N=64,
  common random numbers) simulate regime, disagreements, query outcomes, the **pending queue and
  delay** (ring buffer), the **hard budget**, belief updates inside the rollout, and a fixed base
  rule (switch when closed-form remaining benefit exceeds k+margin; query every disagreement while
  budget remains and the label can land). Replans only on a queryable round or on a release.
- **A1 QVOI**: value tables V[t,a,pi] (switching DP on a belief grid with a background label-arrival
  rate rho tied to remaining budget). VOI of a query = KG*-style `max_n [E V(m pending) - E V(m+n
  labels)]/n` evaluated at the landing round t+d, exact enumeration over the pending outcomes. Query
  iff voi_mult*VOI > c_q + lam_q. Plain one-step (n=1) VOI was implemented first and queried ~never
  (a single label cannot flip a k=3 decision): the batch lookahead is the standard KG* fix and is
  part of A1, not an ablation. Action: greedy w.r.t. the same tables. Ablations: `use_delay=False`
  (tau=t+1, no pending), `use_cont=False` (one-round value after arrival), `use_switch_pen=False`
  (VOI tables built with k=0; real switches still cost k).
- **A2** = core `Gate(A1)` (betting e-process on released Z, alpha, lambda). The planner proposes,
  the gate certifies 0->1 promotions. Gate null: P(any promotion) <= alpha under E[Z|past]<=0 on the
  observed rounds, history-measurable queries; it is a global-null statement only.
- **A3 DualPrice**: prices lam_q (label) and lam_sw (switch); query iff kappa * EVPI-of-the-switch-
  sign * (actionable horizon fraction) > c_q + lam_q; hard reservation cap on cumulative spend vs a
  pacing path (front-loading parameter); optional dynamic dual ascent on spend minus pacing. Action:
  tables-greedy with extra switch price lam_sw. Ablations: eta=0 (static duals), lam_sw=0.
- **A4 LearnedContinuation**: MLP (torch, GPU training, numpy inference) regressing realised
  cost-to-go from causal features (belief mean/uncertainty under the fitted model, fitted levels,
  pending count, budget/time left, deployed model, costs) for the 4 first decisions (a,q), on TRAIN
  seeds only (dev block offset 1000..1039), behaviour = A1 with random forced first decisions.
  Policy = argmin Q with tuned margins; optionally behind the core Gate.
- **A5 RankReversal**: query iff the probability that n_batch extra labels (landing at t+d, after the
  pending ones) change the greedy action versus deciding without them is >= eps and the actionable
  horizon >= h_min.

## Evaluation protocol
Contract regimes `configs/paper3/regimes_v1.json` (24 regimes, B=60 except `label_scarcity` B=6),
T=300 (the horizon used by the core smoke run). Seeds (registry `dev` block, disjoint offsets):
tuning 0-5, dev-eval 100-129, A4 train 1000-1039. Policy coins seed=tape seed.

1. **Tiny exact check.** Known HMM (core default: transition .9/.1, m0=(.5,.5), m1=(.5,.2)), three
   instances with exact `solve_economic` values; each method receives the TRUE model (labelled
   known-model; A0 additionally with its rollout planner) and is scored by paired Monte Carlo on
   HMM-sampled tapes (same tapes as the exact-DP policy run through `run_policy`): value gap =
   mean(J_method - J_exact_policy), plus never/always/calendar references. This separates planning
   error from model learning. Learned-model gap is measured in step 2 instead.
2. **Development.** Every method (WaldEconomic paced, +cutoff, any-acquisition, CUSUM,
   PageHinkley, Gate(Wald), A0..A5) gets the SAME documented search: 32 configs (default + 31
   uniform random draws), 6 tuning seeds x 24 regimes, objective = equal-weight mean over regimes of
   mean J / mean J_never; configs, scores and wall clock are stored. Tuned configs are then run on
   30 separate dev-eval seeds x 24 regimes. The "strongest tuned deployable baseline" is the best of
   the tuned baselines by **tuning** score (not by dev-eval, to avoid selecting on the evaluation).
   Primary: paired Delta J = J_method - J_baseline (negative favours the method), seed-cluster
   bootstrap (2000 resamples) 95% CI, per-regime and equal-weight pooled, relative to baseline mean J.
   Secondary: labels, switches, global-null false promotion (stationary_null, dep_null_rho_0.95,
   and the other mu<=0 regimes), regret to hindsight oracle (UNATTAINABLE, diagnostic only).
3. **Ablations** (A1: no delay queue, no continuation, no switching penalty, no KG* batch; A3:
   static duals, no switch price; A0 vs A1 isolates planner choice) on the same dev-eval seeds with
   the tuned parent configuration, paired against the parent.
4. **Label matching.** The strongest baseline is re-run with the label budget B set per regime to the
   rounded mean queries of the method under comparison; report Delta J at matched labels.

Grading (user standard, interpretive not a gate): substantial >=10%, meaningful ~3-10% with CI
excluding 0, small ~1-3%, negligible <1%. Hindsight regret and the exact DP are not comparators.

## Known limitations declared in advance
- Dev-only; model-selection and confirmation seed blocks are not touched.
- The belief model is a 2-regime approximation; A0/A1/A3/A5 inherit its misspecification.
- Retraining and compute cost are not modelled (core scope); c_compute is never spent.
- Tuning objective weights regimes by relative J, so expensive-switch and null regimes weigh as much
  as the high-signal ones.
