# Protocol v1 source-integrity stop

Protocol v1 required the EIA electricity bulk archive SHA-256
`3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f`, retrieved 2026-10-20.
The current official download at that URL returned a different 2026-11-07 artifact:

- Bytes: `701813969`
- SHA-256: `d1e8e1469237dbd78e15b0e1b4075524ada2cd08f1e255cc14517c4e05fc1ade`
- Archive member: `EBA.txt`

The frozen checksum gate failed. No model predictions, losses, policy decisions, profile statistics,
or 2026 performance metrics were computed from this archive. Inspection was limited to download
receipt, file hash, and archive member listing. The artifact is not used for the EIA-930 model-pair
evaluation; the corrected protocol v2 names the EIA-930 six-month balance CSV files and freezes
their individual checksums before scoring.

The archive was removed from the local worktree after this stop; the checksum and receipt details
remain here. It was never added to Git.
