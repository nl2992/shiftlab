# Gap-conditioned evidence: development protocol v1

**Registered:** 2026-11-04. **Status:** protocol frozen before the new method run. This is a
development screen only; it does not amend cycle 7, consume confirmation seeds, or establish a
SOTA or deployment claim.

## Question and scope

Does a one-sided Markov transition envelope, evaluated at each observed query gap, retain useful
promotion power on the Failure Atlas's persistent late/transient alternatives while controlling
false promotion when persistence is bounded by a declared value? This isolates evidence from the
acquisition question. Every method uses the same deterministic `episode_front` calendar, fixed
release delay, budget, economic check, and rollback rule. There is no tuning of the gap or acquisition
schedule in this phase.

The candidate is scoped to binary paired differences `D_t in {-1,+1}`. Define
`Z_t = 1[D_t < 0]`, `q0 = (1+h)/2`, and the null transition contract

```text
P(Z_t=1 | Z_{t-1}=z, full past) = rho*z + (1-rho)*p_t,
0 <= p_t <= q0, 0 <= rho <= rho_bar < 1.
```

The first-observation marginal must also be at most `q0`. The fixed-delay runner releases queried
labels in event order, and the query calendar is chosen independently of current and future labels.
The method observes only released labels and issue times. Outcome-dependent delay, nonbinary paired
losses, hidden-state models that do not satisfy the displayed conditional transition contract, and
`rho > rho_bar` are outside the guarantee.

## Candidate evidence process

For two consecutive queried outcomes separated by `g` events, the null conditional probability
`v` of a favourable outcome is bounded by

```text
u(g,z_prev) = q0                                  if z_prev = 0,
              q0 + (1-q0)*rho_bar**g              if z_prev = 1.
```

At the first queried outcome use `u=q0`. For each fixed alternative probability
`r in {0.60, 0.65, ..., 0.95}`, use the predictable factor

```text
f_r(Z) = 1                                  if r <= u,
          (r/u)**Z * ((1-r)/(1-u))**(1-Z)   if r > u.
```

For every `v <= u`, `E[f_r | past] = 1 + (v-u)(r-u)/(u(1-u)) <= 1`; hence each product is a
nonnegative supermartingale under the declared null. Average fixed alternative weights and fixed
start weights `w_j=1/(j(j+1))`; the active-start sum plus its unspent tail `1/(k+1)` is a test
supermartingale. Alarm at `1/alpha`. The start mixture allows post-onset evidence without resetting
alpha. This argument is conditional on the contract above and does not cover an estimated or
development-selected `rho_bar`.

Candidate bounds: `rho_bar=.8` (primary declared operating scope) and `.95` (high-persistence
stress/sensitivity). Neither value may be selected from the evaluation results. The `.8` method has
no safety claim at `.95`; the `.95` method is expected to be more conservative.

## Methods and outcomes

All methods use `uniform_calendar(T,B,d)` and `episode_front`'s economic and rollback rules:

1. `episode_front` conditional-mean started e-process;
2. `markov_lr_gate`, retaining its documented homogeneous-skeleton approximation;
3. `thinned_hedged_gate` with its fixed 10-round evidence thinning;
4. `gap_envelope_rho08`;
5. `gap_envelope_rho95`.

Primary development outcomes are (a) null-twin false-promotion frequency and Wilson interval,
(b) cost per round, (c) correctly timed and any promotion, and (d) query/switch counts. Costs are
paired by seed. The primary alternative set is the unchanged 16 cycle-7 primary cells recorded
verbatim in the frozen run manifest. It includes the two adverse-cost regressions
`f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1` and
`on0.6_L1_strong_harmful_d50_b0.05_s0.1`; neither can be removed from analysis.

The exact set is: `on0.3_L0.6_strong_harmful_d10_b0.05_s0.1`,
`on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`, `on0.6_L1_strong_harmful_d50_b0.05_s0.1`,
`on0.1_L0.6_strong_harmful_d1_b0.05_s0.1`, `on0.1_L0.6_strong_harmful_d10_b0.05_s0.5`,
`f3_rho0.5_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`,
`f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1`,
`f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1`,
`f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.05_s0.1`,
`f3_rho0_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`,
`f3_rho0.5_on0.6_L0.6_strong_harmful_d10_b0.05_s0.1`,
`f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1`,
`f3_rho0_on0.6_L1_strong_harmful_d1_b0.05_s0.1`,
`f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`,
`f3_rho0.8_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`, and
`f3_rho0.8_on0.6_L1_strong_harmful_d10_b0.05_s0.1`.

The null panel uses every Family-3 boundary-null configuration from cycle 6:
`rho in {0,.5,.8,.95}`, `B/T in {.05,.1,.25,.5}`, and `d in {1,10}`. The first three persistence
levels are inside the `.8` candidate's declared range; `.95` is a misspecification diagnostic for
that candidate and an in-range diagnostic for the `.95` candidate.

## Development decision rule

This screen is for discarding weak candidates, not for claiming efficacy. Advance a candidate to a
new frozen validation only if all conditions hold:

1. At every null configuration inside its declared persistence range, no implementation-level
   failure is found and the pointwise false-promotion frequency is at most `.15`; report every
   configuration and interval, not only the aggregate. The theorem, not the finite screen, is the
   source of the nominal guarantee.
2. Across the 11 Family-3 failure cells inside its declared range, its paired equal-cell mean cost
   is lower than `markov_lr_gate` with a 95% paired interval below zero, and it is lower in at least
   6/11 cells. Both mandatory adverse-cost cells must be reported, with neither interval hidden.
3. Its equal-cell mean cost must also be lower than `episode_front` with a 95% paired interval
   below zero. Lower false promotions alone do not count as a cost improvement.
4. On each of the two mandatory cycle-7 adverse-cost cells (one Family-1 cell and one Family-3
   cell), the candidate's 95% paired upper
   confidence bound against the lower-cost of `episode_front` and `markov_lr_gate` must be at most
   `+.01` cost per round. Select that cell's reference by mean cost and hold it fixed for the paired
   contrast. This is a development guard against repeating the known local regressions.
5. If neither candidate passes, stop this evidence direction before adding adaptive acquisition.
   If one passes, freeze a second-stage acquisition protocol using entirely new development seeds.

No parameter is tuned on this run. A pass is only permission to propose a separate validation
protocol; it is not that validation.

## Seeds, artifacts, and reproducibility

- Development seeds: `[700000,700040)`, 40 paired streams per cell.
- Reserved prospective validation seeds: `[800000,800200)`; do not touch unless a new frozen
  validation protocol is approved by the method's development result.
- Cycle-7 validation `[290000,290200)` and confirmation `[900000,1000000)` remain excluded.
- Output directory: `outputs/failure_atlas_v1_gap_envelope_dev/` (ignored). Freeze code/protocol
  hashes, cell IDs, method specs, seed list, and source revision before workers start. Preserve raw
  seed records and a complete report; do not pool these seeds with prior results.

Implementation command, once the separately listed runner and candidate are present:

```powershell
uv run python scripts/run_atlas_gap_envelope_development_v1.py
```

## Novelty boundary

Conditional one-sided betting, started mixtures, Markov observation gaps, and bounded-persistence
calibration are established ingredients. The candidate is not novel by construction. A possible
contribution would require a useful, attributable improvement under the same declared transition
contract and hard delayed-label budget, followed by independent validation and source-level prior
art review. The broader user objective remains unmet until that evidence exists.
