# First baseline results

Executed locally on CPU on 2026-10-19. Three data seeds (11,22,33), four controls, 72 method/stream evaluations. These exploratory results are not confirmatory evidence.

| Paper | Method | Concept-shift metric | Mean |
|---|---|---|---:|
| 1 | frozen | mse | 1.5550 |
| 1 | frozen | coverage | 0.4937 |
| 1 | frozen | objective | 1321.7310 |
| 2 | fixed | mse | 1.5550 |
| 2 | fixed | coverage | 0.4937 |
| 2 | fixed | objective | 1321.7310 |
| 2 | rolling | mse | 1.5550 |
| 2 | rolling | coverage | 0.8871 |
| 2 | rolling | objective | 1321.7310 |
| 3 | frozen | mse | 1.5550 |
| 3 | frozen | coverage | 0.4937 |
| 3 | frozen | objective | 1321.7310 |
| 3 | periodic | mse | 0.5301 |
| 3 | periodic | coverage | 0.7961 |
| 3 | periodic | objective | 500.5516 |
| 3 | triggered | mse | 0.3467 |
| 3 | triggered | coverage | 0.8424 |
| 3 | triggered | objective | 314.7241 |

Rolling calibration substantially improves observed coverage in this grid by widening intervals. This is empirical performance, not a nonstationarity coverage theorem. Triggered adaptation improves the objective here, but thresholds and intervention counts are not compute matched. Larger independent replication is required before claiming dominance.

## Run provenance

- `20261019T080503-ab0eefe98d`: paper 1, none, status complete; config SHA256 `218ccede541236348ad03857f83e7029f922224781d20ba48f68e4dce70bc3e8`.
- `20261019T080505-19aa606a9e`: paper 1, benign, status complete; config SHA256 `13b4d2ec4045f597b219be569a77daac06f599ec249dd027eb163928e224f322`.
- `20261019T080508-45b78fdbf7`: paper 1, concept, status complete; config SHA256 `4c8c9dec51e7fd3f348b0513cfb9dc4424593273b9a5fc839965af223cbb3beb`.
- `20261019T080510-023095567d`: paper 1, variance, status complete; config SHA256 `ad528f5233a6eaaa888884060d7aeca0a1f34360e3eee976ce7ad3ed9354b8c8`.
- `20261019T080512-f32668b12a`: paper 2, none, status complete; config SHA256 `00188c71b35f8f624e54c3734e513e1a2369b6418c8c4829f2670f01ed4e14d5`.
- `20261019T080515-c7e14d0bd4`: paper 2, benign, status complete; config SHA256 `531694efee4aeec45f4d85a9f32bfdb98bd6295d09a05a29b12fc978636020bd`.
- `20261019T080519-b77854411b`: paper 2, concept, status complete; config SHA256 `265456a5085354ca7abcf78cab53f5ebada918051a0fa7ad5c8641e78cb179c4`.
- `20261019T080520-3c146ffd91`: paper 2, variance, status complete; config SHA256 `3a64dda3b2c666ac8124149ad74385518aeb996060603f399b2c26b13d75f7be`.
- `20261019T080521-5f6812c5f3`: paper 3, none, status complete; config SHA256 `3a208ec98ad0b358ebbf5421a59233120aed7632fab5f2f7d3d62828f31924f9`.
- `20261019T080523-103c895dbb`: paper 3, benign, status complete; config SHA256 `a990f5c8c6f0fe2ad60e07cd3f588393380eff38ddc3d739cb16ee5a28d771fd`.
- `20261019T080524-905e7e03d1`: paper 3, concept, status complete; config SHA256 `23a098e62d4c1eecc018cb8011835dc9bcbd4e7bcc95f4c5dd0f6bebfdf5d77c`.
- `20261019T080526-3ad5b015b6`: paper 3, variance, status complete; config SHA256 `947a0b282f84006aa3c1f7191b51ffcf7cc26d3c1eedd48f7c17059351d1a809`.

Git revision is null because this newly initialized repository has no first commit. Configurations, dependency lock, DGP parameters and seeds are saved; a future committed revision is needed for full source provenance.

Local full results: `outputs/all_metrics.csv` and `outputs/summary.csv`. The CSV summary carries protocol hashes so different configurations are never pooled. Bootstrap intervals resample independent streams; three-seed intervals are unstable.
