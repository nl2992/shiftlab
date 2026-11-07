# Check: CAMS status note (Liu et al., NeurIPS 2024)

Checker run 2026-11-06. The spec explicitly did not read the paper or equations; I did. Sources: NeurIPS 2024
camera-ready PDF (proceedings.neurips.cc .../5966e7c5c017d8449d215faeb1db4173-Paper-Conference.pdf); author
repo `xuefeng-cs/Contextual-Active-Model-Selection` at `6cbcc62fa289983d10c77637e4bd49f13c2248ed`
(`gh api`: exists, committed 2025-01-19T00:56:37Z, message "update", equals `main` HEAD). I read
`src/methods/CAMS_identity.py` (169 lines) and the head of `CAMS_test.py` (140 lines) at that SHA. Nothing
executed. ShiftLab code read: scripts/promising_directions/sota/competitors/cams.py (458 lines) and
docs/sprint2/SOTA_BENCHMARK_AUDIT.md.

## Claim-by-claim
1. Citation and authors: spec gives none. CONFIRMED: Xuefeng Liu, Fangfang Xia, Rick L. Stevens, Yuxin Chen
   (U Chicago / Argonne), "Contextual Active Model Selection", NeurIPS 2024.
2. Pinned SHA exists, equals upstream HEAD: CONFIRMED. cams.py docstring lines 3-5 carry the pin: CONFIRMED.
3. `CAMS_test.py:8` comment "#CAMS-MAX": CONFIRMED (line 8 reads that). `CAMS_identity.py` header comment
   "#The CAMS agorithm in stochatic setting": CONFIRMED (line 7). CAMS-MAX in the paper is App. G.7: CONFIRMED
   (paper text: in the stochastic setting CAMS-MAX takes the most probable policy index and then that
   policy's highest-valued model). The cams.py docstring "w_t = E_t[argmax Q]" is consistent.
4. Function positions in cams.py (normalise_advice 62, smooth_advice 76, policy_posterior 89, learning_rate 107,
   weighted_entropy_query 115, query_probability 138, loss_increment 166, _CAMSCore 177, constant_policy_advice
   281, CAMSNative 333, CAMSDeploymentAdapter 381): CONFIRMED by `grep -n` (all match).
5. Registration: scripts/sota_sprint/bench.py:66 lists `cams_adapter` (the spec also cites :67/:78 and
   fam_d.py:151-153; not re-opened, UNVERIFIABLE beyond bench.py:66).
6. Audit sentence at SOTA_BENCHMARK_AUDIT.md:24 (row text "CAMS/CAMS-MAX constant-policy deployment adapters"
   and "D2 is a ShiftLab hybrid, not published CAMS"): CONFIRMED verbatim in the row for Liu et al.
   The sentence at "l.65" ("numerical source reproduction for CAMS, Model Picker and SMCS") is present in the
   paragraph after the CAMS-MAX block: CONFIRMED (line number within a couple of lines; not exact-checked).

## Paper-vs-author-code-vs-port facts the spec did not have (material)
A. **Prediction action (CORRECTION to spec Sec. 6).** The spec says the author's action is "sample I_t ~ w_t"
   and treats argmax deployment as a pure adapter choice not in CAMS. In the PAPER's stochastic setting
   (Fig. 1, RECOMMEND, lines 30-32; Sec. 4 text) CAMS recommends the deterministic
   `j_t = maxind(w_t)`, with w_t = sum_i q_{t,i} pi_i(x_t); sampling a policy then a model is the ADVERSARIAL
   branch. The author code (CAMS_identity.py:70-73) samples `I_t ~ w_t` only to log hidden loss. So the
   port's `deploy="argmax"` default is closer to the paper than to the author code; both are legitimate but
   the docstring/spec should say "argmax follows the paper's stochastic rule; sampling follows the author
   code". Switching cost remains a ShiftLab addition (CONFIRMED: neither paper nor code has one).
B. **Learning rate.** Paper Fig. 1 SETRATE (stochastic): eta_t = sqrt(ln m / t) with m = |Pi*|. Author code
   (CAMS_identity.py:46): `sqrt(num_policies_identity / t)` (no log, policies in the numerator). The port
   (cams.py:107-112) follows the code and already notes it is not the paper schedule: CONFIRMED. The spec
   omitted this; it is a genuine paper-vs-code gap and the code value is far larger.
C. **Query probability.** Paper Eq. (4): z_t = max(1/sqrt(t), E(y_hat, w_t)), E = (1/c) sum over labels with
   lbar_y in (0,1) of lbar_y log_c(1/lbar_y); rounds where all models agree are removed as a precondition
   (footnote 3). Code (CAMS_identity.py:81-143 and utils `_compute_weighted_entropy_t` as quoted in
   cams.py:115-135): in the agreement region u=0 (matches footnote 3), but ALSO `v_t == 0 -> u_t = 0` with no
   exploration floor, and the whole score is zeroed as soon as any class has `round(w.loss_c, 6) == 0`,
   whereas the paper skips only the offending label and keeps z_t >= 1/sqrt(t). Different behaviour when w
   is nearly degenerate (a model weight < ~5e-7). The port copies the code (CONFIRMED against the port text
   at cams.py:115-163). Not a problem for the port's T1 claim, but "the paper's algorithm" is not what is
   ported in this corner.
D. **Loss update.** Paper: l_hat_{t,j} = l_{t,j} U_t / z_t, policy loss <pi_i(x_t), l_hat>; code
   `loss_hat = loss / u_t; Loss += E @ loss_hat` (CAMS_identity.py:145-153): CONFIRMED equal.
E. **Smoothing of advice** (CAMS_identity.py:61-65, `e_0` variance term) is code-only; the paper's
   regularised policy is its App. Algorithm 1 (pi + eta)/(1 + |F| eta) form. Not compared in detail:
   UNVERIFIABLE equivalence (both are "regularisation", constants differ visibly).
F. **Budget semantics.** Author code keeps drawing U_t after the budget is spent and only skips loss updates
   (CAMS_identity.py:145, 156); the paper's Fig. 1 line 12 queries only if `C_t <= b`: same effect.
G. `tuning_par` is overwritten with 1 at CAMS_identity.py:18, so any `tuning_par` argument is ignored in the
   main branch; the spec mentions only task9 constants. Minor.
H. CAMS has no stated finite-sample test guarantee of the kind ShiftLab needs: its theorems are regret/query
   complexity bounds (stochastic and adversarial), not type-I-error control. The spec said "not re-read";
   I confirm the abstract-level statement only (UNVERIFIABLE for theorem numbers/constants).

## Parity test and vendor availability
`/Users/nigelli/Desktop/ICML/Shift-lab/vendor_sota` (main checkout) contains only `.gitignore`; no `cams/`.
`tests/promising_directions/test_sota_cams.py:35` fixes `VENDOR = ROOT / "vendor_sota/cams"` and `:269`
`skipif(not (VENDOR/"src/methods/CAMS_identity.py").exists())`; no env-var/path override exists. Not run;
pytest is also absent from both `.venv`s I found. Result: parity UNVERIFIABLE by me. The pinned author
source needed for a future clean clone is exactly the SHA above.

## Tier
`CAMSNative` T1 (claimed, unconfirmed here); `cams_adapter` / `cams_max_adapter` T3 constant-policy
deployment adapters: CONFIRMED as the honest labels. With constant policies in a 2-model stream the CAMS
contextual machinery is not exercised (paper Remark: constant Dirac policies reduce to Karimi et al.'s
context-free problem); CONFIRMED in the paper Sec. 4 Remark.

**ACCEPT WITH CORRECTIONS** (correct the "argmax is an adapter choice" statement; add the eta and v_t==0
paper-vs-code gaps; parity remains unverified)
