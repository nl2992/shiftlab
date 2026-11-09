# FLQ two-tier re-test: registered protocol

**Registered:** 2026-11-06, before any run at the seed bases below. The protocol, regimes,
runner, analysis script and tests are committed together. The commit hash is the registration
record. The only executions before registration were a 4-seed plumbing smoke at the Sprint 2
development seed base 2026110701, plus unit tests on synthetic records; neither produces a
result used here.

**Why this exists:** [ACCEPTANCE_CRITERIA_REVIEW.md](ACCEPTANCE_CRITERIA_REVIEW.md) found that
Atlas v2 rejected front-loaded acquisition with a promotion bound on dependent Markov nulls, a null
class its certificate does not claim, and that its cost on those nulls matched its host. This
protocol replaces that gate with the two-tier criterion and re-tests on fresh seeds and new regime
instances. The Atlas v2 results stay on record unchanged.

## Code and contract

- Code: this commit. It includes the adaptive-range propensity-ordering fix `c66185c0`.
- Contract: `T=2000`, hard `B=200`, `c_q=.05`, `c_s=5`, `alpha=.05`, the common simulator
  (`scripts/promising_directions/sota/simulator.py`), and objective `J = loss + .05·labels + 5·switches`.
- Runner: `scripts/p2_benchmark/run_two_tier.py`, which wraps `scripts/sota_sprint/screen.py` and
  registers the new `N_*` regimes from `scripts/p2_benchmark/two_tier_regimes.py`.
- Analysis: `scripts/p2_benchmark/analyze_two_tier.py`, whose constants are the rules below.

## Policies

| Role | Policies |
|---|---|
| **Primary candidate** | `gated_adaptive_range+front` (host `gated_adaptive_range`) |
| Secondary candidate | `gated_deployment+QCE+front`: FLQ as registered in Atlas v2 (host `gated_deployment`) |
| Certified comparators (all six, simultaneously) | `gated_deployment`, `gated_adaptive_range`, `discern_style`, `discern_design_floor`, `SMCS+retain-incumbent`, `xu_acquisition_only` (the last is a ShiftLab certificate with Xu acquisition; included because it was the strongest on Atlas v2 alternatives) |
| Pacing check | `gated_adaptive_range+pace_tuned` |
| Context | `model_selector_causal` (uncertified), `CONTROL_never_switch` |

## Regimes and seeds

Seed bases are unused before this registration. Alternatives use **2026110681**; nulls use **2026110682**.

| Set | Regimes | Seeds | Role |
|---|---|---:|---|
| Tier A | V_null, V_worse, F0_null, **N_null** | 1000 | Claimed (iid conditional) null |
| Tier B | V_null_dep_r5, V_null_dep_r8, **N_null_dep_r7**, **N_null_dep_r9**, W_null_dep_r95, O_null_order2, O_null_semimarkov | 500 | Dependent nulls outside the claimed class |
| Primary region | **N_better_a, N_better_b, N_better_c, N_dep_better_r6, N_near, N_bursty** | 200 | Declared region: stationary or slowly varying improvement; new parameter instances |
| Replication | V_better_a, V_better_b, V_better_c, V_dep_better_r5, V_near, V_bursty | 200 | Atlas v2 instances (parameters exposed), fresh seeds |
| Outside region | V_late_600, V_reversal_1000, V_recurrent, W_late_1000, W_reversal_700, **N_late_800**, **N_reversal_900** | 100 | Reported; no gate |

Bold names are the new instances. Their parameters differ from every existing regime, and a unit test checks this.

## Decision rules (fixed now)

1. **Tier A, a hard gate.** On every Tier A null, the candidate's promotion rate is ≤ `.05 + 2·sqrt(.05·.95/1000) = .0638`.
2. **Tier B, an economic tolerance.** On every Tier B null, the upper end of the paired 95% t-interval for
   `J(candidate) − J(host)` is ≤ `+5` (one switch cost). Promotion rates for the candidate and its host, and
   `J − J(never-switch)`, are reported alongside, not gated.
3. **Efficacy.** In a primary-region regime, the candidate "wins" if all six one-sided simultaneous 95% upper
   bounds on `J(candidate) − J(comparator)` are < 0. The bounds come from a max-statistic paired bootstrap over seeds:
   4,000 resamples, seed 20261106. Efficacy passes with **≥ 4 of 6** wins.
4. **Verdict.** `SUPPORTED` iff rules 1–3 all pass. The primary candidate carries the claim. The
   secondary candidate is reported under the same rules but makes no separate headline claim.
5. **Replication** wins (V_* set) and **outside-region** contrasts vs host, never-switch and the best
   comparator are reported descriptively. The pre-stated expectation is a loss under reversal.
6. **Framing.** If the 95% CI of `J(candidate) − J(pace_tuned)` lies within `[−2, +2]` in ≥ 4 of 6
   primary-region regimes, any supported claim is framed as *budget-feasible pacing*, not
   front-loading specifically.
7. The analysis fails closed if any (regime, seed) cell lacks a policy, or if seed counts differ
   from this table.

## Consequences

- `SUPPORTED`: front-loaded (or paced) acquisition becomes the P2 benchmark's companion baseline. It is
  scoped to the declared region, with reversal losses in the headline table, and the next step is the
  untouched real-data run (scope item W5). It is not a novelty claim: front-loading equals DISCERN with π=1.
- `NOT_SUPPORTED` on Tier B: front-loading carries economic harm under dependence. This is recorded
  as a negative result and as a benchmark finding.
- `NOT_SUPPORTED` on efficacy: the Atlas v2 gains do not hold against all certified comparators on
  new instances. This is recorded as a negative result.

## Limitations

The test is synthetic only. Replication-set parameters were exposed during Atlas v2. The comparators are
common-contract ports, not author-native code. Empirical null rates are not guarantees. No real data are
opened under this protocol.

## Commands

```bash
export PYTHONPATH=scripts/promising_directions/sota
P=gated_adaptive_range+front,gated_deployment+QCE+front,gated_adaptive_range,gated_deployment,discern_style,discern_design_floor,SMCS+retain-incumbent,xu_acquisition_only,gated_adaptive_range+pace_tuned,model_selector_causal,CONTROL_never_switch
uv run python scripts/p2_benchmark/run_two_tier.py --regimes V_null,V_worse,F0_null,N_null --policies $P --seeds 1000 --seed-base 2026110682 --workers 8 --out outputs/p2_benchmark/two_tier/tier_a
uv run python scripts/p2_benchmark/run_two_tier.py --regimes V_null_dep_r5,V_null_dep_r8,N_null_dep_r7,N_null_dep_r9,W_null_dep_r95,O_null_order2,O_null_semimarkov --policies $P --seeds 500 --seed-base 2026110682 --workers 8 --out outputs/p2_benchmark/two_tier/tier_b
uv run python scripts/p2_benchmark/run_two_tier.py --regimes N_better_a,N_better_b,N_better_c,N_dep_better_r6,N_near,N_bursty,V_better_a,V_better_b,V_better_c,V_dep_better_r5,V_near,V_bursty --policies $P --seeds 200 --seed-base 2026110681 --workers 8 --out outputs/p2_benchmark/two_tier/region
uv run python scripts/p2_benchmark/run_two_tier.py --regimes V_late_600,V_reversal_1000,V_recurrent,W_late_1000,W_reversal_700,N_late_800,N_reversal_900 --policies $P --seeds 100 --seed-base 2026110681 --workers 8 --out outputs/p2_benchmark/two_tier/outside
D=outputs/p2_benchmark/two_tier
uv run python scripts/p2_benchmark/analyze_two_tier.py --runs $D/tier_a $D/tier_b $D/region $D/outside --out docs/p2_benchmark/results/flq_two_tier
```
