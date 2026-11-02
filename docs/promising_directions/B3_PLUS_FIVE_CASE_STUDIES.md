# B3+ five real-world case studies

Method frozen at commit `e846107` (**P7s**: P3b plus settled-decision acquisition). Screening
rules registered at `670c1bf` **before** any new dataset was downloaded. No method parameter was
tuned on any dataset. Configuration identical throughout: `T = 2000`, `B = 200`, `c_q = 0.05`,
`c_s = 5`, 100 shared query seeds, seed base `20261101`.

## Screening denominator (required disclosure, protocol section 5)

**21 datasets screened. 11 reached locked-window evaluation. 5 selected as case studies.**

| Outcome | Count | Datasets |
|---|---:|---|
| **SUCCESS** | **5** | spam, rialto, weather, openml_ldpa, uci_occupancy |
| `USELESS_NO_HEADROOM` (condition 2: P7s not better than never-switching) | 5 | airlines, bank, elec2, criteo, insects_abrupt_balanced |
| `USELESS_NO_HEADROOM` (dev-window precheck; locked window never read) | 3 | creditcard, keystroke, trec07 |
| `USELESS_NO_IMPROVEMENT` (condition 1: CI not below 0) | 1 | openml_eeg_eye_state |
| `USELESS_INELIGIBLE` (no defensible chronological order; none invented) | 7 | http, smtp, openml_covertype, openml_shuttle, openml_run_or_walk, river_phishing, sms_spam |

Because selection uses the locked-window outcome (condition 1), **these five are a selected set.**
They are five positive case studies. They are **not** an unbiased success rate, and the paper may
not imply the method was evaluated only on these five. The full 11-stream evaluation stays in the
paper.

## The five cases

Paired with P3b on identical episodes and query seeds. Episode bootstrap where `K >= 5`; seed
bootstrap, marked LOW-POWER, where `K < 5`.

| Dataset | Domain | K | P0 | P3b | **P7s** | P7s vs P3b (95% CI) | labels | P6 | Power |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **openml_ldpa** | human activity / localisation | **32** | 663.00 | 483.25 | **478.82** | **-4.43** [-7.03, -2.58] | 181 -> 115 | 506.51 | episode |
| **rialto** | streaming image classification | **16** | 202.06 | 103.73 | **98.42** | **-5.31** [-6.01, -4.61] | 159 -> 53 | 122.91 | episode |
| uci_occupancy | building sensors | 4 | 481.25 | 177.63 | **176.62** | -1.01 [-1.03, -0.99] | 102 -> 81 | 236.45 | LOW-POWER |
| weather | environmental | 3 | 504.00 | 475.77 | **472.57** | -3.20 [-3.33, -3.08] | 178 -> 114 | 465.56 | LOW-POWER |
| spam | email text | 1 | 849.00 | 254.09 | **247.43** | -6.66 [-6.77, -6.55] | 200 -> 67 | 315.95 | LOW-POWER |

Two of the five (ldpa `K=32`, rialto `K=16`) carry episode-level bootstraps and are the load-bearing
cases. The other three are low-power and are labelled as such everywhere.

## Mechanism, uniform across all five

The gain is **entirely** the query-cost term. On spam, rialto and weather, deployment loss is
bitwise identical to P3b per episode, promotion times are identical, and rollbacks are zero for
both policies: P7s is a **strict Pareto improvement**, obtaining the identical deployed-model
sequence with 36-67% fewer labels. The method improves no decision; it removes spend that P3b
continues to pay at its budget-paced rate after the deployment decision is already settled.

Label reductions: spam 67%, rialto 67%, ldpa 36%, weather 36%, occupancy 20%.

## P6 comparison, stated in full

Among the five selected cases, **P7s beats P6 on four** (spam, rialto, ldpa, occupancy) and loses
on weather. This is a material change from the earlier seven-stream picture: on openml_ldpa, a
`K=32` episode-bootstrapped case, **P6 loses to P3b by +23.26**, so the simple batch test does not
dominate once streams with large persistent advantage are included.

Across **all 11** streams evaluated on locked windows, however, the split is **P7s better on 5,
P6 better on 6** (P6 wins weather, airlines, bank, elec2, criteo, insects). Both counts belong in
the paper. P6's validity additionally rests on an assumed exchangeability of disagreement
outcomes that the sequential procedure does not require; that asymmetry must be stated wherever
the comparison appears.

## Known gap

No selected case exhibits post-promotion reversal: rollbacks are zero throughout. P7s reduces
post-promotion querying to the propensity floor, so its rollback latency is strictly worse than
P3b's, and that failure mode is characterised **only in simulation** (synthetic world W3, where
the frozen setting is neutral). A real stream with post-promotion reversal remains the single most
valuable addition to this evaluation.

## Reproduction

```bash
uv run pytest -q tests/promising_directions/
uv run python scripts/promising_directions/b3_plus_experiments.py \
  --streams spam,rialto,weather --variants P0,P1,P2,P3b,P6,P7s --config S0 --horizon 2000
uv run python research/b3_plus/dataset_discovery/run_screening_queue.py --resume
```

Per-episode records: `docs/promising_directions/results/b3_plus/` and `.../screening/<dataset_id>/`.
Registry of every candidate: `research/b3_plus/dataset_discovery/dataset_registry.json`,
`successful_cases.json`, `discarded_cases.json`.
