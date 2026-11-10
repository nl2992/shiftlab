# Independent check: periodic-burst label schedules (prior art)

2026-11-10. Checker report. PDFs were saved to the session scratchpad `prior_art_bursts_check/` and
only their text was extracted; no downloaded code was run. "Opened" means the full text or the
publisher or repository abstract was read. "Snippet" means only a search-tool summary was seen,
and those statements are unverified.

## Claim table

| Claim / source | Opened | Status | Location and note |
|---|---|---|---|
| Geng–Bayraktar–Lai arXiv 1309.5396: Thm 1 / Remark 1 (the optimal sampling time depends on π_{t_n}, so the schedule is adaptive) | yes | verified | Remark 1 (text l.626 ff.). Bayesian setting with a geometric prior. |
| 1309.5396 Prop 2 (uniform interval ς gives an asymptotic ADD upper bound if N ≥ \|log α\|/(\|log(1−ρ)\|ς)) | yes | verified | Prop 2, eq. (26)–(27). It is an α→0 bound with no statement about bursts. The greedy rule (sample whenever a right is held) belongs to the stochastic-rights section (Sec. IV) and is first-order optimal as α→0, not exactly optimal (l.1188–1192). |
| 1309.5396 Remark 10 cites Geng–Lai as the non-Bayesian stochastic-rights work | yes | verified; gap (d) filled | Ref. [17] is Geng & Lai, IEEE TSP 61 (2013) 5090–5102, arXiv **1302.3834**. I opened the abstract: it is minimax (Lorden-type) worst-case delay under a stochastic energy-harvesting constraint. "Spend energy whenever the battery is non-empty" plus CUSUM is optimal under an algorithm-level ARL constraint and asymptotically optimal under a system-level one. That is greedy, with no bursts, no horizon, and no delay. |
| arXiv 1302.0792 | yes (Sec. 1–2) | **qualified / partly wrong** | Cohen, Hassidim, Kaplan, Mansour, Raz, Tzur, *Probe scheduling for efficient detection of silent failures* (v3 2014). The report says the objective is worst-case "over elements, not over failure time". **That is wrong.** Sec. 2.1 defines M_t, the sup over failure time t, and studies Me·Mt and Mt·Ee. It compares deterministic, memoryless and general stochastic schedules: deterministic gives hard guarantees but has a D2M gap, and computing the stochastic optimum is NP-hard. One probe covering e detects the failure (m=1), the horizon is infinite, and there is no budget horizon. |
| arXiv 2602.09394 | yes | verified, but it is off-topic | Emadi, *The Critical Horizon: Inspection design principles for multi-stage operations and deep reasoning* (UNC, v2 Feb 2026). Thm 3, Sec. 6: uniform checkpoint spacing minimises the maximal gap L(T) under homogeneous signal attenuation. The problem is credit assignment over the **stages** of a process, not over a change time. It is weak evidence for "spread". |
| (a) Reynolds & Stoumbos, JQT 36(4) 2004 343–366, "Should observations be grouped…"; Technometrics 46(2) 2004 200–214 | publisher page refused (403); secondary source opened | qualified (secondary) | Ajadi & Zwetsloot arXiv 1906.08038, l.124–128, summarises the univariate result (text opened). At a fixed sampling rate: **for CUSUM/EWMA, n=1 (spread) is best; for Shewhart, n>1 (grouped) is better.** Snippet of the Technometrics abstract: n=1 with EWMA/CUSUM beats the best Shewhart n>1, and concentrated vs dispersed n>1 depends on transient shifts shorter than d. Shift-size details were not seen. Duncan 1956 and the VSI/VSS papers were not opened. |
| (b) Derman 1961 NRLQ 8:415–419; Roeloffs 1963 NRLQ 10:307–322; Leung 2001 EJOR 132 | Roeloffs (RePEc) and Leung (IAOR) abstracts only | unverified | Derman gives a minimax schedule for a completely unknown lifetime distribution with a single perfect inspection. I could not find the **form** of that schedule (equal spacing or otherwise) in any source I could open, so it is not asserted here. Leung adds *imperfect* inspection, the nearest single-test analogue of m>1, but the result was not seen. Barlow–Hunter–Proschan 1963 was not opened. |
| (c) Alpern, Morton, Papadaki, *Patrolling games*, Oper. Res. 59(5) 2011 | yes (LSE accepted version) | verified (structure) | An attack needs m consecutive periods at one node, and a **single** patroller visit intercepts it. The value is an interception probability, and randomisation is intrinsic: "a predictable Patroller is an ineffective one" (l.91). There is a periodic game variant (l.166–223). Detection needs one hit (not m>1), there is no budget, and the objective is not delay. |
| Sanborn 1992 (randomised vs periodic inspection) | no | not rechecked | Listing only. |
| Zhang–Cheung (FINAL_RESEARCH_PROPOSAL l.201) | yes (NeurIPS abstract page) | identified | Xilin Zhang and Wang Chi Cheung, *Piecewise-Stationary Bandits with Knapsacks*, NeurIPS 2024. It uses an inventory-reserving algorithm and proves an O(log(η_max/η_min)) competitive ratio against a dynamic benchmark. Its objective is cumulative reward, not detection. |
| In-repo G4 pre-screen stop rule | yes | verified | `FINAL_RESEARCH_PROPOSAL.md:197–201`: stop if the result is "fixed or uniform gating up to constants, or maps onto Geng–Bayraktar–Lai sampling rights or Zhang–Cheung reservation". The expected outcome was stop. |
| In-repo A2 "contiguous confirmation burst" | yes | verified | `12_NOVELTY_DECISION.md` A2 section: 108 tight-α cells (54 families), T=8, B=3, d=1, all bursts [2,3,4] / [3,4,5] / [1,2,3]. Unconstrained optima spread out instead ([2,4,6]). `13_A2…:189–270`: Prop 6 (support certificate) and Thm 7 (chain reduction under (P), "promote only on B unanimous positives"). Thm 7 is stated as the explanation for the burst. |
| In-repo WP3 temporal schedule | yes | verified | `docs/data_efficient_edetector_prescreen_protocol.md:47–50`: paced intensity ×0.25 before index 1200 and ×1.75 after. This is an end-loaded **step** schedule, not periodic, and it encodes a late-onset prior (onset fractions .50/.75). Results l.30–35: 20/20 detections, best registered configuration, recorded as "a standard baseline finding". |

## Verdicts

**(b1) Bursts beat spread when m>1 under a budget: partly published, in the opposite direction.**
The closest classic analogue is the SPC n-vs-h trade-off at a fixed sampling rate. There, grouping
helps only for a memoryless detector (Shewhart), which needs several samples *within one look*.
For accumulating detectors (CUSUM/EWMA, like our SR/e-detector), spread n=1 wins. Those results are
infinite-horizon and steady-state, with no hard budget. None of the opened sources shows bursts
beating spread for an accumulating detector over a finite horizon. In the fluid check, the gain
from bursts comes from integer and boundary effects at B/m≈3 (it reverses at m=54). It is not a
structural mechanism, which fits the SPC result.

**(b2) Random phase vs deterministic against an adversarial onset: published as a principle.**
Patrolling games (verified) and Cohen et al. (verified: deterministic vs stochastic schedules
under a sup-over-time objective) both establish that randomised schedules can beat deterministic
ones against a worst-case timing adversary. The specific form here (expected delay, m-hit
coverage, budget) was not found. It is a routine corollary, not a contribution.

**(b3) Combined with label delay and an anytime-valid detector: not found.** Every detection
source opened has zero delay (1309.5396, 1302.3834, Cohen et al.). Delay d only shifts the window
by a constant.

**(b4) Is A2 the same mechanism? No.** A2's burst is a single contiguous block, chosen under a
Bayesian HMM prior with d=1. It is driven by a *risk* constraint that requires unanimous
confirmation, and pruning dead histories makes the chain calendar-implementable (Thm 7).
Without the constraint, A2 optima spread out. The pacing burst is periodic, is chosen against an
adversarial onset, and has no confirmation constraint. Both share "need several labels close
together", which is the Shewhart-grouping intuition. A2's evidence does not transfer: its
unconstrained optima spread out, which matches the SPC finding. WP3's end-loaded step is a third,
prior-driven mechanism.

## Is a new protocol worth it?

Prior art does not settle the exact claim, but the case for a new protocol is weak. The
randomisation half (b2) is a known principle. For accumulating detectors, the SPC literature
points towards spread. The fluid gain is about 8–10%, depends on integer effects at B/m≈3, and
reverses at m=54. It is below the screen's 10% bar before stochastic thresholds and label cost are
added. The G4 stop rule ("uniform up to constants") already fires on this evidence. A protocol is
justified only as a cheap, locked hygiene check that closes the "untested class" caveat in
`pacing_minimax_results.md`: 2–3 burst configurations, random phase, the same harness, and a
pre-registered expectation of STOP. It should not be run as a search for a novelty claim. Any
write-up should cite Reynolds–Stoumbos, Cohen et al. and Alpern et al., and should state that
Derman/Roeloffs remain unopened.
