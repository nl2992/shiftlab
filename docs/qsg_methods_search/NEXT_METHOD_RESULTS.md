# Next-method results (2026-11-07 continuation)

Authoritative per-candidate rows: [NEXT_METHOD_LEDGER.md](NEXT_METHOD_LEDGER.md). This file is the
summary and the reproduction recipe. Code: `scripts/qsg_methods_search/next_method.py` (all
candidates, the oracle diagnostic and the S-family regimes), commit `2db4ddef` and later.

## Headline

**Twelve mechanisms were screened against tuned fixed-discount Wald-LCB economic switching.
None produced a meaningful, attributable gain on the synthetic contract.** The best gains are
≈1–1.6 units per episode (≈2–4% of avoidable cost), all from in-sample selection over many
configs, so they are within selection noise. That is a robust negative result for C2, plus three
positive structural findings:

1. **Frontier efficiency.** For every weighting of change vs guard regimes, the lower envelope
   of 27 fixed (λ, γ) Wald configs is within ≈1 unit of the best of ≈150 candidate configs.
2. **The headroom exists, but only with change-time information.** An evaluator-side oracle
   restart gains 11.7 units on change regimes. Online, change detection at ≈0.1 labels/event
   plus a 100-event delay is no faster than a short fixed memory. Label-only evidence
   processing is saturated.
3. **Real streams reverse the memory optimum (M5).** On the 14 exposed real streams, the best
   fixed Wald is long memory (λ=.97). The synthetic-tuned short memory, including the frozen
   C4 arm EQSDp-B, is 6–9 units worse there. Real disagreement outcomes are strongly serially
   dependent: lag-1 autocorrelation .3–.95 on 9 of 14 streams.

## Candidate summary (dev seeds 2026110901 × 40; Δ = candidate − best fixed Wald on the same seeds)

| ID | Mechanism | Family | Δ family | Verdict |
|---|---|---|---|---|
| A3 | fast/slow memory, test-gated | 14 | +3.20 [+2.18, +4.22] | STOP |
| A1 | two-state restart | 14 | +2.66 [+1.61, +3.71] | STOP |
| A4 | follow-the-leader over discounts | 14 | +1.19 [+0.37, +2.01] | STOP |
| B1 | asymmetric promotion/rollback levels | 14 | +1.29 [+0.55, +2.03] | STOP |
| A5 | BOCPD mixture quantile | 14 | +0.12 [−0.81, +1.05] | STOP (tie) |
| A5b | BOCPD MAP segment | 14 | +9.6 | STOP |
| A6 | GLR change-point-cut window | 14 | +3.3 | STOP |
| D1 | decision-ambiguity label bursts | 14 | −0.75 [−1.66, +0.17] | STOP (tie) |
| S | label-free sentinel reset + burst | S-family (10) | −1.18 [−2.99, +0.63] (+1.20 on the 14) | STOP |
| E | dependence-adjusted (ESS) Wald | 14 + 6 dependence | −0.81 [−1.62, +0.01] | best robust option; below the gate |
| F | Bayes-filter payback (BOCPD + hazard horizon) | 14 | +0.35 [−0.68, +1.38] | STOP (tie) |
| G | OPE-selected shadow switchers | 14 + 6 + real | cross-domain minimax regret 4.21 vs 4.37 (best fixed Wald) and 3.28 (E) | STOP |

Cross-domain minimax regret (worst of synthetic-14, dependence-6 and real-14, each vs the
per-domain best fixed Wald; development, in-sample): **E 3.28**, best fixed Wald (λ=.95, γ=.2)
4.37, G 4.21. E's component effect on real streams vs its own r≡0 ablation is −2.17 pooled. It
is concentrated on the dependent streams (appliances −20.3, household_power −5.9,
beijing_pm25 −6.3), zero on 5 streams, and +4.3 on bank.

## Development gate outcome

The gate (NEXT_METHOD_PLAN.md) requires a gain over the in-sample-tuned best Wald that
replicates, with an ablation and a coherent family. **No candidate passed condition (1).** E
comes closest (−0.81, CI touching 0, on the mixed family). Therefore the NM-dev replication
seeds (2026110941) and the NM-C3 seeds (2026110977) were **not opened**. They remain reserved.

## Reproduce

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONPATH="scripts/qsg_methods_search;scripts/failure_atlas_v2_flq"
POL=$(cat outputs/qsg_methods_search/nm_dev_policies.txt)   # likewise nm_dev{2..8}_policies.txt
uv run python scripts/failure_atlas_v2_flq/run_atlas_v2.py --kind synthetic --seeds 40 --seed-base 2026110901 \
  --regimes <see ledger per stage> --extra next_method --policies "$POL" --workers 20 --out outputs/qsg_methods_search/nm_dev
cd scripts/qsg_methods_search && uv run python analyze_nm.py ../../outputs/qsg_methods_search/nm_dev/records.jsonl
uv run python nm_real_dev.py run --out ../../outputs/qsg_methods_search/nm_real_dev --seeds 5 --seed-base 2026110961 --workers 20
uv run python analyze_nm_real.py ../../outputs/qsg_methods_search/nm_real_dev/records.jsonl
```

Raw records are gitignored under `outputs/qsg_methods_search/nm_dev*/` and `nm_real_dev*/`.
Real-stream checksums were verified on both runs (`checksums.json`). Stage-8 records pair
exactly with Stage-1 on shared arms (max |Δ| = 0.0).

## Limitations

- Development only: every number above is in-sample selection on 40 seeds or exposed real
  streams, with no confirmatory test.
- Fixed contract (B=200, c_q=.05, c_s=5, delay mostly 100). Long-delay (F6), near-tie (F7),
  rare (F8) and high-budget-pressure (F9) regimes were not screened.
- Candidate designs were kept deliberately simple (one or two knobs). A failure here says a
  *simple* version of each mechanism does not beat tuned Wald, not that no version could.
