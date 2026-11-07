# Frozen confirmation protocol (checkpoint D) — written and committed BEFORE running

**Data:** G5 with seed block 90000+, 600 seeds per cell, **8 deployed-model conditions** (the 6 development conditions plus two never run: `biased_neg` b = −0.8 and `over_subgroup` a = 2, c = −3) × shifts {none, prior1, concept2, **concept1.5** (new)}; T = 2000, t0 = 700, delay 5, label rates 10% and 20%, threshold 1/α (α = .05). Nominal risks from each condition's own pre-shift stream. Roles from ground-truth decision harm ≥ 0.10 (computed by population simulation per condition/shift, not by detector outcome). Fresh seeds are not shared with the development run (80000+).
**Finalists (frozen from `outputs/h2c_next/dev_summary.csv`, g5_dev.csv):** F1 = H2c (`pp_cost_guided` guided_disc, γ = .995); F2 = C3 guided ONS (`guided`); F3 = C6b multi-horizon guided (`pp_cost_multi`, guided=True).
**References (cost null):** C0 cost parent, C1 cost discounted (γ = .995), C2 cost ONS, C7a cost SR (empirical threshold, null-calibrated on the cell's own null stream). **Diagnostic references (Brier null):** HG_unifcap, Brier ONS.
**Scoring:** per cell harm power (alarm ≥ t0), benign/null false alarm (alarm before t0 if harmful; any alarm if the cell is benign or null). Paired differences are computed per harm cell over seeds, then averaged over harm cells; the interval is a two-level bootstrap (resample cells, then seeds within cell; 4000 resamples).
**Hypotheses (decided now, reported pass/fail, no re-run, no retuning):**
- D1: F1 − max(C1, C2) mean paired harm-power difference ≥ +0.05 at **both** label rates, and the lower bound of the 95% interval > 0.
- D2: F1 ≥ F2 − 0.02 and F1 ≥ F3 − 0.02 at both label rates (non-inferiority of the cheaper H2c vs the other finalists).
- D3: null-cell false alarm ≤ 0.07 for F1, F2, F3 in every null cell, and pooled benign-cell false alarm ≤ 0.07.
- D4 (descriptive): F1 vs C7a power and false alarm; F1 vs Brier references on benign false alarm.
Legacy exit condition and every earlier frozen verdict untouched. Real data is not part of this protocol.
