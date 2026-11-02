# B3+ evaluation protocol

Registered 2026-11-02, before any B3+ policy was run on the locked windows. Method frozen by
`B3_PLUS_METHOD.md`; this file freezes the evaluation. Amendments must be appended with a date
and a reason, never edited in place.

## 1. Relationship to B3

The original B3 artifacts under `docs/promising_directions/results/b3/` are **read-only**. B3+
writes only to `docs/promising_directions/results/b3_plus/`. B3+ reuses B3's cached frozen-pair
per-event losses (`results/b3/losses/*.npz`), so the loss streams are bit-identical and no model
is retrained. The frozen incumbent/challenger pairs, episode boundaries, delays and the seed
base (`20261101`) are inherited unchanged, which makes every B3+ vs P3b comparison paired on
both episodes and query-randomisation seeds.

## 2. Datasets

Central: **spam**, **rialto**, **weather**. Retained as safety checks only: airlines, bank,
elec2, criteo.

**Power, stated up front.** Rialto has 16 locked episodes and is the only properly powered
real-data testbed; it is the principal robustness case. Spam has **1** episode and weather
**3**. Their intervals are bootstraps over the 100 query seeds and are reported with
`bootstrap_level: "seed"` and `low_power: true`. Query-seed replication is not episode-level
evidence and will not be presented as such anywhere, including in the manuscript.

## 3. Configurations (Phase 3.1)

| ID | Change from S0 | Question |
|---|---|---|
| S0 | none: `T=2000`, `B=200`, `c_q=0.05`, `c_s=5`, protocol delay (spam 50, rialto 100, weather 1) | Does B3+ improve the reference result? |
| S1 | `B = 400` | Does more label availability change the ranking? |
| S2 | `c_s = 20` | Does cost awareness become more valuable? |
| S3 | delay x 2 | Is the policy excessively delay-sensitive? |
| S4 | `c_q = 0.10` | Does the acquisition rule economise on labels? |
| S5 | one alternative model pair per dataset | Does behaviour survive a different challenger? |

Six targeted configurations. No Cartesian sweep. Where a configuration already exists in B3 for
an unchanged policy, B3's saved result is reused rather than rerun.

**S5 availability, stated honestly.** Constructing an alternative pair requires the raw data
root, which is a Windows path on another machine (`b3_real_data.RAW`) and is **not present in
this worktree**. S5 therefore runs only if cached alternative-pair losses are supplied at
`{data_root}/alt/{stream}.npz`. If they are not, S5 is reported as **not executed, for want of
data**, and no alternative pair is synthesised or inferred. Alternative pairs, when built, are
selected on train/dev portions only, by the same rule across datasets, and never using realised
locked-window losses.

## 4. Horizon (Phase 3.3)

Main results use the original 2,000-event episodes. A 1,000-event robustness diagnostic splits
each cached episode into two consecutive slices with the budget scaled proportionally
(`B = 100` at S0). Results are stored in separate files and never pooled with the 2,000-event
results. The slices are a diagnostic, **not independent datasets**.

## 5. Policies and baselines (Phase 4)

| Code | Role |
|---|---|
| P0 | never switch — deployable reference |
| P1 | always challenger — **hindsight reference, not deployable** |
| P2 | incumbent-alarm switching — deployable alternative |
| P3b | original certified switching — the method B3+ extends |
| P6 | fixed-sample paired batch test — simpler procedure |
| PCT | point-estimate cost-aware threshold — tests whether *any* cost awareness suffices |
| P4ref | the repository's existing cost-aware persistence rule — the promotion rule's true incumbent |
| P7a / P7b / P7c | B3+ ablations (promotion only / acquisition only / plus persistence) |
| P7 | full B3+ |

Fairness: identical realised loss streams, identical budget, `c_q`, `c_s` and imposed delay,
query-randomisation seeds shared across policies, and no policy may access an unqueried label.
P1's hindsight status and P6's exchangeability assumption are stated wherever they appear.

## 6. Metrics

Primary: `NetCost = DeploymentLoss + c_q * N_q + c_s * N_s`.

Secondary, all tied to the contribution: labels requested, promotion frequency, promotion
timing, switches and rollbacks, headroom capture `(P0 - X)/(P0 - min(P0, P1))` when the
denominator is positive, and the per-episode paired net-cost difference. No further metrics.

## 7. Statistical analysis (Phase 6)

- Paired differences on the same episodes and the same seeds.
- 95% CI by bootstrap over **episodes** (2,000 resamples) when `K >= 5`; over **seeds** when
  `K < 5`, flagged `low_power`.
- Mean cost and percentage change reported together.
- Effect sizes and consistency across S0-S5 reported; both positive and negative outcomes are
  retained in the saved records.

## 8. Phase 1 selection rule, fixed before selection

Selection runs on **dev windows and synthetic streams only**; the locked windows are not read
during selection. Order: (1) net-cost improvement, (2) simplicity, (3) mechanism clarity,
(4) combine components only if the interaction adds measurable value, (5) stop once a useful
contribution exists. The selected variant is then run **unchanged** on the locked windows.

## 9. Pre-registered outcome reading

No minimum effect size is imposed. The reading fixed in advance:

- **Primary claim supported** if, on rialto (the powered testbed, S0), the 95% episode-bootstrap
  CI of `P7 - P3b` lies below 0, **or** `P7` matches `P3b` on cost while requesting
  significantly fewer labels.
- **Conditional benefit** if the advantage appears in the configurations where the mechanism
  predicts it (`S2` large `c_s`, `S4` expensive labels, small-advantage weather, short horizon)
  and is neutral elsewhere. This is an acceptable and reportable outcome.
- **No contribution** if B3+ is indistinguishable from P3b everywhere and from P4ref on
  promotion. In that case the fallback in Phase 9 of the goal applies: the original P3b
  implementation will **not** be rebranded as a new algorithm.

Failures and negative results are recorded in `B3_PLUS_RESULTS.md` regardless of outcome.
