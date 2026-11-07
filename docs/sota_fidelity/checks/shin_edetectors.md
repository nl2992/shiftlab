# Check: Shin, Ramdas, Rinaldo, E-detectors (NEJSDS 2024)

Independent check of `specs/shin_edetectors.md`, 2026-11-06. Nothing downloaded was executed. Own
scratch code (Algorithm 3, e-SR/e-CUSUM recursions) was written from the printed equations.
Scratch: `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/check_edet/`
(`alg3.py`, `nba_repro.py`, `nej/`, `arx/`, `code_*`).

## Sources actually read

- NEJSDS PDF `https://nejsds.nestat.org/journal/NEJSDS/article/59/file/pdf`: 32 pp, sha256
  6e2ac474...4c6f. Matches the spec. Page numbers below are NEJSDS printed pages (229-260).
- arXiv 2203.03532 v4, 50 pp, sha256 564dc11f...aa1c. Matches the spec.
- Code, fetched with `gh api` at the full SHAs (all four resolve): `shinjaehyeok/e_detector_paper`
  2fbf585457e31495978cdf7c075f43d0b15961d2; `shinjaehyeok/stcp`
  c9ff9a69bc18a82c909f6c4c8e17cc0def0069ae; `shinjaehyeok/stcpR6`
  9eaafb491f315094861d1eea712677c4468dfb51.
- Version comparison method: two-column layout defeats a sequence diff. I compared token multisets
  of the whole PDFs plus side-by-side reading of Alg 1, Alg 3, Sec 3.1, Remark 2.7, Sec 5.2 and
  the constants. Differences found: front/back matter, hyphenation, equation numbering, appendix
  numbering ((A.n)/(B.n) in NEJSDS; Alg 3 eqs (94)-(96) are (B.10)-(B.12), p255-256), and a longer
  arXiv reference list. No change to algorithms, theorem statements or constants in the passages
  read. A full sentence-level diff was NOT done: **UNVERIFIABLE** that no wording changed elsewhere.

## Claim table

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1a | The paper has no two-sided construction | CONFIRMED | grep both PDFs for two-sided / both directions / either direction: none. Only "one-sided" hits: NEJSDS p240 ("only consider the one-sided and well-separated case") and the appendix "(one-sided) level-alpha sequential test". Multi-stream combination is only min/sum of local CUSUMs (p251) |
| 1b | stcpR6 `two.sided` = 50/50 mixture, each side at alpha/2 | CONFIRMED, one addition | `R/helper_functions.R` `convertDeltaToExpParams`, branch `alternative == "two.sided"`: two `compute_baseline(alpha / 2, ...)` calls, `weights <- c(omega/2, omega_less/2)`, lambdas `c(base$lambda, -m_pre*lambda_less/(1-m_pre))` for Bounded. Stopping threshold is the user `threshold` (`alpha <- exp(-threshold)`, `R/stcp.R` ~l.130), so the grid is built at alpha/2 but the alarm level is 1/alpha on the 50/50 mixture. Validity needs the point null E[X given past] = m: algebra gives `1 - (m/(1-m))*lambda*(E[X]/m - 1)`, which exceeds 1 when the mean is below m. Spec's "point null" statement CONFIRMED |
| 1c | stcp (older) has only `is_flipped` and `combine_stcp` | CONFIRMED | `R/run_stcp.R` `combine_stcp_run`: mixture `w*e1 + (1-w)*e2`, threshold from `combine_stcp`. Not re-derived beyond the call |
| 2 | Typo "M_0^mSR = M_0^mCU := 1" contradicts recursions and Algorithm 1 | CONFIRMED, location refined | It sits in the sentence introducing the mixtures, NOT inside the displayed equations: NEJSDS p238, just before (3.5)/(3.6) (arXiv v4 sentence before eq (24)/(25), text line 774). Contradicts "with M_0^SR(k) = M_0^CU(k) = 0" after (3.8)/(3.9) (arXiv (27)/(28)) and Algorithm 1 line 4 "M_0^mSR <- 0" (p242). Same in both versions. M_0 = 1 would also violate Def 2.2 at tau = 0 |
| 3a | Official code uses the eq (70) increment | CONFIRMED | stcp `R/e_detectors.R` l.66-89 `generate_log_bounded_base_fn`: `log(1 + lambda*((x - bound_lower)/m_gap - 1))`. stcpR6 `src/baseline_increment.h` l.168 `log(1.0 + m_lambda * (x / m_mu - 1.0))` |
| 3b | ... with grid weights from the eq (72) sub-E psi | CONFIRMED | stcp `R/build_stcp_model.R` `build_stcp_bounded` l.261-269: `compute_baseline(..., psi_fn_list = generate_sub_E_fn(), v_min = 0, ...)`, then `generate_log_bounded_base_fn` at l.282 |
| 3c | Which increment produced the paper's Fig 3 dates (spec: UNVERIFIED) | **CORRECTED: eq (70)** (independent reproduction) | My own Algorithm 3 (sub-E, v_min 0, Delta_L 0.024, Delta_U 1600, K_alpha 189, 190 components) on the 640-game Cavaliers file (Saha-Ramdas repo CSV, same games). e-SR with eq (70): first alarm game 378, 2015-03-10 = the paper's reported date (Fig 3 caption: "378-th game (SR)"). With eq (72): game 427, 2016-01-06, does not match. e-CUSUM with (70): value 963.9 at game 444 (paper: 444 / 2016-02-06), crosses at game 445 (2016-02-08), one game late; with (72) never crosses. Same result for Delta_L, Delta_U from eq (75) exactly and for v_min 0 or 1. Cause of the one-game CUSUM gap not identified (data revision or g_alpha tolerance): UNVERIFIED. The paper prose (p247) says the sub-E bound is used to set the range and that mixtures for the original increments are "always more sample-efficient": consistent with the code |
| 3d | Paper prose says Algorithm 1 is run on (72) | CORRECTED | p247: the text sets the (Delta_L, Delta_U) range via (72) and states the mixtures for the original increments {L^lambda} can be built too. It never says the figure used (72); the code and the reproduction say (70) |
| 4a | Remark 2.7: initial weights summing to <= 1 give PFA <= alpha | CONFIRMED as printed | NEJSDS p234. Stated without proof in either version (grep "Remark 2.7", "initial weight", "Ville": the only Ville uses are in Sec 1/6, not tied to this remark). Delay growing like log nu is also asserted without proof |
| 4b | Is an H/alpha threshold with weights 1/H proved anywhere in the paper? | CONFIRMED: not proved | The paper has no finite-horizon or H/alpha statement; it follows only as the special case pi_s = 1/H of Remark 2.7 (sum of weights = 1, threshold 1/alpha on the weighted sum, equivalently M/H >= 1/alpha). My own derivation: V_n = S_n + sum_{j>n} w_j with S_n = (S_{n-1}+w_n)L_n is a nonnegative supermartingale started at <= 1 when E[L_n given past] <= 1, so Ville gives P(sup S_n >= 1/alpha) <= alpha; max-over-starts (CUSUM) is dominated by the sum. Proof is short but is not in the paper. Mixing over lambda keeps it valid (Prop 2.3, p233) |
| 5 | Algorithm 3 outputs: 69 (Bernoulli) and 190 (bounded) baselines | CONFIRMED with a counting caveat | My Algorithm 3 (eqs (94)-(96)): Bernoulli, p0 0.49, Delta_L 0.02, Delta_U 0.41, alpha 1e-3, v_min 1: g_alpha 12.19, K_alpha 69, plus the lambda_U atom = 70 components. Bounded: g_alpha 13.19, K_alpha 189, plus atom = 190. So the paper's "69" counts K_alpha only and "190" counts K_alpha+1 (or uses a different v_min). The paper prints no weights table |
| 5b | Code vs paper input for Bernoulli example | CORRECTED (new) | Paper text p245: Delta_U = 0.41. `e_detector_paper/nba_example/NBA_example.R` l.90-95 and `NBA_example_with_stcpR6.R` l.97 pass `delta_upper = 1 - (p_pre + delta_lower)` = 0.49, which gives K_alpha 75 (76 components) in my Algorithm 3, not 69 |
| 6 | Eq (70)-(75) forms and constants | CONFIRMED | NEJSDS p246-247: (5.6) = (70), (5.8) = (72), (5.11) = (75); m = 0.494, delta = 0.0125, Delta_L 0.024, Delta_U 1600, alpha 1e-3, Kmax 1000, 190 baselines (p247). Delta_U exact = 1599.77 |
| 7 | Algorithm 1 / 3 pseudo-code and eq (94)-(96) weights | CONFIRMED | p242 and p256. Weights: atom e^{-g} (only if g > v_min D_U) plus K_alpha equal weights e^{-g/eta}, normalised by W |
| 8 | Reported simulation numbers 91.3 and 123.7; Kmax 1000; 5000 reps | CONFIRMED (text only) | NEJSDS p248. Not re-simulated |
| 9 | Mixtures are mixtures of per-lambda detectors, not max over lambda | CONFIRMED | (3.5)-(3.9); Remark 3.1 (p238): swapping integral for sup over lambda "does not in general yield a valid e-detector" |
| 10 | stcpR6 defaults: k_max 1000; two-sided delta_upper default | CONFIRMED, plus new finding | `checkDeltaRange` l.104-118: NULL delta_upper gives `min(1-m, m) - 0.001` for Ber/Bounded two-sided (Normal: 5). NEW: `convertDeltaToExpParams` passes `v_min = 1` for every family including Bounded, and uses variance bound 0.25 in the Bounded delta conversion, whereas stcp (and the paper, v_min = inf of (x/m-1)^2 = 0) uses v_min 0. With v_min 1 my Algorithm 3 drops the lambda_U atom (189 components). Still a valid e-detector (weights sum to 1); only delay efficiency differs. stcpR6 Bounded grids are therefore not paper-identical |
| 11 | stcp update: SR `logSumExp(prev, 0) + log L`; CUSUM `max(prev, 0) + log L`; M_0 = 0 as -Inf | CONFIRMED | `R/e_detectors.R` `update_log_e` l.14-31. stcp alarm uses strict `>` (`run_stcp.R` l.42, combine l.86); paper uses >= |

## Not re-verified

Proofs in App A/B (Prop 2.14, Thm 3.4, Prop 3.3, Lemma B.1, Thm 4.3, Cor 4.6) were not read beyond
statements; Algorithm 2 defaults (r, m, K_0) are absent from the main text (checked arXiv p22-23
and grep): UNVERIFIED. Page numbers for arXiv v4 in the spec were not re-checked individually.

## Repo characterisation (decides novelty of ShiftLab's Track-A methods against e-detectors)

All line numbers are in this worktree.

### RMM statistic: `scripts/failure_atlas_v2/restart_monitor.py`

- `MixtureSRDetector` l.72-102. State is one SR value per bet `lams = (0.15, 0.3, 0.5)` (l.76, 89-90).
  Start `s` is injected as `sr += pis[s]` before label `n` when `n % gap == 0` and
  `n // gap < n_starts` (l.94-95, gap = 10); then `sr *= 1 + lams*x` (l.96); stat = plain mean over
  lambdas (l.102); alarm at stat >= 1/alpha (l.98). Prior masses: uniform `1/n_starts`, or
  `w_first` on the first start (l.82-88); both sum to 1. `n_starts = ceil(max_labels/gap)` (l.80).
- Therefore: **CONFIRMED** "RMM = e-SR mixed over a 3-point bet grid, start weights summing to 1,
  starts every 10 labels, label clock, not e-CUSUM". It is Shin Def 2.6 (SR sum over starts), mixed
  over lambda as in (3.7) (Prop 2.3), with the Remark 2.7 start weights. Wealth factor `1 + lam*x`,
  x in {-1, +1}, is eq (70) with m = 1/2 after the map (x+1)/2.
- Clock: `x` is built from queued disagreement outcomes in request order (`observe`, l.196-215;
  `order` holds only disagreement events, l.188-193); `x = d if deployed == 0 else -d` (l.212):
  x = +1 means the non-deployed model was right. Label clock, no IPW. CONFIRMED.
- Latent defect (not in spec): `order` gets every queried disagreement but `queue` only
  `d != 0` outcomes (l.205-206). If a disagreement can have `d == 0` (multiclass, both wrong)
  the head of `order` is never matched and the detector stalls (`while` at l.210). Harmless for
  binary labels. UNVERIFIED whether any ShiftLab benchmark has this case.

### E_srr / SRRDetector: `scripts/sota_sprint/fam_e.py`

- `SRRDetector` is at **l.62-85** (spec said ~l.77-96: CORRECTED). kind "sr": `sr = (sr + 1) * f`,
  stat = mean over lambda (l.75-77): eq (13) with (26). kind "cusum" (default): one row per label
  start, `stat = max over starts of mean over lambda` (l.78-85): CONFIRMED "max over starts of
  bet mixture". This is a valid e-CUSUM (a mixture e_j-process inside Def 2.6) but is NOT the
  paper's mixture of CUSUMs (3.6); since max of mean <= mean of max, it is never larger than (3.6),
  so it is a weaker competitor than the real mixture-of-CUSUMs.
- Grid is `fam_b.HOST_LAMBDAS = (0.15, 0.3, 0.5)` (fam_b.py l.72), not Algorithm 3. Threshold 1/alpha_k,
  unit mass per start, ARL semantics only: the module says so itself (fam_e.py l.24-27). The
  docstring says `edetect` is R-only so it is a Python re-implementation. Tier: T3.
- `DetectorSwapMonitor` (l.117-128) replaces only `_new_detector`, keeping RMM's alpha split,
  acquisition and restart. Registered as `E_srr:<host>` (cusum) for 4 hosts and `E_srrSR` (sr) for
  one host only (l.226-229).

### E_rb: `scripts/sota_sprint/fam_e.py` l.137-142, 226 with `scripts/sota_sprint/fam_b.py`

- `E_rb:<host>` = `fam_b.RecoveryMonitor(rollback=True)` (fam_e.py l.137-142, 226). CONFIRMED
  "alternating one-sided e-SR detectors with sign flipped after promotion", but note the flip is
  inherited from RMM (`restart_monitor.py:212`), not added by E_rb: base RMM already rolls back at
  `alpha_rb = alpha` over a start grid sized to the total budget B.
- What E_rb changes (fam_b.py): rollback detector alpha 0.10 (`alpha_rb_new`, l.145; `_new_detector`
  l.162-169); start grid sized `max(_remaining_hint, 20)` (l.168), the budget left; horizon gate
  `h_min = ceil(c_s/g_ref)`, `G_REF = 0.1` (l.74, 149) that vetoes a rollback with fewer than
  h_min events left (l.229-233); re-promotion base alpha halves per rollback (l.243-244);
  base-initiated switches also counted in `n_promotions`/`n_rollbacks` (l.190-194).
  Detector `GridMixtureDetector` (l.77-114) with the host component (1, gap 10, ceil(m/10)) is
  identical in statistic to `MixtureSRDetector` (docstring l.84-85).
- Error accounting: promotion alpha is claimed under the iid conditional null; a false rollback is
  "a cost, not a safety error" (fam_b.py l.27-29; fam_e.py l.8-9). No joint promote/rollback cycle
  guarantee exists in the repo (docs/sprint2/novelty/NOVELTY.md l.130-132 concedes this).

### What RMM / E_rb do that a two-sided e-SR on the label clock with restart-at-switch would not

The per-phase detection statistic adds nothing: alternating one-sided e-SR with a sign flip and a
reset at each switch is exactly RMM's detector loop. The differences are all in the wrapper:

1. Host and alpha split: base certificate at alpha/2, detector at alpha/2; promotion detector at
   alpha_det/2^j, so the j-th promotion costs a halved share (restart_monitor.py l.140-142, 161;
   fam_b.py l.243-244). A bare e-SR has no host and no spending ledger.
2. Host restart: on every alarm the base policy is rebuilt on the remaining horizon and budget with
   model indices swapped (l.219-234, `_View` l.105-124).
3. Budget continuation after a verdict: the wrapper keeps buying disagreement labels with its own
   pacer after the base stops (l.190-193, `HorizonWeightedPacer` l.53-69), sharing the hard budget.
   The repo's own ablation attributes most of the gain to this (NOVELTY.md l.121-123).
4. Finite prior mass over a coarse start grid sized to the label budget (PFA form, Remark 2.7)
   instead of unit mass on every label (ARL form). This is the one detector-level difference from
   the paper's default Def 2.6 / Thm 2.4 use, and it is a paper remark, not a ShiftLab invention.
5. Delayed-feedback ordering: outcomes enter the detector in request order after release
   (`order`/`queue`), a ShiftLab contract adaptation.
6. E_rb only: remaining-budget grid, alpha_rb 0.10, horizon gate against switch cost, base-alpha
   halving on re-promotion.

Conclusion for novelty: ShiftLab Track-A's detector is an instance of the e-SR with Remark 2.7
weights; novelty can only rest on items 1-3 and 6 (system-level), none with a proved joint error
statement. The repo already says "RMM is a composition" (NOVELTY.md l.118). The E_srr comparison in
RESULTS.md compares RMM's PFA-weighted SR to an ARL-calibrated CUSUM with a 3-point grid, so it
measures the value of Remark 2.7 weights (validity), not novelty of RMM. The matched competitor
(SR with Remark 2.7 weights, start at every label, `pi_s` summing to 1) is not run.

### Other ShiftLab files named in the task

- `src/shiftlab/dive/horizon_edetectors.py`: recursion l.134-137 CONFIRMED (SR `logaddexp(0, .)`,
  CUSUM `max(0, .)`, init -inf). Per-stake components mixed with log weights in `log_statistic`
  (l.107); the spec's "l.139" is the call site (CORRECTED: l.107). Factor `1 + stake*x/B` l.130-132
  CONFIRMED; stakes l.42, uniform weights l.62; stake 1 allowed by the l.58 check. Threshold
  `log(horizon) - log(alpha)` l.85-87 with `>=` l.140 CONFIRMED: this is Remark 2.7 with pi_s = 1/H,
  not an ARL threshold. `skip=True` gives factor 1 and still opens a start (l.125-135) CONFIRMED.
- `src/shiftlab/sota_search/paired_edetectors.py`: stakes (.2,.5,.8) l.36; `x` l.40; factor l.56;
  SR `(1+sr)*f`, CUSUM `max(1,cus)*f` l.58-59; mixtures = mean over stakes l.60; thresholds
  `T/alpha` and `1/alpha` l.64; switch-cost gate l.65: all CONFIRMED. Correction to spec section 6
  wording: unqueried events while budget remains give `x = -margin`, factor < 1 when margin > 0
  (l.40), not factor 1. Delay: factor 1 for `t < delay` l.53-57, calendar shift only.
- `src/shiftlab/sota_search/restart.py:32-42` `S_t = (S_{t-1}+w_t) f_t`, `M_t = S_t + tail`:
  CONFIRMED, this is the Ville form of Remark 2.7.

## Fidelity tier call

Spec's calls stand: T1 only for a full-information port validated against stcp/stcpR6; the
contract version (budget, delay, IPW) is T3; RMM detector is T3 (SR recursion line T2); E_srr T3,
and its cusum variant deviates from (3.6). Added: the spec should cite eq (70) increments as the
code and figure reality, and note that stcpR6's Bounded grid differs from stcp's (v_min).

**Verdict: ACCEPT WITH CORRECTIONS** (eq (24)/(25) typo location; (70) vs (72) now resolved by
reproduction; Bernoulli Delta_U 0.41 vs code 0.49; counting of 69/190; line numbers for
SRRDetector and horizon_edetectors; unqueried-event factor in paired_edetectors).
