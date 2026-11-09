# P2-NAD development results

All runs are development evidence. They use `scripts/sota_sprint/wp2_run.py` with the P2 contract
(T=2000, B=200, c_q=.05, c_s=5, α=.05, delay 100) unless a row says otherwise. Raw records are under
`outputs/p2/` (gitignored). Tables come from `scripts/p2/analyze_dev.py`, `paired.py` and
`real_table.py`. Seed bases:

- 2026110901: selection seeds (dev1–dev5)
- 2026110911: neighbourhood sweep, not used for selection
- 2026110921: real-data development

## Rounds on the selection seeds (40 seeds × 14 regimes)

| Round | Dir | What | Outcome |
|---|---|---|---|
| dev1 | `outputs/p2/dev1` | 43 policies: 13 comparators + NAD {m,p}×{80,90,95}×{g0,5,10,20,40,rate} | NAD-m80-g10 is the cheapest certificate with in-class null ≤ .025. No spacing (g0) reproduces env8's budget waste. ρ̄ ≥ .9 is close to never-switch |
| dev2 | `outputs/p2/dev2` | bounded-ρ UI, envelope+UI mixtures, payback PB | UI80/MIX80 are cheap but brittle (.90–.95 on r95, harm ≤ 11). PB80-g10 has zero harm on all nulls |
| dev3 | `outputs/p2/dev3` | envelope + unbounded UI (MIXA), NAD φ, g15 | MIXA at a fixed gap does not recover iid efficiency |
| dev4 | `outputs/p2/dev4` | A5b density rule for NAD / MIXA | MIXA80-ad: iid 374 but dependent cost rises (387.8 overall). NAD80-ad 402 |
| dev5 | `outputs/p2/dev5` | author-endpoint MOPE (`*_native`) | pending |

### Paired J on the six alternatives, NAD-m80-g10 minus comparator (selection seeds, n=240)

| Comparator | Δ [95% CI] | % |
|---|---|---|
| gated_adaptive_range (quad-endpoint port) | −4.89 [−9.57, +0.07] | −1.3% |
| A5b | −15.35 [−20.42, −10.21] | −3.9% |
| D5 | −14.60 [−19.88, −9.31] | −3.7% |
| QSG-env8 | −14.55 [−19.32, −9.82] | −3.7% |
| discern_design_floor | −9.49 [−13.86, −5.16] | −2.4% |
| SMCS+retain-incumbent (V1; .25 on r95 null) | +21.83 [+17.21, +26.61] | +6.1% |
| gated_adaptive_range+front (V1; .375) | +32.54 | +9.3% |
| QSG (V1; .70) | +40.23 | +11.8% |
| never switch | −37.59 [−43.42, −31.97] | −8.9% |

## Neighbourhood sweep (independent seeds 2026110911, 30 seeds, 6 alternatives)

NAD-m80-g10 minus comparator:

| Setting | vs gated_adaptive_range | vs A5b | vs QSG-env8 | vs discern_design_floor |
|---|---|---|---|---|
| base | −9.42 [−14.42, −4.69] (−2.4%) | −12.61 [−18.83, −6.35] | −17.08 | −8.81 |
| delay ×¼ | −10.18 [−15.38, −5.33] (−2.6%) | −11.91 [−18.44, −5.49] | −18.39 | −9.01 |
| delay ×4 | −10.51 [−15.01, −6.32] (−2.6%) | −8.94 [−14.86, −3.05] | −13.16 | −11.19 |
| budget 100 / 400, c_s 1 / 20, c_q .2 | pending | | | |

## Interpretation so far

- Among certificates that stay near α on persistent Markov nulls, NAD-m80-g10 is the cheapest by
  2–4%, and this holds on independent seeds and across delay ×¼–×4. That grades as a small to
  meaningful effect against a quad-endpoint MOPE port that is known to be conservative. The
  author-endpoint comparison (dev5) is the decisive check.
- Against V1 front-loaders (QSG, GAR+front, SMCS), NAD costs 6–12% more. Those methods promote
  on 25–70% of persistent marginal nulls. This is the price of robustness, and P3 shows it is
  largely intrinsic.
