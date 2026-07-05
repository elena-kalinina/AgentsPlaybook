#!/usr/bin/env bash
# Commit and push agent artifacts after a CI run (playbook + persisted state).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

git config user.email "github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"

git add playbooks/playbook.md \
  data/settled.json \
  data/predictions.json \
  data/metrics.json \
  data/intel_cache.json \
  data/schedule.json \
  data/prebet_state.json 2>/dev/null || true

if git diff --staged --quiet; then
  echo "No agent artifacts to push."
  exit 0
fi

git commit -m "CI: update agent state ($(date -u +%Y%m%dT%H%M%SZ))"
git push
echo "Pushed agent artifacts."
