# E-SR slower acquisition pacing screen

**Status:** one fixed operating-configuration screen. This is not a new detector or a novelty
claim. Freeze this protocol and source before the null calibration. No rate grid is permitted.

## Target and hypothesis

Target Failure Atlas regime: `F1_late_800`, with a persistent challenger advantage beginning at
event 800. The calibrated default E-SR can detect this change, but its budget-paced label stream
spends a substantial portion of the hard cap before the improvement begins. The candidate uses
the existing horizon-weighted pacing formula with `k=0.5` in both the Gated host and the E-SR
monitor. This reduces early acquisition propensity while preserving the same horizon, pathwise
budget, delay, alpha and e-SR detector. The candidate may leave the cap unspent if the evidence
does not support more queries; every unused label and its cost are reported.

For `r_t = (N_disagree(t) + 5) / (t + 20)`, remaining budget `b_t`, horizon `T`, and current time
`t`, the pacing propensity on disagreement events is
`q_t = min(1, max(0.05, 0.5 b_t / max(r_t (T-t), 10^-9)))`. Agreements are not queried. The
propensity is predictable from prior disagreements and the current event; no label or regime truth enters it.
The policy uses E-SR's unchanged detector, global alpha 0.0005, 50/50 host/detector split, and
restart rules. Because changing acquisition changes the observed-label sequence, the prior E-SR
null calibration does not transfer; recalibrate this exact candidate.

## Prior-art boundary

Time-varying label-budget allocation in drifting data streams is established prior work. For
example, Castellani, Schmitt, and Hammer study delayed-label active learning and a drift-dependent
dynamic budget that increases sampling after detected drift ([paper](https://arxiv.org/abs/2204.06822));
the 2024 *Dynamic budget allocation for sparsely labeled drifting data streams* likewise reallocates
label budgets around detected drift ([journal article](https://doi.org/10.1016/j.ins.2023.119821)).
This candidate has no post-drift detector, and its `k=0.5` setting is a conventional pacing
configuration. Even if it passes, claim at most a scoped deployment configuration unless the
matched ablations show an effect not explained by this existing adaptive-budget prior art.

## Matched methods and costs

Horizon 2,000; hard label cap 200; 100-event delay; label cost 0.05; switch cost 5.0; paired
synthetic loss streams. Candidate: `E_srrSR:pace_k0.5:gated_deployment`, alpha 0.0005. Primary
comparator: calibrated default `E_srrSR:gated_deployment`, alpha 0.0005. Secondary, identical-stream
comparators: never-switch, PFA-SR, RMM, E_rb, E_swcert, corrected Gated+front, plus Qiu and Gong
ports. Qiu/Gong results are labelled as port diagnostics, not author-native algorithm reproductions
or equal-safety controls.

## Calibration and independent operating validation

1. **Calibration only:** run the fixed candidate on 1,000 fresh iid `F0_null` streams at seed base
   `7110601301`. Require the one-sided 95% Wilson upper bound on any promotion to be at most 0.05.
   If it fails, stop; keep the alternative-regime seed set closed.
2. **Independent validation:** only after a pass, record calibration count/hash and commit an
   evaluation amendment. Then run 1,000 independent `F0_null` streams at seed base `7110601302`
   and 100 paired streams per alternative at seed base `7110601303`.
3. **Primary target gate:** on `F1_late_800`, save at least 5 net-cost units per 1,000 events
   against both default E-SR and each applicable certificate/restart comparator (PFA-SR, RMM,
   E_rb, E_swcert, never-switch), with paired 95% intervals below zero. Compare costs with the
   complete loss/label/switch decomposition.
4. **Scope gates:** on independent `F0_null`, the one-sided 95% Wilson upper bound on any promotion
   must remain `<=0.05`. On `F0_better`, `F3_reversal_800`, and `F3_reversal_1200`, candidate mean
   excess cost versus never-switch and default E-SR must each be no greater than 5 units per
   1,000 events. Report promotion/rollback timing, labels actually used, and all adverse results.

All gates are conjunctive. A pass permits a separately frozen real-data replay but does not create
novelty. A result explained by an ordinary pacing configuration or a conventional dynamic-budget
baseline is an existing-method application finding. A failure stops this candidate; do not tune
`k` after seeing it.

## Calibration command

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srrSR:pace_k0.5:gated_deployment \
  --seeds 1000 --seed-base 7110601301 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_tail_pacing_20261106/calibration
```

Do not run the alternative-regime command unless calibration passes and the evaluation amendment
is committed.
