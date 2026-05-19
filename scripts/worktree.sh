#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/worktree.sh new <task-id> [-Bootstrap|--bootstrap]
  scripts/worktree.sh list
  scripts/worktree.sh remove <task-id> [-Force|--force]
  scripts/worktree.sh prune
  scripts/worktree.sh -h|--help

Verbs:
  new       Create ../<repo>-worktrees/<task-id> on branch task/<task-id> from current HEAD.
  list      List active worktrees with branch and dirty state.
  remove    Remove worktree and delete task/<task-id> branch (warn if unmerged unless --force).
  prune     Run git worktree prune.

Flags:
  -Bootstrap, --bootstrap  (new) Run dependency install commands in the new worktree.
  -Force, --force          (remove) Remove even if worktree is dirty and delete unmerged branch.
USAGE
}

die() {
  echo "Error: $*" >&2
  exit 1
}

warn() {
  echo "Warning: $*" >&2
}

repo_root() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "Not inside a git repository."
  printf '%s\n' "$root"
}

validate_head_attached() {
  git symbolic-ref --quiet HEAD >/dev/null 2>&1 || die "HEAD is detached. Checkout a branch before creating a worktree."
}

worktree_parent() {
  local root parent leaf
  root="$1"
  parent="$(dirname "$root")"
  leaf="$(basename "$root")"
  printf '%s/%s-worktrees\n' "$parent" "$leaf"
}

branch_exists() {
  git show-ref --verify --quiet "refs/heads/$1"
}

warn_longpaths_if_needed() {
  local value
  value="$(git config --get core.longpaths 2>/dev/null || true)"
  if [[ "$value" != "true" ]]; then
    warn "git core.longpaths is not true. On Windows, run: git config core.longpaths true"
  fi
}

bootstrap_worktree() {
  local path
  path="$1"

  if [[ -f "$path/package.json" ]]; then
    if [[ -f "$path/package-lock.json" ]]; then
      (cd "$path" && npm ci)
    else
      (cd "$path" && npm install)
    fi
  fi

  if [[ -f "$path/requirements.txt" ]]; then
    (cd "$path" && python -m pip install -r requirements.txt)
  fi

  if [[ -f "$path/pyproject.toml" ]]; then
    (cd "$path" && python -m pip install -e .)
  fi
}

cmd_new() {
  local task_id bootstrap root parent target branch
  task_id="${1:-}"
  shift || true
  bootstrap=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -Bootstrap|--bootstrap)
        bootstrap=true
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for new: $1"
        ;;
    esac
    shift
  done

  [[ -n "$task_id" ]] || die "Missing <task-id> for new."

  root="$(repo_root)"
  validate_head_attached
  warn_longpaths_if_needed

  branch="task/$task_id"
  parent="$(worktree_parent "$root")"
  target="$parent/$task_id"

  branch_exists "$branch" && die "Branch already exists: $branch"
  [[ ! -e "$target" ]] || die "Target directory already exists: $target"

  mkdir -p "$parent"
  git worktree add -b "$branch" "$target" HEAD

  if [[ -f "$root/.env" ]]; then
    cp "$root/.env" "$target/.env"
  fi

  if [[ "$bootstrap" == true ]]; then
    bootstrap_worktree "$target"
  fi

  echo "$target"
}

cmd_list() {
  repo_root >/dev/null

  local path branch dirty
  while IFS=$'\t' read -r path branch; do
    [[ -n "${path:-}" ]] || continue
    if [[ -n "$(git -C "$path" status --porcelain 2>/dev/null || true)" ]]; then
      dirty="dirty"
    else
      dirty="clean"
    fi
    printf '%s\t%s\t%s\n' "$path" "${branch:-detached}" "$dirty"
  done < <(git worktree list --porcelain | awk '
    /^worktree / {path = substr($0, 10)}
    /^branch / {branch = substr($0, 8)}
    /^detached$/ {branch = "detached"}
    /^$/ {
      if (path != "") {
        print path "\t" branch
      }
      path = ""
      branch = ""
    }
    END {
      if (path != "") {
        print path "\t" branch
      }
    }
  ')
}

cmd_remove() {
  local task_id force root parent target branch
  task_id="${1:-}"
  shift || true
  force=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -Force|--force)
        force=true
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for remove: $1"
        ;;
    esac
    shift
  done

  [[ -n "$task_id" ]] || die "Missing <task-id> for remove."

  root="$(repo_root)"
  parent="$(worktree_parent "$root")"
  target="$parent/$task_id"
  branch="task/$task_id"

  [[ -d "$target" ]] || die "Worktree directory does not exist: $target"

  if [[ "$force" == true ]]; then
    git worktree remove --force "$target"
  else
    git worktree remove "$target"
  fi

  if branch_exists "$branch"; then
    if git merge-base --is-ancestor "$branch" HEAD >/dev/null 2>&1; then
      git branch -d "$branch"
    elif [[ "$force" == true ]]; then
      git branch -D "$branch"
    else
      warn "Branch $branch is unmerged; leaving branch in place (use --force to delete)."
    fi
  fi
}

cmd_prune() {
  repo_root >/dev/null
  git worktree prune
}

main() {
  local verb
  verb="${1:-}"

  case "$verb" in
    new)
      shift
      cmd_new "$@"
      ;;
    list)
      shift
      cmd_list "$@"
      ;;
    remove)
      shift
      cmd_remove "$@"
      ;;
    prune)
      shift
      cmd_prune "$@"
      ;;
    -h|--help|'')
      usage
      ;;
    *)
      die "Unknown verb: $verb"
      ;;
  esac
}

main "$@"
