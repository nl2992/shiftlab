# Reduced exact dynamic program for budgeted, delayed, reversible switching (Workstream E3)

Written 2026-11-09. Code: `scripts/paper1_scale25/theory/` (`reduced_dp.py`, `hazard_dp.py`, `run_dp_experiments.py`, `run_hazard_dp.py`, `real_stack_mc.py`, `crosscheck_real_code.py`, `structure_analysis.py`). Outputs: `docs/paper1_scale25/theory/` (`dp_gaps.csv`, `hazard_dp_values*.csv`, `real_stack_mc*.csv`, `structure_tables.json`).

## 0. Status of every claim (read this first)

| kind | statements |
|---|---|
| **Proved (standard MDP theory, short argument given)** | the Bellman recursions of section 2 give the Bayes-optimal expected cost of the stylised model over all non-anticipative, possibly randomised, policies; the (k, n) and lagged-filter states are sufficient. |
| **Verified numerically (exactness of the implementation)** | recursion vs direct simulation of the optimal policy (z within 2.3 SE at 4,000 episodes, then 19.74 and 19.62 +- 0.08 vs 19.597 exact at 20,000); two independent DP implementations (the (k, n) solver and the belief-grid hazard solver at h=0) agree to 1e-5; the policy evaluator agrees with the repository's own `EQSD` class run in the repository simulator (4 instances, |z| <= 1.3); belief-grid refinement G=100 -> 200 changes values by <= 0.009. |
| **Numerical findings (one stylised instance family; no theorem)** | the approximation gaps of the cutoff, E48 and F60 controllers; the shape of the optimal purchase rule in pending labels and remaining horizon; delay, budget and switching-cost curves. |
| **Not claimed** | any guarantee for E48, F60, EQSDp or the cutoff; any statement about real data; that the reduced model's gaps transfer to the real contract. |

The model is a *stylised stand-in*. It drops: non-disagreement events (every step is a disagreement, rate known), discounting, many datasets, non-binary losses. Parameters of the controllers were **not tuned** for it (they are the frozen v1 values mapped to reduced units, section 4). A gap measured here is a property of that mapping, not of the frozen method on real streams.

## 1. Model

Two frozen predictors. Every step is a disagreement event, so exactly one predictor is wrong. p = P(challenger correct) drawn once from a prior (stationary case), or follows a two-state regime chain (hazard case). Deploying the incumbent costs 1[challenger correct], deploying the challenger 1[incumbent correct]. At the start of step t the labels bought at step t-d are released (delay d). After the release the policy chooses the deployment (cost c_s per change) and then whether to buy the label of step t (price c_q), subject to a hard cap B on purchases. Horizon T. A label bought at step s reveals the outcome of step s only. Objective: expected total cost (mean, no tail functional).

Why this is the right reduction: disagreement events are the only ones with paired information; the payback of a switch is (advantage per disagreement) x (remaining disagreements). Queue length d plays the role of the delay measured in disagreement events (real delay 100 events at disagreement rate 0.2 is about 20 steps).

## 2. Bellman recursion

**Stationary case.** State at the start of step t, before the release: s = (dep, k, n, q). k = challenger wins among n *released* labels; q in {0,1}^d marks the steps (bit j <-> step t-1-j) whose purchases are in flight; the budget used is n + |q| (every purchase is either released or in flight). Let m(k,n) = E[p | k,n] (Beta(1,1) prior: (k+1)/(n+2); finite-mixture priors only change m).

Release. If bit d-1 of q is set (the purchase of step t-d), draw X ~ Bernoulli(m(k,n)); (k,n) <- (k+X, n+1); drop that bit. Call the result (k', n', q_r), q_r in {0,1}^{d-1}.

Post-release value (deployment, then acquisition):

W_t(dep, k', n', q_r) = min over dep' in {0,1} of
&nbsp;&nbsp;[ c_s 1{dep' != dep} + l(dep', k', n') + min( V_{t+1}(dep', k', n', (q_r,0)),  c_q + V_{t+1}(dep', k', n', (q_r,1)) 1{B - n' - |q_r| >= 1 and t + d <= T-1} ) ]

with expected step loss l(0,k,n) = m(k,n), l(1,k,n) = 1 - m(k,n), and (q_r, b) the queue after shifting in the new purchase bit b. V_T = 0 and

V_t(dep, k, n, q) = E_X[ W_t(dep, k+X, n+1, q_r) ] if the oldest bit is set, W_t(dep, k, n, q_r) otherwise.

The Bayes-optimal expected cost is V_0(0, 0, 0, empty). Policy evaluation of a fixed (possibly randomised) controller replaces the min by the controller's switch table S_t(dep,k,n) and purchase probability P_t(dep,k,n,q_r); for F60 an auxiliary packet counter is carried.

**Lemma (sufficiency; standard).** (i) Decisions at step s are measurable with respect to information that excludes the outcome X_s of step s (the label is what reveals it), so X_s is conditionally independent of the decision given p and the past. (ii) Hence the posterior predictive of the next released outcome given everything the policy knows is Bernoulli(E[p | released labels]) = Bernoulli(m(k,n)), and pending outcomes need not be tracked, only their due times. (iii) The expected step loss given the information at decision time is l(.) by the tower property. (iv) The state space is finite and the action sets are finite, so backward induction gives the optimum over all non-anticipative policies and randomisation cannot strictly help. This is the Bayes-adaptive MDP argument, i.e. the same structure as the delayed-response model of Chick, Forster and Pertile (JRSS-B 2017), where the optimum is computed by dynamic programming in the Gaussian case with a pipeline of undelivered outcomes.

**Hazard case (`hazard_dp.py`).** Regime z_s in {lo, hi} flips with probability h per step; the challenger is correct with probability p_lo or p_hi. A label bought at s informs about z_s only. State (dep, g, u, q): g = P(z_{t-d} = hi | labels released so far), u = purchases made. The belief about the current regime is the d-step propagation pi_now = 1/2 + (g - 1/2)(1 - 2h)^d; the next step's lagged belief is g propagated one step; releasing the label of step t-d updates g by Bayes with outcome probability g p_hi + (1-g) p_lo. This is an exact HMM filter (a label touches exactly one issue step); the only approximation is linear interpolation of the value function in g (checked by G=100 vs 200, and at h=0 against the (k,n) solver, which makes the two programmes independent implementations of the same value).

## 3. Validation of the implementation

| check | result |
|---|---|
| recursion vs simulation of the optimal policy (T=60, B=8, d=3, c_s=3) | exact 19.5973; simulated 19.743 +- 0.078 and 19.620 +- 0.078 (20,000 episodes each) |
| `evaluate` for the beta controller vs simulation | 22.588 vs 22.503 +- 0.193; pair package 20.342 vs 20.429 +- 0.190 (4,000 episodes) |
| (k,n) solver vs belief-grid solver at h=0, two-point prior | equal to 1e-5 for G=100 and G=200 |
| reduced beta controller (lambda=1, estimated rate) vs the repository's `EQSD` class in the repository simulator (`crosscheck_real_code.py`) | DP 21.242 / 23.513 / 33.647 / 36.219 vs real-code MC 21.007 +- 0.186 / 23.614 +- 0.214 / 33.716 +- 0.294 / 36.536 +- 0.324 (z = -1.26, +0.47, +0.23, +0.98) |
| belief-grid convergence | 79.2155 vs 79.2184 (h=.02); 57.4152 vs 57.4239 (strong) |
| table controllers E48/F60 vs the real search60 compositor, stationary | cutoff effect agrees (+0.15 vs +0.16 +- 0.05) and F60 agrees in direction (-0.03 vs -0.16 +- 0.07); **E48 magnitude does not**: table +1.23, real stack +0.47 +- 0.11 (the table uses the plain posterior; the real `Post` adds a hazard mixture and staleness component; not diagnosed further) |

## 4. Instance, scaling, controllers

Contract-like reduced instance: T=160, B=24, d=8, c_q=0.05, c_s=2.0. Mapping from the real contract (T=2000, delay 100, c_s=5, B=200, disagreement rate about 0.2): real 400 disagreement steps -> 160 (factor 0.4); delay 20 -> 8; c_s 5 -> 2 (so that payback horizon relative to T is preserved); E48 lookahead 50 events -> 4 steps, F60 horizon 100 events -> 8 steps, hazard 0.002/event -> 0.025/step; cutoff H = 0.55 T = 88 (real 1100 of 2000). The budget B=24 is a *tight* regime (15% of steps; the real ratio is about 50% of disagreements); larger B was too slow for the pure-Python VOI tables. Controllers: EQ = Beta-quantile payback (gamma = .3, lambda = 1), W = normal lower bound on the same posterior, + cut = matched hard cutoff, + E48 (arrival discount .5), + F60 (bundle 2), paced purchases (remaining budget / expected remaining disagreements, floor .05). The real-stack Monte Carlo runs the repository's own `compositor` + `Stage1C1Stop`/`Stage2Wald` + `E48` + `F60` unchanged, with lambda = 1 (stationary) or .95 (hazard).

## 5. Results

### 5.1 Stationary Bayes model: exact expected cost (`dp_gaps.csv`; rate estimated as in the panel)

Flat prior on p, base instance (V* = 46.20; value with p known and no labels 41.03; value with no labels at all 80.0):

| controller | J | gap to V* | % of J |
|---|---|---|---|
| EQ (no cutoff) | 48.668 | 2.466 | 5.1 |
| EQ + cut | 48.521 | 2.318 | 4.8 |
| EQ + cut + E48 | 49.753 | 3.551 | 7.1 |
| EQ + cut + F60 | 48.494 | 2.292 | 4.7 |
| EQ + cut + E48 + F60 | 49.705 | 3.503 | 7.0 |
| W + cut | 48.502 | 2.299 | 4.7 |
| W + cut + E48 + F60 | 49.623 | 3.421 | 6.9 |

Other instances (EQ+cut, EQ+cut+E48+F60 vs V*): short delay d=2: V* 44.62, 47.08 (5.2%), 52.14 (14.4%); high switching cost c_s=5: V* 47.96, 50.80 (5.6%), 54.88 (12.6%); two-point prior {.35,.65}: V* 63.48, 68.06 (6.7%), 69.86 (9.1%); null-heavy prior (p=.5 w.p. .6, .65 w.p. .4): V* 72.40, 77.33 (6.4%), 77.65 (6.8%). Beta and Wald differ by < 0.04 everywhere.

Reading: the quantile payback package captures about 93% of the achievable gain in the flat-prior model (labels worth 80.0 - 46.2 = 33.8; controller realises 31.5) and sits 4.7-6.7% of J above the optimum. The cutoff improves the flat-prior and null-heavy cases by 0.15-0.3 and *worsens* the two-point prior by 0.3. **E48 hurts everywhere in the exact stationary model** (+0.3 to +5 in the table, +1.2 on the base instance; +0.47 +- 0.11 in the real-stack Monte Carlo) because it vetoes purchases on the basis of a hazard that is absent. **F60 is neutral** (-0.03 table, -0.16 +- 0.07 real stack).

### 5.2 Real search60 stack, Monte Carlo (6,000 paired episodes per cell, common random numbers; `real_stack_mc*.csv`)

J = mean net cost; "share" = (80 - J)/(80 - V*), the fraction of the Bayes-optimal gain over never buying and never switching (80.0 in every environment) that the controller realises. delta = paired difference to the same parent with cutoff only (+- paired SE).

| environment | V* | oracle (regime path known) | EQ+cut J (share) | + F60 delta | + E48 delta | + E48 + F60 delta | no cutoff delta |
|---|---|---|---|---|---|---|---|
| stationary flat (lambda 1) | 46.20 | 41.03 | 48.43 (93%) | -0.16 +- 0.07 | +0.47 +- 0.11 | +0.005 +- 0.11 | +0.16 +- 0.05 |
| hazard h=.02, p in {.35,.65} | 79.22 | 61.85 | 80.37 (-48%) | -0.15 +- 0.07 | +0.10 +- 0.11 | +0.07 +- 0.12 | +0.38 +- 0.07 |
| hazard h=.05, p in {.35,.65} | 80.00 (= no labels) | 66.40 | 82.10 (n/a) | +0.10 +- 0.06 | -0.18 +- 0.09 | -0.07 +- 0.10 | +0.74 +- 0.06 |
| hazard h=.01, p in {.2,.8} (strong) | 57.42 | 35.96 | 69.28 (47%) | -0.52 +- 0.11 | +0.36 +- 0.16 | -0.34 +- 0.17 | -1.52 +- 0.13 |

Wald-parent J values differ by at most 0.05 from the EQ rows in every cell. Findings:
1. **The approximation gap is largest where information is most valuable.** In the strong-change environment the package realises about half of the Bayes-optimal gain: J=69.3 vs V*=57.4 (gap 11.9, 17% of J; 33 above the oracle that knows the regime path). With weak signals (h=.02 at effect .15, delay 8) the optimum gains only 0.8 over doing nothing, and the controller *loses* 0.4 relative to never buying; at h=.05 the optimum is not to buy at all and the controller loses 2.1.
2. **F60 helps modestly where there are changes** (-0.5 +- 0.1 strong, -0.15 +- 0.07 mild), is neutral or slightly harmful elsewhere. Its size, 0.2-0.8% of J, is consistent in order of magnitude with the -0.39% found on fresh real data (doc 20), which is a coincidence of scale, not a replication.
3. **E48 does not help in this family** (+0.36 +- 0.16 strong, +0.47 stationary, -0.18 +- 0.09 at h=.05 only). The pair is the sum of a small gain from F60 and a loss from E48.
4. **The label cutoff is environment-dependent.** It helps when late labels are noise (stationary, frequent changes) and hurts a lot when changes may occur after the cutoff (strong, rare changes: -1.52 +- 0.13 for *removing* it). A single H fitted on real dev data is a bet on the change process.

## 6. Where do pending labels and the remaining horizon change the optimal action? (`structure_tables.json`)

Exact DP, flat prior, T=160, B=24, d=8, c_s=2. dQ = (value of not buying now) - (value of buying now), at fixed evidence (k,n), dep=0; positive means buy. `pend` = number of the most recent steps whose purchases are in flight.

| evidence (k,n) | pend | t=0 | t=60 | t=100 | t=120 | t=140 | t=150 |
|---|---|---|---|---|---|---|---|
| (1,2) | 0 | .172 | .172 | .167 | .152 | .100 | -.050 |
| (1,2) | 1 | .172 | .172 | .168 | .152 | .100 | -.050 |
| (1,2) | 2 | .072 | .072 | .062 | .055 | -.014 | -.050 |
| (1,2) | 5 | .040 | .040 | .033 | .033 | -.017 | -.050 |
| (3,5) | 0 | .065 | .065 | .061 | .044 | -.050 | -.050 |
| (3,5) | 1 | **.111** | **.110** | .103 | .087 | -.046 | -.050 |
| (3,5) | 2 | .085 | .084 | .080 | .074 | .021 | -.050 |
| (3,5) | 5 | .040 | .041 | .037 | .011 | -.013 | -.050 |
| (6,10) | 0 | .024 | .024 | .020 | -.050 | -.050 | -.050 |
| (6,10) | 2 | .018 | .019 | .014 | -.028 | -.050 | -.050 |
| (6,10) | 5 | .009 | .009 | -.003 | -.005 | -.044 | -.050 |

(-0.05 is the label price: the value of information is zero and the label is not worth buying.)

Numerical findings, all for this instance family:
1. **Pending labels move the optimal purchase decision in both directions.** When evidence is already decisive (6,10) or the next label is far from changing the decision, extra pending labels lower the value of another purchase (diminishing returns: .024 -> .018 -> .009). When evidence is ambiguous (3,5) the *first* pending label **raises** the value of another purchase from .065 to .111: the two labels are complements. This is the Radner-Stiglitz / Frazier-Powell nonconcavity of the value of information, and it is the exact reason the one-label value of E48 can be zero while the two-label value is positive. Using the repository's `voi` at c_s=2, rate 1, horizon 20: the one-label value is 0 and the two-label value is positive at 11 of the evidence states (k,n) with n <= 11 (e.g. (0,1): 0.333; (2,2): 0.200; (3,4): 0.286); at (3,5) the one-label value is 0.857, 0.048, 0.381 with 0, 1, 2 pending, i.e. non-monotone in the pending count.
2. **The remaining horizon enters as a state-dependent deadline, not a fixed cutoff.** The value of a purchase is flat in t over the first 60-70% of the horizon, then falls and becomes negative: between t=110 and 120 for decisive evidence (6,10), between 130 and 140 for (3,5), and between 140 and 150 for ambiguous evidence (1,2). Among the feasible table states the optimum buys in 23% up to t=90 and in 8.5% at t=150. The heuristic cutoff stops all purchases at t = T - H - d = 64. **The optimal stop is much later than the heuristic cutoff; the cutoff is a repair for a controller that uses late labels badly, not a property of the Bayes-optimal controller.**
3. **Cost of delay** (V*, d = 1, 2, 4, 6, 8): 44.38, 44.62, 45.13, 45.67, 46.20, about 0.13 per unit of delay. **Budget** (V*, B = 0, 4, 8, 16, 24, 32 at d=6): 80.0, 50.5, 47.6, 46.1, 45.7, 45.5: strongly diminishing. **Switching cost** (c_s = .5, 1, 2, 5, 10): 44.6, 45.0, 45.7, 47.4, 50.0. Normalised cost V*/T falls with T: .326, .300, .285, .277 for T = 60, 100, 160, 240.

What is *not* known: whether any of these shapes (complementarity, state-dependent deadline) holds in general; no theorem is stated. A proof would need a structural analysis of the Bayes-adaptive MDP (value functions are piecewise linear in a mixture-of-Beta belief); I did not attempt it.

## 7. What this does and does not say about the frozen package

- It shows **the exact optimum is computable** at reduced scale and that the heuristic package sits 5-7% of J above it in a stationary Bayes world and about 17% of J above it where information is most valuable. The hand-built package is a long way from the Bayes-adaptive optimum even though it beats strong heuristic baselines on real data.
- It does **not** show that E48 or F60 are useful: in the exact stationary model E48 is harmful and F60 neutral; in the hazard environments F60 gives 0.15-0.5 and E48 does not help. The frozen real-data improvements (-0.39% of J, doc 20) are of the same order as F60's effect here, and nothing in this analysis explains why E48 would help on real data.
- It does **not** certify the cutoff: its effect flips sign across environments; the optimum has no early deadline.
- Direction for a stronger Paper 1 method: a controller that solves (or approximates by lookahead on) this DP with the evidence model matched to real streams would close part of the 5-17% gap; this is a research hypothesis, not a result.

## 8. Reproduction

```
export OPENBLAS_NUM_THREADS=1 PYTHONIOENCODING=utf-8
PY=<main checkout>/.venv/Scripts/python.exe
$PY scripts/paper1_scale25/theory/hazard_dp.py                 # h=0 cross-check of the two solvers
$PY scripts/paper1_scale25/theory/crosscheck_real_code.py      # DP vs repository EQSD class (about 100 s)
$PY scripts/paper1_scale25/theory/structure_analysis.py        # section 6 (about 80 s)
$PY scripts/paper1_scale25/theory/run_dp_experiments.py        # section 5.1 (14 workers, about 7 min)
$PY scripts/paper1_scale25/theory/run_hazard_dp.py             # optimum and oracle values, section 5.2
$PY scripts/paper1_scale25/theory/real_stack_mc.py             # section 5.2 (14 workers, about 10 min); with env name: strong env only
```
Code state: commit recorded in `11_NOVELTY_AND_THEORY.md`. Seeds are fixed in the scripts; simulation uses common random numbers across controllers.
