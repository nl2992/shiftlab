# Decisive result: the economic stopping trigger loses

Run 2026-11-03 under `SOTA_NARROWED_PROTOCOL.md` and its amendment, both registered before this
experiment existed. Primary configuration: `T=2000`, `B=200`, `c_q=0.05`, `c_s=5`, `alpha=0.05`,
`eps=0`, `p_min=0.05`, 100 seeds, seed base `20261101`. Policies paired on episodes and seeds;
pathwise budget feasibility asserted for every policy on every episode.

## The numbers

| Dataset | K | discern_style | **economic_stop (ours)** | gated_deployment | ours - gated (95% CI) | ours better in |
|---|---:|---:|---:|---:|---:|---:|
| rialto | 16 | 210.020 | **96.546** | **94.695** | **+1.852** [+0.989, +3.394] | **0 / 16** |
| openml_ldpa | 32 | 656.980 | **544.016** | **534.430** | **+9.585** [+5.320, +14.678] | **6 / 32** |

Both intervals lie **entirely above zero**. We lose on both powered cases.

We beat the DISCERN-style comparator enormously (-113.5 and -113.0), but the amendment registered
*before* this run states that beating only DISCERN-style does not satisfy the rule, because its
`c = B/pi_min` increment range wastes range rather than reflecting evidence. That exclusion was
written down in advance precisely so it could not be reached for now.

## Decomposition: the pre-registered mechanism check fails against us

Protocol section 4 required that any gain appear as **fewer switches** or **labels saved**, and
**not** as deployment loss. Measured:

| Dataset | total | deployment loss | label cost | switch cost |
|---|---:|---:|---:|---:|
| rialto | +1.852 | **+1.758** | +0.094 (+1.9 labels) | 0.000 (0.000 switches) |
| openml_ldpa | +9.585 | **+9.728** | +0.215 (+4.3 labels) | -0.358 (-0.072 switches) |

On `openml_ldpa` the economic trigger **did** do what it was designed to do: it switched less
(-0.072 switches, saving 0.358). But the deployment-loss penalty is **27 times larger** than that
saving. And on both datasets we spent **more** labels, not fewer — the direct opposite of the
prediction.

The effect is real, correctly attributed, and against us.

## Why it loses

Raising the bar from `g > 0` to `g > c_s/(T-t)` delays promotion. On a stream where the
challenger is genuinely better, every event of delay is paid in incumbent loss.

At `c_s = 5` and `T = 2000` the threshold is only `0.0025`, yet the confidence sequence's lower
bound spends a long stretch between `0` and `0.0025`, and we pay incumbent loss for the whole of
it. The switching cost we save is a one-off `5`; the loss we accrue while waiting is per-event and
unbounded by `c_s`.

Stated generally: **the economic trigger is strictly worse whenever switching is cheap relative to
the per-event advantage**, because it buys a bounded saving with an unbounded delay. The regime
where it could help — `c_s` large relative to the advantage, or a short remaining horizon — is
not the regime these datasets are in.

## Pre-registered decision

> **STOP** if we **lose** on either powered case.

We lost on **both**. **The programme stops here.**

## What is deliberately not being done

The mechanism above identifies a configuration where the economic trigger should win: large
`c_s`, small advantage, short horizon. **We are not running it.** The pre-registered rule fired on
the primary configuration, and searching for a configuration that reverses the verdict after
seeing the verdict is exactly what pre-registration exists to prevent. If that boundary is worth
testing, it is a **new question needing its own registration**, not a rescue of this one.

## What stands

- The six competitor implementations, five verified numerically against author code (SMCS
  cross-language against R at 4e-15), with every adapter deviation and irreproducibility recorded.
- The shared simulator, whose design caught a silent label-loss bug twice from independent
  directions before any comparison ran on it.
- The prior-art record, which found that both halves of the previously intended paper were
  already published.
- `B3_PLUS_*`: settled-decision acquisition still beats **P3b** on five datasets. That result is
  unaffected. What this experiment shows is that it does **not** beat the published
  certificate-triggered alternative, which is the comparison that matters.

Gate: `IN PROGRESS` becomes **`NOT MET — PROGRAMME STOPPED`**.
