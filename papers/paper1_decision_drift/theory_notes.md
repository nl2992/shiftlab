# Assumptions and limitations

Within-regime independence and Gaussian synthetic responses permit evaluator Bayes risk calculations. No anytime-valid alarm or arbitrary-nonstationarity coverage guarantee is claimed. Feedback cannot identify unobserved changes without assumptions on label missingness. Adaptation-oracle regret is deferred.

## Stratified monitor phase: conditional statements, 2026-10-27

These statements concern a proposed new path under the assumptions below. They do not upgrade
the preceding baseline-study claims or establish that any real stream satisfies the null.

### Target and filtration

Write gross paired cost `D_t=c(pi_t(X_t),Y_t)-c(ref_t(X_t),Y_t)` and centered harm
`Z_t=D_t-epsilon`. Before the current outcome, a fixed partition assigns `G_t in {1,...,K}`
using current features. Policies, proxy `h_t`, and query propensity `q_t>0` are fixed before the
query coin; that coin is conditionally Bernoulli(q_t) and independent of the potential outcome.
The stratum may be known after `F_(t-1)`, so "pre-outcome" does not mean measurable at the
previous event. Delays are outside this phase's immediate-feedback derivation.

The intersection null is `H0=intersection_k H0,k`, where
`H0,k: E[Z_t | F_(t-1),G_t=k] <= 0` at every event with positive stratum probability.
This is stronger than the pooled null `E[Z_t|F_(t-1)]<=0`. Mixed-sign stratum means can satisfy
the pooled null and violate this intersection null. The earlier decision-local mixed-sign
experiment therefore becomes an alternative here; its old pooled-null interpretation is not
repaired by relabelling it.

Let `H_t=h_t + Q_t/q_t*(D_t-h_t)-epsilon`. Query averaging conditional on the potential
outcome gives `E_Q[H_t|F_(t-1),X_t,Y_t]=Z_t`; integrating current features/outcomes within a
stratum gives `E[H_t|F_(t-1),G_t=k]=E[Z_t|F_(t-1),G_t=k]`. Agreement costs are known zero,
so they need no query and give centered increment `-epsilon` exactly.

### Validity: standard subgroup betting composition

Fix constants `B_k>0`, positive fixed weights `a_k` summing to one, and fixed stakes
`0<s<=1`. Require `|H_t|<=B_k` whenever `G_t=k`. The calendar-time process

```text
E_(k,t)(s) = product_(i<=t) [1 + 1{G_i=k} * s*H_i/B_k]
```

is nonnegative. Its factor has conditional expectation
`1 + P(G_t=k|past)*s/B_k*E[H_t|past,G_t=k] <= 1` under H0,k.
This directly proves the optional-subsequence claim without falsely assuming that the current
stratum is measurable at the previous event. Stakes selected from prior history work too if
they are fixed before current stratum/features, or have a separate appropriate conditional-null
argument. Arbitrary current-feature-dependent stake or bound choices within a stratum are not
licensed. Bounds may be learned on a disjoint pilot and then conditioned on/frozen.

Fixed mixtures over stakes retain the supermartingale property. Ville and a union bound give
strong FWER at most alpha for individual declarations `sup_t E_(k,t)>=1/(alpha*a_k)`, provided
each true stratum null holds in the common filtration, even if other strata are alternatives.
The fixed convex mixture `sum_k a_k E_(k,t)` is a nonnegative supermartingale under the
intersection null and can reject that global null at `1/alpha`; its crossing alone does not
identify a particular harmed stratum. These are published betting/merging principles, not a
new validity result. See the Chugg comparator audit and Vovk–Wang.

### Regime-specific detection approximations

Under an approximately stationary post-change working law, write stratum frequency `w_k`,
positive centered mean `mu_k`, second moment `V_k(q_k)=E[H_t^2|k]`, and label tariff mean `c_k`.
Keep frequency `w_k` separate from alpha weight `a_k`. Let
`L_k=log(1/(alpha*a_k))`; a fixed stake-mixture component additionally pays `log(1/omega_s)`.
Ignoring overshoot and pre-change accumulated wealth, wall-clock detection time is approximately
`T_k=L_k/(w_k*G_k)`. This is a working approximation, not an expected-delay theorem.

For a continuous stake approximation, `G_k(lambda) ~= lambda*mu_k-lambda^2*V_k/2`,
with `lambda<=s_max/B_k`. Thus:

```text
uncapped: lambda*=mu_k/V_k; G_k*=mu_k^2/(2 V_k)
capped:   lambda*=s_max/B_k;
          G_k*=s_max*mu_k/B_k - s_max^2*V_k/(2 B_k^2)
```

Only when the quadratic correction is negligible does the capped time reduce to
`B_k*L_k/(w_k*s_max*mu_k)`, linear in the support bound. In the uncapped regime the leading
time is `2*V_k*L_k/(w_k*mu_k^2)` and has no direct B dependence. A Hoeffding/range-limited
comparison instead uses a quadratic support penalty proportional to `B_k^2*L_k/(w_k*mu_k^2)`.
These three comparisons must not be interchanged.

For a fixed gross-cost anchor and constant-within-stratum propensity q_k, define `C_k=E[(D_t-h_t)^2|k]` and
`A_k=E[Z_t^2|k]-C_k`. Query randomization gives exactly
`V_k(q)=A_k+C_k/q`. A_k need not be nonnegative; V_k is nonnegative at feasible q.
The quadratic approximation must be checked against the exact finite-stake expected log
factor using the existing growth machinery, including whether its optimizing stake really
lies in the stated regime. No unverified 4.3x, 10x, or derived 18x measurement is used.

### Label-dollar allocation and choosing K

There is no distribution-free optimal K: it depends on how partition refinement changes
`w_k, mu_k, V_k, B_k`, tariffs, and alpha weights. State an allocation objective. For a
conservative unknown-location working alternative, use minimax time across the prespecified
potentially harmed strata, with `sum_k w_k*c_k*q_k<=b` and registered floors/caps.
This objective is a development design choice, not a universal optimality claim.

In the small-q support approximation `B_k~=d_k/q_k`, and temporarily ignoring floors/caps:

```text
range-limited: T_k=C^R_k/(w_k*q_k^2), C^R_k=d_k^2*L_k/mu_k^2
q*_k = b*sqrt(C^R_k/w_k) / sum_j c_j*sqrt(w_j*C^R_j)
T*   = [sum_j c_j*sqrt(w_j*C^R_j)/b]^2

cap-dominated, negligible curvature: T_k=C^C_k/(w_k*q_k),
C^C_k=d_k*L_k/(s_max*mu_k)
q*_k = b*C^C_k / [w_k*sum_j c_j*C^C_j]
T*   = sum_j c_j*C^C_j / b

uncapped: T_k=u_k+v_k/q_k,
u_k=2*L_k*A_k/(w_k*mu_k^2), v_k=2*L_k*C_k/(w_k*mu_k^2)
q_k(T)=v_k/(T-u_k), for T>max_k u_k
```

The last regime gives a monotone one-dimensional budget equation, not the same allocation as
either support approximation. With floors/caps, choose the smallest T for which every required
q_k(T) is within its upper cap and the dollar cost of `max(q_floor,k,q_k(T))` is at most b.
Handle `C_k=0` separately: its time is constant and no stochastic label correction is needed.
Upper caps include q_k<=1. If `sum_k w_k*c_k*q_floor,k>b`, the design is infeasible before
allocating any remaining budget; do not clip a solution and silently exceed the cap.
For the exact symmetric support `B_k=M_k*(2/q_k-1)`, analogous monotone inversion replaces
`d_k/q_k`; verify the selected solution numerically, not by clipping an unconstrained optimum
and assuming the dollar budget still holds.

For every registered K in {2,4,8}, obtain learner-side partition quantities from the specified
pilot, solve each regime's feasible allocation, and select the discrete minimizer of that regime's
predicted objective. Then check exact expected growth before any development simulation. For
one known harmed stratum the time-minimizing allocation instead gives it all budget remaining
after other registered floors, capped at one; that oracle knowledge is not available to the
learner. Report it only as an oracle reference.

For equal-frequency strata with the same bound and homogeneous harm, the range-limited pooled
versus stratum calendar-time gain is `(B_global/B_k)^2 * L_pooled/(K*L_k)`; the cap-dominated
counterpart is `(B_global/B_k) * L_pooled/(K*L_k)`. The uncapped counterpart depends on V, not B.
Uniform q and homogeneous harm with equal local and pooled bounds therefore give no
support-based stratification advantage.
Any practical gain needs localized harm, smaller feasible local bounds, or a demonstrably better
allocation. Give that same composition/allocation to the published subgroup incumbent too.

### Gating special case and an exact-equivalence caveat

As a label-allocation problem, agreement/disagreement is the K=2 special case: gross cost on
agreement is identically zero, so all labels go to disagreement. This is DISCERN's established
idea. With positive epsilon, the agreement's *centered* value is -epsilon, not zero.

A pooled gated WP1 process multiplies the known agreement factors as well as the disagreement
factors. A subgroup process which simply skips agreements and tests `E[D-epsilon|disagreement]
<=0` has a different null and wealth path. Therefore a naive K=2 intersection combination
cannot be asserted to equal the WP1 pooled HT arm exactly. An exact implementation-parity test
must use a separately named pooled-gating specialization which retains every known agreement
increment and the same common bound/stakes. For the intersection process, test its own explicit
wealth identity. Neither a factor-of-K alpha penalty nor a changed centering margin may be
silently removed to manufacture equality. This distinction is registered before WP2 outcomes.

### Real-path orientation condition

For a fixed full-information path, independent fair orientation coins S_t give
`E[S_t*D_t|path,past coins]=0`. Strata and their bounds must be invariant to the current coin
and each bound must cover both swapped action orientations. Then conditional mean within each
fixed path stratum is -epsilon and the intersection-null argument applies. Ordered-policy-role
strata or orientation-specific bounds need not preserve sign cancellation and are excluded.
This verifies a randomized null on a path; it establishes neither real policy harm nor utility.

**Independent check (2026-10-27).** A scoped smaller-model audit checked the conditional-factor
proof, strong FWER, mixture, all three growth regimes, moment identity, minimax allocation
formulas, gating caveat, and orientation condition. Fixed-constant numerical checks of the
allocation equations spent exactly b and equalized the modeled stratum times. The primary
agent reviewed the report and incorporated its three precision clarifications: constant
within-stratum q for the moment formula, infeasible floors/upper probability caps, and equal
local/pooled bounds in the homogeneous no-gain statement. This is an independent algebra check,
not a calibration result or a formal external theorem review.

## Predictable observation control for WP3 (2026-10-27)

Let H_t=D_t-epsilon, |H_t|<=B, and E[H_t|F_(t-1)]<=0. Choose theta_t from
F_(t-1), before current X_t, and draw an independent Bernoulli I_t. For any
predictable stake s_t in [0,1], the factor `1+s_t I_t H_t/B` has conditional
expectation at most1 and is nonnegative. A skipped event has factor1. A selected
agreement has exactly known H=-epsilon without needing a label; retaining that
score preserves the pooled-null argument. Selecting only current disagreements
and dropping agreement scores would require a different argument/null.

A hard-cap stop based on past spend and the known maximum tariff is predictable,
so setting all later factors to1 is valid. The lagged pacer and lagged SR statistic
may choose theta, but a current sentinel may affect only the next decision.
The present prescreen uses only lagged SR and past tariffs/actions. This removes
the DE-CuSum drift during skips, which is not a null e-factor by itself.

For fixed start j let E_(j,t) be its product of valid factors. With calendar SR
`R_t=sum_(j=1)^t E_(j,t)` and horizon T, E[R_t|F_(t-1)]<=R_(t-1)+1.
Consequently M_t=R_t+T-t is a nonnegative supermartingale starting at T. Since
R_t>=T/alpha implies M_t>=T/alpha, Ville's inequality gives
`P(max_(t<=T) R_t>=T/alpha)<=alpha`. A fixed mixture over stake-specific SRs
has the same proof; the corresponding CUSUM maximum is bounded by SR pathwise.
Every skip still opens a calendar start. An equal-weight mixture of a fixed set
of start-specific e-processes (including dormant wealth1 before each start) is
instead an e-process and uses threshold1/alpha. Restart adaptive betting history
at each such start, or explicitly prove the chosen shared-history construction.

This is a known e-factor/e-detector composition. Its proof gives no guarantee
that an adaptive sampling policy beats paced sampling, a temporal budget policy,
or a stronger betting engine. WP3 tests that separate efficiency question with
the full matched panel under its frozen prescreen protocol. The 20 alternative
seeds do not establish empirical null calibration or a confirmed method win.
