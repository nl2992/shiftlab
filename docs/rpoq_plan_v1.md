# Plan: resolved-prefix optimal querying (RPOQ), a one-gate feasibility test

## Context

ShiftLab's switching programme has run 30+ prior-art audits and has no surviving new algorithm. Every candidate was closed as a known composition (Bellman/POSG, robust FSC, group-sequential futility, online-FWER). Two threads are worth keeping:

- **Option 1 (structure result).** `src/shiftlab/dive/first_promotion_decomposition.py` is an exact solver. It cuts realization variables 15,693 → 705 at T=6, B=3, and finishes at T=8 where the generic oracle hits its node limit (`outputs/first_promotion_decomposition_scaling_v1/results.json`).
- **Option 2 (validity result).** The delayed evidence-directed PPI monitor passed 11 of 12 null cells. The registered dose×onset grid then showed −0.17 points on average and a 17-point loss for early, strong harm (`docs/delayed_ppi_fixed12_dose_onset_grid_results.md`).

**Hypothesis (RPOQ).** Define the class of query-and-stop policies that are admissible, i.e. predictable with respect to the resolved-prefix filtration, and prove when they keep the eventwise conditional null under delayed or outcome-dependent feedback. Then compute the optimal admissible policy exactly on a sufficient statistic of e-value or count, pending-label queue and remaining budget. The heuristic's early-strong-harm loss would then be a measured suboptimality gap inside a valid class.

This is a hypothesis to test and not a method claim. By the repo's own standard, a framework that is only "validity + solver" is a composition, and it fails.

**Assumptions I made about your references:**
- "HKUSTDial" is read as the HKUSTDial GitHub org's `Supervisor-Skills`. PaperBanana is not in that org; it is `dwzhu-pku/PaperBanana`.
- I read only the READMEs, not the individual `SKILL.md` files, and the ARIS summary is partly second-hand. Please correct any misreading.

## How the three frameworks map onto this repo

| Source | Principle used | Where it applies here |
|---|---|---|
| Supervisor-Skills `idea-evaluator` | Fatal-flaw audit first, then a pivot-or-proceed verdict | Stage S1 is a fatal-flaw gate before any scoring or coding |
| Supervisor-Skills | Human holds the academic judgment; AI does mechanical work with reviewable evidence | Each stage ends with a decision entry you sign off, and no stage self-approves |
| Supervisor-Skills `deep-research` / `paper-writer` | No fabricated citations; model memory never counts as a source; no placeholders | Matches `AGENTS.md`. Every prior-art claim must cite a source read this session |
| Supervisor-Skills reviewer | Reviewers reject "a simple combination of existing methods" and weak baselines | This is the S3 separation test; baselines are uniform, evidence-directed, `variance_proxy` and the Podkopaev–Ramdas delayed monitor |
| Supervisor-Skills `figure-designer` | One figure, one message | The three figures below |
| ARIS executor/reviewer split | Executor never judges its own work; the reviewer is a different model | Use for the proof and the claim map only (S2, S5), never to iterate on confirmatory results |
| ARIS `/proof-checker`, `/kill-argument` | Adversarial proof and claim attack | S2 gate and S5 claim map |
| ARIS `/result-to-claim` | Claims at the strength the evidence supports | S4 and S5 claim-to-artifact table |
| ARIS ABANDON-names-a-paper rule | A drop decision must cite the paper that already has the result | S1 and S3 kill entries |
| ARIS iteration log | Two empty rounds force a direction change | Time-box: two failed screens end the branch |
| ARIS `DATA_NEEDED` markers | Unevidenced slots stay visible | Any unproven lemma stays marked in the docs |
| PaperBanana | Diagrams and plots from paper text with a critic loop; `AGENTS.md` requires it | Visuals, below |

**Deliberate departures from ARIS:**
- No autonomous review-until-pass loop on results. It conflicts with the repo's rule to freeze hypotheses, thresholds and seeds before confirmatory runs, and it creates forking paths.
- Keep the repo's `docs/*_protocol.md` and `*_results.md` convention instead of ARIS's `.aris/` state files. If an ARIS-style log is wanted, add it as a thin index and not a second source of truth.
- Supervisor-Skills is CC BY-NC-SA 4.0. Borrow the practices, not the text.

## Stages and exit gates

Each stage ends with a dated continue/pivot/stop entry in a new `docs/rpoq_*.md`. Stop at the first failed gate.

**S1. Fatal-flaw audit (no code).**
- Write the problem in one page: filtration, query propensity, pending-label policy, delay model (fixed, independent, informative), null.
- Check the three failure risks: (i) no low-dimensional structure in the optimal policy, (ii) sufficiency of the statistic breaking under informative delay, (iii) Hampson–Jennison group-sequential delayed-response designs already covering the structure.
- Read the primary text for (iii), including its theorems, in this session.
- Gate: either name the paper that already has the result and ABANDON, or state the exact delta.

**S2. Admissibility theorem.**
- State and prove validity of the resolved-prefix-predictable class. Include the boundary case where informative delay breaks the null, with a counterexample.
- Brute-force check on small instances, reusing `src/shiftlab/dive/delayed_feedback.py` and the existing causal-game exact verifier.
- Reviewer pass by a different model family on the proof only.
- Gate: proof plus counterexample both check out.

**S3. Structure test (the decision point).**
- Solve the optimal admissible policy exactly on small T and B with `first_promotion_decomposition.py`, extended to the statistic above.
- Check whether the optimal policy is a monotone threshold in e-value, budget and pending-queue.
- Gate: threshold structure with a stated state-space growth bound is the algorithm. No structure means drop the framework and keep Options 1 and 2 as separate results.

**S4. Separation versus strongest equally equipped baselines.**
- Pre-register the primary contrast, practical threshold, seeds and stop rule using development seeds only.
- Report the gap to uniform, evidence-directed and Neyman-style allocation at matched labels, null calibration, and the early-strong-harm cell where the heuristic failed.
- Gate: the registered gain with a seed-cluster interval and a null-calibration pass.

**S5. Claim map and decision.**
- A claim-to-proof-to-artifact table, a kill-argument pass by the reviewer model, and a continue/pivot/stop record.
- Real data stays out unless a task meets the timing contract in `switching_real_data_eligibility_v1.md`.

**S6. Real-data transfer (only if S4 is mildly promising).** Yes, it can be tested on the pulled data, but the repo's own audit limits what that test can show (`docs/switching_real_data_eligibility_v1.md`, 2026-10-28).
- *What the audit found.* No audited dataset is eligible for a confirmatory real-data claim: none has verified delayed-feedback timing, a decision/availability clock and an application-grounded cost together. CRSP is the closest. It supports only a predictive-loss switching replay under an imposed daily clock, and its 2020–2025 test period is already exposed. Criteo Attribution has only 3.31% of labels maturing within its stream under the registered 30-day convention. Open Bandit has no reward-release clock. CivilComments has no event times.
- *So S6 has two tiers:*
  1. **Exploratory external-sequence replay (feasible now).**
     - Run on CRSP (and Open Bandit or Criteo as secondary dependent sequences) after the algorithm and matched-budget baselines are frozen at S4. Reusing exposed test data for development can't be repaired by new seeds.
     - Task: two frozen predictors from the registered training interval, paired next-return losses, one- and two-event release delays as sensitivity, calendar-block and security-cluster bootstrap.
     - The clocks, query cost and switching charge are imposed assumptions and must be labelled as such.
     - It answers: do the query/switch accounting and the relative gain over baselines survive a dependent real sequence? It is not a validity, causal-shift, profit or deployment test.
  2. **Genuine confirmation (needs new data).** A new, uninspected period with point-in-time features, label-availability times or an auditable fixed-delay contract, both losses identifiable from a common outcome, and a licence permitting the analysis. Until that exists, report G4 as unmet and narrow the empirical claim.
- *SOTA baselines on the real data, at matched label budget, delay clock and switching/query charges:*
  - Uniform prediction-powered monitoring.
  - The repo's evidence-directed PPI rule.
  - Active Statistical Inference allocation and Robust ASI (`robust_active_inference_proxy`).
  - Podkopaev–Ramdas delayed risk monitoring.
  - PPRM (the paired-cost PPI/CM-EB adaptation in `docs/pprm_paired_decision_benchmark.md`, labelled as an adaptation).
  - Comparing Sequential Forecasters via the authors' `comparecast` code.
  - Cheng-style hard-budget switching, and a no-switch baseline.
  - WATCH stays a scope reference, not a scored arm, until a cost-linked conformity score maps its null to the harm null.
  - Credit adaptations as adaptations. Do not describe incompatible-feedback tasks as faithful reproductions.
- *Practical dependency:* the clone has `data/reports` only. Processed datasets are excluded from Git, so restore them per `docs/cross_device_data_access.md` and verify checksums before any run. I have not checked that they are available in this session.
- *Reporting:* real-data results go in a separate table from the synthetic ones, with the imposed assumptions stated beside each number, and a claim-to-artifact row saying "exploratory, imposed clocks".

## Visuals (PaperBanana)

`AGENTS.md` requires PaperBanana for research visuals. Three figures, one message each. For plots, derive data and labels from validated outputs and inspect the exported image against the source values.
1. Method diagram of the resolved-prefix filtration and admissible class (S2/S3).
2. State-space growth: generic oracle vs reduced solver, from the scaling `results.json` (S3).
3. Gap to the heuristic across the dose×onset grid (S4).
4. Synthetic vs real-replay comparison against the SOTA baselines, with the imposed-clock caveat in the caption (S6).

Dependency to check first: PaperBanana needs a Gemini or OpenRouter key, and its plot mode is labelled legacy in its README. If neither is available in the session, `AGENTS.md` says to report the dependency and not substitute another generator.

## Verification

- Existing suites: `uv run pytest -q tests -k "first_promotion or delayed"`.
- New exact checks compared against brute-force enumeration on small instances.
- Every figure's source values checked against the exported image.

## Kill criteria

- Hampson–Jennison or another source already covers S3's structure result.
- The optimal policy has no threshold structure.
- The separation is within noise, or fails null calibration.
- The synthetic gain disappears or reverses on the real replay at matched budget. That is reported as a negative result, not tuned away.
- Two stages in a row produce no new finding, so the branch ends.
