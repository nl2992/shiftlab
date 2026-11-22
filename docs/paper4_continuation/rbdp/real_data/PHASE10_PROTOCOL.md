# Phase 10: extra benchmark diversity (protocol, written 2026-11-22 before any Phase 10 fit)

Goal (user, 2026-11-22): add more datasets that support the paper's claim, with a stated reason for each; record any that
do not work and why, and move on; failures are not integrated into the paper. Keep adding until the supporting set is
genuinely diverse (domains, drift types, modalities) and the comparison with the decided baselines (P1 fixed-sample test,
P2 count SPRT, P3 HMM-filter threshold, P4 myopic VOI, P5 IID-optimal, P6 e-process gate) holds on each.

Pipeline, evaluator, shuffle control, positivity rule and orientation handling are exactly Phase 7's (`run_phase7.py`,
`run_phase5.py`); only the dataset list changes. Script: `scripts/paper4_continuation/rbdp/real_data/run_phase10.py`;
raw data under `data/raw/real_chains/phase10/`; records in `results/attempts_phase10_shard*.jsonl`.

## Datasets and the reason each is included

Family B (fresh standard drift benchmarks from Phase 7's scope, not run before because Phase 7 stopped at 35):
covtype (spatial ordering, slow covariate drift), poker-hand (no temporal structure, a negative control: a null result is
expected and is the correct outcome), KDD Cup 99 10% (bursty attack regimes), Intel Berkeley sensor (smooth diurnal drift),
Ozone (small n, seasonal). INSECTS is hosted on a Google Drive share and is not fetched.

Family Bext (OpenML): electricity, Bike_Sharing_Demand, MagicTelescope, Higgs (first 200k rows), PhishingWebsites,
SMSSpam, adult, bank-marketing, default-of-credit-card-clients, OnlineNewsPopularity, occupancy, gas-drift. Reasons:
cover energy, demand, physics (iid, expected null), web security, text, census, finance, news popularity over time,
building sensors, and gas-sensor drift.

Family C (new, OpenML): numerai28.6 (era regime shifts), nomao (behavioural drift), Click_prediction_small (ad clicks),
road-safety (accidents over years), Amazon_employee_access, kdd_el_nino-small (climate regimes), electricity-normalized
(preprocessing sensitivity of an existing stream), jannis (iid, expected null), Diabetes130US (practice drift),
credit-g and pc1 (small-n edge cases), mozilla4 (release process drift), ailerons and elevators (stable regimes).

## Rules

1. A dataset counts as supporting only under the Phase 4b-7 positivity rule (two-state fit passes G1/G2, positive premium
   in some (T, B) cell, 0 of 5 positive shuffles). Nothing about the rule changes.
2. Every attempted dataset is recorded in the ledger below with its status and, when it is not positive, the reason
   (fetch failed, too short, no premium, fit rejected, persistent chain with no premium, shuffle positive).
3. Non-positive datasets are not added to the paper. Positive ones are added to Table `real35` (renamed) and to the
   baseline panel (`run_phase7_baselines.py`).
4. Datasets are never dropped after seeing a positive result to protect a headline; the ledger is append-only.

## Ledger

(filled in after the run: `LEDGER_PHASE10.md`)

## Phase 10b: family D, alternation sources (protocol, written 2026-11-22 before any Phase 10b fit)

Goal: add sources where a known mechanism produces alternation (anti-persistence), each with its stated reason; same
evaluator, shuffle control, positivity rule and orientation handling as above (`p5.eval_streams`, `p5.both`); no stopping
target; every outcome is recorded. Script: `scripts/paper4_continuation/rbdp/real_data/run_phase10b.py`; raw data under
`data/raw/real_chains/phase10b/`; records in `results/attempts_phase10b*.jsonl`. Every stream is capped at the first 3,000
rounds in time order and needs at least 200. Streams are level thresholds or natural binary events only, never
differences or "did it rise" events (a difference of i.i.d. data has r1 = -1/3 by construction). Each record carries
`difference_of_series: false` and `wn_r1_same_construction` (r1 of the same construction applied to i.i.d. noise of the same
length, expected near 0). Sources that cannot be fetched are recorded as `fetch failed` with the error.

| Source | Reason | Stream |
|---|---|---|
| GeyserTimes archive, per-geyser files (geysertimes.org/archive/geysers/*_eruptions.tsv.gz; Old Faithful from 2020-01-01, Daisy, Riverside, Grand, Castle, Beehive) | Old Faithful's long/short interval alternation is a known mechanism in other periodic geysers | inter-eruption interval > median of the used intervals; only eruptions with primary ID = eruption ID, not approximated (A=0) and not questionable (q=0); intervals longer than 3x the geyser's median interval span unobserved eruptions and are dropped, not bridged |
| Sackmann tennis_pointbypoint (ATP and WTA files, raw GitHub CSV) | serve alternates by game, so "player 1 wins the point" switches regime each game | point winner, within matches, concatenated in file order, one stream per tour |
| UCI Bach Chorales (id 25, pitch events) | melodic register alternation | MIDI pitch > median pitch of its chorale, per event, chorales concatenated in file order |
| PhysioNet Fantasia (f1y01-03, f1o01-03; beat annotations read directly from `.ecg` files, `wfdb` is not installed) | respiratory sinus arrhythmia makes RR intervals oscillate | RR interval > median RR of the subject's first 3,000 intervals (0.3 s < RR < 2 s) |
| NCBI genome purine/pyrimidine | already evaluated in Phase 4 (family G, 16 genomes) | not repeated; recorded as "already evaluated in Phase 4" |

## Phase 10c: family E, more diverse supporting sources (protocol, written 2026-11-22 before any Phase 10c fit)

Goal: add sources from further domains (more geysers, sport, protein structure, language families, cricket), each with a
stated reason. Same evaluator, shuffle control, positivity rule and orientation handling as Phases 5-10b (`p5.eval_streams`,
`p5.both`); no stopping target; every outcome (positive, null, fetch failed) is recorded. Script:
`scripts/paper4_continuation/rbdp/real_data/run_phase10c.py`; raw data under `data/raw/real_chains/phase10c/`; records in
`results/attempts_phase10c*.jsonl`. Every stream is capped at the first 3,000 rounds in time (file) order and needs at
least 200. Streams are level thresholds or natural binary events only, never differences or "did it rise" events. Each
record carries `difference_of_series: false` and `wn_r1_same_construction` (r1 of the same construction applied to
i.i.d. noise of the same length: a level threshold of Gaussian noise for geysers; i.i.d. Bernoulli with the stream's own
mean for natural binary events, expected near 0). Sources that cannot be fetched are recorded as `fetch failed` with the error.

| Source | Reason | Stream and fixed selection rule |
|---|---|---|
| E1. GeyserTimes archive per-geyser files (same URL pattern and filters as Phase 10b: primary ID = eruption ID, A=0, q=0, no start-date restriction, intervals longer than 3x the geyser's median interval dropped, not bridged) | interval alternation is a known geyser mechanism; tests how widely it holds | inter-eruption interval > median of the used intervals, first 3,000 in time order. Selection: every geyser in the archive listing (`archive/geysers/*_eruptions.tsv.gz`) except those already evaluated in Phase 10b (Old_Faithful, Daisy, Riverside, Grand, Castle, Beehive); count its valid intervals under the filters above (full history); keep those with at least 3,000 valid intervals; order by descending count (ties by name); evaluate the first 12. Counting is done once (`--prepare`) before any fit. |
| E2. Sackmann tennis_MatchChartingProject, `charting-m-points-to-2009.csv` and `charting-w-points-to-2009.csv` (raw GitHub) | the serve switches every game, so "the first server wins the point" switches regime each game | per match, 1 if the point winner (`PtWinner`) equals the match's first server (`Svr` of the first row of the match), else 0; points with missing Svr or PtWinner dropped; matches concatenated in file order; first 3,000 points; one stream per tour (men, women). Only the first (earliest) file is used per tour because the cap is reached inside it. |
| E3. UniProt fibrillar collagens (REST `uniprotkb/<acc>.fasta`): P02452 human COL1A1, P08123 human COL1A2, P02461 human COL3A1, P02453 bovine COL1A1, P11087 mouse Col1a1, P08121 mouse Col3a1 | Gly-X-Y repeats impose periodicity on the sequence | hydrophobic indicator with `run_phase5.HYDRO` = IVLFCMA (the Phase 5/6 mapping), first 3,000 residues, both orientations |
| E4. Project Gutenberg via gutendex (`languages=<code>&sort=popular`, first page, first plain-text book; text from the Gutenberg mirror as in Phase 5/6). Languages not evaluated in Phases 4-6 (those were en fr de es it pt nl sv da fi hu pl cs la ru el ro ca eo tr cy is no tl ga sw id), Latin script only: eu (Basque), af (Afrikaans), gl (Galician), oc (Occitan), fy (Frisian), br (Breton), ia (Interlingua), gd (Scottish Gaelic), lt, lv, et, sk, sl, hr, sq. The earlier candidate list also named Icelandic, Norwegian, Irish and Tagalog; these were evaluated in Phase 6 and are skipped. | alternation in phonotactics across language families | vowel / consonant stream exactly as Phase 4b/6 (`p4b.letters`: lower-cased letters of the book body, positions 2,000 to 5,000, so at most 3,000 letters; both orientations). Vowels = Phase 6 `LATIN_BASE` plus the macron/breve/ogonek/dot vowels `āăąēĕėęěĩīĭįıōŏőũūŭůųű` so that Baltic, Albanian and similar orthographies are not mis-coded; sq adds `ë`. A language is skipped (recorded `fetch failed`) if gutendex lists no plain-text book or the book has fewer than 1,000 usable letters ("too few letters"). |
| E5. Cricsheet IPL ball-by-ball JSON (cricsheet.org/downloads/ipl_json.zip) | strike rotation: odd runs swap the batter, so scoring pattern per ball may alternate (exploratory) | per delivery 1 if `runs.total` > 0 else 0; regular innings only (super-over innings excluded); innings in order, matches in ascending file-name (match id) order; concatenated; first 3,000 deliveries; one stream |

Selection rules and accessions above are fixed before looking at any result; datasets are not dropped after seeing a result.

### Phase 10c retry of the 13 languages that failed on gutendex (written 2026-11-22 before any retry fit)

Languages: eu, fy, lt, sl, lv, hr, gl, ia, et, sq, oc, gd, sk (all `fetch failed` in `attempts_phase10c.jsonl`, which is not modified).
Script `run_phase10c_retry.py`; records in `results/attempts_phase10c_retry.jsonl`, each with `source` (ebook id and URL),
`retry_of` and `reason`. Same vowel/consonant construction, vowel sets and evaluator as the Phase 10c languages af and br.
1. Gutendex is tried again (3 attempts, 60 s each) with the original rule (most popular first-page book with a plain-text format). If it answers with such a book, that book is used.
2. If gutendex does not answer (timeout/HTTP error), or answers with no plain-text book, fallback via Project Gutenberg's catalog `https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv` (Language column; Type = Text): for each language, the lowest-numbered Text-type ebook whose plain-text file yields at least 3,000 letters after stripping the Gutenberg header and footer. Candidates are tried in ascending ebook number; the first one satisfying the rule is used. The stream is letters 2000-5000 of the stripped body (Phase 4b window) when the body has at least 5,000 letters, otherwise its first 3,000 letters (recorded in `window`). Catalog entries listing several languages count if the language code is among them.
3. A language whose catalog or text cannot be fetched is recorded `fetch failed` again with the error.
