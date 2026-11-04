# Versioned promotion and rollback: dual-monitor development specification

**Status:** exploratory specification written alongside/after the first development run. It is not a
preregistered or confirmatory protocol. No method or SOTA claim is established.

**Real-data cost-result warning:** the five-stream results cited below inherited the v2 training
label leakage in the charged runner and are invalid as hard-budget cost comparisons. The independent
synthetic stress screen is unaffected. Corrected real-data results are in
[`versioned_real_provenance_fixed_results.md`](versioned_real_provenance_fixed_results.md).

The initial five-stream results below used the unreserved implementation. A later 100-seed stress
screen tested both that version and a per-test budget reservation; the reservation changes query
eligibility and label use. The later screen supersedes the initial results for development
retention decisions: [`versioned_stress_screen_2026-11-04.md`](versioned_stress_screen_2026-11-04.md).

## Candidate

For each predictably activated version `v`, freeze its deployed baseline `b_v`. Test promotion on
fresh paired losses only. For a queried event `t`, define

```text
G_t(v) = loss_t(b_v) - loss_t(v) in {-1, 0, +1}.
```

Positive values favor the challenger. The promotion e-process is a fixed mixture of products
`prod_t (1 + lambda G_t(v))`, with fixed `lambda in [0,1]` and mixture weights summing to one.
After promotion at a predictable release-time stopping time, start a fresh rollback process against
the same cached baseline using `-G_t(v)`. A rollback signal returns deployment to `b_v` and retires
version `v`, so each version has at most one promotion and one rollback decision.

For fixed version weights `w_v > 0` summing to one and total error budget `alpha`, allocate
`alpha_v^+ = alpha*w_v/2` to its promotion test and `alpha_v^- = alpha*w_v/2` to its rollback test.
Across the predeclared finite version set, the sum of all decision budgets is at most `alpha`.
Crossing thresholds are `1/alpha_v^+` and `1/alpha_v^-` respectively. The rollback test starts
after promotion; pending promotion labels issued before that time update promotion evidence only.

## Shared query rule

At each event, request a label if a current promotion comparison or the deployed version's active
rollback comparison disagrees. Freeze all active `(test kind, version, baseline, issue time)` pairs
at issue. The returned label updates each listed test, including a zero increment when that pair's
models agreed on the queried event. Each physical label is charged once to the common hard budget.
When a later version is active, a query can therefore update both its promotion process and the
current deployed version's rollback process.

The selected query event and all compared predictions must be predictable before the current label.
The error guarantee requires, for every active pair, a conditional mean null *after conditioning on
the queried-event union*: `E[G_t(v) | full released-label history, predictions, query=1] <= 0` for
promotion and `E[-G_t(v) | same information] <= 0` for rollback. Under these strong directional
nulls, `1+lambda G` is nonnegative and has conditional expectation at most one. Fixed mixtures,
Ville's inequality, and the union bound over the allocations above control any false promotion or
false rollback by `alpha`. Fixed, noninformative delay preserves the issue-order filtration. This
does not cover a marginal-only null, outcome-dependent delay, unregistered pair reuse, or infinite
versions without a summable allocation.

This guarantee is distinct from preventing every harmful promotion: an alpha-level false promotion
can still occur, and rollback can only limit subsequent harm after enough queried evidence accrues.
It also spends query budget on post-promotion monitoring, so it may lose power or acquisition
efficiency. Both effects must be reported.

## Literature boundary

The nearby *Retrain, Alert, or Rollback?* framework (Sadeghian et al., arXiv:2611.02251, posted
2026-11-01) has a two-stage canary and rollback. Its quality rollback rule compares a finite
canary-window accuracy difference with a margin and is explicitly described as an operational
screen, not a significance test. It does not report a paid-label hard-budget contract. The possible
difference here is the anytime error allocation and shared delayed-label stream, not the general
idea of canary rollback.

* [RAR paper](https://arxiv.org/abs/2611.02251)
* [The Challenger: sequential learning-curve model switching](https://arxiv.org/abs/2512.18390)
* [Sequentializing a Test: Anytime Validity is Free](https://arxiv.org/abs/2501.03982)

These ingredients are individually established. A source-level novelty audit is still required to
determine whether the joint guarantee and paid-budget implementation are already covered elsewhere.

## First development screen

Runner: `scripts/sota_sprint/versioned_real_dev.py`. Records:
`outputs/sota_sprint/versioned_real_rollback_dev/records.json` (ignored). It uses the same five
selected chronological streams as the charged versioned-challenger screen, with one update and one
deterministic policy run per dataset. The rollback variant was added after the initial results were
inspected, so this is a post-hoc development screen. It is evidence about feasibility and the
household-power reversal only, not an unbiased estimate of comparative performance.

| Policy | Mean net cost | Mean paired difference vs original gate (SE) | vs RMM (SE) | vs front certificate (SE) | vs Model Picker (SE) |
|---|---:|---:|---:|---:|---:|
| Original version gate | 436.32 | — | — | — | — |
| Version gate + rollback monitor | 426.79 | −9.53 (11.46) | −37.01 (17.19) | −7.18 (12.71) | +5.88 (16.76) |
| RMM | 463.80 | — | — | — | — |
| Front-loaded certificate | 433.97 | — | — | — | — |
| Version-aware Model Picker | 420.91 | — | — | — | — |

The rollback variant rolled household_power v1 back to the incumbent at event 1,224. Its cost there
was 770.95 versus 826.10 for the original gate. It requested 199 labels including the 100 training
labels; all candidate policies stayed within the 200-label cap. It did not roll back on the other
four streams. Mean cost remains higher than Model Picker and the front-loaded certificate. Five
selected deterministic streams are not an inferential sample; no confidence claim is made from these
standard errors.

## Next required work

1. Independently audit the theorem and code paths, especially version activation, stale pending
   labels, simultaneous pair updates, and rollback after a later version becomes active.
2. Register a fresh development panel with no-improvement, early degradation, late degradation,
   recovery, strong dependence, and null streams, with several independent seeds per cell.
3. Compare under the identical training-plus-query cap to the strongest certified and active
   baselines, reporting rollback latency and harm before rollback as first-class outcomes.
4. Continue only if the method improves net cost over the strongest applicable baseline while
   preserving the proved decision-error allocation. Then freeze a separate validation protocol.
