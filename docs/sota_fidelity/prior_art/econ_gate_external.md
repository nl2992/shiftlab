# External prior-art check: economic gating of promotion / rollback

Date: 2026-11-07. Retrieval-only audit (web search + PDF text extraction with `pdftotext`; no
downloaded code run). PDFs/text were stored in the session scratchpad
(`.../scratchpad/prior_art_econ_gate/`), not in Git. "Opened" means the full text was extracted
and the cited location was read. "Not opened" means only the abstract or listing was checked, and
nothing is claimed beyond it. ids on the repository's audited list are marked *already audited*.

Setting under test: an incumbent model and a frozen challenger, T=2000 rounds, label budget B=200
on disagreement rounds (cost 0.05, delay about 100), switch cost c_s=5. The challenger's advantage
is piecewise constant and may reverse. Promotions under the global null are controlled at
alpha=0.05 with an anytime-valid procedure. The question is whether the economic gate is new.
The gate decides promotion and rollback from remaining horizon, switch cost, estimated effect and
reversal hazard.

Coverage codes: **HP** = horizon-aware promotion, **HR** = horizon-aware rollback, **RH** =
reversal hazard, **SC** = switch cost, **AV** = anytime-valid error control under a null.

## Source table

| id / DOI | Title (short) | Authors, year | Opened | Where the mechanism appears | Covers |
|---|---|---|---|---|---|
| arXiv 2304.00420 (KDD 2023) | Experimentation platforms meet RL: Bayesian sequential decision-making for continuous monitoring | Wan, Liu, McQueen, Hains, Song, 2023 | yes | §5.2.4 Eq.(1): launch term `u2(δ,H,T,t) − c_h` with `u2 = δ·(H+T−t)·N`, which values the remaining post-launch horizon H minus a launch "hurdle cost". §5.3: the fixed-horizon Bayes rule launches when posterior-mean impact × H × N > c_h. §5.3 "Statistical inference": RL picks only *when to stop*, and the launch decision comes from always-valid p-values (Johari et al.), so it keeps type-I control. A Lagrangian variant is also given. | HP, SC (one-time launch), AV (bolt-on) |
| DOI 10.1111/rssb.12225 (York DP 15/09) | A Bayesian decision-theoretic model of sequential experimentation with delayed response | Chick, Forster, Pertile, 2017 (JRSS-B) | yes (DP v2) | §2: one-time switching cost I for adopting the new technology, with P future patients benefiting. The adoption boundary is centred on I/P (Prop. 2.4). Delayed "pipeline" responses are modelled explicitly. Finite T_max (Props. 2.2–2.3). | HP, SC, delay. No AV, no rollback |
| arXiv 2608.12949 | Bayesian inference procedures for A/B testing: an overview | Schultzberg, Frånberg (Spotify), 2026 | yes | §5.3 and App. H proposition: for finite-horizon continue/accept/reject problems with costs affine in the posterior, the optimal rule is a time-varying Bayes-factor threshold. Part (d) shows that any rule rejecting only when BF ≥ C has P(reject \| H0) ≤ 1/C "regardless of the loss function". Checked numerically on Wan et al.'s horizon + hurdle-cost utility. §6.4 / Fig. 9 add a per-launch shipping cost s. | HP, SC, AV (equivalence) |
| arXiv 2605.06521 | Time-sensitive anytime-valid testing | Clerico, Wegel, Azangulov, Rebeschini, 2026 | yes | Reward R(τ) on the rejection time. Thm 1: Bellman representation in (time, wealth). §6: hard deadline (finite-horizon Neyman–Pearson). §7: exponential decay (EDO criterion). Cites Taga et al. (2026), horizon-aware RL betting (not opened), and Voráček & Orabona (2025). | horizon-aware AV test. No SC, no rollback |
| arXiv 2205.00901 (PNAS 2024) | Beyond Neyman–Pearson: e-values enable testing with a data-driven alpha | Grünwald, 2022/24 | yes (located only) | §2, Thm 1: e-value-based decision rules are Type-I-risk safe for losses chosen post hoc, and they are the only admissible ones. | AV + general loss. No horizon, no SC |
| arXiv 2508.00770 | On admissibility in post-hoc hypothesis testing | Chugg, Lardy, Ramdas, Grünwald, 2025 | no | Abstract: admissible post-hoc rules must be e-value based. | AV + loss |
| arXiv 0712.0413 | Sequential tracking of a hidden Markov chain using point process observations | Bayraktar, Ludkovski | *already audited* | Finite-horizon optimal switching. The controller tracks a hidden Markov regime, earns tracking benefits and pays switching costs bounded below by k0>0 (listing summary). | HP, HR, RH (Markov), SC. No AV |
| arXiv 1908.01162 | Sequential tracking of an unobservable two-state Markov process under Brownian noise | Muravlev, Urusov, Zhitlukhin, 2019 | abstract only | Tracks a symmetric two-state switching drift. The abstract mentions no switching cost. | RH (Markov) |
| DOI 10.1016/j.spa.2006.04.005 | The Wiener disorder problem with finite horizon | Gapeev, Peskir, 2006 | no | Abstract: Bayesian disorder with a finite horizon gives a time-dependent stopping boundary (Volterra equation). | horizon-aware detection. No SC/AV |
| JPE 97(3):620–638 | Entry and exit decisions under uncertainty | Dixit, 1989 | no | Abstract: entry and exit triggers with a hysteresis band created by sunk entry/exit costs. | SC, HR-type band (infinite horizon) |
| Econometrica 62(3):687–694 | Switching costs and the Gittins index | Banks, Sundaram, 1994 | no | Abstract: with switching costs, no index policy is optimal. | SC in bandits |
| arXiv 1711.02186 (IEEE TIT 2019) | QCD under transient dynamics | Zou, Fellouris, Veeravalli | yes (skim) | Abstract and §1: "transient" means intermediate phases *before* a persistent post-change law, not a reversal. D-CuSum/WD-CuSum are optimal under ARL. | none of the gate levers |
| DOI 10.1109/ISIT.2016.7541254 | Sequentially detecting transitory changes | Moustakides, Veeravalli, 2016 | no | Listing: a gradual transition into steady state, with a CUSUM-like optimum. Not a reversal. | — |
| DOI 10.1109/ISIT.2015.7282436 | Sequential detection of transient changes … under a sampling constraint | Ebrahimzadeh, Tchamkerten, 2015 | no | Listing: transient change with a worst-case delay objective and a sampling-rate constraint. | sampling budget, transient |
| DOI 10.1080/07474946.2012.719443 | Sequential detection of transient changes (window-limited CUSUM) | Guépié, Fillatre, Nikiforov, 2012 | no | Listing: a finite-duration change must be detected within the window. | RH-flavoured detection, no SC |
| arXiv 2501.10974 | Finite-horizon QCD motivated by piecewise-stationary bandits | Huang, Veeravalli, 2025 | no | Listing: detectors order-optimal in the horizon. | horizon-aware detection |
| Biometrika 90(4):923, DOI 10.1093/biomet/90.4.923 | Choosing sample size for a clinical trial using decision analysis | Y. Cheng, 2003 | no | Abstract: finite patient population N. The optimal first stage scales roughly as N^(1/3). | HP (patient horizon) |
| JASA 1994 | Group sequential clinical trials: a classical evaluation of Bayesian decision-theoretic designs | Lewis, Berry | no | Secondary sources: Bayesian decision-theoretic stopping evaluated and calibrated on frequentist error. | economic + error constraint (non-anytime) |

The classical "patient-horizon" papers (Anscombe 1963; Colton 1963) and Chick & Frazier / Chick &
Gans value-of-information stopping were **not opened**. They are commonly cited antecedents of the
same horizon-times-effect-versus-cost logic.

## Closest prior art

1. **Wan et al. 2023 (arXiv 2304.00420)** is the closest to the promotion half. Its utility
   rewards launch as effect × remaining horizon × population minus a hurdle (switch) cost. §5.3
   explicitly bolts an always-valid p-value onto the launch decision to keep type-I error
   control. This is essentially g1 plus a one-shot form of g4. It has no rollback, no reversal,
   no label budget or delayed paired labels, and the AV bolt-on is a remark rather than an
   analysed procedure.
2. **Schultzberg & Frånberg 2026 (arXiv 2608.12949), App. H.** For finite-horizon launch problems
   with affine costs (Wan's utility included), the Bayes-optimal economic rule *is* a
   time-varying Bayes-factor threshold, and Ville gives FPR ≤ 1/C at any threshold C. This poses
   a **threat to g4's novelty and substance**: an "economic gate ∧ certificate" may reduce to
   choosing a time-varying evidence threshold. A reviewer could call it a reparameterised α.
3. **Chick–Forster–Pertile 2017.** Adoption is worthwhile only if expected benefit over the P
   remaining users exceeds the switching cost I (boundary at I/P), and it models delayed
   outcomes. This is g1 with delay, though Bayesian and with no frequentist control.
4. **Bayraktar–Ludkovski (0712.0413, already audited)** and the optimal-switching / real-options
   line (Dixit 1989). Switching back and forth under a hidden, reverting regime with switching
   costs and a finite horizon is the textbook form of g2 and g3, but it is purely Bayesian/optimal
   control with no null-hypothesis error guarantee.
5. **Clerico et al. 2026 (arXiv 2605.06521).** Horizon-aware anytime-valid testing (the value of
   rejection decays or hits a deadline) touches g1 ∧ AV from the testing side. It has no switch
   cost or rollback.

## Verdicts per sub-lever

**(g1) Promote only if the remaining horizon pays (effect × remaining rounds > switch cost [+
label cost]).** **Published.** See Wan et al. 2023 Eq.(1) and the §5.3 fixed-horizon Bayes rule;
Chick–Forster–Pertile 2017 §2 / Prop. 2.4 (I/P threshold); and the patient-horizon literature
(Cheng 2003; Anscombe/Colton, not opened). Confidence: **high**. Using it in our setting is an
application, not a contribution.

**(g2) Roll back only if the expected remaining loss exceeds the switch cost.** **Published as a
generic mechanism.** Optimal switching with switching costs and hysteresis appears in Dixit 1989
(abstract) and in Bayraktar–Ludkovski's finite-horizon tracking with switching costs (already
audited); Banks–Sundaram 1994 covers bandits. I **did not find** it in model-rollout or A/B form
combined with an anytime-valid harm or rollback certificate. Industry "guarded rollouts" roll back
on sequential-test significance alone, with no economic term (vendor pages, not academic).
Confidence: **high** that the mechanism is known, **medium** that the AV rollback combination is
unpublished.

**(g3) Hazard-aware promotion (discount the expected benefit by the probability that the
advantage reverses).** **Partly published.** Bayesian regime-switching control with switching
costs (Bayraktar–Ludkovski; regime-switching real options, not opened) prices the reversal through
the regime generator. The transient-change detection literature does not do this. Zou et al.,
Moustakides–Veeravalli and Ebrahimzadeh–Tchamkerten treat transient or transitory phases for
detection delay. Guépié et al. treat a finite-duration change for missed detection. None of them
gates a promotion by expected remaining benefit under reversal. **Not found**: a hazard-discounted
promotion rule placed on top of a frequentist/anytime-valid promotion certificate. Confidence:
**medium**. The coverage of the operations-research/real-options literature is incomplete.

**(g4) Combine a certified (alpha-controlled, anytime-valid) test with an economic gate.**
**Partly published.** Wan et al. 2023 §5.3 (an always-valid p-value decides launch while
economics decides stopping, plus a Lagrangian alternative) and Schultzberg & Frånberg 2026 App. H
(a Bayes-optimal economic rule is a BF threshold with a Ville FPR bound for any loss) both cover
one-shot promotion. Grünwald 2022/24 Thm 1 and Clerico et al. 2026 give loss- and time-sensitive
e-value decision theory. Lewis & Berry 1994 is the non-anytime antecedent (not opened). **Not
found**: the conjunctive gate with *both* promotion and rollback, a switch cost on each move,
reversal hazard, a paired-label budget and delayed labels, while keeping the promotion error
bound. Confidence: **medium-high** for "partly published". The App. H equivalence is the main
risk. The economic gate may add nothing beyond a time-varying threshold unless rollback and
reversal break the affine/one-shot structure.

## Bottom line

Taken alone, each of g1 and g2 is known. g3 and g4 exist in Bayesian-control or one-shot launch
form. The only unclaimed space is the **combination**: anytime-valid promotion control together
with economics-gated promote *and* rollback under reversal, switch costs, and a budgeted, delayed
paired-label stream. Any claim should be framed as that combination and benchmarked against Wan
et al.-style horizon-utility rules with an AV launch constraint and against a time-varying BF/e
threshold (Schultzberg & Frånberg App. H). It should not be framed as "economic gating" per se.

## Checker qualifications (2026-11-07, see ECON_CHECK.md)

- Chick–Forster–Pertile: the adoption rule is in §2.1.1; Prop. 2.4 only gives symmetry of the continuation region about I/P. The beneficiary count is fixed, not shrinking.
- Schultzberg & Frånberg App. H: exactly optimal only for a two-point prior with affine costs; in their worked example the economic Bayes-factor threshold (~0.42) is below 1, where Ville's bound gives no error control. The threat to g4 is somewhat smaller than stated above.
- Grünwald 2205.00901: type-I safety is Prop. 1, not Thm 1, and the setting is one-shot post-hoc alpha, not anytime-valid.
- Wan et al. §5.3 uses horizon H, not H+T−t; the always-valid launch rule is proposed, not analysed.
- Muravlev et al. do penalise each switch (Eq. 20), contrary to the table; g2/g3 are better supported than stated.
- Verdicts g1–g4 survive.
