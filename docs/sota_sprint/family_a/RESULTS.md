# Family A: dependence-aware certification. Screening results

Status: development screening (20 dev seeds, base 2026110501) plus a 300-seed null check (base
2026110511) for the promising candidates. Nothing here is validation evidence. Code:
`scripts/sota_sprint/fam_a.py`; tests: `tests/sota_sprint/test_fam_a.py` (16 pass). Ledger:
`ledger.json`. Analyzer tables: `screen1.md` (A1-A6), `screen2.md` (round-2 dev variants
A1b/A5b/A6b/A2b), `ablations.md`, `null300.md`. Raw records: `outputs/sota_sprint/A/` (gitignored).

## Candidates

| id | mechanism | null class / validity |
|---|---|---|
| A1 | sequential universal inference: Markov-mixture numerator / rigorous upper bound on the null sup of the gap-indexed Markov likelihood; sparse started mixture | stationary 2-state Markov sign, p <= 1/2, **any rho in [0,1]**; P(false promotion) <= alpha (Ville) |
| A2 | adaptive query density: min event gap g* = min{g: rho_hat^g <= .25}, rho_hat = gap-indexed MLE from released labels; QSG iid evidence | not certified under dependence |
| A3 | dual-clock: new tests start at the next outcome in query order (in-flight outcomes used); front-loading pauses when in-flight queries exceed 2x projected need | QSG's (iid) |
| A4 | bet only on outcomes following an unfavourable one: P(z=1 given prev=0) = (1-rho^g)p <= 1/2 for any rho | same class as A1 |
| A5 | A1 + A2 | as A1 |
| A6 | A1 + A2 + A3 | as A1 |

Round-2 dev variants, declared as dev tuning after screen1: `A1b`/`A5b`/`A6b` put .7 of the
numerator prior on rho'=0 (was .5) and .75 weight on the first start (was .5). `A5b`/`A6b`/`A2b`
set rho_hat = 0 unless its likelihood beats rho = 0 by > 2 nats. These values were set a priori
and not searched. The 300-seed nulls ran after this and nothing was tuned on them.

## Dev screen (20 seeds; net cost, lower is better; promotion rate in parentheses)

| policy | F0_better | F6_delay400 | S_delay800 | F9_bursty | F5_dep_better_r8 | S_dep_better_r95 | null r8 | null r95 | F0_null |
|---|---|---|---|---|---|---|---|---|---|
| A1 | 381.2 | 386.7 | 398.4 | 380.6 | 434.1 | 427.7 | 0 | 0 | 0 |
| A1b | 375.8 | 376.8 | 397.6 | 380.0 | 434.1 | 429.7 | 0 | 0 | 0 |
| A2 | 364.2 | 373.7 | 394.0 | 363.8 | 350.2 | 360.1 | .20 | .60 | 0 |
| A3 | 366.6 | 373.7 | 393.9 | 360.7 | 342.1 | 342.2 | .20 | .75 | 0 |
| A4 | 416.2 | 402.6 | 407.4 | 405.7 | 434.1 | 429.7 | 0 | 0 | .05 |
| A5 | 376.6 | 385.9 | 398.4 | 388.9 | 427.7 | 424.0 | 0 | 0 | 0 |
| A5b | 373.8 | 376.8 | 397.6 | 384.8 | 430.5 | 424.4 | 0 | 0 | 0 |
| A6 | 376.4 | 388.4 | 398.4 | 389.5 | 427.7 | 423.9 | 0 | 0 | 0 |
| QSG | 366.6 | 371.8 | 394.0 | 360.7 | 341.7 | 340.9 | .20 | .75 | 0 |
| QSG-env8 | 417.6 | 413.6 | 408.1 | 409.3 | 427.6 | 391.4 | 0 | .30 | 0 |
| xu_acquisition_only | 379.5 | 403.9 | 423.9 | 388.0 | 380.1 | 374.9 | .10 | .50 | 0 |
| gated_adaptive_range+front | 380.9 | 377.9 | 397.2 | 362.4 | 346.3 | 344.6 | .10 | .55 | 0 |
| SMCS+retain-incumbent | 383.9 | 388.7 | 404.2 | 367.4 | 358.2 | 366.9 | .05 | .45 | .10 |
| discern_design_floor | 413.7 | 417.2 | 416.2 | 413.4 | 390.2 | 390.8 | 0 | .25 | 0 |
| CONTROL_never_switch | 426.8 | 422.9 | 414.0 | 430.8 | 424.1 | 419.7 | 0 | 0 | 0 |

On 20 seeds, no certified published comparator *run in this screen* stays at 0 on the rho=.95 null (best: .25).
**Correction (lead, after the milestone 1-2 review, O5):** discern_style (corrected DISCERN) was not in
this screen. In other dev screens it holds 0/20 on both Markov nulls because it almost never promotes,
so the earlier unqualified wording was false. Each
point estimate is a screening diagnostic only.

Paired contrasts against the best certified published comparator, chosen per regime (95% t-CI):
A5b F0_better -5.7 [-20.2, +8.8], F6 -1.0 [-6.0, +3.9], S_delay800 +0.5 [-3.5, +4.4], bursty
+22.4 [+8.1, +36.7], F5_dep_better_r8 +84.1 [+67.9, +100.4]. A1b F0_better -3.6 [-18.6, +11.4].

## 300-seed null check (base 2026110511; empirical frequency, Wilson 95% upper bound)

| policy | F5_dep_null_r8 | F5_dep_null_r95 | F0_null |
|---|---|---|---|
| A1 | 0/300 (≤.013) | 1/300 (≤.019) | 1/300 (≤.019) |
| A1b | 0/300 (≤.013) | 0/300 (≤.013) | 2/300 (≤.024) |
| A5b | 0/300 (≤.013) | 0/300 (≤.013) | 3/300 (≤.029) |
| A6b | 0/300 (≤.013) | 0/300 (≤.013) | 3/300 (≤.029) |
| QSG | 78/300 (.26) | 195/300 (.65) | 6/300 (.02) |

All four SUI variants sit well below .0936. This is empirical frequency on the declared
model. The mathematical guarantee is the SUI argument below, and it holds only inside the
declared class.

## Ablations (20 dev seeds)

* A1-nogap: same SUI with a constant transition (gap ignored) has null promotion **.40 (r8) and
  .60 (r95)**, so the gap indexing is what makes A1 valid.
* A1-rho8 (declared rho <= .8) has null r95 promotion 1.00. A declared bound fails as soon as it is
  violated, and it buys no iid power (F0_better identical to A1).
* A1-nostart: F0_better +1.9, F6 -1.2. Starts matter little here, and A1 and A1-nostart both fail
  F1_late_800.
* A2-fixedgap6 vs A2: F0_better +19.7, bursty +50.8. Adaptive density beats fixed thinning, but
  neither is safe with iid evidence.
* A5-fixedgap6 vs A5: F0_better +25.9.
* A3-noinflight vs A3, and A6-noinflight vs A6: within ±2.5 everywhere. The dual-clock mechanism
  has no material effect.

## Diagnostics behind the negative parts

For SUI evidence after 100 queried outcomes (10 synthetic sequences, scratch probe), with the
oracle alternative likelihood minus the iid p=.5 likelihood as the benchmark:
* iid p=.65 alternative: oracle 4.4 nats. The free-rho null absorbs .4, the cell upper bound adds
  .6-1.6 depending on grid resolution (301 rho x 121 p cells used), and the numerator mixture costs 1.6.
* p=.65, rho=.8 alternative: oracle 20.5 nats, of which the free-rho null absorbs 18.5. A rho-free
  test is information-limited here, so the dependent-alternative loss reflects that limit and is
  not a tuning defect. Methods that "win" there (QSG, gated+front, xu) are the same methods that
  falsely promote on the rho=.95 null.

## Certified profile-bound development pilot (2026-11-04)

Tested whether adaptive interval branch-and-bound could tighten the null denominator by optimizing
the joint sequence likelihood over p in [0,.5], rho in [0,1], while retaining a certified upper
bound. The implementation is an isolated diagnostic (`scripts/sota_sprint/profile_bound_dev.py`);
it is not used by A5b. Nine synthetic sequences (120 observations each; p=.65; rho in {0,.5,.8};
three seeds per rho; base 2026110701) were screened. The search stopped at its 20,000-box cap on
every sequence with tolerance .02 nats. For example, at rho=0 / seed 0, the current grid bound was
-80.58 nats, while the branch-and-bound upper bound remained -34.66 and its attained lower bound
was -83.18. Thus this implementation is far too loose at the capped budget; no policy comparison
or SOTA claim follows. **Do not integrate this version.** A faster certified likelihood optimizer
would be required to revisit denominator tightening.

## Validity argument (A1/A5/A6)

Filtration F_k: queried outcomes z_1..z_k in issue order with their issue events, the disagreement
indicators, and private randomness. The issue time of query k+1 depends only on released labels
(a subset of F_k), disagreement indicators and private randomness, so it is predictable, and the
sign at that event is not read before issue. Declared null H+: the sign is a stationary two-state
Markov chain in event time with P(s=1) = p <= 1/2, any persistence rho in [0,1], independent of
disagreements. Then P(z_{k+1}=1 | F_k) = a z_k + (1-a)p with a = rho^{g_{k+1}}. For each start j,
U_{j,k} >= sup over H+ of L(z_j..z_k | z_{j-1}, gaps). This holds because each factor's cell maximum
is at a monotone corner, the product of the per-factor maxima bounds the cell sup, and the max over
cells covers [0,1/2]x[0,1] (unit-tested against exact likelihoods on a coarse grid). So
Q_{j,k}/U_{j,k} <= Q_{j,k}/L_theta(j..k), a mean-one nonnegative martingale from j under the true
theta. The started mixture plus the tail weight of unstarted terms is a test supermartingale, so
by Ville the promote test crosses 2^c/alpha with probability <= alpha/2^c in cycle c. Summed
over cycles, P(any false promotion) <= alpha for every member of H+ simultaneously. No rho bound
is declared.

Limits:
* The guarantee needs a stationary first-order Markov sign process independent of disagreements.
  QSG's iid H+ covers time-varying p_t <= 1/2; A1's class does not. Higher-order or
  nonstationary dependence is not covered.
* The constant delay makes release order equal issue order. Out-of-order release is not handled.
* Rollback tests (alpha_r) are not safety claims.

## Continue / pivot / stop

* **Continue A5b (with A1b as its density-off control) to 100-seed validation.** It is the only
  family-A line that is valid at rho=.8 and .95 and not slower than the best certified published
  method on stationary alternatives. Its advantage there is small and not significant on 20 seeds
  (-5.7, CI includes 0), it loses on bursty (+22), and it cannot detect dependent alternatives.
  The success criterion from the Atlas audit (CI < 0 on >= 4/6 stationary alternatives) looks
  unlikely to be met. The plausible claim is "matches the best certified cost while being the only
  one valid at rho=.95", and validation should test exactly that.
* Stop A2, A3, A4 and A6 as separate candidates.
