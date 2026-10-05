#!/usr/bin/env bash
# Dispatch .github/workflows/route.yml for one board and wait for the run to finish.
# Usage: bash scripts/pcbgen/dispatch_route.sh <board> <branch> <from-stage> [<to-stage>] [--workers N] [--max-minutes M] [--no-wait]
set -euo pipefail

usage() {
  printf 'Usage: bash scripts/pcbgen/dispatch_route.sh <board> <branch> <from-stage> [<to-stage>] [--workers N] [--max-minutes M] [--no-wait]\n' >&2
  exit 2
}

positional=()
fields=()
wait=1
while (($#)); do
  case $1 in
    --workers) fields+=(-f "workers=${2:?}"); shift 2 ;;
    --max-minutes) fields+=(-f "max_minutes=${2:?}"); shift 2 ;;
    --no-wait) wait=0; shift ;;
    -h | --help) usage ;;
    *) positional+=("$1"); shift ;;
  esac
done
((${#positional[@]} == 3 || ${#positional[@]} == 4)) || usage
board=${positional[0]} branch=${positional[1]} from=${positional[2]} to=${positional[3]:-}

git ls-remote --exit-code --heads origin "$branch" >/dev/null || {
  printf 'Branch %s does not exist on origin.\n' "$branch" >&2
  exit 1
}

since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# workflow_dispatch only sees workflows on the default branch; the job checks out <branch> itself.
gh workflow run route.yml --ref main -f "board=$board" -f "branch=$branch" -f "from_stage=$from" -f "to_stage=$to" "${fields[@]}"

run_id=
for _ in $(seq 30); do
  sleep 2
  run_id=$(gh run list --workflow route.yml --event workflow_dispatch --limit 10 \
    --json databaseId,createdAt,displayTitle \
    --jq "[.[] | select(.createdAt >= \"$since\" and .displayTitle == \"Route $board on $branch from $from\")] | last | .databaseId // empty")
  [[ -n $run_id ]] && break
done
[[ -n $run_id ]] || { printf 'Dispatched, but no run appeared within 60 s.\n' >&2; exit 1; }

url=$(gh run view "$run_id" --json url --jq .url)
printf 'Run %s: %s\n' "$run_id" "$url"
((wait)) || exit 0

status=0
gh run watch "$run_id" --interval 60 --exit-status >/dev/null || status=$?
gh run view "$run_id" --json conclusion,jobs --jq '"conclusion: \(.conclusion)"'
gh run view "$run_id" --log 2>/dev/null | grep -E 'open edges$|rerun --from-stage|^.*(status|minutes|peak_mb|edges_before|edges_after|resume)=' | sed -E 's/^[^\t]*\t[^\t]*\t[^ ]+ //' | tail -n 40 || true
exit "$status"
