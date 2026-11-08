# Next-method plan (continuation directive of 2026-11-07)

Start state: branch `research/qsg-methods-search-2026-11-07` at `6ce1a3f7`. Historical results
(C3 PASS `10ba0237`, comparator panel PARTIAL `5bc1b3e2`, C4-0 pilot GO `e281400c`) stand as
recorded and are not re-run or rewritten.

## Problem the next method must solve

The comparator panel showed EQSDp-B ≡ tuned fixed-discount Wald-LCB (Δ −0.05 [−0.28, +0.19]).
The C2 contribution is therefore "an uncertainty-scaled payback hurdle", which is established
practice. The next method must show an attributable gain **over tuned fixed-discount Wald-LCB
switching** on the same contract (T=2000, B=200, c_q=.05, c_s=5, per-regime delay, paced
disagreement-only acquisition).

Diagnosis from the recorded panel: every tuned family chose λ=.9 (short memory, n_eff≈10). Short
memory reacts fast to reversals but churns on nulls (3.3 switches/episode on null streams vs 2.0
at λ=.95). A fixed discount cannot have both. That is the Atlas M2/M3 trade-off restated for
the strongest simple baseline, and it motivates Candidate A (adaptive evidence memory).

## Candidates (code `scripts/qsg_methods_search/next_method.py`)

| ID | Directive slot | Rule |
|---|---|---|
| A3 `ms_*` | multi-timescale | fast (λ_f) and slow (λ_s) counts; hurdle uses fast counts only when a predictable inconsistency test fires, else slow |
| A1 `rs_*` | two-state forgetting | slow counts; when the inconsistency test fires, replace slow counts by fast counts (restart), then accumulate slowly |
| A4 `ld_*` | mixture over discounts | follow-the-leader over λ ∈ {.8,.9,.95,.98} by discounted predictive log-likelihood |
| B1 `asym_*` | asymmetric hysteresis | separate Wald confidence levels for promotion and rollback |

C (pending-aware) and D (decision-value acquisition) are run only if the evidence from A/B
shows delay or acquisition is binding (prior records: D2 decision-at-stake acquisition clause
failed −0.9 n.s.; GAVE-R coupling failed).

## Seed allocation (registered before use)

| stage | seed base | seeds | status |
|---|---|---|---|
| D3 / panel Stage 1 (historical) | 2026110731 | 40 | used |
| C3 confirmation (historical) | 2026110799 | 100 | used |
| panel Stage 2 (historical) | 2026110851 | 100 | used |
| **NM-dev screen** | **2026110901** | 40 | development (selection allowed) |
| NM-dev replication | 2026110941 | 40 | development (replicate the finalist and the re-tuned Wald on fresh dev seeds) |
| **NM-C3 confirmation** | **2026110977** | 100 | reserved; opened once after the freeze in `NEXT_METHOD_C3.md` |

## Development gate (heuristic, not a test)

Advance a candidate when, on the NM-dev seeds, (1) family-mean net cost is below the best
widened-grid fixed-discount Wald (λ ∈ {.8,.85,.9,.93,.95,.97} × γ ∈ {.1,.15,.2,.3}) selected
in-sample on the same seeds, (2) the gain replicates on the replication seeds against the Wald
config re-selected there, (3) an ablation (setting the adaptive component off: λ_f=λ_s or
g_pro=g_rb) removes the gain, (4) the gain sits in a coherent regime family.

The primary comparator is always the in-sample-tuned best Wald, which favours the comparator.
