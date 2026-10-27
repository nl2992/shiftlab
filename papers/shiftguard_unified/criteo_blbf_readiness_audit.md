# Criteo Banner Filling Challenge readiness audit

**Audit date:** 2026-10-26  
**Status:** public structural sample acquired and parsed; full archive not acquired; no policy evaluation performed.

## Source and evidence

Cornell's public test-bed page describes a Criteo display-ad banner dataset with more than 103 million impressions. Each impression contains hashed visitor information, display/context features, candidate product features, the displayed banner's logged propensity, and click outcomes. Banner size ranges from one to six slots, with multiple candidates per impression. The source states that example IDs increase with time and that only a random 10% of non-click impressions are retained; its published scoring code applies a subsampling correction. The source archive is approximately 35 GB compressed and 250 GB uncompressed. The page calls the data public and requests citation but does not state a standard redistribution license.

The local `sample.txt` is the publisher-linked ~1 MB sample, SHA-256 `8b3e2fde7a39a1b9f5b81c0c2d44d9caff2038efa2a830c1a2edf953e7b524fa` (recorded in the aggregate manifest). The streaming structural audit parsed 412 impressions and all 9,574 candidate rows; every candidate block matched its impression ID, propensity values were finite and in `(0,1]`, and there were no invalid-value flags. Slot counts ranged from one to six. The sample's example IDs had 204 order inversions, consistent with the publisher describing it as a small sample rather than an ordered stream. Its observed propensity range was `7.97e-10` to `0.9996`, warning that some logged policies can create extreme importance weights. The manifest contains aggregate counts only; no IDs, hashed visitor identifiers, or feature values are published.

The publisher's helper archive was downloaded for source inspection but not executed (ZIP SHA-256 `b11d1e4e25a8e3e02cebb113fb7700eb9a560be6ca89a41fb17d363a2e6ab793`; `parser.py` SHA-256 `5ab39ec551d87754b7447a1a248d6045817e0ff9d11bfe842e191a25a3a6bed5`; `scorer.py` SHA-256 `76ab2bbed3989eb9a06717bec50fa7a3b65ca5c6c6ac1031566fd287d4e80c32`). The parser adjusts negative-outcome propensities by the documented 0.1 retention probability and estimates the original denominator as clicks plus ten times the sampled non-clicks. It emits the official learning split only for one-slot banners; the script assigns train/validation/test round-robin through file order, so a temporal study must define a separate chronological split and verify the full file's ordering. The inspected scorer reports batch IPS/SNIPS summaries, not a time-uniform guarantee.

Runner: `scripts/audit_criteo_blbf_sample.py`. Aggregate manifest: `data/reports/criteo_blbf_sample_manifest.json`, including optional hashes for the inspected helper archive. The sample and downloaded helper ZIP are stored under ignored `data/raw/` and must not be committed or redistributed.

## Research fit and limitations

This source is a stronger candidate than the currently acquired OBD archive for a separate **offline logged-policy learning and evaluation** task: it supplies action-dependent rewards and banner-level behavior propensities, and its full impression IDs encode temporal order. It may support a future time-ordered candidate-training and OPE development study if the full source can be obtained and the original subsampling correction and banner/slate estimand are implemented faithfully.

It does not currently satisfy a ShiftLab real-data confirmation gate. Only the 412-impression sample is locally present; it is not chronological and cannot support training, certification, or uncertainty estimates. The outcome-dependent omission of 90% of non-click impressions must be accounted for in every estimator and any sequential feedback contract. The very small observed propensity minimum signals severe overlap risk, but the sample is too small and not representative enough to infer full-archive support. The page documents event order, not wall-clock feature availability or click-release times, so this is not verified real-time monitoring. Logged click value is not revenue or net business utility, and full-slate interactions need to be handled according to the source paper's banner-level action.

The current C: volume had approximately 546 MB free at the audit, far below the source's 35 GB compressed size. Do not attempt the full archive on this volume. Before acquisition, identify storage with adequate headroom or a stream-processing location and verify current source transfer/checksum, license/attribution terms, and original correction code. A bounded fixed-horizon OPE protocol should be prototyped on the sample first, with no efficacy claim, then frozen before using a full archive or temporal holdout.

## Decision

**GO for a bounded feasibility prototype; NO-GO for full real-data evaluation or confirmation with the sample.** The next evidence gate is to verify the official source's archive contents, temporal ordering, banner propensity semantics, and outcome-subsampling correction on an adequately stored full archive. If access/storage cannot be arranged, retain the existing OBD development analysis and state that the real-data Q2 confirmation condition is unmet.

## Sources

- [Cornell Criteo counterfactual-learning test-bed and data description](https://www.cs.cornell.edu/~adith/Criteo/)
- [Lefortier et al., *Large-scale Validation of Counterfactual Learning Methods: A Test-Bed*](https://arxiv.org/abs/1612.00367)
