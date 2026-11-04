# Exact-gap Markov SUI transfer: dense-start development results

**Status:** screen complete; candidate fails the registered advance rule. No confirmation or
novelty/SOTA claim. Protocol: [registered v1](failure_atlas_gap_markov_sui_development_protocol_v1.md).

- Manifest digest: `3d706baa2cd2277626081003e34567f6e5c7f27099c9dffca3ac0aaf0e09a93d`.
- Seeds `[720000,720020)`; 960 paired method-cell records. Raw rows and manifest are in
  `outputs/failure_atlas_gap_markov_sui_dev/`.
- The manifest stores the dense implementation's run-time source SHA256. The shared source file
  was subsequently changed in place for the sparse-start screen; an immutable dense source copy
  was not archived. Treat this first screen as a local development result, not a source-reproduced
  result. The sparse-start manifest's source SHA256 matches the current implementation file.
- The SUI candidate had zero false promotions in each of eight 20-stream null cells, including
  `rho=.95`. This is only a small finite screen; with zero events in 20 streams, uncertainty is
  still broad.

Null false-promotion counts with Wilson 95% intervals (EP=`episode_front`, G08=`gap_envelope_rho08`,
SUI=`gap_markov_sui`, MLR=`markov_lr_gate`):

| rho / budget | EP | G08 | SUI | MLR |
|---|---:|---:|---:|---:|
| 0 / .1 | 4/20 `[.081,.416]` | 3/20 `[.052,.360]` | 0/20 `[.000,.161]` | 2/20 `[.028,.301]` |
| 0 / .25 | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .5 / .1 | 1/20 `[.009,.236]` | 1/20 `[.009,.236]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .5 / .25 | 2/20 `[.028,.301]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .8 / .1 | 4/20 `[.081,.416]` | 5/20 `[.112,.469]` | 0/20 `[.000,.161]` | 1/20 `[.009,.236]` |
| .8 / .25 | 13/20 `[.433,.819]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 1/20 `[.009,.236]` |
| .95 / .1 | 13/20 `[.433,.819]` | 8/20 `[.219,.613]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .95 / .25 | 20/20 `[.839,1.000]` | 8/20 `[.219,.613]` | 0/20 `[.000,.161]` | 1/20 `[.009,.236]` |

## Equal-cell paired cost difference (candidate minus comparator)

| comparator | mean | paired 95% interval |
|---|---:|---:|
| Markov LR | +0.0102 | [+0.0041, +0.0162] |
| episode_front | +0.0950 | [+0.0807, +0.1093] |
| gap envelope rho .8 | +0.0380 | [+0.0280, +0.0481] |

The candidate loses to every comparator. On the mandatory adverse cell, episode_front was the
lower-cost reference; SUI cost was higher by `+0.2406` per round (paired 95% interval
`[+0.2057,+0.2755]`). The method fails both the equal-cell criteria and the local guard. The
evidence transfer is not advanced to acquisition work.
