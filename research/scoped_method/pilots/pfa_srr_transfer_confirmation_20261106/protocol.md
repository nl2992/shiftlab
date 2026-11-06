# PFA-SR matched-host synthetic transfer confirmation

**Status:** prospective confirmation protocol for a published-baseline application. The prior
30-seed PFA-SR screen is development evidence only and had a cross-host comparator flaw; it is not
used as confirmation. The current method is the 2026 PFA-weighted e-Shiryaev–Roberts construction,
not a new detector contribution. This experiment asks whether that established detector, when
attached to the same deployment hosts, improves net cost in a scoped persistent-improvement region.

## Frozen claim

In synthetic settings with iid conditional label feedback, a persistent positive challenger
advantage, and a binding label budget, attaching PFA-SR to the existing Gated deployment host will
reduce net cost by at least 5 units relative to both (i) the strongest corrected existing adapter,
`xu_acquisition_only`, and (ii) same-host uniform-start RMM, while keeping null promotions within
the registered 9.36% screening tolerance. No claim covers reversal, serial dependence, or general
real-world transfer yet.

The PFA-SR definition is fixed in `scripts/sota_sprint/pfa_srr_baseline.py`: signed disagreement
outcomes `X_n`; fixed bets `{0.15, 0.30, 0.50}`; start weights
`pi_s = 1/[2 s log(e s)^2]`; alarm threshold `1/alpha`. The weights sum to at most one by the
decreasing-series integral bound. The iid conditional null is `E[X_n | F_{n-1}] <= 0`; the detector
controls any alarm in one monitoring run by its allocated alpha. The deployment wrapper splits
first-promotion alpha between base and detector and geometrically spends subsequent promotion
alpha. Delay and acquisition are observable only through ordered feedback release. No future or
oracle data are passed to policies.

## Frozen regimes and budgets

Use 100 fresh matched streams per cell with seed base `2026110628`. All streams have horizon 2,000,
switch cost 5, label price 0.05, and alpha 0.05. The label budget is 200 except the delayed/scarce
cell, which is run at budget 100. The four new profiles are added in
`scripts/sota_sprint/pfa_confirmation_spec.py` before outcomes:

| Regime | Event-level advantage / release | Budget | Purpose |
|---|---|---:|---|
| `PFA_confirm_persistent` | `0.25 × (2×0.68−1) = 0.09` throughout | 200 | persistent alternative |
| `PFA_confirm_near` | `0.25 × (2×0.57−1) = 0.035` throughout | 200 | weaker persistent alternative |
| `PFA_confirm_delay_scarce@B100` | `0.22 × (2×0.67−1) = 0.0748` throughout, 400-event delay | 100 | delayed labels and scarce budget |
| `PFA_confirm_null` | zero throughout | 200 | correctly specified iid conditional null |

Also replay existing `F3_reversal_800` on the same fresh seed base as a predeclared adverse
transport diagnostic; it is outside the scoped claim and does not determine the target-cell gate.

## Frozen comparator panel and decision rule

Compare `PFA-SR:gated_deployment` and `PFA-SR:gated_adaptive_range` against:

- `xu_acquisition_only` (strongest previously corrected adapter in the persistent and late cells),
- same-host `rmm:gated_deployment+RMM` and `rmm:gated_adaptive_range+RMM` (isolates the start-prior
  detector effect),
- `E_rb:gated_adaptive_range`, `E_swcert`, `E_srrSR:gated_deployment` (ARL-only diagnostic), and
  `CONTROL_never_switch`.

Primary endpoint is paired net cost = predictive loss + 0.05 × labels requested + 5 × switches.
For each target alternative, require a ≥5-unit mean saving with paired 95% interval entirely below
zero against both `xu_acquisition_only` and the same-host RMM. Require the PFA-SR promotion rate on
the null to be ≤0.0936 and report its Wilson 95% interval. With 100 null streams this is a screening
check, not a substitute for the mathematical PFA argument. Report full per-cell loss, labels,
switches, promotion and rollback timing, and net-cost decomposition, including every adverse result.
No method is modified after outcomes. A result against only the ARL-only SR baseline cannot pass.

## Command

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes PFA_confirm_persistent,PFA_confirm_near,PFA_confirm_delay_scarce@B100,PFA_confirm_null,F3_reversal_800 \
  --policies 'CONTROL_never_switch,xu_acquisition_only,E_rb:gated_adaptive_range,rmm:gated_deployment+RMM,rmm:gated_adaptive_range+RMM,E_swcert,E_srrSR:gated_deployment,PFA-SR:gated_deployment,PFA-SR:gated_adaptive_range' \
  --seeds 100 --seed-base 2026110628 --workers 4 \
  --out research/scoped_method/pilots/pfa_srr_transfer_confirmation_20261106/run
```

Prior art: Shin, Ramdas & Rinaldo, [*E-detectors: A Nonparametric Framework for Sequential Change
Detection*](https://nejsds.nestat.org/journal/NEJSDS/article/59/text); Shin et al.,
[*Non-partitioned e-detectors for nonparametric sequential change detection*](https://arxiv.org/abs/2607.28322),
§2.2, Theorem 2.3. The start-weighted PFA construction is established prior art. A pass would
support a scoped benchmark/application claim only until independent real-data transfer and a
targeted originality review are completed.
