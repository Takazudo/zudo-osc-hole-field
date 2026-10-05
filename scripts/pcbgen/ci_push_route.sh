#!/usr/bin/env bash
# CI only: commit the promoted board and grid-routing receipts, then push them to the routing branch.
# Usage: bash scripts/pcbgen/ci_push_route.sh <board> <branch> <message-file>
# If the branch moved and a rebase fails, the commit goes to ci-route/<board>-<run id> instead.
set -euo pipefail
board=$1 branch=$2 message=$3

git add -- "boards/$board/$board.kicad_pcb" "boards/$board/reports/grid-routing"
if git diff --cached --quiet; then
  echo "No adopted stage; nothing to commit." | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
  exit 0
fi
git config user.name "github-actions[bot]"
git config user.email "41898+github-actions[bot]@users.noreply.github.com"
git commit --quiet -F "$message"
if git push origin "HEAD:refs/heads/$branch"; then exit 0; fi
git fetch --quiet --unshallow origin "$branch" || git fetch --quiet origin "$branch"
if git rebase "origin/$branch" && git push origin "HEAD:refs/heads/$branch"; then exit 0; fi
git rebase --abort 2>/dev/null || true
side="ci-route/$board-${GITHUB_RUN_ID:-local}"
git push origin "HEAD:refs/heads/$side"
echo "::warning::$branch moved and the rebase failed; result pushed to $side"
echo "Result pushed to side branch \`$side\` because \`$branch\` moved." >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
