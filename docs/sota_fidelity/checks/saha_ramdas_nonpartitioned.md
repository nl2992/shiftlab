# Check: Saha & Ramdas, Non-partitioned e-detectors (arXiv 2607.28322v1)

Independent check of `specs/saha_ramdas_nonpartitioned.md`, 2026-11-06. Nothing downloaded was
executed. Numerical checks used own scratch code (`.../scratchpad/check_edet/grid_check.py`,
`brent_check.py`) on the author's data CSV and my own re-implementation of the printed formulas.

## Sources actually read

- arXiv PDF `https://arxiv.org/pdf/2607.28322v1`, 94 pp, sha256 daaf5169...bb75e0 (matches spec).
  The arXiv abs page shows only `[v1]`, "Submitted on 30 Jul 2026" (re-fetched). No venue.
- Read page by page: pp 1, 6-8, 10-13 (Sec 2-5 detectors), 23-24 (Sec 8), 31 (Cor A.2), 36-37 (B.1
  proofs); keyword searches (grid, label, feedback, budget, measurab, github) over all 94 pages.
  Not read: pp 2-5, 9, 14-22 (Sec 6-7 statements), 25-30, 32-35, App B.2-E.
- Code `Aytijhya/Nonseparated-e-detector` at `1966da8dd36224c000f94f564c7219d3d90e4779` (commit date
  2026-08-12; README is a title line). Read in full: `cleveland-bounded.R` (222 lines),
  `run_exact_up_oracle.py`, `run_bounded_double_asymptotic.py`. Data
  `cleveland_cavaliers_2011_2018_regular_season.csv` (640 games) and
  `nonpartition_cavaliers_detector_A1000.csv` used as data only.

## Claim table

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Problem: iid, composite class P, H0 iid R in P, no partition | CONFIRMED | p1 |
| 2 | Def 2.1 s-delay e-process | CONFIRMED | p6 |
| 3 | Eq (1) ARL detector `inf_R sum_{s<=t} M^R_{s:t}`, threshold A; Thm 2.2: E[tau] >= A, `P(tau <= m) <= m/A` | CONFIRMED | p7, eq (2); proof p36: apply e-detector inequality to `tau ^ m` |
| 4 | Eq (3) PFA detector with `sum pi_s <= 1`, threshold 1/alpha; canonical `pi_s = c_pi/(s log^2(es))`; Thm 2.3 sup PFA <= alpha | CONFIRMED | p7, eq (4); proof p37 via `1 - sum pi + sum pi Z` and Ville |
| 5 | Measurability of the infimum is assumed, not shown | CONFIRMED | p7 ("we always implicitly assume ... measurable") |
| 6 | Thm 2.2/2.3 hold for dependent data via a conditional s-delay e-process | CONFIRMED | App A Cor A.2 p31, proof "identical to Thm 2.2/2.3"; only the 2-state Markov class is covered |
| 7 | Eq (6) sub-Gaussian e-process `(1+rho^2 sigma^2 n)^{-1/2} exp{rho^2 n^2 (xbar - theta)^2 / (2(1+rho^2 sigma^2 n))}`; detector (7) inf over theta in R | CONFIRMED | p8 |
| 8 | Bounded mean: eq (17) bets in `[-1/(1-theta), 1/theta]`; eq (18) Cover/Jeffreys portfolio with `lambda_theta(p) = (p-theta)/(theta(1-theta))`; eq (21) `D^{UP,w}`; ARL `w_s = 1`, PFA `w_s = pi_s` | CONFIRMED | p10-11. The null is the point null E[X given past] = theta (equality), so the object is not a one-sided test |
| 9 | Gauss-Chebyshev with K >= (H+1)/2 nodes is exact for horizon H | CONFIRMED | p11. Author R uses `ceil((H+1)/2)` nodes = 321 for H = 640 (cleveland-bounded.R l.110-114); Python uses `(H+2)//2` (run_exact_up_oracle.py l.55) |
| 10 | Table 1 CADD (17.297 vs 28.489; 11.297 vs 16.335; 8.129 vs 10.905; 5.177 vs 6.309), Table 2 Panel A/B, I_bet 0.087177 / 0.485201 / 0.505800 | CONFIRMED (text only) | p23-24; not re-simulated. Note: Panel A in `run_exact_up_oracle.py` uses the point null at the TRUE mean a = 0.3 (l.44-66), an oracle, not the infimum detector; Panel B uses a two-start composite with 30 bisection steps on the gradient in theta (`run_bounded_double_asymptotic.py` l.21-33) |
| 11 | Delay results asymptotic (alpha -> 0, late change) | CONFIRMED | Thm 3.2, 4.2 conditions `log T = o(log A)` etc., p8, p11 |
| 12 | Not covered: one-sided challenger-better, promotion, non-stationary pre-change, label budgets, IPW, delayed or missing feedback, restart | CONFIRMED | grep of pp 1-30 for label / feedback / budget / sampling: no hits; "delay" hits are detection delay only. A constantly better challenger never fires because H0 is any constant iid law |
| 13 | Venue: preprint, version may change | CONFIRMED | abs page lists v1 only |

## Item (5): is the numerical infimum anti-conservative?

- Direction: **CONFIRMED**. Any numerical minimum of the objective over a finite set or with finite
  tolerance is >= the true infimum, so `D_t` computed this way is >= the true `D_t`, and crossings
  can only occur earlier than the exact detector. The paper never says how to certify the infimum
  numerically (grep: no certified lower bound). For the studentized detector it notes the problem
  is one-dimensional and convex with minimiser inside the hull of segment means, and "bisection or
  safeguarded Newton costs O(t log(1/eps_num))" (p13), i.e. a tolerance, not a bound.
- Magnitude in the author's own bounded-mean run: I re-implemented `cleveland-bounded.R`
  (SR recursion `factor*(1+state)`, theta grid of 4001 points on [1e-5, 1-1e-5], 321 Chebyshev
  nodes, A = 1000). My log statistic matches the author's CSV (`log_detector_statistic`) to
  6.4e-14 over all 640 games: this is an independent numerical reproduction of the author's
  output. First crossing: game 366, 2015-02-11, equal to the CSV's `crossed` flag. Refining the
  grid to 80001 points lowers log D by at most **0.0033** nats (a factor 1.003 on D) and leaves the
  crossing at game 366. So the grid bias is real but tiny here; it is uncertified and not an
  upper bound on the error at other thresholds or streams.
- The grid also truncates theta to [1e-5, 1-1e-5], a second upward bias, not checked further.
- ShiftLab pilot (sub-Gaussian, eq (6)): the objective is convex in theta (sum of exponentials of
  convex quadratics), so Brent on the hull is well posed. On one length-120 path (the script's
  seed 202670000, 60 null + 60 shifted points) the Brent minimum was never above the minimum of a
  400001-point grid at any t (`brent_check.py`, maximum excess 0). The bias is therefore far below
  the 1001-point grid the script itself asserts against (check_nonpartitioned_pfa.py l.86-90).
  Still not certified.
- Verdict on the spec phrase "crossings can be anti-conservative": CONFIRMED as an inequality;
  CORRECTED as to size: negligible in the cases I ran, so it does not by itself justify
  discarding the pilot; it does forbid describing a numerical crossing as a PFA-valid alarm.

## Repo check: `scripts/exhaustive_evaluation/check_nonpartitioned_pfa.py`

- `log_point_sum` l.16-19 is eq (6) with sigma^2 = rho^2 = 1 and `pi_s = 1/H`: it returns
  `logsumexp(terms) - log(H)`, i.e. the SUM over the t active starts divided by H (l.19, and the
  `direct` check l.77-84 uses `log(mean) + log(t/H)`). The spec's "log mean over s" is loose:
  CORRECTED wording (sum over t starts, divided by horizon H = 120).
- Infimum: `minimize_scalar` bounded on `[min, max]` of segment means, `xatol 1e-12` (l.60-72):
  CONFIRMED. Registration text l.40 already says "upper approximation to infimum, no certified PFA
  guarantee". Threshold `log(20)` = alpha 0.05 (l.106). Four paths, one seed (l.38-39, 45-50):
  CONFIRMED; no PFA estimate. Constant-0 closed form check l.101-103: CONFIRMED correct.
- Does not implement the bounded-mean portfolio detector (eq (18), (21)); no Markov detector:
  CONFIRMED. Registered source is the arXiv HTML v1, same version (l.29).

## Mapping and tier

Spec section 6 stands: sentinel on a stream law, not a promotion or rollback certificate (H0 is
"some constant iid law", so harm without a law change is invisible, and a law change need not be
harm). Bounded mapping `(d+1)/2` is correct only if the sampling design leaves the label-clock
sequence iid; IPW breaks boundedness; delayed feedback not covered (confirmed absent). T1 is now
demonstrably achievable for the full-information bounded ARL detector: my port reproduces the
author CSV to 1e-13 (reproduction test for the ledger). Contract version T3.

## Corrections to the spec

1. "log mean over s" in section 7: sum over t starts divided by H.
2. Section 5: grid minimum is an upper bound on the infimum (right), but its measured size in the
   author's run is <= 0.0033 nats; add this and the 6e-14 reproduction.
3. Section 8: Table 2 Panel A is an oracle at the true null mean, not the infimum detector.
4. Add: first crossing of the author's A = 1000 ARL detector is game 366, 2015-02-11.

**Verdict: ACCEPT WITH CORRECTIONS**
