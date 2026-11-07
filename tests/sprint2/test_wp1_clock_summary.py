from scripts.sota_sprint.analyze_wp1_clock_ablation import summarize


def test_clock_summary_pairs_policy_rows_and_uses_equal_dataset_weight():
    rows = []
    for dataset, delta in (("a", 2.0), ("b", -1.0)):
        for episode in (0, 1):
            for seed in (0, 1):
                base = 10.0
                rows.extend(
                    [
                        {
                            "regime": dataset,
                            "episode": episode,
                            "seed": seed,
                            "policy": "rmm:gated_deployment+RMM",
                            "net": base,
                            "ever_promote": 0,
                            "labels": 1,
                        },
                        {
                            "regime": dataset,
                            "episode": episode,
                            "seed": seed,
                            "policy": "rmm:gated_deployment+RMM_wallclock",
                            "net": base + delta,
                            "ever_promote": 1,
                            "labels": 2,
                        },
                    ]
                )
    out = summarize(rows, bootstrap_reps=20, bootstrap_seed=4)
    assert out["n_datasets"] == 2
    assert out["equal_dataset_mean_delta_net"] == 0.5
    assert out["n_paired_episode_seed_rows"] == 8
