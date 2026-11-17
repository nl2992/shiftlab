# 03F Risk-budgeted reversible intervention (F3): design, theorem and dev protocol

Status: design + theory written 2026-11-14 before any F3 code or run. Branch
`research/paper3-f3-risk-budget-2026-11-14` (from `research/paper3-safe-budgeted-intervention-2026-11-09`
@ ad5a6dab). Nothing here uses the registered confirmation block (5303...) or the sealed real group.

## 1. Formulation (what F3 is and is not)

F3 does **not** certify that a challenger will repay its switching fee over a future horizon. That
needs a drift class and is limited by T0/T1/T5 in `06_THEOREM_LEDGER.md`. F3 instead bounds the
**realised cumulative harm of intervening**, measured against never-switch, and keeps the
intervention reversible. Realised harm is observable in hindsight from sampled labels, so no
forecast and no drift class is needed. Failure of the payback certificate therefore does not bear
on F3.

Notation (contract `02_SCIENTIFIC_CONTRACT.md`): Z_t = ell_t(0) - ell_t(1) in [-1,1]; g_t in {0,1}
is the prediction-disagreement flag seen before acting, and Z_t = 0 when g_t = 0; a_t in {0,1},
a_0 = 0; N_t = number of action changes through t; k = switch fee.

    x_t = -a_t g_t Z_t                 per-round excess loss of the deployed action vs action 0
    H_t = k N_t + sum_{s<=t} x_s       intervention harm (model excess loss + switching fees)

Label fees are not part of H (they are governed by the label budget B and reported separately).

**Target.** For a user-chosen risk budget R >= 0 and level delta in [0,1):

    P( sup_{t<=T} H_t > R ) <= delta          for every loss sequence.            (F3)

Gains count: x_t < 0 lowers H_t, so a challenger that earns its keep frees capacity.

## 2. Observation model (stated precisely)

O1 Exogenous outcomes: actions and queries do not change losses (contract section 5).
O2 On each round with a_t = 1 and g_t = 1 ("exposed round") the controller picks a probability
   pi_t in {0} U [pi_min, 1] from its observed history, then queries with a private coin
   q_t ~ Bernoulli(pi_t). The coin is independent of the tape (losses, flags, delays) given the past.
   pi_t = 0 is a "blind" round (e.g. label budget exhausted).
O3 A queried label is released at some later round, or never. The delay may be random, depend on
   the outcome (informative), or be chosen adversarially. No assumption. (Added 2026-11-17 while drafting: the delay
   and loss of round s may depend on the past and on the outcome, but not on round s's own query
   coin, which O2 already requires to be independent of the tape given the past.)
O4 Losses in [0,1]; agreement rounds have Z_t = 0.

No assumption on the law of (Z_t): arbitrary drift, reversals and serial dependence are allowed.
All probability in (F3) comes from the query coins (design-based).

## 3. Anytime upper confidence bound

For exposed rounds s <= t split blind / monitored (pi_s > 0). At the start of round t+1 (after
releases) define, over rounds s <= t,

    A   = sum over queried and released s of x_s / pi_s            (observed)
    P   = sum over queried and still-pending s of 1 / pi_s         (worst case for unreleased)
    nb  = number of blind exposed rounds                            (worst case x = 1)
    V   = sum over monitored s of (1/pi_s - 1)                      (predictable variance proxy)
    M_t = sum over monitored s of x_s (1 - q_s/pi_s)                (unobserved martingale)

Pathwise: sum_{s<=t} x_s <= nb + A + P + M_t (since x_s <= 1 and x_s q_s/pi_s <= 1/pi_s).

**Lemma 1 (Bennett mixture).** Let b = max(1, 1/pi_min - 1), phi(lam) = (e^{lam b} - 1 - lam b)/b^2,
Lambda a finite grid of lam > 0 with weights w summing to 1. Under O1-O2, with probability
>= 1 - delta, for all t simultaneously, M_t <= D(V_t), where D(0) = 0 and for V > 0

    D(V) = min_{lam in Lambda} [ ln(1/(delta w_lam)) + phi(lam) V ] / lam .

Proof. xi_s = x_s (1 - q_s/pi_s) has conditional mean 0 (O2), conditional variance
x_s^2 (1/pi_s - 1) <= 1/pi_s - 1, and xi_s <= b (x_s >= 0 gives xi_s <= x_s <= 1; x_s < 0 gives
xi_s <= |x_s|(1/pi_s - 1) <= 1/pi_min - 1). Bennett's inequality gives
E[exp(lam xi_s) | past] <= exp(phi(lam)(1/pi_s - 1)), so exp(lam M_t - phi(lam) V_t) is a
nonnegative supermartingale started at 1, and so is the w-mixture. Ville's inequality gives the
claim for V_t > 0; when V_t = 0 every monitored round had pi = 1, so M_t = 0 surely. QED.

    U_t = k N_t + nb + A + P + D(V_t)      is an anytime (1-delta) upper bound on H_t.

With pi = 1 everywhere V = 0, D = 0 and the bound is deterministic (delta = 0).

## 4. Controller: risk-budget shield around any promotion rule

The shield wraps an arbitrary inner policy (here: tuned Wald+cutoff). The inner policy proposes
actions and, while a = 0, queries. The shield enforces one invariant. At round t, after releases,
if the inner policy proposes a_t = 1, compute for a monitoring rate pi (c(pi) = 1/pi, or 1 if blind):

    W_t(pi) = k (N_{t-1} + 1{a_{t-1}=0})     fees incl. this promotion
            + k                               RESERVE: fee of a later rollback
            + nb + A + P                      resolved harm + worst case for pending feedback
            + g_t c(pi)                       RESERVE: this round's own harm, known only after its delay
            + D(V_{t-1} + g_t (1/pi - 1))     confidence width after this round

Deploy a_t = 1 iff W_t(pi_t) <= R for the chosen pi_t; otherwise a_t = 0 (a rollback if a_{t-1} = 1;
its fee was already reserved). pi_t is the cheapest rate in a menu (e.g. {pi_lo, 1}) that keeps
W_t(pi) <= R - margin, falling back to 1; blind if no labels remain.

Ride-out (optional): if k N_{t-1} + nb + A + P + D(V_{t-1}) + (T - t + 1) <= R while a_{t-1} = 1, the
remaining horizon cannot exhaust the budget; stay deployed to T without queries, each remaining
round booked as blind, and no rollback reserve is needed.

Label reserve: while a = 0 the inner policy sees `labels_remaining` reduced by a reserve L_res so
that monitoring labels exist after a promotion.

**Theorem 2 (pathwise risk budget).** Under O1-O4, for any inner policy, any loss sequence, any
delay or missing-label mechanism and any R >= 0, the shielded controller satisfies
P(sup_t H_t > R) <= delta. With pi_t = 1 on every monitored round, sup_t H_t <= R surely.

Proof. Let I_t = k N_t + k a_t + nb + A + P + D(V_t), all evaluated after round t. I_0 = 0.
(i) A + P never increases when a label is released (x_s/pi_s <= 1/pi_s) and D is nondecreasing in
V. (ii) If a_t = 1, the round adds at most g_t c(pi_t) to nb + A + P and g_t(1/pi_t - 1) to V, so
I_t <= W_t(pi_t) <= R. (iii) If a_t = 0: a rollback raises N by 1 and drops the reserve, so
k N_t + k a_t is unchanged, and no other term grows, hence I_t <= I_{t-1}. By induction I_t <= R
for all t. On the Lemma 1 event H_t <= U_t <= I_t. Ride-out replaces the reserve k by the
remaining-horizon count, which each later round decrements while adding at most 1. QED.

**Proposition 3 (the reserves are necessary).** (Proved 2026-11-16; replaces the earlier sketch.)
Suppose every label requested at round s is released no earlier than s + d (d >= 1). Let a
controller satisfy (F3) for every loss sequence. Fix any environment E and rounds j, m with
1 <= m <= d, and let A be the event that the first promotion is at round j and a_s = 1 for
s = j, ..., j+m-1. Write e for the number of disagreement rounds in [j, j+m-1] and n for the number
in [j, T]. If P_E(A) > delta then

    R >= min( 2k + e,  k + n ).

Proof. Let E' agree with E before round j and have Z_s = -1 on every disagreement round s >= j.
Any label visible at a round s <= j+d-1 was requested at or before s - d <= j - 1, where E and E'
coincide, so with the same coins the controller takes the same actions through round j+d-1 in both
environments; hence P_E'(A) = P_E(A) > delta. On A under E', H_{j-1} = 0 (no earlier promotion) and
H_{j+m-1} = k + e. If the controller later rolls back at some round rho, H_rho >= k + e + k. If it
never rolls back, H_T = k + n. Since n >= e, sup_t H_t >= min(2k + e, k + n) on A, and (F3) forces
this to be <= R. QED.

Reading. The three terms of W_t on a first promotion are exactly these: k for the promotion, k
reserved for the rollback, and one unit for every exposed round whose label cannot yet have
arrived. With labels that may never arrive (d = infinity) the bound covers every hold length, which
is the blind accounting. The shield meets the bound with equality: on an all-harm tape it holds a
first promotion for exactly floor(R - 2k) rounds (`results/riskbudget/props_check.json`, 12 of 12
(d, R) cells), so it permits every feedback-blind hold that any valid controller could make. The
ride-out branch corresponds to the k + n term (it uses the remaining round count, an upper bound
on n, because future flags are unknown). The proposition is about the feedback-blind window only;
it says nothing about how well a controller uses labels once they arrive.

**Proposition 4 (price of safety).** (Proved 2026-11-16; replaces the earlier sketch.)
Consider the full-sampling shield (pi = 1) with fixed delay d, during its first deployment spell,
while labels remain and the inner policy keeps proposing action 1. Let y_1, y_2, ... be the values
of Z on the exposed rounds of the spell, in order, and suppose E[y_i | everything before exposed
round i] >= mu > 0. Let m = R - 2k - d. Then

    P( the shield forces a rollback during the spell ) <= exp(-2 mu m),

and if y_i takes values in {-1, +1} with P(y_i = +1 | past) >= p > 1/2, the probability is at most
((1-p)/p)^(floor(m)+1).

Proof. During the spell N = 1 and W_t = 2k + (sum of x over released exposed rounds) + (pending
count) + g_t. With fixed delay d the pending rounds and the current round lie in the last d rounds,
so their count is at most d, and the released rounds are a prefix of the exposed sequence. Hence
W_t <= 2k + d - S_n for some n, where S_n = y_1 + ... + y_n. A forced rollback needs W_t > R, that
is S_n < -m for some n. For theta = 2 mu, Hoeffding's lemma (y_i in [-1,1]) gives
E[exp(-theta y_i) | past] <= exp(-theta mu + theta^2/2) = 1, so exp(-theta S_n) is a nonnegative
supermartingale and Ville's inequality gives P(inf_n S_n <= -m) <= exp(-2 mu m). For +-1 steps,
(q/p)^{S_n} with q = 1 - p is a supermartingale and S_n < -m means S_n <= -(floor(m)+1), which gives
the second bound. QED.

Numerical check (`scripts/paper3/riskbudget/check_props.py`, dev seeds offsets 50000-51999, 2000
runs per cell, inner = always-challenger, label budget not binding, no ride-out): the forced-
rollback frequency is within Monte Carlo error of the ruin bound or below it in all 24 cells (corrected 2026-11-17: 5 of 24 cells exceed it at the point estimate, by at most 0.7 binomial standard errors) (p in {.6,.7,.8}, d in {1,5},
R in {10,12,15,20}). At d = 1 the bound is tight: p = .6, R = 10 gives .204 against .198 (within
Monte Carlo error); p = .7, R = 10 gives .035 against .034. At d = 5 it is loose by 2-6x, because
the pending count is usually well below d.

Scope. The proposition covers the first spell with labels available. The forced rollbacks seen in
the dev and confirmation runs in beneficial regimes (e.g. 13% at R = 20 in `stationary_better`) are
mostly outside it: there the label budget B = 60 runs out and rounds are booked blind, and the
Wald inner policy starts further spells, each costing another 2k of budget.

Honest novelty note: Lemma 1 is IPW + Bennett + Ville, all standard. What is specific to F3 is the
target (realised harm, not future payback), the design-based validity that survives dependence,
informative delays and missing labels, and the reserve accounting for feedback that arrives after
an action. The e-process gates in A_RESULTS lost validity at rho = .95 (FP .47-.57); Theorem 2
does not need a mean-zero null at all.

## 5. Dev protocol (exploratory; dev seed block only)

Seeds (dev block 5301000000+): tuning offsets 0-5 (as workstream A); F3 pilot offsets 20000-20199;
F3 dev-eval offsets 30000-30999 (1000 seeds). T = 300. The 24 regimes of `regimes_v1.json` plus
stress regimes in `regimes_f3_v1.json`:
`adverse_informative_delay` (labels unfavourable to the challenger arrive much later),
`label_dropout` (a fraction of requested labels never arrives),
`bait_reversal` (challenger strongly better for the first quarter, then strongly worse),
`dep_harmful_rho_0.95` (challenger worse, strong dependence).

Arms:
- never; tuned wald_cut (matched inner, same B); tuned cusum; tuned gate_wald (e-process gate).
- cusum_rb: Wald+cutoff promotion with a one-sided CUSUM rollback on post-promotion labels.
- stoploss_plugin: Wald+cutoff + naive budget stop (roll back when k N + A > R - k; no pending
  reserve, no confidence width). The "obvious" risk-budgeted controller.
- F3 shield over the same tuned wald_cut: pi = 1 (deterministic), and adaptive pi with
  pi_lo in {.5, .25}; R in {8, 10, 12, 15, 20, 30}; delta = .05.
- F3 ablations: no pending reserve; no rollback reserve; no confidence width; no ride-out.
- Baseline conservativeness sweeps to trace each baseline's own risk/cost frontier:
  wald_cut gamma in {.02,.05,.1,.2,tuned}; cusum h in {2,4,8,12}; gate alpha in {.01,.05,.1,.2}.

Metrics per (arm, regime): violation rate P(sup_t H_t > R) with Wilson 95% interval; mean, 95%,
99% and max of sup_t H_t; mean J; paired Delta J vs matched wald_cut and vs never (seed-cluster
bootstrap 95% CI); labels used; switches; forced rollbacks. Pooled equal-weight over regimes.

What would count as a positive result (no pass/fail gate; report whatever happens):
1. F3 violation rate <= delta in every regime, including dependence, informative-delay and
   dropout regimes, while at least one comparator exceeds it materially.
2. Mean-J cost of the shield relative to matched Wald+cutoff is small, or negative in harmful /
   reversal regimes.
3. At equal tail harm (95% quantile of sup H), F3 has lower J than each baseline's own
   conservativeness frontier.
4. Each ablated reserve produces violations on some regime (the components are needed).

## 6. Version 2 (designed 2026-11-14 after the first dev run; v1 code and results are kept)

Diagnosis from `results/riskbudget/dev_summary.json` (v1, dev seeds 30000-30999): the cost against
Wald+cutoff in benign regimes is mostly label exhaustion, not the budget itself. With pi = 1 the
shield spends 54-59 of B = 60 labels in beneficial regimes, then runs blind (worst case 1 per
exposed round) and is forced back or vetoed; deployed time is .51-.57 against .68 for Wald even at
R = 30. The partial-sampling arms did not help because (a) a queried pending round reserved 1/pi,
(b) the uniform 16-point mixture costs ln 16 inside the width, (c) pi was lowered only by a margin
rule, not by label pacing.

### 6.1 Simpler validity argument (covers v1 and v2)
Let E be the event of Lemma 1 (or 1'). Suppose that at every round t with a_t = 1 the controller
has verified W_t <= R for a quantity W_t that satisfies H_t + k <= W_t on E (H_t + remaining
worst case <= W_t in ride-out). Then on E, sup_t H_t <= R: at deployed rounds H_t <= W_t - k; after
the last deployed round t' harm is H_t' plus at most the rollback fee k. No monotone invariant is
needed, so any valid upper bound may be used at each round.

### 6.2 Lemma 1' (exact coin mixture)
For x in [-1,1] and coin rate pi, E exp(lam x (1 - q/pi)) is convex in x, so it is at most
exp(psi(lam, pi)) with
    psi(lam, pi) = ln max( pi e^{-lam(1/pi-1)} + (1-pi) e^{lam},  pi e^{lam(1/pi-1)} + (1-pi) e^{-lam} ).
psi >= 0 and psi(lam, 1) = 0. With Psi_t(lam) = sum of psi(lam, pi_s) over the rounds included in
M, exp(lam M_t - Psi_t(lam)) is a supermartingale; mixing over a small grid (default 5 lam values
aimed at total variance 4, 16, 64, 256, 1024; weights 1/5) gives, with probability >= 1 - delta for
all t, M_t <= D_t = min_lam [ ln(1/(delta w_lam)) + Psi_t(lam) ] / lam, and D_t = 0 if no included
round had pi < 1. Any per-round pi in [pi_min, 1] is allowed (no global b).

### 6.3 Settlement accounting for sampled rounds
Rounds with pi_s = 1: as v1 (worst case 1 while pending, then exact x_s; no martingale term).
Rounds with pi_s < 1: fix a window w >= 1 (declared delay if known, else a parameter). The round is
"unsettled" until s + w and is booked at worst case 1 (x_s <= 1) regardless of its coin. At s + w
it settles: it enters M (its psi is added to Psi) and contributes x_s/pi_s if queried and released,
1/pi_s if queried and still unreleased (replaced by x_s/pi_s if it arrives later), 0 if not queried.
Validity: the settled set at time t is the deterministic prefix {s <= t - w}, so M over settled
rounds is the same martingale stopped at a deterministic time and Lemma 1' applies; unsettled
rounds are bounded by 1 each pathwise. Blind rounds: worst case 1.

    W_t = k (N_{t-1} + 1{a_{t-1}=0}) + k + [blind] + [pi=1: resolved x + pending count]
        + [sampled, settled: A_s + unreleased 1/pi] + [sampled, unsettled count] + g_t + D_t

### 6.4 Label-paced monitoring (predictable)
On an exposed round: target = labels_remaining / max(rhat (T - t + 1), 1), rhat = running
disagreement rate (prior as PacedAcq). If target >= 1 use pi = 1. Else pi = max(pi_min, target),
or blind if no labels remain. Additionally, if headroom R - W_t(blind) >= blind_margin the round may
be left blind to save labels (generalised ride-out). If the paced choice fails W_t <= R, escalate to
pi = 1; if that fails, roll back.

### 6.5 Joint tuning with the same budget as every baseline
The shielded system (inner Wald lam, gamma, stop; label_reserve_frac; pi_min; blind_margin; window w
when the delay is undeclared) gets the same 32-config random search on the 6 tuning seeds x 24
original regimes with the same objective (mean over regimes of J / J_never), at R = 20. The chosen
config is then frozen and used at every R. Evaluation of v2 uses FRESH dev seeds, offsets
40000-40999, with v1 arms and baselines re-run on the same tapes; the stress regimes are not used
for tuning.

## 7. Label-scarce regime (designed 2026-11-16 after the real-stream check; exploratory)

Finding (`F_RESULTS.md`, real-stream check): with T = 2000, B = 200 and 120-1,560 disagreement
rounds per episode, the frozen arms cost 7-46% more than Wald+cutoff. Diagnosis to be confirmed on
simulation, not on the real streams: (a) full sampling spends one label per exposed round, runs out,
books the rest blind and is forced back with no labels left to re-enter; (b) the frozen paced arm
has pi_min = .5, so its pacing target L_rem / n_rem (about .2-.3 here) is floored at .5 and it also
runs out; (c) when the exposure inside one delay window r*d exceeds the headroom h, Proposition 3
forces every valid controller to cycle (deploy, roll back, wait, re-enter) until banked gains cover
the window; that part is not removable.

Why a fix should exist for (a)-(b): at sampling rate pi the width after n sampled rounds is about
sqrt(2 ln(1/delta) n (1/pi - 1)) while a challenger with advantage mu per exposed round banks mu n,
so the bound falls once n > 2 ln(1/delta)(1/pi - 1)/mu^2. Labels spread over the whole horizon can
therefore certify a clearly better challenger; a weakly better one (mu below about .3 at these
sizes) cannot be certified from 200 labels by any IPW bound of this kind.

v3 = the v2 controller with no change to its validity argument (6.1-6.3): pacing floor lowered
(pi_min candidates .05, .1, .25), mixture grid extended to V = 4096 for the larger variance, and the
existing look-ahead guard keeping pi = 1 while headroom is thin (exact-first). Candidates also vary
label_reserve_frac (.1, .25) and blind_margin (None, 8).

Development data: a new label-scarce simulation family `configs/paper3/regimes_f3_scarce_v1.json`
(T = 2000, B = 200, k = 5, c_q = .05; disagreement r in {.1, .25, .4}; delay in {24, 100, 144};
beneficial, harmful and reversal paths; rho in {0, .8}). Selection on dev seeds offsets
70000-70199 by pooled mean J at h = 50 (ties: larger pi_min); the chosen config is frozen and
evaluated on fresh dev seeds 71000-71499, on the original 30 regimes (offsets 72000-72299) to check
it does not cost anything where labels are plentiful, and then once more on the 14 real streams.
That last run is a SECOND LOOK at streams already seen once with the earlier arms and is reported
as such next to the first.
