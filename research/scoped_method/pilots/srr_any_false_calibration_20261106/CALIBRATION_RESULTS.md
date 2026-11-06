# E-SR any-false-promotion calibration results

**Status:** calibration only; no reversal outcomes inspected. Alpha was selected according to the frozen grid/rule in the parent protocol.

## Calibration outcomes

The candidate is the unchanged `E_srrSR:gated_deployment` implementation. Each row uses 1,000 iid `F0_null` streams at seed base `7110601101`; one-sided Wilson upper limits use 99% confidence, Bonferroni-adjusted over seven predeclared thresholds.

| Nominal alpha | Any-promotion episodes | Rate | Adjusted 99% one-sided Wilson upper bound | Qualifies? |
|---:|---:|---:|---:|---|
| 0.05 | 998/1,000 | 0.998 | 0.9996 | No |
| 0.02 | 890/1,000 | 0.890 | 0.9110 | No |
| 0.01 | 565/1,000 | 0.565 | 0.6010 | No |
| 0.005 | 285/1,000 | 0.285 | 0.3193 | No |
| 0.002 | 108/1,000 | 0.108 | 0.1330 | No |
| 0.001 | 46/1,000 | 0.046 | 0.0640 | No |
| **0.0005** | **16/1,000** | **0.016** | **0.0282** | **Yes** |

Per-threshold raw record and manifest SHA-256 values:

| Alpha | `records.jsonl` SHA-256 | `manifest.json` SHA-256 |
|---:|---|---|
| 0.05 | `e1fe7e3e22db956c4d00629982d8786b1ddce38d015ca256f10e3a48e7106a1e` | `8ce18b7036ce79b2984d736071f8861937a8c558663fa0c45bfa81ec1da651fb` |
| 0.02 | `079a235a2cc3414ac51bad79c77547f4dbe30bd94a4e60b1a2504d4120d7fc15` | `377278ffef623a88ee664b5a5feb810f44479f5d708ba14c6ea855c06cc873d8` |
| 0.01 | `3cbde192e9cbb3879e879e30d3aa171c3e1997cebe62539b87a599342aea6d64` | `f17f6881d08c416f68c18c0592d847ca5ef54354a67bdc3af0863fbb92cb365a` |
| 0.005 | `eb2813e924999eba1eed9f504e81ef1327579c310edfbcff270eb272c6c13e0c` | `a54499cab671ec5985e88f6affa020e6fa971ea20fdd7092797b3a5add015f71` |
| 0.002 | `4efe815dd75a5db4a137961012b1a28da2b257eb7daf4331d5acf1e3a71564ad` | `523527f27f4b32a42b4f4873fba0f4925b25c86288976271a24901c0f8a63bf9` |
| 0.001 | `c110e739c72fdad9c5d565e90672556980fffe432611d783cf1f018389ad3fc1` | `c358761eaabcc7a7732a02e40445f29783946df2def55820487f5bb6c805e520` |
| 0.0005 | `6548ee492f2de27d386c0fadcce2d06631aec2d27546924d3e78797260efa0b9` | `95a6ee0034943b2ad59e84ee1435c59650ea4724377569e6932fb50fa5db7a7b` |

The selected empirical operating point passes the calibration gate; this does not guarantee the false-promotion probability or establish a method contribution. Independent null evaluation remains mandatory.
