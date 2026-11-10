# Atan & van der Schaar, Data-Driven Online Decision Making with Costly (Information Acquisition) Observations
URL: https://arxiv.org/abs/1602.03600 ; PDF https://arxiv.org/pdf/1602.03600 (v2 21 Oct 2017; v1 11 Feb 2016). Accessed 2026-11-09.
Access: abstract page via WebFetch; full PDF downloaded and text-extracted (pdftotext); model, Sim-OOS/Seq-OOS and regret-bound sections skimmed, not a line-by-line read.
Facts: contextual MAB with costly observations (CMAB-CO). The learner chooses which observations (set I_t, cost sum of c_i) AND the action each round; T-time regret against a policy choosing the best observation set and action; Sim-OOS (simultaneous) and Seq-OOS (sequential observation) achieve sublinear regret (a t^(2/3)-type bound is stated for Sim-OOS in the text I saw). Application: breast-cancer screening. The v2 header says "Under review by AISTATS 2018".
Not covered (by my read): hard total label cap with pending-queue reservation, label delay, non-stationarity, switching costs or reversal, a risk (false-promotion) constraint.
Repo audits: docs/g1_deadline_aligned_acquisition_kill_v1.md; docs/closest_prior_work.md.
