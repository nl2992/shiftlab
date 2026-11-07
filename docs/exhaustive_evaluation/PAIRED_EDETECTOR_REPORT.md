# Paired SR/CUSUM e-detector comparison

2026-10-30. Previous turn: progress (native Markov pilot/scope check committed). This registered development run is complete; the goal remains active. Existing scalar recurrences were reused as the verification reference rather than inventing a detector.

## Contract

[Shin, Ramdas and Rinaldo, E-detectors](https://nejsds.nestat.org/journal/NEJSDS/article/59/text) develop SR/CUSUM constructions with average-run-length guarantees. Our paired adapter uses fixed stakes.2/.5/.8 and their equal mixture on bounded queried gain-minus-margin factors. At release, SR=(1+SR)f and CUSUM=max(1,CUSUM)f. Initial unreleased events use factor1; calendar starts still open. Same fixed-delay, uniform query, cap400, horizon2000, margin.01, query cost.001 and switch cost1 as prior comparisons. All requests before promotion, including pending requests, count in paid labels.

We explicitly separate thresholdH/alpha (finite-horizon conversion) from threshold1/alpha (ARL-style diagnostic). For valid conditional factors, each start has a supermartingale; the average overH starts, including not-yet-started mass, is a supermartingale. SR/H is bounded by that process; the max-start CUSUM is bounded by SR. Thus thresholdH/alpha supports a finite-horizon crossing bound under the stated factor assumptions. The same reasoning does not give a1/alpha global crossing bound for SR or max-start CUSUM. Delayed in-order prefixes and fixed stakes preserve this supporting argument; arbitrary informative/reordered feedback and real conditional-null assumptions are not established.

One exact test has null factors identically1. SR reaches20 at event index19 with probability1, while the registered horizon threshold does not cross. This is compatible with mean-run-length20 and demonstrates why those arms are not equal-safety comparisons. It is not a refutation of the e-detector paper.

Vector recurrences match the existing HorizonCalibratedEDetector scalar mixture under delayed skips and budget exhaustion.29 relevant tests passed. Ruff0.17.1 checks pass. This is a formula/engine adaptation, not native R-package or full author experiment reproduction.

## Completed registered run

Eight cases ×256 paths=2048 shared synthetic streams.16 detector settings and4 frozen references, no new method search count. All settings frozen before outcome scoring, seeds202666000/202667000. Primary: horizon-converted cost versus strong references; ARL arms diagnostic only. Results are development, not multiplicity-adjusted confirmation. Zero observed null alarms on256 paths does not prove safety across the family.

| Method | Persistent mean total cost | Late-benefit excess cost | Reversal excess cost | Max observed null promotion rate |
|---|---:|---:|---:|---:|
| SR stake.2, horizon | 281.689 | +.196 | +85.776 | 0 |
| SR stake.5, horizon | 230.079 | −50.750 | +32.359 | 0 |
| SR stake.8, horizon | 213.591 | −72.584 | +11.977 | 0 |
| SR mixture, horizon | 219.693 | −64.354 | +19.862 | 0 |
| CUSUM stake.2, horizon | 352.998 | +.394 | +.393 | 0 |
| CUSUM stake.5, horizon | 269.116 | −1.929 | +82.003 | 0 |
| CUSUM stake.8, horizon | 238.945 | −36.298 | +44.534 | 0 |
| CUSUM mixture, horizon | 246.172 | −25.569 | +53.874 | 0 |
| Kelly parent | 204.065 | −76.325 | +5.582 | .01172 |
| Tuned FTL | 206.234 | −82.342 | +9.611 | .01172 |
| Empirically calibrated CUSUM.05 | 204.378 | −82.997 | +1.502 | .02734 |
| Empirically calibrated CUSUM.1 | 200.371 | −88.460 | −4.222 | .01563 |

Persistent mean averages useful_initial/useful/late/small equally. No horizon-converted e-detector beats the reference cost in this registered panel. Delayed promotion can leave little useful time before reversal. For weak stakes, lack of action can also look safe while missing beneficial alternatives.

ARL-threshold SR settings have maximum null promotion rate1.0 and are ineligible as safety-matched controls. ARL CUSUM stake.8 costs186.266 but has maximum null rate.46484; stake.5 has rate.17578 and mixture.23438. These apparent cost gains cannot vindicate a safe switching method. The stake.2 ARL CUSUM has0 observed null alarms here but remains without the matched general guarantee and costs235.595. All settings remain in paired_edetectors_results.json rather than discarding unfavorable comparisons.

## Source update and remaining scope

A current search located [Saha and Ramdas, Non-partitioned e-detectors, arXiv2607.28322v1](https://arxiv.org/html/2607.28322). Its abstract, Section1 and performance-metric definitions were inspected. It provides distinct ARL and PFA constructions for unknown no-change laws, including a Markov appendix. Therefore no claim that e-detectors only support ARL is justified. OurH/alpha conversion is a known conservative finite-horizon baseline, not the strongest possible PFA construction.

The new paper tests change from an unknown no-change distribution, not the same conditional paired-mean inequality; nuisance change can be benign for action utility. Its detailed point-null aggregation/infimum and bound constructions still require theorem-level mapping before exclusion or an adapted comparison. This is a newly explicit unclosed obligation, not a validated residual novelty claim. Do not call the detector family exhaustive after only these16 settings.

Next: inspect the non-partitioned PFA construction and robust-controller synthesis mapping. Further generic pacing/restarts must compete against these relevant published constructions, not merely against conservative thresholds. No new combination or publication claim survives this run. Reserved real windows remain closed; no paid jobs or subagents.

Artifacts: paired_edetectors_registration.json, paired_edetectors_status.json, paired_edetectors_results.json; outputs/exhaustive_evaluation/paired_edetectors/{case}.npz. Command: python scripts/exhaustive_evaluation/run_paired_edetectors.py (registration now protects evidence). Source snapshots and hashes preserve executed versions.
