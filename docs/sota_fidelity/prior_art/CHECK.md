# Independent check of `pacing_external.md` and `delay_alpha_external.md`

Date: 2026-11-07. Checker: an independent agent. The reports were not trusted. Each primary source
below was re-opened from arXiv or the author-hosted PDF and text-extracted with `pdftotext` into new
directories under the session scratchpad (`.../scratchpad/prior_art_check/{ren15,ren14,premkumar,vernade,goeman,fischer_obr,hartog,zhangmei}/`).
These files are untrusted data and are not committed. No code was downloaded or executed. The
contract criterion comes from `docs/switching_problem_v1.md:42-50`.

Verdicts: **CONFIRMED** (the claim matches the source), **CORRECTED** (the claim is wrong or missing
a material qualification, and the correct statement is given), **UNVERIFIABLE** (with the reason).

## Claim table

| # | Claim | Verdict | Evidence (source, location, short quote) | Correction / qualification |
|---|---|---|---|---|
| 1a | Ren–Johansson–Shi–Shi 1503.04999: CuSum-AC censoring depends on the CuSum statistic (Eq. 9) | CONFIRMED | arxiv.org/pdf/1503.04999v2, Eq. (9): ψ_k = ψ*(1) "if s_{k−1} ≥ a1", ψ*(ε1) "if s_{k−1} < a1". Eq. (8): reset to a1 on up-crossing. Eq. (12): N-level extension | v2 is dated 5 Aug 2016, "to appear in IEEE TCNS", DOI 10.1109/TCNS.2016.2598250 |
| 1b | Theorem 2: asymptotic optimality as the ARL grows | CONFIRMED | Thm 2: "asymptotically (ζ → ∞) optimal for Problem 1". Holds "for any ε > 0" with a = ln ζ | Thm 1 is the equalizer property. Remark 2: parameters "can only be obtained by numerically simulating" |
| 1c | Assumptions: known densities, average rate constraint, infinite horizon, ARL criterion | CONFIRMED | Eq. (2): r(Ψ) = limsup (1/n) E∞[Σγ_k ∣ T ≥ n] ≤ ε. Observations iid with pdfs f0, f1. False alarm via "ARLFA" g = E∞[T]; Lorden delay | The rate constraint applies to the pre-change period only. Remark 3: optimality "does not hold if the total cost is considered" |
| 2 | 1411.3107: the censoring rule depends only on the current observation; statistic-dependent censoring is future work | CONFIRMED | arxiv.org/pdf/1411.3107v1 §II: "decision is made based only on current observations, i.e., θk = µk(Xk)". Stationary µ. Constraint (5): E∞[µ(X1)] ≤ ε. Conclusion lists "time-varying censoring strategies, which may depend on the detection statistic" | Theorem III.4's optimal rule is a randomised LR-interval rule (independent auxiliary κ1, κ2), so it is "current observation plus independent randomisation". It still has no statistic dependence. `docs/lane_b_burst_allocation/B0_prior_art.md:29` says "Yes: censoring depends on the statistic" for both ids, which is wrong for 1411.3107 (and that row was "Search snippet only") |
| 3a | Premkumar–Kumar INFOCOM 2008: posterior-based MDP choice of sensing rate | CONFIRMED | ece.iisc.ac.in author PDF, Eqs. (5)–(8): closed-loop M_{k+1}(Π_k), closed-loop q_{k+1}(Π_k), open-loop q. T ~ geometric(0.01) | — |
| 3b | Theorem 5 structure M*(π) = max{m : d(m;π) ≥ λs} | CORRECTED (qualification) | Thm 5: "If for each π ∈ [0, Γ), d(m; π) decreases monotonically in m". The authors say "We hypothesize this monotonicity property" from numerical Gaussian examples | Theorem 5 is **conditional** on an unproven monotonicity of d(m;π) in m. The report states the structure without the condition |
| 3c | Numbers: adaptive ≈38 vs best constant ≈55 | CONFIRMED (exact) | §V Summary: open-loop least cost "J*(0) = 55 … when the attempt probability, q is 0.15". Closed loop: "J*(0) = 50 for … q_{k+1} and J*(0) = 38 for … M_{k+1}" | Exact values 38 / 50 / 55, n = 10, λf = 100 (PFA ≈ 0.04), λs = 0.5, N(0,1)→N(1,1). This is a single setting and the values are read from a figure/summary, not a table |
| 4a | Vernade–György–Mann 2006.02119 Prop. 1: signal-agnostic algorithms pay delay per change | CONFIRMED | arxiv.org/pdf/2006.02119v2 §4.2, Prop. 1: for any signal-agnostic algorithm "there exists an NSD problem" with R(T) ≥ Ω(min{T, √(K(Γ_T+1)T) + (Γ_T+1)D}). §4.3: NSD-UCRL2 "only pays the price of the delay once" | It is a **minimax** lower bound for bandit regret, with reward distributions chosen adversarially per segment. It is not a statement about detection delay or switching policies |
| 4b | The Prop. 1 proof is only sketched | CONFIRMED | Text: "it is easy to show a lower bound". Footnote 1: "This argument can be made precise by carefully considering" integer segment lengths… Appendices B–D prove Theorems 1–3 only; there is no proof of Prop. 1 | — |
| 5a | Goeman–Solari Thm 1 supports fixed-sequence at full α with strong FWER control | CONFIRMED (static only) | arxiv.org/pdf/1211.3313v1 §2.1 Thm 1 (Sequential rejection principle): monotonicity (2) plus single-step (3) give P_M(R∞ ⊆ F(M)) ≥ 1−α. §6.1: serial gatekeeping, of which fixed sequence is the singleton-family case. §6.2 cites graphical approaches covering "gatekeeping, fixed sequence and fallback procedures" | Hypotheses are a **fixed** collection of submodels and the data are a single static sample. Thm 1 does **not** address an online setting or hypotheses formed after earlier rejections. The fixed-sequence instance is the reader's specialisation (via serial gatekeeping), not a displayed corollary |
| 5b | Fischer–Bofill Roig–Brannath, "The Online Closure Principle", Thm 3.2 | CONFIRMED, with caveat | arxiv.org/abs/2211.11400 (v3, 21 Dec 2023; Ann. Statist. 52(2):817–841, 2024). Thm 3.2: closed procedure "controls the FWER at level α in the strong sense", online if the family is predictable (Def. 3.1). Remark after Def. 4.5: "online analogue of the fixed sequence procedure … reject Hi if p1 ≤ α, …, pi ≤ α" | Formally "(Hi) … can be formally considered as subsets of P", i.e. fixed sets of laws. Decisions are F_i-measurable. The paper does **not** formally state that H_i may be constructed from earlier data. That permission comes from Fischer–Ramdas 2407.15733v3 §2 ("hypotheses do not have to be prespecified"; may be built from F_{i−1}), which the report cites separately |
| 5c | Hartog–Lei, "Family-wise Error Rate Control with E-values", Thm 2.5 | CONFIRMED, with caveat | arxiv.org/abs/2501.09015 (v4, 17 May 2026; v1 15 Jan 2025; no journal ref). §2.3 Thm 2.5: P(max_{i∈H0} sup_t e*_{it} ≥ 1/α) ≤ α, with every e_{I,t} an e-process on a common filtration F_t. §5: e-Fallback is "defined by a fixed sequence of hypotheses" | Setting α_1 = α and α_i = 0 otherwise in eq. (5.1) gives e_I = e_{min I}, so e*_i = min_{j≤i} e_{j,t}. That is fixed sequence at full α. Hypotheses H_1..H_n are fixed and finite. The min is taken at the same t, so a promotion e-process must be stopped/frozen at its crossing for the rollback leg to remain testable. Thm 2.5 does not cover data-adaptively formed hypotheses |
| 5d | Together, 5a–5c support "pre-fixed order, full α each, stop at first non-rejection ⇒ strong FWER ≤ α, including online with later hypotheses formed after earlier rejections" | CORRECTED (partly) | as above | The **pre-fixed order / full α / stop at first non-rejection / strong FWER** part is supported by all three. The **online** part is supported by 5b and, for e-processes over time, 5c. The **"hypotheses formed after earlier rejections"** part is supported by none of the three theorems as stated. It rests on Fischer–Ramdas 2407.15733 §2, or on the report's device of writing H_R through a predictable deployment indicator so that it is a fixed set of laws. The report's attribution of Goeman–Solari Thm 1 to the sequential/online case is an overreach |
| 6a | Criterion (i): P(any promotion) = P(first promotion) ≤ α; rollback needs no α | CONFIRMED, with stated requirements | Logic check (below) | Requires A_0 = 0 (start on the incumbent). It holds with fresh detectors for re-promotions, since every re-promotion path is already inside {first promotion ≤ T}. It requires the **global** null as in the contract. Only the null on the rounds before the first promotion is actually used. It fails for a time-varying null |
| 6b | Criterion (iii): (1−α_P)(1−α_R) ≥ 1−α, so full α on promotion forces α_R = 0 | CONFIRMED in conclusion; CORRECTED in framing | Logic check (below) | The product formula needs no independence. It needs **conditional validity** of the rollback leg given F_τ at the promotion stopping time τ (a fresh e-detector started at τ). Without that, the safe statement is the union bound α_P + α_R ≤ α. Both conditions force α_R = 0 when α_P = α. "Admissible region" overstates: the product curve is a sufficient (certifying) condition. It is necessary only when both levels are attainable in the worst case, and Ville is generally loose in discrete time |
| 7a | Spot-check: Zhang & Mei, TSSRP, 2009.11891 | CONFIRMED | arxiv.org/abs/2009.11891 (v2, 10 Apr 2022). Hard per-time constraint "Σ_k δ_{k,t} = q at each time step". Thm 1: Geometric(p) prior link to Bayes. "Theorem 2 … E∞(T) ≥ A/K". Thms 3–4 cover sensor layouts. Technometrics 65(1):33–43 (Feb 2023), DOI 10.1080/00401706.2022.2054861, per a library record | arXiv says "Published in Technometrics, 2022" (online-first). The 2023 issue citation is consistent |
| 7b | Spot-check: Halme & Koivunen survey 2604.18008 | CONFIRMED (minor attribution slip) | arxiv.org/abs/2604.18008 (v1 only, 20 Apr 2026; "Submitted to Entropy"; DOI 10.3390/e28050566 listed). §3.2: "|A_n| ≤ L ∀n if at most L<K of the sensors can be deployed". No total-budget or remaining-time rule found in the full HTML. Conclusion: "develop adaptive sampling rules with rigorous performance guarantees" | The report credits the "exploration increment Δ" to Xu, Mei & Shi. The survey credits the rule to Liu, Mei & Shi [37]. Xu, Mei & Shi [38] study the effect of Δ. The negative-search conclusion stands |

## Logic check for claim 6

**Criterion (i).** The error event is E = {∃t ≤ T : A_{t−1} = 0, A_t = 1}. Let τ_1 be the first
promotion time. If A_0 = 0, then E = {τ_1 ≤ T} exactly. Every later promotion, including one made
by a fresh detector after a rollback, lies on a path where τ_1 ≤ T already happened. So
P(E) = P(τ_1 ≤ T). Before τ_1 the incumbent is deployed and only the first-phase detector acts. If
that detector is a valid level-α e-detector under the conditional null on those rounds, then
P(E) ≤ α. The rollback and re-promotion detectors never enter the bound, so they need no α. The
argument requires:

- A_0 = 0.
- The null on all rounds before τ_1. The contract's global null "E[Z_t | H_t] ≤ 0 for every round"
  implies this. The rounds after τ_1 are never used.
- That the error is "any promotion" under that null.

With a **time-varying** null, where the error is a promotion made while the challenger is not
currently better, the reduction breaks. A correct first promotion, then a rollback, then a
re-promotion inside a later no-benefit regime is an error that a false first promotion does not
imply. Re-promotions and rollbacks then need their own α. So (i) holds only for the global
(all-rounds) null. The contract says exactly this: "It does not certify every switch in a stream
containing positive and negative regimes". (i) is therefore a weak guarantee. It controls promotions
only in streams where the challenger never helps.

**Criterion (iii).** Take the report's single-change scenario. Let F_P be a false promotion before
the change, and F_R a rollback while the challenger is better after a correct promotion at stopping
time τ. Then P(error) = P(F_P) + P(F_R ∩ F_P^c). Suppose the rollback detector is started fresh at
τ and is valid conditionally on F_τ (Ville applied conditionally). Since {correct promotion at τ}
∈ F_τ:

- P(F_R ∩ F_P^c) ≤ α_R · P(F_P^c),
- so P(error) ≤ p + (1−p)α_R with p = P(F_P) ≤ α_P,
- and since this is increasing in p, P(error) ≤ α_P + (1−α_P)α_R = 1 − (1−α_P)(1−α_R).

Requiring this to be ≤ α gives the product condition. Independence is **not** needed. Conditional
(F_τ) validity of the rollback leg is. If the rollback detector is only marginally valid, for
example if it runs from time 0 or its validity is not conditional on the promotion branch, the
available bound is the union bound α_P + α_R ≤ α. Either way, α_P = α leaves α_R = 0, i.e. no
certified rollback. With reversals, each extra leg adds a factor (1 − α_j). "Forces" is about what
the bound certifies. Realised error may fall below α because e-detector overshoot makes Ville loose,
but that gives no guarantee.

## Overstatements and imprecisions in the reports

**`pacing_external.md`**

1. §2.3 states Premkumar–Kumar Thm 5's structure without its hypothesis. The monotonicity of
   d(m;π) is conjectured from numerics, not proved.
2. §2.3 / §4: "closed-loop beats best open-loop" rests on one numerical setting with a Bayesian
   Lagrangian cost (the report does say "one numerical setting"). It shows nothing about a hard cap
   or a frequentist guarantee. Calling it the analogue of "adaptive pacer beats fixed pacer" is
   suggestive, not evidential.
3. §2.8: minor misattribution of the Δ exploration rule (Liu–Mei–Shi, not Xu–Mei–Shi). The survey
   also has an Entropy DOI (10.3390/e28050566), which the report omits.
4. §2.2 relayed the 1411.3107 "future work" statement from a summarising fetch. It is now
   confirmed verbatim, so that UNVERIFIED item can be closed.
5. §3 item 1 relies on the repo's own audit of Geng–Bayraktar–Lai for "uniform/greedy is
   first-order optimal". This checker did not re-verify it.

**`delay_alpha_external.md`**

1. B1 "CLOSES the hope of beating '+d per change' without auxiliary information" overstates what
   Vernade Prop. 1 gives. It is a sketched minimax bandit-regret lower bound with adversarial
   per-segment reward laws, not a detection or switching result. The repo's own lower bound does
   the real work here. Vernade is a supporting analogy.
2. §4(ii) cites Goeman–Solari Thm 1 as support alongside the online results. Thm 1 is
   static/offline with fixed hypotheses. Hartog–Lei Thm 2.5 covers time but with a fixed finite
   hypothesis set. None of the three cited theorems covers hypotheses defined after a random
   promotion time. That step rests on Fischer–Ramdas 2407.15733 §2, or on the predictable-indicator
   formulation, which the report itself calls "my instantiation". The C1/C2 "CLOSES" verdicts
   should read "closes for fixed hypotheses".
3. §4(ii): H_P is defined "on the predictable set {incumbent deployed}". That set also contains
   post-rollback incumbent periods, so it overlaps with the re-promotion hypotheses. The chain's
   hypotheses should be indexed by episode.
4. §4(iii) calls (1−α_P)(1−α_R) ≥ 1−α "the admissible region". It is a sufficient condition that
   needs conditional validity of the rollback leg at τ, not an exact feasibility region. The
   union-bound version is the assumption-light alternative. The conclusion (α_P = α ⇒ α_R = 0) is
   unaffected.
5. §4(iii) borrows the repo's two-episode formula (`switching_two_episode_risk_recycling_v1.md:23`).
   That note concerns two promotion looks on the no-promotion branch, not promotion then rollback.
   The algebra carries over, but the "exact under the full-history conditional null" claim there
   does not automatically transfer.
6. §4(i): "valid, trivially" is correct, but the report should state A_0 = 0 and that the guarantee
   is vacuous for any stream in which the challenger ever helps. The contract already notes this.
