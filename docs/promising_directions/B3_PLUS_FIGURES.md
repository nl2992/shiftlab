# B3+ figures: specification, source data and exact commands

AGENTS.md requires PaperBanana for research visuals, including empirical figures, and forbids
silently substituting another generator. This file records the setup, the validated source data
and the exact commands, so that figure generation is one command per figure once a key is present.

## Status

- **PaperBanana is cloned and its dependencies are installed**, in an isolated directory outside
  this repository (third-party code and a ~2 GB dependency tree do not belong in Git):
  `<scratchpad>/paperbanana/repo`, cloned from `https://github.com/dwzhu-pku/PaperBanana`
  (`--depth 1`), with its own `.venv` created by `uv venv --python 3.12` and
  `uv pip install -r requirements.txt` completed.
- It supports both task types we need: `--task diagram` and `--task plot`.
- **BLOCKED on an API key, which is the user's to provide.** The tool needs one of
  `OPENROUTER_API_KEY` (recommended: one key covers text reasoning and image generation) or
  `GOOGLE_API_KEY`; `configs/model_config.yaml` also accepts `anthropic_api_key` and
  `openai_api_key`. No key is stored in this repository and none was entered on the user's
  behalf. Set it as an environment variable in your own shell, or write it into
  `configs/model_config.yaml` in the clone, which is outside Git.
- **No figure has been generated.** Nothing below reports a figure that exists.

## Source data, all generated from saved per-episode records

In `docs/promising_directions/results/b3_plus/figure_data/`. Every row carries the file it came
from; no value is hand-entered.

| File | Backs | Contents |
|---|---|---|
| `fig2_netcost_by_case.csv` | Figure 2 | P0 / P3b / P6 / P7s mean net cost and mean labels for all five cases at S0, with K and bootstrap level |
| `fig3_ldpa_per_episode.csv` | Figure 3 | per-episode P3b and P7s cost, their difference, labels and rollbacks across ldpa's 32 episodes |
| `fig4_sensitivity.csv` | Figure 4 | `P7s - P3b` for every case at every configuration run, with its source file |

## Commands

Run from the clone, with the key already in your environment. `PB` is the clone path.

Figure 1 — method diagram:

```bash
cd "$PB/repo" && .venv/bin/python skill/run.py --task diagram --aspect-ratio 21:9 --content-file <repo>/paper/b3_plus/figures/fig1_method.txt --caption "Settled-decision acquisition. Each event passes through issue, release and decide. Acquisition falls to the propensity floor once the deployment decision is settled; the evidence process and promotion rule are unchanged." --output <repo>/paper/b3_plus/figures/fig1_method.png
```

Figure 2 — five-case net cost:

```bash
cd "$PB/repo" && .venv/bin/python skill/run.py --task plot --aspect-ratio 16:9 --content-file <repo>/docs/promising_directions/results/b3_plus/figure_data/fig2_netcost_by_case.csv --caption "Net cost per episode on the five case studies at the primary configuration. Lower is better. P1 is a hindsight reference and is omitted. Bars for spam, weather and uci_occupancy rest on seed-level bootstraps (K<5)." --output <repo>/paper/b3_plus/figures/fig2_netcost.png
```

Figure 3 — ldpa per-episode paired difference:

```bash
cd "$PB/repo" && .venv/bin/python skill/run.py --task plot --aspect-ratio 16:9 --content-file <repo>/docs/promising_directions/results/b3_plus/figure_data/fig3_ldpa_per_episode.csv --caption "Per-episode paired difference P7s minus P3b on openml_ldpa (K=32). Negative is an improvement. Two episodes are worse, worst +3.13, and the episode-bootstrap mean is -4.43." --output <repo>/paper/b3_plus/figures/fig3_ldpa.png
```

Figure 4 — sensitivity:

```bash
cd "$PB/repo" && .venv/bin/python skill/run.py --task plot --aspect-ratio 16:9 --content-file <repo>/docs/promising_directions/results/b3_plus/figure_data/fig4_sensitivity.csv --caption "Paired net-cost difference P7s minus P3b by configuration. S0 primary, S1 budget 400, S2 switching cost 20, S3 double delay, S4 query cost 0.10. All 23 cells are negative." --output <repo>/paper/b3_plus/figures/fig4_sensitivity.png
```

## Mandatory verification after generation

AGENTS.md requires inspecting the exported visual against the source values. For each figure,
before it enters the manuscript:

1. Read the generated PNG and check every plotted value against the backing CSV.
2. Confirm Figure 2 does not present seed-bootstrap cases as if they were episode-bootstrapped.
3. Confirm Figure 3 shows the 2 worse episodes rather than only the mean.
4. Confirm Figure 4's sign convention matches the caption (negative = improvement).
5. Record the check, and the model and version used, in this file.

A generated figure that has not been checked against its CSV must not be used.

## Correction 2026-11-02: Google's `AQ.` authorization-key format

I asserted that a 53-character credential with an `AQ.` prefix was "not an API key of the form
PaperBanana needs" and that no field placement would authenticate it. **That was wrong, and it
was asserted from prefix convention rather than from documentation.**

Google AI Studio's own documentation (`https://aistudio.google.com/docs/api-key`) describes a
second credential type alongside the long-standing `AIza...` keys: **authorization keys**, "bound
directly to a Google Cloud service account" and "restricted to the Generative Language API
(Gemini API) by default", offering faster enforcement against leaked keys. AI Studio now issues
these by default, and they carry the `AQ.` prefix. They are a valid Gemini credential and belong
in `google_api_key`.

`set_figure_key.sh` now recognises `AQ.` and routes it to `google_api_key`, and it also accepts a
file containing just the key, so no clipboard round-trip is needed:

```bash
./scripts/promising_directions/set_figure_key.sh path/to/keyfile
```

Verified against a throwaway config: an `AQ.`-prefixed value sets `google_api_key` and leaves
every other provider field empty.

### Caveat worth knowing if it still fails

Reported on Google's own developer forum (community reports, **not** official documentation, and
not verified here): `AQ.` keys have returned `401 UNAUTHENTICATED` with
`ACCESS_TOKEN_TYPE_UNSUPPORTED` against `generativelanguage.googleapis.com`, and "Multiple
authentication credentials received" on OpenAI-compatible endpoints; some third-party tools reject
them through hardcoded key-format checks. If generation fails after the key is correctly placed in
`google_api_key`, that is the likely cause -- a client/endpoint limitation rather than a bad
credential -- and the workarounds reported are an `AIza` key created through the Google Cloud
console or an OpenRouter key. The earlier silent hang is consistent with this, but it was also
running with the key in the *wrong* field, so it is not evidence either way.
