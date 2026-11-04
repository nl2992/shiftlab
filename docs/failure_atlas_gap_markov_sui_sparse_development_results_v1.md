# Exact-gap Markov SUI with sparse starts: development results

**Status:** screen complete; candidate fails the registered advance rule. No confirmation or
novelty/SOTA claim. Protocol: [registered sparse-start v1](failure_atlas_gap_markov_sui_sparse_development_protocol_v1.md).

- Manifest digest: `da882f39915e002af4522a87086c44187fb9d4d12634891d62e13c5f92939d80`.
- Seeds `[720020,720040)`; 960 paired method-cell records. Raw rows and manifest are in
  `outputs/failure_atlas_gap_markov_sui_sparse_dev/`.
- SUI had zero false promotions in each of eight 20-stream null cells, including `rho=.95`.
  These small counts do not establish the nominal false-promotion guarantee.

Null false-promotion counts with Wilson 95% intervals (EP=`episode_front`, G08=`gap_envelope_rho08`,
SUI=`gap_markov_sui`, MLR=`markov_lr_gate`):

| rho / budget | EP | G08 | SUI | MLR |
|---|---:|---:|---:|---:|
| 0 / .1 | 1/20 `[.009,.236]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| 0 / .25 | 1/20 `[.009,.236]` | 2/20 `[.028,.301]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .5 / .1 | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .5 / .25 | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .8 / .1 | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .8 / .25 | 9/20 `[.258,.658]` | 1/20 `[.009,.236]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .95 / .1 | 11/20 `[.342,.742]` | 7/20 `[.181,.567]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |
| .95 / .25 | 20/20 `[.839,1.000]` | 8/20 `[.219,.613]` | 0/20 `[.000,.161]` | 0/20 `[.000,.161]` |

## Equal-cell paired cost difference (candidate minus comparator)

| comparator | mean | paired 95% interval |
|---|---:|---:|
| Markov LR | +0.0059 | [+0.0004, +0.0114] |
| episode_front | +0.0969 | [+0.0808, +0.1130] |
| gap envelope rho .8 | +0.0469 | [+0.0381, +0.0558] |

The matched sparse start prior reduced the Markov-LR gap compared with the dense-start run, but
the entire interval remains above zero. On the mandatory adverse cell, SUI cost exceeded the
lower-cost episode_front reference by `+0.2459` per round (paired 95% interval
`[+0.2026,+0.2892]`). It fails every advance condition. Stop this exact-gap SUI transfer before
adding acquisition or further tuning on these seed blocks.
