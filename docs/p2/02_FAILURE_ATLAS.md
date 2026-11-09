# P2 Failure Atlas (development, 2026-11-09)

Evidence: dev screen `outputs/p2/dev1` (seed base 2026110901, 40 seeds × 14 regimes × 43
policies; not in Git). Table: `outputs/p2/dev1_table.txt`, from `scripts/p2/analyze_dev.py`.
Contract: T=2000, B=200, c_q=.05, c_s=5, α=.05, delay 100. J is the mean over the six Tier B
alternatives. Decision harm is −db (loss + switches vs never-switch; labels excluded). These are
development numbers, 40 seeds; standard errors for J are about 2–4 per regime.

## Reference points

| Policy | Claims | J_alt | Worst null promotion | Max mean decision harm on nulls |
|---|---|---|---|---|
| economic_replacement | V3 (none) | 331.5 | .975 (WP2_sm) | 6.58 |
| D2 | V1 | 340.0 | .575 (r95) | 5.12 |
| QSG | V1 | 342.2 | .700 (r95) | 6.92 |
| gated_adaptive_range+front | V1 | 349.9 | .450 (hs) | 1.57 |
| choe_ramdas_eb+front | V1 | 353.3 | .425 | 1.93 |
| SMCS+retain-incumbent | V1 | 360.6 | .375 | 3.27 |
| gated_adaptive_range | V1 | 387.3 | .300 (hs) | 0.12 |
| discern_design_floor | V1 | 391.9 | .150 | 2.25 |
| A5b | V2 (Markov, any ρ) | 397.8 | .475 (hs) | 0.00 |
| D5 | V2 | 397.0 | .450 (hs) | 0.00 |
| QSG-env8 | Markov ρ̄=.8 | 397.0 | .350 (hs) | 0.00 |
| CONTROL_never_switch | — | 420.0 | 0 | 0 |

## Failure cells and mechanisms

| ID | Failure | Where | Mechanism (diagnosed) |
|---|---|---|---|
| FA1 | V1 certificates promote on persistent marginal nulls | QSG .70, D2 .575, GAR+front .375, SMCS .25 on F5 r95; similar on order-2 | Their null is conditional: under persistence the challenger *is* conditionally ahead during an excursion. Out of contract, not a violated theorem (F1/F2) |
| FA2 | Robust (V2) certificates cost about as much as never switching on dependent alternatives | A5b 420.1 (r8), 425.0 (r95) vs never 414.9/419.8; QSG 338/338 | Information-theoretic in part: under M(ρ̄) the per-event information rate is 2.0e-3 vs QSG's spurious 28.6e-3 (`docs/p2/05_VALIDITY_AUDIT.md` P3). A5b's UI also allows ρ→1, which leaves 1→1 transitions with no evidence |
| FA3 | The envelope precursor wastes its budget | QSG-env8 421.5 on r8 (= never) | Front-loading queries every disagreement (gap ≈ 5). After a favourable outcome u = 1/2 + .8^5/2 = .66 > p_alt, so ~65% of labels carry zero evidence and the budget runs out at t ≈ 1000 |
| FA4 | Robust certificates are not robust to slow hidden states | A5b .475, D5 .45, env8 .35 on WP2_hs_null | Latent flips every ~500 events: outside first-order Markov with any ρ, because conditionally on the latent state the sign is not Markov in z alone |
| FA5 | Everything promotes on heavy-tailed semi-Markov nulls | 5–30% for all certified rows | Pareto(1.5) run lengths have no geometric mixing envelope; outside every declared class |
| FA6 | The cheapest policies have no guarantee | economic_replacement 331.5, promotes .73–.98 on nulls | Uncertified; decision harm per null episode is small (≤ 6.6) because a null promotion costs one switch |
| FA7 | Robust certificates pay a large tax on iid alternatives when the envelope is not adaptive | NAD-m80-g10 402 vs A5b 367 on F0_better | The envelope charges ρ̄^g on every post-favourable label even when ρ = 0; UI's null supremum adapts to ρ̂ ≈ 0 |

## Implications for method design

1. **FA3 is a design failure, not an information limit.** Spacing queries by the envelope (NAD) is
   the direct repair. Dev1: NAD-m80-g10 has J 382.4 vs env8 397.0, A5b 397.8 and D5 397.0, with in-class null
   promotion ≤ .025 and max harm .75.
2. **FA2 is largely intrinsic.** No M̃(ρ̄)-valid certificate can match QSG on persistent
   alternatives. The defensible target is the robust frontier (cost at a stated class), plus making
   the class an explicit, reportable parameter (the robustness value, P4).
3. **FA7** motivates evidence that adapts to ρ inside a bounded class: bounded-ρ UI, or envelope+UI
   mixtures. These are screened in dev2.
4. **FA4–FA5** fall outside every declared class. Report them as stress tests; do not claim
   validity there.
5. **FA6 / Tier B** motivates the payback variant (PB). It certifies that a promotion pays back
   over the remaining horizon, a sequential analogue of the Tier B gate.
