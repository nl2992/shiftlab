# WP2 H5: historical cached-real sensitivity

This is a post hoc descriptive extension of H5 to nine cached sources from Atlas v2. These streams
were exposed in earlier work; this is not fresh validation. The run used 3 seeds per episode,
seed base `2026110901`, T=2000, B=200, c_q=0.05, c_s=5, alpha=0.05, and registered source delays.
The run contains 504 episode-seed jobs (2,520 policy episode-seed records) in the gitignored output directory
`outputs/sprint2/WP2/cached_real_h5/`; the run manifest records hashes and settings.

As in H5, contrasts are A5b−QSG and D5−D2. We retain episodes with positive realized mean
advantage (`ep_adv > 0`) across the seed replicates. This selection uses evaluation outcomes and is
retrospective. We first pair policies within source, episode and seed; average seeds within episodes,
then episodes within each source. The reported point estimates equally weight the nine dataset/source
clusters. Percentile intervals resample those nine sources (10,000 draws). They quantify source
heterogeneity in this selected cached panel, not uncertainty over a population of new datasets.

Positive net and delay differences mean the first policy in the pair has higher cost and later first
promotion. Negative label and promotion differences mean fewer labels/promotions for the first policy.

| Contrast | Positive episodes / sources | Δ net [95% source-cluster CI] | Δ delay [95% CI] | Δ labels [95% CI] | Δ promotion rate [95% CI] |
|---|---:|---:|---:|---:|---:|
| A5b−QSG | 126 / 9 | +76.91 [22.63, 154.10] | +721.66 [384.31, 1089.34] | −10.08 [−18.43, −3.11] | −0.425 [−0.633, −0.225] |
| D5−D2 | 126 / 9 | +73.96 [19.80, 150.93] | +573.72 [359.08, 804.24] | +48.95 [28.08, 71.59] | −0.330 [−0.489, −0.185] |

The aggregate contrasts show higher net cost and later deployment for both certificate-bearing
policies in this selected panel. A5b uses fewer labels; D5 uses more. These results do not establish
a general dependence-robustness cost law: all policies share one fixed economic contract, episodes
were selected using realized advantage, and the nine cached sources are not independent new data.

## Reproduction

```sh
uv run python scripts/sota_sprint/wp2_run.py --sources 'file:data/atlas_v2_losses/rialto.npz:rialto,file:data/atlas_v2_losses/openml_ldpa.npz:openml_ldpa,file:data/atlas_v2_losses/airlines.npz:airlines,file:data/atlas_v2_losses/criteo.npz:criteo,file:data/atlas_v2_losses/bank.npz:bank,file:data/atlas_v2_losses/elec2.npz:elec2,file:data/atlas_v2_losses/weather.npz:weather,file:data/atlas_v2_losses/spam.npz:spam,file:data/atlas_v2_losses/uci_occupancy.npz:uci_occupancy' --policies A5b,QSG,D2,D5,CONTROL_never_switch --seeds 3 --seed-base 2026110901 --workers 2 --out outputs/sprint2/WP2/cached_real_h5
uv run python scripts/sota_sprint/wp2_score.py --runs outputs/sprint2/WP2/cached_real_h5 --out outputs/sprint2/WP2/cached_real_h5_scores.csv
uv run python scripts/sota_sprint/analyze_wp2_cached_h5.py
```

Machine-readable outputs are `cached_real_h5_summary.json` and
`outputs/sprint2/WP2/cached_real_h5_h5_paired.csv`. The score table for all episodes, not just
positive-advantage episodes, is `outputs/sprint2/WP2/cached_real_h5_scores.csv`.
