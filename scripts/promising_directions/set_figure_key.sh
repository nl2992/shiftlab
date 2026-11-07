#!/usr/bin/env bash
# Put the API key that is currently on the clipboard into PaperBanana's config.
#
# Usage: copy the key and run with no arguments, or pass a file containing just the key:
#   set_figure_key.sh                 # from the clipboard
#   set_figure_key.sh path/to/keyfile # from a file (never echoed)
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

PAPERBANANA_CFG="$CFG" KEYFILE="${1:-}" python3 - <<'PY'
import os, pathlib, re, subprocess, sys

src = os.environ.get("KEYFILE") or ""
if src:
    kp = pathlib.Path(src)
    if not kp.is_file():
        sys.exit(f"no such key file: {src}")
    key = kp.read_text().strip()
    if not key:
        sys.exit(f"{src} is empty")
else:
    key = subprocess.run(["pbpaste"], capture_output=True, text=True).stdout.strip()
    if not key:
        sys.exit("clipboard is empty: copy the API key first, or pass a file containing it")
if any(c.isspace() for c in key):
    sys.exit("clipboard does not look like a single key (it contains whitespace)")

# "AQ." is Google's newer authorization-key format: AI Studio issues these by default and
# they are bound to a Cloud service account, restricted to the Gemini API. They are a valid
# Gemini credential and belong in google_api_key, NOT in an OpenRouter field. Some clients
# and the OpenAI-compatible endpoints are reported not to accept them yet, so a 401 with
# ACCESS_TOKEN_TYPE_UNSUPPORTED after this is a tool/endpoint limitation, not a bad key.
field = ("google_api_key" if key.startswith(("AIza", "AQ."))
         else "openrouter_api_key" if key.startswith("sk-or-")
         else "anthropic_api_key" if key.startswith("sk-ant-")
         else "openai_api_key" if key.startswith("sk-")
         else None)
if field is None:
    sys.exit(f"unrecognised key prefix {key[:4]!r}... — expected AIza or AQ. (Google), "
             "sk-or- (OpenRouter), sk-ant- (Anthropic) or sk- (OpenAI). Edit by hand if needed.")

cfg = pathlib.Path(os.environ["PAPERBANANA_CFG"])
text = cfg.read_text()
pat = re.compile(rf'^(\s*{field}:\s*)"[^"]*"', re.M)
if not pat.search(text):
    sys.exit(f"could not find {field} in {cfg}")
# Blank every OTHER provider key first. PaperBanana prefers OpenRouter when several are
# set, so a stale or wrong-format value left in another field silently wins over the key
# just supplied -- which is exactly how the first attempt here failed.
cleared = []
def blank(m):
    name = m.group(1).strip().rstrip(":")
    if name != field and m.group(2):
        cleared.append(name)
        return m.group(1) + '""'
    return m.group(0)
text = re.sub(r'^(\s*\w*api_key:\s*)"([^"]*)"', blank, text, flags=re.M)
if cleared:
    print("cleared stale values in: " + ", ".join(cleared))
cfg.write_text(pat.sub(lambda m: m.group(1) + '"' + key + '"', text, count=1))
cfg.chmod(0o600)
print(f"{field} set in {cfg} ({len(key)} chars, not shown); file mode 600")
PY
