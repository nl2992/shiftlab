# Exchangeable-twin known-null loss streams (P2)

Built by `scripts/sota_sprint/twin_null.py` under the protocol
[docs/sota_sprint/p2_known_null_protocol.md](../../docs/sota_sprint/p2_known_null_protocol.md), which
was registered (36d9796) before this build. Source data: the five fresh UCI datasets
(`data/sprint_fresh_losses/README.md`). Each file stacks 20 splits x K episodes, giving rows `l0`
and `l1` with shape (20K, 2000), plus `split` and `ep`. Per-dataset construction statistics, realised
advantages, persistence estimates and array content hashes are in `stats.json`. The `.npz` file hash
changes on rebuild because of zip timestamps; use `array_content_sha256` instead.
