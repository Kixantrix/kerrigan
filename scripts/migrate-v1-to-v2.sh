#!/usr/bin/env bash

set -euo pipefail

# Label migration logic:
# - Remove legacy v1 labels:
#   role:swe, role:architect, role:spec, role:testing, role:debugging,
#   role:triage, agent:sprint, agent:triage, agent-ready
# - Only one label maps forward: agent-ready -> agent:go
# - The mapping happens only when the issue is OPEN and has no assignees.
# - All other legacy labels are removed with no replacement.

readonly V1_LABELS=(
  "role:swe"
  "role:architect"
  "role:spec"
  "role:testing"
  "role:debugging"
  "role:triage"
  "agent:sprint"
  "agent:triage"
  "agent-ready"
)

dry_run=false

usage() {
  cat <<'EOF'
Usage: scripts/migrate-v1-to-v2.sh [--dry-run]

Migrates legacy Kerrigan v1 issue labels to the v2 label set using the GitHub CLI.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

has_label() {
  local needle="$1"
  shift || true

  local label
  for label in "$@"; do
    if [[ "$label" == "$needle" ]]; then
      return 0
    fi
  done

  return 1
}

join_by() {
  local separator="$1"
  shift || true
  local first=true
  local item

  for item in "$@"; do
    if [[ "$first" == true ]]; then
      printf '%s' "$item"
      first=false
    else
      printf '%s%s' "$separator" "$item"
    fi
  done
}

issue_lines="$(gh issue list \
  --state all \
  --limit 1000 \
  --json number,state,labels,assignees \
  --template '{{range .}}{{.number}}{{"\t"}}{{.state}}{{"\t"}}{{len .assignees}}{{"\t"}}{{range $i, $label := .labels}}{{if $i}},{{end}}{{$label.name}}{{end}}{{"\n"}}{{end}}')"

if [[ -z "$issue_lines" ]]; then
  echo "No issues found."
  exit 0
fi

changed=0

while IFS=$'\t' read -r number state assignee_count labels_csv; do
  if [[ -z "${number:-}" ]]; then
    continue
  fi

  labels=()
  if [[ -n "${labels_csv:-}" ]]; then
    IFS=',' read -r -a labels <<< "$labels_csv"
  fi

  remove_labels=()
  for label in "${V1_LABELS[@]}"; do
    if has_label "$label" "${labels[@]}"; then
      remove_labels+=("$label")
    fi
  done

  if [[ "${#remove_labels[@]}" -eq 0 ]]; then
    continue
  fi

  add_labels=()
  if has_label "agent-ready" "${labels[@]}" &&
     [[ "$state" == "OPEN" ]] &&
     [[ "$assignee_count" == "0" ]] &&
     ! has_label "agent:go" "${labels[@]}"; then
    add_labels=("agent:go")
  fi

  remove_csv="$(join_by , "${remove_labels[@]}")"
  add_csv="$(join_by , "${add_labels[@]}")"

  if [[ "$dry_run" == true ]]; then
    if [[ -n "$add_csv" ]]; then
      echo "DRY RUN #$number remove=$remove_csv add=$add_csv"
    else
      echo "DRY RUN #$number remove=$remove_csv"
    fi
  else
    cmd=(gh issue edit "$number" --remove-label "$remove_csv")
    if [[ -n "$add_csv" ]]; then
      cmd+=(--add-label "$add_csv")
    fi
    "${cmd[@]}" >/dev/null

    if [[ -n "$add_csv" ]]; then
      echo "UPDATED #$number remove=$remove_csv add=$add_csv"
    else
      echo "UPDATED #$number remove=$remove_csv"
    fi
  fi

  changed=$((changed + 1))
done <<< "$issue_lines"

if [[ "$changed" -eq 0 ]]; then
  echo "No legacy labels found."
else
  echo "Processed $changed issue(s)."
fi
