# 06 — Full SOTA results matrix

Arm B = `EQSDp_l0.9_g0.2` (frozen). Δ = J(arm B) − J(comparator); negative favours arm B.

- **Synthetic**: 04 (fresh seeds, exploratory; 50 seeds × 14 regimes; Holm over 43).
- **Nine**: 05 (retrospective; 759 episodes × 10 seeds; stratified bootstrap with Holm over 43;
  dataset sign count; dataset-level t).
- **SD** = configuration selected on synthetic development seeds; **RD** = configuration selected
  on the 14 real development streams.
- **Fidelity** (02): A source-faithful / B common-contract adaptation / C heuristic inspired by the
  source / int = internal control. No comparator reaches class A: author-parity tests cannot run
  because `vendor_sota/` is empty.

Inventory:
- 18 external method families (S1–S10, e-SR, Shekhar–Ramdas, ARW, online LLM picker,
  variance-min, the Challenger, plus Wald and economic controls);
- 43 policy entries on the nine datasets (counted with the never-switch control, the descriptive
  arm A and the ablation; 25 fixed + 15 tuned configurations);
- 9 datasets plus 1 synthetic family. Nothing was dropped.

## Main matrix

| ID | Method (as implemented) | Fidelity | Synthetic Δ (% cost) | Nine Δ (% cost; neg/9) | Statistical evidence | Verdict |
|---|---|---|---|---|---|---|
| S1 | Gong–Zhang-style paid-observation payback, tuned (SD w100 m10) | C | −8.7 (−2.4%) | −3.7 (−0.8%; 9/9) | synth Holm p<1e-3; nine boot-Holm .02, sign p .004, t-Holm .64 | **WIN** (synthetic meaningful; real negligible) |
| S1 | same, real-dev tuned (RD w800 m20) | C | −23.4 (−6.2%) | +0.9 (+0.2%; 3/9) | nine n.s. | **COMPETITIVE** on real |
| S1 | Gong–Zhang-style untuned | C | −14.9 (−4.0%) | −3.9 (−0.9%; 7/9) | both significant | WIN |
| S2 | Qiu-style blocked fixed-share Hedge | C | −8.6 (−2.4%) | −8.1 (−1.8%; 9/9) | synth p<1e-3; nine t-Holm .024, sign p .004 | **WIN** (small; robust across datasets) |
| S3 | UPF-style T3 switch timing (SD δ.95 m50) | B | −30.1 (−7.8%) | −14.0 (−3.1%; 6/9) | synth p<1e-3; nine boot-Holm .02, t-p .045 (not Holm-robust) | **WIN** (meaningful) |
| S3 | same, RD δ.8 m50 | B | −30.4 (−7.9%) | −12.3 (−2.7%; 6/9) | as above | WIN |
| S4 | Model Picker deployment adapter | B | −25.1 (−6.6%) | −2.0 (−0.5%; 6/9) | synth p<1e-3; nine t-p .41 | **WIN** on economic adaptation (synthetic meaningful; real negligible, not robust). Native objective NOT COMPARABLE |
| S5 | Model Selector causal adapter | C | −21.6 (−5.7%) | −4.2 (−1.0%; 6/9) | synth p<1e-3; nine t-p .14 | **WIN** on economic adaptation (real negligible). Native objective NOT COMPARABLE |
| S6 | CAMS deployment adapter | B | −32.2 (−8.3%) | −7.7 (−1.7%; 6/9) | synth p<1e-3; nine t-p .033 | **WIN** on economic adaptation (real small). Native objective NOT COMPARABLE |
| S7 | DISCERN-style / design floor (±front, ±QCE) | B/C | −34 to −44 | −8.9 to −88.4 (7/9) | — | **NOT COMPARABLE** (certified; arm B 71% false promotion vs ≤3%) |
| S8 | SMCS retain-incumbent / +QCE+front | B/C | −38.8 / −37.7 | −16.8 / −8.7 (7/9) | — | **NOT COMPARABLE** (certified) |
| S9 | Xu acquisition / +front | C | −37.0 / −39.5 | −24.4 / −17.4 (7/9) | — | **NOT COMPARABLE** (certified) |
| S10 | gated certificate; MOPE adaptive range (±front) | B/C | −35 to −39 | −10.2 to −78.9 (7/9) | — | **NOT COMPARABLE** (certified) |
| S11 | Wald LCB hurdle, SD λ.9 γ.2 | int | −0.3 (n.s.) | −0.2 (7/9, n.s.) | p .17 / .32 | **COMPETITIVE** (tie in both) |
| S11 | Wald LCB hurdle, RD λ.97 γ.2 | int | −9.5 (−2.6%) | **+2.1 (+0.5%; 0/9)** | nine boot-Holm .02, sign p .004 | **LOSS** on real (negligible); WIN on synthetic |
| S12 | front-loaded economic econF (SD / RD) | int | −16.2 / −15.0 | −3.3 / −3.0 (1/9) | nine n.s.; econF cheaper on 8/9 datasets | **COMPETITIVE** on real; WIN on synthetic |
| S12 | horizon-scaled margin (SD / RD λ.97) | int | −2.4 / −12.6 | −0.9 (6/9) / **+2.2 (1/9)** | RD: boot-Holm .02 | SD WIN (negligible); **RD LOSS** (negligible) |
| S12 | dwell k-streak (SD / RD λ.97 k3) | int | −3.0 / −7.6 | −4.2 (9/9) / 0.0 (4/9) | SD t-Holm .012 | SD WIN (negligible); RD COMPETITIVE |
| S12 | economic replacement (no front-load) | int | −17.7 | −9.0 (6/9) | t-p .067 | WIN (small) |
| — | Hoeffding LCB hurdle (SD / RD) | int | −3.3 / −16.6 | +1.3 (3/9) / −0.4 (5/9) | SD boot-Holm .02 | SD **LOSS** (negligible) on real; RD COMPETITIVE |
| N1 | Challenger-style irreversible Hoeffding payback (nominal / RD) | C | −30.9 / −15.1 | −5.1 (6/9) / −2.9 (6/9) | nine t-p .06 / .25 | **WIN** (synthetic meaningful; real small/negligible, not dataset-robust) |
| E1 | two-sided e-SR; e-SR RMM bets full α | B/C | −33.9 / −28.7 | −31.7 / −24.9 (6/9) | — | **NOT COMPARABLE** (certified per phase) |
| E2 | Shekhar–Ramdas RCS any-excludes | B | −39.2 | −19.3 (6/9) | — | **NOT COMPARABLE** (certified) |
| E3 | Han ARW label clock | B | −102.0 | −70.0 (9/9) | robust | WIN (substantial; ARW flips on noise, 14.8 switches) |
| O1 | online LLM picker | B | −27.8 | −3.7 (6/9) | nine t-p .24 | WIN on economic adaptation (real negligible) |
| O2 | variance-min IPW | C | −32.4 | −9.3 (6/9) | nine t-p .013 | WIN on economic adaptation (real small) |
| int | QSG (certified, internal) | int | −33.3 | −4.4 (6/9) | — | NOT COMPARABLE (certified) |
| ctrl | never switch | ctrl | −24.5 | −118.8 (6/9) | — | WIN (substantial); loses on la_crime, montgomery, nyc |
| desc | arm A λ.95 (EQSDp) | int | −4.5 | +2.0 (0/9) | — | descriptive: the longer-memory EQSDp is better on real data |
| abl | arm B with posterior-median hurdle | int | −50.8 | −24.9 (9/9) | robust | mechanism ablation: the confidence-bound hurdle matters |
| — | Ryabchenko capacity, river Page–Hinkley, WATCH, Timans, IUPM, Tenzer | — | — | — | — | **NOT VERIFIED / excluded**: not in this panel (no covariates on these streams, or no decision rule; see the fidelity LEDGER on the methods-strategy branch) |

## Answers in one line each

- **EQSDp wins (adapters only):**
  - against Qiu-style, Gong–Zhang-style (synthetic-tuned), UPF-style, the Challenger-style rule,
    CAMS, Model Selector, Model Picker, the online LLM picker, variance-min and ARW;
  - against its own simpler hysteresis controls when they are tuned on synthetic data (dwell,
    scaled margin), and against economic replacement.
- **Ties:**
  - Wald LCB at matched tuning (both environments);
  - Gong–Zhang-style tuned on real development data;
  - econF on real data;
  - real-tuned Hoeffding and dwell.
- **Losses:** real-dev-tuned Wald LCB (λ=.97) and real-dev-tuned scaled margin. Both are about
  +2.2 per episode (+0.5%) on 8–9 of 9 datasets. The descriptive arm A shows the same thing: EQSDp
  with longer memory beats arm B.
- **Not comparable:** every certified method (DISCERN, SMCS, Xu, gated/MOPE, e-SR, Shekhar–Ramdas,
  QSG). The native objectives of Model Picker, Model Selector and CAMS (best-model identification)
  are also not comparable; only their economic deployment adaptations are ranked.
- **Native vs adapter:** every comparison is against an adapter (class B or C) or an internal
  control. None is against a native, author-parity-verified implementation.
