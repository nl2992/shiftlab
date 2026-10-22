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
acquired source; all 288 source files and its checksum manifest are published as flat assets on the
private release. The full 295-asset release inventory passed size and SHA-256 comparison.
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

## Exceptionally large datasets

Keep large data out of Git and use a data host, with a small versioned manifest in the repository
that records the source, immutable revision, license, expected files, sizes, and checksums. The
study scripts then read the verified files from the normal ignored `data/raw/` path. For private or
licensed data, use an access-controlled host approved by the relevant agreement; the current WRDS
archives stay on the private GitHub release. A private object-store bucket (S3-compatible, GCS, or
Azure Blob) is a good home for future one-off files larger than release assets, but none is
configured for this project yet.

For the optional Criteo 1TB Click Logs benchmark, a second hosted copy is unnecessary:
Criteo's public Hugging Face repository currently reports 4.37 billion rows and a 276 GB
Parquet representation under CC BY-NC-SA 4.0. Pin the repository revision and stream the
dataset or read selected Parquet shards; this avoids downloading all files to both laptops.
The repository was pinned at `e11d69ae913b16cdd7387706a2133def0fdc6ced` on 2026-10-22.
For example, Hugging Face Datasets supports an iterable stream:

```python
from datasets import load_dataset

click_logs = load_dataset(
    "criteo/CriteoClickLogs",
    split="train",
    streaming=True,
    revision="e11d69ae913b16cdd7387706a2133def0fdc6ced",
)
```

This click-only benchmark is useful for scale and classification checks but does not provide
delayed conversion feedback. A ShiftLab source adapter should map the stream in bounded batches
and record the pinned revision and selected rows/shards in its manifest. For large private
sources without an approved public host, an access-controlled object store remains the option;
Cloudflare R2 currently lists standard storage at $0.015/GB-month with no egress charge, subject
to account setup and current pricing.

CriteoPrivateAds already has a suitable public upstream host: its pinned
[Hugging Face dataset revision](https://huggingface.co/datasets/criteo/CriteoPrivateAd/tree/343645889b157f104ac23d0d07afa6a18115eb30).
On another laptop, clone the repo and run the existing downloader to fetch the same 288 Parquet
files directly into the study's raw-data path. It checks the pinned revision and each file's
publisher SHA-256 before accepting it. This avoids downloading 288 separate GitHub release assets;
the private release remains available as a mirror.

```powershell
cd C:\work\shiftlab
uv sync
uv run python scripts/acquire_criteo_private_ad.py --workers 4
```

The download is about 31.7 GiB, so allow that much free disk space plus room for derived outputs.
For another laptop, the same script is restart-safe and can reuse verified local files. The source
manifest is written to `data/raw/criteo_privatead/source_manifest.json`. The downloader's revision
pin and checksums make this a reproducible source for the study, rather than a mutable "latest"
snapshot. Hugging Face documents revision-pinned repository downloads in its
[download guide](https://huggingface.co/docs/huggingface_hub/en/guides/download).

The CRSP raw extracts still need the joins and date-availability rules described
in `crsp_study_execution.md` before the study panel is complete.

WRDS's current policy also says not to load retrieved WRDS data into LLMs unless
the vendor permits a protected setup; avoid attaching observations to support
requests. Aggregate counts and error messages without data rows are suitable for
troubleshooting.
