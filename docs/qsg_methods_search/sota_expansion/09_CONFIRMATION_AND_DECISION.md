# 09 — Independent confirmation plan and continue/pivot/stop

Written 2026-11-08, after 04–08. **No confirmation run has started. Nothing here is a result.**

## 1. Why confirmation is still needed

- Every nine-dataset comparison in 05 is **retrospective**: the nine were opened before these
  comparators were run (03 §1).
- The synthetic panel (04) uses fresh seeds, but the C3 family was used for development.
- So the only pre-registered real-data evidence is still the C4 claim against tuned Gong–Zhang-style
  (`c4_results.md`, 9/16 supporting, −0.75%). The wider adapter claim in 08 has no confirmatory
  evidence yet.

## 2. Proposed confirmatory design (to lock before any data is opened)

**Data.** Fresh streams only:
- not one of the nine (batch 1), the seven (batch 2), or the 14 development streams;
- built by the existing `c4_build.py` contract (same T, B, c_q, c_s, delay rule), with source
  provenance and checksums recorded before any policy runs;
- candidates are additional public municipal 311 sources not yet in a registration. The OPSD 2020
  holdout is locked for the lane-B programme and must not be used here (`real_data_inventory.md`).

**Arms** (frozen, no changes after locking):
- primary: arm B `EQSDp_l0.9_g0.2` (frozen since `10ba0237`);
- secondary, declared in advance: an EQSDp configuration selected only on the 14 development
  streams by the 03 §4 rule. 05 shows real streams prefer λ = .97; this arm tests the class claim
  without touching the confirmation data.

**Primary contrasts** (small family, to keep power): arm B vs
1. Qiu-style (`qiu_delayed_movement`);
2. tuned Gong–Zhang-style, both SD (`gongT_w100_m10`) and RD (`gongT_w800_m20`);
3. UPF-style SD (`upf_d0.95_m50`);
4. Challenger-style nominal (`chalgse_l1.0_g0.2`);
5. CAMS adapter (`cams_adapter`).

Holm over these six. Wald λ.97, scaled margin λ.97 and econF are reported as **expected ties or
losses**, not tested for a win.

**Verdict rule.** As 03 §6 (Holm p < .05 and ≥ 6/9-equivalent sign majority), plus the dataset-level
t-test registered as co-primary rather than as a robustness column. On nine datasets, only the
Qiu-style contrast survives dataset-level Holm, so the plan needs ≥ 9 fresh datasets to have a
realistic chance for the 0.8–1.8% effects. A power estimate from the 05 between-dataset variance
must be computed and written into the registration before locking.

**Guarantee reporting.** Certified methods are reported as cost Δ under a different guarantee
class, never as wins (08 disclosure 4).

## 3. Continue / pivot / stop

**Assessment: CONTINUE, with a narrowed claim. Do not expand the method search.**

- **Continue** the write-up as framed in 08: a matched-contract benchmark of 18 families plus a
  reversible confidence-bound payback rule as the class representative (Beta ≡ Wald).
  - Supported: synthetic wins against every adapter (meaningful against UPF-style and the selection
    adapters); real-data wins against Qiu-style (9/9, dataset-level Holm .024) and synthetic-tuned
    Gong–Zhang-style (9/9); the confidence-bound ablation (−25 real, −51 synthetic).
- **Do not claim**:
  - that arm B beats its strongest controls on real data. Real-tuned Wald and scaled margin beat
    it by about 0.5% on 8–9/9 datasets, and real-tuned Gong–Zhang-style and econF tie;
  - any false-promotion guarantee (71% false promotion on real episodes where the challenger is not
    better);
  - wins against native published methods. Every comparator is a class B/C adapter, and
    `vendor_sota/` is empty.
- **Pivot trigger.** If the fresh-data confirmation in §2 does not reproduce the Qiu-style and
  Gong–Zhang-style wins, drop the method claim and publish the benchmark and the three-mechanism
  analysis (07) alone.
- **Stop trigger.** None reached. The remaining risks are prior-art overlap (Challenger GSE;
  Regol UPF), which 08 already scopes as NOVEL-INTEGRATION, and small real-data effect sizes.

## 4. Open items

- [x] Choose and audit fresh streams; record provenance and checksums. (Done: 10 eligible, `c4_build_audit.md` batch-F section, `c4_registration_batchF.json`.)
- [x] Select the secondary EQSDp configuration on the 14 development streams only. (Done: arm R λ.98 γ.3, `batchF_armR_selection.md`.)
- [x] Compute power from the 05 variance; write and commit the registration before opening data. (Done: 10 §4; registration 00d00084 at 15:51:09, run started 15:51:29; results in 12.)
- [ ] **OPEN (2026-11-08 audit):** `vendor_sota/` still holds only `.gitignore`. Obtain author code for at least one comparator (Gong–Zhang or Qiu) and run parity tests, to
  lift a fidelity class to A.
- [ ] **OPEN (2026-11-08 audit):** not run yet; should now cover 08 and 12. Run `paper-claim-audit` on 08 against `nine_analysis.txt` and `synth_analysis.txt` before
  any manuscript text is drafted.
