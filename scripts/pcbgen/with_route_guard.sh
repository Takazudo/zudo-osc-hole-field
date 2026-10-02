#!/usr/bin/env bash
set -euo pipefail
# GitHub-hosted jobs have isolated runner resources and no developer HOME guard.
# Local, shared and self-hosted execution must always use the machine-wide gate.
# https://docs.github.com/en/actions/reference/workflows-and-actions/variables
if [[ ${GITHUB_ACTIONS:-} == true && ${RUNNER_ENVIRONMENT:-} == github-hosted ]]; then
  exec "$@"
fi
exec bash "$HOME/.codex/scripts/heavy-guard.sh" -- "$@"
