# Baseline preservation manifest

Fetched `origin` on 2026-10-29. Base `origin/main`: `ec42a2da9fdf59a6cf26970fb19aa9d5fb8973cc`.
Branch: `research/risk-preserving-switching-approx-2026-10-29`.
Worktree: `C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-risk-approx-2026-10-29`.
Toolkit-only commit `cfd0c00` was carried from the earlier isolated setup branch.

The exact user brief is preserved byte-for-byte in `RESEARCH_BRIEF.md`.
`baseline_manifest.json` records Git blob IDs, byte lengths and SHA-256 hashes
for 16 tracked reference files, including the required mathematical
notes, exact solver sources/tests and tracked outputs in selected anchor folders.
Hashes use Git blob bytes, avoiding Windows checkout line-ending differences.
This is an integrity baseline, not a claim that any theorem or numerical result
has been independently reproduced in this worktree.

Reference values to verify: T6 cost `461083/160000`, risk `1/10`;
T7 full/decomposed equality; T8 generic-builder cap and reduced-only completion.
No independent T8 full-oracle certificate is claimed.

Ignored data, historical source caches, environments and untracked experiment
outputs are absent unless separately restored with provenance. No holdout access,
seed allocation, experiment or solver execution was needed for branch adoption.

Preservation checks compare every tracked path at the base with branch HEAD,
allowing only the explicitly changed project guidance/tooling files. Run targeted
reference tests after creating a local environment, before candidate coding.
