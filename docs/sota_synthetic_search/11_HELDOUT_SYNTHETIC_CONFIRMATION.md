# Held-out synthetic confirmation (part 1: G1 held-out pool)

**Frozen before running:** `configs/sota_search/frozen_finalists_v1.json` (committed in the same commit as this preamble). Finalists were selected on the development pool only; the held-out pool is evaluated **once** and nothing is re-tuned afterwards. The held-out pool has different shift magnitudes, onsets and schedules (recurrent, onset 500 and 1100) and fresh seeds (400 per world, seed block 5000).

Held-out worlds: concept recurrent δ=2.5, concept abrupt δ=1.2 (onset 1100), concept gradual δ=2.5 (ramp 400), subgroup recurrent δ=4, `cov_benign` recurrent δ=2.5, `cov_inform` gradual δ=1.5, `prior` abrupt δ=1.5 (onset 1100), null.

Decision rule: see the frozen file. Results are filled below after the single run.

## Part 1 results: G1 held-out parameters (single run, 400 seeds per world, registry `registry_heldout_g1.sqlite`)

3 harm worlds, 4 benign-shift worlds, 1 null world. Mean over worlds; each cell is one frozen configuration.

| Arm | Label rate | Power (harm) | False alarm (benign) | False alarm (null) | Harm before alarm |
|---|---|---|---|---|---|
| `pprm_tight` (strongest valid baseline) | 0.10 | 0.513 | 0.021 | 0.012 | 162.5 |
| **`HG_brier`** (frozen finalist) | 0.10 | **0.566** | 0.022 | 0.008 | 146.3 |
| Page–Hinkley (empirical) | 0.10 | 0.570 | 0.052 | 0.042 | 157.9 |
| CUSUM (empirical) | 0.10 | 0.514 | 0.076 | 0.032 | 152.4 |
| `pp_cost_tight` | 0.10 | 0.170 | 0.008 | 0.010 | 215.6 |
| `DK_cost` | 0.10 | 0.244 | 0.009 | 0.012 | 206.1 |
| `BD_cost` (marginal control `CTRL_BD_cost` 0.245) | 0.10 | 0.290 | 0.017 | 0.015 | 196.2 |
| `pprm_tight` | 0.20 | 0.715 | 0.042 | 0.012 | 120.4 |
| **`HG_brier`** | 0.20 | **0.801** | 0.051 | 0.010 | **95.5** |
| Page–Hinkley | 0.20 | 0.731 | 0.054 | 0.030 | 126.3 |
| CUSUM | 0.20 | 0.684 | 0.078 | 0.032 | 120.7 |
| `pp_cost_tight` | 0.20 | 0.375 | 0.009 | 0.005 | 185.5 |
| `DK_cost` | 0.20 | 0.482 | 0.010 | 0.008 | 166.9 |
| `BD_cost` (control 0.478) | 0.20 | 0.554 | 0.026 | 0.015 | 151.0 |

Per-world harm power, `HG_brier` vs `pprm_tight`: 10% labels: abrupt δ=1.2 0.185 vs 0.065; gradual δ=2.5 0.945 vs 0.925; recurrent δ=2.5 0.568 vs 0.548. 20% labels: 0.462 vs 0.242; 0.998 vs 0.992; 0.942 vs 0.910. **No harm world is worse.**

### Verdict against the frozen rule
- **HG_brier: improvement over its parent and over the strongest valid baseline `pprm_tight` at both label rates** (power +0.053 and +0.086; benign false alarm +0.001 and +0.009; null ≤ 0.012). At 20% labels it is better than Page–Hinkley and CUSUM on power, benign false alarm and harm before alarm; at 10% labels it ties Page–Hinkley on power (0.566 vs 0.570) and is better on benign false alarm (0.022 vs 0.052) and harm before alarm.
- **DK_cost, BD_cost: improve their parent `pp_cost_tight`** (+0.074 / +0.120 at 10%; +0.107 / +0.179 at 20%); BD's marginal effect over the same-γ control is +0.045 (10%) and +0.076 (20%). **Neither goes beyond `pprm_tight`** (0.244–0.290 and 0.482–0.554 vs 0.513 and 0.715), so they are not improvements over the strongest valid baseline.

### Limits of this part
Only three harm worlds; same generator family, different parameters; the +0.053 gain at 10% labels sits at the registered +0.05 boundary; intervals not computed here (see the paired analysis planned in part 3). Part 2 (a different generator family) follows.
