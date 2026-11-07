# WP6 host-port calibration audit (written incrementally; later sections may be missing if the session ended)

Scope: hosts (Drift2Act, RAR, Cost-Aware Binary, Binary) and the frozen dev suite only. No Stage-B candidate was run;
`EXPERIMENT_LEDGER.jsonl` untouched; `DEV_SUITE.json`, `stream_families.yaml`, `cost_vectors.yaml` untouched.
Code HEAD at start: cc867f40. All numbers below come from runs executed in this audit (cache: `results/d2a_rar/host_audit/`).
Seeds: exactly Stage B's (`110_000_000 + cell_index*1000 + rep`, 20 reps), paired across methods. J is the mean over 20 seeds.

## 1. Diagnosis of the UNCHANGED ports (before any fix)

Frozen cells (Q1 balanced; Q2 label_dear), T=1000, label_cap=50, 20 seeds. Components are means over seeds (loss, c_q N_q, c_s N_s,
c_r N_r, c_b N_b, c_a N_a, c_h N_h). `never` = never-switch (AlwaysContinue), a reference added for diagnosis only.

| cell | method | J | loss | cq | cs | cr | cb | ca | ch | N_q | N_s | N_r | N_b | N_h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Q1[0]:iid_null_boundary** (correct_null, balanced) ||||||||||||||
| | d2a_v0 | 662.7 | 500.0 | 2.5 | 0.0 | 52.5 | 7.8 | 0.0 | 100.0 | 50.0 | 0.00 | 1.75 | 1.55 | 1000 |
| | rar_v0 | 552.9 | 550.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 552.8 | 550.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 552.8 | 550.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 472.7 | 468.4 | 2.3 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 45.8 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 470.4 | 465.9 | 2.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 455.4 | 450.9 | 2.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | episode_front | 552.9 | 550.2 | 2.5 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.05 | 0.00 | 0.00 | 0 |
| | never_switch | 550.2 | 550.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q1[1]:markov08_marg_null_only** (adverse_dependence_stress, balanced) ||||||||||||||
| | d2a_v0 | 661.7 | 500.0 | 2.5 | 0.0 | 52.5 | 6.8 | 0.0 | 100.0 | 50.0 | 0.00 | 1.75 | 1.35 | 1000 |
| | rar_v0 | 573.0 | 570.3 | 2.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 572.8 | 570.3 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 572.8 | 570.3 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 448.9 | 444.6 | 2.3 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 45.5 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 454.6 | 450.1 | 2.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 436.4 | 432.1 | 2.5 | 1.9 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.95 | 0.00 | 0.00 | 0 |
| | episode_front | 572.8 | 570.3 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | never_switch | 570.3 | 570.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q1[2]:markov05_shift_d10** (alternative, balanced) ||||||||||||||
| | d2a_v0 | 642.4 | 499.9 | 2.5 | 0.0 | 34.5 | 5.5 | 0.0 | 100.0 | 50.0 | 0.00 | 1.15 | 1.10 | 1000 |
| | rar_v0 | 636.9 | 634.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 636.8 | 634.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 636.8 | 634.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 310.1 | 305.7 | 2.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 47.8 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 292.2 | 287.8 | 2.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 475.5 | 471.9 | 2.5 | 1.1 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.55 | 0.00 | 0.00 | 0 |
| | episode_front | 528.9 | 520.4 | 2.5 | 1.8 | 0.0 | 4.2 | 0.0 | 0.0 | 50.0 | 0.90 | 0.00 | 0.85 | 0 |
| | never_switch | 634.2 | 634.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q1[3]:iid_null_lognormal_delay** (neighbouring_negative_control, balanced) ||||||||||||||
| | d2a_v0 | 660.5 | 500.0 | 2.5 | 0.0 | 51.0 | 7.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.70 | 1.40 | 1000 |
| | rar_v0 | 550.8 | 548.1 | 2.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 550.6 | 548.1 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 550.6 | 548.1 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 473.2 | 468.9 | 2.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 47.4 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 472.4 | 467.9 | 2.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 461.8 | 457.2 | 2.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | episode_front | 551.2 | 548.4 | 2.5 | 0.1 | 0.0 | 0.2 | 0.0 | 0.0 | 50.0 | 0.05 | 0.00 | 0.05 | 0 |
| | never_switch | 548.1 | 548.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[0]:iid_null_boundary** (correct_null, label_dear) ||||||||||||||
| | d2a_v0 | 672.7 | 500.0 | 12.5 | 0.0 | 52.5 | 7.8 | 0.0 | 100.0 | 50.0 | 0.00 | 1.75 | 1.55 | 1000 |
| | rar_v0 | 562.9 | 550.2 | 12.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 562.8 | 550.2 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 562.8 | 550.2 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 481.9 | 468.4 | 11.4 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 45.8 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 480.4 | 465.9 | 12.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 465.4 | 450.9 | 12.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | episode_front | 562.9 | 550.2 | 12.5 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.05 | 0.00 | 0.00 | 0 |
| | never_switch | 550.2 | 550.2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[1]:iid_shift_informative_missing** (adverse_sampling_stress, label_dear) ||||||||||||||
| | d2a_v0 | 603.0 | 481.4 | 12.5 | 0.0 | 16.5 | 2.8 | 0.0 | 89.9 | 50.0 | 0.00 | 0.55 | 0.55 | 899 |
| | rar_v0 | 655.5 | 642.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.1 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 655.4 | 642.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 655.4 | 642.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 391.6 | 377.4 | 12.1 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 48.5 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 398.1 | 383.6 | 12.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 621.2 | 612.2 | 8.8 | 0.2 | 0.0 | 0.0 | 0.0 | 0.0 | 35.2 | 0.10 | 0.00 | 0.00 | 0 |
| | episode_front | 650.8 | 637.5 | 12.5 | 0.2 | 0.0 | 0.5 | 0.0 | 0.0 | 50.0 | 0.10 | 0.00 | 0.10 | 0 |
| | never_switch | 642.9 | 642.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[2]:iid_shift_geo20** (alternative, label_dear) ||||||||||||||
| | d2a_v0 | 639.1 | 497.3 | 12.5 | 0.0 | 27.0 | 4.5 | 0.0 | 97.8 | 50.0 | 0.00 | 0.90 | 0.90 | 978 |
| | rar_v0 | 657.6 | 644.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 657.4 | 644.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 657.4 | 644.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 302.6 | 289.4 | 11.2 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 45.0 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 315.0 | 300.5 | 12.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 557.8 | 544.7 | 12.5 | 0.6 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.30 | 0.00 | 0.00 | 0 |
| | episode_front | 509.0 | 491.1 | 12.5 | 1.9 | 0.0 | 3.5 | 0.0 | 0.0 | 50.0 | 0.95 | 0.00 | 0.70 | 0 |
| | never_switch | 644.9 | 644.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[3]:iid_null_lognormal_delay** (neighbouring_negative_control, label_dear) ||||||||||||||
| | d2a_v0 | 670.5 | 500.0 | 12.5 | 0.0 | 51.0 | 7.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.70 | 1.40 | 1000 |
| | rar_v0 | 560.8 | 548.1 | 12.5 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_v0 | 560.6 | 548.1 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_v0 | 560.6 | 548.1 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | uniform_query | 482.7 | 468.9 | 11.8 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 47.4 | 1.00 | 0.00 | 0.00 | 0 |
| | fixed_schedule | 482.4 | 467.9 | 12.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | pending_cap | 471.8 | 457.2 | 12.5 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 1.00 | 0.00 | 0.00 | 0 |
| | episode_front | 561.2 | 548.4 | 12.5 | 0.1 | 0.0 | 0.2 | 0.0 | 0.0 | 50.0 | 0.05 | 0.00 | 0.05 | 0 |
| | never_switch | 548.1 | 548.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 0.00 | 0.00 | 0 |

### 1.1 Mechanisms (each verified by a host-only instrumented run, seeds = first 3 of the cell)

1. **Label cap is spent before the shift (Drift2Act, RAR, CAB, Binary).** Drift2Act requests k_low=max(1,round(cap/T*audit_every))=max(1,round(0.2))=1
   label every `audit_every`=4 rounds (0.25 labels/round, i.e. 5x the intended pacing B/T=0.05) and exhausts the 50-label cap at t=200 on
   every instrumented seed (onset of the shift is at t=295-345). RAR/Binary use `AllLabelsPolicy` (request every round) and exhaust the cap at
   t=50 (last query t=50; ADWIN received exactly 50 pre-shift labels, `det_updates`=50, zero flags, zero gate events). After exhaustion they are blind:
   J(RAR) = J(CAB) = J(Binary) = J(never-switch) + c_q N_q (+2.5 balanced, +12.5 label_dear), plus at most 0.2 of alert cost in RAR_v0.
2. **Drift2Act certificate cannot open at B=50 (paper formula, not a bug).** gate_ok is False on every round of every instrumented seed
   (0 gate-open rounds). rad(50, 0.05)=0.336 (`rad(n,delta)=sqrt(log(pi^2 n^2/(6 delta))/(2n))`, DRIFT2ACT.md section 1), so even n=50 labels
   at the pre-shift risk 0.25 give U>=0.59 > tau=0.5 (min observed U = 0.52-0.96). Opening needs n >= ~100 labels at risk 0.25 (rad(100)=0.252). Hence the host
   abstains on all 1000 rounds: N_h=1000 (c_h x 1000 = 100 at balanced), loss = 1000 x fallback 0.5 = 500, plus 1-2 retrains and 1-2 rollbacks
   from the failure branch (cooldowns 800/400) that have no effect while abstaining.
3. **Null cells have incumbent risk 0.55 > tau=0.5.** `iid_null_*` and `markov08_marg_null_only` set p=0.55 (the gain-null boundary), so the *abs-risk* null is
   false there; the Drift2Act gate is *correctly* closed. This is a property of the cell pair (cond/marg null != abs-risk null), not a port bug.
4. **RAR/Binary/CAB never use the candidate model.** Their action set is retrain (+ canary/rollback for RAR). On shift cells the controls promote the
   free candidate (loss 0.1 vs incumbent 0.9); a retrained model is at best 0.25 (needs 70% clean labelled fraction, theta_L=0.7) and about 0.575 at the
   cap-50 label fraction. Even with perfect gating a retrainer cannot match a free better candidate. This is a *model-set* property, not a porting error.
5. **Host cost vector.** RAR and CAB hosts run on `intervention_dear` (dev-suite override) while the controls run on the cell vector; J across the two is not
   comparable. This audit compares everything on the SAME cost vector (the cell's), and reports the override separately.

Reading the table: (i) RAR/CAB/Binary equal never-switch plus c_q N_q to within 0.2 J on every cell (they act on nothing); (ii) Drift2Act = 500 (all-abstain loss) + 100 (c_h)
at balanced + 1-2 retrains + 1-2 rollbacks; (iii) on the three shift cells the controls win by promoting the candidate; (iv) on the null cells the *promotion controls
beat never-switch by ~80* because the boundary null has gain exactly h=0.1 per round in favour of the candidate (promotion is profitable, not harmful, at hurdle h): J(never) 550 vs
J(uniform_query) 473. `episode_front` is ~never-switch on nulls (promotes in 5% of seeds) and 529 on the markov shift cell.

## 2. Classification and PREREGISTRATION of `calibrated_v1` (written BEFORE any calibrated run)

Rule for admissible changes: only (P) = the port deviates from a rule/value the paper states, or applies a constant at the wrong scale. Contract-scale
constants are set by a rule stated here, derived from the paper's own numbers and the contract's T and label cap, never by a J search. Anything else is (D) and
stays as ported. Old behaviour stays the default (`profile="native_v0"`, bit-identical, tested); `profile="calibrated_v1"` opts in.

| # | cause | class | change in calibrated_v1 | rule (decided now) | source |
|---|---|---|---|---|---|
| C1 | Drift2Act audit pacing 5x over budget (integer rounding of k_low) | P | k_low=1, `audit_every_eff = max(1, ceil(T / label_cap))`; k_high=4, k_max=8 kept (paper ratio 32:8:64 = 4:1:8) | the port's own stated rule "native pacing k_low/audit_every = B/L" (docstring + DRIFT2ACT.md section 6) must hold; ceil guarantees rate <= B/T | DRIFT2ACT.md s1 (k_max=64,k_high=32,k_low=8), port docstring |
| C2 | Drift2Act round-valued paper constants given for L=1500 used unscaled at T=1000 (N=1024 spans the whole stream, cooldowns 800/400 > 1/2 horizon) | P (scale) | `N, cooldown_retrain, cooldown_rollback` multiplied by T/1500 and rounded: N=683, 533, 267 | "scale windows by horizon ratio", L_paper=1500 (App. E, 'L=1500'); only paper-stated round constants are scaled; reconstruction constants (a3_cooldown, recent, alert_spacing, warmup) untouched | DRIFT2ACT.md s1 rows Window / Budget / Streams |
| C3 | RAR/Binary/CAB request a label every round -> cap exhausted at t=50 | P (contract-scale: native assumes labels free for all t) | `PacedLabelPolicy`: request iff `t % ceil(T/label_cap) == 0` (equal spacing, spends the cap uniformly) | same acquisition as the `fixed_schedule` control and as C1; the only rule that neither exhausts early nor leaves budget unspent; decided without looking at J | RAR.md Hooks (a) 'AllLabelsPolicy = labels eventually arrive' |
| D1 | Drift2Act certificate vacuous when label_cap < ~100 at risk 0.25 / tau 0.5 | D | none | the radius is the paper's formula; tau=0.5 equals the stream's tau; delta=0.05 is the paper's | DRIFT2ACT.md s1/s2 (own vacuity note) |
| D2 | Drift2Act abstain charged per abstained round, fallback loss 0.5 | D | none | contract defines N_h as abstained rounds; no persistent hand-off state exists in the action vocabulary | adapters_drift2act.py docstring |
| D3 | RAR Gate 2 (theta_L=0.7 labelled fraction in W_train=100) unreachable at label rate B/T=5% | D | none (theta_L is a STATED paper value and equals the evaluator's retrain saturation fraction `retrain_sat_fraction=0.7`) | rescaling theta_L would trivialise the gate | RAR.md Gate 2 |
| D4 | RAR/CAB windows (W_cur=40, W_ref=100, min_window_labels=5) hold <5 labels at 1 label/20 rounds -> A_cur None, gates un-evaluable | D | none | would require inventing new window rules; fixed by cells with a larger label cap (section 5) | adapters_rar.py CONTRACT_DEFAULTS |
| D5 | RAR/CAB never use the candidate model | D | none | model-set property of the method | RAR.md |
| D6 | max_lookback=0 (audit can only label the current round) | D (workload clock) | none in the port; sensitivity run reported only | clocks are frozen by DEV_SUITE.json | DEV_SUITE.json workload |
| D7 | proxy sensing / hand-set evidence and T for Drift2Act | D (documented deviation) | none | no calibration data in the contract | DRIFT2ACT.md s6 |

Comparison plan (fixed now): hosts {Drift2Act, RAR, CAB, Binary} x {native_v0, calibrated_v1} and controls {uniform_query, pending_cap, fixed_schedule,
episode_front} + never-switch, on all 8 frozen cells, SAME cost vector per cell (the cell's), 20 paired seeds, `verify_run` on every run. Statistic: mean paired
dJ = J(host) - J(control) with 95% paired percentile bootstrap CI (2000 resamples, `paired_bootstrap_ci`). Effect grading per FAIR-EVALUATION standard
(relative to the control's J: <1% negligible, 1-3% small, 3-10% meaningful, >10% substantial). No parameter of calibrated_v1 is revisited after seeing results; a
host that still loses is recorded as a (D) finding.

### 2.1 Amendment (logged before the comparison tables were written, after the first calibrated frozen-suite run)

The first calibrated run showed RAR/CAB/Binary with zero ADWIN flags even with paced labels. I therefore examined the detector IN ISOLATION (synthetic Bernoulli
sequence 0.25 -> 0.9, `river` 0.26.1 ADWIN delta=0.002, no host, no J): with 15 pre-shift labels (what a 5% label rate yields by t~300) ADWIN detected 0/40 sequences within 150 post-shift
labels for both `clock=32` (river default) and `clock=1` (exact ADWIN); with 30 pre-labels 18/40 (clock 32, median 98 post-labels) and 26/40 (clock 1, median 102); with 60 pre-labels 40/40
(median 68 / 48.5 post-labels). So the check period is NOT the cause and changing it would not help; delta=0.002 is river's default (RAR.md lists it among the *unstated* parameters),
a false-alarm rate, not a scale constant. Classified **D8** (detector under-powered at B=50 labels); NOT changed. Result files: `results/d2a_rar/host_audit/frozen_cell.json` (and
`frozen_override.json`) were produced by exactly the calibrated_v1 defined in section 2 (C1-C3); no parameter changed after that run.

## 3. Frozen-suite results after calibrated_v1 (host-only; same seeds as Stage B; cell cost vector for every method)

Raw: `results/d2a_rar/host_audit/frozen_cell.json` (all methods on the cell's cost vector) and `frozen_override.json` (all methods on `intervention_dear`, the dev-suite
host override). Reproduce: `python -m shiftlab.autoresearch.host_audit frozen` (about 4 min CPU).

### 3.1 Component decomposition of the calibrated hosts (means over 20 seeds)

| cell | method | J | loss | cq | cs | cr | cb | ca | ch | N_q | N_s | N_r | N_b | N_h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Q1[0]:iid_null_boundary** (correct_null, balanced) ||||||||||||||
| | d2a_cal | 637.5 | 500.0 | 2.5 | 0.0 | 30.0 | 5.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 1.00 | 1000 |
| | rar_cal | 552.8 | 550.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 552.8 | 550.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 552.8 | 550.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q1[1]:markov08_marg_null_only** (adverse_dependence_stress, balanced) ||||||||||||||
| | d2a_cal | 637.5 | 500.0 | 2.5 | 0.0 | 30.0 | 5.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 1.00 | 1000 |
| | rar_cal | 572.8 | 570.3 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 572.8 | 570.3 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 572.8 | 570.3 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q1[2]:markov05_shift_d10** (alternative, balanced) ||||||||||||||
| | d2a_cal | 637.5 | 500.0 | 2.5 | 0.0 | 30.0 | 5.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 1.00 | 1000 |
| | rar_cal | 636.8 | 634.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 636.8 | 634.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 636.8 | 634.2 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q1[3]:iid_null_lognormal_delay** (neighbouring_negative_control, balanced) ||||||||||||||
| | d2a_cal | 637.5 | 500.0 | 2.5 | 0.0 | 30.0 | 5.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 1.00 | 1000 |
| | rar_cal | 550.6 | 548.1 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 550.6 | 548.1 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 550.6 | 548.1 | 2.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[0]:iid_null_boundary** (correct_null, label_dear) ||||||||||||||
| | d2a_cal | 647.5 | 500.0 | 12.5 | 0.0 | 30.0 | 5.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 1.00 | 1000 |
| | rar_cal | 562.8 | 550.2 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 562.8 | 550.2 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 562.8 | 550.2 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[1]:iid_shift_informative_missing** (adverse_sampling_stress, label_dear) ||||||||||||||
| | d2a_cal | 645.7 | 500.0 | 12.5 | 0.0 | 30.0 | 3.2 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 0.65 | 1000 |
| | rar_cal | 655.4 | 642.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 655.4 | 642.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 655.4 | 642.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[2]:iid_shift_geo20** (alternative, label_dear) ||||||||||||||
| | d2a_cal | 647.5 | 500.0 | 12.5 | 0.0 | 30.0 | 5.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 1.00 | 1000 |
| | rar_cal | 657.4 | 644.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 657.4 | 644.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 657.4 | 644.9 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| **Q2[3]:iid_null_lognormal_delay** (neighbouring_negative_control, label_dear) ||||||||||||||
| | d2a_cal | 647.5 | 500.0 | 12.5 | 0.0 | 30.0 | 5.0 | 0.0 | 100.0 | 50.0 | 0.00 | 1.00 | 1.00 | 1000 |
| | rar_cal | 560.6 | 548.1 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | cab_cal | 560.6 | 548.1 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |
| | bin_cal | 560.6 | 548.1 | 12.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.0 | 0.00 | 0.00 | 0.00 | 0 |

(`d2a_cal` is the same 637.5 on every balanced cell: it abstains 1000 rounds (500 + 100), issues exactly one retrain (30) and one rollback (5) and 50 labels (2.5), independent of the stream.)

### 3.2 Paired dJ = J(host) - J(control), mean [95% paired-bootstrap CI], 20 seeds, positive = host worse

Cell cost vector. Columns: uniform_query, episode_front, pending_cap, fixed_schedule.

| cell | host | dJ vs uniform_query | dJ vs episode_front | dJ vs pending_cap | dJ vs fixed_schedule |
| Q1[0]:iid_null_boundary | d2a_v0 | +190.0 [+176.4,+202.7] | +109.9 [+100.6,+118.8] | +207.3 [+197.7,+217.2] | +192.3 [+181.4,+203.4] |
| Q1[0]:iid_null_boundary | d2a_cal | +164.8 [+154.2,+175.1] | +84.6 [+77.9,+91.2] | +182.0 [+175.5,+188.8] | +167.0 [+158.8,+175.8] |
| Q1[0]:iid_null_boundary | rar_cal | +80.0 [+64.4,+95.5] | -0.1 [-0.3,+0.0] | +97.3 [+84.5,+110.5] | +82.3 [+68.7,+97.0] |
| Q1[0]:iid_null_boundary | cab_cal | +80.0 [+64.4,+95.5] | -0.1 [-0.3,+0.0] | +97.3 [+84.5,+110.5] | +82.3 [+68.7,+97.0] |
| Q1[1]:markov08_marg_null_only | d2a_v0 | +212.8 [+193.0,+234.4] | +88.9 [+66.4,+111.1] | +225.3 [+200.8,+251.6] | +207.1 [+182.5,+234.5] |
| Q1[1]:markov08_marg_null_only | d2a_cal | +188.6 [+168.3,+208.8] | +64.7 [+41.4,+86.9] | +201.0 [+177.6,+225.4] | +182.9 [+158.2,+209.4] |
| Q1[1]:markov08_marg_null_only | rar_cal | +123.9 [+82.5,+166.9] | +0.0 [+0.0,+0.0] | +136.3 [+91.0,+183.7] | +118.2 [+74.1,+166.9] |
| Q1[1]:markov08_marg_null_only | cab_cal | +123.9 [+82.5,+166.9] | +0.0 [+0.0,+0.0] | +136.3 [+91.0,+183.7] | +118.2 [+74.1,+166.9] |
| Q1[2]:markov05_shift_d10 | d2a_v0 | +332.4 [+306.3,+358.1] | +113.5 [+79.3,+148.2] | +166.9 [+97.3,+231.1] | +350.2 [+337.0,+363.9] |
| Q1[2]:markov05_shift_d10 | d2a_cal | +327.4 [+301.9,+352.5] | +108.6 [+73.7,+144.0] | +162.0 [+92.4,+225.8] | +345.2 [+334.6,+355.5] |
| Q1[2]:markov05_shift_d10 | rar_cal | +326.7 [+295.7,+355.7] | +107.8 [+71.9,+144.7] | +161.2 [+90.6,+226.3] | +344.5 [+331.2,+358.0] |
| Q1[2]:markov05_shift_d10 | cab_cal | +326.7 [+295.7,+355.7] | +107.8 [+71.9,+144.7] | +161.2 [+90.6,+226.3] | +344.5 [+331.2,+358.0] |
| Q1[3]:iid_null_lognormal_delay | d2a_v0 | +187.3 [+179.0,+194.9] | +109.2 [+101.9,+116.2] | +198.7 [+189.8,+207.3] | +188.0 [+177.0,+197.9] |
| Q1[3]:iid_null_lognormal_delay | d2a_cal | +164.3 [+156.9,+171.2] | +86.2 [+81.5,+90.9] | +175.7 [+170.7,+180.9] | +165.0 [+155.5,+173.3] |
| Q1[3]:iid_null_lognormal_delay | rar_cal | +77.4 [+68.3,+87.1] | -0.7 [-1.9,+0.0] | +88.8 [+79.5,+98.5] | +78.2 [+66.4,+89.8] |
| Q1[3]:iid_null_lognormal_delay | cab_cal | +77.4 [+68.3,+87.1] | -0.7 [-1.9,+0.0] | +88.8 [+79.5,+98.5] | +78.2 [+66.4,+89.8] |
| Q2[0]:iid_null_boundary | d2a_v0 | +190.8 [+177.3,+203.5] | +109.9 [+100.6,+118.8] | +207.3 [+197.7,+217.2] | +192.3 [+181.4,+203.4] |
| Q2[0]:iid_null_boundary | d2a_cal | +165.6 [+154.8,+175.9] | +84.6 [+77.9,+91.2] | +182.0 [+175.5,+188.8] | +167.0 [+158.8,+175.8] |
| Q2[0]:iid_null_boundary | rar_cal | +80.8 [+65.1,+96.5] | -0.1 [-0.3,+0.0] | +97.3 [+84.5,+110.5] | +82.3 [+68.7,+97.0] |
| Q2[0]:iid_null_boundary | cab_cal | +80.8 [+65.1,+96.5] | -0.1 [-0.3,+0.0] | +97.3 [+84.5,+110.5] | +82.3 [+68.7,+97.0] |
| Q2[1]:iid_shift_informative_missing | d2a_v0 | +211.5 [+174.4,+251.2] | -47.7 [-73.6,-20.3] | -18.2 [-60.0,+36.5] | +204.9 [+169.2,+239.2] |
| Q2[1]:iid_shift_informative_missing | d2a_cal | +254.2 [+215.5,+290.3] | -5.0 [-14.9,+9.1] | +24.5 [-8.2,+71.5] | +247.6 [+214.9,+277.9] |
| Q2[1]:iid_shift_informative_missing | rar_cal | +263.8 [+223.8,+302.1] | +4.6 [-3.9,+17.7] | +34.1 [+2.9,+80.4] | +257.2 [+225.0,+287.3] |
| Q2[1]:iid_shift_informative_missing | cab_cal | +263.8 [+223.8,+302.1] | +4.6 [-3.9,+17.7] | +34.1 [+2.9,+80.4] | +257.2 [+225.0,+287.3] |
| Q2[2]:iid_shift_geo20 | d2a_v0 | +336.5 [+317.6,+355.2] | +130.1 [+95.2,+165.6] | +81.3 [+16.9,+149.8] | +324.1 [+304.4,+343.6] |
| Q2[2]:iid_shift_geo20 | d2a_cal | +344.9 [+326.5,+361.5] | +138.5 [+103.2,+172.0] | +89.7 [+24.6,+156.2] | +332.5 [+315.0,+350.4] |
| Q2[2]:iid_shift_geo20 | rar_cal | +354.8 [+336.5,+371.7] | +148.4 [+113.3,+181.2] | +99.6 [+32.9,+166.9] | +342.4 [+324.2,+360.3] |
| Q2[2]:iid_shift_geo20 | cab_cal | +354.8 [+336.5,+371.7] | +148.4 [+113.3,+181.2] | +99.6 [+32.9,+166.9] | +342.4 [+324.2,+360.3] |
| Q2[3]:iid_null_lognormal_delay | d2a_v0 | +187.8 [+179.6,+195.5] | +109.2 [+101.9,+116.2] | +198.7 [+189.8,+207.3] | +188.0 [+177.0,+197.9] |
| Q2[3]:iid_null_lognormal_delay | d2a_cal | +164.8 [+157.4,+171.7] | +86.2 [+81.5,+90.9] | +175.7 [+170.7,+180.9] | +165.0 [+155.5,+173.3] |
| Q2[3]:iid_null_lognormal_delay | rar_cal | +77.9 [+68.8,+87.6] | -0.7 [-1.9,+0.0] | +88.8 [+79.5,+98.5] | +78.2 [+66.4,+89.8] |
| Q2[3]:iid_null_lognormal_delay | cab_cal | +77.9 [+68.8,+87.6] | -0.7 [-1.9,+0.0] | +88.8 [+79.5,+98.5] | +78.2 [+66.4,+89.8] |

On `intervention_dear` (RAR/CAB override): columns uniform_query, episode_front, never_switch.

| cell | host | dJ vs uniform_query | dJ vs episode_front | dJ vs never_switch |
| Q1[0]:iid_null_boundary | rar_v0 | +72.4 [+56.8,+88.0] | -0.1 [-1.1,+0.5] | +2.9 [+2.9,+3.0] |
| Q1[0]:iid_null_boundary | rar_cal | +72.0 [+56.4,+87.5] | -0.5 [-1.5,+0.0] | +2.5 [+2.5,+2.5] |
| Q1[0]:iid_null_boundary | cab_cal | +72.0 [+56.4,+87.5] | -0.5 [-1.5,+0.0] | +2.5 [+2.5,+2.5] |
| Q1[1]:markov08_marg_null_only | rar_v0 | +116.3 [+74.8,+159.3] | +0.4 [+0.3,+0.5] | +2.9 [+2.8,+3.0] |
| Q1[1]:markov08_marg_null_only | rar_cal | +115.9 [+74.5,+158.9] | +0.0 [+0.0,+0.0] | +2.5 [+2.5,+2.5] |
| Q1[1]:markov08_marg_null_only | cab_cal | +115.9 [+74.5,+158.9] | +0.0 [+0.0,+0.0] | +2.5 [+2.5,+2.5] |
| Q1[2]:markov05_shift_d10 | rar_v0 | +319.1 [+288.1,+348.0] | +84.0 [+48.9,+119.8] | +2.9 [+2.8,+3.0] |
| Q1[2]:markov05_shift_d10 | rar_cal | +318.7 [+287.7,+347.7] | +83.7 [+48.4,+119.3] | +2.5 [+2.5,+2.5] |
| Q1[2]:markov05_shift_d10 | cab_cal | +318.7 [+287.7,+347.7] | +83.7 [+48.4,+119.3] | +2.5 [+2.5,+2.5] |
| Q1[3]:iid_null_lognormal_delay | rar_v0 | +69.8 [+60.7,+79.5] | -1.7 [-5.8,+0.5] | +2.9 [+2.8,+3.0] |
| Q1[3]:iid_null_lognormal_delay | rar_cal | +69.4 [+60.3,+79.1] | -2.0 [-6.2,+0.0] | +2.5 [+2.5,+2.5] |
| Q1[3]:iid_null_lognormal_delay | cab_cal | +69.4 [+60.3,+79.1] | -2.0 [-6.2,+0.0] | +2.5 [+2.5,+2.5] |
| Q2[0]:iid_null_boundary | rar_v0 | +72.4 [+56.8,+88.0] | -0.1 [-1.1,+0.5] | +2.9 [+2.9,+3.0] |
| Q2[0]:iid_null_boundary | rar_cal | +72.0 [+56.4,+87.5] | -0.5 [-1.5,+0.0] | +2.5 [+2.5,+2.5] |
| Q2[0]:iid_null_boundary | cab_cal | +72.0 [+56.4,+87.5] | -0.5 [-1.5,+0.0] | +2.5 [+2.5,+2.5] |
| Q2[1]:iid_shift_informative_missing | rar_v0 | +255.8 [+215.6,+294.1] | +2.1 [-7.8,+13.8] | +2.8 [+2.7,+2.9] |
| Q2[1]:iid_shift_informative_missing | rar_cal | +255.5 [+215.3,+293.8] | +1.8 [-8.1,+13.5] | +2.5 [+2.5,+2.5] |
| Q2[1]:iid_shift_informative_missing | cab_cal | +255.5 [+215.3,+293.8] | +1.8 [-8.1,+13.5] | +2.5 [+2.5,+2.5] |
| Q2[2]:iid_shift_geo20 | rar_v0 | +346.2 [+327.8,+363.0] | +127.2 [+93.0,+159.8] | +2.9 [+2.8,+3.0] |
| Q2[2]:iid_shift_geo20 | rar_cal | +345.8 [+327.5,+362.6] | +126.8 [+92.6,+159.5] | +2.5 [+2.5,+2.5] |
| Q2[2]:iid_shift_geo20 | cab_cal | +345.8 [+327.5,+362.6] | +126.8 [+92.6,+159.5] | +2.5 [+2.5,+2.5] |
| Q2[3]:iid_null_lognormal_delay | rar_v0 | +69.8 [+60.7,+79.5] | -1.7 [-5.8,+0.5] | +2.9 [+2.8,+3.0] |
| Q2[3]:iid_null_lognormal_delay | rar_cal | +69.4 [+60.3,+79.1] | -2.0 [-6.2,+0.0] | +2.5 [+2.5,+2.5] |
| Q2[3]:iid_null_lognormal_delay | cab_cal | +69.4 [+60.3,+79.1] | -2.0 [-6.2,+0.0] | +2.5 [+2.5,+2.5] |

### 3.3 What the calibration changed (and what it did not)

* Drift2Act (C1+C2): J 662.7 -> 637.5 on balanced null cells (-25: one retrain+rollback fewer), -5 on the markov shift cell, +8..+10 on Q2 shift cells (cooldown scaling changes the retrain count; no
  mechanism gain). calibrated gate-open rounds: **0 in all 160 runs**. native_v0 opened the gate only in Q2[1] informative_missing (10/20 seeds, mean 417 rounds) and Q2[2] geo20 (3/20 seeds), i.e.
  exactly where the released-label subset is unrepresentative (informative missingness) or labels were exhausted early; calibration removes those by pacing, it does not make the certificate informative.
* RAR / CAB / Binary (C3): |dJ| <= 0.4 between profiles. Both profiles: **0 ADWIN flags and 0 gate evaluations in all 160 runs**; J = never-switch + c_q N_q exactly (dJ vs never-switch is +2.5 on
  balanced and +12.5 on label_dear cells in every cell = 50 labels x c_q). They are inert at B=50.
* Counts over the 8 frozen cells (95% paired CI excludes 0), calibrated hosts: Drift2Act worse than uniform_query / fixed_schedule on 8/8, worse than pending_cap on 7/8 (1 tie), worse than episode_front on 7/8
  (1 tie); never better than any control. RAR, CAB, Binary: worse than uniform_query / fixed_schedule / pending_cap on 8/8, tie with episode_front on 6/8 (worse by 0.1-2 on 2). The single native_v0
  win (d2a_v0 vs episode_front on Q2[1], -47.7 [-73.6,-20.3]) disappears in the calibrated profile (-5.0 [-14.9,+9.1]).
* Therefore: the frozen-suite result "hosts are dominated by simple controls" is **not an artefact of the two porting errors**; after fixing C1-C3 it is unchanged (largest host-J change 25 on a ~650 base, 4%).
  Its causes are (D): see section 4.
* The dev-suite statement that controls run on the cell vector while RAR/CAB run on `intervention_dear` matters little here: on `intervention_dear` RAR/CAB are still never-switch + 2.5.

## 4. Final classification (per port)

| port | cause | class | fix | rule | effect on J (frozen suite) |
|---|---|---|---|---|---|
| Drift2Act | audit pacing 0.25 labels/round vs B/T=0.05; cap gone at t=200 (before onset t~330) | P | C1: audit_every=ceil(T/B)=20, k_low=1 | stated pacing rule k_low/audit_every<=B/T | -5 .. -25 / +8 on Q2 shift (no systematic gain) |
| Drift2Act | N=1024 (> T) and cooldowns 800/400 unscaled from L=1500 | P (scale) | C2: x T/1500 -> 683/533/267 | horizon ratio | included above |
| Drift2Act | certificate U=R^+rad(n,0.05) cannot reach tau=0.5 with n<=50 (rad(50)=0.336; needs n>~100 at risk 0.25) -> gate closed, abstain on all 1000 rounds | **D** | none | paper radius, stream tau, paper delta | explains J = 500 + 100 + ~37 |
| Drift2Act | per-round c_h and fallback loss 0.5 per abstained round (contract definition of hand-off) | D | none | contract | 600 J / 1000 rounds of abstention |
| Drift2Act | null cells have incumbent risk 0.55 > tau 0.5 (abs-risk null false): closed gate is correct | D (cell property) | none | | |
| Drift2Act | max_lookback=0: audit can only label the current round | D (workload) | none; v2 cells keep 0 | frozen clocks | n_t truncated to 1 per round (k_high unreachable) |
| RAR / CAB / Binary | AllLabelsPolicy requests every round -> cap spent by t=50 (pre-shift) | P | C3: PacedLabelPolicy every ceil(T/B)=20 rounds | spend the cap uniformly | <=0.4 J (still inert) |
| RAR / CAB / Binary | ADWIN(delta=0.002) given <=15 pre-shift and <=35 post-shift labels never fires (isolated test: 0/40 within 150 post-labels at 15 pre-labels, clock 32 or 1) | **D** (D8) | none | river default; false-alarm rate, not a scale constant | 0 flags in 160 runs |
| RAR | Gate 2 (theta_L=0.7 labelled in W_train=100) unreachable at 5% label rate; windows hold <5 labels | **D** (D3/D4) | none | stated theta_L = evaluator's retrain saturation 0.7 | 0 gate evaluations |
| RAR / CAB / Binary | never use the candidate model; retrain best case 0.25 loss vs candidate 0.1 | **D** (D5) | none | model-set property | cannot beat promotion controls on shift cells even with perfect gating (S2a: RAR 529 vs uniform 356) |
| CAB | economic test d_hat*H >= c_r (0.65*100=65 < 100) refuses retrain even after a flag | D | none | paper rule | S2a: CAB 1.8 flags, 0 retrains |
| all hosts | host-cost-vector override (rar/cab on intervention_dear, controls on cell vector) makes J incomparable in Stage-B ledger comparisons | note | audit compares on one vector | | none at B=50 |

Honest bottom line: after fixing every porting error I could justify from the papers, the hosts still lose to simple controls on the frozen suite, and the reason is the **label cap (B/T=5%) combined with
the paper's own statistical thresholds**, not a defect in the port: it is a legitimate benchmark result "SOTA host dominated by simple control under contract X (cap 50, free candidate)". A
fair host-vs-candidate comparison needs cells where the host can operate (section 5).

## 5. DEV_SUITE_v2: new cells that make the inert hooks matter (host-only; NO candidate was run)

Files (new; nothing existing was edited in place): `docs/d2a_rar/registry/DEV_SUITE_v2.json` (15 cells; parent = sha256 of DEV_SUITE.json recorded in it), `configs/d2a_rar/stream_families_v2.yaml`
(11 new families; the frozen v1 families `iid_shift_d10`, `iid_null_boundary`, `iid_null_lognormal_delay` are referenced from `stream_families.yaml` with `family_source: v1`),
`StreamSpec.regime_process='semi_markov'` (new optional fields, default 'single' = bit-identical; tested). Regenerate: `python -m shiftlab.autoresearch.host_audit build-v2`
(deterministic; a test compares the files with a rebuild). Seeds: `110_050_000 + cell_index*1000 + rep` (inside the dev block, disjoint from v1 cells), 20 reps, paired. Every cell has per-cell T, label_cap,
cost vector (no host override in v2: every method uses the cell vector), max_lookback=0, retrain_duration=20. Run: `python -m shiftlab.autoresearch.host_audit v2` (about 10 min CPU), raw `results/d2a_rar/host_audit/v2_host_only.json`.

| scenario | cells (alternative / correct null / neighbouring negative control) | hook targeted | design |
|---|---|---|---|
| S1 tight deadline | S1a `td_shift_lognormal_T400` / S1b `td_null_lognormal_T400` / S1c `td_null_fixed10_T400` | request feasibility, deadline priority, pending inventory | T=400, lognormal delay median 80 sigma 1 (tail ~ remaining horizon); control = same null with fixed delay 10 |
| S2 RAR label-rich | S2a `iid_shift_d10` / S2b `iid_null_boundary` / S2c `iid_null_lognormal_delay`, cap = T = 1000, intervention_dear | rar.gate2/gate3, cab.gate | RAR's native 'every label arrives'; Gate 2 reachable |
| S2 certifiable | S2d `iid_shift_d10` / S2e `cert_null_p030` / S2f `cert_null_p030_lognormal`, cap 300, label_dear | Drift2Act certificate / request size / abstain | S2e,S2f: cond, marg AND abs-risk nulls hold (risk 0.30 <= tau) |
| S3 reversal (FL-043) | S3a `reversal_1200` / S3b `reversal_null_1200` / S3c `reversal_persistent_1200`, T=1200, cap 60, balanced | rollback / promote-then-revert | candidate better on ~[300,720), worse again after (p_after=0.25); S3c persistent twin: a rollback mechanism must not hurt |
| S4 hazard / semi-Markov | S4a `hazard_shift_k25` / S4b `hazard_null_k25` / S4c `hazard_shift_k10`, cap 50, balanced | hazard-aware gating, regime-duration priors | Weibull sojourns (shape 2.5 increasing hazard; 'before' scale 250, 'during' scale 150); S4c = flat hazard (shape 1), same scales |

Null truth flags in the JSON are computed from `make_stream` truth (not typed): correct-null cells have cond=marg=True; S2e/S2f also abs_risk=True; all `alternative` cells have marg=False.

### 5.1 Host-only results on v2 (calibrated hosts vs controls; exploratory, nothing tuned, 20 paired seeds)

**J (mean over 20 seeds)**

| cell | role | T | cap | cv | d2a_v0 | d2a_cal | rar_v0 | rar_cal | cab_cal | uniform_query | pending_cap | fixed_schedule | episode_front | never_switch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1a td_shift_lognormal_T400 | alternative | 400 | 50 | label_dear | 287.5 | 287.3 | 281.4 | 281.4 | 281.2 | 157.8 | 230.1 | 153.1 | 274.8 | 268.8 |
| S1b td_null_lognormal_T400 | correct_null | 400 | 50 | label_dear | 287.5 | 284.0 | 233.4 | 233.3 | 233.2 | 211.2 | 210.0 | 209.1 | 233.2 | 220.8 |
| S1c td_null_fixed10_T400 | neighbouring_negative_control | 400 | 50 | label_dear | 287.5 | 287.5 | 228.2 | 228.5 | 228.0 | 206.2 | 201.8 | 205.8 | 228.0 | 215.5 |
| S2a iid_shift_d10 | alternative | 1000 | 1000 | intervention_dear | 839.9 | 901.6 | 529.0 | 529.0 | 689.9 | 355.6 | 355.6 | 355.6 | 328.2 | 640.0 |
| S2b iid_null_boundary | correct_null | 1000 | 1000 | intervention_dear | 931.2 | 985.4 | 605.6 | 605.6 | 602.5 | 509.2 | 509.2 | 509.2 | 605.6 | 552.5 |
| S2c iid_null_lognormal_delay | neighbouring_negative_control | 1000 | 1000 | intervention_dear | 933.7 | 983.2 | 600.1 | 600.1 | 596.9 | 514.2 | 514.2 | 514.2 | 596.4 | 546.9 |
| S2d iid_shift_d10 | alternative | 1000 | 300 | label_dear | 692.9 | 726.4 | 714.2 | 703.1 | 621.4 | 324.1 | 459.2 | 324.2 | 376.0 | 639.3 |
| S2e cert_null_p030 | correct_null | 1000 | 300 | label_dear | 685.2 | 707.7 | 375.0 | 363.4 | 362.1 | 709.4 | 751.1 | 685.0 | 374.6 | 299.6 |
| S2f cert_null_p030_lognormal | neighbouring_negative_control | 1000 | 300 | label_dear | 684.9 | 717.1 | 378.5 | 366.9 | 365.5 | 663.6 | 737.4 | 664.1 | 378.0 | 303.0 |
| S3a reversal_1200 | alternative | 1200 | 60 | balanced | 727.0 | 758.0 | 574.8 | 574.6 | 574.6 | 560.8 | 581.9 | 547.6 | 564.0 | 571.6 |
| S3b reversal_null_1200 | correct_null | 1200 | 60 | balanced | 793.0 | 758.0 | 659.8 | 659.6 | 659.6 | 566.1 | 549.4 | 562.5 | 659.2 | 656.6 |
| S3c reversal_persistent_1200 | neighbouring_negative_control | 1200 | 60 | balanced | 785.3 | 758.0 | 891.2 | 891.0 | 891.0 | 273.5 | 655.5 | 252.2 | 450.4 | 888.0 |
| S4a hazard_shift_k25 | alternative | 1000 | 50 | balanced | 650.6 | 637.5 | 452.4 | 452.2 | 452.2 | 510.5 | 470.4 | 522.0 | 452.2 | 449.8 |
| S4b hazard_null_k25 | correct_null | 1000 | 50 | balanced | 666.7 | 637.5 | 551.6 | 551.4 | 551.4 | 484.4 | 457.7 | 474.1 | 551.4 | 548.9 |
| S4c hazard_shift_k10 | neighbouring_negative_control | 1000 | 50 | balanced | 634.9 | 635.7 | 449.6 | 449.4 | 449.4 | 467.5 | 446.1 | 485.6 | 446.9 | 446.9 |

**paired dJ** = J(host)-J(control) [95% CI], positive = host worse

| cell | host | uniform_query | episode_front | pending_cap |
|---|---|---|---|---|
| S1a | d2a_cal | +129.5 [+110.9,+146.8] | +12.5 [+6.7,+20.1] | +57.2 [+33.3,+84.0] |
| S1a | rar_cal | +123.6 [+103.5,+142.2] | +6.5 [+0.1,+13.9] | +51.2 [+26.8,+79.2] |
| S1a | cab_cal | +123.5 [+103.3,+142.1] | +6.5 [+0.0,+13.8] | +51.1 [+26.8,+79.0] |
| S1b | d2a_cal | +72.9 [+67.9,+77.7] | +50.8 [+45.1,+56.2] | +74.0 [+68.6,+79.3] |
| S1b | rar_cal | +22.2 [+15.1,+29.4] | +0.1 [+0.0,+0.1] | +23.3 [+18.5,+28.0] |
| S1b | cab_cal | +22.1 [+15.1,+29.3] | +0.0 [+0.0,+0.0] | +23.3 [+18.5,+28.0] |
| S1c | d2a_cal | +81.3 [+76.1,+85.8] | +59.5 [+54.3,+65.2] | +85.8 [+80.2,+91.0] |
| S1c | rar_cal | +22.3 [+13.0,+31.1] | +0.5 [+0.5,+0.6] | +26.8 [+15.8,+36.9] |
| S1c | cab_cal | +21.8 [+12.5,+30.6] | +0.0 [+0.0,+0.0] | +26.2 [+15.2,+36.4] |
| S2a | d2a_cal | +545.9 [+532.6,+559.7] | +573.4 [+520.3,+609.5] | +545.9 [+532.6,+559.7] |
| S2a | rar_cal | +173.4 [+152.1,+194.7] | +200.8 [+153.6,+229.5] | +173.4 [+152.1,+194.7] |
| S2a | cab_cal | +334.3 [+317.1,+353.3] | +361.8 [+315.5,+389.0] | +334.3 [+317.1,+353.3] |
| S2b | d2a_cal | +476.1 [+457.3,+490.6] | +379.8 [+356.7,+397.2] | +476.1 [+457.3,+490.6] |
| S2b | rar_cal | +96.3 [+84.6,+107.0] | -0.0 [-5.2,+3.6] | +96.3 [+84.6,+107.0] |
| S2b | cab_cal | +93.3 [+81.5,+104.0] | -3.0 [-8.2,+0.5] | +93.3 [+81.5,+104.0] |
| S2c | d2a_cal | +469.0 [+448.2,+483.7] | +386.8 [+364.8,+402.4] | +469.0 [+448.2,+483.7] |
| S2c | rar_cal | +86.0 [+74.7,+96.0] | +3.8 [+3.6,+3.9] | +86.0 [+74.7,+96.0] |
| S2c | cab_cal | +82.7 [+71.5,+92.7] | +0.5 [+0.5,+0.5] | +82.7 [+71.5,+92.7] |
| S2d | d2a_cal | +402.2 [+383.0,+419.7] | +350.4 [+312.2,+373.8] | +267.1 [+209.2,+320.1] |
| S2d | rar_cal | +378.9 [+359.7,+395.5] | +327.1 [+286.4,+353.2] | +243.8 [+181.1,+301.4] |
| S2d | cab_cal | +297.2 [+274.8,+317.8] | +245.4 [+204.7,+277.1] | +162.2 [+95.2,+225.9] |
| S2e | d2a_cal | -1.7 [-30.6,+26.9] | +333.1 [+322.2,+343.2] | -43.5 [-63.7,-23.4] |
| S2e | rar_cal | -346.0 [-374.2,-316.0] | -11.1 [-11.2,-11.1] | -387.7 [-405.9,-370.0] |
| S2e | cab_cal | -347.3 [-375.5,-317.4] | -12.5 [-12.5,-12.5] | -389.1 [-407.2,-371.4] |
| S2f | d2a_cal | +53.5 [+8.5,+105.1] | +339.1 [+327.7,+349.1] | -20.2 [-37.2,-2.6] |
| S2f | rar_cal | -296.7 [-340.5,-245.6] | -11.1 [-11.1,-11.0] | -370.4 [-384.3,-355.6] |
| S2f | cab_cal | -298.1 [-341.9,-247.0] | -12.5 [-12.5,-12.5] | -371.9 [-385.8,-357.0] |
| S3a | d2a_cal | +197.2 [+177.4,+217.0] | +194.0 [+180.2,+208.4] | +176.1 [+166.9,+184.4] |
| S3a | rar_cal | +13.8 [-8.6,+35.6] | +10.7 [-2.0,+23.5] | -7.2 [-15.8,-0.5] |
| S3a | cab_cal | +13.8 [-8.6,+35.6] | +10.7 [-2.0,+23.5] | -7.2 [-15.8,-0.5] |
| S3b | d2a_cal | +191.9 [+180.7,+203.8] | +98.7 [+91.0,+106.9] | +208.6 [+200.2,+216.9] |
| S3b | rar_cal | +93.5 [+75.9,+111.4] | +0.3 [+0.0,+1.1] | +110.2 [+93.9,+125.9] |
| S3b | cab_cal | +93.5 [+75.9,+111.4] | +0.3 [+0.0,+1.1] | +110.2 [+93.9,+125.9] |
| S3c | d2a_cal | +484.5 [+464.9,+503.1] | +307.6 [+270.0,+338.9] | +102.5 [-18.9,+227.1] |
| S3c | rar_cal | +617.5 [+589.1,+644.4] | +440.6 [+402.5,+474.9] | +235.5 [+110.7,+363.7] |
| S3c | cab_cal | +617.5 [+589.1,+644.4] | +440.6 [+402.5,+474.9] | +235.5 [+110.7,+363.7] |
| S4a | d2a_cal | +127.0 [+101.4,+156.2] | +185.2 [+168.5,+200.6] | +167.1 [+144.7,+187.9] |
| S4a | rar_cal | -58.3 [-91.7,-20.3] | +0.0 [+0.0,+0.0] | -18.1 [-42.5,+2.6] |
| S4a | cab_cal | -58.3 [-91.7,-20.3] | +0.0 [+0.0,+0.0] | -18.1 [-42.5,+2.6] |
| S4b | d2a_cal | +153.1 [+143.5,+162.0] | +86.1 [+78.4,+93.7] | +179.8 [+173.1,+187.0] |
| S4b | rar_cal | +67.0 [+55.5,+79.6] | +0.0 [+0.0,+0.0] | +93.7 [+79.3,+108.5] |
| S4b | cab_cal | +67.0 [+55.5,+79.6] | +0.0 [+0.0,+0.0] | +93.7 [+79.3,+108.5] |
| S4c | d2a_cal | +168.3 [+116.6,+222.2] | +188.8 [+142.3,+231.5] | +189.6 [+143.3,+233.0] |
| S4c | rar_cal | -18.0 [-82.8,+52.4] | +2.5 [-5.8,+12.8] | +3.4 [-58.7,+66.6] |
| S4c | cab_cal | -18.0 [-82.8,+52.4] | +2.5 [-5.8,+12.8] | +3.4 [-58.7,+66.6] |


### 5.2 Hook-reach evidence (host-only; counters are means over 20 seeds)

`labels released after T` = requested labels whose release round exceeds the horizon (never usable); `q_rounds p_within<x` = query rounds at which the host's OWN observed delay law gives
P(delay <= remaining horizon) < x (the predicate a feasibility/deadline hook evaluates; measured on the host run, no candidate rule is applied); `gate evals/gate2/gate3/flags/retrains` are RAR/CAB
policy-log events; `cert evals/gate-open rounds` are Drift2Act log rows with n_cert>0 / gate_ok; `promoted-then-regime-left` and `cand rounds when cand worse` are evaluator-side facts measured on the
promotion control `uniform_query` (the rollback/hazard headroom).

| cell | method | q_rounds p_within<1 | p_within<0.5 | labels released after T / requested | max pending | gate evals | gate2 pass | gate3 pass | flags | retrains issued | cert evals | gate-open rounds | regime switches | promoted-then-regime-left (frac seeds) | cand rounds when cand worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1a | d2a_cal | 20.3 | 7.8 | 14.4 / 50 | 15.9 | - | - | - | - | - | 344.3 | 0.0 | 1.0 | 0.00 | 0.0 |
| S1a | rar_cal | 20.3 | 7.8 | 14.4 / 50 | 15.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 1.0 | 0.00 | 0.0 |
| S1a | cab_cal | 20.3 | 7.8 | 14.4 / 50 | 15.9 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 1.0 | 0.00 | 0.0 |
| S1a | uniform_query | 18.6 | 5.0 | 12.5 / 47 | 18.1 | - | - | - | - | - | - | - | 1.0 | 0.15 | 5.2 |
| S1b | d2a_cal | 19.2 | 7.5 | 14.9 / 50 | 16.1 | - | - | - | - | - | 347.5 | 0.0 | 2.0 | 0.00 | 0.0 |
| S1b | rar_cal | 19.2 | 7.5 | 14.9 / 50 | 16.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S1b | cab_cal | 19.2 | 7.5 | 14.9 / 50 | 16.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S1b | uniform_query | 17.9 | 6.2 | 13.8 / 48 | 17.6 | - | - | - | - | - | - | - | 2.0 | 0.95 | 0.0 |
| S1c | d2a_cal | 2.0 | 2.0 | 2.0 / 50 | 2.0 | - | - | - | - | - | 382.0 | 0.0 | 2.0 | 0.00 | 0.0 |
| S1c | rar_cal | 2.0 | 2.0 | 2.0 / 50 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S1c | cab_cal | 2.0 | 2.0 | 2.0 / 50 | 2.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S1c | uniform_query | 0.5 | 0.5 | 0.5 / 48 | 4.3 | - | - | - | - | - | - | - | 2.0 | 1.00 | 0.0 |
| S2a | d2a_cal | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | - | - | - | - | - | 989.0 | 322.9 | 2.0 | 0.00 | 0.0 |
| S2a | rar_cal | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2a | cab_cal | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | 0.0 | 0.0 | 0.0 | 1.8 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2a | uniform_query | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | - | - | - | - | - | - | - | 2.0 | 1.00 | 269.8 |
| S2b | d2a_cal | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | - | - | - | - | - | 980.5 | 73.0 | 2.0 | 0.00 | 0.0 |
| S2b | rar_cal | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2b | cab_cal | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2b | uniform_query | 10.0 | 10.0 | 10.0 / 1000 | 9.0 | - | - | - | - | - | - | - | 2.0 | 1.00 | 0.0 |
| S2c | d2a_cal | 279.9 | 15.2 | 24.7 / 1000 | 33.5 | - | - | - | - | - | 983.9 | 105.2 | 2.0 | 0.00 | 0.0 |
| S2c | rar_cal | 279.9 | 15.2 | 24.7 / 1000 | 33.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2c | cab_cal | 279.9 | 15.2 | 24.7 / 1000 | 33.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2c | uniform_query | 279.9 | 15.2 | 24.7 / 1000 | 33.5 | - | - | - | - | - | - | - | 2.0 | 1.00 | 0.0 |
| S2d | d2a_cal | 3.0 | 3.0 | 3.0 / 250 | 3.0 | - | - | - | - | - | 986.0 | 32.0 | 2.0 | 0.00 | 0.0 |
| S2d | rar_cal | 3.0 | 3.0 | 3.0 / 250 | 3.0 | 111.0 | 0.0 | 0.0 | 1.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2d | cab_cal | 3.0 | 3.0 | 3.0 / 250 | 3.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.9 | - | - | 2.0 | 0.00 | 0.0 |
| S2d | uniform_query | 1.7 | 1.7 | 1.7 / 295 | 7.2 | - | - | - | - | - | - | - | 2.0 | 1.00 | 137.8 |
| S2e | d2a_cal | 3.0 | 3.0 | 3.0 / 250 | 3.0 | - | - | - | - | - | 984.0 | 242.4 | 2.0 | 0.00 | 0.0 |
| S2e | rar_cal | 3.0 | 3.0 | 3.0 / 250 | 3.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2e | cab_cal | 3.0 | 3.0 | 3.0 / 250 | 3.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2e | uniform_query | 1.9 | 1.9 | 1.9 / 294 | 7.1 | - | - | - | - | - | - | - | 2.0 | 1.00 | 831.4 |
| S2f | d2a_cal | 51.1 | 4.1 | 7.3 / 250 | 10.8 | - | - | - | - | - | 983.3 | 263.8 | 2.0 | 0.00 | 0.0 |
| S2f | rar_cal | 51.1 | 4.1 | 7.3 / 250 | 10.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2f | cab_cal | 51.1 | 4.1 | 7.3 / 250 | 10.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S2f | uniform_query | 63.5 | 3.0 | 6.5 / 295 | 13.9 | - | - | - | - | - | - | - | 2.0 | 0.95 | 729.9 |
| S3a | d2a_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | - | - | - | - | - | 1170.0 | 0.0 | 2.0 | 0.00 | 0.0 |
| S3a | rar_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S3a | cab_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S3a | uniform_query | 0.3 | 0.3 | 0.3 / 57 | 3.2 | - | - | - | - | - | - | - | 2.0 | 1.00 | 503.4 |
| S3b | d2a_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | - | - | - | - | - | 1170.0 | 0.0 | 2.0 | 0.00 | 0.0 |
| S3b | rar_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S3b | cab_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 2.0 | 0.00 | 0.0 |
| S3b | uniform_query | 0.1 | 0.1 | 0.1 / 58 | 3.2 | - | - | - | - | - | - | - | 2.0 | 1.00 | 0.0 |
| S3c | d2a_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | - | - | - | - | - | 1170.0 | 0.0 | 1.0 | 0.00 | 0.0 |
| S3c | rar_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 1.0 | 0.00 | 0.0 |
| S3c | cab_cal | 1.0 | 1.0 | 1.0 / 60 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 1.0 | 0.00 | 0.0 |
| S3c | uniform_query | 0.3 | 0.3 | 0.3 / 56 | 3.0 | - | - | - | - | - | - | - | 1.0 | 0.20 | 44.0 |
| S4a | d2a_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | - | - | - | - | - | 961.2 | 0.0 | 5.2 | 0.00 | 0.0 |
| S4a | rar_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 5.2 | 0.00 | 0.0 |
| S4a | cab_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 5.2 | 0.00 | 0.0 |
| S4a | uniform_query | 0.2 | 0.2 | 0.2 / 47 | 3.2 | - | - | - | - | - | - | - | 5.2 | 0.95 | 473.2 |
| S4b | d2a_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | - | - | - | - | - | 964.6 | 0.0 | 5.3 | 0.00 | 0.0 |
| S4b | rar_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 5.3 | 0.00 | 0.0 |
| S4b | cab_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 5.3 | 0.00 | 0.0 |
| S4b | uniform_query | 0.2 | 0.2 | 0.2 / 46 | 3.2 | - | - | - | - | - | - | - | 5.3 | 1.00 | 0.0 |
| S4c | d2a_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | - | - | - | - | - | 968.1 | 0.0 | 4.9 | 0.00 | 0.0 |
| S4c | rar_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 4.9 | 0.00 | 0.0 |
| S4c | cab_cal | 1.0 | 1.0 | 1.0 / 50 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | - | - | 4.9 | 0.00 | 0.0 |
| S4c | uniform_query | 0.2 | 0.2 | 0.2 / 48 | 3.2 | - | - | - | - | - | - | - | 4.9 | 0.85 | 396.4 |


Reading (all numbers from the tables above):
* **S1 deadline/feasibility**: on S1a 20.3 of 50 query rounds (7.8 with P<0.5) happen while the host's observed delay law puts mass beyond the horizon, and 14.4 of 50 labels (29% of the budget) are released after T; on the
  neighbouring short-tail cell S1c it is 2.0 / 50 (4%). On the frozen suite (T=1000, short delays) these counts are near zero, which is why those hooks were inert.
* **S2 RAR Gate 2**: at cap = T the gate is evaluated and passed once per seed (retrain issued); on the frozen cap-50 cells there are 0 gate evaluations in 160 runs. At cap 300 (S2d) the gate is evaluated 111 times per seed and never
  passes (labelled-in-window below 70), i.e. the hook is exercised as the binding gate (A1 alert path). RAR J=529 vs never-switch 640 on S2a, so the RAR host does work when it can.
* **S2 Drift2Act certificate**: gate open on 323 (S2a), 32 (S2d), 242 / 264 (S2e / S2f) rounds per seed versus 0 on every calibrated frozen run.
* **S3 reversal**: the promotion control promotes and then sees the regime leave in 100% of seeds on S3a and spends 503 candidate-rounds when the candidate is worse; on the persistent twin S3c 20% of seeds / 44 rounds.
* **S4 hazard**: 5.2 regime switches per stream; the promotion control promotes then outlives the regime in 95% of seeds with 473 worse-candidate rounds (S4c flat-hazard control: 4.9 switches, 85%, 396 rounds, i.e. the cell pair
  isolates the hazard SHAPE, not the existence of switches; a hazard mechanism must be judged on S4a vs S4c, not on switches alone).
* Headroom check (not a candidate result): never-switch beats the promotion controls on S2e (299.6 vs 709.4), S2f, S4a (449.8 vs 510.5): the naive `GainSwitchRule` (mean of last 10 gains > h) false-promotes in clean-null
  cells once the cap is large (many windows), so there the controls are weak; candidate comparisons on v2 must include never-switch.
* On v2 the calibrated RAR beats uniform_query on S2e/S2f (-346 / -297) and S4a (-58.3 [-91.7,-20.3]) only because the control false-promotes; RAR/CAB still lose on alternative cells with a free better candidate
  (S1a, S2a, S2d). Drift2Act is worse than uniform_query with CI excluding 0 on 14/15 cells and ties on S2e (-1.7 [-30.6,+26.9]). These are descriptive, not tuned, and not Stage-B evidence.

## 6. Open issues and what was NOT done

* No Stage-B candidate rerun and no ledger append (as instructed). The Stage-B reference cache (`results/d2a_rar/stage_b/cache`) is keyed by a code hash over `src/shiftlab/bench/contract`, which this audit changed
  (`adapters_drift2act.py`, `adapters_rar.py`, `streams.py`); it will recompute on next use. native_v0 defaults are asserted bit-identical (8 golden J/count pairs from cc867f40 in the test); I did not diff the full cache.
* `stage_b.py` (and `stage_b_variants.FeedDrift2Act/FeedRAR/GatedBinary`) still build native_v0 hosts. To use calibrated_v1 in Stage B pass `profile="calibrated_v1"` (the Feed* classes forward **kw);
  to run v2 cells Stage B needs per-cell T / label_cap / cost-vector support (it reads DEV_SUITE only). Neither was done; `host_audit.run_v2` is the host-only runner.
* The decisive finding is a benchmark-design one: B/T=5% makes both papers' statistical thresholds unreachable, so DEV_SUITE v1 cannot differentiate host-hook candidates from the host; v2 can. A WP6 decision is needed on whether
  v2 becomes the primary Stage-B suite (preregister before use) or an auxiliary suite.
* The Drift2Act port still lacks a native hand-off state (abstain charged per round) and uses proxy sensing / hand-set evidence; documented (D) deviations, untouched.
* `max_lookback=0` everywhere (frozen clock): Drift2Act's windowed uniform audit is degenerate in all cells. A lookback>0 sensitivity run was NOT done.
* The naive controls false-promote on large-cap null cells (S2e/f); a stronger control (e.g. a cond-null certified promoter) is needed before reading control-vs-candidate gaps on v2.
* S2a-c use `intervention_dear` for every method (RAR convention), which penalises Drift2Act's per-round c_h=0.2; do not read Drift2Act-vs-control gaps on S2a-c as a host-port statement.
* The first calibrated run (C1-C3) is the one reported; no hyper-parameter of calibrated_v1 was revisited after any result.

## 7. Verification

* `pytest tests/d2a_rar -q`: **228 passed** (158 s; includes the 17 new tests in `tests/d2a_rar/test_host_calibration.py`, 11 s). New tests: native_v0 bit-identical to cc867f40 (8 golden J + count pairs), calibrated_v1 passes
  verify_run and is paced (cap spread, audit cadence 20, N=683, cooldowns 533/267), ReachProbe does not change behaviour, v2 files deterministic/frozen files untouched, all 15 v2 cells pass the contract guards with
  uniform_query + d2a_cal + rar_cal + cab_cal, semi-Markov stream, and hook-reach counters > 0 on the new cells (and == 0 for RAR Gate 2 on the frozen cap-50 cell).
* `ruff check` and `ruff format --check` clean on all touched files. Nothing committed; `EXPERIMENT_LEDGER.jsonl` and `DEV_SUITE.json` untouched.
