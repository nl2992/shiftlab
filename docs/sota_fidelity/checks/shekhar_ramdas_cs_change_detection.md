# Check: Shekhar & Ramdas RCS-Detector spec

Independent check (step 2), written 2026-11-06. Spec checked: `specs/shekhar_ramdas_cs_change_detection.md`.

Sources re-read independently (not executed):
- PMLR camera-ready `shekhar24a.pdf`, 15 pages (pdfinfo), from `mlresearch/v235` raw URL.
- arXiv 2309.09111v2, 11 pages, stamped "25 Nov 2023".
- Official code `sshekhar17/SCDtoCS` at `c3a7eceaf9fa8e2756105c233a791592916c57d1` (commit date 2023-12-07T03:52:28Z,
  message "first commit", files .gitignore, README.md, example.ipynb, main.py, utils.py; confirmed via `gh api commits/<sha>`).
  `gh api commits` lists that SHA as the only commit. Files fetched via raw.githubusercontent at the pinned SHA.
- Scratch dir: `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/check_shekhar/`.
- I did NOT read Shin-Ramdas-Rinaldo or Waudby-Smith-Ramdas 2023; items depending on them stay UNVERIFIABLE here.

Labels: CONFIRMED / CORRECTED / UNVERIFIABLE. Spec section numbers in brackets.

## 1. Citation, version, code [spec s1]

1. Citation, PMLR 235:44628-44642, camera-ready 15 pages, arXiv v2 11 pages: CONFIRMED (page counts, v2 date; I did not check the
   PMLR page range or the "lists no supplement" claim).
2. PMLR is the only version with experiments, Prop 2.9, Remark 2.3: CONFIRMED (arXiv text has no experiments section and no
   Prop 2.9). arXiv numbering Thm 2.2 / Thm 2.5 / Prop 2.7 / Def 1.3 / Def 2.1 "repeated-FCS-Detector": CONFIRMED.
   Add: arXiv Remark 2.3 = PMLR Remark 2.5 (PFA variant).
3. Official code only commit c3a7ece, file list, date, README links arXiv: CONFIRMED (file list and date; README link not re-opened).
4. "Code does not reproduce paper experiments (no BCS, CuSum, dependent data, alpha sweep)": CONFIRMED against example.ipynb:
   three experiments only (no change mu0=0.6/Nmax=1000/alpha=0.005/100 trials; change 500, Delta .4, mu0 .5, Nmax 2000;
   Delta in {.15,...,.4}, Nmax 2500, 20 trials). Extra: notebook cell 3 calls `plt.xlable`/`plt.ylable` (typos), so it would not run
   to completion; Exp2/3 reuse the global `change_point`. Harmless for the port, but the notebook is not a clean reproduction artefact.

## 2. Problem and estimand [s2]

5. Filtration, Problems 1.1/1.2, ARL >= 1/alpha criterion, partitioned/non-partitioned, P1 may depend on X_1..X_T: CONFIRMED.
6. "No delay / no missing data / no sampling control" and "nothing about harm": CONFIRMED (paper is silent; this is a reading, fine).

## 3. Algorithm [s3]

7. Definition 2.1 steps 1-3, C^(0)=Theta or Theta0, stop when intersection of all initialised CSs is empty, non-nested variant
   `cap_m cap_{i=m..n} C_i^(m)`: CONFIRMED verbatim in structure. Remark 1.5 (running intersection WLOG): CONFIRMED.
8. Joint-emptiness, not "any one CS excludes theta0": CONFIRMED and correct caveat. Note: for the partitioned form C^(0)=Theta0
   so the rule is "cap_m C^(m) cap Theta0 = empty"; Prop 3.1's proof (Sec 4.4) uses C^(0)={theta0}. Lorden equivalence is therefore
   proved for the singleton partitioned case only; Remark 3.2's composite-null Lorden rule uses `Theta0 cap C_n = empty` per CS,
   which is NOT the same as joint emptiness. The spec flags this; CONFIRMED.
9. Remark 2.3 (cost grows, window w "interesting direction", no w chosen): CONFIRMED. Conclusion "per-step computation grows linearly":
   not re-checked, UNVERIFIABLE (minor).
10. Remark 2.5 level `1 - 6alpha/(n^2 pi^2)` gives P_inf(tau<inf) <= alpha, ARL infinite: CONFIRMED (printed sum bound).
    "Logarithmic in T delay" is asserted with "we can show" and no proof: CONFIRMED UNVERIFIABLE as spec says.

## 4. Hyperparameters [s4]

11. Hoeffding CS formula: midpoint `sum lam X / sum lam`, half-width `(log(2/alpha)+sum lam^2/8)/sum lam`: CONFIRMED (P6, P14).
12. **CORRECTED: lambda schedule.** The spec writes `sqrt(...) ^ 1`. The printed symbol is the minimum operator, `... ∧ 1`, i.e.
    `lambda_i = min{ sqrt(8 log(2/alpha)/(i log(i+1))), 1 }` in the main text (P6) and
    `min{ sqrt(8 log(2/alpha)/(i(i+1))), 1 }` in Appendix C (P14). The cap at 1 is part of both printed schedules and is missing
    from the code (see item 25). The spec's i log(i+1) (P6) vs i(i+1) (P14) mismatch itself is CONFIRMED.
13. Hoeffding chosen because closed form; betting CS only in proof of Prop 2.10; EB CS not in the paper: CONFIRMED.
14. ARL experiment (Delta=0, alpha=10^-i i=1..5, 50 trials, cap 50000), Appendix C heuristics (width shrunk by unstated factor <1;
    stopping checked every 10 or 20 steps): CONFIRMED. Shrink factor unstated: CONFIRMED. P5 text "slightly higher variability": CONFIRMED.
15. Delay experiment (alpha=.001, six Deltas .05-.175, 50 trials, clip 24000): CONFIRMED. Fig 3 left CuSum with known P0, P1, right
    dependent example (X_{n-1} < 0.5 switches distribution): CONFIRMED. Draft note "Fix Figure 3 + caption..." present in the PDF: CONFIRMED.
16. mu0 and T not stated in the experiment text: CONFIRMED (grep finds no mu0 value or T value).
17. Beta(2, 2(1-mu)/mu) data: CONFIRMED. utils.py:35-62 `createBoundedSource` uses `b = 2(xmax-xmin)/(mu-xmin) - 2`, equal for [0,1]: CONFIRMED.
18. Code defaults: `Nmax=1000, alpha=0.005, max_num_CSs=1000` main.py:17-18; subclass `max_num_CSs=500` at main.py:112-114 and
    184-186; deque with maxlen at main.py:64: CONFIRMED.

## 5. Guarantees [s5]

19. Theorem 2.4 (ARL >= 1/alpha, T=inf), proof route via e-process `E^(m)_n = 1/alpha*1{theta0 not in C^(m)_n}`, `M_n = sum_m E^(m)_n`,
    `{tau<=n} ⊂ {M_n >= 1/alpha}` (eq. (4)), Shin et al. Prop 2.4: CONFIRMED (PMLR Sec 4.1, eq. (4) is on P7). The e-process step
    needs each C^(m) to be a level-(1-alpha) CS for the same theta0 started at m; CONFIRMED. BCS ARL `1/(2alpha) - 3/2`: CONFIRMED (Remark 2.8).
20. Derived union bound `P(tau <= N) <= N*alpha` for level-(1-alpha) CSs: CONFIRMED valid. Same inclusion as eq. (4): tau<=n implies some of
    C^(1..n) misses theta0 at some time <= n; each such miss has probability <= alpha by time-uniform coverage; C^(0) never misses.
    So the bound is at most N (not N+1) CSs. Remark 2.5 gives the tighter, printed route.
21. Assumption 2.6 (deterministic width envelope w(n,P,alpha) -> 0): CONFIRMED.
22. Theorem 2.7 (product P1 independent of pre-change; good event E_T = {theta0 in cap_{n<=T} C^(1)_n}; condition
    w(T,P0,alpha) < d; bound `3/(1-alpha) u`; partitioned eq. (1)): CONFIRMED.
    **Spec item "constant UNVERIFIED" resolved by me:** PMLR proof gives `E[(tau-T)+] <= u(k0 + alpha^k0/(1-alpha)^2)` with
    `k0 = ceil(2 log(1/(1-alpha))/log(1/alpha))`, so `alpha^k0 <= (1-alpha)^2` and the bound is `<= u(k0+1)`. For alpha < 1/2 the ratio
    `log(1/(1-alpha))/log(1/alpha) < 1`, so k0 <= 2 and `u(k0+1) <= 3u <= 3u/(1-alpha)`: the stated constant holds for alpha <= 1/2 (my
    arithmetic). For large alpha (e.g. 0.9: k0=44) the PMLR choice of k0 would give about 45u > 30u = 3u/(1-alpha), so the printed
    constant is not shown for all alpha in (0,1). Irrelevant for alpha=0.05. arXiv v2 writes `alpha^k0/(1-alpha)` (its sum is
    actually `alpha^k0/(1-alpha)^2`, a slip) and omits the factor 2 in k0: CONFIRMED.
23. Prop 2.9 (PMLR only; stationary post-change independent of F_T gives `E_0[N_1]`; non-partitioned uses ball radius d/2) and
    Prop 2.10 (i.i.d. both sides, independent, `T >= 64 log(64/(Delta^2 alpha))/Delta^2`, K1/K2, eqs. (2),(3)), Remark 2.11 Pinsker,
    Prop 3.1/Remark 3.2: CONFIRMED. Prop 2.10's conditions (i)-(ii) (independent, i.i.d.) are stated for both pre and post: CONFIRMED.
    The mixture-bet regret `2 log n for n >= 13` and bet range `[-1/(1-s), 1/s]`: CONFIRMED (Appendix B). Width bound `4 sqrt(log(n/alpha)/n)`
    used to derive the T threshold: CONFIRMED.
24. "Not covered" list (delayed/missing/reordered/adaptive sampling, dependence delay theory, windowing, one-sided harm, cost semantics): CONFIRMED
    as absence; the paper explicitly allows martingale dependence for the ARL via forward CSs (contributions bullet), and the Appendix C
    dependent example is empirical. Add (spec understated): Theorem 2.4's only requirement is CS validity under P_inf, so martingale dependence
    is genuinely covered for ARL provided the plugged-in CS is valid under that dependence. Whether the WSR Hoeffding CS holds for
    conditional-mean (non-independent) data: UNVERIFIABLE here (WSR not read).

## 7. Code deviations [spec s7] (verified against exact lines)

25. **Code lambda schedule: CONFIRMED mismatch vs main-text, equal to Appendix C except the cap.** main.py:153
    `lambda_t = sqrt(8 * log(2/self.alpha) / (t * (t + 1)))`: matches i(i+1) (P14) but there is NO `min(., 1)`. At alpha=0.005
    `8 log(400)=47.9`, so lambda exceeds 1 for t(t+1) < 47.9, i.e. up to t=6: the cap would bind in the first six updates (t=2 gives
    about 2.8). **New deviation the spec missed**: the code omits the printed `∧ 1`. The docstring at main.py:127 states the main-text
    `t log(t+1)` formula and the code uses `t(t+1)`, an internal doc/code mismatch (CONFIRMED, spec item 3).
26. **First observation skipped: CONFIRMED.** one_trial main.py:68-83: for each new `x` (n=i+1) it first updates existing CSs
    (72-74), then `init_conf_seq(n0=i+1)` (76) which returns the state dict with no data used (main.py:119-141), appended at 77.
    The new CS is first updated at the next loop with n=n0+1: `t = n - n0 + 1 = 2` (main.py:151), reading `self.data[n-1]` = X_{n0+1}
    (149). X_{n0} is never fed to that CS. Spec's description exact. The code's CS is not the paper's C^(n) built from X_n onward;
    effectively a CS started one step later whose lambda index begins at 2. Both facts together look like an off-by-one (the init
    state seems to treat X_{n0} as already counted), but the intent is UNVERIFIABLE.
    Corroboration in the Bernstein class: `sig_hat_sq = sig_num/t` (main.py:238) at t=2 with `sig_num` still the 1/4 prior implicitly
    assumes one real observation was already absorbed, which never happened.
27. **Initial state lambda_sum=1, mu_num=0: CONFIRMED** (main.py:134-135; Bernstein 213-214). Midpoint is `mu_num/(1+sum lam)`
    and half-width `w_num/(1+sum lam)`, i.e. an extra weight 1 at value 0 in the denominator only. The coverage argument printed in the paper
    gives `|mu_num - mu*sum lam| <= w_num`; with the extra 1 one only gets `|mu*(1+sum lam) - mu_num| <= w_num + mu`, so the
    half-width in the code is short by `mu/(1+sum lam)` relative to what that argument supports, and the center is biased toward 0 by
    `mu/(1+sum lam)`. My algebra; it shows the paper's argument does not imply coverage, not that coverage fails. Coverage of the code CS is
    UNVERIFIABLE, as the spec says. The w_num initial `log(2/alpha)` (main.py:136) matches the paper.
28. Window default 500 (main.py:112, 184), nesting via running max/min (162-163, 171-177), strict `u_ < l_` (177): CONFIRMED. Deque `maxlen`
    drops the oldest CS, i.e. a window the paper only suggests in Remark 2.3.
29. EB CS only in docstring/code: CONFIRMED (main.py:195-204 docstring; 244 uses t(t+1) not t log(t+1), also 3/4 cap).
30. Extra code facts: Hoeffding path never clips lambda, EB path clips at 3/4 (main.py:244). `self.data` is reset per trial in run_expt and
    asserts `n >= len(self.data)` (148). No randomness seed. These do not change conclusions.

## 6. Mapping, tiers [spec s6]

31. T2 for the native bounded-mean Hoeffding RCS from Definition 2.1 plus Appendix C formula: CONFIRMED, with a caveat: the formula is only
    fully specified once the cap `∧ 1` and one lambda schedule are chosen (the two printed ones disagree). The port must state which, and
    say that the code's CS differs (no cap, skip, pseudo-weight). T1 not clean: CONFIRMED and now stronger (three deviations, not two).
    Betting/EB RCS not T2 from this paper: CONFIRMED (bet schedule not given).
32. **"ARL >= 1/alpha means unusable at B=200": CORRECTED in wording.** What is true: Theorem 2.4 is a mean-run-length statement; at
    alpha=0.05 it only guarantees E[tau] >= 20, and the only printed finite-horizon consequence is the derived union bound
    `P(tau <= N) <= N alpha` (here 10 at N=200, vacuous) or Remark 2.5 (`P(tau<inf) <= alpha` with level `1-6alpha/(n^2 pi^2)`).
    So the guarantee does not control a per-episode false-alarm probability at B=200; it does not follow that the detector cannot run. The Hoeffding
    RCS is very conservative empirically (the paper had to shrink widths to measure ARL), so the realised null rate can be low. Use
    Remark 2.5 or `alpha/N` per CS to get a stated bound; test the realised rate against `NULL_PROMOTION_BOUND`.
33. T threshold arithmetic: `64 ln(64/(0.25*0.05))/0.25 = 2187`, `64 ln(32000)/0.04 = 16,590`: CONFIRMED my arithmetic (spec "2186"/"16,600"). Whether
    the rescaled Delta_Y = Delta_D/2 map is right depends on D in [-1,1]: UNVERIFIABLE (needs bench check; not done here).
34. Label-clock, delay, adaptive sampling deviations: reasonable ShiftLab choices, none from the paper. IPW with q: needs bounded Z
    and predictable q, but also validity of the CS under non-independent data: UNVERIFIABLE (WSR not read). Fewer-intersections-only-stops-later
    argument for windowing: CONFIRMED (printed in Sec 4.3, P8-9).

## 7b. Repo references [spec s7]

35. `bench.py:25` CONTRACT and `:30` NULL_PROMOTION_BOUND: CONFIRMED. `interface_v2.py:82-101` MonitorV2/Switcher span: CONFIRMED (class MonitorV2 at 82,
    Switcher `choose` at 101).
36. `eprocess.py` refs :9, :38, :314, :386, :443, :469, :502, :635, :693, :769, :897: CONFIRMED (def/class lines match; :314 docstring cites
    Waudby-Smith and Ramdas 2024). `detectors.py:18` ALPHA, `:221` hoeffding_width, `:226` pr_cs: CONFIRMED.
    `published_baselines.py:16`, `paired_references.py:8,96`: CONFIRMED.
37. **CORRECTED: "no e-detector / RCS implementation".** No RCS or Shekhar-Ramdas code exists (grep `shekhar|rcs.detector|SCDtoCS` in src/scripts
    py: none). But the repo does contain SR/CUSUM e-detectors the spec never mentions: `src/shiftlab/sota_search/paired_edetectors.py:11`
    (`paired_edetectors`, SR/CUSUM recurrences on queried paired-cost factors), `src/shiftlab/dive/horizon_edetectors.py:15`
    (`HorizonCalibratedEDetector`), `scripts/exhaustive_evaluation/run_paired_edetectors.py`, `check_nonpartitioned_pfa.py` (a numerical pilot of a
    Saha-Ramdas Eq3/6 non-partitioned e-detector, explicitly not author code). Their statement "found the Podkopaev-Ramdas label only" is
    imprecise: `ramdas` greps many files. `docs/anchored_gated_harm_monitor_development_protocol.md:76` already lists "Shekhar & Ramdas (2023)"
    as a required late-onset baseline, "none implemented in src (checked 2026-10-27)". An RCS port belongs beside these and must be
    differentiated from the SR/CUSUM e-detector (mixture/sum of started e-processes) versus RCS (intersection of CSs).

## Missed or understated by the spec

- The `∧ 1` cap (item 12/25) and its absence in code.
- Theorem 2.4 is stated for a fixed theta0 under P_inf; for the non-partitioned mode theta0 is unknown, so C^(m) are valid for the unknown pre-change
  theta0 under null; fine, but the detector then detects any change in theta in either direction, with no harm semantics (spec says this).
- In the non-partitioned form, ARL is proved but the delay theorem needs the pre-change CS to have shrunk (w(T,P0,alpha) < Delta) before T; this is
  why the T thresholds matter; spec covers.
- Existing e-detector code in the repo (item 37).
- Notebook typos (item 4); the pinned repo is not a runnable end-to-end reproduction.
- The reproduction identity "stopping iff no common point of running intersections" is trivial; a more discriminating test is item 26 versus the
  paper: feeding the code's and the paper's CS the same stream and checking they differ.

## Verdict

**ACCEPT WITH CORRECTIONS.** The spec is accurate on citation, definitions, theorem structure, code defaults and the first-observation skip and
initial-state deviations. Required corrections: (1) lambda has an explicit `min(.,1)` cap in both printed schedules and the code omits it;
(2) the constant 3/(1-alpha) is derivable for alpha <= 1/2 (not an open question; not shown for large alpha); (3) the "ARL >= 1/alpha unusable"
argument should be restated as "no finite-horizon false-alarm guarantee at alpha=0.05; use Remark 2.5 / alpha-per-CS"; (4) add the existing
SR/CUSUM e-detector code and the protocol-doc reference; (5) T1 not available (three code deviations, coverage of code CS unproven).
