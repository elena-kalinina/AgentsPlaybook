#!/usr/bin/env bash
# Commit playbook changes — called by the agent after EVOLVE.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MSG="${1:-Agent playbook update}"
cd "$ROOT"
git config user.email "${GIT_AUTHOR_EMAIL:-github-actions[bot]@users.noreply.github.com}"
git config user.name "${GIT_AUTHOR_NAME:-github-actions[bot]}"
git add playbooks/playbook.md
if git diff --staged --quiet; then
  echo "No playbook changes to commit."
  exit 0
fi
git commit -m "$MSG"
echo "Committed playbook: $MSG"
