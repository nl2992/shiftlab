# Monitoring Risks in Test-Time Adaptation: source and task-fit audit

**Audit date:** 2026-10-26  
**Primary source:** Schirmer, Jazbec, Naesseth, and Nalisnick, *Monitoring Risks in Test-Time Adaptation*, NeurIPS 2025. [Proceedings paper](https://proceedings.neurips.cc/paper_files/paper/2025/file/746960ad49ddb47248970a0e1404230c-Paper-Conference.pdf) · [proceedings record](https://proceedings.neurips.cc/paper_files/paper/2025/hash/746960ad49ddb47248970a0e1404230c-Abstract-Conference.html)  
**Author code:** [`monasch/tta-monitor`](https://github.com/monasch/tta-monitor), checked-out `main` at `f200f00d4ca79567df0214bdd46150bb729c2227` (2026-10-26). The checkout is clean. No top-level license file was present in this revision; no code was copied or redistributed.

## Published target

The paper monitors a sequence of predictive models `p_1, …, p_t` that are updated online from unlabeled test batches. Its tested null concerns the running predictive risk of the adapted model sequence relative to the source model's risk plus a tolerance:

\[
\bar R_t(p_{1:t}) = t^{-1}\sum_{k=1}^t R_k(p_k) \le R_0(p_0)+\epsilon_{\mathrm{tol}}\quad\text{for every }t.
\]

The paper distinguishes two monitoring routes. Its supervised extension uses test labels to form a lower confidence sequence for the adapted model sequence's risk. Its unsupervised method replaces test losses with feature-only loss proxies and constructs a lower bound on running predictive risk using labeled source calibration data. For the concrete uncertainty proxy, it uses `1 − max_c p_k(x)_c`, with proxy thresholds recalibrated as the model changes.

The unsupervised result depends on a specific proxy-separation condition: averaged test false-positive rates for declaring high proxy/low loss must be bounded by the source false-positive rate plus averaged test false-negative rates. The paper also requires bounded nonnegative loss and its stated data-independence and calibration conditions. This proxy condition is a substantive assumption, not a consequence of using a confidence sequence. The authors report that it can fail during warm-up and when the source model is static. Their main configuration uses total alpha 0.2 split between source and test risk, 1,000 labeled source calibration examples, 0–1 and Brier losses, and tolerance thresholds 0.05 and 0.01 respectively.

The reported experiments use ImageNet-C, Yearbook, and FMoW-Time with TENT, CoTTA, SAR, and SHOT. The official code expects its own model/data setup and pretrained checkpoints; the README specifies a separate Conda environment. This is evidence for the paper's predictive-risk setting, not a transferable ShiftLab result.

## Relation to ShiftLab and disposition

This is a strong prior-work comparator for the claim that sequential monitoring can continue while a model is updated at test time, including without test labels. It rules out presenting adaptive-model monitoring itself as new. Its endpoint is running predictive risk against a source-model threshold. It does not test the paired cost of a deployed policy against a reference policy, choose or certify an alternative, or account for label, retraining, switching, and intervention costs.

The current ShiftLab real-data runs do not instantiate its task: Gas Sensor is a coarse batch-held-out classifier study; WILDS CivilComments uses sample-split candidate selection without test-time adaptation; EIA refits with assumed mature labels; and CRSP is an offline retrospective replay. None supplies the online unlabeled TTA protocol plus source calibration and proxy-separation evidence required for a fair reproduction. A synthetic paired-cost monitor comparison would also change its endpoint and would not reproduce the paper.

**Decision:** keep this as a required Q1 scope comparator, but exclude it from the current paired decision-cost numerical frontier. Do not call its predictive-risk alarms decision-harm detections. Revisit a quantitative adaptation only if a preregistered task actually performs test-time updates and supports the paper's calibration, proxy, and information assumptions; report predictive risk separately and retain the supervised risk route as an oracle only where labels are available.

## Primary-source record

- The risk null and conditioning on prior unlabeled test features are in the published paper's §3.1, Eq. 5.
- The unlabeled risk lower bound and proxy-separation condition are in §3.2, Assumption 1 and Proposition 1.
- Uncertainty proxy construction and online threshold recalibration are in §§3.3–3.4.
- The authors' data/model setup and risk criteria are in §5; limitations of the proxy condition are discussed with the experiments.
- The checked code commit is recorded above. Its README describes the data/checkpoint setup and supported loss proxies; no code or results from that repository were included in ShiftLab's benchmark.
