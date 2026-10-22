# WRDS finance data acquisition

`scripts/acquire_wrds_finance_panels.py` exports the daily Fama–French factors,
CRSP daily Treasury risk-free series, annual Compustat North America fundamentals,
and (by default) CCM CRSP–Compustat link history for 2000–2025. It runs in an
authenticated WRDS Cloud Python/Jupyter environment, streams compressed CSV
parts, records query and file hashes, and refuses to overwrite existing output.
The WRDS database catalog is checked at runtime; a missing or unsubscribed table
fails with a clear error rather than substituting data.

## Run in WRDS Cloud

1. In JupyterLab, upload `acquire_wrds_finance_panels.py` from this repository.
   Do not upload the data archive into GitHub.
2. Run a one-year pilot first:

   ```python
   %run acquire_wrds_finance_panels.py --start-year 2025 --end-year 2025 --output ~/shiftlab_wrds_finance_pilot
   ```

3. Confirm `factors/`, `treasury/`, `compustat/` and `ccm_links/` each have a
   manifest and matching compressed parts. If WRDS reports a table is missing or
   not subscribed, confirm its exact schema/table in **Get Data** and request the
   institution administrator to enable it. Do not guess a replacement table.
4. Run the full study window in a new output directory:

   ```python
   %run acquire_wrds_finance_panels.py --start-year 2000 --end-year 2025 --output ~/shiftlab_wrds_finance_2000_2025
   ```

The default is 2000–2025 and the default chunk size is 200,000 rows. A failed
partition is left in place for inspection. Fix or remove it only after reviewing
the failure, or use a fresh `--output` path for a clean retry. A completed output
directory is not overwritten.

### Included extracts

- `ff.factors_daily`: market, size, value, profitability, investment, momentum
  (when present), and risk-free factor fields. The conventional WRDS values are
  percent units; convert consistently before combining with decimal CRSP returns.
- `crsp_a_treasuries.tfz_dly_rf2` (with a documented table-name fallback): the
  daily risk-free series and native fields. The exact fields are discovered from
  the subscribed WRDS catalog and saved in the manifest.
- `compd.funda` (with a schema fallback): annual fundamentals keyed by `gvkey`
  and `datadate`; when available, the script applies the standard industrial,
  consolidated, domestic, standardized-format filters. It retains `rdq` when
  present so analysis can impose a conservative reporting-availability rule.
- `crsp.ccmxpf_lnkhist` (with a table-name fallback): CRSP–Compustat link
  history overlapping the study period. Retain `linktype`, `linkprim`, and the
  effective dates when joining; resolve link priority and date validity in the
  analysis code rather than merging on current ticker or CUSIP alone.

Compustat annual files are not inherently point-in-time snapshots. The script
does not claim that `datadate` means a value was publicly available that day;
use `rdq` (or a point-in-time fundamentals product, if subscribed) to prevent
look-ahead. Compustat values retain source units. The factors/Treasury data are
benchmarks or controls; they are not needed to form the basic next-day CRSP target.

## Optional TAQ extraction

TAQ exports are deliberately opt-in. Use a small symbol list and a short date
window first; one request may cover at most 365 calendar days. TAQ is tick-level,
so even a few sessions can create large files. The script preserves the available
trade/quote fields and does not filter sale conditions or quote modes. Define and
document those filters in the study protocol before computing microstructure
measures.

Upload a UTF-8 text file with one TAQ `sym_root` per line (comments may begin
with `#`), then run for a limited window, for example:

```python
%run acquire_wrds_finance_panels.py --skip factors --skip treasury --skip compustat --skip-ccm-links --taq-kind both --taq-start 2025-01-02 --taq-end 2025-01-03 --taq-symbols-file ~/shiftlab_symbols.txt --output ~/shiftlab_taq_pilot
```

Date arguments include both the start and end calendar dates. Use the TAQ table
dictionary to confirm the available symbol/date and condition fields for your
subscribed vintage. Do not interpret the current ticker as a point-in-time CRSP
identifier; build a time-valid ticker mapping if you expand the universe.

## Verify manifests in WRDS Cloud

Run this after extraction to check part-file sizes and SHA-256 hashes against all
manifests, without displaying any observations:

```python
from pathlib import Path
import hashlib, json

root = Path.home() / "shiftlab_wrds_finance_2000_2025"
problems = []
for manifest_path in root.rglob("manifest.json"):
    manifest = json.loads(manifest_path.read_text())
    for item in manifest["files"]:
        path = manifest_path.parent / item["name"]
        if not path.is_file() or path.stat().st_size != item["bytes"]:
            problems.append(str(path))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            problems.append(str(path))
print({"manifests": len(list(root.rglob("manifest.json"))), "problems": problems})
```

Download/export the completed directory only through a WRDS-approved route and
store it in the local ignored `data/raw/licensed/` area. Do not commit these files
or send observations to an LLM. Record the script hash and manifest summary in
the study notes.

## WILDS and Criteo are separate sources

They are not fetched from WRDS. WILDS has an existing ShiftLab adapter; try the
CivilComments pilot locally with:

```powershell
uv sync --extra wilds
uv run python scripts/download_data.py --dataset wilds --config configs/data/public/wilds.yaml --execute
```

The repo's acquisition audit records a certificate failure at the official
CivilComments host; TLS verification remains enabled. Criteo has a configured
adapter and command:

```powershell
uv run python scripts/download_data.py --dataset criteo --config configs/data/public/criteo.yaml --execute
```

The Criteo adapter requires a source-verified delay unit before processing. Its
official archive endpoint returned 404 in the latest recorded check, so retrying
may still fail until the publisher restores the file or provides an authorized
local export. Do not substitute a different Criteo dataset without changing the
study target and availability protocol.
