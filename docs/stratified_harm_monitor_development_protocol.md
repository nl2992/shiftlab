# Stratified paired-harm monitor: bounded development protocol

**Status:** specification frozen before any 587/588/589 block use, 2026-10-27.
The follow-up header records this specification's commit. This is development, not confirmation.
**Freeze commit:** `7dd8d94aae2073305df468fdf5fb2677055fc0e1`
**Freeze recorded at:** `2026-10-27T14:08:27Z` (no live-data clock).
The [phase goal](agent_goal_stratified_monitor_phase.md), [comparator supplement](agent_goal_sota_benchmark_supplement.md),
[regime map](stratified_monitor_regime_map.md), and charter govern this protocol.

## 1. Target, construction, and prediction

Let D be gross paired decision cost and H=D-epsilon, epsilon=0.10. Test the intersection
`for every k: E[H_t|past,G_t=k]<=0`. This differs from the pooled history-conditional null.
Use a fixed partition, constant-within-stratum query probabilities and support bounds, fixed
equal alpha weights 1/K, and the standard weighted-Bonferroni or fixed convex-mixture
composition of bounded-mean betting processes. The primary combination is Bonferroni;
the convex mixture is a registered secondary. The [theory note](../papers/paper1_decision_drift/theory_notes.md)
states the filtration, proof, three allocation regimes, and independent algebra check.

**Falsifiable prediction:** the candidate and the equally equipped Chugg-style subgroup
composition will tie, because they use the same scores, allocations, bounds, weights and engines.
Any gain over a pooled method may instead reflect localization or the stronger intersection null.
Do not call the composition a new method. The primary G1 advancement criterion below is
expected to fail against that same-null incumbent. A numerical identity failure is a code issue,
not evidence of a contribution. This prediction is recorded before the learner-slice calculations.

## 2. Fixed strata and pilot information

Use the hard-budget binary task, n=3200, d=16, fn=5, fp=1; train events 0–399 and validation
events 400–799. For G1, reuse `adg_growth_prescreen.learner_slice` on CPU. It supplies only
learner-side validation actions, support, fitted proxy/classifier quantities and tariffs.
Do not access oracle probabilities or monitor-window outcomes.

For K in {2,4,8}, stratum 0 is policy agreement. On disagreement, split the known tariff
interval [0.5,2.5] into K-1 fixed equal-width bins, clipping the upper endpoint into bin K-1.
The boundaries are fixed here, not learned from outcomes. This partition is unchanged by
swapping policy roles and is eligible for a later real-path orientation check if all local bounds
cover both directions. No label is needed on agreement. Pilot frequencies and mean tariffs use
validation features/tariffs only. Report empty disagreement bins; assign them query floor 0.01
and exclude their zero pilot mass from numerical allocation objectives, without suppressing
their existence in K, alpha weights, or reports. In a future monitor their fixed bound still applies.

Agreement increments are known -epsilon. The K=2 allocation special case is gating; a subgroup
wealth process that skips agreements is not identical to the positive-margin pooled WP1 wealth.
Verify exact pooled-gating parity using the separately named pooled specialization retaining all
agreement increments, and test the subgroup process's own wealth identities separately.

## 3. Allocations and bounds registered before G1

The expected dollar target per event is b=r*mean(validation tariff), r in {0.02,0.05,0.10,0.20}.
All disagreement propensities lie in [0.01,1]; agreement query rate is zero. Excess capacity is
reported as underspend; it is not reassigned to artificial agreement labels. All competitors
receive the same allocation/bounds when testing whether that composition itself adds anything.

Evaluate three prespecified minimax allocation approximations from the theory note:

- Range-limited: `T_k=C_R/(w_k*q_k^2)`, `C_R=5.1^2*L/0.25^2`.
- Cap-dominated: `T_k=C_C/(w_k*q_k)`, `C_C=5.1*L/(0.8*0.25)`.
- Uncapped: `T_k=u_k+v_k/q_k`, using the exact pilot second-moment decomposition
  `V_k=A_k+C_k/q_k`, `u_k=2*L*A_k/(w_k*0.25^2)`,
  `v_k=2*L*C_k/(w_k*0.25^2)`.

Here L=log(K/0.05), w_k is pilot frequency, and c_k is mean pilot tariff. For the uncapped
design moments only, use a prespecified within-disagreement centered working mean 0.25:
gross mean 0.35, corresponding to probability `(0.35-l)/(u-l)` of the unfavorable binary cost.
Use the fixed pre-tilt learner ridge anchor `h=proxy_centered+epsilon` when evaluating its
residual moment. This design law is not an oracle estimate of the generator's future harm.
Solve the constrained budget problem with floors/caps; do not clip an unconstrained optimum
and assume the budget still holds. For a stratum with no residual second moment, its time is
constant and no stochastic residual correction is needed.

The PPI local bound on a disagreement bin is `B_k=5.1*(2/q_k-1)`, constant within that bin.
The agreement bin has bound epsilon and known increment -epsilon. The matched-common-bound
ablation uses max_k B_k for every bin on exactly the same increments/labels. Do not weaken the
existing context-alpha guard in `budgeted_promotion.py`.

## 4. Arms and matched comparator contract

| Arm | Null/information | Role |
|---|---|---|
| Stratified candidate K=2,4,8, each allocation above | Intersection null; PPI local bounds, fixed strata | Primary candidate family |
| Chugg-style subgroup composition, same K/allocation | Identical intersection null, scores, alpha weights, bounds and engine | Required strongest same-null construction comparator; expected exact identity |
| Stratified common-bound ablation | Same local null and query path; common max B | Isolates support bounds |
| Stratified proportional-query ablation | Same strata/engine; constant q_D from pilot disagreement spend | Isolates allocation |
| Pooled on each candidate query path | Pooled null; PPI increments with a valid fixed max B | Matched-label estimand comparison |
| Pooled ungated U1 | Pooled null; uniform r with correct policy-specific bound | Ungated baseline |
| Gated pooled HT | Pooled null; WP1 best applicable frozen arm, or fixed G1f if WP1 unfinished | Required gated comparison; G1f is the G1 analytic reference |
| Oracle-strata/full-feedback reference | Knows harm support; full labels on disagreements | Informationally/label-unmatched upper reference; never a learner input |

All fixed-growth comparisons use the same stake grid (0.05,0.1,0.2,0.4,0.8,1), equal weights.
Reachable zero factors have expected log factor minus infinity, not a clipped finite substitute.
Shared Timans GRAPA, plug-in adaptive, PPE/Xu, and horizon SR/CUSUM/started-mixture panel rows
are required if simulation is reached. An adaptive history-dependent engine has no single
eventwise fixed-stake growth number; G1 records that analytic limitation, and the pathwise
identity with the equally equipped subgroup composition applies to those engines as well.
Do not infer a win from an analytically omitted stronger engine.

Comparecast and PPRM have different null/estimands and cannot support a same-null ranking.
Q2 certification methods are outside this phase. The ADWIN feature sentinel is diagnostic only,
with its own feature-null calibration as in WP1. These exclusions are explicit panel entries.

## 5. G1 working laws and criterion

No monitor, query coin or future outcome is drawn. On the learner-side validation slice:

- Homogeneous harm: unfavorable-outcome probability 0.90 on every disagreement.
- Localised harm: probability 0.90 in the lowest `ceil((K-1)/3)` tariff bins on disagreement;
  other disagreement bins have gross mean zero (unfavorable probability `-l/(u-l)`).
  Report the actual pilot-average pooled excess. Cells at or below zero are intersection-only
  alternatives, not positive-pooled R4 evidence; retain them in the tables with that label.
- Mixed-sign: agreement has centered mean -epsilon. In the positive tariff-bin subset above,
  choose gross mean `min(4.4,(epsilon+0.5*w_rest)/w_positive)` when w_rest>0, then solve the
  common remaining-disagreement gross mean so the exact pilot-weighted pooled centered mean
  is zero. If w_rest=0, use gross mean epsilon/w_positive on disagreement. Convert each mean
  to its binary outcome probability and flag infeasible support targets, without clipping away
  infeasibility. This is a working-law contrast, not a calibration stream.

Compute exact outcome/query expected log factors with the existing ADG growth machinery.
Within-stratum expected growth is multiplied by pilot event frequency. A fixed subgroup
mixture's asymptotic rate is the largest stratum rate; report the finite log(K/alpha) penalty
separately. Record each stake's rate, selected maximizing stake and actual expected spend.
Selection among the three modeled allocations and K is a design screen, not confirmatory evidence.

For every allocation/K, independently evaluate the candidate and the equally equipped subgroup
formula, then require agreement to 1e-12. The strongest applicable analytic incumbent includes
that subgroup rate and the gated/pooled rates. The registered advancement criterion is:

1. At some registered budget, best-K localised positive-pooled growth is at least 1.5 times
   the strongest applicable incumbent with positive denominator.
2. At that budget its homogeneous-harm growth is at least 0.8 times gated growth when defined.

Undefined/nonpositive-denominator ratios cannot pass. Since the identical known subgroup
composition is in the incumbent maximum, condition 1 is predicted to fail. Report any benefit
over pooled methods next to this tie and the estimand distinction. Do not tune the partition,
effect sizes, allocations, stakes or thresholds after inspecting these outputs.

## 6. Seed registry, later gates, and stop rules

G1 CPU learner slices: 58700000–58700019, rechecked before freeze. No monitor-window field
enters G1. If G1 fails, write results/research-log entries and stop WP2 before simulation.

**Pre-G1 clarification, 2026-10-27:** the generator scenario for these learner slices is
`boundary_local_harm`; only train/validation events 0–799 enter the calculations. This
names the scenario omitted in the original seed-registry sentence. No 587 block slice or
G1 outcome has been computed before this amendment. The registered working laws replace
outcome probabilities analytically; natural monitor-window outcomes are never inspected.

Only if G1 passes: complete the stream adapter and formula/invariance tests before development.
Use the exact vector binary null from `stratified_harm_design`: on an action pair with costs
{+5,-1}, boundary probability is (1+epsilon)/6, not 0.5; on the reverse pair it is
(1-epsilon)/6. Agreement is strictly below the boundary at -epsilon. Every per-stratum mean
must equal its registered boundary or lie below it to 1e-12. Never use stationary or benign
nuisance to calibrate this intersection null.

Development: 58800000–58800059 per registered cell, CUDA generation, all four budgets,
K choices, allocations, homogeneous/localised/mixed-sign laws and matched panel/ablations.
Require at least +10 detection points over the gated arm and strongest same-null incumbent
in the localised primary, with no loss beyond 3 points in homogeneous harm, at no more labels.
No pre-onset alarm counts as detection; nondetections receive horizon-censored delay.
If this fails, stop. Only if it passes: exact intersection-null calibration, 2,000 streams per
cell on 58900000–58901999, simultaneous one-sided exact 95% upper bound at most 5% across
the registered candidate cells. Two failures after one explicitly registered fix stop the phase.

An oracle perturbation must not change learners; K=1 must match the pooled component;
Bonferroni/mixture wealth identities and local support bounds must hold. All runs record
configuration, HEAD/dirty paths, source/output hashes, hardware, device and runtime. Do not
change a frozen protocol silently. No confirmation uses 59100000–59100999 in this phase.

## 7. Exit and reporting

At G0/G1/development/calibration stop, publish the negative results and move to WP3, subject to
the phase hard stops. A G1 tie is a successful falsification, not a new-method result. If all
gates pass, WP4 minimum verification remains required before checkpoint A. Stop the whole
phase at checkpoint A, B or C exactly as specified in the goal. PaperBanana is required for any
figure; no figure is necessary for these tabular screens.
