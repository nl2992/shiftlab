# P2-NAD claim-to-evidence map

Evidence classes:
- **R**: registered confirmation (`07_CONFIRMATION.md`)
- **D**: development
- **P**: proof (`05_VALIDITY_AUDIT.md`, internal only, no external review)
- **Desc**: post-registration descriptive

| # | Claim (wording to use) | Evidence | Class | Status |
|---|---|---|---|---|
| C1 | NAD's envelope certificate bounds false promotion by α for every process in the per-step class M̃(ρ̄) (Markov persistence ≤ ρ̄), with predictable spacing and restart-safe conditioning | P1 | P | Supported; needs external proof review |
| C2 | NAD-2S (envelope on a sign-independent flagged stream + unbounded-ρ UI, Bonferroni) keeps level α on its claimed class | P5; H4: .002 / .002 at n=500 | P + R | Supported |
| C3 | Within the dependence-robust class, NAD-2S is ~3% cheaper than A5b and D5 on synthetic dependent and iid alternatives | H1 −2.9% [99% CI −13.8, −8.8]; H3a −3.1% | R | Supported (small effect) |
| C4 | That advantage does **not** transfer to weakly dependent real replacement streams | H2 +0.1%, H3b +0.0% (ties) | R | Must be stated |
| C5 | NAD-2S passes the Tier B gate on all eight synthetic nulls (harm UB ≤ 5) | H5: max UB 1.40 | R | Supported |
| C6 | Cheaper certificates buy their cost with marginal-null validity: author-endpoint MOPE promotes .25–.32 on ρ=.95 nulls and .15 pooled (4/5 datasets above α) on real twins; NAD-2S .15 and .037 | 07 frontier; twin v3 | R + Desc | Supported |
| C7 | On real twins, those invalid promotions are economically harmless (decision harm ≤ +0.8, often negative) | 07 twins; replicates P2 F2 / H8 | R + Desc | Supported. **It weakens the economic motivation for robustness on real data** |
| C8 | The envelope bet is growth-optimal against M̃(ρ̄), giving the information rate R*(ρ̄); the price of robustness PoR = R*_iid / R*(ρ̄) explains most of the A5b−QSG gap (F5) | P3; `info_rates.py` | P | Supported for the relaxed class only. No bound for the stationary class |
| C9 | Fixed-edge envelope mixtures degrade gracefully when ρ > ρ̄. Bounded-ρ UI and plug-in (Kelly) bets do not (.90–.95 / .75 promotion on ρ=.95) | dev2, smokeK | D | Empirical only. The drift argument does not explain it (`misspec_drift.py`) |
| C10 | The anytime dependence-robustness value is valid (P4) | P4 | P | Implemented. Not evaluated as a decision aid |
| C11 | The payback arm bounds non-payback promotions | P2 | P | Proof only. H6 (harm ≤ 1) failed empirically at r95, which is out of class |
| C12 | The author-endpoint MOPE port matches author code (width ratio 0.95–1.00); our earlier quad port was 1.3–1.4× wider | `_mope_native.md` | D | Supported. A benchmark fidelity correction |

## Claims not to make

- That NAD beats the strongest SOTA on cost. Author-endpoint MOPE and the V1 front-loaders are
  cheaper on synthetic data (by 1.4–13%) and on real data (by 0.6–2.2%).
- That robustness pays economically on real data (C7).
- Any validity on hidden-state or heavy-tailed semi-Markov nulls, or on bike_hour twins.
- Any statement that a delay is a recorded label-release time. All delays are imposed.
