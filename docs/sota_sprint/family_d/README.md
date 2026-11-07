# Family D: transferable deploy-or-abstain safety architecture (SOTA sprint, Agent D)

Status: development screen only (20 dev seeds, base 2026110501, 9 DEV_ENVS) plus a 300-seed null
check (base 2026110514, F0_null and F5_dep_null_r8). These are screening diagnostics. They are not
validation evidence, and an empirical null rate is not a guarantee.

Code: `scripts/sota_sprint/fam_d.py` (`DeployGate`, `SelectThenMonitor`). Tests:
`uv run pytest -q tests/sota_sprint/test_fam_d.py` (30 passed). Ledger: `ledger.json`. Analyzer
output: `screen1.json/.md`, `null300.json/.md`. Paired ablations: `ablations.json`. Raw records:
`outputs/sota_sprint/D/{screen1,screen1b,null300,null300_cert}` (gitignored).

## Design
- **Host:** an unmodified fast selector port: Model Picker, CAMS with constant policies, or Model
  Selector (causal adapter). The host keeps its query rule, its private RNG stream (it uses the
  same generator names as the native entries), and its learning.
- **Gate:** the incumbent stays deployed until two things hold. First, a started-mixture e-process
  on query-conditional disagreement outcomes must cross `2^cycle/alpha`. Second, the host must
  rank the challenger first.
- **Acquisition:** the gate adds q=1 queries on disagreements only while the cycle is undecided
  and the host prefers the challenger (`host_pref`).
- **Label sharing:** gate labels also reach the host. Each carries the frozen combined
  propensity `u + (1-u) q_gate`, which keeps the host's IPW unbiased.
- **After promotion:** if there is no rollback, promotion is absorbing and all queries stop.

Validity statement (what holds, and its scope):
- **Predictable query decisions.** The host's decision is Bernoulli(u_t). Its u_t depends on a
  posterior built from labels released before t and on the current predictions, and the draw uses
  a private RNG. The gate's decision depends on the host's ranking, its own past evidence and the
  remaining budget. A rule that depends on past labels through a posterior is still predictable.
  Neither rule reads label t.
- **What the bound covers.** Under the conditional null "challenger never better on a queried
  disagreement, given query-time information", Ville bounds P(ever promote) <= alpha, summed over
  cycles. The AND with the host only removes promotions.
- **What it does not cover:** Markov-persistent signs (F5). There, P(z=1 | past) > 1/2 after a
  favourable outcome even when the stationary p = 1/2. The 300-seed check shows exactly this
  failure.
- **D5:** swaps in the A1 evidence process `fam_a.MarkovSUI`. Its null is a stationary Markov sign
  chain with no declared rho bound, and validity is as argued in the fam_a docstring.

## Cost vs null-promotion frontier (dJ vs never-switch, 20 dev seeds; null rates at 300 seeds)
`alt` = mean over F0_better, F9_bursty_better, F7_near_better, F1_late_800. `null` = F0_null,
F0_worse, F5_dep_null_r8. `change` = F3_reversal_800, F4_recurrent.

| policy                     |   alt_dJ |   null_dJ |   change_dJ |   null_prom20 |   null_sw |   labels | F0_null_300   | F5r8_300   |
|:---------------------------|---------:|----------:|------------:|--------------:|----------:|---------:|:--------------|:-----------|
| economic_replacement       |   -64.5  |     14.64 |       44.66 |          0.58 |      0.58 |   198.41 | nan           | nan        |
| model_picker_adapter       |   -58.22 |     32.36 |       39.01 |          0.75 |      5.3  |    86.28 | 273/300       | 283/300    |
| model_selector_causal      |   -55.79 |     33.32 |       35.81 |          0.78 |      4.3  |   198.29 | nan           | nan        |
| D3                         |   -55.71 |     25.94 |       28.79 |          0.77 |      3.03 |   198.39 | nan           | nan        |
| cams_adapter               |   -54.53 |     46.47 |       43.84 |          0.78 |      7.47 |   189.14 | 288/300       | 291/300    |
| online_llm_picker          |   -50.58 |     33.73 |       31.13 |          0.83 |      5.93 |    86.13 | nan           | nan        |
| variance_min_ipw           |   -47.34 |     41.72 |       47.25 |          0.73 |      6.27 |   193.51 | nan           | nan        |
| D1                         |   -36.57 |      5.79 |       46.97 |          0.03 |      0.03 |   121.77 | 5/300         | 53/300     |
| D1-no_and                  |   -36.57 |      5.79 |       46.97 |          0.03 |      0.03 |   121.77 | nan           | nan        |
| D2                         |   -34.9  |      9.94 |       44.19 |          0.07 |      0.07 |   147.16 | 6/300         | 54/300     |
| D1-always                  |   -34.38 |      7.24 |       44.19 |          0.07 |      0.07 |   137.32 | nan           | nan        |
| D1-no_share                |   -34.2  |      5.76 |       46.96 |          0.03 |      0.03 |   122.51 | nan           | nan        |
| D4-no_reserve              |   -33.98 |      6.05 |       47.87 |          0.03 |      0.03 |   172.79 | nan           | nan        |
| D6-D1params:ms             |   -32.87 |      9.8  |       46.8  |          0.03 |      0.03 |   153.17 | 5/300         | 45/300     |
| D4-r10                     |   -32.39 |      5.7  |       47.51 |          0.03 |      0.03 |   166.48 | nan           | nan        |
| QSG                        |   -32.16 |      8.91 |       50.14 |          0.07 |      0.08 |   199.37 | 3/300         | 74/300     |
| D6:cams                    |   -29.35 |      7.68 |       44.6  |          0.05 |      0.07 |   168.73 | 5/300         | 46/300     |
| D2-host_only               |   -28.69 |      9.53 |       38.67 |          0.05 |      0.05 |   140.62 | nan           | nan        |
| D6:mp                      |   -28.67 |      5.13 |       44.52 |          0.03 |      0.03 |   154.42 | 4/300         | 51/300     |
| D4                         |   -28.67 |      5.13 |       44.52 |          0.03 |      0.03 |   154.42 | nan           | nan        |
| D6:ms                      |   -27.65 |      7.65 |       45.56 |          0.03 |      0.03 |   169.16 | 4/300         | 42/300     |
| gated_adaptive_range+front |   -25.51 |      7    |       45.69 |          0.03 |      0.03 |   151.43 | nan           | 20/300     |
| SMCS+retain-incumbent      |   -23.33 |      9.55 |       39.76 |          0.05 |      0.05 |   198.53 | nan           | 25/300     |
| D3-gated                   |   -18.96 |      9.14 |       41.24 |          0.02 |      0.02 |   198.39 | nan           | nan        |
| xu_acquisition_only        |   -18.43 |      9.31 |       38.26 |          0.03 |      0.03 |   194.28 | nan           | 22/300     |
| D1-host_only               |    -8.13 |      4.03 |       27.07 |          0.02 |      0.02 |    78.53 | nan           | nan        |
| D5                         |    -6.85 |      9.81 |       43.32 |          0    |      0    |   176.16 | 0/300         | 1/300      |
| A1                         |    -4.48 |     10    |       43.82 |          0    |      0    |   199.91 | nan           | nan        |
| QSG-env8                   |    -2.67 |     10    |       43.94 |          0    |      0    |   199.94 | nan           | nan        |
| gated_adaptive_range       |    -1.92 |      9.31 |       29.35 |          0    |      0    |   179.32 | nan           | nan        |
| D5-standin_env8            |    -0.82 |      9.81 |       39.2  |          0    |      0    |   181.92 | nan           | nan        |
| CONTROL_never_switch       |     0    |      0    |        0    |          0    |      0    |     0    | 0/300         | 0/600      |

How to read the table:
- The D1-parameter wrapper sits between the fast selectors and the certified published methods.
  - On alternatives it gives up about 20-25 J relative to its host.
  - It beats the best certified published method on F0_better by 15.7 (D1) and 18.2 (D2), and
    on F1_late_800 by 12.0 (D1).
  - It cuts null cost by 44-67 J and null switching from 5-12 to 0.02.
- It fails the registered bound on the rho=.8 Markov null: 53/300 and 54/300 (bound .0936). On the
  same 300 seeds the certified published ports promote on 20-25/300, inside the bound, and QSG on
  74/300.
- D5, the gate with A1 evidence, is the only Family D entry inside the bound on F5 (1/300). Its
  power collapses: alt dJ is -6.9, against -34.9 for D2.

## D6 transfer (same module, same frozen parameters, three independent hosts)
| | MP | CAMS | Model Selector |
|---|---|---|---|
| F0_null promote, 300 seeds: host alone | 273 | 288 | n/a (19/20 dev) |
| F0_null promote, 300 seeds: D6 frozen params | 4 | 5 | 4 |
| F0_null promote, 300 seeds: D1 params | 5 | 6 (=D2) | 5 |
| F5 r8 promote, 300 seeds: D6 / D1 params | 51 / 53 | 46 / 54 | 42 / 45 |
| F0_null dJ vs host (D6) | -45.4 | -69.1 | -37.5 |
| F0_better dJ vs host (D6 / D1 params) | +43.4 / +24.0 | +36.9 / +20.7 | +34.5 / +25.4 |

Transfer holds: the null behaviour and cost profile carry across hosts nearly unchanged. Two
caveats apply:
- The registered D6 parameters (reserve .25 plus rollback) are dominated by D1's. The reserve
  costs +15.6 on F0_better, and rollback does not pay on F3 (-6.6, n.s.).
- `D6-D1params:ms` was added after screen1 to complete the D1-params row, so it is a post-hoc
  entry.

## Mechanism ablations (paired dJ, 20 seeds; full table in ablations.json)
- **Gate front-loading vs pure veto** (D1 - D1-host_only): F0_better -48.1, F9 -49.8. Without
  extra labels the certificate starves.
- **Host-steered vs always front-load** (D1 - D1-always): F1_late_800 -8.6 [-20.0,+2.8],
  F0_null -1.8, F0_worse -2.6. Not front-loading while the host prefers the incumbent saves budget
  for late onset.
- **Host-agreement AND:** inert. Results are identical on every seed in the two-model task.
- **Sharing gate labels with the host:** -4.9 on F0_better (n.s.).
- **Reserve .25:** +15.6 on F0_better. **Rollback:** -6.6 on F3 (n.s.) and +8.4 on F4.
- **A1 vs iid evidence** (D5 - D2): +29.4 on F0_better and +70.0 on F9; null promotion on F5 drops
  from 54/300 to 1/300.
- **D3 monitoring vs native MS:** -11.3 on F0_null. Null promotion stays at 19/20 because the
  initial selection is uncertified.

## Provenance
- **Code versions.**
  - Screens ran at git 39d25ce, with uncommitted fam_d.py (and fam_a.py from Agent A).
  - fam_d.py sha256[:16]: 8cde9c7fa4e9b561 for screen1; 2b045b84b21b7a23 for screen1b and the
    null runs. The only change between them is the added `D6-D1params:ms` entry.
  - fam_a.py sha256[:16]: 3c9f6de5c68a438e for screen1; e17dd2c07b15bf99 for the null runs. Agent
    A edited it between runs, so the lead should re-run D5 with the final A1.
- **Runtime.** The mean is under 0.4 s per episode. D5 reaches 1.54 s on its worst episode.
- **Figures.** None were made: PaperBanana was not used in this pass.
