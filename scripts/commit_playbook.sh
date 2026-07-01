#!/usr/bin/env bash
# Commit playbook changes — called by the agent after EVOLVE.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MSG="${1:-Agent playbook update}"
cd "$ROOT"
git add playbooks/playbook.md
if git diff --staged --quiet; then
  echo "No playbook changes to commit."
  exit 0
fi
git commit -m "$MSG"
echo "Committed playbook: $MSG"
