# B0c: Transient change detection reads (arXiv 1501.05930, 1302.6574)

Date of reads: 2026-10-28. Method: WebFetch (a small summarizing model applied to arXiv pages). Nothing here was checked against the PDF or LaTeX source. Quotes below are model-extracted fragments, not verified verbatim. Treat every quote as "to be checked against the PDF before citing."

## Verification level

- **arXiv 1501.05930**: VERIFICATION LEVEL = partial. Abstract page and HTML full text read via WebFetch (https://arxiv.org/abs/1501.05930, https://arxiv.org/html/1501.05930v5). The HTML text was 105,152 characters. The tool summarized characters 0 to 100,000. The final 5,152 characters were NOT ACCESSED. Section numbers come from the summarizer and are unverified.
- **arXiv 1302.6574**: VERIFICATION LEVEL = partial. Abstract page and HTML full text read via WebFetch (https://arxiv.org/abs/1302.6574, https://arxiv.org/html/1302.6574v2). Theorem and section numbers are from the summarizer. Proof-level notation is garbled in the extraction.

## Scope correction (important)

The task assumed 1302.6574 is a quick or transient change detection paper. It is not. It is a communication paper:

- **1302.6574** is "Energy and Sampling Constrained Asynchronous Communication" by Aslan Tchamkerten, Venkat Chandar, and Giuseppe Caire (cs.IT, submitted to IEEE Trans. Inf. Theory, v1 26 Feb 2013, v2 22 Mar 2013). It studies decoding a single sparse, asynchronous message under a sampling-frequency constraint. It is not change detection and it has no change-detection theorems.
- **1501.05930** is "Sampling Constrained Asynchronous Communication: How to Sleep Efficiently" by Venkat Chandar and Aslan Tchamkerten (cs.IT, v1 23 Jan 2015, v5 24 Oct 2017, accepted to IEEE Trans. Inf. Theory per the abstract page). The change-detection content is one part of it. Its method is "a new, multi-phase adaptive sampling scheme for locating transient changes." A search snippet gave the earlier title "Quickest Transient-Change Detection under a Sampling Constraint." I did not verify that title against an arXiv version.

## Paper 1: arXiv 1501.05930

**Observation model (Sec. II, III-A).** Observations are i.i.d. P_0 outside the change and i.i.d. P_1 inside the window. The receiver observes only a subset of outputs. The sampling times S_1 < S_2 < ... may be non-adaptive or adaptive (S_j = g_j of past samples). The sampling constraint is a sampling-rate constraint, not a hard pathwise budget. Definition 8 (Sec. III-A) defines the sampling rate as the smallest r such that P(|S^tau|/tau <= r) >= 1 - eps. The summarizer found no separate total sample budget and no cost model.

**Change model (Sec. III-A).** Binary hypothesis P_0 vs. P_1 on a finite alphabet with finite D(P_1||P_0). The change length n is known as a parameter. The summarizer found no explicit statement that the detector knows n. nu is uniform over {1,...,A}, where A = 2^{alpha n}. Only one change occurs. The change is transient: it occupies the window [nu, nu+n-1] and then reverts to P_0. Single window, duration n.

**False-alarm criterion (Def. 6, Sec. III-A).** P(tau < nu) with the probability taken under P_0. Vanishing false-alarm probability is required for achievability (Def. 9).

**Delay criterion (Def. 7, Sec. III-A).** The smallest l >= 0 such that P(tau - nu <= l - 1) >= 1 - eps. This is a quantile-type "typical" delay, not E[(tau - nu)^+]. The summarizer quoted the paper's remark that this avoids "a large penalty in the tail event where tau is much larger than nu." Achievability (Def. 9) requires delay sub-exponential in n, and a sampling rate rho_n.

**Adaptive multistage sampling scheme (Sec. IV-C).** Parameters: f(n) = omega(1) increasing, rho_n = f(n)/n, s-instant spacing Delta-bar(n) = n / f(n)^{1/3}, and Delta_0 = f(n)^{1/3}. Recursion: Delta_i = min{ 2^{c Delta_{i-1}}, n*(alpha)(1+eps) } with 0 < c < D(P_1||P_0).
- Phase 0 (preamble): take Delta_0 consecutive samples and test typicality against P_1. If the test fails, wait for the next s-instant and repeat.
- Phases 1 to l-1 (confirmations): take a fresh block of Delta_i samples and test again. A failure returns the detector to phase 0.
- Phase l (full block): take n*(alpha)(1+eps) samples. If typical, stop. Otherwise return to phase 0. If nothing is typical by time A+n-1, stop.
- Example f(n) = log log log log n gives two confirmation phases. The paper stresses that the first phase must dominate the sampling rate so that later phases are rarely reached under P_0 (Sec. IV-D).

**Achievability and converse theorems (Sec. III-B), from the summarizer.**
- Theorem 4 (full sampling). Claims: (1) the supremum of achievable exponents is D(P_1||P_0); (2) for alpha < D(P_1||P_0), liminf d_n/n*(alpha) >= 1; (3) any such alpha is achievable with limsup d_n/n*(alpha) <= 1. Minimum detectable change n_min(A_n) ~ log A_n / D(P_1||P_0).
- Theorem 5 (sparse sampling). For alpha < D(P_1||P_0), any rho_n = omega(1/n) is achievable with limsup d_n/n*(alpha) <= 1. If rho_n = o(1/n), the detector samples only from P_0 with probability tending to one, and the delay is Theta(A_n) whenever the false-alarm probability tends to zero.
- Lemma 1 (Sec. IV-B). For alpha > 0 and rho_n = o(1/n), with probability at least 1 - o(1) the detector takes no samples inside {nu,...,nu+n-1}.
- Verbatim status: NOT VERIFIED. These are summarizer restatements.

**Adaptive vs. non-adaptive separation and scaling (Sec. I, II, IV-B, IV-D).**
- Non-adaptive sampling reaches full-sampling capacity but the delay is multiplied by 1/rho (Sec. I).
- The minimum sampling rate for detection is Theta(1/n): sufficiency needs rho = omega(1/n), necessity needs rho = Omega(1/n). The converse extends to adaptive sampling (Sec. IV-B).
- A two-phase scheme reaches only omega((log n)/n) by a Sanov-type argument and is suboptimal (Sec. IV-D).
- Minimum delay n* = Theta(B) (Eq. 7, communication setting).

**Label delay and hard budget.** No label delay is discussed. The only budget is the sampling-rate constraint rho. The summarizer quoted an expected sample count bound E_0|S^t| <= t * f(n)^{2/3}/n * (1+o(1)) (Eq. 33). I did not check this against the source.

## Paper 2: arXiv 1302.6574

**Observation model (Sec. II).** Discrete memoryless channel with input alphabet X union {star}, output Y, transition Q(y|x). Idle symbol star is pure noise. Before and after transmission the receiver sees Y_i ~ Q(.|star). Sampling constraint: sampling times S_1 < S_2 < ... with sampling frequency rho in (0,1] (Def. 3: smallest r with min_m P_m(tau/S_tau <= r) >= 1 - eps). This is a sampling-rate constraint. The summarizer found no hard pathwise budget.

**Message/burst model (Sec. II).** B information bits give M = 2^B messages coded into length-n codewords. A message arrives at random time nu uniform over {1,...,A}, with A = 2^{beta B}, beta = log A / B. One-shot: only one message arrives. Not a change detection model.

**Cost and delay definitions.** Cost K(C) = max_m sum_i k(c_i(m)), with only star at zero cost (Def. 2). Delay d(C, eps) = smallest integer l with min_m P_m(S_tau - nu <= l-1) >= 1 - eps (Def. 4). Achievability requires (1/B) log d(C_B, eps_B) <= eps_B (Def. 5), i.e., sub-exponential delay.

**Sampling schemes (Sec. IV, proof sketches).**
- Non-adaptive (proof of Theorem 2): sampling only at transmission times that are multiples of 1/rho. If star is in X, the codeword is sent in the first n transmission times at or after nu. Decoder uses joint-type typicality against all codewords and breaks ties randomly. If star is not in X, the timeline is split into superperiods of length n/rho with transmission in the last n steps.
- Adaptive (proof of Theorem 3): sparse mode samples at S_j = ceil(j/rho), computes the type of the last log n samples, and applies a switch test: stay sparse if P_star(type) > 1/n^2, otherwise switch to dense mode. Dense mode samples continuously for at most n steps and applies typicality decoding. If no codeword is typical after n steps, return to sparse mode. Each codeword begins with log n repetitions of a symbol x with Q(.|x) != Q(.|star) (preamble). The 1/n^2 threshold can be any decreasing function decaying no faster than polynomially.

**Theorems (from the summarizer).** The paper numbers only Theorems 1-3, Definitions 1-5, Facts 1-2, and Remarks 1-2. There are no numbered Propositions, Corollaries, or Lemmas.
- Theorem 1 (from [1], full sampling). C(beta,1) = max over X of min{ I(X;Y)/E[k(X)], (I(X;Y) + D(Y||Y_star)) / (E[k(X)](1+beta)) }. Restated by the summarizer, not verbatim.
- Theorem 2 (non-adaptive). Verbatim fragment (model-extracted): "Under non-adaptive sampling it is possible to achieve the full-sampling capacity per unit cost." Restated: C_na(beta,rho) = C(beta,1) for any beta > 0, rho > 0. Delay bounds: lim_{gamma->1} liminf_B d/n*_B >= 1/rho if star is in X, and >= (1+rho)/rho if star is not in X. Tight up to any eps > 0.
- Theorem 3 (adaptive). Verbatim fragment (model-extracted): "Under adaptive sampling it is possible to achieve the full-sampling capacity per unit cost." Codes exist with d(C_B, eps_B) = n*_B(1 + o(1)) for any beta > 0, rho > 0. The summarizer flagged a typo: the statement writes C_na where C_a is meant.
- Remark 1: results hold under universal decoding (MMI decoder, pure noise estimated from the first sqrt(A) outputs). Remark 2: multiple-access extension with upsilon <= beta/2.

**Adaptive vs. non-adaptive separation and scaling.**
- Non-adaptive: full-sampling capacity per unit cost, delay multiplied by 1/rho (star in X) or (1+rho)/rho (star not in X).
- Adaptive: full-sampling capacity with delay n*_B(1+o(1)) for any rho > 0. The paper says adaptive sampling achieves minimal delay "regardless of the sampling rate rho, as long as it is non-zero."
- Synchronous case (beta = 0): C(0,rho) = rho * C(0,1) for both sampling types. The summarizer attributes the difference to asynchronism being exponential in B.

**Label delay and budget.** No label delay is defined. The explicit budgets are the sampling fraction rho (with tolerance eps_B -> 0) and the sub-exponential delay requirement.

**Garbled or unresolved math.** The summarizer reported garbled inline formulas in the proofs: sampling-set definitions, threshold statements (e.g., "P_star(T_P) > 1/n^2"), and the star not in X delay bound. Meaning is clear from context but notation is unverified.

## Follow-up and related work (search-level only; not read in full)

Source: WebSearch, 2026-10-28. Nothing below was opened except where noted.

- Ebrahimzadeh and Tchamkerten, "Sequential detection of transient changes in stochastic systems under a sampling constraint," ISIT 2015. Listed on a research portal (https://researchportal.ip-paris.fr/en/publications/sequential-detection-of-transient-changes-in-stochastic-systems-u/). No arXiv id seen. Not opened.
- US patent application/grant on "Method for transient change detection with adaptive sampling" (US 20170353293 application, grant 10116434 per search results). Patent, not arXiv. Not opened.
- Banerjee and Veeravalli, data-efficient quickest change detection with on-off observation control: arXiv 1105.1361 (Bayesian), arXiv 1211.3729 (minimax, DE-CuSum), arXiv 1408.4747 (decentralized), arXiv 2412.20207 (robust, Dec 2024), and arXiv 1309.5396 (limited or random sampling rights). These assume a persistent post-change regime, not transient. Not opened; description from search snippets only.
- arXiv 1210.5552, "Quickest Change Detection" (survey-type). Seen in search results only. Not opened.
- arXiv 2511.02452. Appeared in search results with no description. Not opened.
- No arXiv follow-up by Chandar or Tchamkerten specifically on budget-constrained transient detection was found in search. Author listings were not checked.

## Limitations

- Every quote is model-extracted from WebFetch summaries. Exact wording must be re-checked against the PDF or LaTeX source before citation.
- The final 5,152 characters of the 1501.05930 HTML were NOT ACCESSED.
- Section and equation numbers come from the summarizer and were not checked against the paper.
- Follow-up papers were identified by search only and were not read.
- The 1501.05930 title discrepancy (arXiv v1 vs. later title) was not verified against v1.
