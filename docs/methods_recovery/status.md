# Gap-Mix+ status log (methods-recovery, branch research/methods-recovery-2026-11-07)

- [x] Step 1a: src/shiftlab/gaver/gapmix_plus.py written (governor, 4a via mode=frozen, Arm 5 via mode=pace, QSG-envelope evidence port). Smoke test pending.
- [ ] Step 1b: runner scripts/methods_recovery/run_gmplus.py
- [ ] Step 2: tests/gaver/test_gapmix_plus.py + ruff
- [ ] Step 3: seed registry
- [ ] Step 4: tuning -> configs/methods_recovery/gapmix_plus_frozen.json, 10_TUNING.md
- [ ] Step 5: eval (detached)
- [ ] Step 6: 20_GAPMIX_PLUS_RESULTS.md

- 2026-11-07T22:29:10 steps 1-3 done (module, tests 8 passed + ruff clean, seeds registered 101300000-309999 tuning, 101400000-429999 eval). Tuning launched detached: outputs/methods_recovery/tune/rows.csv (resumable: rerun same command: run_gmplus.py --stage tune --workers 10). Arm4 grid shifted to kappa{1,2,4} x phi{1,1.5,2.5} x omega{0,.5,1} after an 8-cell/1-seed smoke on tuning seeds (kappa=2,phi=1.5 at old grid edge); 27 configs. Arm5 32 configs.
- 22:33:35 analysis scripts written: scripts/methods_recovery/{tune_select,analyse_gmplus}.py. Tuning ~110 min est (23040 runs).
- 23:38:01 tuning DONE; frozen config + sha256 written (configs/methods_recovery/gapmix_plus_frozen.json), 10_TUNING.md written. Launching eval: alt then null, detached (outputs/methods_recovery/eval.log). Resume: rerun run_gmplus.py --stage alt / --stage null --workers 10.

## 2026-11-07 23:45 (Opus coordinator)
- Verified: frozen config sha256 1010a0f9… written 23:37:51, first eval row 23:38:05 (freeze precedes eval). 15 tests pass. Committed 9edca5e1.
- Eval running detached (parent shell gone): alt stage about 80 min, then null stage about 2 h. The agent was stopped; the run is unaffected.
- NEXT: when both stages print "done" in outputs/methods_recovery/*/eval.log, run `scripts/methods_recovery/analyse_gmplus.py`. Opus then checks that the C3 numbers do NOT use the per-cell-table fallback (Arm 3 -> Arm 2 values when PAVE rows are absent; it applies outside the delay gate, where delay-gated PAVE = shell rule). Recompute criteria 1-5 and commit the verdict.
- Watch: tuning gain for Arm 4 over Arm 2 was only 0.75% (0.4386 vs 0.4419), against a >=3% C3 bar. kappa=4 sits on the grid edge; omega=0 means the pending-label term is unused.

## 2026-11-08 (Opus coordinator): Gap-Mix+ C3 development verdict = FAIL
- The alt stage had crashed on missing neighbour-family Arm-5 configs. Amendment A1 (`b74a1fc3`)
  tuned them on tuning seeds; they were frozen at `17dd261b`, and the alt stage was then resumed
  to completion (112 cells × 60 seeds × 11 arms).
- Registered analysis (`20_GAPMIX_PLUS_RESULTS.md`):
  - Arm 4 is **3.97% worse** [3.27, 4.66] than the strongest valid comparator (C1 fails);
  - C3 fails (no gain over Arm 3 in the gate-on subset);
  - neighbours fail, with up to 12.7% loss at B/T=.5;
  - attribution (C2: +1.19% vs evidence-frozen) and validity (C4: worst UCB .060) pass.
- Gap-10 thinning (valid) is 2.6% cheaper than Gap-Mix+. Per prereg §5 the next step would be
  PAVE-Delay+, but its bounded feasibility (`40_PAVE_PLUS_FEASIBILITY.md`) also stops: PAVE ties
  `episode_front`.
