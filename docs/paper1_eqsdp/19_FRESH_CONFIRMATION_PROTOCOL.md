# 19 — Fresh chronological confirmation of the cutoff + E48 + F60 add-on (locked before data)

Written 2026-11-09 on `research/paper1-eqsdp-foundation-2026-11-08`, after PHASE5_REPORT (bde5bbd5).
At the time of writing, no data for the periods below has been fetched, built or inspected. This
document is committed before any build. This is the Stage 4 step of doc 10, applied to the
search60 winner.

## 1. Frozen arms (no retuning after this commit)

| id | definition |
|---|---|
| **EQ+pair** | EQSDp λ.98 γ.3 + hard label cutoff H=1100 + E48 (setting 0: arrival_discount .5, lookahead 50, hazard .002) + F60 (setting 0: bundle 2, horizon 100, hazard .002). This is search60 spec `P2_K2__E48_F60`. |
| **EQ+cut** | `s2armr_H1100` (parent; doc 18) |
| **W+pair** | Wald λ.98 γ.3 + cutoff H=1100 + the same E48/F60 settings (`P4W__P2_K2__E48_F60`) |
| **W+cut** | `s2wald_l0.98_g0.3_H1100` |
| panel | the 25 uncertified comparators of `scripts/qsg_methods_search/analyze_all.py`: 14 ADAPTERS and 11 CONTROLS. Arm R `EQSDp_l0.98_g0.3` is also included. |

The k=2 pair is frozen and the k=3/k=4 variants are not. D40 and B15 were found later, and their evidence is weaker (PHASE5_REPORT).

## 2. Data (built after this commit, sealed, opened once)

- **Sources:** the nine Paper 1 sources (00_SCOPE), using the same `c4_sources/<name>.py` recipe, label definition, features, delay (100), contract and the `c4_build.py` pipeline. The only change is the time window.
- **Window rule** (mechanical, fixed here):
  - **start** = end of the registered C4 window;
  - **end** = start + length of the registered window, capped at **2026-07-01** so that outcomes have at least 4 months to settle before the 2026-11 fetch.
  - The resulting windows:
    - sf, dallas, kc, austin, cincinnati, oakland: 2025-07-01 → 2026-07-01;
    - dc and sandiego: 2025-01-01 → 2026-01-01;
    - montgomery_traffic: its registered window already ends 2026-07-01, so **no later period exists**, and it is excluded in advance.
- **Model pair:** retrained on each new window by the unchanged builder: 20% train-old, 20% train-new, 10% validation, 50% sealed test. No information from the new test halves reaches any arm.
- **Eligibility:** the unchanged C4 gates (validation disagreement ≥ .03, error in [.02, .5], ≥ 35 episodes). A source that cannot be fetched, has changed schema beyond the recipe, or fails a gate is reported as **ineligible**. It is not repaired using test-window information and is not replaced.
- **Registration:** `docs/paper1_eqsdp/fresh_registration.json` records the hashes, episode counts, windows and build times. It is committed before the run.
- **Policy seeds:** 10, with seed base **2026111901**. Seeds are derived as in `sota_nine.py`, and every episode is used.

## 3. Hypotheses and analysis

The statistic is the equal-dataset mean of the per-dataset mean paired episode Δ = J(arm) − J(ref). The 95% CI is a stratified episode bootstrap (2000 resamples, rng seed 0). The secondary analyses are the dataset-level one-sided t-test and the sign count. K is the number of eligible datasets.

- **H1 (primary):** EQ+pair vs EQ+cut. Δ < 0, with the 95% CI upper bound < 0.
- **H2:** W+pair vs W+cut. This tests whether the add-on is portable.
- **H3:** EQ+pair vs W+cut. This compares against the best matched fair reference from doc 18.
- H2 and H3 are judged by their CIs at Holm-adjusted levels (two tests, α = .05). Bootstrap p is computed as 2·min(P(Δ*≥0), P(Δ*≤0)).
- **Accuracy constraint for all three:** ΔL/T ≤ +0.1 pp.
- **Graded size:** substantial ≥ 2%, meaningful 0.5–2%, small < 0.5%. The development estimate was −0.41%, so "small" is the expected outcome if it holds.
- **Descriptive:**
  - EQ+pair vs each of the 25 panel comparators: pooled CI, and per-dataset ≥ SOTA counts using amendment 11's 1% non-inferiority rule;
  - labels, switches, the decomposition, and the CVaR95 of the per-episode excess cost.

**Decision**
- If H1 passes, the add-on claim is confirmed on fresh data, at its graded size.
- If H1 fails, the add-on is reported as a development-only finding. Doc 18 (EQ+cut vs panel, held-out episodes) remains the Paper 1 method result, and this fresh run also reports the EQ+cut vs panel comparison as fresh evidence for it.

No other arms, settings or analyses are substituted after opening. Anything added later is labelled exploratory.
