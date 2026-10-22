# Cross-device access to ShiftLab data

## Keep code in Git and licensed records out of Git

The private `nl2992/shiftlab` GitHub repository is the source of truth for code,
protocols, and reproducibility instructions. The repository ignores `data/raw/`,
`data/interim/`, `data/processed/`, and `data/manifests/`. Keep WRDS observations,
archives, and their detailed manifests outside Git, including Git LFS. A private
repository still stores data with a third-party hosting provider and is not a
license exception.

WRDS terms say use is governed by the institution's subscription agreement and
any additional institutional restrictions; they also restrict reproducing and
distributing proprietary material. Confirm with the Columbia WRDS administrator
that the intended encrypted storage/sync service and personal second device are
permitted before syncing licensed files. Never share WRDS credentials. See the
[WRDS Terms of Use](https://wrds-www.wharton.upenn.edu/users/tou/).

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
   same GitHub account (`gh auth login` if needed), download both archives:

   ```powershell
   $bundle = Join-Path $env:TEMP 'shiftlab-wrds-archives'
   New-Item -ItemType Directory -Force $bundle | Out-Null
   gh release download data-2026-10-22 --repo nl2992/shiftlab --pattern '*.tar' --dir $bundle
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
   Push-Location $finance
   tar.exe -xf (Join-Path $bundle 'shiftlab_wrds_finance_2000_2025.tar')
   Pop-Location
   ```

   GitHub's release-asset metadata records SHA-256 digests for both files. The
   CRSP archive is 1,353,994,240 bytes and the finance archive is 20,746,240
   bytes; each is below GitHub's 2 GiB per-release-file limit. Access remains
   restricted to users who can access the private repository.

3. If the Columbia-approved storage service permits it, sync only the licensed
   data directory through that service. The current machine's files are under:

   ```text
   OneDrive/桌面/ICML/shift-research-starter/data/raw/licensed/
   ```

   On the second machine, make the approved synced folder available offline,
   then connect it to the local clone's ignored `data/raw/licensed` path. For
   example, after replacing the paths with the actual local folders:

   ```powershell
   New-Item -ItemType Directory -Force .\shiftlab\data\raw | Out-Null
   New-Item -ItemType Junction `
     -Path .\shiftlab\data\raw\licensed `
     -Target 'C:\ApprovedSync\ShiftLab\licensed'
   ```

   Do not use this OneDrive route until the institution confirms that storage
   location is permitted for the WRDS products in use. If it is not, use the
   institution's approved encrypted research storage or rerun the WRDS Cloud
   acquisition under your own authorized WRDS login on the other machine.

4. From the local clone, run the analysis and validation commands in the repo's
   README. The local `data/raw/` ignore rule prevents accidental data commits;
   confirm with `git check-ignore -v data/raw/licensed/...` before any commit.

## Data available for this study

The local `data/raw/licensed/` tree currently contains the CRSP CIZ 2000–2025
extract and the WRDS daily factors, Treasury, Compustat, and CCM link-history
extracts. Extraction manifests and per-part checksums are retained with those
files locally. The raw extracts still need the joins, date-availability rules,
and processed ShiftLab dataset described in `crsp_study_execution.md`.

WRDS's current policy also says not to load retrieved WRDS data into LLMs unless
the vendor permits a protected setup; avoid attaching observations to support
requests. Aggregate counts and error messages without data rows are suitable for
troubleshooting.
