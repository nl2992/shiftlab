# Straddle acquisition: prior-art audit, validity argument, and label-saving bound

**Date:** 2026-10-31. **Status:** Failure Atlas cycle 4, Amendment 5 item 5. Theory note and R2
audit. Nothing here is confirmatory; no novelty claim is made. Numeric check:
`PYTHONPATH=src .venv/Scripts/python scripts/check_straddle_bound.py` (development-grade).

Object studied: `acq=straddle` in `src/shiftlab/dive/atlas_components.py` (`ComposedMethod._query`).
While the call is undecided it requests a label at every round subject to (i) at most `pending_cap`
(default P = 2) requests in flight, (ii) a cumulative pace cap `ceil(burst_frac*B) + floor(2*B*t/T)`
and the hard cap B, and (iii) `t + d <= T`. When the call is clear it requests only a keepalive
label every `K = max(d+1, ceil(keepalive_mult*T/B))` rounds. "Undecided" is a function of released
labels and the method's own state only. Evidence is `VectorizedStartedMixtureEProcess` (or the
variants), fed with released labels in release order.

Reading conventions: **[read]** = I opened the primary text this session and cite the numbered
statement. **[summary]** = known only from a search summary, an abstract page, or a repository audit
note; theorem numbers are not asserted.

---

## (a) R2 prior-art audit

Question for every source: does a theorem state or directly imply any of (L) label saving from
undecided-only querying, (D) its dependence on release delay d, (V) validity of an anytime test when
the query indicator is predictable and labels are released with delay d?

| Source | Contract (what it does) | L | D | V | Basis |
|---|---|---|---|---|---|
| Chernoff 1959, sequential design of experiments | Choose the next experiment to best discriminate the currently most likely hypothesis from the alternatives; stop on a posterior threshold | informal (sampling stops when posterior is confident) | no | not an anytime-valid test (Bayes / error-probability) | **[summary]**, via Naghshvar-Javidi Sec. 2.2 which describes the scheme and cites "Theorem 2 in [17]" |
| Naghshvar and Javidi, Active sequential hypothesis testing, Ann. Stat. 41(6), 2013 (arXiv 1203.4626) | Problem (P): M hypotheses, finite sensing actions, known kernels, **immediate** conditionally independent observations, objective E[tau] + L * P(wrong declaration) | The optimal policy stops when the posterior is confident, so sampling after "clear" is excluded by construction; Theorems 1, 2 (lower bounds on V) and Theorem 3 (upper bound on V for policy 2) bound expected sample number | no delay, no pending queue, no hard budget | Bayesian error bound, not Ville-type | **[read]**: Problem (P), Assumptions 1-2, Lemma 1, Theorem 1, Proposition 1, Theorem 2, Theorem 3 statements; proofs not read |
| Active testing with costly or limited observations. In the repo: Vershinin, Cohen, Gurewitz arXiv 2509.11632 (cost-aware Chernoff); Li et al. TMLR 2024, Active Sequential Two-Sample Testing (Theorem 5.1: P_0(exists n <= N_q: W_n <= alpha) <= alpha under adaptive feature selection with a finite label cap; Theorem 5.4: asymptotic MI characterisation) | Heterogeneous costs / finite label budget; adaptive query selection with a classifier updated from queried labels; labels immediate | cost/information trade-off, not a delay-indexed saving | no | Li et al. Theorem 5.1 is validity under adaptive (predictable) selection, immediate labels | **[summary]** via `docs/switching_risk_search_active_test_audit_v1.md` and `docs/switching_active_sequential_two_sample_audit_v1.md` (those notes record that the theorem statements and Theorem 5.1 proof were read; I did not re-read the sources) |
| Waudby-Smith and Ramdas, Estimating means of bounded random variables by betting, JRSSB 2024 (arXiv 2010.09686) | Bounded-mean CS by nonnegative (super)martingales with **predictable** betting fractions | no | no | Theorem 1 (4-step supermartingale confidence-set recipe via Ville) and Proposition 1 / Theorem 2 (predictable plug-in Hoeffding / empirical-Bernstein CS: the capital process is a test supermartingale for any predictable lambda_t). Observations are consumed in order; no selective sampling and no delay | **[read]**: Theorem 1 with its Ville remark, Proposition 1, statement of Theorem 2 |
| Zrnic and Candes, Active statistical inference (arXiv 2403.03208, ICML 2024) | Label with probability pi(x) driven by model uncertainty u(x); budget is **expected** label count E[n_lab] <= n b; inverse-propensity-corrected estimator | Variance-optimal "oracle" sampling rule (Sec. 7.1); saves labels in the variance sense, not stop-when-clear | no delay (the text has no occurrence of "delay") | **asymptotic** CLT validity: Proposition 1 and Theorem 1 (batch), Proposition 2 and Theorem 2 (sequential, requires model/rule convergence and the Lindeberg condition). Not anytime-valid, not finite-sample | **[read]** Sec. 5-6 and the statements of Prop. 1-2, Theorems 1-2 |
| Xu, Karampatziakis, Mineiro, Active, anytime-valid RCPS (arXiv 2406.10490) | Labelling policy q_t predictable w.r.t. F_{t-1}, lower bounded by q_t^min; IPW e-process; budget is expected label rate (problem (10)) | Proposition 5 gives the growth-optimal q; Theorem 3 relates its estimation error to wealth growth | no delay (no occurrence found) | Proposition 2 (e-process for any predictable (q_t), (lambda_t)) and Theorem 2 (anytime-valid risk control by Ville). Closest published statement of "predictable selection preserves the test supermartingale" | **[read]** Sec. 2.1, Propositions 2-5, Theorems 2-3 statements; the proofs of Prop. 2 read |
| Chugg, Cortes-Gomez, Wilder, Ramdas, Auditing fairness by betting, NeurIPS 2023 (arXiv 2305.17570) | Sequential two-sample testing by betting; stopping-time bounds under the alternative; handles drift | not addressed | no | test-martingale validity, standard | **[summary]** (search result only) |
| Active model selection with budgets: CAMS (Liu et al., arXiv 2207.06030) and Online LLM Picker (Turrin et al., arXiv 2610.01592) | Disagreement / entropy-driven query probability, exponential weights, regret and query-complexity bounds | Query-complexity bounds for expected count, immediate feedback | no (CAMS delay is a repo adaptation: `docs/switching_cams_comparator_contract_v1.md`) | regret, not test validity | **[summary]** via the two repo audit notes; CAMS is implemented in `src/shiftlab/dive/hard_budget_delayed_cams.py` |
| Delayed feedback in sequential testing. Lu et al., Feedback-Enhanced Online Multiple Testing, JMLR 27(186) (Theorems 3, 7, 9: mFDR/FDR with immediate or fixed-delay feedback); Lindon and Kallus (arXiv 2603.25971, anytime-valid inference when outcomes arrive late) | Delayed revealed truth used to recycle alpha; late outcomes make the observed sequence treatment dependent | no | no | FDR/mFDR, not any-promotion FWER (Lu); union-bound CS for late outcomes (Lindon-Kallus) | **[summary]**: Lu et al. via `docs/switching_feedback_online_testing_prior_audit_v1.md`; Lindon-Kallus from a search summary only |
| Repository: `docs/switching_pending_null_information_lemma_v1.md` | Predictable betting with a stake chosen before the query; null filtration H_t includes pending labels; fixed delay, in-order release | no | no | **Yes, V**: states the supermartingale argument for predictable query times with pending labels and Ville. This is the validity statement of (b) in the bounded-X setting | repo document, read |
| Repository: `docs/g1_deadline_aligned_acquisition_kill_v1.md`, `docs/switching_economic_acquisition_screen_v1.md`, `docs/switching_order_sensitive_acquisition_separation_v1.md`, `docs/switching_budget_pacing_prior_audit_v1.md`, `docs/switching_budget_delay_lower_bound_v1.md`, `docs/switching_delay_capacity_audit_v1.md` | Earlier kills of "deadline-aligned", VOI-based, order-sensitive acquisition; hard-budget pacing; a budget-and-delay lower bound; capacity-constrained delayed learning | The deadline-aligned kill says delay-aware acquisition is a heuristic approximation to belief-state control with a pending queue; the budget-delay bound (proposition with proof) gives a regret floor depending on B and d for any learner meeting the null risk | yes, as lower bounds on regret rather than as label counts | n/a | repo documents, read (partial: openings) |

### What the sources do and do not cover

- **V (validity).** Covered, as three independent published or repo statements: predictable
  betting fractions (Waudby-Smith and Ramdas, Prop. 1 / Thm. 2, **[read]**), predictable labelling
  policies (Xu et al., Prop. 2 / Thm. 2, **[read]**), adaptive predictable query selection with
  finite cap (Li et al. Theorem 5.1, **[summary]**), and pending labels under fixed delay (repo
  lemma). No source states the combination "indicator is a function of released labels, with
  release delay d, inside a *round-indexed* test supermartingale", but the repo lemma plus the
  definition of predictability makes it a one-paragraph consequence. Section (b) writes it out; it
  is not a new theorem.
- **L (label saving from undecided-only querying).** Naghshvar-Javidi's optimal policy stops
  sampling once the posterior is confident, so "stop querying when clear" is the defining feature of
  sequential testing since Wald. Zrnic-Candes and Xu et al. give uncertainty-driven sampling with an
  expected budget. No source gives a count of labels saved relative to uniform pacing under a
  pathwise cap with pending requests, but the count in (c) is elementary arithmetic, not a theorem
  anyone would need.
- **D (delay dependence).** No source in the table has delay in the contract except the repo's own
  budget-delay lower bound, `Lu et al.` (FDR), and `Lindon-Kallus` (late outcomes, **[summary]**).
  None states how the saving from undecided-only querying varies with d. The repo's deadline-aligned
  kill (`g1_deadline_aligned_acquisition_kill_v1.md`) already treats delay-aware acquisition as an
  approximation to the pending-queue belief-state planner.

### R2 verdict

**No source theorem states the straddle result as a package** (label saving from undecided-only
querying, its delay dependence, and validity with delayed release). But every ingredient is covered
by a source or a repo note: undecided-only querying is Chernoff/Naghshvar-Javidi/active-learning
practice, predictable selection validity is Waudby-Smith-Ramdas Prop. 1 / Xu et al. Prop. 2 and the
repo pending-label lemma, and delay-aware acquisition is already classified as an approximation to
belief-state control. The absence of a single source theorem for the package is therefore not
evidence of an open gap: the validity part is a corollary of known facts, and the saving part
is arithmetic about a particular schedule. **R2: not novel as theory; at most a known technique in a
new (delayed, hard-cap, conditional-null) contract.** Gaps in the audit: Chernoff 1959, Chugg et al.
and Lindon-Kallus were not read as primary texts, and I did not search for sequential-testing
sources on pathwise budgets with pending requests beyond the repo notes.

---

## (b) Validity argument

### Setting and assumptions

Rounds t = 1..T; fixed release delay d >= 1 (the label requested at t is released at the start of
round t + d, if t + d <= T). Let X_t be the (bounded, |X_t| <= b) increment that the e-process
would consume at round t: the paired excess cost with the sign convention that the null is
E[X_t | .] <= 0. Let U be all independent randomness of the method (rng draws). Define the
**full-information filtration** F_t = sigma(X_1..X_t, U_1..U_t), including values of unqueried
rounds and pending labels. This is the null player's filtration of `switching_pending_null_information_lemma_v1.md`.

- (A1) Conditional null: E[X_t | F_{t-1}] <= 0 for all t.
  If the null is only assumed relative to a coarser filtration G (e.g. generated by queried
  values and own actions), the argument below goes through with F replaced by G, provided q_t,
  the stakes, and the actions are G_{t-1}-measurable. A null that holds relative to a *finer*
  filtration implies it for F by the tower property.
- (A2) Exogeneity of outcomes: X_t does not depend on the query decision q_t or on the method's
  past queries/actions beyond what F_{t-1} contains. In the harness the paired difference
  D_t = loss1_t - loss0_t is a function of the stream only, and queries only reveal it. In a
  deployed loop this requires that both action losses be identifiable and that the stream not react
  to the learner. If X_t reacts to q_t, (A1) must be stated *including* q_t in the conditioning; the
  violation experiment in the script shows what goes wrong otherwise.
- (A3) Predictability: q_t = Q_t(F_{t-1}) for some measurable Q_t, hence in particular when q_t is a
  function of released labels (X_u: u <= t - d, queried), own past q and actions, the round index
  t, and U_1..U_t. The code's straddle rule has this form: `undecided` uses `ep_labels` (released
  labels), `ep.alarm` (a function of released labels), `act`, `used`, `pending_events`,
  `last_query`, all of which are determined at round t by the history before X_t is realised.
  The cap `cap(t)` and `keepalive` are deterministic.
- (A4) Stakes predictable: lambda for the factor of round t is G-measurable at t-1. In the started
  mixture the stake and start weights are fixed before data (a function of the label index only).

### Round-indexed process

Let N_t = sum_{u<=t} q_u (labels requested through round t), and, since q_t is F_{t-1}-measurable, so is
N_t (it counts the request at round t itself). Fix a **component** (start s, stake lambda,
fixed before data). Its factor for round t is

  f_t = 1 + q_t * a_t * lambda * X_t / b,   a_t = 1{N_t > s}   (component active from the (s+1)-th label; whichever convention
  the code uses, `time >= start`, it is a function of N_t only),

with lambda in [0, 1). All of q_t, a_t, lambda are F_{t-1}-measurable and |X_t| <= b, so f_t >= 0
and

  E[f_t | F_{t-1}] = 1 + q_t a_t lambda E[X_t | F_{t-1}] / b <= 1  (by A1).

Define M_t^{(c)} = prod_{u<=t} f_u. It is a nonnegative supermartingale in (F_t) started at 1.
The mixture M_t = sum_c w_c M_t^{(c)} with fixed weights w_c >= 0, sum = 1, is again a nonnegative
supermartingale with M_0 = 1. This is the claim: the queried-labels process is a test
supermartingale in the round filtration.

### Link to the code's label-order indexing

The code (`VectorizedStartedMixtureEProcess.update`) keeps `time` = number of labels already
absorbed and applies the factor `1 + stake*value/bound` to every component with `time >= start`.
That is the label-indexed product W_k = prod_{j<=k} (1 + lambda_j Y_j / b), where Y_j = X_{rho_j}
and rho_j = min{t : N_t = j} is the round of the j-th request.

1. *Predictable stopping time.* {rho_j = t} = {N_{t-1} = j-1, q_t = 1} is F_{t-1}-measurable, so
   rho_j is a predictable time. By the computation above, E[Y_j | F_{rho_j - 1}] = sum_t 1{rho_j = t}
   E[X_t | F_{t-1}] <= 0 (on {rho_j <= T}). Thus the label-ordered sequence is a supermartingale
   difference sequence w.r.t. H_j = F_{rho_j} even though its index is random. This is optional
   skipping with a predictable skipping rule.
2. *The two products coincide.* With in-order release, the j-th released label is Y_j. The
   label-indexed wealth is W_{N_t} = M_t^{round} (rounds without a request multiply by 1, and
   the stake depends on j = N_t only). So the code's process, evaluated at the right time, equals
   the round-indexed supermartingale.
3. *Release delay is a time shift, not a filtration change.* At round t the method has absorbed the
   labels of rounds <= t - d, so its state is M_{t-d}, which is itself a supermartingale
   sub-sampled along a deterministic shift. The event {exists t : log e-value at t >= log(1/alpha)}
   is contained in {sup_s M_s >= 1/alpha}, and Ville's inequality gives P(sup_s M_s >= 1/alpha) <= alpha. The
   method is *allowed* to look only at M_{t-d}; this restriction can only shrink the event.
   Labels pending at the horizon (t + d > T) are never absorbed; they are charged to the budget
   and contribute nothing to M.
4. *Pending queries.* Their values X_t are in F but not yet in the learner's view. Because the
   supermartingale property is proved with respect to F, the learner's ignorance of pending values
   is irrelevant: F contains pending values, and A3 uses only that q_t is F_{t-1}-measurable (which
   it is, since the learner's information is a sub-sigma-field). This is exactly the pending-label
   lemma in `switching_pending_null_information_lemma_v1.md`. The same conclusion holds if q_t
   were allowed to depend on pending labels, which the learner cannot see; the released-only
   dependence is an implementability restriction, not a validity requirement.
5. *The cost of selection is power only.* Selection depends only on released labels, so the
   process under the alternative can stall (no labels while "clear" in the wrong direction). It
   cannot create evidence under the null.

### Episodes, rollback and the composed decision

`ComposedMethod` restarts the evidence on rollback with `alpha_j = alpha * 2^{-(j+1)}` and absorbs only
labels with `ev >= ep_start`. Episode j's process uses the inclusion indicator
I_u = 1{u >= ep_start_j}. Now ep_start_j = t_rb is a round at which the rollback decision, a function
of labels released by t_rb (rounds <= t_rb - d), was taken. So {ep_start_j <= u} is
F_{u-d}-measurable, hence F_{u-1}-measurable for d >= 1, and I_u is predictable. It can be folded into
the q_t * a_t factor above. The rounds requested before t_rb but released after it are excluded;
because that exclusion is decided at round t_rb, using only rounds <= t_rb - d, it is predictable for
the excluded rounds (and for rounds in (t_rb - d, t_rb), whose values the decision has not seen). Union bound:
sum_j alpha_j <= alpha. Promotion requires alarm AND an economic check AND rollback state; these extra
conditions only shrink the event, so P(any false promotion) <= alpha under A1-A4. (The code cannot
test A1 itself; the unit tests and null-twin runs of the atlas test the code path.)

Not covered by this argument: (i) validity of the *rollback monitor* (CUSUM) or of the economic check; they
carry no guarantee here. (ii) The case where the null is stated only for the marginal law
rather than conditionally on the selection. (iii) Informative delay (release time depending on X),
out-of-order release, and a stream that reacts to the deployed action; each needs an explicit
filtration. (iv) `weighted_starts` designs derived from expected label counts under a schedule: they are
fixed before data, so validity is untouched, but for straddle the schedule is data dependent and the
"expected label count" is only the uniform-pace approximation (see
`expected_queries_by_round`), a power question only.

### Numeric corroboration (development-grade)

`scripts/check_straddle_bound.py`, Part B, 1500 reps per cell, T = 1000, B = 50, P = 2,
alpha = 0.1, boundary-null Rademacher X_t, straddle-type predictable rule, 7 starts, 5 stakes:

| rule | d = 1 | d = 10 | d = 50 |
|---|---|---|---|
| predictable q (valid) | 0.015 | 0.018 | 0.009 |
| violation: outcome reacts to query (mean +0.4 when queried) | 0.266 | 0.353 | 0.249 |
| violation: query peeks at X_t | 1.000 | 1.000 | 1.000 |

The valid rows are below alpha (the sampling SD at p = 0.1 is about 0.008), and both violations
break the guarantee, as the assumptions say they should. This is consistent with, but not a proof
of, the argument above. The peeking violation is a deliberately extreme cherry-picking rule.

---

## (c) Label-saving bound as a function of d

### Model (simplifications S1-S5)

- S1. **Clear after tau released labels:** the call is undecided until the tau-th label is released,
  and clear afterwards, for ever. tau is a constant (the expected value of a stopping time
  would need independence assumptions). The ledger's "decision becomes clear" is a function of
  released labels, so this is its simplest consistent abstraction.
- S2. Straddle requests a label at every round with fewer than P labels pending (pending is
  counted at decision time, after releases), subject to the pace cap `cap(t) = burst + floor(2Bt/T)` with
  burst = ceil(0.1 B), the hard cap B, and t + d <= T. After the call is clear it requests only a
  keepalive every K = max(d+1, ceil(4T/B)) rounds. ("Queries already pending keep their budget
  charge" is automatic: used counts at request time.)
- S3. Uniform pacing requests at the calendar rounds ceil(j (T-d)/B), j = 1..B, and never stops.
- S4. Both schemes see the same labels, so the same tau; only the *time* at which the tau-th label is
  released differs.
- S5. Asymptotic bookkeeping ignores floors/ceilings (the script uses the exact discrete schedule).

### Proposition 1 (wasted labels). Under S1-S2, the number W of requests in flight at the round t* when the call becomes clear satisfies

  0 <= W <= min(P, d - 1),   and W = 0 when d = 1.

*Proof.* At the decision at round t*, labels due at t* have been released and removed. Requests still
in flight were issued in rounds t*-d+1..t*-1 (at most one per round), hence at most d-1 of them,
and at most P by the pending rule. At t* the call is clear, so no further undecided request is
made. These in-flight requests are charged but cannot change the decision that was just made: they
are the "wasted" labels. For d = 1 the range is empty. QED.

The steady-state approximation of the user-facing formula: while undecided, requests are issued at
spacing g rounds (g = 1/rate); in-flight count is about (d-1)/g, capped at P, so

  W ~ min(P, (d-1)/g),   g = max(T/(2B), d/P)  [pace-cap spacing, or pending-cap spacing].

For the atlas grid (T = 1000, B = 50, P = 2): d = 1 gives W = 0, d = 10 gives about 0.9, d = 50 gives 2.
The script's exact simulation gives W in {0, 1} for d in {1, 10, 25, 38, 50} depending on the position of the
tau-th label in the batch; the bound W <= min(P, d-1) holds in every case (asserted).

### Proposition 2 (labels saved vs uniform). Under S1-S5, tau <= B, the total requests are

  straddle:  N_str = tau + W + k_alive,  k_alive = floor((T - d - t*)/K) (keepalives after clear),
  uniform:   N_uni = B,

so labels saved = B - tau - W(d) - k_alive(d), with t* = t*(d, tau) the clear time. *Proof.*
Counting: before the tau-th release straddle has issued exactly tau + (in-flight at that time)
requests; the in-flight ones are W by definition; afterwards only keepalives are issued, at most one
per K rounds on the remaining window of length T - d - t*. Uniform issues B. QED (arithmetic).

**Consequence: the saved label count is almost independent of d.** d enters through W (at most P = 2)
and through k_alive via t* and K. In the exact schedule (tau = 10) the saving is 29, 29, 29, 30, 31
labels at d = 1, 10, 25, 38, 50, i.e. a spread of 2 labels out of 50 (script, Part A). So the saved
*budget* cannot by itself explain a gain that goes from +0.115 (d = 1) to -0.017 (d = 50) per
round (`docs/failure_atlas_v1_ledger.md`, Amendment 4 check 2). The query price is c = 0.01 per
label by default, so 30 saved labels is worth about 0.3 total cost, which in per-round units is
orders of magnitude smaller than the observed gain. **The label-saving channel and the observed
gain are therefore different quantities, and "saved labels" is not the primary mechanism for the
d-dependence.** (Caveat: this uses c = 0.01 from `Config`; I have not checked that the atlas cost
accounting uses the same c in its per-round normalisation.)

### Proposition 3 (latency channel, where d matters). Under S1-S2 with the pending cap binding

(d/P > T/(2B)), the tau-th label is requested at about rho_tau ~ ceil(tau/P) d and is released at
t*_str ~ ceil(tau/P) d + d. When the pace cap binds (d/P < T/(2B)), rho_tau ~ max(tau, (tau - burst) T/(2B)) and
t*_str ~ rho_tau + d. Uniform releases the tau-th label at t*_uni = tau (T-d)/B + d. Hence the latency
advantage of straddle, t*_uni - t*_str, is

  (tau (T-d)/B) - rho_tau   >  0   iff   rho_tau < tau (T-d)/B.

In the pending-limited regime this is **d < d* = P (T-d)/B, i.e. d* ~ P T/(B + P)**, about 38.5 for
(T, B, P) = (1000, 50, 2). Below d* straddle clears first; above d* the pending cap throttles it to
P/d < B/T requests per round, below the uniform rate, so it clears *later* and also faces the
same horizon cut-off t + d <= T. This is an elementary calculation, not a theorem about the
full atlas method, whose clear time is random and depends on the evidence and stakes.
Script, Part A (exact discrete schedule, tau = 10): latency advantage 150, 148, 93, 39, -12 rounds at
d = 1, 10, 25, 38, 50 (positive up to d = 38, negative at d = 50; the crossing is between 38 and
50, so d* = 38.5 is a first-order estimate, not an exact crossing).

### Why the gain can turn negative at large d

1. **Throttling by the pending cap (proved above, Prop. 3).** With P = 2 and large d straddle sends 2
   requests per d rounds. At d = 50 that is 0.04 per round against the uniform 0.05, so the evidence
   arrives later than under uniform pacing.
2. **Labels arriving too late (heuristic, as in the task).** `can_query` requires t + d <= T. The
   burst cap front-loads the first `ceil(0.1B)` requests, and the keepalive logic
   (`K >= d + 1`) spends labels at fixed spacing regardless of whether they can still change a
   decision. With d = 50 a request made after round 950 is never released, yet it consumes budget;
   since straddle's clear time grows with d, a larger fraction of its remaining budget is spent late.
   I did not simulate the atlas method to quantify this channel; the exact schedule above only
   covers the stylised model.
3. **Stale "clear".** The call is judged clear on released labels that are d rounds old.
   Under a regime change at onset, a call that was clear before onset stays "clear" until the first
   post-onset label is released, d rounds later, so the keepalive-only queries during that window are
   uninformed about the change. (Heuristic; not tested.)

### Status of (c)

Propositions 1-2 are exact consequences of the stated schedule (proved, trivial). Proposition 3 is
proved for the stylised deterministic schedule. The link from these to the atlas gain is **heuristic**:
it predicts a sign change at d ~ 38 (between the registered d = 10 and d = 50) and a nearly d-independent label
saving. The atlas cost gain also depends on the evidence's random clear time, stakes, and the economic
check, none of which the model captures.

### Comparison with the map data

**Pending.** `outputs/failure_atlas_v1_cycle4_map/summary.md` did not exist when I finished (a run
was in progress: `run.log` showed 60 of 791 tasks done). Predictions to check once it exists, written
before seeing it:

- P1' (supports Prop. 3): family-1 mean gain falls from d = 1 to d = 50 (this is registered P1) and
  is already near or below zero at d = 50 in cells where tau >= 10.
- P2' (supports "saved labels are not the mechanism"): the gain by d has a much larger spread than
  the budget spent; check `used` (labels) by d if the map records it. Prediction: the difference in
  labels used between straddle and the ablation is roughly constant across d (within about 2 to 5
  labels), while the cost gain is not.
- P3' (falsifiable extension, beyond the registered grid {1, 10, 50}): at d = 25 the gain is positive; the zero-crossing is near d = 38 to 50. The
  grid has no such d, so this needs a targeted run if wanted.

Already available from the cycle-3 mechanism check (single cell, 200 fresh seeds): gain +0.1152, +0.0660,
-0.0166 at d = 1, 10, 50. These are consistent with a zero crossing between 10 and 50, and, since a
single cell cannot separate Prop. 3 from other explanations, consistent is all it is.

---

## Implication

Straddle is a **known technique in a new contract**, not a standalone contribution. Undecided-only
querying is the Chernoff / Naghshvar-Javidi / active-learning principle; the validity of predictable
query selection with delayed release follows from predictable-betting results (Waudby-Smith and Ramdas
Prop. 1 / Thm. 2, Xu et al. Prop. 2 / Thm. 2) and the repo's pending-label lemma, and the argument in (b) is a
re-statement of them; the label-saving count in (c) is arithmetic about a schedule; and the repo's
deadline-aligned kill already files delay-aware acquisition under approximate belief-state control.
Per Amendment 5, novelty is claimed only if the R2 audit finds no source theorem covering the result.
It does cover the validity part, and the saving part is too elementary to be a result, so **no
novelty claim should be made**. What survives is an empirical mechanism finding in the atlas
(straddle beats uniform acquisition in fast-feedback cells, and the gain shrinks with d) plus one
substantive correction: the d-dependence is best explained by acquisition *latency* (a pending-cap
throttle that crosses the uniform rate near d* ~ P T/(B + P)), not by the number of labels saved, which is
nearly constant in d. It is not killed as a mechanism, but it is killed as a contribution, and the
Amendment 4 wording ("saves labels only when feedback arrives before the decision becomes clear") should be
read as incomplete. The model-based predictions above remain heuristic until the map table is compared.
