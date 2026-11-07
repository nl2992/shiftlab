# Elexon F8 profile screen — development only

**Profile gate: FAIL.** This is a 2024-train / 2025-development profile screen; it is not a policy-cost experiment or independent confirmation.

Contains BMRS data © Elexon Limited copyright and database right 2026. Source: [Elexon BMRS](https://bmrs.elexon.co.uk/). [Data licence](https://www.elexon.co.uk/bsc/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/).

| Half-year | Eligible events | Disagreement | Challenger accuracy on disagreement | 2,000-event blocks | Profile gate |
|---|---:|---:|---:|---:|---|
| 2025_H1 | 7714 | 17.021% | 52.856% | 3 | FAIL |
| 2025_H2 | 8073 | 8.745% | 48.725% | 4 | FAIL |

Records read: ATL 36,591; DATL 36,624. Publication-window receipts and response SHA-256 values are in `DATASET_PROFILE.json`; quantity values and row-level outcomes remain in ignored `data/raw/`. The request boundary ended at 2025-12-30 00:00 UTC, and the program rejects any response containing a 2026 valid time.

Duplicate valid times with multiple publications/documents: ATL 204; DATL 1248. Vintage selection uses the latest publication available at issue time; labels use first publication.

**Interpretation:** the method here is the standard validation-selected fixed-challenger rule. A passing profile would show that Elexon 2025 contains an F8-like model-pair stream, not that a new algorithm transfers or that deploying the challenger is economically beneficial. Keep the 2026 period closed unless a separately frozen case-study decision permits it; one operator remains one source cluster.


## Reproduction and execution history

Reproduction command: `uv run python research/scoped_method/pilots/elexon_f8_profile_20261107/profile_f8.py`. The successful run used runner commit `99a74a106532386b1da1d65bb72ca66a38a14b97` (SHA-256 `1b35c02c42c6a5c638d98ca90dbb5b14841c95e7448e7ba183fe4c1371e8b893`), protocol SHA-256 `6b387173533f1d5d367fd60f5f4806af855fc23cf0732f521227b31b33f54302`, and `uv.lock` SHA-256 `a50f921c44e4f37d0e746f9a2680c8ec823d21a1f6a8901406620e1ca55c44fd` with Python 3.12.15, NumPy 2.5.4, and scikit-learn 1.9.1. The 50 monthly ATL/DATL response hashes are in `DATASET_PROFILE.json`; raw quantities remain in ignored `data/raw/`.

Two earlier attempts halted before any model fit: the first used target-relative lags, which were unavailable at the 12-hour-ahead issue time; the second encountered a missing ATL target label. Both failures and the pre-rerun corrections are recorded in the protocol. The successful run excludes/counts missing labels and uses lags relative to the freshest mature actual.
