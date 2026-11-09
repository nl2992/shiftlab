# Wild-Time HuffPost/arXiv feasibility audit

Audit date: 2026-11-06. Scope: inspect current repository/environment and official benchmark/source descriptions only. No Wild-Time data were downloaded, no held-out outcomes were inspected, and no production code was changed.

## Decision

Wild-Time HuffPost and arXiv are feasible as **chronological prediction-drift datasets**, but the published benchmark releases do not establish authentic label-release chronology. On their own they are therefore **not yet admissible as untouched confirmation of a method whose claim depends on scarce/delayed labels**. They can become an authentic paired-model stream only if a source-side audit establishes what was visible at prediction time, records a valid target release clock, and freezes model/data artifacts before exposing the confirmation labels. If that evidence cannot be established, use them only for retrospective predictive-loss replay and label the replay as such.

There are two top-level data sources (HuffPost and arXiv); two clusters are too few for reliable source-cluster uncertainty. They are useful independent domains as a transfer check, but cannot alone satisfy a robust source-level generalization claim. Add independently governed time-series or other chronological sources, each with a defensible target-release mechanism.

## What the official benchmark establishes

- Wild-Time describes HuffPost as classifying headlines into 11 categories over 2012–2018, partitioned by year. Its Eval-Stream protocol randomly holds 10% of each year for test and trains on the remainder; for OOD it evaluates all samples in each year. The official supplement says the underlying Kaggle source is a CSV and the published setup shuffles samples within year. This is a benchmark split, not an event-by-event online replay protocol. The official page documents annual timestamps and a package loader, but not per-item prediction and label-release events.
- Wild-Time describes arXiv as predicting one of 172 primary categories from paper title over 2007–2022, partitioned by year. Its supplement says metadata is JSON, sorted by “update date,” and randomly split within year. Update date and latest category metadata do not by themselves reconstruct what was known at first submission or announcement.
- The source descriptions do provide candidate event-time fields: the Kaggle HuffPost `date` is described as article publication date; arXiv records include version history, with arXiv’s first-version timestamp potentially usable as an event-time proxy. These are event clocks, not label-release clocks. The official benchmark does not document category annotation availability, any query service, or release delay.
- Both datasets are listed by Wild-Time as CC0/public-domain sources. The Wild-Time loader is an available acquisition route; its public documentation recommends `pip install wildtime`, and the GitHub README specifies `pip install wildtime==1.1.3`.

Sources: [Wild-Time official page](https://wild-time.github.io/), [official NeurIPS 2022 supplement, HuffPost/arXiv protocol](https://proceedings.neurips.cc/paper_files/paper/2022/file/43119db5d59f07cc08fca7ba6820179a-Supplemental-Datasets_and_Benchmarks.pdf), [Wild-Time official repository](https://github.com/huaxiuyao/Wild-Time), [Kaggle HuffPost News Category Dataset v2](https://www.kaggle.com/datasets/rmisra/news-category-dataset), [Kaggle arXiv metadata dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv).

## Current worktree and environment

- The active checkout is `/Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/scoped-method-research-2026-11-06`, branch `codex/scoped-method-research-2026-11-06`, HEAD `c13f232edd72f7d56c286aba5c3cd68e0315b68b` at audit start.
- `data/` has no files with `wild`, `huff`, or `arxiv` in their paths. Repository search found no Wild-Time-specific acquisition or evaluation implementation.
- The project virtualenv has `pandas` and `pyarrow`, but no `wildtime`, `torch`, `torchvision`, `datasets`, or `huggingface_hub`. The root environment has none of these packages either. The `pyproject.toml` offers optional `wilds`/`torchvision` and neural dependencies, but not Wild-Time. Installing the official loader may require resolving its PyTorch dependency; this audit did not install packages.
- Wild-Time itself supplies data loading and conventional benchmark training/evaluation, not authentic prediction-time/label-release event records or ShiftLab paired-policy stream construction.

## Prospective stream protocol

Use raw source records rather than the Wild-Time annual random splits. Freeze the extraction code, upstream snapshot/version, license and checksum before any model fit. Maintain a row-level manifest with stable source ID/hash, raw event timestamp and timezone, feature availability time, each model prediction time, label provenance, label-release time and release evidence. Remove duplicates and revisions using rules fixed on development data only.

### HuffPost candidate protocol

1. Use each article’s original publication date as the event clock only after validating the column’s precision, timezone and source provenance. If it is date-only, order within each day with a deterministic source-ID tie-break and treat all same-day decisions as simultaneous; do not invent intraday order.
2. A possible chronological split is fit both frozen model candidates on the source’s pre-2016 records and evaluate the untouched 2016–2018 stream in publication-time order. This aligns with the benchmark’s 2016 split while avoiding its random within-year shuffling. Freeze tokenization/vocabulary and any embeddings using training records only. Preserve exact headline/category versions as of prediction time.
3. Prediction time can be the recorded article publication time (or day boundary if only date is available), if the input headline and model output are archived as available then. The source’s `category` is a retrospective supervised target. Neither the official dataset nor paper provides evidence that the category was publicly available at that publication time. Do not define a fabricated fixed delay and call it real. For loss replay, record `label_release_time = unknown`; for a hypothetical operational scenario, choose explicit imposed delays, mark them synthetic, and exclude that analysis from real delayed-feedback confirmation.
4. A source-specific live/archived HuffPost tag feed or editorial metadata release log could establish the label clock. Seek permission/documentation or verifiable historical archive records before considering labels “released.” If such evidence is unavailable, HuffPost does not validate a scarce-label method claim.

### arXiv candidate protocol

1. Use the first submitted version’s submission/announcement time as an event-time candidate only after resolving timezone and whether it denotes submission completion or public announcement. Pin exact metadata snapshot and source version. Do not use Wild-Time’s `update_date` to order first-seen predictions without checking whether later replacement metadata changed it.
2. Use a prospective cutoff such as first submissions through 2015-12-31 for training, then first submissions from 2016 onward for untouched chronological evaluation. Use only v1 title and v1 primary category captured at v1; exclude later titles/category revisions from inputs and targets. Check whether the official archive offers a version-specific category snapshot; the common Kaggle metadata’s current `categories` field and version date list alone do not prove historical v1 category.
3. Prediction time is the first public announcement time, not an earlier author-submission timestamp, unless the prediction system demonstrably receives the submission before public announcement. For target release, the category may be present in the public announcement metadata, but the currently available benchmark specification does not document when the primary category becomes observable or whether it is stable. Therefore queried-label release is still unknown until an arXiv announcement feed/archive is captured and category state is versioned. Any fixed post-announcement delay is a sensitivity analysis, not observed delay.
4. As a safe no-leakage alternative, freeze the pair before the confirmation window and compute all predictions before unmasking v1 labels. This establishes chronological predictive performance. It cannot establish a label-acquisition advantage or runtime adaptation unless the release feed is authenticated.

### Paired model construction and independent units

- Choose the classifier family, tokenizer, training cutoff, hyperparameters and pair construction using development data, then hash weights, tokenizer, source snapshot and prediction outputs before revealing target labels. Both models must predict every same eligible record. Avoid LLM/API models whose training cutoff or training-data exposure to 2007–2018 records is unknown; a modern pretrained text encoder may have memorized these records. Prefer models trained from scratch or an auditable checkpoint with known cutoff and document the limitation.
- Keep one shared chronological sample path and compare methods on identical item IDs, horizon, query eligibility, label budget/cost and switch cost. A query reveals one outcome for both frozen model predictions; labels for unqueried items remain hidden to the policy. If category labels were already available publicly at prediction time, this is an archival replay with artificial query costs, not selective real feedback.
- Treat HuffPost and arXiv as two source clusters, and preserve year blocks within each source for time dependence. With only two source clusters, report source-specific effects and do not present a source-bootstrap interval as well-calibrated external uncertainty. Increase source count with independently sourced datasets before claiming general real-world transfer.

## Reproducible acquisition commands (not executed)

These are small metadata/setup commands; the dataset files themselves were not fetched in this audit. Pin the repository commit and exact upstream artifact SHA-256 in a registry before running an acquisition. The official loader can be used as a convenience to inspect its URLs/download behavior, but the registered raw artifact and checksum, not a mutable “latest” loader response, must define the experiment.

```bash
# Capture upstream code revision without downloading benchmark data.
git ls-remote https://github.com/huaxiuyao/Wild-Time.git refs/heads/main

# Optional loader installation in an isolated environment, after its dependency
# versions are pinned and compatible with the project runtime.
python -m venv .venv-wildtime
. .venv-wildtime/bin/activate
python -m pip install 'wildtime==1.1.3'

# Inspect package location/API before choosing any data-download call.
python - <<'PY'
import importlib.util
print(importlib.util.find_spec('WildTime'))
print(importlib.util.find_spec('wildtime'))
PY

# Kaggle acquisition route (requires Kaggle account/CLI and a frozen dataset
# version; do not use `-o`/overwrite after registration).
kaggle datasets list -s 'News Category Dataset'
kaggle datasets list -s 'Cornell University arxiv'
# After confirming owners, exact dataset IDs and version numbers, download to a
# write-once raw directory, then hash and log metadata before parsing:
# kaggle datasets download <owner>/<dataset> --dataset-version-number <N> -p data/raw/<source>
# shasum -a 256 data/raw/<source>/*
```

Do not execute the Kaggle download until exact IDs/versions are verified and approved in the frozen source registry; dataset snapshots can be large and have mutable release history. A reproducibility manifest should include source URL, dataset owner/slug, source version, retrieval UTC, artifact filename/size/SHA-256, license, parsing-code commit, and all exclusion/deduplication rules.

## Blockers and smallest next action

1. **Label-release proof is missing for both tasks.** Obtain versioned HuffPost category availability evidence and arXiv v1 announcement/category provenance. If neither is available, classify both as retrospective chronological loss streams; do not claim genuine label scarcity/delay.
2. **No local data/package support exists yet.** First pin source versions and resource estimates, then install the official loader only in an isolated environment or download a selected frozen metadata snapshot. Hash before parsing.
3. **Wild-Time’s standard splits are not online episodes.** Rebuild from row-level source records with event time, causal train cutoff, no random within-time split, and precommitted confirmation window.
4. **Two source clusters are insufficient for source-level uncertainty.** Add more independent source domains or restrict the claim to two-case transfer evidence with source-specific results.
5. **Pretraining leakage risk is material.** Verify model training cutoff/data contamination or train from scratch. Unknown pretrained exposure to historical titles makes untouched-model confirmation doubtful.

Smallest next step: obtain and freeze source/version metadata and confirm category release semantics without opening the held-out target labels. If no defensible release timestamps can be documented, close the Wild-Time path for real delayed-label confirmation while retaining it only as a chronological predictive-loss replay candidate.
