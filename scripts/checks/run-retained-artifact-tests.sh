#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
printf '%s\n' 'Retained-artifact integration regressions: require preserved issue-38 recovery files and experimental boards.'
printf '%s\n' 'Missing, stale, or changed artifacts are failures; this command does not regenerate or rebind evidence.'
python3 -m unittest discover --start-directory scripts/pcbgen --pattern '*_retained_regression.py' -v
