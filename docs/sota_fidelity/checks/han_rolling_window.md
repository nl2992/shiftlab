# Check: Han, Huang, Wang adaptive rolling window (ARW)

Independent check of `specs/han_rolling_window.md`, 2026-11-06. Nothing executed; sources only read.

## Sources actually read

- PMLR camera-ready: `https://raw.githubusercontent.com/mlresearch/v235/main/assets/han24b/han24b.pdf`
  (linked from https://proceedings.mlr.press/v235/han24b.html), 19 pp, two-column, text via
  `pdftotext -layout`.
- arXiv 2402.08672v2 (3 Jun 2024, 26 pp), re-fetched for comparison.
- Code: `eliselyhan/ARW@c48f8303d317f143d6a203d88347c7fada9aee55` via raw.githubusercontent
  (`code-synthetic-data/ARW.py`, `code-housing/ARW.py`, `algo_syn.py`, `realdata_housing.py`,
  `figures.ipynb`, `code-arxiv/arxiv_main.ipynb`, READMEs) and the git tree listing.
- Local copies: `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/check_han_iupm/`.
- Appendix proofs (A.2 to A.4, B) NOT re-derived by me; I only confirmed statement-level chain.

## Camera-ready vs arXiv v2

Mathematics and numbers are the same in every item I compared (Eq. 3.1-3.5, 3.7-3.8, Alg. 1-3, 0.1/0
experimental setting, Tables 1-4, Appendix-pointed items). Differences are cosmetic:

- NUMBERING. PMLR numbers equations (1)-(8) and results sequentially: Thm 3.8 (oracle inequality),
  Lemma 3.3 (Bernstein), Cor 3.4, Lemma 3.5, Cor 3.6, Lemma 3.7, Lemma 3.11, Thm 4.2, Assumptions
  4.3-4.5, Thm 4.6 (fast rate), Thm 4.7 (tournament), Remark 3.12. arXiv v2 uses (3.1)-(3.8),
  Cor 3.1/3.2, Lemma 3.2/3.3/3.4, Thm 3.1, Thm 4.1/4.2/4.3, Assumptions 4.1-4.3, Remark 1/2. The spec
  uses arXiv numbering throughout; label every citation with the version.
- arXiv v2 has appendix C.1 (Example 2 of synthetic data) that the PMLR PDF cites but is shorter;
  PMLR is 19 pp vs 26. No statement the spec relies on is absent from the camera-ready.
- Spec said the ICML PDF was "UNVERIFIED identical": now VERIFIED equivalent for all items below.

## Claim-by-claim

| # | Spec claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Citation PMLR 235:17374-17392; arXiv v2 3 Jun 2024 | CONFIRMED | ARW README BibTeX pages 17374--17392; arXiv stamp `2402.08672v2 [cs.LG] 3 Jun 2024` |
| 2 | Problem 3.1: B_j >= 1 iid draws from Q_j, independent datasets | CONFIRMED | PMLR Problem 3.2 (arXiv Problem 3.1), "Bj >= 1 i.i.d. samples" |
| 3 | Eq. 3.1 window mean | CONFIRMED | PMLR Eq. (1) |
| 4 | Eq. 3.2 sample variance, divisor B_{t,k}-1 | CONFIRMED | PMLR Eq. (2) |
| 5 | Eq. 3.3 psi_hat: M if B=1; v sqrt(2 log(2/d')/B) + 8M log(2/d')/(3(B-1)) | CONFIRMED | PMLR Eq. (3). Note the oracle (non-hat) psi in Cor 3.4 uses 2M log(2/d)/(3B); the 8/(3(B-1)) factor is specific to the empirical proxy (Lemma 3.5 has 13(b-a)/(3(B-1)) slack). Spec is silent; harmless |
| 6 | Eq. 3.5 phi_hat = max_{i in [k]} [ |mu_k - mu_i| - (psi_k + psi_i) ]_+ | CONFIRMED | PMLR Eq. (5); positive part and i in [k] as stated |
| 7 | Eq. 3.7/3.8 summary-statistic forms | CONFIRMED | PMLR Eq. (7),(8): `v^2 = B/(B-1) * ( (1/B) sum B_j omega_j - mu^2 )` |
| 8 | Alg. 1: argmin_k {phi_hat+psi_hat}, "any" minimiser | CONFIRMED | PMLR Alg. 1 "Choose any k in argmin" |
| 9 | Alg. 2: u = l(f1)-l(f2); output f1 iff Delta_hat <= 0 | CONFIRMED | PMLR Alg. 2: r=1 if Delta_hat <= 0, 2 if > 0 |
| 10 | Alg. 3: S=ceil(log2 m) rounds, disjoint pairs, one possible singleton, exactly m-1 Alg-2 calls, pairing order unspecified | CONFIRMED | PMLR Alg. 3 and text "calls Algorithm 2 exactly m-1 times"; no pairing rule given |
| 11 | Theorem needs M=b-a and delta'=delta/(3t) (Thm 3.1/PMLR 3.8); Thm 4.3/PMLR 4.7 uses delta/(3 m^2 t) | CONFIRMED | PMLR Thm 3.8, Thm 4.2, Thm 4.7. Also Thm 4.6 and Thm 4.7 need bounded-regression assumptions 4.3-4.5 |
| 12 | Experiments set delta'=0.1, M=0 "throughout" | CONFIRMED | PMLR Sec. 5 opening: "set to be 0.1 and 0 throughout our numerical study" (arXiv p.11) |
| 13 | Code defaults delta=0.1, M=0 | CONFIRMED with detail | `ARW.py:53,94,119`; `realdata_housing.py:161`; `figures.ipynb` "delta = 0.1; M = 0; seed = 2024"; `arxiv_main.ipynb` also `delta = 0.1`, `M = 0`. `algo_syn.py:63,116` default M=10 but every driver overrides to 0 |
| 14 | With M=0, psi_hat(B=1)=0 and the Bernstein lower-order term vanishes | CONFIRMED | `ARW.py:74-77`: B==1 gives `psi_hat = M`; else second term scales with `M` |
| 15 | Tie-rule discrepancy (code `<0` -> model 1, else model 2; paper `<=0` -> model 1) | CONFIRMED | `ARW.py:110-113`. Housing copy identical at the `pairwise_comparison` level (diff shows only prepare/psi formatting differences). Impact is larger than spec says, see "Missed" M1 |
| 16 | Housing `prepare` does not clamp negative variance, synthetic does | CONFIRMED | diff of the two ARW.py: housing line 35 `sqrt(tmp*(mu2-mu^2))`, synthetic lines 38-42 clamp. Housing result can be NaN on float round-off; unmentioned by the paper |
| 17 | Tournament shuffles with `np.random.seed(seed)`, bye to last element, consecutive pairing | CONFIRMED | `ARW.py:133-159` (note `np.random.shuffle(candidates)` is re-run each round with a global RNG). Paper does not specify |
| 18 | Window set: ARW searches all k in [t]; fixed windows I={1,4,16,64,256} | CONFIRMED | Alg. 1 loop `for k=1..t`; PMLR Sec. 5 "I = {1, 4, 16, 64, 256}" |
| 19 | Synthetic: 100 periods, 20 trials, B_va ~ U{2,3,4}, train = 3x val | CONFIRMED | PMLR Sec. 5.1 |
| 20 | arXiv topic data: 200 weeks, 15 train / 5 val per week | CONFIRMED | PMLR Sec. 5.2 |
| 21 | Housing: 192 months, 60/20/20 split, 10 candidates | CONFIRMED | PMLR Sec. 5.3 |
| 22 | Table 1: V_ARW 0.015 / 1.293, V_1 0.043 / 4.117, V_256 0.010 / 0.982 | CONFIRMED | PMLR Table 1, arXiv Table 1 |
| 23 | Table 2 V_ARW 0.139 / 2.052 | CONFIRMED | PMLR Table 2 |
| 24 | Table 3 (x1e-3) V_ARW 2.4, V_1 6.7, V_256 1.9 | CONFIRMED | PMLR Table 3 (V_64 = 1.7 is the best, unmentioned) |
| 25 | Table 4: V_ARW 0.071, V_1 0.071, V_256 0.095 | CONFIRMED | PMLR Table 4 (V_4 0.069 best; V_64 0.091) |
| 26 | Thm 3.1: probability >= 1-delta, "<~" hides log t and log(1/delta) | CONFIRMED | PMLR Thm 3.8 text |
| 27 | Chain Cor 3.2 (prob 1-2t d'), Lemma 3.3 (0<=phi_hat<=2phi), Lemma 3.4 (factor 3), Lemma 3.2 | CONFIRMED | PMLR Cor 3.6, Lemma 3.7, Lemma 3.11, Lemma 3.5 (renumbered) |
| 28 | Fast-rate theorems need bounded regression, no covariate shift; 0/1 classification only conjectured | CONFIRMED | PMLR Thm 4.6/4.7 assumptions; "We believe that in other scenarios such as binary classification..." |
| 29 | No uniform-in-t / anytime claim; Remark 2 mentions loglog t only | CONFIRMED | PMLR text after Lemma 3.11 (Remark 3.12 is about sub-exponential; the loglog remark in PMLR sits in Thm 3.8 discussion; arXiv Remark 2). No time-uniform theorem found |
| 30 | No LICENSE at the pinned SHA | CONFIRMED | git tree listing at c48f8303 has no LICENSE; `gh api repos/eliselyhan/ARW/license` returns 404 |
| 31 | Pinned HEAD c48f8303 dated 2026-08-27 "Update README.md" | CONFIRMED | `gh api commits/c48f8303` |
| 32 | "Last code change 839f8569 (2024-07-15)" | UNVERIFIED | I did not look it up; for ARW.py itself the last commit is `ab303d3c` 2024-06-01 (synthetic) and `197093cb` 2024-06-01 (housing) |
| 33 | ARWME `k_hat = argmin + 1` picks first minimiser | CONFIRMED | `ARW.py:87` |
| 34 | `prepare` special-cases B_{t,1}=1 | CONFIRMED | `ARW.py:30-35` (only handles B_all[0]==1; the sentinel of tmp=0 gives v_hat=0 for k=1; psi branch overrides with M) |
| 35 | Behaviour for B_j=0 is nan from np.mean of an empty slice | CONFIRMED by reading, not by running | `ARW.py:20-21` takes `np.mean` of a period slice with no guard; also the paper requires B_j >= 1 |
| 36 | Page numbers p.3-p.14 | CORRECTED (minor) | In the arXiv PDF Eq. (3.4)-(3.8) are on p.5, (3.2)-(3.3) on p.4; Thm 3.1 on p.5; Alg 2 on p.8; Alg 3 on p.10; the 0.1/0 setting p.11. Spec's "Eq. 3.5 p.4" should be p.5 |

## Missed by the spec (add to the record)

- M1. Discrete-loss ties are material, not an edge case. With 0/1 losses (ShiftLab) the paired gap u in
  {-1,0,+1}; Delta_hat == 0 happens whenever the retained window has equal mean losses (and always when
  all labelled rounds are agreements). Paper Alg. 2 then picks f1 (incumbent), code picks f2 (candidate).
  A port must pick one and state it; "incumbent on ties" is the paper rule and the safer one under switch cost.
- M2. delta' = 0.1 is incompatible with the theorem for any t > 3. Theorem takes delta' = delta/(3t), so
  delta' = 0.1 corresponds to nominal delta = 0.3 t, which exceeds 1 for t >= 4 (t = 100 gives 30). The
  experiments therefore carry no stated probability guarantee at all; the spec said "outside the stated
  theorem" but did not quantify.
- M3. The estimand lag: ARW targets mu_t (the LAST period's mean); window k is "k most recent periods".
  Under ShiftLab's delayed labels the freshest labelled events are those released earliest, so the most recent
  periods are systematically empty: the spec noted this for delays but not that B_{t,1} may be 0 for many
  rounds (violating B_j >= 1 and making `prepare` NaN).
- M4. Algorithm 4 (fixed-window baseline V_k) prints `s = max{t,k}` in both PMLR and arXiv; should be
  min{t,k} for the sum index t-s+1 to stay in range. Paper typo, irrelevant to ARW but relevant if ShiftLab
  ports the V_k baseline; use min.
- M5. Eq. 3.3's "8M/(3(B-1))" has no counterpart in the oracle psi (2M/(3B)); with M = 2/q_min (HT range) the
  M-term dominates quickly, so the spec's "loses power" statement is understated: M is a hard parameter of
  the bound, not a tuning nicety.
- M6. Code uses np.log(2/delta) where delta is the per-test delta' (not delta/(3t)); the driver functions never
  rescale by t, consistent with the paper's 0.1 setting but confirming that the released code cannot produce the
  theorem's guarantee without the caller rescaling.
- M7. `tournament_selection` reseeds the global NumPy RNG on every call and shuffles in place; two calls with the
  same seed are deterministic but any other NumPy use in the same process is perturbed. A port should use a local
  Generator.

## Contract questions resolved

- B = 200 is a label COUNT. `scripts/sota_sprint/bench.py:25` `CONTRACT = dict(T=2000, budget=200, cq=0.05,
  cs=5.0, alpha=0.05)`; `scripts/promising_directions/sota/simulator.py:163` `remaining = int(budget)`,
  `:197` `granted = ... and remaining > 0`, `:202` `remaining -= 1` per granted request; query price
  accrues separately at `:235` (`label_price * n_requested`). So 200 labels cost 10 loss units in total.
  Caveat: the separate `src/shiftlab/contract/interface.py` PublicEvent/TaskSpec contract states
  `remaining_budget` "in price units" (line 50) and `interface_v2.py:75` SwitchContext uses a float in loss
  units. The two contracts differ; ARW work targets the simulator contract.
- Paired losses are identifiable only on events where a label was bought: `ReleasedFeedback.model_losses`
  (simulator.py `:67-76`, constructed at `:208`) gives both models' 0/1 loss for exactly the queried event.
  Good: Alg. 2's u = l_incumbent - l_candidate is directly available per released label.

## Fidelity-tier call

- Agree with spec: core estimator on fully labelled equally spaced batches is T1-portable (author code at SHA,
  numpy-only); the ShiftLab deployment is T3 and must be named "ARW-style label-clock window selection".
- Additional constraint: because the author code ships with M=0 and the tie rule `<0`, and has no licence, port
  from the printed equations (T2 audited port), check numerically against `prepare`/`ARWME` outputs on random
  inputs, and declare both M and the tie rule explicitly. Do not vendor the unlicensed file.
- Two M settings should be reported: M = b - a (theory; for 0/1 gap b-a = 2) and M = 0 (author experiments).

## Verdict

ACCEPT WITH CORRECTIONS. All equations, algorithm boxes, defaults, tables and the tie-rule discrepancy
are confirmed against the camera-ready and the code. Corrections: use PMLR numbering alongside arXiv numbering;
fix the Eq. 3.5 page; mark item 32 UNVERIFIED; resolve the spec's B-budget question as a label count (with the
price-unit caveat on the other contract); add M1 to M7, especially the ties/B=0 handling and the delta' = 0.1
vacuity (M2).
