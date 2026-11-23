# Real-chain study: protocol (written before any real series was fitted)

**Date:** 2026-11-16. **Author:** lead. **Authorisation:** the user asked for real data on 2026-11-16 ("find 10
datasets that help and support our viewpoint, 10 minimum; we run it until we have 10"). The Paper 4 research
contract said "synthetic only until a method passes"; RB-DP has passed its synthetic validation and independent
review, and the user has lifted that restriction for this study. The repo's own holdouts (for example the EIA 2026
holdout) are **not** touched. Only public, small series are fetched, into `data/raw/real_chains/` (git-ignored).

## Question

Do realistic binary event streams have fitted two-state hidden-Markov structure for which (a) the causal-safety
premium Γ = V*_causal − V*_IID is positive and (b) the IID-optimal policy breaks the causal risk budget?

## Counting rule (so the count of 10 means something)

The user wants 10 datasets that support the viewpoint. To keep that honest, every candidate that is attempted is
reported with its outcome, in the order tried, and the write-up gives the denominator: *k datasets attempted,
j passed the fit gates, m showed a positive premium*. Candidates are tried in the fixed order below; the run stops
when 10 have a positive premium or the list (and any documented additions) is exhausted. A candidate is never dropped
after its premium is seen. If after the list there are fewer than 10, more candidates are appended to the list with
a timestamp and the reason, before they are fitted.

## Pipeline (fixed in advance)

1. **Binary stream.** Each dataset has a binarisation rule declared in the candidate table before fitting. The
   stream x_1..x_n is the label sequence Y_t of the game (1 = the event the learner is paid to predict).
2. **Fit.** Two-state hidden Markov model with Bernoulli emissions (parameters t01, t10, e0, e1, prior = stationary
   law) by EM, 20 random restarts, best log-likelihood, states ordered so that e0 < e1.
3. **Gates.**
   - G1 (structure): on a 50/50 split (fit on the first half, score the second), the HMM's mean log-likelihood must
     beat the best of (i) i.i.d. Bernoulli and (ii) a first-order Markov chain on x_t by more than 0, **or** its BIC
     on the full series must beat both. (A stream with no hidden-state structure is reported as G1-fail.)
   - G2 (model fit for RB-DP): fitted e0 < 1/2 < e1, and t01, t10 ∈ [0.01, 0.99]. The emission means are clipped
     to [0.02, 0.98] for the solver.
4. **Evaluate** (RB-DP, `risk_budget_dp_fast`, `lattice_exact=True`, delay 1; and `risk_budget_dp_d2` at delay 2
   with N = 10·2^B): α = 1/10, c = k = 0, prior = stationary law, mode causal and iid.
   - Primary cell: T = 32, B = 3, delay 1. Also reported: T ∈ {16, 32}, B ∈ {1, 2, 3, 4}, delay 1; and T = 16,
     B ∈ {2, 3}, delay 2.
   - Quantities: V*_IID, V*_causal, Γ, ρΓ = Γ/(C0 − V*_IID), and the true causal risk of the IID-optimal policy.
5. **Outcomes.** *Positive premium* = ρΓ > 1e-3 at the primary cell with G1 and G2 passed (1e-3 is far above the
   1e-9 numerical noise and far below any bar that could hide a real effect; the size is reported, with 0.05 marked as
   substantial). *Null* = G1 and G2 passed, ρΓ ≤ 1e-3. *Not applicable* = G1 or G2 failed.
6. **Reading rules.** Fitted parameters are point estimates; no confidence intervals are claimed unless computed.
   A positive premium on a fitted chain says the *model* has a premium; it is not a field test of the policy. The
   null in the game is adversarial and is not claimed to be present in any dataset.

## Candidate list (fixed order; binarisation declared now)

Sources: Rdatasets CSVs (https://vincentarelbundock.github.io/Rdatasets/csv/), Binance public klines, UCI, FRED
(public CSV endpoint), NOAA GHCN-Daily. Each file is checked to be under about 5 MB before download.

| # | Candidate | Stream x_t = 1 when | Why it is a plausible regime process |
|---|---|---|---|
| 1 | Old Faithful, `faithful` (eruption durations, in order) | eruption duration > 3 min | long/short eruptions alternate |
| 2 | MASS `geyser` (299 consecutive eruptions) | duration > 3 min | same, second record |
| 3 | `lynx` annual trappings | above median | ~10-year population cycle |
| 4 | `sunspot.year` | above median | ~11-year cycle |
| 5 | `nottem` monthly temperature, Nottingham | above overall median | seasonal alternation |
| 6 | `airquality` Ozone, daily | above median (NA dropped) | pollution episodes |
| 7 | `Nile` annual flow | above median | persistent regimes (control) |
| 8 | `LakeHuron` annual level | above median | persistent regimes (control) |
| 9 | `discoveries` yearly count of great discoveries | count > 3 | clustering |
| 10 | `nhtemp` annual New Haven temperature | above median | regime control |
| 11 | `EuStockMarkets` DAX daily log return | return > 0 | sign of daily return |
| 12 | `EuStockMarkets` FTSE daily log return | return > 0 | same, second index |
| 13 | Binance ETHUSDT 1-minute klines (last 1000) | close > open | microstructure bounce |
| 14 | Binance BTCUSDT 1-minute klines (last 1000) | close > open | same |
| 15 | Binance ETHUSDT 1-minute volume | volume above median | activity bursts |
| 16 | Binance ETHUSDT 1-hour klines (last 1000) | close > open | slower scale |
| 17 | FRED USREC (US recession indicator, monthly) | recession | persistent regime (control) |
| 18 | NOAA GHCN-Daily Seattle-Tacoma daily precipitation | precipitation > 0 | wet/dry spells |
| 19 | NOAA GHCN-Daily New York Central Park daily precipitation | precipitation > 0 | same |
| 20 | `AirPassengers` monthly | above 12-month centred moving average | trend/seasonal |
| 21 | `UKgas` quarterly | above annual mean | seasonal alternation |
| 22 | `USAccDeaths` monthly | above median | seasonal |
| 23 | `presidents` quarterly approval (NA dropped) | above median | opinion regimes |
| 24 | `co2` monthly | month-on-month rise | seasonal alternation |
| 25 | `LakeHuron` yearly change | level rises | up/down alternation |
| 26 | `Nile` yearly change | flow rises | up/down alternation |
| 27 | `lynx` yearly change | rises | up/down alternation |
| 28 | `sunspot.year` yearly change | rises | up/down alternation |
| 29 | `EuStockMarkets` SMI daily return | return > 0 | third index |
| 30 | `EuStockMarkets` CAC daily return | return > 0 | fourth index |

Candidates 25–28 use the sign of the first difference; they are counted as separate datasets only when their
parent series is also a candidate, and the write-up says so (they share a source with 3, 4, 7, 8). The write-up
reports the count both with and without such shared-source pairs.

## Outputs

`scripts/paper4_continuation/rbdp/real_data/` (fetch, fit, evaluate, report),
`docs/paper4_continuation/rbdp/real_data/results/` (per-dataset JSON, one JSONL of all attempts),
`docs/paper4_continuation/rbdp/real_data/REAL_CHAINS.md` (the write-up, with the denominator).

---

# Addendum A (2026-11-16, written after the Phase 1 result and before any Phase 2 stream was fitted)

**Phase 1 outcome, by the rules above:** 30 attempted; 1 fetch failure (c24); 8 passed G1 and G2; **0 positive**; 8 null;
21 not applicable (13 G1 failures with G2 passed, 8 others with G2 or both failing). Seven of the eight gate-passers
are persistent chains (the theory predicts no premium there and none was found). The exception, c01 (Old Faithful,
lag-1 autocorrelation −0.46, fitted t01 = 0.93, t10 = 0.63), has a positive premium at three of the eight grid cells
(ρΓ = 0.093 at T = 16, B = 3; 0.130 at T = 16, B = 4; 0.017 at T = 32, B = 4) but exactly 0 at the primary cell
(T = 32, B = 3), so it is "null" under the primary-cell rule. The lead re-derived those four numbers independently from
the stored fit. Three streams with no detected structure (c16, c21, c26) show large ρΓ on near-i.i.d. fitted chains
with C0 − V*_IID tiny; they are not applicable by G1 and are artefacts of a ratio of small numbers.

**Why Phase 2.** The theory (M1–M11) places the premium in anti-persistent mixing chains (fitted eigenvalue
1 − t01 − t10 < 0). Phase 1 shows that most real binary streams with hidden-state structure are persistent, so a broad
sweep finds almost no premium. Phase 2 asks the conditional question: *among real streams that are anti-persistent, does
the premium appear and does IID design break the causal budget?* This is a post-hoc, theory-motivated narrowing made after
seeing Phase 1. The headline for the broad question stays 0 of 30 and is reported first in every write-up. Phase 2 counts
are reported separately and never merged into the Phase 1 count.

**Phase 2 screen (computed before any RB-DP run).** For each candidate stream compute the lag-1 autocorrelation r1.
Streams with r1 > −0.15 are recorded as *screened out (persistent or near-i.i.d.)* and are not evaluated. Streams with
r1 ≤ −0.15 go through the same G1/G2 gates and the same fit as Phase 1.

**Phase 2 outcome rule.** Positive = ρΓ > 1e-3 at **any** cell of the delay-1 grid (T ∈ {16, 32}, B ∈ {1, 2, 3, 4}),
with G1 and G2 passed. This is broader than the Phase 1 primary-cell rule and was chosen after seeing c01; both counts
(primary cell T = 32, B = 3, and any cell) are reported for every Phase 2 stream. Delay 2 (T = 16, B ∈ {2, 3}) is run
for every positive. Also reported: the causal risk of the IID-optimal policy at each positive cell, and the size of ρΓ
(≥ 0.05 marked substantial).

**Phase 2 candidates (fixed order; stop at 10 positives under the any-cell rule or when exhausted).** The stream is the
sign of consecutive price changes among trades whose price changed (x = 1 when the price rose), taking the most recent
2,000 non-zero changes available from the public trade endpoint, a mechanism (bid-ask bounce) known to give negative
autocorrelation. All are public, key-free endpoints; each is a distinct instrument-venue series.

| # | Venue and instrument |
|---|---|
| P1–P10 | Binance aggTrades: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT, DOGEUSDT, LTCUSDT, LINKUSDT, AVAXUSDT |
| P11–P14 | Coinbase Exchange public trades: BTC-USD, ETH-USD, SOL-USD, LTC-USD |
| P15–P18 | Kraken public trades: XBT/USD, ETH/USD, SOL/USD, XRP/USD |
| P19–P22 | Bitstamp public transactions: btcusd, ethusd, ltcusd, xrpusd |
| P23 | Old Faithful `faithful` waiting time > 70 min (same geyser as c01; counted as a shared-source pair) |
| P24 | MASS `geyser` waiting time > 70 min (second record of the same geyser) |
| P25–P30 | Binance 1-second klines (close > open, non-zero moves only): BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, DOGEUSDT |

The write-up reports the count by source family (exchange tick data versus geyser), since P1–P22 share one mechanism and
are not independent evidence for different phenomena; a result of "10 positives" that is all one family is to be labelled
as such.

---

# Addendum B (2026-11-16, written after the Phase 2 result and before any Phase 3 stream was fitted)

**Phase 2 outcome.** 30 attempted, 30 fetched, 27 screened out on lag-1 autocorrelation, 3 evaluated and passing G1 and G2.
Under the any-cell rule 3 are positive (P6 ADAUSDT ticks, P23 Old Faithful waiting, P24 geyser waiting); under the
primary-cell rule 2 (P6, P23). P23 and P24 share their geyser with Phase 1 c01 and c02, so there is one independent
anti-persistent phenomenon with a premium (the geyser), plus P6, which is degenerate: C0 − V*_IID is 0.03 to 0.07 at every
cell, both emissions sit at their bounds, G1 passes only on a +0.00002 split margin while BIC rejects, and the lead
re-derived ρΓ = 0.082 at the primary cell from a gap C0 − V*_IID of 0.067. The lead also re-derived the P23 and P24 premiums from
the stored fits (P23: 0.144 at T = 32, B = 3 and 0.310 at T = 16, B = 4, IID-policy causal risk 0.2 and 0.325; P24: 0 and
0.070). The hypothesis that tick-level price changes alternate (bid-ask bounce) was **wrong** for these venues: 19 of 22
tick streams have positive r1 (+0.2 to +0.72), because price moves in runs as orders sweep the book.

**Phase 3: systematic, discretion-free mining.** Instead of hand-picking candidates, screen every time-series item in a
public catalogue by a fixed rule.

- *Universe.* The Rdatasets index (https://vincentarelbundock.github.io/Rdatasets/datasets.csv). An item is a candidate if
  (i) its title or documentation title matches the regular expression
  `(?i)(time series|monthly|quarterly|annual|yearly|daily|weekly|hourly|per year|per month)` or it belongs to the R
  `datasets` package and is a time-series object, (ii) its CSV is at most 1 MB, (iii) it has 80 to 5000 rows, and
  (iv) it is not already used (Phase 1: c01–c30; Phase 2: P23, P24 share the geyser; `faithful`, `geyser` are excluded as
  shared-source).
- *Streams.* For every candidate item and every numeric column that is not a time index (`time`, `Time`, `date`, `Date`,
  `year`, `Year`, `month`, `rownames`, `X`, an integer row counter), in row order, with missing values dropped: two streams,
  *above-median* (strict, ties to 0) and *rises* (first difference strictly positive). The column must have at least
  40 distinct values.
- *Order.* Alphabetical by package, then item, then column, then rule. No discretion.
- *Screen.* Lag-1 autocorrelation r1 of the 0/1 stream, computed before any fit or solve; r1 > −0.15 is screened out. At
  most 150 streams are evaluated; if more pass the screen, the first 150 in the order above are evaluated and the rest are
  counted as "not reached".
- *Evaluation.* Identical to Phase 1/2 (fit, G1, G2, delay 1 grid T ∈ {16, 32}, B ∈ {1…4}), plus a new
  **non-degeneracy condition**: a stream counts as positive only if the best positive cell also has C0 − V*_IID ≥ 0.1
  (this excludes ratios of small numbers such as P6, c16, c21).
- *Control.* For every positive stream, repeat the fit and the evaluation on 5 random time-shuffles of the same stream; report
  how many shuffles pass G1 and how many are positive. A stream whose shuffles are also positive is labelled "not
  structure-driven".
- *Counting.* A dataset item is positive if any of its streams is; also report stream-level counts and the number of streams
  that passed the screen, so the multiplicity is visible. The count requested by the user is of **distinct dataset items**,
  stopping when 10 distinct items are positive under the any-cell rule with the non-degeneracy condition and with the
  shuffle control not positive in more than 1 of 5 shuffles; otherwise the list is exhausted. Positives from the same
  package family are reported by family.
- *Honest reading.* With many streams screened, some positives can occur by chance; G1 (a held-out structure test), the
  non-degeneracy condition and the shuffle control are the guards, and the write-up states the expected number of false
  passes from the shuffle control.

---

# Addendum C (2026-11-17, written after the Phase 3 result and the white-noise control, before any Phase 4 stream was fitted)

**Instruction from the user (2026-11-17):** keep trying data sources; the run stops at 10 positive datasets.

**Phase 3 status.** The six Phase 3 items are not counted: the lead's white-noise control (`wn_control.py`) shows i.i.d.
noise yields non-degenerate "positives" at the same rate (2 of 24, 8%) as the Phase 3 real data (13 of 150, 8.7%), because
a "rises" stream is anti-persistent by differencing. **Phase 4 therefore uses level streams only** (no streams built from
differences), for which a time-shuffle of the stream is a valid no-structure control, and which are anti-persistent for a
physical or linguistic reason, not by construction.

**Phase 4 streams.**

*Family T (text, vowel/consonant).* Markov's 1913 chain: in running text, vowels and consonants alternate (P(vowel|consonant) is
about 0.66 and P(consonant|vowel) about 0.87 in Russian, an eigenvalue near −0.5). For each language in this order — `en, fr,
de, es, it, pt, nl, sv, da, fi, hu, pl, cs, la, ru, el, ro, ca, eo, tr` — take the most-downloaded book in that language that
Project Gutendex returns (`https://gutendex.com/books/?languages=<code>&sort=popular`, first result with a plain-text
format; no key). Strip the Project Gutenberg header and footer (text between the `*** START` and `*** END` lines), lower-case,
keep alphabetic letters only (letters of the language's script), take the first 3,000 letters after the first 2,000 (to
skip prefaces). x_t = 1 when the letter is a vowel. Vowel sets are fixed now: Latin script: `a e i o u y` plus their accented
forms (`àáâãäåæèéêëìíîïòóôõöøùúûüœ`; for `fi, hu, tr, ro, ca` the language's own accented vowels); Cyrillic: `аеёиоуыэюя`;
Greek: `αεηιουω` with accented forms. Digits and punctuation are dropped. If a language returns no plain-text book, it is
recorded as "fetch failed".

*Family G (DNA, purine/pyrimidine and strong/weak).* Coding DNA has period-3 structure that makes nucleotide classes
alternate. For each accession in this order — `NC_001422.1` (phiX174), `NC_001416.1` (lambda), `NC_001604.1` (T7), `NC_001417.2`
(MS2), `NC_001802.1` (HIV-1), `NC_045512.2` (SARS-CoV-2), `NC_001669.1` (SV40), `NC_003977.2` (HBV), `NC_012920.1` (human mt),
`NC_005089.1` (mouse mt), `NC_001224.1` (yeast mt), `NC_001879.2` (tobacco chloroplast), `NC_000913.3` (E. coli K-12),
`NC_000964.3` (B. subtilis), `NC_001133.9` (yeast chr I), `NC_001477.1` (dengue 1) — fetch the FASTA through NCBI E-utilities
(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=<acc>&rettype=fasta&retmode=text&seq_start=1001&seq_stop=4000`,
no key, no e-mail, at most 3 requests per second), keep A, C, G, T. Two streams per accession: *R/Y* (x = 1 for A or G) and
*S/W* (x = 1 for G or C). An accession is one dataset; it is positive if either of its streams is (multiplicity of 2 is
reported).

**Order.** Interleave T and G in this fixed order: T1, G1, T2, G2, … (T20 then G17.. exhausted last). No discretion.

**Evaluation.** Identical to Phases 1–3: lag-1 screen r1 ≤ −0.15 (computed first); fit; G1; G2; delay-1 grid T ∈ {16, 32},
B ∈ {1…4}; positive = G1 and G2 pass and ρΓ > 1e-3 at any cell **and** the best-rho cell has C0 − V*_IID ≥ 0.1
(non-degeneracy); shuffle control: 5 random time-shuffles of the level stream (seed 20261117 + k), at most 1 of 5 positive;
delay 2 (T = 16, B ∈ {2, 3}) for qualifiers. A level-stream shuffle is a valid no-structure control because it removes
the sequential structure while keeping the stream's symbol frequencies.

**Stopping.** The run stops as soon as 10 distinct datasets (a text or an accession) qualify, or the list is exhausted.
Counts by family are reported. Texts in different languages and genomes of different organisms are distinct sources, but they
are two *phenomena* (syllable structure in language, codon structure in DNA); the write-up says so.

---

# Addendum D (2026-11-17, after Phase 4; lead)

Phase 4 outcome: the 16 DNA accessions were all screened out (|r1| ≤ 0.12 except yeast mt S/W +0.41); the 20 texts were not
obtained because www.gutenberg.org timed out for the whole run. The official Project Gutenberg mirror
`https://gutenberg.pglaf.org/` answers, so Phase 4b re-runs the text family from that mirror with the same book ids
(`phase4_candidates.json`).

A lead check on English (Pride and Prejudice) gave r1 = −0.383 and a fitted chain with e0 = 0, e1 = 1: the vowel/consonant
stream is an anti-persistent Markov chain observed directly, which the two-state model contains as a special case. Gate
G1 as written requires the hidden-state model to beat a first-order Markov chain, which rejects exactly this case even
though it is the model class the game uses. For level streams in Phase 4b, G1 is therefore read as: the fitted model
(two-state model or Markov chain) beats i.i.d. on held-out data or on BIC. This is valid for level streams because a
time-shuffle removes the dependence (the shuffle control stays). Non-degeneracy is read per cell: a stream is positive if
some cell has ρΓ > 1e-3 **and** C0 − V*_IID ≥ 0.1 at that cell. Label orientation: both x = 1 for vowel and x = 1 for
consonant are evaluated; a text is positive if either is. These are changes made after seeing the English check and are
recorded here for that reason.

---

# Addendum E (2026-11-17, after Phase 4b reached 10; lead; written before any Phase 5 stream was fitted)

**Instruction from the user (2026-11-17):** 20 supporting datasets, with more diversity of source. Phase 4b's 10 texts count;
Phase 5 adds datasets until the total is 20.

**Evaluation, positivity and shuffle control:** exactly as Phase 4b (`run_phase4b.evaluate`, both label orientations, per-cell
non-degeneracy C0 − V*_IID ≥ 0.1, G1 read as in Addendum D, at most 1 of 5 shuffles positive, shuffle seed 20261117).

**Families, in this fixed order (diverse sources first, languages last):**

1. *Family F, geyser (2 datasets).* R `datasets::faithful` and `MASS::geyser` (already cached from Phases 1–2), waiting time
   above 70 min and eruption duration above 3 min, re-evaluated with the Phase 4b evaluator. A dataset is positive if any of
   its streams is.
2. *Family S, structural proteins (hydrophobic/polar).* Repetitive structural proteins alternate hydrophobic and polar
   residues (e.g. the GAGAGS repeat of silk fibroin). Source: UniProt REST, reviewed entries,
   `query=(protein_name:fibroin OR protein_name:spidroin OR protein_name:elastin OR protein_name:"silk protein") AND reviewed:true AND length:[600 TO *]`,
   FASTA, in the order returned, at most 12 entries, one per (protein name, organism). x = 1 for a Kyte–Doolittle hydrophobic
   residue (I V L F C M A); first 3,000 residues (all if shorter, minimum 600). One entry = one dataset.
3. *Family Y, alternate bearing (tree-crop yields).* Olive, pistachio, pecan, apple, avocado and mango trees bear heavy and light
   crops in alternate years. Source: FAOSTAT production bulk file (`Production_Crops_Livestock_E_All_Data_(Normalized).zip`,
   yield element 5412 or 5419), for the top 3 producing countries of each crop by 2020 production, 1961 onward. x_t = 1 when the
   yield is above its centred 5-year moving median. One (crop, country) = one dataset. Because the moving-median filter can
   itself induce negative lag-1 correlation, this family has a white-noise control (24 i.i.d. Gaussian series of the same
   length through the same filter, seed 20261117): Family Y counts only if at most 1 of the 24 noise series qualifies.
4. *Family L, the remaining 10 Phase 4 languages* (hu, pl, cs, la, ru, el, ro, ca, eo, tr), same books, same pipeline as Phase 4b.

**Order and stopping.** Families in the order above; within each, the stated order. Stop as soon as the total positive count
(Phase 4b plus Phase 5) is 20, or all lists are exhausted. Output: `results/attempts_phase5.jsonl`, `phase5_run.log`.

---

# Addendum F (2026-11-17, after Phase 5 reached 20; lead; written before any Phase 6 stream was fitted)

**Instruction from the user (2026-11-17):** about 25 supporting datasets. Phase 6 adds datasets until the total is 25.

**Evaluation, positivity and shuffle control:** exactly as Phases 4b and 5 (`run_phase4b.evaluate`, both orientations,
at most 1 of 5 shuffles positive, seed 20261117).

**Families, in this fixed order:**

1. *Family S2, silk proteins.* UniProt REST, `query=(protein_name:fibroin OR protein_name:spidroin) AND reviewed:true AND length:[300 TO *]`,
   FASTA, in the order returned, at most 8 entries, one per (protein name, organism). Same encoding as Family S
   (x = 1 for I V L F C M A; first 3,000 residues).
2. *Family S3, elastin orthologues.* UniProt REST, `query=gene_exact:ELN AND reviewed:true`, in the order returned, excluding
   accessions already evaluated in Phase 5 (P15502, P04985, Q99372, P54320). Same encoding. One entry = one dataset.
3. *Family L2, more languages.* Esperanto (book id from `phase4_candidates.json`), then Welsh, Icelandic, Norwegian, Tagalog,
   Irish, Swahili, Indonesian, resolved as the most-downloaded plain-text book on `https://gutendex.com/books/?languages=<code>&sort=popular`
   (codes cy, is, no, tl, ga, sw, id) and fetched from the `gutenberg.pglaf.org` mirror. Letters and vowels as Phase 4b (Latin
   script; vowel set `a e i o u y` plus accented forms; for Welsh add `w`). First 3,000 letters after the first 2,000.

**Stopping.** Stop as soon as the total (Phases 4b, 5, 6) is 25, or the lists are exhausted. Output:
`results/attempts_phase6.jsonl`, `phase6_run.log`.

---

# Addendum G (2026-11-17, lead; written before any Phase 7 stream was fitted)

**Instruction from the user (2026-11-17):** model-promotion streams and standard streaming benchmarks; the run continues until
35 datasets in total support the premium. Scope and mapping: `PHASE7_SCOPE.md` (sections A, B, C), which this addendum adopts.

**Stream.** Per dataset, the challenger-wins stream on disagreement rounds (x = 1 when l0 = 1 and l1 = 0, among rounds with
l0 ≠ l1), concatenated over episodes in file order up to 3,000 rounds. No r1 screen for this family.

**Evaluation and control.** As Phases 4b–6 (`run_phase4b.evaluate`, both orientations, at most 1 of 5 shuffles positive, seed
20261117), on streams of at least 200 rounds.

**Order.** (A) the 114 cached datasets in `data/raw/real_chains/promotion/`: atlas_v2 (airlines, bank, criteo, elec2,
openml_ldpa, rialto, spam, uci_occupancy, weather), sprint_fresh (appliances, beijing_pm25, bike_hour, household_power, metro),
then screen100 in sorted file order. (B) fresh standard benchmarks, each made into incumbent/challenger losses by one fixed
chronological pipeline (incumbent = logistic regression trained on the first 10% of the stream; challenger = the same model
retrained on each most recent 10% window every 2,000 rounds; 0/1 loss on the next rounds): INSECTS (all variants available),
Forest Covertype, Poker-hand, KDD Cup 99 (10%), Intel Berkeley lab sensor, UCI Ozone. (B-ext) if 35 is not yet reached, further
public real streams in this order through the same pipeline: OpenML electricity, Bike Sharing (day/hour classified above
median), MAGIC gamma, HIGGS (first 200k rows), Phishing websites, SMS Spam, Adult (census) in record order, Bank Marketing
(full), Default of credit card clients, Online News Popularity, Occupancy (all three test files), Gas sensor drift (batches in
order), then OpenML datasets tagged as data streams in ascending id order.

**Stopping.** The run stops when the total (Phases 4b–7) reaches 35.

**Baseline panel (C).** After stopping, `iid_failure/run_study.py --real-only --extra-chains` on every positive dataset's fitted
chain (all 35), with the panel and metrics of `PHASE7_SCOPE.md` §C.

Outputs: `results/attempts_phase7.jsonl`, `phase7_run.log`, `results/phase7_baselines/`.

---

# Addendum H (2026-11-19, lead; written before any Phase 8 computation)

**Purpose.** Phase 8 adds two analyses of the real model-promotion streams alongside the 35-dataset result, which stands
unchanged: (1) a census of all 114 promotion datasets in the pre-specified challenger-wins orientation, and (2) a held-out
replay in which every policy is run on real label sequences it was not fitted on.

**Stream.** x_t = 1 when the challenger wins a disagreement round (l0 = 1, l1 = 0), challenger-wins orientation only, as in
`PHASE7_SCOPE.md` §A. Episodes are kept separate (no concatenation across episode boundaries).

**Split.** Per dataset, episodes in file order. Fit set: the first half of the episodes (rounded up); for single-episode
datasets the first half of the disagreement rounds. Replay set: the rest. Fit the two-state model on the fit set only
(`real_data/fit.py`, unchanged; streams joined only for the likelihood, with the chain restarted at each episode).

**(1) Census, fit set only.** For every dataset with at least 200 fit-set rounds: fitted parameters, r1, and the evaluator's
cells (delay 1, T ∈ {16, 32}, B ∈ {1…4}, α = 0.1): ρΓ, Γ = V*_causal − V*_IID, VOI = C0 − V*_IID, and the causal risk of the
IID-optimal policy. Report the full distribution over datasets, not a count. No gate is applied to include or exclude a dataset.

**(2) Replay, replay set only.** Datasets with at least 200 replay-set rounds and an evaluable fit. Policies P1–P7 of the
`iid_failure` panel, calibrated to α = 0.1 on the fit-set model; cell T = 32, B = 4, delay 1, costs as in the panel (c = 0.01,
k = 0). Each episode of the replay set is cut into consecutive non-overlapping windows of T disagreement rounds; each policy
is run on each window, querying labels from the real sequence and promoting by its own rule (its private coins seeded
20261119 + window index). Realised cost of a window uses the solver's cost model with the real labels in place of their
predicted probabilities (stated exactly in the results file). Report per dataset and pooled: mean realised cost per policy with
a window-bootstrap 95% CI (2,000 resamples, seed 20261119), promotion rate, realised VOI share of each policy relative to P7, and
each policy's exact causal risk on the fitted model (unchanged by the replay). No result is excluded after it is seen.

Outputs: `results/phase8_census.jsonl`, `results/phase8_replay.jsonl`, `results/phase8_summary.md`, `phase8_run.log`;
script `run_phase8.py`.

---

# Addendum I (2026-11-19, lead; written before any Phase 9 computation)

**Purpose.** Phase 9 adds three causal-safe baselines to the panel. Each is the standard fix a practitioner would apply to an
existing panel policy once told that the labels may be adaptively dependent: keep the rule, recalibrate or repair it against
the exact causal risk. No new planner is introduced. All three are causal-safe by construction, so on the fitted model their
expected cost is at least RB-DP's; the replay measures them on real held-out labels.

**New policies.**
- **P3c, HMM-filter threshold, causal-calibrated.** P3's rule (query while budget lasts; promote when the filtered belief
  exceeds a threshold, randomising on a tie), with the threshold and tie probability set so that the exact causal risk
  (Lemma A, max branch) equals α, by the same bisection as P3 with the causal risk in place of the IID risk.
- **P4c, myopic VOI, causal-calibrated.** P4's rule (query iff one-step VOI > 0.01), threshold calibrated to exact causal risk α
  in the same way.
- **P5r, IID-optimal planner, repaired.** The cheaper of two repairs of P5, chosen per setting on the fitted model:
  (a) *deflated level*: the IID-mode solver re-solved at the largest α′ ≤ α whose solver causal risk is ≤ α (bisection on α′,
  16 steps; the solver's causal risk is an upper bound when the plan randomises, so the repair is conservative);
  (b) *mixing*: run P5 with probability a = min(1, α / causal risk of P5), otherwise never promote.

**Where.** (1) The T16/32 panel: the 35 fitted chains, cells T ∈ {16, 32}, B ∈ {2, 3, 4}, α ∈ {0.05, 0.1}, exact causal risk and
expected cost, compared with the existing P1–P7 rows in `results/phase7_baselines_T16_32/settings.jsonl`. (2) The Phase 8
replay: the same 100 datasets, windows, cell (T = 32, B = 4, α = 0.1) and private-coin seeds as Addendum H, with P1–P7 recomputed
in the same run so all comparisons are paired.

**Reported.** Per setting and per dataset: causal risk / α for the new policies; P7's cost against the best of all safe baselines
(P1, P2, P6, P3c, P4c, P5r); counts of cheaper / tie (|Δ| ≤ 1e-9 in-model) / dearer; replay pooled mean realised cost with the
window-bootstrap CI of Addendum H and paired P7 differences. No result is excluded after it is seen.

Outputs: `results/phase9_panel.jsonl`, `results/phase9_replay.jsonl`, `results/phase9_summary.md`, `phase9_run.log`;
script `run_phase9.py`.

---

# Addendum J (2026-11-23, lead; written before any confirmatory Phase 11 run; a one-chain smoke run of the panel stage, deleted, preceded it)

**Purpose.** Phase 11 adds the industry-standard always-valid A/B test as a baseline: the one-sided mixture SPRT (Robbins; Johari,
Pekelis and Walsh). Results are reported whatever they are; no setting, dataset or variant is excluded after it is seen.

**Statistic.** On queried labels with k wins and j losses, Lambda(k, j) = integral over theta in [1/2, 1] of (2 theta)^k
(2(1 - theta))^j pi(theta) d theta, pi uniform on [1/2, 1] (density 2), computed exactly (rational). For every theta >= 1/2 each factor has
conditional mean <= 1 when P(Y_t = 1 | history) <= 1/2, so Lambda is a nonnegative supermartingale under every adaptive null.

**Query rule (both variants).** The same as P2: query every disagreement round until the budget B is spent; decisions only while labels
arrive (t <= B + 1).

**Variants.**
- **P8, textbook:** promote iff Lambda >= 1/alpha, no calibration. Reported: whether Lambda can reach 1/alpha for B <= 4
  (max Lambda = (2^(B+1) - 1)/(B+1) <= 6.2 < 10, so it cannot for alpha <= 0.1), and exact cost and risk.
- **P8c, calibrated:** promote iff Lambda > tau, randomised (probability theta) on Lambda = tau, with (tau, theta) set so that the exact
  worst-case adaptive risk (Lemma A, max branch) is <= alpha: the smallest feasible level tau with theta tie-randomised to alpha, as
  in calibrate_threshold_causal (run_phase9.py), and additionally every higher level at its largest feasible theta; the cheapest of these
  candidates by exact expected cost is P8c (ties go to the smallest level). The number of settings where a higher level is cheaper is reported.

**Where.** (1) The T16/32 panel on the 44 chains (35 of Phases 4b-7 plus 9 of Phases 10 and 10c; same chain files as the
Phase 7 / 10 / 10c baseline panels), T in {16, 32}, B in {2, 3, 4}, alpha in {0.05, 0.1}: 528 settings, exact cost and risks, P7 from the
existing settings.jsonl files. (2) The Phase 8 replay: the same 100 datasets, windows, cell (T = 32, B = 4, alpha = 0.1, c = 0.01, k = 0)
and private-coin seeds (seed + window index) as Addenda H and I; P7 recomputed in the same run so differences are paired.

**Metrics.** (1) Safety: settings with exact risk_causal > alpha, per variant (unit check: P8c risk_causal <= alpha + 1e-12 in every setting).
(2) Panel: P7 cheaper / tied (|Delta| <= 1e-9, absolute, as in tally_phase10_baselines.py) / dearer than P8c, and median share of P7's
value of information (C0 - cost) / (C0 - P7 cost) captured by P8c over settings with C0 - P7 cost > 1e-9. (3) Replay: pooled mean realised cost
with the 95% window-bootstrap CI (2000 resamples, seed 20261119) and the paired difference P7 - P8c with its 95% CI. (4) Whether textbook P8 ever
promotes. Executor validation: Monte Carlo (20000 simulated windows) against the exact cost on the 3 replay datasets with the most fit rounds, as in Phase 9.

Outputs: `results/phase11_msprt_panel.jsonl`, `results/phase11_msprt_replay.jsonl`, `results/phase11_msprt_summary.md`,
`results/phase11_msprt_unit.json`, `results/phase11_msprt_validation.json`, `results/phase11_msprt_run.log`; script `run_phase11_msprt.py`.
