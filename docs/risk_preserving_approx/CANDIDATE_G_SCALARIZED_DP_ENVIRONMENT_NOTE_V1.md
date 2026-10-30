# Candidate G scalarized-DP runtime environment note

This is a post-run provenance supplement for
`candidate_g_scalarized_dp_screen_v1.json`. The screen's runner did not record
runtime/library versions in its result payload, despite the protocol requesting
them. The original result and its hash remain unchanged.

The branch environment was inspected on 2026-10-30 with `uv run python`:

- Python `3.13.1`
- psutil `7.2.2`
- NumPy `2.5.4`
- SciPy `1.18.1`
- `uv.lock` SHA-256 `a50f921c44e4f37d0e746f9a2680c8ec823d21a1f6a8901406620e1ca55c44fd`

The runner uses exact `Fraction` arithmetic for belief transitions, Bellman
values, alternative costs and risk recursions. It does not call a numerical LP
solver. This inspection occurred after the screen, so these versions are
reproducibility context rather than a contemporaneous process capture. The
result's runner snapshot, configuration and source hashes remain the authoritative
record for the execution itself.
