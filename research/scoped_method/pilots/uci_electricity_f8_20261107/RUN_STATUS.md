# UCI Electricity F8 profile-screen execution record

## Source receipt

- Source: UCI Machine Learning Repository dataset 321, `ElectricityLoadDiagrams20112014`,
  DOI `10.24432/C58C86`, CC BY 4.0.
- Download URL: `https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip`.
- Retrieved 2026-11-07 UTC. Archive size: 261,335,609 bytes.
- SHA-256: `f6c4d0e0df12ecdb9ea008dd6eef3518adb52c559d04a9bac2e1b81dcfc8d4e1`.
- `unzip -t` passed for `LD2011_2014.txt` and the archive metadata file.
- Raw archive is stored only under ignored `data/raw/uci_electricity_f8_20261107/` and is not
  tracked by Git.

## Execution notes

The first source parse exposed the documented decimal-comma encoding; no target metrics were
computed. The next parser pass detected that the first source row is 2011-01-01 00:15 and therefore
adjusted the fixed train/development row boundary to 35,039 / 35,136 rows. A timestamp-only
boundary check showed 2011-12-31 23:45 and 2012-12-31 23:45 at the declared endpoints. No 2013 or
2014 row values were processed.

The first model-screen process was interrupted during a HistGradientBoosting fit after sampling
showed 52 OpenMP workers active on one client and no progress for over two minutes. It produced no
`DATASET_PROFILE.json` and no reported profile results. The frozen model and data are unchanged;
the runner now limits OpenMP to one worker per fit to avoid oversubscription. This is an execution
setting only.

A separate boundary diagnostic printed only the timestamp strings at the first/last train and
development rows and the immediately following boundary row (`2013-01-01 00:00:00`). It did not
parse or report that row's client values. The full ZIP CRC check validated archive integrity only;
no 2013–2014 values were used in feature construction, fitting, or profile metrics.

## Current status

The frozen screen completed using the 2011-fit / 2012-profile partition only. Of 370 listed clients,
158 met the train-only history/class eligibility rule. Exactly one client (`MT_330`) met the F8
profile: disagreement rate 2.399%, challenger accuracy on disagreements 87.663%, with 17
nonoverlapping 2,000-event development blocks. The predeclared minimum is 20 matching clients, so
the screen gate **failed**. No economic policy replay was run and 2013–2014 outcomes remain unopened.

## Reproduction and artifacts

```bash
uv run ruff check scripts/sota_sprint/uci_electricity/profile_f8.py
uv run python scripts/sota_sprint/uci_electricity/profile_f8.py
```

Profile output: `DATASET_PROFILE.json`. Source archive SHA-256 is recorded in that JSON and above.
The original attempt was interrupted during one OpenMP-oversubscribed model fit before it emitted
any metrics; the completed single-thread-per-fit run reproduced this profile screen without changing
the frozen estimator or data split.

## Decision

This dataset does not currently support a generalized F8 policy evaluation under the frozen minimum
support rule. Do not open 2013–2014 for this candidate and do not relax the profile gate after seeing
the one matching client. The result is a source-feasibility and profile diagnostic, not an economic
failure or confirmation result. The broader ShiftLab research goal remains open.
