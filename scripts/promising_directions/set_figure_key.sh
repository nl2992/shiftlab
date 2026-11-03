#!/usr/bin/env bash
# Put the API key that is currently on the clipboard into PaperBanana's config.
#
# Usage: copy the key, then run this script with no arguments.
#
# The key goes clipboard -> config file and is never printed, logged or passed as an
# argument (so it does not reach shell history or process listings). The provider field
# is chosen from the key's prefix. Override the clone location with PAPERBANANA_REPO.
set -euo pipefail

DEFAULT_REPO="/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-b3-plus-icml-fcc9c6/5708b58e-c6ed-4f49-8c37-d7f13f2fee32/scratchpad/paperbanana/repo"
REPO="${PAPERBANANA_REPO:-$DEFAULT_REPO}"
if [ ! -d "$REPO" ]; then
  echo "PaperBanana clone not found at: $REPO" >&2
  echo "Set PAPERBANANA_REPO to the clone path and re-run." >&2
  exit 1
fi

CFG="$REPO/configs/model_config.yaml"
if [ ! -f "$CFG" ]; then
  cp "$REPO/configs/model_config.template.yaml" "$CFG"
  echo "created $CFG from template"
fi

PAPERBANANA_CFG="$CFG" python3 - <<'PY'
import os, pathlib, re, subprocess, sys

key = subprocess.run(["pbpaste"], capture_output=True, text=True).stdout.strip()
if not key:
    sys.exit("clipboard is empty: copy the API key first")
if any(c.isspace() for c in key):
    sys.exit("clipboard does not look like a single key (it contains whitespace)")

field = ("google_api_key" if key.startswith("AIza")
         else "openrouter_api_key" if key.startswith("sk-or-")
         else "anthropic_api_key" if key.startswith("sk-ant-")
         else "openai_api_key" if key.startswith("sk-")
         else None)
if field is None:
    sys.exit(f"unrecognised key prefix {key[:4]!r}... — expected AIza (Google), sk-or- "
             "(OpenRouter), sk-ant- (Anthropic) or sk- (OpenAI). Edit the config by hand.")

cfg = pathlib.Path(os.environ["PAPERBANANA_CFG"])
text = cfg.read_text()
pat = re.compile(rf'^(\s*{field}:\s*)"[^"]*"', re.M)
if not pat.search(text):
    sys.exit(f"could not find {field} in {cfg}")
cfg.write_text(pat.sub(lambda m: m.group(1) + '"' + key + '"', text, count=1))
cfg.chmod(0o600)
print(f"{field} set in {cfg} ({len(key)} chars, not shown); file mode 600")
PY
