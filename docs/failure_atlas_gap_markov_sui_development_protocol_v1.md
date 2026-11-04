# Exact-gap Markov SUI transfer: development protocol v1

**Registered:** 2026-11-04 before execution. Development screen only; not confirmation, a SOTA
claim, or evidence of novelty.

## Question

Does a gap-indexed sequential universal-inference (SUI) gate retain useful cost and promotion
performance on Failure Atlas Family 3 when compared with the existing homogeneous-skeleton
Markov likelihood gate and the broader bounded-persistence envelope? This isolates evidence under
the fixed uniform calendar. It does not test a new acquisition rule.

## Method and validity scope

For a Family-3 null twin, `Z=1[D<0]` is a stationary refresh-or-hold chain with mean
`p=q0=(1+h)/2` and persistence `rho`. At gap `g`,

```text
P(Z_next=1 | Z_prev=z) = rho**g * z + (1-rho**g) * p.
```

The candidate uses a fixed mixture over alternative stationary `(p,rho)` pairs with `p>q0`.
For each possible label-index start, it conditions on that start's first observed label and
multiplies only subsequent transition probabilities. The null denominator is an upper bound on
the likelihood supremum: partition `[0,q0] x [0,1]` into rectangles, maximize each transition
factor at its four corners, multiply those per-factor maxima within each rectangle, then take the
largest rectangle product. Each factor is separately monotone in `p` and `rho` on a rectangle;
the resulting product bounds the shared-parameter likelihood for every null member. Dividing the
fixed alternative mixture by this bound is dominated by a likelihood-ratio martingale for each
true null parameter. A uniform finite start prior over the known calendar labels keeps dormant
starts at unit capital and requires no free reset. Alarm threshold is `1/alpha`.

The guarantee is restricted to binary outcomes from the stationary refresh-or-hold null, fixed
label-independent query calendar, and constant delay with release order preserved. It does not
cover time-varying `p_t`, arbitrary hidden dependence, informative delays, or adaptive acquisition.
This is a transfer of established universal-inference machinery, not a novelty claim. The
implementation avoids the prior SUI implementation's log flooring and conditions each start on
its first label. The conservative cell mesh may lose power; it is not tuned on this screen.

## Frozen comparison

- Seeds: `[720000,720020)`; 20 paired development streams per cell. This range was checked against
  the existing `outputs/failure_atlas_v1*/records.jsonl` seed fields and was unused there.
- Horizon `T=1000`; unchanged cell configuration, fixed delay, budget, switching cost, economic
  rule, and rollback rule from the Failure Atlas runner.
- Methods: `episode_front`, `markov_lr_gate`, `gap_envelope_rho08`, and `gap_markov_sui`.
- Alternatives: `f3_rho0.5_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`,
  `f3_rho0.8_on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`,
  `f3_rho0.5_on0.6_L1_strong_harmful_d1_b0.05_s0.1`, and the mandatory adverse-cost cell
  `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`.
- Null twins: `rho in {0,.5,.8,.95}`, delay `1`, budget fraction `.1` and `.25` (eight cells).
  The `.95` row is explicitly outside `gap_envelope_rho08`'s declared range and remains a stress
  diagnostic; the exact-gap SUI null permits all `rho in [0,1]`.
- Report false-promotion counts and Wilson intervals by null cell, cost/promotion/query/switch
  summaries on every alternative, and paired per-seed cost differences versus each comparator.
  Twenty streams give a coarse screen only.

## Interpretation / advance rule

Advance only to a separately frozen, larger development screen if (i) no implementation failure
occurs, (ii) no more than 3/20 false promotions occur in any in-scope null cell, (iii) SUI's
equal-cell mean cost is below `markov_lr_gate` and `episode_front` with paired 95% intervals below
zero over the four alternatives, and (iv) the adverse-cost cell's upper paired 95% cost-difference
bound versus the lower-mean-cost of `episode_front` and `markov_lr_gate` is at most `+.01` per
round. These are screening rules, not formal validity tests. Failure means do not add adaptive
acquisition to this SUI candidate. Passing authorizes only a larger fresh-seed study; it cannot
support a novelty or SOTA claim.
