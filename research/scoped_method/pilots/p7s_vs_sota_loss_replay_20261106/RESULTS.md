# P7s exposed SOTA loss-replay results

**Decision:** no SOTA-qualified target; do not open a fresh confirmation source for this unchanged
P7s candidate. This screen does find a narrow positive against Gated deployment on the exposed
OpenML-LDPA loss path, but the frozen rule fails because P7s loses to other applicable published
baselines. It is not independent real-data confirmation.

## Primary paired results

All policies used the same event-level binary loss pairs, delay, horizon, query budget, label price,
switch cost, and 100 shared randomization seeds. Reported intervals are paired episode-bootstrap
95% intervals over 16 Rialto or 32 LDPA episodes; seed replicates are averaged within episode.
Both label encodings gave **exactly identical results** (maximum difference in any mean cost was
0.0), so the table reports the common result.

| Dataset | Policy | Mean net cost | Loss | Labels | Switches | P7s minus policy [95% CI] |
|---|---|---:|---:|---:|---:|---:|
| Rialto | P7s | 98.504 | 90.853 | 53.0 | 1.00 | — |
|  | Gated deployment | 94.657 | 88.110 | 30.8 | 1.00 | +3.847 [+2.447, +5.709] |
|  | SMCS retain-incumbent | 89.959 | 77.000 | 159.2 | 1.00 | +8.545 [+6.347, +10.947] |
|  | Model Picker adapter | 74.384 | 67.890 | 28.9 | 1.01 | +24.120 [+22.523, +26.398] |
|  | Model Selector adapter | 77.922 | 64.880 | 160.9 | 1.00 | +20.583 [+18.552, +23.165] |
|  | Online LLM Picker | 73.038 | 65.000 | 57.9 | 1.03 | +25.467 [+23.636, +27.819] |
|  | Xu acquisition-only | 99.512 | 86.670 | 156.9 | 1.00 | −1.007 [−2.971, +1.745] |
| OpenML-LDPA | P7s | 478.351 | 467.718 | 115.7 | 0.97 | — |
|  | Gated deployment | 536.103 | 527.370 | 97.6 | 0.77 | **−57.751 [−79.748, −38.126]** |
|  | SMCS retain-incumbent | 465.220 | 451.870 | 181.3 | 0.86 | +13.131 [−10.265, +32.105] |
|  | Model Picker adapter | 431.866 | 420.970 | 56.3 | 1.62 | **+46.485 [+34.996, +58.528]** |
|  | Model Selector adapter | 434.959 | 418.380 | 184.8 | 1.47 | **+43.392 [+30.951, +56.347]** |
|  | Online LLM Picker | 431.851 | 418.820 | 82.8 | 1.78 | **+46.500 [+35.294, +58.033]** |
|  | Xu acquisition-only | 489.255 | 475.870 | 176.7 | 0.91 | **−10.904 [−19.325, −3.854]** |

Negative P7s-minus-comparator favors P7s. It clears the frozen five-unit benefit threshold against
Gated deployment on LDPA, and loses to Gated by less than five on Rialto. However, it is materially
more costly than the Model Picker and Model Selector adapters on LDPA, with both paired intervals
entirely above zero. The screen therefore fails the frozen requirement to be cheaper than every
applicable published baseline on the nominated target.

## Cost mechanism

On LDPA, P7s saves 59.65 predictive-loss units against Gated while spending 0.90 more on labels and
1.00 more on switching, for a net saving of 57.75. This is an observed accuracy/deployment-policy
advantage in this replay, not merely cheaper monitoring. But against Model Picker, P7s incurs 46.75
more loss, 2.97 more label cost, and saves only 3.25 in switch cost, yielding a 46.49 net-cost
loss. Against Model Selector, P7s incurs 49.34 more loss while saving 3.46 in label cost and 2.50
in switching cost, still losing 43.39 net. These stronger baselines close the apparent SOTA gap.

On Rialto, P7s loses to Gated by 3.85: 2.74 more loss, 1.11 more label cost, and equal switches.
It loses more to SMCS, Model Picker, Model Selector, and Online LLM Picker. Xu acquisition-only is
statistically unresolved on Rialto.

## Interpretation and limitations

- This replay preserves the saved real-data 0/1 model-loss paths, but reconstructs binary
  predictions using two artificial label encodings. It does not reproduce original model
  predictions, covariates, or the label-feature relationship. Equality across encodings confirms
  robustness only to this particular binary marginal transformation.
- Rialto and LDPA were already selected/exposed in the B3+ case study. The results are development
  diagnostics, not fresh validation, source-level generalization, or confirmation.
- The methods are adapters under the fidelity and guarantee caveats in
  `docs/promising_directions/sota/SOTA_IMPLEMENTATION_VALIDATION.md`. In particular, do not equate
  cost ranking with equal statistical safety guarantees.
- P7s wins against Gated on one exposed target but does not beat the strongest overall applicable
  baselines. No new repair, novelty claim, or real-data transfer claim follows.

## Reproduction and artifacts

Exact commands are frozen in [`PROTOCOL.md`](PROTOCOL.md). Machine-readable outputs are
[`zeros/vs_sota_results_zeros.json`](zeros/vs_sota_results_zeros.json) and
[`xor/vs_sota_results_xor.json`](xor/vs_sota_results_xor.json).

| Artifact | SHA-256 |
|---|---|
| zeros results | `11212217e37df70b1628add43f06e83b7019e51806d1e97286eed47c310bc976` |
| xor results | `5926f1141ea0beca887dc4c708b751a5cc0d62f5c0ba3776657251f50ade0f28` |

The next useful step is a targeted extension that addresses the LDPA loss gap against Model
Picker/Model Selector, with a prior-art review and a new frozen protocol. Do not spend or open a
fresh real confirmation source for P7s unchanged.
