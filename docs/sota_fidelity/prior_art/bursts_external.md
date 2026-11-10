# External prior-art check: scheduled / periodic burst sampling vs uniform sampling

2026-11-10. Retrieval-agent report (web search + selected PDF text extraction; no code executed).
Downloaded PDFs (text only) are in the session scratchpad `prior_art_bursts/`.
Reading depth: **opened** = PDF text extracted and searched; **not opened** = search-result abstract or
snippet only (statements below are then the listing's, not verified). The WebSearch tool is a summarising
layer, so every "not opened" row should be treated as unverified. One extended search was refused by the
tool backend and was not retried; coverage is therefore incomplete (see section 5).

Already audited in the repo (per `audited_arxiv_ids.txt`): 1309.5396, 1211.3729, 1105.1361, 1212.4717,
1408.4747. 1411.3107 and 1503.04999 are covered by `pacing_external.md`. None of these covers bursts, see below.

## 1. Source table

| id / DOI | Title, authors, year | Opened | Location | Burst vs spread | Minimax / Bayes | Budget | Delay |
|---|---|---|---|---|---|---|---|
| arXiv 1309.5396 (IEEE TIT 60(10), 2014) [already audited] | Bayesian QCD with sampling right constraints; Geng, Bayraktar, Lai | yes | Thm 1 (optimal sampling interval t_{n+1} is a function of pi_{t_n}, i.e. adaptive, Remark 1); Thm 2 (V_n concave, threshold stopping); Prop 2 (uniform sampling with interval varsigma gives upper bound on ADD when N >= \|log alpha\|/(\|log(1-rho)\| varsigma)); Thm 3 (DP for stochastic rights); Remark 6, Sec. on greedy rule | Optimal schedule is an adaptive DP, no closed form. The only explicit schedules are **uniform** (Prop 2, upper bound) and **greedy** (sample whenever a right is available, first-order optimal). No periodic-burst statement. | Bayesian (geometric prior) | hard N, or stochastic rights | none |
| arXiv 1411.3107 / 1503.04999 [in pacing_external.md] | Ren et al. censoring | previous report | see pacing_external.md | stationary or statistic-dependent censoring, not bursts | minimax (Lorden) | average rate | none |
| arXiv 1105.1361, 1211.3729, 1408.4747, 1410.3450 [1105.1361, 1211.3729, 1408.4747 already audited] | DE-CuSum family; Banerjee, Veeravalli | search snippets only | n/a | Baseline is "fractional sampling" (skip a fixed fraction, deterministically or by coin flip); DE-CuSum (on-off, statistic-driven) beats it. No finding about burst structure. | minimax and Bayes | average pre-change cost | none |
| arXiv 1105.6024; INFOCOM 2008, DOI 10.1109/INFOCOM.2008.198 | Sleep-wake scheduling for quickest detection; Premkumar, Kumar | INFOCOM PDF opened in `pacing_external.md`; 1105.6024 snippet only | Sec. V of INFOCOM paper | Closed-loop (posterior-driven) beats best open-loop constant wake probability. 1105.6024 states a fixed deterministic duty cycle ignores prior information and is not optimal (snippet). | Bayes | Lagrangian cost | none |
| arXiv 1302.0792 (Cohen et al.) | Probe scheduling for silent failures; Cohen, Hassidim, Kaplan, Mansour, Raz, Tzur, 2014 | yes (abstract, intro, pieces) | abstract; Sec. on deterministic vs memoryless schedules | Worst-case (MAX) objective over elements, not over failure time. Compares deterministic and randomised (memoryless) probe schedulers. Not a change-time game. | worst-case over elements | probing overhead | none |
| arXiv 2602.09394 | The Critical Horizon: inspection design for multi-stage operations; (authors not recorded) | yes (text) | Sec. 6 ("uniform checkpoint spacing is minimax-optimal under homogeneous signal attenuation", maximal-gap L(T)) | **Spread**: minimises the maximal gap among m inspection points. Single-sample inspections, no detector needing m>1 samples. Preprint, not peer-reviewed as far as seen. | minimax (gap) | fixed m | none |
| Derman, "On minimax surveillance schedules", Naval Res. Logist. Q. 8 (1961) 415-419; Roeloffs, NRLQ 10 (1963) 307-322 (RePEc); Beichelt (1975, 1981); Leung, EJOR 132 (2001) 106-115 | Minimax inspection schedules for unknown / partly known failure distributions | **not opened** (listing and snippets only) | n/a | Derman: schedule minimising the maximum expected cost for a completely unknown lifetime distribution. Formulae not verified. | minimax over failure distribution | fixed number or cost | none |
| Sanborn, J. Nucl. Mater. Manage. 20(4), 1992 | Examination of randomized inspection schedules w.r.t. two detection criteria | listing abstract fetched | abstract | For expected detection time, no randomized scheme beats periodic (two of three classes). For timely-detection probability, periodic is optimal when resources are adequate; with limited resources, randomly selecting fixed-interval opportunities is optimal. | average / probability, not adversarial minimax | limited inspections | none |
| Alpern, Morton, Papadaki, "Patrolling games", Oper. Res. 59(5), 2011; Alpern, Lidbetter, Papadaki, "Optimizing periodic patrols against short attacks", EJOR 2019; Alpern and Gal book 2003 | Patrolling games with attack duration | **not opened** (snippet) | n/a | Attacker of fixed duration vs patroller; value of the game is an interception probability. Randomised patrols are the equilibrium notion. Structurally the closest to "cover every window [nu, nu+w]". | zero-sum game | patrol coverage | none |
| Reynolds, Amin, Arnold, Nachlas (1988, VSI X-bar); Park and Reynolds (1994, 1999, VSS / VSR); Costa (1997); Duncan economic design (1956, 1971); Tagaras (1996) and Tagaras and Nikolaidis (2002) [pacing_external.md] | Variable sample size / interval control charts | **not opened** (snippets) | n/a | Classic SPC trade-off: sample size n versus interval h. Adaptive large/small samples chosen by the current chart statistic. Designs are optimised numerically per cost model, no theorem on bursts under a hard budget. | average run length / economic cost | cost per hour | none |

## 2. What the literature says about each ingredient

1. **Optimal sampling under a hard observation budget (1309.5396).** The exact solution is an adaptive
   DP; the paper proves a uniform schedule gives an upper bound on delay and a greedy rule is first-order
   optimal as alpha -> 0. In the asymptotic regime (budget >> required samples) the schedule does not
   matter to first order, so the paper has no statement about regimes where the budget covers only a few
   detections. It has no delay and no minimax change time (Remark 10 cites Geng-Lai for the non-Bayesian
   stochastic-energy greedy result; that paper was not opened).
2. **Duty cycling.** Premkumar-Kumar and DE-CuSum show closed-loop beats open-loop. The open-loop
   comparators are constant-rate or deterministic fractional skipping. No source found compares periodic
   bursts with uniform spacing for worst-case delay.
3. **Inspection scheduling.** Closest classic: Derman / Roeloffs / Beichelt / Leung (minimax
   inspection schedules, not opened), Sanborn 1992 (periodic is optimal for average-delay objectives),
   and 2602.09394 (uniform spacing is minimax-optimal for a gap objective). All treat an inspection as
   a single perfect test that reveals the failure. They give a spread schedule because one test per window
   suffices.
4. **Randomisation against an adversary.** Patrolling games (Alpern et al.) give the randomised-vs-
   deterministic structure with an attack of finite duration, but the objective is interception
   probability, not delay, and nothing was read in detail.
5. **Bursts because m>1.** Nothing found. The SPC literature trades n against h but with adaptive
   rules and average-run-length objectives.

## 3. Closest prior art

- **Closest on structure:** Alpern-Morton-Papadaki patrolling games (window-coverage versus an adversary
  with an attack of fixed duration) and Derman/Roeloffs minimax surveillance schedules (not opened).
  If a burst-length versus gap-length theorem exists for "attack lasts w, need to be present k times in
  the window," it would most likely sit in the patrolling-game or inspection-scheduling literature and
  could subsume the fluid calculation. This was not checked.
- **Closest on detection:** 1309.5396 (hard budget, uniform vs greedy vs adaptive DP) and DE-CuSum/Ren
  (evidence-state-dependent rates). Neither covers open-loop bursts, finite-horizon minimax, or delay.

## 4. Verdicts

| Claim | Verdict | Confidence | Basis |
|---|---|---|---|
| (b1) Periodic bursts beat uniform sampling for worst-case delay when the detector needs m>1 samples under a budget | **Not found** as a stated result. The ingredients (windows needing several hits, minimax adversary) are standard in patrolling and inspection games, so a version may exist outside the sources opened. | Medium-low. Several key sources unopened, one search refused. | No opened source discusses burst structure. Opened inspection sources (2602.09394) and the Sanborn listing favour spread / periodic schedules for single-test or average-delay settings, which is the opposite regime. |
| (b2) Random-phase schedules beat deterministic ones against an adversarial change time | **Partly published.** The general principle (randomisation helps against a worst-case timing adversary; deterministic schedules are exploitable) is established in inspection and patrolling games and noted in Cohen et al. for probes. The specific detection-delay-with-window-coverage version was not found. Sanborn 1992 is a counter-signal for average-delay criteria. | Medium | Alpern et al. (snippet), Cohen et al. 1302.0792 (opened, abstract-level), Sanborn (listing). |
| (b3) Combination with delayed labels and an anytime-valid detector | **Not found.** No source with label delay, rate cap, and an e-detector together with schedule design. | Medium-high (consistent with `pacing_external.md` finding no match). | Search log below; all QCD sources found have zero delay. |

Implication for novelty wording: do not claim "bursts beat uniform sampling" as new in general. A safe
claim is the specific finite-horizon fluid analysis with label delay, a per-round availability cap,
and an m-label e-detector requirement, stated as an instantiation of window-coverage scheduling, with
the Derman/Roeloffs and patrolling-game literature cited as unverified related work until opened.

## 5. Gaps and limitations

- Not opened: Derman 1961, Roeloffs 1963/1967, Beichelt, Leung 2001, Alpern et al., Geng-Lai non-Bayesian
  stochastic-energy paper, Reynolds/Park VSS/VSI papers, Zhang-Mei, Krishnamurthy, Tartakovsky observation
  control, Liu-Mei-Shi. Kander-Raviv and Dresher / Garnaev were not searched individually.
- The search tool returns summaries; titles and results attributed to "snippet" are unverified.
- The prior verdicts can flip if Derman/Roeloffs or Alpern et al. contain a burst result. Recommended next
  step: open those four references before any novelty claim goes into a paper.

Search log (2026-11-10): minimax inspection fixed number; Geng-Bayraktar-Lai sampling right; randomized vs
equally spaced inspection game; Banerjee-Veeravalli open-loop; Derman/Roeloffs; VSS/VSI/Duncan; Premkumar
sleep-wake duty cycle; Alpern-Gal patrolling. One extended-mode query was rejected by the tool backend.

## Checker corrections (2026-11-10, see BURSTS_CHECK.md)

- 1302.0792 (Cohen et al., probe scheduling) does maximise over failure time (Sec. 2.1); it compares deterministic vs randomised schedules, but with m = 1 (one probe detects).
- 2602.09394 (Emadi) is off-topic: "uniform spacing is minimax" there concerns checkpoint placement across process stages, not an unknown change time.
- Gaps filled: Reynolds & Stoumbos 2004 (via Ajadi & Zwetsloot 1906.08038): at a fixed sampling rate, spread single observations are best for CUSUM/EWMA; grouping helps only memoryless Shewhart charts. Geng & Lai 1302.3834 (non-Bayesian, worst-case delay): greedy sampling with CUSUM. Alpern–Morton–Papadaki 2011: randomised patrols essential against a timing adversary (m = 1). Derman/Roeloffs: abstracts only.
