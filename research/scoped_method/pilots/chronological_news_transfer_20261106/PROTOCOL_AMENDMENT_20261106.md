# Prospective source and implementation audit — 2026-11-06

This amendment was written before any test-window model loss or deployment-policy outcome was
computed. It clarifies source metadata and implementation details while leaving the registered
model pair, windows, validation thresholds, cost contract, primary contrasts, and bootstrap plan
unchanged.

## Source receipts

| Source | Download / pinned version | Bytes | SHA-256 | Provenance and restrictions |
|---|---|---:|---|---|
| UCI News Aggregator 359 | Official UCI static archive, retrieved 2026-11-06 22:17 UTC | 29,224,203 | `1f5f08691f0ce576cb0b5cfdbcb8c55e0ec14dda8f3e07933da72c500338845a` | UCI repository metadata says CC BY 4.0; the archive README says “Public domain” and also imposes source/use restrictions. Treat as restricted, keep raw archive local, and do not redistribute it. It supplies titles and approximate publication timestamps. |
| MN-DS v1 | Zenodo record 7394851, retrieved 2026-11-06 22:21 UTC | 47,598,602 | `ce71a92bc8d8d896e8eeacbbe1e73819f42e09b535a04a47d5b67d968c9ddd5f` | Zenodo describes CC BY 4.0, 10,917 articles, 2019 dates, 17 first-level categories and outlet field. Its included license text has a stale “Retail fuzzy cognitive map dataset” attribution; keep raw local and do not redistribute until the attribution is resolved. `published_utc` is used as the event clock. |
| Wild-Time HuffPost | Hugging Face dataset `khalidalt/HuffPost` at commit `01020533529fc1cda0af7d99231eb96e7837f883`, retrieved 2026-11-06 22:25 UTC | 83,917,554 | `fc5d8d34bd4ba55206cd715aa5fdf6d52b6e5e8e32fcac8684d941a9c5cbef95` | Dataset card declares CC0; Wild-Time README also identifies HuffPost as CC0. This v2 archive has calendar dates, not intraday publication times. Use midnight UTC for the date and retain the 24-hour delay as explicitly simulated. |

The raw files are under ignored `data/raw/chronological_news_transfer_20261106/`; they are not
added to Git. UCI's archive contains 422,936 data rows, with its README describing only web
references and not full articles. The registered classifier therefore uses only the title.

## Holdout and source-cluster audit

During schema inspection of the MN-DS CSV, the first data row was printed. Its `data_id` is
`1809`, and its timestamp falls in the registered October–December test window. No MN-DS model
prediction, loss, policy decision, or test aggregate was computed. Exclude that record from any
MN-DS test replay and record this exposure in the manifest. MN-DS is otherwise only a validation
screen unless a reviewer approves that exclusion as adequate.

The original protocol's three-independent-cluster rule governs pooled/generalization claims; it
is not an additional source-eligibility threshold. Source eligibility remains exactly the four
registered validation checks: at least 100 disagreements; overall error advantage at least 0.03;
conditional disagreement advantage at least 0.20; and improvement in at least two of three
chronological validation blocks. UCI freezes its qualifying publishers for source-level analysis;
MN-DS freezes qualifying outlet names; HuffPost is one source cluster. Fewer than three eligible
independent source clusters precludes a pooled generalization claim but does not rewrite the
source-level validation eligibility rule.

## Pre-test validation results

The protocol's four eligibility checks were run only on the registered training and validation
periods. No test outcomes were evaluated.

| Source | Eligible by frozen validation rule? | Validation evidence | Test status |
|---|---|---|---|
| UCI News Aggregator | No | 70,999 validation rows; incumbent-minus-challenger error advantage `0.0090`; conditional disagreement advantage `0.0641`; fails the 0.03 and 0.20 thresholds. | Locked; do not open. |
| MN-DS | No | 2,091 validation rows; advantage `−0.0158`; conditional disagreement advantage `−0.0603`; not better in two of three blocks. | Locked; do not open. One exposed row excluded as above. |
| Wild-Time HuffPost | Yes | 8,786 validation rows; 6,953 disagreements; advantage `0.4046`; conditional disagreement advantage `0.5113`; block advantages `0.4199`, `0.3749`, and `0.4191`. One source cluster only. | Eligible for a source-level test replay; no cross-source generalization claim. |

The initial analysis scripts mistakenly made three validation publishers an eligibility check.
This amendment corrects that implementation error before test opening; the registered four
validation conditions are unchanged. The UCI and MN-DS conclusions remain ineligible under the
four correct conditions. HuffPost is eligible. The test window and primary outcome remain frozen.
The earlier HuffPost validation artifacts using headline sorting for tied dates are preserved as
`pretest_manifest_title_tiebreak_superseded.json` and
`source_eligibility_title_tiebreak_superseded.json`. Development rows were subsequently sorted by
the registered stable source line ID within date, and the training/validation preparation was
rerun before any test opening. The table above reports the corrected frozen result.

## Current scope

The only source eligible for the frozen test analysis is HuffPost. A positive test result would
support a time-blocked retrospective transfer case study under simulated 24-hour feedback, not a
cross-source generalization claim, causal deployment claim, or transfer of PFA-SR's iid
conditional-null guarantee. PFA-SR is published prior art; this remains an application study, not
a novel-method contribution.

## Pre-opening evaluator and clock clarification

Before test opening, the evaluator was independently reviewed and amended to write an exclusive,
fsynced opening-start marker containing metadata-selected candidate row IDs before target cleaning,
then a second exclusive marker with the final ordered, target-cleaned source-row IDs before computing
predictions/losses. Targets outside the registered 11-class mapping are excluded before predictions
or loss calculations, and the 2,000-row gate is checked after this cleaning. The evaluator checks
the archive, frozen model pair, eligibility,
code, simulator/policy sources, `uv.lock`, and protocol hashes against a separate pre-outcome code
freeze. Same-day events follow original JSONL line order; every request at a date's midnight is
issued before labels whose simulated release timestamp is that midnight. Labels released on dates
without articles are delivered before requests at the next later event timestamp.

The policy APIs accept an integer event-count `delay` for acquisition pacing, while actual feedback
delivery is timestamp-aware. Actual labels enter `observe` only at publication date + 24 hours. The
delay argument supplied to policy constructors is the median number of eligible validation
articles per calendar day, computed only from 2017 validation rows; it configures algorithm pacing
and is not the actual feedback clock. This is a shared, explicit event-clock approximation for
policies whose acquisition logic takes an integer delay. The test report must state this limitation
and must not describe policy-internal delay as exact calendar-time modeling. This clarification was
recorded before opening the test window.
