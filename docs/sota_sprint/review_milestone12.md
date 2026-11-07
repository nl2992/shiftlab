# SOTA sprint: independent experiment review, milestones 1 and 2 (Agent G)

Date: 2026-11-03. Branch `research/sota-sprint-24`. Reviewed range 4198723..fcc0c75. HEAD moved to
54c6a37 during the review (e664e52, aeb2d4f and 54c6a37 were committed by the lead). I checked the
54c6a37 `screen.py` diff: it changes only the real-data loss-file and delay lookup, and the
synthetic path is untouched.

## Reviewer status and independence

* The HKUSTDial/ARIS skills `experiment-audit` and `result-to-claim` are **not installed**. I
  searched `~/.claude/skills`, the repo `.claude/skills` (which does not exist) and `~/.codex`.
  This review is a **native substitute**. I am the same model family as the authoring agents, so
  independence is limited to fresh context and my own recomputation from raw records.
* I did **not** open `outputs/sota_sprint/validation/`, `docs/sota_sprint/validation/` or
  `outputs/sota_sprint/validation.log`. I read two code files that touch validation:
  `outputs/sota_sprint/run_validation.sh` (the launcher) and `scripts/sota_sprint/analyze_validation.py`.
  Neither contains results.
* No git state was changed. My scratch scripts and outputs are in `/private/tmp/claude-501/review12/`:
  `integrity.py`, `nullrates.py`, `repro_cmp.py`, `corner_check.py`, `misspec.py`,
  `misspec2.py`, `gate_audit_copy.py`, `repro_{A,C,D}/`, `misspec_out.txt`, `misspec2_out.txt`.

## What I recomputed

| check | method | result |
|---|---|---|
| cost identity `net = loss + .05 labels + 5 switches` | all 61,264 raw rows in 24 runs under `outputs/sota_sprint/{A,B,C,D,X}` | 0 violations, max deviation 0 |
| hard budget | `labels <= budget` per row, including `@B100` and `@B400` | 0 violations |
| pairing | stream fingerprint `net - regret_hindsight` (the hindsight oracle cost of the realised loss stream), checked per (seed base, regime, seed) across every policy and run | 3,280 stream keys, 0 conflicts. Every policy and every run sees the identical stream |
| seed provenance | manifests | dev 2026110501; null checks 2026110511 to 2026110514. The validation bases 2026110601/02/03 appear in no dev manifest |
| future-label access | simulator release-before-act loop and a grep of `fam_*.py` | labels reach policies only through `observe`. `truth_gain` is used only in the evaluator-side `fam_b.diagnose` |
| code provenance | re-ran 3 seeds x 3 regimes at the committed code (A1-A6 and QSG; C1-C6 and pace_tuned; D1-D4) into scratch | **162/162 rows identical** to the stored dev rows (net, labels, switches, first_deploy) |
| unit tests | `uv run pytest -q tests/sota_sprint -p no:cacheprovider` | 102 passed |
| A1 corner bound | `corner_check.py`: 80 random sequences (Markov null and alternative, iid, rho=.999), 5-120 outcomes, random gaps 1-14, default and coarse (30x10) cell grids. Compared the code's `log U` with a brute-force sup over 251 p values in [0,1/2] x 451 rho values in [0,1] (including the 1-1e-6..1-1e-3 tail) | 160 comparisons, min(log U - log sup) = **0.0**, never negative |
| misspecified nulls | `misspec.py`/`misspec2.py`: new seed base 777000, T=2000, B=200, delay 100, A5b/A1b/QSG through the common simulator | see O2 |

Recomputed 20-seed null promotion on **F5_dep_null_r95** (dev base 2026110501; from A/screen1 and
X/combo_screen):

| comparator | promoted | rate [Wilson 95%] |
|---|---|---|
| gated_adaptive_range | 5/20 | .25 [.11,.47] |
| gated_adaptive_range+front | 11/20 | .55 [.34,.74] |
| discern_design_floor | 5/20 | .25 [.11,.47] |
| **discern_style** | **0/20** | 0 [0,.16] |
| SMCS+retain-incumbent | 9/20 | .45 [.26,.66] |
| xu_acquisition_only | 10/20 | .50 [.30,.70] |
| choe_ramdas_eb / +front | 7/20, 11/20 | .35, .55 |
| gated_deployment | not run in any dev screen | |
| A5b, A1b, X_A5C, CONTROL_never_switch | 0/20 each | |

These match family A's table for the comparators it ran. `family_a/RESULTS.md` also says "no
certified published comparator stays at 0 on the rho=.95 null (best: .25)". That sentence is
**false**: discern_style is 0/20 there (it was not in the A panel) and 0/20 on F5_dep_null_r8.

## Objections, ranked

### CRITICAL

**O1. The H1 claim text is false as worded, and H1 quietly relaxes the stop rule the Atlas v2
report had already registered.**
* The protocol's claim text reads: "the only method in the comparison whose false-promotion rate
  stays within the registered bound under persistence up to rho = .95". On the dev data the
  following are also within the bound: CONTROL_never_switch, A1b, X_A5C and discern_style.
  discern_style is a certified published comparator with 0/20 on both Markov nulls, so H1 part 2
  is likely to fail for it. It achieves this by never promoting (0/20 on F0_better, F7 and F9),
  at a cost above never-switch.
* `docs/failure_atlas_v2_flq/results/REPORT.md` section 9 registered the continuation test as
  "promotion <= .094 at rho=.8 and .95 and CI<0 on >= 4/6 stationary alternatives; stop if it
  fails".
* H1 part 3 replaces superiority with non-inferiority at a +5 margin. It also drops V_bursty and
  V_dep_better_r5 from the alternatives. This followed `family_a/RESULTS.md` noting that the
  Atlas criterion "looks unlikely to be met". The protocol does not flag the change as a deviation.

**Corrective action** (a pre-result amendment, committed before any validation row is opened):
1. Add the Atlas v2 section 9 criterion verbatim as a reported outcome on the six stationary
   alternatives. Change the verdict rule so that `SOTA_MET` cannot be declared if that criterion
   fails. The most such a result can be is "scoped reliability result".
2. Replace the claim template with: "A5b is within the .0936 bound on all seven in-class Markov
   nulls; certified published comparators {those listed by part 2} exceed it on {regimes};
   comparators {those passing} stay within it [with promotion rate on iid alternatives]; A5b is
   non-inferior (+5) on k/5 iid alternatives with Bernoulli disagreement arrivals." Drop "only".
   If the word "only" is kept, it must be restricted to methods that also meet part 3.

**O2. Out-of-class persistence breaks A5b's bound, and every validation null is in-class.**
Validity of A1/A5b holds only under a stationary first-order Markov sign chain with homogeneous
p <= 1/2, independent of disagreement arrivals, with constant delay. The fam_a docstring and
RESULTS.md say so. All seven `NULL_REGIMES` are inside that class, so validation cannot detect a
failure outside it. Reviewer stress test (marginal p = .5 unless stated; 800 seeds = 200 + 600
fresh):

| null (out of class unless noted) | A5b | A1b | QSG (200 seeds) |
|---|---|---|---|
| semi-Markov, Pareto(1.2) run lengths, dis .2 | **71/800 = .089 [.071,.110]** | 57/800 = .071 [.055,.091] | .58 |
| semi-Markov, dis .5 | 54/800 = .068 [.052,.087] | 4/800 = .005 | .69 |
| 2nd-order momentum, dis .5 | 44/800 = .055 [.041,.073] | 54/800 = .068 [.052,.087] | .85 |
| 2nd-order, dis .2 (200 seeds) | .025 | .025 | .75 |
| HMM p in {.5,.2} / nonstationary p_t <= .5 (200) | .005 / .005 | .005 / .005 | .015 / .015 |
| in class: Markov rho=.99, dis .2 / .5 (200) | .005 / 0 | .005 / 0 | .97 / .91 |

A5b's first-cycle promotion threshold is 2/alpha, which gives a nominal level of .025. Under
heavy-tailed run lengths its rate is 3-4x that, and the Wilson lower bound exceeds .05. The rate
stays under the .0936 tolerance on 800 seeds, but the first 200 seeds gave .105.

**Corrective action:**
1. The final claim must name the class: "stationary, first-order, time-homogeneous Markov sign
   process with p <= 1/2, any rho in [0,1], independent of disagreement arrivals, constant label
   delay". It must also state that the guarantee is model-dependent, unlike the conditional-mean
   null of Choe-Ramdas and Henzi-Ziegel.
2. Add a declared **descriptive supplemental** run of 1,000 seeds on semi-Markov,
   second-order and HMM nulls. Run it for A5b, A1b, X_A5C, both choe_ramdas ports and the
   strongest certified comparators. Report it adjacent to H1 as a limitation, not as a hypothesis.

### MAJOR

**O3. Excluding V_bursty from H1 part 3 is not a legitimate "iid stationary" exclusion.**
V_bursty's sign process is iid with p = .63; only the disagreement arrivals are bursty. On dev,
A5b loses +22.4 [+8.1,+36.7] to the best certified comparator on F9_bursty and +24.1 to QSG.
Excluding the dependent alternatives and the change regimes is a legitimate scope choice. A5b has
almost no power under persistence: S_dep_better_r95 promotes 0/20 and F5_dep_better_r8 promotes
.10, both at a cost above never-switch.

**Corrective action:** report part 3 as k/6 with V_bursty included, alongside the locked k/5.
Alternatively, state in the claim that it covers Bernoulli arrivals only. Print every excluded
regime's CI in the same table as the claim, and state that power under persistent alternatives is
near zero.

**O4. The "safety under persistence" dimension measures type-I error, not decision harm.**
On p = .5 Markov nulls G_t = 0. A false promotion there costs about c_s = 5, and
`excess_vs_expected_G` is identically 0. Only V_worse and W_worse_dep_r8 carry real harm. The
comparators control a different null: the time-averaged conditional mean. During a run of
favourable outcomes that null is genuinely positive, so their promotions there are correct by
their own null.

**Corrective action:**
1. Report, per null regime, the mean cost of each method minus never-switch, and its
   post-promotion excess loss.
2. Add the decision-relevance argument to the claim. With label delay >= 100 and rho <= .95, the
   forward-looking conditional advantage at decision time is at most about rho^delay
   (.95^100 is roughly .006). The marginal null is therefore the decision-relevant one. Without
   that argument, "comparator failure" is a null mismatch and not a defect.

**O5. Comparator fidelity.**
* `choe_ramdas_eb` is ShiftLab's internal `DiscernQCE`: PrPl-EB, p_min .05, query-conditional
  and unweighted, renamed. It is not the Choe-Ramdas boundary, and it is not the IPW-adapted port
  the novelty audit required.
* Waudby-Smith et al. 2022 (arXiv:2210.10768), recommended as a required comparator, was not added.
* gated_deployment was never screened on dev.
* discern_style is power-degenerate, as described in O1.

**Corrective action:**
1. Rename the port to "conditional-mean EB CS (QCE port, Choe-Ramdas null)".
2. As a declared supplemental on the validation seeds, add a hedged-betting (WSR) conditional-mean
   CS on the same Y, and an IPW-weighted variant.
3. Footnote discern_style as power-degenerate in the part-2 accounting.
4. Correct the false sentence in RESULTS.md.

**O6. X_A5C passed H4 on an off-target regime.**
* Its only CI below 0 is F1_late_800: -1.8 [-3.4,-0.1].
* That regime is where "no labels after discard" forfeits late improvement. Promotion falls from
  .15 to 0. The saving is 152 versus 200 labels, which outweighs a forgone promotion at t of
  about 1961.
* X_A5C is identical to A5b on the other 7 regimes.
* The regimes the mechanism actually targets (F0_worse, S_rare_null), where discard fires, were
  not in the combination screen.
* This was one marginal hit among about 30 combination-regime CIs.

**Corrective action:**
1. Amend H4 to require per-combination targeted regimes listed before the screen.
2. Record X_A5C's advance as "rule-satisfied, off-target".
3. In validation, report X_A5C against A5b on V_late_600 and W_late_1000 (the expected loss) and
   on V_worse and W_worse_dep_r8 (the expected saving).
4. Allow no X_A5C claim unless it beats A5b on its targeted regimes.

**O7. The mandatory gate fails mechanically on provenance, and the committed `gate_audit.json`
is stale.**
* Running the checker (as a scratch copy, so nothing in the repo was overwritten) gives 13/24 FAIL
  on `manifest_hash_committed`: A2-A6, C1-C6, D3 and D4. Those screens ran on uncommitted family
  code. `_git_rev` checks only `git diff`, so untracked files are invisible to it and the
  manifests show a clean 39d25ce.
* My reproduction (162/162 identical rows) shows that the results do reproduce. This is a
  bookkeeping failure, not missing execution.
* The committed `gate_audit.json` differs from the script's current output. It marks
  A4/B2/B3/B4/B6 as having no ablation and D6 as not executed.

**Corrective action:**
1. Complete the Amendment-1 re-screen of all 24 candidates at the committed revision on their
   full dev regimes, and regenerate `gate_audit.json` from it.
2. Make `_git_rev` flag untracked files under `scripts/` (`git status --porcelain scripts`).

### MINOR

* **O8. Asymmetric safety threshold.** H1 part 1 uses the point estimate <= .0936 on 1,000 seeds,
  while comparator failure needs a Wilson lower bound above .05. *Action:* report Wilson upper
  bounds, and treat "Wilson upper <= .0936" as the safety statement. Report against nominal
  alpha/2 = .025 too.
* **O9. Analysis script gaps.** `analyze_validation.py` does not evaluate H1 for X_A5C, although
  the protocol says combinations are tested "exactly as A5b". It does not load
  `synth_b5`/`null1000_b5` (Amendment 1). The H2 success count ("any" vs "all" of 5) is
  undefined. *Action:* patch and commit before reading results, and log the change as a
  pre-result fix.
* **O10. The C held-out check is not held out.** It shares seed base 2026110513 with C/null300,
  so its F0_null and F5_dep_null_r8 seeds 0-19 are the same streams. It was also used to select
  C6. C2 advanced despite not replicating and losing +24.4 at B100. *Action:* relabel the check
  as dev selection. The validation bases are confirmed fresh.
* **O11. Amendment 1 contradicts the family B evidence.** It advances B5, which the family B
  README marks "Stop". The README attributes B5's reversal gain to reserve-induced promotion
  suppression and recommends B5-reserve instead. *Action:* justify B5 or swap it, and report B5's
  reversal gain with its promotion rate.
* **O12. Exposed regime parameters.** 4/5 of the part-3 regimes are V_* instances whose
  parameters were seen in Atlas v2, and QSG, A5b's skeleton, was chosen after them. *Action:* add
  a W_*-only sensitivity row.
* **O13. Benchmark-derived constants.** B2's horizon gate uses G_REF = .1, and C uses a
  disagreement prior of .25. Both come from the generator design. *Action:* disclose them.
* **O14. Family D.** The host-AND is inert: it gives identical results on every seed. D validity
  is for a query-conditional iid null. D1 and D2 already fail rho = .8 on 300 seeds
  (.177/.180, Wilson lower bound above .0936). *Action:* predeclare that H2 for D1/D2 will be
  "cheaper but unsafe" and say that the D null is query-conditional for any real-data use.

## Mechanism checks (area 2), details

* **A1/A5b MarkovSUI.**
  * The monotone-corner bound is correct for all four transition factors. Clipping at LOG0 is
    conservative.
  * Starts snapshot before the update, so each start conditions on z_{j-1}.
  * The started mixture plus the unstarted tail mass is a test supermartingale. Each started
    ratio Q/U is at most Q/L_theta.
  * The query rule (rho_hat from released labels, gap since the last issue, private coin) is
    predictable. Disagreement indicators are independent of the sign in the generator, and
    prediction vectors carry no sign information because labels are uniform.
  * A1-nogap is an invalid ablation (null .40/.60), as reported.
  * Verdict: valid in class (see O2).
* **D DeployGate.** Ville applies to the latched certificate. Cycles run at alpha/2^c with c
  starting at 1. The combined propensity u + (1-u)q is frozen at issue. The validity claim is
  correct for the iid query-conditional null, and the authors already state the Markov failure.
* **B2.** First promotion <= alpha_base + alpha_det = alpha. Re-promotions are halved, and base
  switches are counted. The Gated base is absorbing, so it cannot re-promote at full alpha.
  Rollbacks at alpha_rb = .10 are correctly labelled as cost, not safety.
* **C.** q is frozen at issue and used as `ReleasedFeedback.query_probability`. wmax = max(1/q, 2)
  is fixed at issue, and DISCERN clamps q >= pi_min. Skipping uses a predictable coin. The
  stated estimand change (recorded events only) is correct.

## Verdicts per audit area

| area | verdict | main reasons |
|---|---|---|
| 1 Benchmark integrity | **PASS** | identity, budget and pairing exact; seeds clean; no label leakage |
| 2 Implementation fidelity/validity | **PASS-WITH-ISSUES** | A1 bound verified numerically; validity model-dependent (O2); D/B2/C correct as stated |
| 3 Comparator fidelity/strength | **PASS-WITH-ISSUES** | O5; discern_style degenerate; RESULTS.md misstatement; comparators mostly strong (+front ports favour them) |
| 4 Screening/selection integrity | **PASS-WITH-ISSUES** | O6, O10, O11; no validation-seed contamination |
| 5 Locked validation protocol | **FAIL as written** (fixable by a pre-result amendment) | O1, O3, O4, O8, O9 |
| 6 Mandatory gate | **PASS-WITH-ISSUES** | all 24 executed, each with >= 4 envs, null and outside coverage, ablations, saved records; 13/24 fail the committed-hash check (reproduction verified on a sample), stale JSON (O7) |

Continue/pivot/stop: **continue to validation only after the O1/O2/O9 amendments are committed
and the lead attests that no validation row has been read.** At best, the result supports a
scoped, model-dependent reliability claim. It does not support an unqualified SOTA claim.
