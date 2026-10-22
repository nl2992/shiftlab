# Reproducible Folktables state/year panels

```powershell
# Preview all five tasks without acquiring data.
python -m uv run python scripts/folktables_suite.py --config configs/data/public/folktables_suite.yaml
# Execute the selected panel.
python -m uv run python scripts/folktables_suite.py --config configs/data/public/folktables_suite.yaml --execute
# A single-task version uses the ordinary acquisition CLI.
python -m uv run python scripts/download_data.py --dataset folktables --config configs/data/public/folktables_panel.yaml --execute
```

The initial panel uses CA, NY, TX, FL and NJ, surveys 2017 and 2018, and ACSIncome,
ACSEmployment, ACSPublicCoverage, ACSMobility and ACSTravelTime. It downloads the ten
official person-survey Census ZIPs using retries, byte caps and immutable receipts,
then streams the CSV members without extraction. The maximum compressed file size is
80 MB and maximum uncompressed member size is 600 MB; CSV reads use 20,000-row chunks.
Individual task versions reference only the
requested source archives, not unrelated cached files. Publisher SHA256 digests are
not supplied here: receipt checksums establish local integrity, not independent authenticity.

A seeded Bernoulli sample retains 5% of source records before applying each official
task filter. Each state/year has its own deterministic random stream; results are
stable across processing chunk sizes and common source records are paired across tasks.
The full official archives remain available locally. Source-row IDs remain stable and
unique across chunks. The recorded probability is a sampling parameter, not an assertion
that exactly 5% of every demographic stratum is retained.

The adapter invokes installed Folktables' official preprocessing, target transform,
group mapping and feature postprocessing. An immutable `acs_protocol.json` stores
task features, target, group, package version and function source definitions. Official
missing-value feature coding is retained; metadata names the originally missing source
feature fields so this postprocessing is explicit. Age, sex, race and Hispanic-origin
codes are preserved in metadata where present. Original PWGTP survey weights stay aligned
with task-filtered observations. They are not divided by the extra Bernoulli sampling
probability: descriptive weighted rates are ratios; population-total estimation would
need the additional sampling design and suitable variance calculations. No IID or
complex-survey confidence guarantees are inferred from these summaries.

Annual records have unknown within-year order. No individual event, prediction, release,
or outcome-availability time is assigned, and standard stream splits stay unassigned.
The version's protocol defines four explicit retrospective comparison designs:
within-state across years, across states in the same year, pooled cross-year, and joint
new-state/new-year. These domain selectors are not fabricated online changepoints or
random person-level train/test splits. Fitting must use only the designated training
domains; cross-year observations are not guaranteed independent individuals or households.

The suite writes per-task/domain counts and unweighted/survey-weighted target frequencies,
preserving partial completion after each task. `validation.json` records the exact
versions, their source checksums and protocols. Raw ZIPs and processed rows remain ignored
by Git; aggregate reports and configurations are tracked.

Run `python -m uv run python scripts/folktables_diagnostics.py` after acquisition to
execute the four comparison designs across all five tasks. `comparison_evidence.csv`
records per-domain apparent-training and held-out metrics, including weighted accuracy
and decision loss under an explicitly imposed 5:1 false-negative:false-positive cost.
The logistic model and preprocessing are fit only on the designated training domains;
there is no later-domain tuning. `comparison_protocol.json` records exact input versions,
manifest hashes, script hash, utility and weighting caveats. The plot summarizes the
mean held-out domain weighted accuracy within each comparison kind. These are retrospective
descriptive diagnostics: no survey-design or extra Bernoulli-sampling uncertainty is
estimated, and population, coding, selection and label-composition effects may confound
the comparison. No online detector or causal shift attribution is evaluated.

Source definitions: [Folktables](https://github.com/socialfoundations/folktables),
[Census ACS PUMS](https://www.census.gov/programs-surveys/acs/microdata.html).

The panel now includes 2017–2019 for all five tasks and all five states. Census 2019
renamed `RELP` to `RELSHIPP` and `JWTR` to `JWTRNS`; the adapter selects the year-specific
source columns, records the aliases and native field names in each version's protocol,
and preserves the 2019 category codes as released. See `data/reports/folktables_compatibility.json`
and the [Census 2019 PUMS ReadMe](https://www2.census.gov/programs-surveys/acs/tech_docs/pums/ACS2019_PUMS_README.pdf).
The renamed fields' category codes are not harmonized across years. Source categorical
coding and population definitions may still differ, so cross-year domain comparisons do
not establish a causal drift mechanism.
