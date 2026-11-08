# Post-confirmation comparator panel (locked before any panel run)

Locked 2026-11-07 in the commit that adds this file. This panel **adds** comparators after the C3
confirmation (`synthetic_confirmation.md`). The C3 result stands as recorded. This panel decides
whether the C2/C3 claim survives the baselines the novelty audit requires
(`novelty_audit.md` §5, §7).

## Comparator families (code `scripts/qsg_methods_search/hurdles.py`, `p1_extra.py`)

Every family except UPF uses EQSDp's evidence, pacing and payback. Only the hurdle differs.

- **wald**: Wald LCB/UCB, λ {.9,.95} × γ {.05,.1,.2,.3}.
- **hoef**: Hoeffding LCB/UCB, λ {.9,.95} × γ {.1,.2,.3,.45}.
- **smarg**: horizon-scaled margin (switch when (adv − κ)·r·(T−t) > c_s), λ {.9,.95} × κ {.05,.1,.2,.3}.
- **dwell**: point-estimate payback that must hold on k consecutive releases, λ {.9,.95} × k {3,5,10,20}.
- **upf**: Regol-style UPF T3 adapter, ported verbatim from
  `origin/claude/shiftlab-methods-strategy-dba13e` with its 13 tests passing. δ {.5,.8,.95} × m {50,100,200}.

## Stage 1: comparator tuning (development)

Seed base 2026110731 (the D3 seeds, where EQSDp arm B was selected), 40 seeds, the 14-regime
family. For each family, select the configuration with the lowest family-mean net cost. That
gives five tuned comparators. This is in-sample tuning in the comparators' favour.

## Stage 2: confirmation (fresh)

Seed base **2026110851**, **100** seeds, the same 14 regimes. Arms: EQSDp A (`EQSDp_l0.95_g0.2`)
and B (`EQSDp_l0.9_g0.2`), frozen since `10ba0237`. Comparators: the 5 tuned family winners,
plus `gongT_w100_m10` and `qiu_delayed_movement` for reference.

**Primary analysis.** Family-mean paired differences for {A, B} × {5 tuned families}: 10
contrasts, two-sided paired t over seeds, Holm-adjusted at .05.

**Claim survives (per arm)** if all 5 of its contrasts are negative and significant after
Holm. **Partial**: list which families it beats, ties and loses to. If an LCB family (wald or
hoef) ties or beats EQSDp, the contribution becomes "a confidence-bound hurdle" rather than "a
Beta quantile", and the paper must say so. If upf ties or beats it, C2/C3 fails as a method
claim.

Secondary: change and guard splits; null switches; per-regime table.

## Not allowed

No retuning of EQSDp. No changing the family, the weights or the selection rule after Stage 1.
