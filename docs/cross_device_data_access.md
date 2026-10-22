# Cross-device access to ShiftLab data

## Keep code in Git and licensed records out of Git

The private `nl2992/shiftlab` GitHub repository is the source of truth for code,
protocols, and reproducibility instructions. The repository ignores `data/raw/`,
`data/interim/`, `data/processed/`, and `data/manifests/`. Keep WRDS observations,
archives, and their detailed manifests outside Git, including Git LFS. A private
repository still stores data with a third-party hosting provider and is not a
license exception.

WRDS use is governed by the institution's subscription agreement and any
additional institutional restrictions. Columbia has confirmed that this private
repository is permitted for the study's data. Never share WRDS credentials. See
the [WRDS Terms of Use](https://wrds-www.wharton.upenn.edu/users/tou/).

## Recommended setup

1. Clone/pull the private repository on each machine into a normal local folder
   (not a folder that synchronizes the `.git` directory):

   ```powershell
   git clone https://github.com/nl2992/shiftlab.git
   # Later:
   git -C .\shiftlab pull --ff-only
   ```

2. The existing WRDS archive files are attached to the private GitHub release
   [`data-2026-10-22`](https://github.com/nl2992/shiftlab/releases/tag/data-2026-10-22).
   No data query needs to be rerun. On the second laptop, after signing into the
   same GitHub account (`gh auth login` if needed), download all four archives:

   ```powershell
   $bundle = Join-Path $env:TEMP 'shiftlab-wrds-archives'
   New-Item -ItemType Directory -Force $bundle | Out-Null
   gh release download data-2026-10-22 --repo nl2992/shiftlab --pattern '*.tar' --dir $bundle
   gh release download data-2026-10-22 --repo nl2992/shiftlab --pattern '*.tar.gz' --dir $bundle
   ```

   Extract into a fresh local clone. These commands use ASCII-only paths to
   avoid Windows `tar.exe` path-encoding issues:

   ```powershell
   $repo = 'C:\work\shiftlab'
   $crsp = Join-Path $repo 'data\raw\licensed\crsp'
   $finance = Join-Path $repo 'data\raw\licensed\wrds_finance_2000_2025'
   New-Item -ItemType Directory -Force $crsp, $finance | Out-Null
   Push-Location $crsp
   tar.exe -xf (Join-Path $bundle 'shiftlab_crsp_ciz_2000_2025_verified.tar')
   Pop-Location

   $raw = Join-Path $repo 'data\raw'
   New-Item -ItemType Directory -Force $raw | Out-Null
   Push-Location $raw
   tar.exe -xzf (Join-Path $bundle 'shiftlab_other_raw_2026-10-22.tar.gz')
   Pop-Location

   Push-Location $repo
   tar.exe -xzf (Join-Path $bundle 'shiftlab_phase1_derived_2026-10-22.tar.gz')
   Pop-Location

   Push-Location $finance
   tar.exe -xf (Join-Path $bundle 'shiftlab_wrds_finance_2000_2025.tar')
   Pop-Location
   ```

   GitHub's release-asset metadata records SHA-256 digests for all files. The
   verified digests are:

   | Archive | Size | SHA-256 |
   | --- | ---: | --- |
   | `shiftlab_crsp_ciz_2000_2025_verified.tar` | 1,353,994,240 bytes | `120b36a09b219736735b2dfc653cbca509492d6ff5c69e2255fe6be42dd4df4f` |
   | `shiftlab_wrds_finance_2000_2025.tar` | 20,746,240 bytes | `d8d59154232bd9fb97677a0fe25da6fa8faeba1e19a535afb71862772b53c184` |
   | `shiftlab_other_raw_2026-10-22.tar.gz` | 1,424,666,278 bytes | `1d6fa3075317803f92a8b76573585ba47c51759d4abb14393306981b08b1c7c4` |
   | `shiftlab_phase1_derived_2026-10-22.tar.gz` | 138,255,411 bytes | `5e6855333825da2d058bcac03988c93022c5a3b0468fc02929fd4d7922447bac` |

   Each archive is below GitHub's 2 GiB per-release-file limit. Access remains
   restricted to users who can access the private repository.

3. The private release is the cross-device copy of the raw data. The current
   machine's files remain under:

   ```text
   OneDrive/桌面/ICML/shift-research-starter/data/raw/
   ```

   The Columbia agreement has been confirmed for this private-repository
   transfer. Keep the repository private and do not redistribute these files.

4. From the local clone, run the analysis and validation commands in the repo's
   README. The local `data/raw/` ignore rule prevents accidental data commits;
   confirm with `git check-ignore -v data/raw/licensed/...` before any commit.

## Data available for this study

The release contains the CRSP CIZ 2000–2025 extract, WRDS daily factors,
Treasury, Compustat, CCM link history, other acquired raw sources, processed
real-source datasets, synthetic scenario datasets and oracle outputs, run
outputs, and acquisition manifests. Phase 1 reports are version-controlled in
Git. Extraction manifests and per-part checksums are included in the archives.
The synthetic collection contains 46 stored versions: the original 38 plus the
eight seed-42 smoke cases regenerated at commit `2c915c1` with full code-commit
and file-checksum provenance.
The 90-day Criteo Sponsored Search archive remains unavailable. CriteoPrivateAds is a separate
acquired source; its 288 source files and checksum manifest are added as flat assets on the release.
After downloading `source_manifest.json` and `part-*.parquet` into an inbox, restore the original
day-partitioned layout with:

```powershell
gh release download data-2026-10-22 --repo nl2992/shiftlab --pattern 'source_manifest.json' --dir $inbox
gh release download data-2026-10-22 --repo nl2992/shiftlab --pattern 'part-*.parquet' --dir $inbox
uv run python scripts/restore_criteo_private_ad_release.py --inbox $inbox
```

The restore script verifies every size and SHA-256, puts files under the ignored raw-data tree,
and writes download receipts so the pinned acquisition command recognizes them locally. WILDS
CivilComments was acquired from its pinned raw mirror. Its raw Parquet file and receipt are also
release assets; download and restore them with:

```powershell
gh release download data-2026-10-22 --repo nl2992/shiftlab --pattern 'train-00000-of-00001.parquet' --dir $inbox
gh release download data-2026-10-22 --repo nl2992/shiftlab --pattern 'train-00000-of-00001.parquet.receipt.json' --dir $inbox
$wildsRaw = Join-Path $repo 'data\raw\wilds\civilcomments-hf\raw'
New-Item -ItemType Directory -Force $wildsRaw | Out-Null
Move-Item -LiteralPath (Join-Path $inbox 'train-00000-of-00001.parquet') -Destination $wildsRaw
Move-Item -LiteralPath (Join-Path $inbox 'train-00000-of-00001.parquet.receipt.json') -Destination $wildsRaw
```
The CRSP raw extracts still need the joins and date-availability rules described
in `crsp_study_execution.md` before the study panel is complete.

WRDS's current policy also says not to load retrieved WRDS data into LLMs unless
the vendor permits a protected setup; avoid attaching observations to support
requests. Aggregate counts and error messages without data rows are suitable for
troubleshooting.
