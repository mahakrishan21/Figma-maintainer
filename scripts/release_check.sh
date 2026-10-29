#!/bin/bash
# Release check: run before tagging a new figma-maintainer version (SOP manager).
#   bash scripts/release_check.sh
# Compiles every script with this Mac's Python (catches syntax that older Pythons reject), runs the test suite
# (offline: no Figma, no token), checks the hook and manifest files, and validates the plugin. Exit 1 on any failure.
set -u
cd "$(dirname "$0")/.." || exit 1
fail=0
step() { printf '\n== %s\n' "$1"; }

step "Compile scripts ($(python3 -V 2>&1))"
for f in scripts/*.py; do
  python3 -m py_compile "$f" || { echo "  FAIL $f"; fail=1; }
done
[ $fail = 0 ] && echo "  all scripts compile"

step "Shell scripts"
for f in scripts/*.sh; do bash -n "$f" || { echo "  FAIL $f"; fail=1; }; done && echo "  ok"

step "JSON files"
for f in hooks/hooks.json .claude-plugin/plugin.json .claude-plugin/marketplace.json tests/prompts.json knowledge/cost-config.json knowledge/pricing.json; do
  [ -f "$f" ] || continue
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" || { echo "  FAIL $f"; fail=1; }
done && echo "  ok"

step "Tests"
env -u FIGMA_TOKEN -u FIGMA_FIXTURES -u FIGMA_RECORD python3 -m unittest discover -s tests -t . || fail=1

step "Plugin validation"
if command -v claude >/dev/null 2>&1; then
  claude plugin validate .claude-plugin/plugin.json || fail=1
  claude plugin validate . || fail=1
else
  echo "  claude CLI not found: skipped"
fi

find scripts tests -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null
if [ $fail = 0 ]; then
  printf '\nRELEASE CHECK PASSED\n'
else
  printf '\nRELEASE CHECK FAILED: fix the items above before tagging.\n'
  exit 1
fi
