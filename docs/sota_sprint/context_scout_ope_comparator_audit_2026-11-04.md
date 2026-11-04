# Contextual scout: source-matched OPE comparator audit

**Date:** 2026-11-04. **Status:** corrected source-matched construction identified; implementation and results still outstanding.

## Why this is the next gate

The exact-uniform Markov confirmation passed against pooled-rank and nested-volume selection, but
those internal baselines do not represent the strongest known anytime policy-value methods. A direct
prior is Waudby-Smith et al., [*Anytime-valid off-policy inference for contextual bandits*]
(https://arxiv.org/abs/2210.10768). Its paper covers time-uniform confidence sequences for fixed
and time-varying average policy values, adaptive/predictable logging policies, bounded rewards, and
arbitrary stopping. Its time-varying formulation explicitly allows conditional policy values to
change over time. Context processes may be dependent; the guarantee is expressed through the
conditional reward means. [Karampatziakis, Mineiro & Ramdas]
(https://proceedings.mlr.press/v139/karampatziakis21a.html) is an earlier nonasymptotic OPE-CS
baseline, with an application to gated deployment. Ryu et al.'s [Betting and Freezing]
(https://proceedings.mlr.press/v291/ryu25a.html) is another source for offline policy selection
and variance-adaptive betting under a fixed behavior policy.

These papers do not automatically prove future deployment benefit under a changed environment.
They do establish that time-uniform inference for a selected contextual policy is not itself a new
contribution. The comparator must use the same estimand and feedback, and any future deployment
claim must state the stability assumption that connects certification-period value to deployment.

## Mapping the registered experiment to OPE

After the first scout half, the selected rule is a fixed mapping `g(x)` from the observed context
group to one candidate classifier (or incumbent fallback). During certification, let
`Z_t(g(X_t))` be incumbent cost minus the selected classifier's cost, including the context-specific
action but before the amortized switching charge. With `M=max(FN,FP)=5`, normalize

```text
R_t = (Z_t(g(X_t)) + M) / (2M) in [0,1].
```

The label request `Q_t` is a predictable logging action with known propensity `q_t=budget_rate`.
For the OPE encoding, the target policy requests a label on every eligible event; a skipped request
has a defined zero acquisition reward, and a queried request reveals `R_t`. The direct estimator is
`Q_t R_t/q_t`. A pre-monitor reward prediction `rhat_t` can supply the source paper's doubly robust
pseudo-outcome. Use a threshold

```text
tau = 1/2 + switching_cost / (2 M * deployment_horizon),
```

so a lower confidence sequence crossing `tau` tests positive net decision gain. Stop both methods at
the same hard-budget prefix. Once the cap is exhausted, there is no further labeled outcome for
either certification process.

The selected mapping is fixed before the certification half and is therefore predictable with
respect to the certification filtration. For a time-varying context process, compare against a CS
for the average conditional policy value over the same certification events. Do not treat a CS for
that historical average as a future-deployment guarantee without an explicit stationarity or
conditional-value assumption.

## Implementation and comparison requirements

1. Reproduce the source paper's applicable one-sided time-varying OPE lower CS from its stated
   bounded-reward, predictable-logging construction. Prefer its empirical-Bernstein and LIL
   boundaries; include a doubly robust variant with the model predictions trained before
   certification. The repository already contains an LIL bound and bounded DR pseudo-outcome
   implementation in `src/shiftlab/dive/anytime_policy_identification.py`; verify its exact theorem
   correspondence, clipping/truncation, and adaptive-time assumptions before reuse.
2. Feed the same frozen selected mapping, certification contexts, query uniforms, queried labels,
   costs, hard-cap prefix, alpha, and switching threshold to the OPE CS and the existing fixed-mixture
   process. Any clipping, model fitting, or truncation parameter must be frozen from the scout/validation
   data and charged to the same information split.
3. On new development seeds, compare (a) false promotion under the registered zero-gain null,
   (b) promotion probability and time on positive alternatives, and (c) evaluator-known future net
   utility. Report the actual bound widths and label counts, not only mean utility. Use identical
   context schedules and disclose where the OPE theorem's conditional-value assumptions diverge from
   the deployment estimand.
4. If the OPE CS matches or exceeds the contextual scout, close the current algorithmic lead. If a
   gap survives, freeze a fresh calibration/confirmation protocol and then seek an aligned real-data
   or deployment replay before using novelty/SOTA language.

## Decision

The contextual scout is now a confirmed synthetic improvement over internal rank baselines under
an exact propensity contract. It remains a research candidate. The unresolved source-matched OPE
comparison and future-value transport assumption prevent a claim that it improves on existing SOTA.

## Corrected source-matched construction — 2026-11-04

The earlier proposed encoding `Q_t R_t/q_t` as the reward is withdrawn: that value can exceed one and is not the bounded raw reward required by the existing DR/LIL helper. A valid direct contextual-bandit encoding is available.

Represent each eligible certification event with actions `A_t=1` (query) and `A_t=0` (skip), predictable logging probabilities `h_t=(1-q_t,q_t)`, and target policy `pi=(0,1)` (always query). Let `Z_t(g(X_t))` be incumbent cost minus the scout-selected classifier's cost before switching charge. The selected mapping `g` is fixed after scout. Set `M=max(FN,FP)+switching_cost/deployment_horizon` and define the query reward as `R_t(1)=1/2 + (Z_t(g(X_t))-switching_cost*I[g(X_t) is a selected candidate])/(2M)`. Set the skip-action potential reward to zero; it is immaterial because the target policy puts zero mass on skip. This reward lies in `[0,1]`, and target value above `1/2` is exactly positive average net gain. Observed query rewards are revealed only when `A_t=1`, as in the standard contextual-bandit protocol.

Use the existing `bounded_dr_pseudo_outcomes` with raw bounded rewards, target policy `(0,1)`, logging probabilities `(1-q,q)`, and a fixed predictable reward model, initially `rhat=(0,1/2)` for skip/query. Choose and freeze a fixed truncation `k` (e.g. 1). The helper implements the source DR truncation and returns lower pseudo-outcomes bounded below by `-k`; feed those to `lil_value_bounds` at alpha 0.05 and compare its lower bound to `1/2`. This applies Proposition 3's LIL CS, which permits time-varying average conditional policy values. The hard-cap prefix is a stopping time based on query actions, and the source is time-uniform. Use the same certification query uniforms and selected mapping as the fixed-mixture arm.

This CS targets average conditional certification-period value. Markov dependence is allowed by the paper's exogenous context formulation, but future deployment value still requires a transport/stability assumption. The direct comparison should report promotions, crossing time, bound width, queried labels, false promotions under the registered null, and evaluator-known future utility on a fresh development block. It remains an implementation/result obligation and does not itself support an SOTA claim.

Source check: [Waudby-Smith et al. (2024), Section 3, Theorem 2 and Proposition 3](https://arxiv.org/pdf/2210.10768) specifies bounded `[0,1]` rewards, predictable logging, time-varying average conditional policy values, DR truncation with a `-k` pseudo-outcome lower bound, and arbitrary-stopping confidence sequences.


## Development comparison results — 2026-11-04

Two disjoint 60-seed, 108-cell CPU development blocks completed with 25,920 rows each and zero hard-cap violations. The first used constant `rhat=0.5` (protocol SHA-256 `435afdd8c1c148f0a98dff5fc1d3094738e5cd4518b2744af9742a697c5fe908`); the second used the frozen validation-trained group predictor (SHA-256 `d2568e635458a6a75f0edf316c2c13982f6e95952d97bcd83168c007886c27f5`). Analysis verifies row keys, protocol hashes, OPE fields, and cap integrity in `scripts/analyze_scout_context_ope_markov_comparison.py`; the generated report is `outputs/scout_context_ope_markov_comparison_audit/report.md`.

Neither LIL variant crossed the 0.5 threshold on any of 6,480 eventwise streams, including positive alternatives; the final average lower bounds were about 0.421 and mean interval widths about 0.167. The matched fixed-mixture gate promoted 7.99% and 7.64% of positive rows, with mean evaluator-known net gain 12.90 and 12.66 respectively; zero-signal promotions were 0/2,160 in both blocks. These null counts are diagnostics, not calibration. The OPE gate consequently had zero deployment utility, and the paired positive-cell utility deltas favor fixed-mixture by -12.90 (seed-cluster descriptive 95% interval [-16.07,-9.87]) and -12.66 ([-15.60,-9.85]). The validation predictor did not materially tighten the boundary.

Decision: the source-matched OPE-LIL implementation is valid for its average conditional certification-period estimand under the registered predictable query logging, but it is too conservative on this design and does not outperform the fixed-mixture monitor. This closes the claim that the contextual scout already improves on an established anytime OPE CS. It does not establish superiority of the fixed-mixture procedure over SOTA, nor does it establish future-value transport. The existing contextual scout result remains an internal-baseline synthetic finding. Do not tune these blocks further; any alternate boundary (such as the paper's empirical-Bernstein CS) needs an explicit source mapping and a new frozen development block.

### Newer optimal-policy-identification prior-art audit — 2026-11-04

The June 2026 preprint [Anytime-valid Optimal Policy Identification](https://arxiv.org/abs/2606.17515) is a close finite-class competitor and is already represented in the repository's OPI reproduction. It builds a simultaneous policy-value confidence set and eliminates policies. Its formal setup assumes time-invariant policy values `nu_t(pi)=nu(pi)` (Section 2.2, lines 103–105 of the HTML source), so its fixed-value optimal-policy theorem does not directly cover the persistent Markov profiles used here. For IID context profiles (`rho=0`) the assumption may hold under the simulator, and a matched OPI class comparison is appropriate. For persistent profiles, the cited Waudby-Smith time-varying CSs estimate prefix-average conditional values; a per-time prefix-optimal set can be obtained by simultaneous coverage, but this is not the same as Molitor's fixed-optimal-policy sample-complexity theorem and is not itself a novelty claim. A next comparator should first decide whether the estimand is the best fixed policy over the certification prefix or positive value of a fixed selected policy, then match that estimand explicitly. The source also reinforces that finite-class anytime policy identification is established prior art, so contextual policy selection alone is not a novelty delta.

Reproduction note after adding the explicit predictor configuration: to reproduce v1 with current code, pass `--scout-ope-reward-predictor constant_half`; v2 uses `--scout-ope-reward-predictor validation_group_mean`. This CLI choice matches the predictor recorded in each frozen protocol and preserves both protocol hashes.

### Empirical-Bernstein OPE comparator — 2026-11-04

The source empirical-Bernstein mixture CS from Waudby-Smith et al., Theorem 2, is now implemented in `anytime_policy_identification.py` using the paper's predictable lagged-mean variance process and 48-step inversion. The simulator calculates it alongside the DR-LIL CS on the identical cap-limited pseudo-outcomes. The frozen protocol chose `rho=0.17817019505784423` using the paper's suggested expression with design target `V*=250`, before the fresh block `21,900,120–21,900,179`; no tuning used prior or current outcomes. The result and reproduction details are in `docs/scout_context_ope_empirical_bernstein_gate_2026-11-04.md` and `outputs/scout_context_ope_eb_markov_development_v1/`.

All 25,920 expected rows completed with zero budget violations. In 6,480 eventwise streams, the EB lower bound never crossed `0.5`, including 4,320 positive-signal streams. EB narrowed mean final interval width from `0.1709` (LIL) to `0.1286`; mean lower bound improved from `0.4177` to `0.4389`, still below the net-benefit threshold. Fixed mixture promoted `8.80%` of positive streams and obtained mean evaluator-known future gain `14.28`; OPE-EB obtained zero. Zero-signal promotions were 0/2,160 for EB and 6/2,160 for fixed mixture, diagnostics only. Therefore EB closes the remaining source-boundary efficiency question for this synthetic horizon: it is tighter but not deployable at the specified alpha/budget. Do not tune this block or claim fixed mixture is superior to SOTA; future value remains separate from the paper's average conditional certification-period estimand.
