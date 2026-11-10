# Independent check: Paper 3 pacing minimax screen

Checked against protocol `4d0099f9`, code `scripts/sota_fidelity/pacing_minimax.py` (PM), results
md/json, and `outputs/sota_fidelity/pacing_minimax/`. Scratch scripts (not in repo):
`recompute.py`, `recal.py`, `fluid.py`, `rand.py` in the session scratchpad `pacing_check/`.
`uv run pytest tests/sota_fidelity/test_pacing_minimax.py`: 3 passed.

| Item | Status | Note |
|---|---|---|
| A1 delay semantics | verified | PM 77–88: a label requested at t−d is released at the start of round t, the SR update and promotion happen next, then round-t loss uses `dep` (88). Requests at t (89–95) use `logR` from releases up to t only. |
| A2 cap / promotion / TU horizon | verified | `remaining` drops at request time (95); `~dep` blocks requests after promotion (93). TU horizon is `round(1837.5)=1838` (d=100) and 1928 (d=10), so there are no requests at t ≥ T−τ. τ = d + 5/0.08 matches protocol l.38. Labels in flight at promotion are paid for and then dropped (78), which is consistent. |
| A3 pacer formulas | verified | U/TU: 90; BURST: 91 (`q=1` when logR ≥ h, otherwise r·base). Before any label, logR = −inf, so the rate is r·U. BURST_5 = (r=.5, h=log 10) and BURST_2 = (.25, log 10) match the grid order at l.30. |
| A4 detector and A | verified | Recursion at 44/81 and λ grid at 25 match protocol l.24. A uses the "higher" 0.95 quantile of max over n ≤ 200. My re-run (seed 777, 100k sequences) gives **A = 1807.2**, 1.2% from 1785.3, and P(max ≥ 1785.3) = 0.0507 on the fresh sample, so Monte Carlo error is about 0.001. Ties are negligible: 1922 distinct values sit near the quantile. 200k samples is adequate. |
| A5 validity / invariance | qualified | The IID null holds for every pacer, BURST included. The request at t depends only on (dis, u_req, D's released by t, all from rounds ≤ t−d), and D_t is drawn independently of that history. By optional sampling, the released D's are IID Rademacher. Each pacer sees at most B of them, so P(alarm) ≤ P(max_{n≤B} R_n ≥ A) ≈ α. The p=0.4 pre-change segment is dominated: R is increasing in each D, and with a coupling I measured P = 0.0002 at p=.4. However, protocol l.27 overstates this as "the same null law under every pacer". Only the per-label sequence has the same law. The number of labels released differs by pacer, so the alarm rate is ≤ α with slack that depends on the pacer (observed 0.037–0.061). The unit test (test l.30–38, tolerance 0.05) is weak. |
| A6 oracle / regret | verified | Switching at ν has expected relative cost c_s − G(T−ν). Switching earlier adds +0.04 per round (p0=.4), so a known-ν oracle switches exactly at ν or never: min(0, c_s − G(T−ν)) (PM 101–102). G = 0.2·0.4 = 0.08. Regret includes about 7.5 cost units of label spend, which the oracle never pays. |
| A7 pairing | verified | `default_rng([seed_base, onset, delay])` (PM 64) gives the same u_dis/u_sign/u_req for every pacer in a cell. Streams are independent across onsets. |
| A8 bootstrap | qualified | Resampling one seed index jointly across onsets (174–176) keeps the pacer pairing. Because onset streams are independent, this is equivalent to resampling each onset separately. The percentile interval for a max of means is biased when onsets nearly tie (BURST_5 at 1200, 1300 and 1400). This does not affect the verdict, since the point gains are below 10%. My independent 500-resample bootstrap reproduces TU [3.9, 6.9]% and BURST_5 [1.7, 7.4]%. |
| A9 dev/test separation | verified | `tune` reads only dev.npz (143–152). File times: lock commit 18:33:47, calibration 18:33:51, selection.json 18:34:42, test.npz 18:37:30. Both manifests record HEAD 4d0099f9 with a clean worktree. |
| A-extra decision code | qualified | PM 193 checks BURST ≤ 0.9·W(TU) without the "lower limit > 0" requirement in protocol l.81. This could only make CONTINUE easier, so it cannot bias toward STOP. |
| B reproduction | verified | From test.npz at d=100: U 60.648 (onset 0), TU 57.004 (+6.01%), BURST_5 58.076 (onset 1200, +4.24%). At d=10: U 53.716, TU 51.831 (+3.51%), BURST_2 50.848 (+5.34%). All values match the JSON exactly. |
| D1 "cuts regret by up to 19 for onsets 300–800" | verified | U−BURST_5 is 14.8–19.4 over onsets 300–800, with a maximum of 19.37 at onset 700. |
| D2 "15% lower onset-average" | verified | 42.25 vs 50.01, a 15.5% reduction. |
| D3 miss at 1200: 0.69 vs 0.24 | verified | 0.689 vs 0.241 (TU 0.249). |
| D4 22 cells pass, Wilson hi ≤ 0.078 | verified | The largest Wilson hi is 0.0776 (BURST_2, d=100). Several point rates exceed α (up to 0.061), which is within noise for n=1000. |
| D5 "other bursts lose up to 57%" | qualified | The 57% figure is the d=10 cell. At d=100 the worst configuration loses 34%. The sentence does not say which cell it refers to. |
| C1 Lemma A lower bound | **wrong as stated** | Tiling gives m·⌊(T−τ)/w⌋ ≤ B, not m(T−τ)/w ≤ B. The bound is therefore W ≥ G((T−τ)/(⌊B/m⌋+1) + d). Rounding is not negligible here because B/m ≈ 3 and one window is about 500 rounds, roughly 40 cost units. |
| C2 "constant rate attains it" | **wrong** | Fluid check with m=66 and the rate cap: constant on [0,T−τ] gives W = 56.5, matching the formula. End-loaded periodic bursts at rate dis (3 bursts of 66, period 542, all within B) give W = 51.4. With m=54 the burst schedule does not win (50.2 vs 47.7), so the result is sensitive to integer effects. The rate cap is used only for feasibility, not in the lower bound. Undetectable-onset accounting (regret G(T−ν)−c_s ≤ G(d+w) for ν > T−τ−w) is correct. The uniform formula G(mT/B+d) is correct (60.80 numerically). The lemma ignores label cost. |
| C3 deterministic restriction | qualified / material | The protocol restricts the lemma to deterministic schedules, but every tested pacer is randomised. With a uniformly random phase, periodic bursts give a worst-case *expected* regret of 46.1 (m=54) and 51.9 (m=66), below the deterministic constant-rate value. So the lemma is not a minimax bound over the policies the screen compares. |
| C4 "prediction ~6%" | qualified | G·m·τ/B is about 2–3 units only if m ≈ 38–46. The results md infers m ≈ 66 from W(U), which gives 4.3 units (7.1%). That inference ignores roughly 7.5 units of label cost inside W(U); m ≈ 54 gives 3.5 units (5.8%). The observed 6.0% (3.6 units) agrees only loosely, and only once m is fitted. It is not a sharp prediction. |

## Does STOP survive?

Yes, under the locked rule. The code matches the protocol on every point that bears on the
decision, the numbers reproduce exactly, and the null validity argument holds for every pacer,
including the evidence-gated BURST. Neither TU (+6.0%) nor the dev-selected BURST_5 (+4.2%) reaches
10%, so the pre-registered STOP is correct for the pacers that were tested.

The supporting claims are weaker than written. Lemma A's lower bound and its "constant rate
attains it" claim are false in its own fluid model: integer and boundary effects matter at
B/m ≈ 3. Periodic rate-capped bursts, either deterministic or randomised-phase, beat constant-rate
truncation there by about 8–10%, and beat uniform by up to about 15% for m=66. Neither class was
in the tested grid. "Uniform is near-minimax" is therefore established only within the
U/TU/evidence-gated-BURST family, not over all predictable pacers.

The correct lemma statement is W ≥ G((T−τ)/(⌊B/m⌋+1) + d) for deterministic schedules, and it is
attained by none of the tested pacers. It should be cited as hygiene only after it is restated.
Whether periodic bursts survive a stochastic detection threshold is untested. The stop decision
stands, but the "near-minimax" reading should be narrowed.
