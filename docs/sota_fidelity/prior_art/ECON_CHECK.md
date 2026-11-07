# Independent check of `econ_gate_external.md`

Date: 2026-11-07. Checker re-downloaded arXiv abs pages and PDFs into a fresh scratchpad directory
(`.../scratchpad/prior_art_econ_check/`), extracted text with `pdftotext`, and read the cited
locations. No downloaded code was run. The JRSS-B article page returned HTTP 403, so the DOI was
confirmed through Crossref metadata and the content was checked against the York discussion paper
(DP 15/09 v2, Aug 2015), not the journal version.

| # | Claim | Source opened | Verdict | Note |
|---|---|---|---|---|
| 1 | Wan et al. 2023, arXiv 2304.00420: Eq. (1) launch payoff δ×(H+T−t)×N minus one-off cost; §5.3 launches when value over H beats the cost; AV p-value decides launch | yes (arXiv v1, 2 Apr 2023; authors Wan, Liu, McQueen, Hains, Song) | **verified** | Eq. (1) is in §5.2.4: launch term `(u2(δ,H,T,t) − c_h)`, with `u2 = δ×(H+T−t)×(N_Tr+N_C)` and c_h the "hurdle cost". In §5.3 ("Role of information gain"), the fixed-horizon rule launches iff E[δ\|H_t]×H×N > c_h. Note that this rule uses H, not H+T−t, and is only an illustration for Lemma 1. §5.3 "Statistical inference" proposes letting RL decide only when to stop, with the launch decided by always-valid p-values (Johari et al.), plus a Lagrangian variant. The conclusion says these will be investigated "as our next step", so they are unanalysed. The report's "a remark rather than an analysed procedure" is accurate. |
| 2 | Chick, Forster, Pertile 2017, JRSS-B, DOI 10.1111/rssb.12225: §2 and Prop. 2.4, threshold = switch cost / beneficiaries, delayed outcomes | Crossref: yes (79(5):1439–1462, 2017, same title and authors). Text: DP v2 only | **qualified** | §2 has a one-time switching cost I, P patients treated after the trial, delay τ with "pipeline" subjects, and a finite T_max. The adoption rule itself (adopt iff P·Z > I) is stated in §2.1.1 (around Eq. 8). Prop. 2.4 is a *symmetry* result: with no discounting and no online learning (ρ̃=0, δ_on=0), the continuation region is symmetric about µ = I/P. "Centred on I/P (Prop. 2.4)" is therefore correct; "Prop. 2.4 gives the threshold" is loose. P is a fixed population and does not shrink as time passes, unlike Wan's H+T−t. |
| 3 | Schultzberg & Frånberg 2026, arXiv 2608.12949, App. H: Bayes-optimal economic rule is a time-varying BF threshold; Ville bounds FPR for any loss | yes (v1, 13 Aug 2026, stat.ME; Mårten Schultzberg and Mattias Frånberg, Confidence/Spotify) | **qualified** | The id, date and authors are correct. App. H part (c) gives a BF threshold that generally depends on n. Part (d) gives P(reject\|H0) ≤ 1/C "regardless of the loss function". Exact optimality holds only for the *two-point* model (δ∈{0,δ1}) with costs affine in π_n. Wan's utility was "verified numerically", and the main text calls the BF rule "near-optimal" there. In that worked example the optimal threshold is A*≈0.42 < 1, so the Ville bound is **vacuous**: the economic rule alone gives no α control. So "economics ≡ α" holds only when the economic threshold is at least 1/α. The report does not mention this. §5.3 and §6.4/Fig. 9 (shipping cost s) are as described. |
| 4 | Grünwald, arXiv 2205.00901, Thm 1 | yes (v1 2 May 2022, sole author) | **qualified** | Thm 1 Part 1 says every admissible decision rule is maximally compatible with some e-variable. Part 2 is a partial converse that needs mutual absolute continuity, sharpness and richness. Type-I *risk safety* of e-based rules is Prop. 1, not Thm 1, so the report merges the two. The setting is post-hoc/data-driven α and loss for a batch test, not anytime-valid sequential testing. Coding it "AV" overstates it. |
| 5 | Clerico, Wegel, Azangulov, Rebeschini, arXiv 2605.06521 | yes (v1 7 May 2026, math.ST) | **verified** | "Time-sensitive anytime-valid testing": testing by betting with a non-increasing reward R(τ) on the rejection time (τ = first time wealth ≥ 1/α). Thm 1 shows that Markov policies in (time, wealth) attain the supremum, i.e. a Bellman reduction. §6 covers the hard deadline (finite-horizon Neyman–Pearson). §7 covers exponential decay (EDO). Taga et al. 2026 and Voráček & Orabona 2025 are cited. Use is limited: horizon-awareness shapes *power* (bet sizing). It does not change the decision economics, and it has no switch cost or rollback. The report says this. |
| 6 | Bayraktar & Ludkovski, arXiv 0712.0413 | yes (v2 22 May 2008, math.OC) | **verified** | Finite-horizon optimal switching for a hidden Markov chain observed through a compound Poisson process. Running benefits c_i(a) and switching costs K_i(a,b) > k0 > 0 produce "inertia and hysteresis". Infinite horizon is in §5.1. There is no frequentist error control. |
| S1 | Muravlev, Urusov, Zhitlukhin, arXiv 1908.01162: "abstract mentions no switching cost" | yes (full text) | **understated** | The abstract indeed omits it, but the body imposes a penalty c1 on each switch (Eq. 20, "penalty for frequent switching"). Infinite horizon, discounted. This is further support for g2/g3 as known mechanisms. |
| S2 | Zou, Fellouris, Veeravalli, arXiv 1711.02186: transient = phases before a persistent law | yes | **verified** | The abstract matches: transient phases precede the final persistent distribution, with ARL control. This is not a reversal. |
| S3 | Chugg, Lardy, Ramdas, Grünwald, arXiv 2508.00770 | yes (abstract, v3) | **verified** | Γ-admissible post-hoc rules must be e-value based. Same caveat as row 4: post-hoc α, not anytime validity. |

Not re-checked (no attempt made): Gapeev–Peskir 2006, Dixit 1989, Banks–Sundaram 1994, Moustakides–Veeravalli,
Ebrahimzadeh–Tchamkerten, Guépié et al., Huang–Veeravalli, Cheng 2003, Lewis–Berry 1994. The report itself marks these
as not opened.

## Do verdicts g1–g4 survive?

Yes. All four survive, with one change of emphasis. **g1 (published, high)** stands: Wan Eq. (1)
and the CFP I/P adoption rule both say it directly. The CFP horizon P is fixed rather than shrinking,
which does not matter. **g2 (mechanism published)** stands and gets stronger: Muravlev et al.
also have switching penalties. **g3 (partly published)** stands. Bayraktar–Ludkovski price reversal
through the hidden-chain generator but give no error guarantee. **g4 (partly published)** stands,
but the report overstates the App. H threat. The BF-threshold equivalence is exact only for a
two-point prior with affine costs. It is numerical/near-optimal for Wan's utility. In Wan's own
calibration the economic threshold (≈0.42) gives no α control at all. A conjunctive "BF ≥ 1/α ∧
economic" gate in one-shot form still reduces to the time-varying threshold max(A*_n, 1/α). That
is a real reviewer objection for one-shot promotion, so the recommended baseline is right. For
the economic term to add something beyond α, it has to come from rollback, reversal, repeated
switch costs or budgeted delayed labels, as the report's bottom line says. Grünwald and Chugg et
al. support loss-aware e-value decisions, not anytime-valid ones, so their "AV" tag should be dropped.
