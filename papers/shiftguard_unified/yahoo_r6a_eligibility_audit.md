# Yahoo! Front Page Today Module (R6A) eligibility audit

**Audit date:** 2026-10-26  
**Status:** Source-supported candidate; not acquired or eligible for a registered run yet.  
**Purpose:** Determine whether this historical randomized-click log can fill the real-data policy-evaluation gap without misrepresenting it as a sequential monitoring dataset.

## Source evidence

The primary LinUCB paper describes a Yahoo! Today Module random bucket in May 2009. Users entered the bucket with a per-visit probability, an article was randomly selected from the available pool, and the record included the selected article, user/article information, and whether the user clicked. The paper used the randomized traffic for offline policy evaluation, with a May 1 tuning period and a May 3–9 evaluation period. This establishes a promising randomized logged-action design for a fixed-horizon policy-value study; it does not establish that the Webscope R6A release is byte-for-byte the same sample or that its exact schema and propensities match the paper.

Primary source: [Li et al., A Contextual-Bandit Approach to Personalized News Article Recommendation](https://arxiv.org/abs/1003.0146), especially the data collection and offline replay sections. The Webscope landing page could not be verified: the browser tool could not open it, and a direct HEAD request to `webscope.sandbox.yahoo.com` failed DNS resolution from this environment. This says nothing about whether the archive remains available through another official route. A 2011 announcement attributed to Yahoo Research states that the later R6A click-log release contains more than 45 million visits with uniformly randomized article choices, but that announcement is not a current access or license confirmation: [archived announcement](https://github.com/jaberg/skdata/issues/6).

## Preliminary task fit

| Requirement | Evidence available now | Decision |
|---|---|---|
| Real observations accessible in this workspace | No R6A files or manifest found in the repository; the source has not been acquired. | **Fail for execution.** Do not report R6A as acquired or evaluated. |
| Logged action and outcome | The primary paper says each event records a randomly served article and its click outcome. | **Promising for fixed-horizon contextual-bandit policy evaluation**, conditional on release schema validation. |
| Known assignment probabilities and positivity | The paper describes random article selection and derives replay evaluation for its logging process; the exact probabilities and choice-set support in the specific R6A release are not verified here. | **Unresolved.** Recover per-event or design-level propensities and candidate sets from the licensed release; test support before defining estimands. |
| Event chronology | The paper reports dated periods, but this source review did not establish the exact timestamp field or ordering in the R6A files. | **Unresolved.** Do not assume event-time replay is available until the schema is inspected. |
| Feedback delay / label availability | The paper records click/no-click outcomes but does not establish per-event label-release timestamps or click-maturity timing. | **Not established.** Not eligible for delayed-feedback or anytime-valid monitoring claims. |
| Downstream utility | Click is an observed reward for a news recommendation decision. No operational monetary cost, retraining cost, or switching cost is provided. | **Possible click-value policy study**, with resource counts reported separately; no net-business-utility claim. |
| Independent final evaluation | The paper already used randomized traffic for tuning and evaluation. No ShiftLab split has been frozen and the source may be the same historical release. | **Not confirmatory yet.** Any split must be source-aware, time-respecting if timestamps exist, and audited for prior exposure. |
| Redistribution/access | Historical Webscope documentation reproduced in an archived global README describes signed academic-use terms and restrictions on redistribution, networked storage, and offsite archiving. The current dataset-specific agreement has not been obtained. | **Do not place raw data in GitHub or another networked repository.** Review the actual agreement before access or storage. |

## Why it is worth pursuing, and what it cannot solve

If the exact release can be lawfully accessed and its propensity contract verified, R6A could complement Open Bandit Dataset with a second randomized contextual recommendation task. A frozen, fixed-horizon comparison could evaluate candidate policy value, regret against a declared reference, label use, and estimation uncertainty under replay/off-policy estimators. The primary estimand would be expected click reward, not the paired classification-loss estimand used by DIVE on non-performative data.

R6A alone would not establish sequential decision-harm detection, delayed-label validity, real operational intervention costs, or the full monitor-certify-intervene framework. Nor does a second recommendation dataset by itself satisfy the goal's requirement for two distinct real-data task families. Treat it as a targeted Q2/Q3 acquisition candidate, not a replacement for a separate temporal or non-recommendation external task.

## Acquisition and eligibility gates

1. Obtain the current Webscope listing, dataset-specific license, and written storage/compute rules from the institution's authorized route. Confirm whether local-only processing is allowed and whether derived aggregate outputs may be retained.
2. Check the archive size and current storage before download. This workspace currently has approximately 128 MiB free on C:, which is insufficient for the roughly-gigabyte scale reported by secondary catalogues; that size must be checked against the authorized current listing.
3. If authorized, store the archive outside Git and outside networked/cloud-synced folders unless the agreement explicitly permits them. Record the approved source version, receipt, archive hash, and data-use terms without committing records.
4. Inspect only schema and aggregate diagnostics first: event count, timestamp coverage and order, action-set size, logged propensity values, reward support, missingness, and duplicate keys. Confirm the release is the claimed randomized sample and establish the exact design probability.
5. Freeze a policy-evaluation protocol before reading outcomes for model selection. Separate training, policy development, and one final chronological or randomization-respecting evaluation partition; use independent-user or appropriate clustered uncertainty if user identifiers permit it.
6. Compare only estimators and policies supported by the logged-action contract. Report click value and estimation uncertainty separately from label, compute, or deployment costs; do not combine them without a defensible common unit.

## Current decision

**Keep as a conditional acquisition lead; no download or experiment is authorized by this audit.** The R6A primary-source evidence is sufficient to justify seeking the access and license facts, but not to declare the dataset available, its specific release schema verified, or its task confirmatory. The near-term project can continue using the locally available OBD development artifacts while the independent task-family and timing gaps remain open.

## Provenance

- Workspace search: no occurrence of `Yahoo`, `R6A`, `R6B`, or `Front Page Today` was found in the audited project sources, scripts, outputs, or manifests.
- Filesystem check: C: free space was 134,475,776 bytes at audit time.
- Historical license reference (not a substitute for the current agreement): [Yahoo Webscope global README reproduced in Stanford's archived data catalogue](https://infolab.stanford.edu/~ullman/mining/2009/YahooData.pdf).
- No raw or derived user data were retrieved, written, or committed.
