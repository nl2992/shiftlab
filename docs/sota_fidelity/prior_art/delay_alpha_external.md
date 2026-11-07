# External prior-art check: delay robustness (lever b) and promotion/rollback alpha allocation (lever c)

**Date:** 2026-11-07. **Status:** retrieval and theorem-scope audit only. Nothing here establishes
a method, a novelty claim or an efficacy result. "Read" levels are stated per source. A fetch tool
summarised long HTML pages; where I extracted PDF text myself (Goeman–Solari, Vernade et al.) I
quote from that text. Proofs were not independently re-verified unless stated.

Context: `docs/sota_fidelity/late_change_diagnosis_results.md:17` (delay 10/100/400 gives
e-SR − never-switch of −21.0 / −16.4 / −0.6), `:68` (alpha split costs 4–11 per episode), and
`docs/sota_fidelity/esr_vs_erb_dev_results.md:40` (the split trades promotion speed against rollback).
The contract's risk target is `docs/switching_problem_v1.md:42-50`.

Scratch files (untrusted data, not committed):
`/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/prior_art_delay_alpha/`
(`goeman_solari.txt`, `vernade.txt`, which are pdftotext extractions of the arXiv PDFs).

---

## Lever (b): delay robustness

### 1. Search log (WebSearch unless noted; date 2026-11-07)

| # | Query | Mode | Useful new hits |
|---|---|---|---|
| b1 | quickest change detection delayed observations arXiv | extended | none new (2408.05817, 2511.12803, 2107.10492 already audited) |
| b2 | non-stationary delayed bandits intermediate observations Vernade | standard | arXiv:2006.02119 (ICML 2020) |
| b3 | piecewise stationary bandit delayed feedback change detection regret | standard | none combine delay with CD (1711.03539, 2501.10974, 2501.01291 are immediate-feedback) |
| b4 | Bayesian quickest detection "delayed observations" disorder problem optimal stopping | extended | none on observation lag (delay-penalty and costly-observation papers only; 1505.07612) |
| b5 | anytime-valid sequential test delayed outcomes pipeline e-process stopping 2025 | extended | only Lindon–Kallus 2603.25971 (already audited) |
| b6 | concept drift detection delayed labels data streams verification latency | standard | Pham et al., Mach. Learn. 2021 (FS); 2204.06822 already audited |
| b7 | "label delay" online continual learning Csaba NeurIPS 2024 | standard | arXiv:2312.00923 |
| b8 | sequential change detection observations arrive with random delay out-of-order sensor network CUSUM | extended | 2510.25604 (already audited), 1105.6065 (network delay; not pursued) |
| b9 | Forgetting and Simulating active learning verification latency Pham Kottke Krempl Sick | standard | DOI 10.1007/s10994-021-06099-z |
| b10 | e-values sequential test delayed responses pipeline patients anytime-valid group sequential | extended | 2512.04366, 2602.06379 (trial e-processes; no delay structure) |
| b11 | online experiment stopping delayed conversions finite population remaining horizon | extended | 2606.23962 (detection-delay penalty, not observation delay; checked abstract, irrelevant) |
| b12 | quickest detection "lagged observations" OR "observation delay" OR "delayed measurements" | extended | Niesen–Tchamkerten math/0701261 |

Fetches: arxiv.org/abs/2006.02119 and arxiv.org/pdf/2006.02119v2 (PDF text extracted);
arxiv.org/abs/math/0701261; arxiv.org/abs/2606.23962. Springer and the Kassel repository for Pham et al.
redirected or blocked automated access, so that source is not read beyond search abstracts.

### 2. Internal closures already in the repo (not redone)

- `docs/switching_budget_delay_lower_bound_v1.md:27-28,67-69`: at least `d` rounds are unavoidable and any pulse with `h<=d` is lost entirely; the coupling is prior art (`:94`, Chandar–Tchamkerten Lemma 1).
- `docs/switching_finite_horizon_qcd_budget_delay_audit_v1.md:54,72`: the latency must satisfy `ell >= d + ceil(kl/KL)`. This is a standard adaptive-KL argument. Huang–Veeravalli finite-horizon TVT-CuSum/SR is a required baseline.
- `docs/lane_b_burst_allocation/D0_prior_art.md:148-160` and `D2_split_clock_mechanism.md:7,155,236`: the fast-surrogate split clock exits as a composition. Prop. 2 shows a hidden shift cannot be rolled back before `d_g`. Prop. 5 shows triggered gold cannot beat a continuous backstop.
- `docs/lane_b_burst_allocation/D0_prior_art.md:70-72`: Grover et al. (delayed BAI with partial feedback), Mann et al. (proxies, delay-additive regret) and Impatient Bandits (surrogate fusion) are audited.
- `docs/lane_b_burst_allocation/R3_delayed_update_validity_note.md:7-9`: fixed-delay release-time updating is valid with qualifications; out-of-order release is **not** valid in general; missing labels must apply `-eps`.
- `docs/switching_feedback_online_testing_prior_audit_v1.md:14-20,49`: delayed-feedback alpha-wealth recycling (Lu et al., JMLR 2026) closes generic delayed-label budget recycling.
- `docs/switching_delayed_comparator_audit_v1.md:32-46`: Chick–Forster–Pertile (JRSS B 2017) covers pipeline outcomes, a finite population, a hard maximum sample size and adoption cost. This closes delayed one-shot economic adoption.
- `docs/budgeted_switching_research_goals.md:1974-1978`: Hampson–Jennison (2013) delayed-response group-sequential tests with pipeline data and backward induction are already audited.

### 3. New sources (closest first)

**B1. Vernade, György, Mann, "Non-Stationary Delayed Bandits with Intermediate Observations,"
ICML 2020 (PMLR 119), arXiv:2006.02119v2 (11 Aug 2020).** Read: full PDF text extracted (model §2–3,
Algorithm 1, Theorems 1–3 statements, Proposition 1 and §4.3 discussion). Appendix proofs were not checked.
- *Native problem:* K-armed bandit. A categorical intermediate outcome `S_t ~ p_t(a)` is seen at once and the reward follows after a constant delay `D`. Here `p_t` switches abruptly `Γ_T` times while `θ` (reward given signal) stays fixed (§3).
- *Rule:* NSD-UCRL2 (Algorithm 1) uses sliding-window estimates of the non-stationary `p_t` and delayed full-history estimates of the stationary `θ`.
- *Guarantee:* Theorem 2 is a high-probability (`1-2δ`) dynamic-regret bound in which the delay enters once, as an additive `SD` term next to `WΓ_T`. **Proposition 1** says any *signal-agnostic* algorithm has minimax regret `Ω(min{T, sqrt(K(Γ_T+1)T) + (Γ_T+1)D})`. The paper calls the construction "easy to show" and only sketches it, so treat it as sketch-level.
- *Why it matters:* without a faster informative channel, paying the delay once per change is minimax-unavoidable. Only intermediate signals (with a stationary signal-to-reward map) remove the per-change `D`. This matches the repo's lower bound and D2 Prop. 2.
- *Verdict:* **CLOSES** the hope of beating "+d per change" without auxiliary information. The surrogate route it uses is the split-clock idea that D0/D2 already closed. It has no anytime-valid error control, budget, switching cost or rollback.

**B2. Pham, Kottke, Krempl, Sick, "Stream-based active learning for sliding windows under the
influence of verification latency," Machine Learning 111(6):2011–2036 (online 18 Nov 2021),
DOI 10.1007/s10994-021-06099-z.** Read: **abstract and catalogue metadata only (UNVERIFIED body)**.
- *Native problem:* label acquisition for a sliding-window classifier when labels arrive late with known arrival times.
- *Rule:* "Forgetting and Simulating" (FS) drops outdated data and simulates the pending labels when it computes the utility of a label.
- *Guarantee:* empirical only, as far as the abstract shows.
- *Verdict:* **ADJACENT.** This is the only source found that explicitly exploits pending-label structure for acquisition. It gives no detection guarantee, no change-point validity and no economics. Under the repo's contract, simulating pending labels can only change acquisition and pacing, not when an alarm can fire. The lower bound already fixes that.

**B3. Csaba, Zhang, Kim, Ruiz, Rawal, Bibi, Ozfatura, Gautam, Dokania, Torr, Lim, "Label Delay in
Online Continual Learning," NeurIPS 2024, arXiv:2312.00923.** Read: **abstract-level via search
summary (UNVERIFIED body)**.
- *Native problem:* online continual learning where labels lag the data stream by `d` steps.
- *Rule:* Importance Weighted Memory Sampling rehearses the labelled memory samples most similar to the newest unlabelled data.
- *Reported finding:* self-supervised and test-time adaptation on new unlabelled data did not beat the naive delayed-label baseline.
- *Verdict:* **ADJACENT.** It uses the unlabelled stream as a surrogate (already closed by D0/D2), has no validity guarantee, and shows empirically that adding compute does not undo delay.

**B4. Niesen, Tchamkerten, "Tracking Stopping Times Through Noisy Observations," IEEE TIT 55:422–432
(2009), arXiv:math/0701261v4.** Read: **abstract only**.
- *Native problem:* Bayesian tracking of an `X`-stopping time `S` by a `Y`-stopping time `T`. It minimises `E(T-S)^+` subject to `P(T<S) <= α`, with finite alphabets and bounded `S`.
- *Rule:* an optimal algorithm that runs in polynomial time under some conditions.
- *Verdict:* **ADJACENT.** Lag is implicit, not a fixed release delay. Its probabilistic false-alarm formulation is the nearest classical analogue of "decide on a lagged or noisy view of the change."

**Searched and found nothing new.** I found no QCD paper with a fixed observation release delay that
improves on "detect on released data". Searches b1, b4, b8 and b12 returned only delay-penalty papers,
costly or sampling-right papers (already audited: Geng–Bayraktar–Lai, Banerjee–Veeravalli 1105.1361)
and the lossy-link paper 2510.25604 (already audited). The remaining-horizon-aware stopping rules I
found are the already-audited Huang–Veeravalli time-varying thresholds and Chick–Forster–Pertile's
finite-population pipeline Bellman recursion.

### 5(b). Residual and verdict for lever (b)

- **Verdict: closed as a contribution.** "Delay adds `d`" is a lower bound for any signal-agnostic rule: repo lower bounds, plus Vernade et al. Prop. 1 for the per-change additive `(Γ+1)D` in the bandit setting.
- The only escapes are each already closed:
  - fast or intermediate signals: D0/D2 and Vernade et al.;
  - pipeline-aware economic stopping: Chick–Forster–Pertile and Hampson–Jennison;
  - finite-horizon thresholds: Huang–Veeravalli.
- The −21 → −16 → −0.6 shrinkage at delay 10/100/400 matches horizon arithmetic. Post-change rounds usable after release fall from about 1200 − 10 to about 1200 − 400 minus detection delay, while label and switch costs stay fixed. No source suggests a valid rule that recovers that loss.
- **Residual (composition of known parts):** horizon-aware pacing, meaning no labels whose release time `s+d` leaves too little horizon to repay `c_s` plus the outstanding label charges. This follows directly from the pipeline/finite-population logic (Chick–Forster–Pertile) and from the repo's own lower bound (a label requested at `s` can affect only decisions at or after `s+d`). It may save query cost (at most `c_q` × the number of such labels; about 0.05 × a few dozen in this contract). It is an engineering baseline, not a lever.
- **UNVERIFIED:** Pham et al. 2021 body; Csaba et al. 2024 body; Niesen–Tchamkerten body; proof of Vernade et al. Prop. 1 (sketch in paper).

---

## Lever (c): alpha allocation between the promotion and rollback detectors

### 1. Search log

| # | Query / fetch | Mode | Useful new hits |
|---|---|---|---|
| c1 | online closed testing with e-values Fischer Ramdas arXiv | standard | arXiv:2407.15733 |
| c2 | graphical approach multiple testing e-values sequential e-processes FWER alpha propagation | extended | arXiv:2501.09015 (Hartog–Lei), arXiv:2606.00878 (Brannath–Fischer), Bretz 2011 |
| c3 | Maurer Bretz 2013 multiple testing in group sequential trials using graphical approaches | standard | Maurer–Bretz SBR 5:311–320 (abstract only) |
| c4 | Bretz Maurer Brannath Posch 2009 graphical approach pdf | standard | arXiv:1211.3313 (Goeman–Solari); Bretz 2009 full text not accessible (typeset/scispace redirect not followed) |
| c5 | two-sided CUSUM asymmetric thresholds upper lower chosen by cost or ARL allocation | extended | Qu–Wu–Rahim–Khoo EJIE 2015 (abstract); 1/ARL = 1/ARL⁺ + 1/ARL⁻ folklore |
| c6 | Tamhane Mehta Liu 2010 primary secondary endpoint group sequential | standard | Biometrics 66:1174–1184 (abstract) |
| c7 | "balanced two-sided CUSUM" time between events allocation asymmetric loss | standard | as c5 |
| c8 | sequential change detection two directions different false alarm constraints Nikiforov | standard | Nikiforov detection/isolation (false-isolation constraint); not a directional alpha budget |
| c9 | "online closure principle" Fischer Bofill Roig Brannath | standard | arXiv:2211.11400 (AoS 52:817–841, 2024) |

Fetches: arxiv.org/abs + html for 2501.09015 (v4, two passes covering about 200k of 205k characters);
arxiv.org/abs + html 2606.00878v1; arxiv.org/abs + pdf 1211.3313 (text extracted; §2.1 Theorem 1 read
verbatim); html 2407.15733v3 (first half); html 2211.11400v3 (first 100k of 130k characters); PMC3427907 (Bretz et al. 2011,
§2–3.1).

### 2. Internal closures already in the repo (not redone)

- `docs/switching_problem_v1.md:42-50`: **the contract's risk target counts only promotions under the global no-benefit null.** A direction-specific (per-switch) guarantee is flagged as an "unresolved proof obligation".
- `docs/switching_online_fwer_comparator_audit_v1.md:11-17,26`: Tian–Ramdas online alpha spending and Online Fallback (Prop. 2, arbitrary dependence) recycle a rejected hypothesis's level forward. Generic recycling is closed.
- `docs/switching_two_episode_risk_recycling_v1.md:23,29`: under a local criterion two looks need `(1-a1)(1-a2) >= 1-α`, and conditional-error allocation exhausts it. Closed by Posch–Bauer (1999).
- `docs/switching_sequential_model_modification_prior_audit_v1.md:16-29`: Feng et al. (UAI 2022) adaptive SRGPs recycle alpha over an adaptively explored update tree. Closed.
- `docs/switching_feedback_online_testing_prior_audit_v1.md:49`: feedback-based online alpha recycling is closed.
- `docs/switching_episode_composition_comparator_v1.md:9`: geometric, equal or all-first episode spending is already a baseline.
- `docs/next_phase_plan.md:175`: "Weighted Bonferroni is established composition", so cost-weighted static splits are not new.
- `docs/sota_fidelity/specs/shin_edetectors.md:154-175`: Shin–Ramdas–Rinaldo has **no** two-sided construction. stcpR6 two-sided runs alpha/2 per side, and `combine_stcp` uses a weighted alpha `w α1 + (1-w) α2`. Sequential rollback is "a new one-sided detector with its own alpha".
- Vovk–Wang (arXiv:1912.06116; weighted averages of e-values are e-values) is already audited (`docs/chugg_group_betting_paper_to_code_audit.md:17`).

### 3. New sources

**C1. Hartog, Lei, "Family-wise Error Rate Control with E-values," arXiv:2501.09015v4 (17 May 2026;
v1 15 Jan 2025); no journal reference.** Read: sections 1–9 via HTML (about 98% of the text), and Appendix B
only by reference.
- *Native problem:* closed testing with e-values. The local test of `H_I` is a weighted average `e_I = Σ_{i∈I} w_i(I) e_i >= 1/α` (§3.1, eq. 3.2), and adjusted e-values are `e_i* = min_{I∋i} e_I` (eq. 3.3). The e-graphical approach takes `w_i(I)` from Bretz et al.'s graphical weights (§3.1, §6.1). e-Fallback is the chain or fixed-sequence special case (§5; Algorithm 2; Theorems 5.2–5.3 cover only computation).
- *Guarantee:* Proposition 2.2 (static FWER `<= α`, by Markov, no structural assumption on the e-values). **Theorem 2.5** gives always-valid control `P(max_{i∈H0} sup_t e*_{i,t} >= 1/α) <= α` by Ville, when every `e_{I,t}` is an e-process for `H_I` on a common filtration. Theorem 2.4 gives anytime-valid control at stopping times.
- *Caveats:* the e-version is not consonant (§6.1 counterexample), and running-max "pseudo e-values" are not proven valid (§3.2, Theorem 3.1 only gives `α + o(α)` under independence).
- *Verdict:* **CLOSES** the statistical tool for "pass the promotion budget to rollback after promotion" with e-processes. With all weight on the promotion hypothesis `H_P` and an edge of weight 1 to `H_R`: `e_{PR} = e_P` and `e*_R = min(e_P, e_R)`. Rollback is then tested at full α only after `e_P` has crossed. The hypotheses must be fixed sets of laws; see §4.

**C2. Fischer, Bofill Roig, Brannath, "The Online Closure Principle," Ann. Statist. 52(2):817–841 (2024),
arXiv:2211.11400v3.** Read: §2–4 via HTML (first about 77%).
- *Native problem:* FWER for an online stream of hypotheses, where each decision must be `F_i`-measurable (Def. 2.1).
- *Rule and guarantee:* **Theorem 3.2** says the closed procedure `d_i = min{φ_I : i∈I}` controls FWER strongly for any α-level intersection tests. It is online if the intersection tests are `F_sup(I)`-measurable and the family is predictable (Def. 3.1). It assumes no dependence condition beyond the level of the intersection tests.
- *Special cases:* the online fixed-sequence procedure is a Dirac sub-adjustment (Remark after Def. 4.5). Online-Graph / Tian–Ramdas Online-Fallback is a shortcut (§4.2, Theorem 4.2), and the paper notes that Tian–Ramdas did not prove theirs was online.
- *Caveat:* the fetched summary reports that `H_i` are formally fixed subsets of the model.
- *Verdict:* **PARTIALLY OVERLAPS / CLOSES the recycling logic.** A promotion → rollback → re-promotion chain tested in fixed-sequence order at full α each is an online closed procedure. It controls FWER for fixed hypotheses. It does not address change-point (pathwise) error definitions.

**C3. Fischer, Ramdas, "Admissible online closed testing must employ e-values," arXiv:2407.15733v3
(16 Feb 2025; v1 titled "Online closed testing with e-values").** Read: first half via HTML.
- *Native problem:* online true-discovery and FWER guarantees.
- *Results:* states that hypotheses "do not have to be prespecified" and may be built from previous-step information (§2). It defines sequential e-values with test supermartingales and Ville for anytime-valid intersection tests (§3.1, eq. 11). Theorem 2.3 and Fact 1: admissible online procedures must use test martingales. SeqE-Guard is Algorithm 1 with Theorem 3.1.
- *Missing:* no explicit fallback or recycling theorem was found in the part read.
- *Verdict:* **PARTIALLY OVERLAPS.** It supports data-adaptively defined hypotheses, such as a rollback null defined after a random promotion time, within online closure with e-processes.

**C4. Goeman, Solari, "The sequential rejection principle of familywise error control," Ann. Statist.
38(6):3782–3810 (2010), arXiv:1211.3313v1.** Read: §1–2 verbatim (pdftotext) and the §6 list of covered procedures.
- *Rule:* §2.1, eq. (1): `R_{i+1} = R_i ∪ N(R_i)`.
- *Guarantee:* **Theorem 1** gives strong FWER `<= α` if (2) monotonicity `N(R) ⊆ N(S) ∪ S` holds for `R ⊆ S` and (3) the single-step condition `P_M(N(F(M)) ⊆ F(M)) >= 1-α` holds for every model `M`. Fallback, fixed sequence and Bretz et al. graphs are special cases (§6.2).
- *Application:* for the chain `N(S) = {P if e_P >= 1/α} ∪ {R if P∈S and e_R >= 1/α}`, monotonicity holds. The single-step condition reduces to `P(e_P >= 1/α) <= α` when `H_P` is true and `P(e_R >= 1/α) <= α` when only `H_R` is true. This is my instantiation, not a statement in the paper.
- *Verdict:* **CLOSES** (classical): full α to the first hypothesis, then full α to the second after rejection, for fixed hypotheses.

**C5. Bretz, Posch, Glimm, Klinglmueller, Maurer, Rohmeyer, "Graphical approaches for multiple comparison
procedures using weighted Bonferroni, Simes, or parametric tests," Biometrical J. 53(6):894–913 (2011),
PMC3427907.** Read: §2–3.1. The original Bretz–Maurer–Brannath–Posch, Stat. Med. 28:586–604 (2009),
DOI 10.1002/sim.3495, was **not accessible (UNVERIFIED; content known only via C1, C4, C5)**.
- *Guarantee:* strong FWER via closure with weighted Bonferroni local tests (§2, unnumbered). Fixed sequence (Maurer–Hothorn–Lehmacher 1995; Westfall–Krishen 2001) is a graph special case (§3.1).
- *Verdict:* **CLOSES** (classical recycling along an edge of weight 1).

**C6. Brannath, Fischer, "Anytime-valid testing with e-values and confirmatory adaptive designs,"
arXiv:2606.00878v1 (30 May 2026).** Read: almost all of the HTML via fetch summary; the paper has no numbered theorems.
- *Results:* conditional error functions are equivalent to sequential e-values: eq. (5) for two stages and eq. (6) for multiple stages, with `A_t = min(α M_t, 1)`. For closed weighted-Bonferroni tests the e-value version rejects the same hypotheses as the conditional-error version (§4, eq. 11). E-value tests with threshold `1/α` are "inevitably conservative" when early rejection is possible (App. A, Remark 5). An adjusted level that exhausts α exists (App. A.1, eq. 13).
- *Verdict:* **ADJACENT / supporting.** It links the repo's conditional-error allocation (two-episode note) to e-processes and says why e-detectors leave α unspent. It does not treat directional or rollback allocation.

**C7. Tamhane, Mehta, Liu, "Testing a Primary and a Secondary Endpoint in a Group Sequential Design,"
Biometrics 66(4):1174–1184 (2010).** Read: **abstract only (UNVERIFIED body)**.
- *Native problem:* the secondary endpoint is tested only after the primary is significant, and the FWER must be `<= α`. Given an α-level primary boundary, the paper derives the secondary boundary.
- *Relevance:* the related Hung–Wang–O'Neill (2007) warning is that naive hierarchical borrowing can inflate FWER under repeated looks unless the secondary uses its own valid sequential boundary.
- *Verdict:* **ADJACENT.** With anytime-valid e-processes on both legs, the repeated-look issue disappears (C1 Theorem 2.5). This is the clinical-trial precedent for "gatekeeper at full α, then the next test".

**C8. Qu, Wu, Rahim, Khoo, "A balanced two-sided CUSUM chart for monitoring time between events,"
Eur. J. Industrial Engineering 9(1):1–26 (2015).** Read: **abstract only (UNVERIFIED)**.
- *Native problem:* a two-sided CUSUM whose upward and downward legs are designed by minimising an asymmetric loss. The abstract reports about 20% better average effectiveness than the conventional two-sided chart.
- *Verdict:* **ADJACENT.** It is precedent for cost-weighted asymmetric thresholds on the two sides of an ARL-constrained detector (1/ARL = 1/ARL⁺ + 1/ARL⁻ folklore). It is not a probability guarantee and not sequential promote-then-rollback.

### 4. Is "full α before promotion, then hand a share to rollback" valid?

The answer depends on which error event is controlled. There are three cases.

**(i) The contract's actual criterion (`switching_problem_v1.md:44-46`):** `sup_{P∈H_0^global}
P(∃t: A_{t-1}=0, A_t=1) <= α`, where `H_0^global: E[Z_t|H_t] <= 0` for all `t`.
- Valid, trivially, and stronger than asked. Under `H_0^global` every promotion, including any re-promotion after a rollback, happens only after a first promotion. So `P(any promotion) = P(first promotion) <= α` whenever the first-phase promotion statistic is an e-process / PFA-weighted e-detector at threshold `1/α`.
- PFA-weighted means start weights summing to `<= 1`: Shin et al. Remark 2.7, proved in Saha–Ramdas Thm 2.3 per `specs/shin_edetectors.md:142-144`. That Ville bound comes from those specs. The "first promotion dominates" step is an elementary set inclusion.
- **The rollback detector consumes no α under this criterion.** It may be certified at any level, or purely economic. Re-promotions also need no α/2^j halving.
- Hence the α/2-per-side split, and RMM's `α_det/2^j`, are conservative relative to the stated contract. **[Lead correction, 2026-11-07]** A null check for `esr_rmmbets_fullalpha` does exist: `esr_vs_erb_dev_results.json` (`null_first_promotion`, 1000 seeds each) gives promotion rates 0.016 / 0.019 / 0.000 on F0_null / V_null / V_worse (Wilson upper 0.026 / 0.029 / 0.004), within alpha = 0.05 and the registered 0.0936 bound. These are development null regimes, not a proof under every conditional null.

**(ii) A stronger law-level "any false switch" criterion.** Define fixed composite hypotheses:
- `H_P`: `E[Z_t|F_{t-1}] <= 0` on the predictable set `{incumbent deployed}`;
- `H_R`: `E[-Z_t|F_{t-1}] <= 0` on `{challenger deployed}`;
- re-promotion hypotheses defined similarly.

The FWER is `P(reject some true H)`. Then **fixed-sequence (chain) testing with full α at each stage is valid.** This follows from Goeman–Solari Theorem 1, from Fischer–Bofill Roig–Brannath Theorem 3.2 with the online fixed-sequence remark (§4.1), and from Hartog–Lei Theorem 2.5 with e-Fallback weights `e*_R = min(e_P, e_R)`. Each leg must be an e-process for its hypothesis on the common calendar filtration. The rollback e-process may equal 1 until the promotion stopping time and must be stopped or frozen as in R3 (fixed delay only).

The proof idea: if `H_P` is true, any error needs `e_P` to cross first (prob `<= α`); if `H_P` is false, only `H_R` can be falsely rejected (prob `<= α`). This is **better** than "full α, then split": the rollback leg may also use full α. It is a composition of known parts, not new.

The only extra step is that `H_R` is indexed by a random promotion time. It is still a fixed set of laws because it is stated through the predictable indicator. Fischer–Ramdas §2 explicitly allows data-adaptive hypotheses in online closure. I did not find a paper that states this exact promotion/rollback instance.

**(iii) A pathwise (change-point-local) criterion.** Here a promotion is false if it fires while the challenger is not yet better, and a rollback is false if it fires while the challenger is still better. The full-α-then-split rule is **not certified**, and fixed-sequence logic does not apply.
- Counter-scenario: the pre-change null holds until round 800 and the challenger is strictly better afterwards with no reversal. A local false promotion has probability up to `α_P`. After a correct promotion, any rollback is false with conditional probability up to `α_R`. The total can reach `α_P + (1-α_P) α_R`.
- Hence the admissible region is `(1-α_P)(1-α_R) >= 1-α`. This is the repo's two-episode formula (`switching_two_episode_risk_recycling_v1.md:23`), and `α_P = α` forces `α_R = 0`.
- Under this criterion the only valid savings are the Šidák/conditional-error exhaustion of the split (Posch–Bauer; Brannath–Fischer eq. 13) and a cost-weighted choice of `(α_P, α_R)` on that curve. Both are known (weighted Bonferroni or conditional error).
- The worst case requires the e-detector's null crossing probability to approach its level. Ville is often loose for bounded increments (C6 Remark 5), so realised inflation may be small, but no guarantee covers it.

**Bottom line for the question asked.** "Alpha not spent by the rollback detector before promotion can be recycled":
- (i) It is moot: rollback needs no α.
- (ii) Valid and stronger: full α to both legs, by Goeman–Solari Theorem 1, the online closure Theorem 3.2 and Hartog–Lei Theorem 2.5. This is the classical fixed-sequence / graphical "edge weight 1" argument.
- (iii) Invalid under a pathwise "any false switch" criterion.

The repo must first declare which of (i)–(iii) is the claimed guarantee. The contract text currently states (i).

### 5(c). Residual and UNVERIFIED for lever (c)

- **Verdict: CLOSED as a contribution.**
  - Under (i) the gain from dropping the split is a correction to the baseline, not a method.
  - Under (ii) it is the textbook fixed-sequence / graphical / online-closure composition.
  - Under (iii), Šidák/conditional-error allocation and cost-weighted static splits are already closed in-repo (two-episode note; weighted Bonferroni).
- **Residual (conservative, probably composition):**
  - Adaptive, `F_τ`-measurable reallocation at the promotion time under criterion (iii), for example choosing `α_R` from the remaining horizon and costs. It is probably covered by conditional-error / online-closure machinery (C2, C6), but I did not find or verify a theorem for e-detectors with change-point-local errors.
  - Cost-optimal choice of the static split under (iii), which is a one-parameter tuning problem.
- **Action implication (not a result):** if the claimed guarantee is (i), the fair comparator for any track-B candidate is full-α promotion with an uncertified or economic rollback and no re-promotion halving. If (ii) is wanted, use full-α chains. Only (iii) justifies a split.
- **UNVERIFIED:**
  - Bretz–Maurer–Brannath–Posch 2009 full text.
  - Maurer–Bretz 2013 (SBR) theorem.
  - Tamhane–Mehta–Liu 2010 and Qu et al. 2015 bodies.
  - The remaining 23% of 2211.11400 and about 50% of 2407.15733.
  - Hartog–Lei Appendix B.
  - Whether 2211.11400 formally allows data-adaptive `H_i`; the fetched summary says the formal setup uses fixed subsets, while 2407.15733 §2 says hypotheses need not be prespecified.
  - My instantiations in §4(ii)–(iii) are derivations from the cited theorems and have not been independently reviewed.


---
**Checker qualifications (see [CHECK.md](CHECK.md)):** Vernade et al. Prop. 1 is a minimax bandit-regret bound with a sketched proof, so it is an analogue for detection delay, not a proof. Goeman–Solari Thm 1 is offline; Fischer–Bofill Roig–Brannath Thm 3.2 and Hartog–Lei Thm 2.5 assume fixed hypotheses; hypotheses formed after earlier rejections rest on Fischer–Ramdas 2407.15733 §2. Under criterion (iii) the safe statement is the union bound α_P + α_R ≤ α; the product form needs a rollback detector restarted at promotion. Either way α_P = α forces α_R = 0. The lead verdict is in [README.md](README.md).
