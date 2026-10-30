# 07 Matched baseline verification
Code commit at start: `8552911`; sprint branch `research/shiftlab-dependence-gates-2026-10-31`. Inputs: docs 01, 04. 
* Repaired e-process engine: legacy parity (max |dlogW| 4.8e-7), hard-budget, causality and identity tests — **verified** (30 tests pass).
* PH / CUSUM: local implementations, thresholds from independent null streams — verified as local baselines; **no guarantee**.
* "CAMS-style", "SeqMCS", "Balanced AI", "PAI": local source-inspired — **not verified reproductions** (unchanged).
* Sethi et al. (2026) test: **not reproduced**. Reason: its observation model (fully observed finite-state chain, null = a set of transition matrices) applies to the *Gate-B lazy chain* but not to the hidden-regime, selectively-labelled streams of the programme; a faithful reproduction requires their Algorithm 1 plus a convex solver over the null set and was out of the bounded scope. Obligation: reproduce Algorithm 1 on the binary lazy chain and compare its stopping times with the oracle ceiling in 03 (prediction: it cannot beat the ceiling).
* Podkopaev-Ramdas / PPRM: closest ancestors of the local PPRM-style parent; assumptions verified (independence across time).
**Status: PARTIAL; no equally equipped published comparator exists for the switching problem.**
