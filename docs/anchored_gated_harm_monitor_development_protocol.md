# Anchored, disagreement-gated decision-harm monitor: development protocol

**Status:** draft development protocol, 2026-10-27. **G0 passed** (narrowly; see the
[novelty audit](../papers/shiftguard_unified/novelty_audit.md)). **G1 failed and stop rule S2
fired:** see [G1 results](adg_growth_prescreen_results.md). No monitor has been run under this
protocol. G2–G7 are not authorised unless a new protocol is approved.
This document defines the goal, the derivations, the comparators, the synthetic and real-data
designs, the stage gates, and the stopping rules for one narrow Paper 1 algorithm attempt. Freeze
it (commit hash and date in the header) before any monitor is run on the seed blocks or data
windows named below. Nothing here is a validity, novelty, or performance result.

## 1. Goal and finish line

**Correction (2026-10-27, after G1).** The 6/60 figure below is the common-bound result. The
[propensity-floor diagnostic](propensity_floor_diagnostic_results.md) had already shown that
uniform querying with its valid policy-specific bound (45.9) crosses in 47/60. So the power loss is
smaller than this paragraph implies. G1 used the 45.9 bound for A1, and its conclusion is
unaffected.

**Problem.** Under selective labels, the repository's paired decision-harm monitors lose most of their
power. In the 20%-budget diagnostic ([`monitor_signal_diagnostic_results.md`](monitor_signal_diagnostic_results.md)),
full feedback crossed in 60/60 boundary-harm streams, but PPI monitoring crossed in only 6/60
(uniform) and 4/60 (evidence curve). Two documented causes:

1. **Bet-size clipping.** The fixed bound `B = M(2/q_min - 1) = 96.9` (`M = max(fn,fp) + epsilon =
   5.1`, `q_min = 0.10`) limits the effective betting fraction to `lambda = s/B <= 0.8/96.9 ≈ 0.0083`.
   Realised increments use 0.58% of `B`. The bound is symmetric, but a one-sided test only needs a
   lower bound ([`experiment.py:296-300`](../src/shiftlab/dive/experiment.py)).
2. **Acquisition noise.** About 96–98% of the PPI increment variance comes from Bernoulli query
   randomness. The ridge proxy ([`proxy.py`](../src/shiftlab/dive/proxy.py)) does not use the fact
   that the paired cost is exactly zero when the deployed and reference actions agree. Queries and
   proxy residuals are therefore spent on events whose cost is already known.

**Candidate method (ADG).** An e-process for paired harm, built as follows:

- **(i) Disagreement gating.** Agreement events contribute their known value; labels are spent only
  on disagreements.
- **(ii) One-sided bound with an anchor at the lower support.** The PPI anchor sits at the lower
  edge of the conditional support, so the inverse-propensity correction is never negative and the
  stake bound does not depend on `q`.
- **(iii) Mixture over anchors.** A fixed convex mixture over the anchor weights `gamma` trades the
  `q`-free bound against acquisition variance.
- **(iv) Horizon-calibrated start mixture.** Equivalently, a Shiryaev–Roberts e-detector at
  threshold `T/alpha`, for late onset.
- **(v) Contiguous-prefix release.** Used for delayed labels.

Each ingredient has prior art (Section 2). The question is whether the composition, under the
charter's history-conditional null with covariate-adaptive querying, drift, and delays, gives a
reproducible, matched-budget gain over the strongest existing constructions.

**Finish line (algorithm claim earned).** All of the following must hold:

1. **G0.** The prior-work check leaves a construction or theorem not already published.
2. **T1, T2, T4.** Written, independently checked proofs.
3. **G4.** Fresh null calibration passes.
4. **G5.** Fresh synthetic confirmation shows a positive lower 95% bound for the paired detection
   gain against the strongest matched comparator from G3, with labels no higher.
5. **G6.** On at least two real sources:
   - the random-orientation null holds;
   - injected-harm detection beats the DISCERN-style gated comparator at equal or fewer labels.
6. **G7.** The prospective EIA holdout reproduces the label saving without violating the null.

**Stopping point.** Stop as soon as any stop rule in Section 7 fires. Record the result in the Paper 1
research log as a negative or component result, and fold it into the benchmark/failure-analysis
manuscript. Do not convert a stopped branch into a novelty claim.

## 2. Prior-work check (primary sources, 2026-10-27; targeted, not exhaustive)

| Work | What it already establishes | Consequence for ADG |
|---|---|---|
| Xu, Karampatziakis & Mineiro, [*Active, anytime-valid risk controlling prediction sets*](https://arxiv.org/abs/2406.10490), NeurIPS 2024 | Betting e-process `prod(1 + lambda_i(theta - rhat_i - (L_i/q_i)(R_i - rhat_i)))` with a predictable label policy and a predictor. Stake range `lambda in [0, (1/q_min - theta)^(-1)]` depends on `q_min`. Optimal budgeted policy `q*(x) ∝ sqrt(E[(R - rhat)^2 \| x])`. | **Closest construction.** Active labelling, PPI-style predictors, and variance-optimal `q` are not new. Their stake bound holds uniformly over predictors in `[0,1]`; it does not use the anchor to remove `q_min`. They study a single model's risk, not a paired policy contrast; drift and delay are not covered. Required comparator family. |
| Waudby-Smith, Wu, Ramdas, Karampatziakis & Mineiro, [*Anytime-valid off-policy inference for contextual bandits*](https://arxiv.org/abs/2210.10768), ACM/IMS JDS 2024 | The importance-weighted lower confidence sequence allows `lambda in [0, 1/nu')`, independent of the maximum weight, because IW pseudo-outcomes are nonnegative. The DR version needs truncation `k_t` and `lambda in [0, (nu' + k_t)^(-1))`. | **The one-sided, weight-free stake principle is known.** ADG's ingredient (ii) transfers it to a signed paired contrast by choosing the PPI anchor at the conditional lower support. Any claim must be limited to this transfer, the anchor/variance trade-off (T2–T3), and the composition. |
| Balachandran, [*Pay Only for Disagreement* (DISCERN)](https://arxiv.org/abs/2609.17560), arXiv v1, July 2026 | For model-update audits: paired loss lives only on disagreements. A Horvitz–Thompson increment `A_t (L_t/pi_t) D_t` in `[-B/pi_min, B/pi_min]` feeds an empirical-Bernstein CS. Label complexity is of order `rho^2/eps^2`. Includes a zero-label tier. Assumes i.i.d. data; the unrestarted CS miscovered under synthetic drift, with a windowed restart as a mitigation. Delayed labels are not covered. | **Disagreement gating is not new** (and discordant-pair adjudication is classical, e.g. McNemar). DISCERN-style gating is a required comparator, not an ADG contribution. Its symmetric `B/pi_min` range is exactly the clipping that ingredient (ii) targets. Appendix A (exact CS form) was not read; read it before G0 closes. |
| Csillag, Struchiner & Goedert, [*Prediction-Powered E-Values*](https://proceedings.mlr.press/v267/csillag25a.html), ICML 2025 | Corrected factor `e(mu) + (I/pi)(e(Y) - e(mu))`, with positivity `pi >= 1 - a/b` for factors in `[a,b]`. Change detection via Shekhar & Ramdas. | The visible text does not note that a proxy at the lower end `a` makes the corrected factor `>= a > 0` for every `pi > 0` (the factor-scale version of T2). Verify against the full paper and supplement before G0 closes. **Author correction:** the repository's [PPE audit](../papers/shiftguard_unified/ppe_paper_implementation_audit.md) previously listed "Csillag, Zrnic, and Ramdas"; PMLR lists the authors above. |
| Timans et al., [UAI 2025](https://proceedings.mlr.press/v286/timans25a.html) | Time-uniform monitoring of a bounded eventwise conditional risk under unknown shift (GRAPA). The repository confirmed the null mapping and found no detection advantage for its own monitor under full feedback. | Primary Q1 comparator: full-feedback upper reference, plus an HT-increment adaptation under selective labels. |
| Shin, Ramdas & Rinaldo, [*E-detectors*](https://arxiv.org/abs/2203.03532), NEJSDS 2023; Shekhar & Ramdas (2023), sequential change detection via confidence sequences | SR- and CUSUM-type e-detectors built from sums of e-processes started at each time. Guarantees are ARL-type. Software: R package `edetect`. | **Required late-onset baseline.** None is implemented in `src/` (checked 2026-10-27). T4 converts SR to the charter's finite-horizon false-alarm probability. |
| Ashouritaklimi et al., [*Prediction-Powered Active Testing*](https://arxiv.org/abs/2607.08347), arXiv, July 2026 | Combines a LURE estimator with a prediction-powered control variate and variance-reducing acquisition. Asymptotic CIs; single-model risk. | Scope comparator only: fixed-sample, not anytime-valid, not paired. |

**G0 decision rule.** Close G0 only after reading in full: DISCERN Appendix A, PPE Section 3 and its
supplement, and Xu et al. Section 2–3. If any of them already uses a support-boundary anchor (or an
equivalent nonnegative-correction choice) for signed paired contrasts with a `q`-free stake, ADG
has no construction claim. Stop the algorithm branch (S1) and keep the arms as benchmark
comparators.

## 3. Setting and derivations

### 3.1 Filtration and estimand

Events `t = 1, ..., T`. The timeline for each event:

1. `F_{t-1}` holds the learner's history.
2. `X_t` is revealed.
3. Actions `a_t = pi_t(X_t)` and `b_t = pi_ref(X_t)` are formed; both policies are predictable.
4. The disagreement indicator `A_t = 1[a_t != b_t]` and the query propensity `q_t = q(F_{t-1}, X_t)`
   are formed.
5. The query coin `Q_t ~ Bern(q_t)` is drawn.
6. If `Q_t = 1`, the label `Y_t` is revealed at its availability time.

Cost is `c(a, y) in [0, C]`, with the cost matrix known. Paired cost:
`Z_t = c(a_t, Y_t) - c(b_t, Y_t)`. Null (the charter's history-conditional null):

    H0: E[Z_t | F_{t-1}] <= epsilon   for every monitored t.

**Assumption L (label-only loss).** `A_t = 0` implies `Z_t = 0`. This holds for every fixed-action
cost `c(a, y)`. It fails if cost depends on scores rather than actions.

**Conditional support.** With the cost matrix known and `(a_t, b_t)` given, compute before the
outcome:

    l_t = min_y [c(a_t,y) - c(b_t,y)]
    u_t = max_y [c(a_t,y) - c(b_t,y)]
    L   = max over action pairs of (-l)   (a known constant)

For the DIVE binary task (`fn = 5`, `fp = 1`):
- deployed 1 / reference 0: `Z in {+1, -5}`, so `l = -5`, `u = +1`;
- deployed 0 / reference 1: `Z in {+5, -1}`, so `l = -1`, `u = +5`.

So `L = 5` and the range is `W = u - l = fn + fp = 6`.

### 3.2 Gated, anchored increment

Let `g_t` be a predictable proxy for `E[Z_t | F_{t-1}, X_t]`, clipped to `[l_t, u_t]`. For an anchor
weight `gamma in [0,1]`, define the anchor and the increment:

    h_t(gamma)   = l_t + gamma (g_t - l_t)
    Hhat_t(gamma) = A_t [ h_t(gamma) + (Q_t / q_t) (Z_t - h_t(gamma)) ] - epsilon

Queries are drawn only when `A_t = 1`. On agreements, `Hhat_t = -epsilon` exactly and no label is
spent.

**Lemma 1 (unbiasedness; elementary).**
`E[Hhat_t(gamma) | F_{t-1}, X_t] = E[Z_t | F_{t-1}, X_t] - epsilon`. This uses Assumption L and the
fact that `q_t, h_t` are fixed before the coin and the outcome. Taking the expectation over `X_t`
gives `E[Hhat_t | F_{t-1}] <= 0` under H0.

**Lemma 2 (lower bound; derived here, to be checked: T2).** When queried,

    Hhat_t = l_t + (h_t - l_t)(1 - 1/q_t) + (Z_t - l_t)/q_t - epsilon
          >= l_t - gamma W (1/q_t - 1) - epsilon.

Therefore:

    Hhat_t(gamma) >= -B_gamma,   B_gamma = L + gamma W (1/q_min^D - 1) + epsilon,

where `q_min^D` is the registered floor on disagreement events only. In particular,
`B_0 = L + epsilon`, which does not depend on `q`. More generally, a lower bound free of `q` holds
for a pre-outcome anchor if and only if `h_t <= l_t` almost surely, and `h_t = l_t` is the largest
such anchor.

`B_gamma` is a registered constant. It must not depend on `X_t`; the
[marginal-null bound audit](marginal_null_predictable_bound_audit.md) shows that normalising by a
current-covariate bound is invalid under this null.

**Proposition 1 (validity; T1).** For a fixed stake `s in (0, 1]` and fixed `gamma`, define

    M_t(gamma, s) = prod_{i <= t} (1 + s Hhat_i(gamma) / B_gamma).

`M_t` is a nonnegative supermartingale under H0, because each factor is `>= 1 - s >= 0` and has
conditional mean `<= 1`. Any fixed convex mixture over `(gamma, s)` and over start times (3.4) is
also a nonnegative supermartingale, so Ville gives `P(sup_t M_t >= 1/alpha) <= alpha`. This
requires predictability of `pi_t`, `pi_ref`, `g_t`, `q_t`, and the cost matrix, plus Assumption L.
It does **not** require i.i.d. data, a context-conditional null, or bounded inverse weights.
Unbounded upside is allowed.

**Comparison with the current construction.** The current monitor uses
`|Hhat| <= M(2/q_min - 1)`, about `19 M` at `q_min = 0.10`. Even with a one-sided bound, `gamma = 1`
keeps a bound of order `W/q_min`. Only boundary anchoring removes the dependence on `q`.

### 3.3 Variance cost of anchoring and analytic pre-screen (T3)

For binary costs, write `Z_t = l_t + W·D_t`, where `D_t ~ Bern(p_t)` and `p_t` is the conditional
probability of the outcome unfavourable to the deployed action. The acquisition variance on a
disagreement event is:

- with `gamma = 0`: `(1 - q)/q · W^2 · p_t`;
- with a perfect proxy (`gamma = 1`, `g = E[Z | X]`): `(1 - q)/q · W^2 · p_t (1 - p_t)`.

So the ratio is `1/(1 - p_t)` (derived here). Near the cost-weighted boundary
(`P(Y = 1) ≈ fp/(fn + fp) = 1/6`):

- deployed 0 / reference 1: unfavourable outcome is `Y = 1`, so `p ≈ 1/6` and the ratio is about 1.2;
- deployed 1 / reference 0: unfavourable outcome is `Y = 0`, so `p ≈ 5/6` and the ratio is about 6.

Anchoring therefore helps or hurts depending on the orientation of the harm. That is why ADG mixes
over `gamma` instead of fixing `gamma = 0`.

**Growth-rate criterion.** With small-stake log-growth `G(lambda) ≈ lambda·mu - lambda^2·V/2`,
where `mu = E[Hhat]` under the alternative and `V = E[Hhat^2]`, and the stake cap `lambda <= 0.8/B`:

    G* = mu^2 / (2V)                              if mu/V <= 0.8/B
    G* = 0.8 mu/B - 0.32 V/B^2                    otherwise.

Worked illustration, using the diagnostic's same-seed means (descriptive only): `mu ≈ 0.178`,
`V_1 ≈ 7.66`, `B = 96.9`.
- The current arm is capped: `G ≈ 0.00121`.
- Boundary anchoring has `B_0 = 5.1`, so it is uncapped: `G ≈ 0.00207 / r`, where `r = V_0/V_1`.
- Anchoring helps only if `r < ≈1.7`.

Gating raises `q` on disagreements (`q_D ≈ budget / rho`, where `rho` is the disagreement rate).
This shrinks every `(1 - q)/q` term and is expected to dominate. Its share of any gain must be
attributed to DISCERN, not to ADG.

### 3.4 Late onset: horizon-calibrated Shiryaev–Roberts (T4; derived here)

Let `f_i >= 0` with `E[f_i | F_{i-1}] <= 1` under H0 (an ADG factor).
- The SR statistic is `R_t = f_t (1 + R_{t-1})`. Define `S_t = R_t + (T - t)`.
- Then `E[S_t | F_{t-1}] <= S_{t-1}` and `S_0 = T`, so by Ville
  `P(max_{t <= T} R_t >= c) <= T/c`.
- With `c = T/alpha`, the SR e-detector controls the charter's finite-horizon probability of any
  false escalation at `alpha`. CUSUM (`max_j prod_{i=j}^{t} f_i <= R_t`) at the same threshold is
  also valid.
- The repository's [`StartedMixtureEProcess`](../src/shiftlab/dive/eprocess.py) counts unstarted
  components as 1. With uniform weights on all `T` starts it equals `S_t/T`, so it alarms no later
  than SR at `T/alpha`.

The existing 4- and 8-start mixtures are coarse versions of this detector. The all-start version
costs `O(T)` per event. Registered approximation: a geometric grid of starts, with weights summing
to 1.

### 3.5 Delays (T5; existing theory)

Labels update the process in event order, via the largest contiguous resolved prefix
([`delayed_event_prefix_validity.md`](delayed_event_prefix_validity.md)). An arrival-time alarm is a
crossing of the event-time process, so Proposition 1 carries over under arbitrary delays, provided
events eventually resolve with correct identity. `q_t`, `g_t`, and the anchor may use only labels
already released into that prefix.

### 3.6 Real-data null by random orientation (T6; derived here)

On a real path, draw `S_t in {-1, +1}` uniformly, independent of everything else. The monitor then
sees the swapped pair: the deployed and reference roles exchange when `S_t = -1`, and `l_t, u_t`
are recomputed. So `Z'_t = S_t Z_t`.
- Conditional on the entire realised data path, the only randomness is in the `S` and `Q` coins,
  and `E[S_t Z_t | path, past coins] = 0`.
- Lemma 1 holds given `(X_t, S_t)`, and Lemma 2's bound is unchanged.
- Therefore `P(alarm | path) <= alpha` **exactly, for each real path**.

Replicating over coin seeds on a fixed real stream is a valid per-path check of false escalation
under real covariate, outcome, and dependence structure. It is not a statement about the real
policies' harm.

## 4. Arms, matched information, and endpoints

All selective-label arms share, within each seed or path: the event stream, the query uniforms, the
hard label cap, the proxy training data, and `alpha = 0.05`. Gated arms set `q = 0` on agreements
and spend the same expected budget on disagreements (`q_D = clip(budget / rho_hat, q_min^D, 1)`).
`rho_hat` is estimated on the source/validation slice only.

| Arm | Construction | Role |
|---|---|---|
| A0 `full_feedback` | Bounded-mean mixture on true `Z - epsilon` | Upper reference; not matched |
| A1 `ppi_symmetric` | Current fixed-mixture PPI, `B = M(2/q_min - 1)` | Repository baseline |
| A2 `ppe_fixed_stake` | Existing PPE transfer | Published comparator |
| A3 `discern_gated_eb` | Gated HT (`h = 0`), range `B/pi_min`, predictable plug-in empirical Bernstein | DISCERN-style adaptation (no official code) |
| A4 `xu_active_optimal_q` | Xu et al. factor with `q* ∝ sqrt(residual second moment)`, `q_min`-dependent stake | Published comparator |
| A5 `timans_grapa_ht` | Official `approx_grapa` on HT increments mapped to `[0,1]` with the symmetric range; also on full feedback | Adapted / upper reference |
| A6 `sr_edetector_symmetric` | Horizon-calibrated SR (geometric starts) on A1 increments | E-detector baseline |
| A7 `adg_gamma0` | Gated, `gamma = 0`, fixed mixture over stakes | Ablation |
| A8 `adg_gamma_mix` | Gated, fixed equal mixture over `gamma in {0, 0.25, 0.5, 1}` and stakes | **Primary candidate** |
| A9 `adg_gamma_mix_sr` | A8 inside horizon-calibrated SR starts | **Late-onset candidate** |
| A10 `ungated_gamma0` | Ungated boundary anchor | Ablation separating (i) from (ii) |

A8 is primary for the overall gain and A9 for late onset. Both are named now, before any run.

**Primary endpoint (synthetic).** Post-onset detection by horizon `T` in the boundary-local harm
scenario, at the matched hard label cap. Pre-onset alarms count as non-detections.

**Secondary endpoints.**
- macro detection over the three harmful scenarios, and by onset (25/50/75%);
- censored detection delay;
- labels consumed;
- excess decision loss before alarm;
- false escalation in null cells;
- realised `rho`, `q_D`, and per-arm `B`.

**Inferential unit.** Seed cluster. Use paired bootstrap intervals and a one-sided exact McNemar
test for the primary contrast at confirmation.

## 5. Designs

### 5.1 Synthetic (DIVE simulator, immediate and delayed feedback)

- **Simulator.** Reuse `run_dive_experiment` scenarios: stationary, benign nuisance, boundary-local
  harm, recurring regimes, harmful adaptation. Settings: `n = 3200`, `d = 16`, `epsilon = 0.10`,
  `fn = 5`, `fp = 1`, budget 20%, `q_min^D = 0.10`, `q_max = 1`.
- **Delayed cell.** Independent uniform delays 0–12 with contiguous-prefix release.
- **Seed blocks.** The draft's 57M blocks were replaced on 2026-10-27 because `57_100_000` is
  already used by `scripts/run_started_mixture_horizon_grid.py`. No 58M offset appears in
  `scripts/`, `src/`, `configs/`, `docs/`, or `papers/`.
  - design pre-screen: `58000000–58000019` (source/validation slices only);
  - development: `58100000–58100059`;
  - null calibration: `58200000–58201999` per null cell;
  - confirmation: `58300000–58300999`.
- **Generator.** Use the hard-budget generator (`shiftlab.dive.hard_budget`), matching the
  diagnostic that motivated this protocol. Label budgets are label-dollar rates under its
  covariate tariff.

### 5.2 Real data (development, then prospective)

The design uses fully labelled real streams where one outcome scores both fixed policies (full
information). Label scarcity is imposed by our own known query randomisation. This makes
propensities exact and puts the true full-feedback path on the evaluator side. Costs are
**imposed research costs**, stated as such, with sensitivity at registered alternatives. Every
real-data result is retrospective and exploratory except R1-P.

- **R1 EIA hourly demand, CISO and ERCO (primary real source).**
  - Event: forecast hour. Features: the four contemporaneous EBA series, as in the
    [2026 replay](../papers/shiftguard_unified/eia_2026_out_of_time_confirmation_results.md).
  - Decision: procure reserve if forecast demand exceeds `tau`, the 2019–2024 90th percentile per
    authority.
  - Costs: shortfall `c_s = 5`, over-procurement `c_o = 1` (sensitivity `c_s in {2, 10}`).
  - Deployed policy: frozen Ridge fitted on 2019–2024. Reference: the weekly-refit Ridge from the
    existing protocol. Secondary reference: EIA day-ahead `DF` series, with its availability time
    assumed.
  - Assumptions: demand does not depend on our action. Label delays are assumed at 0, 24, and
    168 hours.
  - Windows: 2025 and 2026-01-01 → 2026-10-19 are **previously examined** (forecasting replays)
    and are development data only.
  - The earlier replay found a large frozen-versus-refit RMSE gap in CISO and a negligible one in
    ERCO. This gives a natural contrast, but it is not ground truth for decision harm.
- **R1-P EIA prospective holdout.**
  - Data: hours published after the protocol freeze timestamp. Acquire once, after at least 6
    weeks (about 1,000 hours per authority), via the per-series API (small) or one bulk snapshot.
  - Code, model, threshold, costs, and arms are frozen by hash beforehand.
  - This is the only source in the plan that is untouched by construction.
- **R2 UCI Gas Sensor drift.**
  - Policies: incumbent fitted on batches 1–3; reference = the batch-1–5 refit from the
    [candidate protocol](../papers/shiftguard_unified/gas_sensor_candidate_protocol.md).
  - Stream: batches 6–10 in source order, with a registered random permutation within each batch.
  - Costs: the three existing multiclass cost matrices.
  - Selective labels are plausible here, because confirming the gas identity costs lab effort.
    Batches have been seen before, so this is development only.
- **R3 CRSP date-level stream (robustness only).**
  - Event: trading date. `Z_t` is the cross-sectional mean paired cost of the
    [pilot policies](../papers/shiftguard_unified/crsp_decision_policy_pilot_results.md).
  - Aggregating to dates respects the cross-sectional dependence.
  - Label cost is artificial and the test period is exposed. Use R3 only for the
    random-orientation null and heavy-tailed robustness. Respect the
    [CRSP execution guide](crsp_study_execution.md).

**Real-data analyses per source.**
- **(a) Random-orientation null (3.6).** 1,000 coin replicates per path. Exact one-sided upper 95%
  bound on the per-path false-alarm rate.
- **(b) Unmodified stream.** 200 query-seed replicates. Per arm: alarm probability, labels at
  alarm, and agreement with the full-feedback A0 verdict (A0 is deterministic per path).
- **(c) Injected harm with known onset** at 25/50/75% of the window:
  - after onset, the deployed action is replaced on events whose frozen-model margin lies in a
    registered band;
  - R1 uses under-procurement; R2 uses a flip to the second-best class;
  - the band is chosen from pre-window data to give about 10% of events;
  - the injected rule is evaluator-only;
  - the realised post-onset paired mean is reported, because real labels decide its size.

## 6. Stage gates (go criteria)

| Gate | Work | Go if |
|---|---|---|
| **G0** prior work | Full reads listed in Section 2 | No published `q`-free, boundary-anchored paired construction. Note the DISCERN/Xu overlap in the related-work table either way. |
| **G1** analytic pre-screen (no monitor runs) | Specification in Section 6.1 | Predicted `G*`(A8) ≥ 1.5 × max(`G*`(A1), `G*`(A3)) in boundary harm at the 20% budget. |
| **G2** implementation | Unit tests (Section 8). Ruff, mypy, full pytest. | All pass. Lower bound never violated in 10^6 randomized checks. Lemma 1 identity holds exactly on enumerated cases. |
| **G3** synthetic development | 60 seeds × 5 scenarios × 11 arms, immediate and delayed | A8 ≥ best of A1–A6 by **+10 pp** in boundary-harm detection. A8 not worse than **−3 pp** in any other harmful scenario. Labels ≤ the comparator's. Zero pre-onset null crossings in the cells (descriptive). A9 is retained only if it adds ≥ +5 pp at 75% onset over A8. |
| **G4** null calibration | 2,000 streams per null cell (stationary, benign nuisance; immediate and delayed) | Simultaneous exact one-sided upper 95% bound ≤ 5% for A8 (and A9 if retained). |
| **G5** synthetic confirmation | 1,000 fresh paired seeds; A8 versus the strongest G3 comparator | Paired gain lower 95% bound > 0, McNemar `p < 0.05`, labels ≤ comparator. |
| **G6** real development | R1, R2, R3 analyses (a)–(c) | (a) Per-path upper bound ≤ 5% on every path. (c) A8 detection ≥ A3 (DISCERN-style) + 10 pp, averaged over onsets, on ≥ 2 sources, at equal or fewer labels. |
| **G7** prospective EIA | R1-P with all arms frozen | (a) Null holds. (c) The injected-harm gain over A3 has the same sign and a lower 95% bound > 0 across replicates. (b) A8's verdict agrees with A0 in ≥ 90% of replicates. |

### 6.1 G1 specification (registered 2026-10-27, before any pre-screen output existed)

**Data and learner-side quantities.**
- Seeds `58000000–58000019`. Scenarios: `boundary_local_harm` (primary) and `stationary`
  (sensitivity). Hard-budget generator, `n = 3200`.
- Only the train slice (events 0–399) and the validation slice (events 400–799) are used. No
  monitor-window event, oracle probability, or evaluator field enters the calculation.
- From the train slice: the logistic classifier `phat`, and the repository ridge proxy (fitted on
  train, with its residual model on validation, exactly as in the generator).
- On each validation event: actions, disagreement, `(l, u)`, the unfavourable-outcome probability
  `pi_bad` from `phat`, and the label tariff.

**Working alternative.** On disagreement events, set
`pi_bad' = pi_bad + eta (1 - pi_bad)`, with `eta` solved so that the validation-slice mean of
`E'[Z] - epsilon` equals `mu`.
- Primary `mu = 0.277`: the diagnostic's post-onset boundary-harm mean excess.
- Sensitivity: `mu in {0.10, 0.178}`.
- A seed and `mu` pair with `eta > 1` is infeasible: report it and exclude it.
- The null growth (`eta = 0`) must be nonpositive for every arm. *(Corrected after the run:
  `eta = 0` is the natural working law, not a null. The valid check is nonpositive growth wherever
  its mean excess is nonpositive; see the results.)*

**Arms, at matched expected label-dollar spend `r · mean(tariff)`.**
- **A1** `ppi_symmetric`: uniform `q = r`, ridge anchor, `B = M(2/r - 1)`. Also reported at the
  diagnostic's `B = 96.9`.
- **A2** `ppe_fixed_stake`: equivalent to A1 at stake 0.9 (`lambda = 0.1`).
- **A3** `discern_gated`: gated, `h = 0`, `q_D = min(1, r·mean(tariff)/mean(A·tariff))`,
  symmetric `B = 5/q_D + epsilon`.
- **A4** `xu_active`: ridge anchor, `q ∝ sqrt(residual second moment)` clipped to `[r/2, 1]` and
  spend-matched, `B = M(2/(r/2) - 1)`.
- **gated_ppi_symmetric**: gated, ridge anchor, `B = M(2/q_D - 1)`.
- **A7**: gated, `gamma = 0`, `B_0 = L + epsilon`.
- **A8**: gated, `gamma in {0, 0.25, 0.5, 1}`, action-aware anchor `g = l + W pi_bad` (pre-tilt).
- **A10**: ungated, `gamma = 0`, `q = r`.

**Growth computation.**
- `G*` for each arm is the exact expectation of `log(1 + s Hhat / B)` over the outcome and query
  coins, averaged over validation events and maximised over the registered stakes
  `{0.05, 0.1, 0.2, 0.4, 0.8}`, and over `gamma` for A8.
- A fixed mixture's asymptotic growth equals its best component's.
- Criterion: on the 20-seed means at `r = 0.20`, `mu = 0.277`.

**Secondary budget cells** (descriptive, not a gate): `r in {0.02, 0.04, 0.06, 0.10}`.

**Pre-run analytic note.** The two policies disagree only where `x0 - 0.9 x1 in [-0.29, 0)`. Under
standard normal features, that is about 8.5% of events, all with deployed 0 and reference 1
(`Z in {+5, -1}`). At `r = 0.20` the gated arms are expected to reach `q_D = 1`, which makes the
anchor irrelevant (A3 = A7 = A8). If so, the primary criterion fails and any predicted gain
belongs to gating (DISCERN), which triggers S2 for the 20%-budget design. The lower-budget cells
show whether the anchor matters when `q_D < 1`. Continuing in that regime would require an amended
protocol approved by the user before any G3 run.

The G3 thresholds are development screens. The confirmatory claim rests only on G4, G5, and G7.

## 7. Stopping rules

- **S1 (prior art).** G0 finds the construction published. Stop algorithm work. Keep A7, A8, and A9
  as benchmark arms.
- **S2 (analytic).** G1 is not met. Stop before any simulation. Record the growth calculation as a
  negative result. If gating alone explains the predicted gain, the result belongs to DISCERN.
- **S3 (development).** G3 fails. Stop, and do not tune `gamma` grids, stakes, or bands on the
  development seeds. One pre-registered revision is allowed only if a G2 bug is found.
- **S4 (validity).** G4 or G6(a) fails. This means an implementation or assumption error. Fix and
  re-register once. A second failure stops the branch.
- **S5 (confirmation).** G5 fails. Stop. Report the confirmed negative or tied result.
- **S6 (external).** G6(c) or G7 fails. Restrict any claim to synthetic and record the failure. Per
  the charter, this is not sufficient for an algorithm paper: narrow the claim to a benchmark
  component.
- **Gain from gating alone.** If A10 ≈ A1 and A3 ≈ A8 at any gate, the gain comes from gating
  (DISCERN), not from ADG. Stop.

## 8. Todos

**Prior work and theory**
- [ ] Read DISCERN Appendix A, PPE full text and supplement, and Xu et al. Sections 2–3. Close G0
      with a short note in `papers/shiftguard_unified/novelty_audit.md`.
- [ ] Write T1 (Proposition 1) and T2 (Lemma 2, including the "if and only if" statement) as full
      proofs in `papers/paper1_decision_drift/theory_notes.md`. Have them checked independently.
- [ ] T3: implement the growth-rate pre-screen (`analyze_adg_growth_prescreen.py`), using
      source/validation slices only.
- [ ] T4: add the SR finite-horizon lemma and its proof. Note the equivalence with
      `StartedMixtureEProcess`.
- [ ] T6: write the random-orientation null argument. State that it covers coin randomness given
      the path only.

**Code** (`src/shiftlab/dive/`)
- [ ] `anchored_monitor.py`:
  - `conditional_support(cost_matrix, a, b)`;
  - `anchored_gated_increment(...)`;
  - `OneSidedBoundedBelowEProcess(bound_below, stakes)`, which accepts unbounded upside and
    rejects `value < -bound_below`;
  - `AnchorMixtureEProcess(gammas, stakes)`, holding a fixed convex mixture of components with
    their own `B_gamma`.
- [ ] `e_detector.py`: `ShiryaevRobertsEDetector(factor_fn, horizon, alpha, starts="geometric")`
      and a CUSUM variant.
- [ ] Optional: cross-check the bounded-mean case numerically against R `edetect`.
- [ ] DISCERN-style A3 arm, reusing `PredictablePlugInEmpiricalBernsteinEProcess`. Document it as
      an adaptation.
- [ ] Xu et al. A4 arm, with the published stake range and `q*`.
- [ ] Wire arms A0–A10 into a new runner (`adg_development.py`). Leave `experiment.py` unchanged.
      Ensure matched query uniforms and a hard cap.

**Tests** (`tests/test_anchored_monitor.py`, `tests/test_e_detector.py`)
- [ ] Lemma 1 identity on enumerated `(a, b, y, q, g)`.
- [ ] Lemma 2 lower bound over randomized inputs, including `q -> 0`.
- [ ] Factor nonnegativity.
- [ ] Agreement events spend no label and return `-epsilon`.
- [ ] `B_gamma` does not read current covariates.
- [ ] Oracle fields cannot alter learner outputs.
- [ ] SR at `T/alpha`: Monte Carlo under an exact null, plus the deterministic identity
      `S_t/T == StartedMixture(all starts)`.

**Real-data adapters** (`src/shiftlab/data/real/` or `scripts/`)
- [ ] R1 EIA paired-decision stream builder from the verified snapshot. Frozen threshold, costs, and
      policies. Per-row availability flags; delays marked as assumptions.
- [ ] R2 Gas Sensor stream with a registered within-batch permutation seed.
- [ ] R3 CRSP date-level aggregator from the pilot policies (robustness only).
- [ ] Injected-harm module (evaluator-only rule) and random-orientation wrapper for all sources.
- [ ] R1-P: decide the acquisition route (EIA API key or bulk snapshot). Record the freeze
      timestamp. Schedule a single acquisition after ≥ 6 weeks.

**Execution and reporting**
- [ ] Freeze this protocol: commit hash in the header, seed-block disjointness check, code hashes.
- [ ] G1 → G2 → G3 → G4 → G5 → G6 → G7, stopping at the first failed gate. Write a
      `*_results.md` for every gate run, including failures.
- [ ] Log each gate outcome in `papers/paper1_decision_drift/research_log.md`, with commands, code
      and data hashes, and a continue/pivot/stop assessment.
- [ ] No figures are planned. If any are needed, generate them with PaperBanana from validated
      outputs and check them against the source values.

## 9. Limits stated in advance

- The guarantees are for the paired-cost null under predictable fixed policies, full-information
  outcomes, and Assumption L.
- They do not identify harm when actions change outcomes. Off-policy designs are out of scope.
- Real-data harm on unmodified streams has no ground truth.
- Imposed costs are research controls, not application utilities.
- EIA availability times and revisions are unknown; R1-P is prospective in publication order only.
- The ingredients are established. The only possible contributions are the boundary-anchor
  transfer with its variance analysis, the composition under drift and delay, and matched evidence
  for both.
