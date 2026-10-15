#!/usr/bin/env bash
# Shared implementation for the global wt:* Mise tasks. Compatible with Bash 3.2.
set -euo pipefail
export LC_ALL=C
export GIT_OPTIONAL_LOCKS=0
# Inherited Git context must not redirect commands away from the explicit -C paths.
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
shopt -s nullglob dotglob

repo_root=${WT_REPOS_ROOT:-"$HOME/Development"}
tasks_root=${WT_TASKS_ROOT:-"$HOME/Development/tasks"}
marker=.wt-workspace
version='mise-worktree-workspace-v1'
fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }
exists() { [[ -e $1 || -L $1 ]]; }
usage() {
    printf '%s\n' 'Usage: worktrees.sh create|add <task> [repo ...]' \
        '       worktrees.sh list' '       worktrees.sh status|remove <task>' \
        'Roots: WT_REPOS_ROOT (~/Development), WT_TASKS_ROOT (~/Development/tasks)'
}
valid_task() {
    [[ $1 =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] &&
        git check-ref-format "refs/heads/task/$1" >/dev/null 2>&1
}
managed() {
    [[ -d $1 && ! -L $1 && -f $1/$marker && ! -L $1/$marker ]] &&
        [[ $(<"$1/$marker") == "$version" ]]
}
# Normalize existing directories without realpath (not available on older macOS).
canonical() { (cd -- "$1" && pwd -P); }

# Read Git's NUL-delimited format so spaces and quoted paths are safe.
registered() {
    local repo=$1 target=$2 field
    while IFS= read -r -d '' field; do
        [[ $field != "worktree $target" ]] || return 0
    done < <(git -C "$repo" worktree list --porcelain -z)
    return 1
}
branch_location() {
    local repo=$1 ref=$2 field location=''
    while IFS= read -r -d '' field; do
        case $field in
            'worktree '*) location=${field#worktree } ;;
            "branch $ref") printf '%s\n' "$location"; return 0 ;;
        esac
    done < <(git -C "$repo" worktree list --porcelain -z)
    return 1
}
# Require a registered worktree with a .git file; reject symlinks and ordinary clones.
member() {
    local path=$1 top
    [[ -d $path && ! -L $path && -f $path/.git && ! -L $path/.git ]] || return 1
    top=$(git -C "$path" rev-parse --show-toplevel 2>/dev/null) || return 1
    [[ $(canonical "$path") == "$top" ]] && registered "$path" "$top"
}

# Prefer a remote's recorded default, then ask the remote if it has no HEAD ref.
# No fetch: creating worktrees never changes existing refs or original checkouts.
default_base() {
    local repo=$1 remote ref line head
    local remotes=()
    if git -C "$repo" remote get-url origin >/dev/null 2>&1; then remotes+=(origin); fi
    while IFS= read -r remote; do
        [[ -z $remote || $remote == origin ]] || remotes+=("$remote")
    done < <(git -C "$repo" remote)
    for remote in "${remotes[@]+${remotes[@]}}"; do
        ref=$(git -C "$repo" symbolic-ref -q "refs/remotes/$remote/HEAD" || :)
        if [[ -n $ref ]]; then
            if git -C "$repo" rev-parse --verify "$ref^{commit}" >/dev/null 2>&1; then
                printf '%s\n' "$ref"; return 0
            fi
            printf 'Default ref %s has no local commit; fetch it first.\n' "$ref" >&2
            return 1
        fi
        head=''
        # Avoid credential prompts; unavailable remotes fall back to local main/master.
        while IFS= read -r line; do
            if [[ $line == 'ref: refs/heads/'*$'\tHEAD' ]]; then
                head=${line#ref: refs/heads/}; head=${head%$'\tHEAD'}
            fi
        done < <(GIT_TERMINAL_PROMPT=0 git -C "$repo" ls-remote --symref "$remote" HEAD 2>/dev/null || :)
        if [[ -n $head ]]; then
            for ref in "refs/remotes/$remote/$head" "refs/heads/$head"; do
                if git -C "$repo" rev-parse --verify "$ref^{commit}" >/dev/null 2>&1; then
                    printf '%s\n' "$ref"; return 0
                fi
            done
            printf 'Remote default %s is not available locally; fetch it first.\n' "$head" >&2
            return 1
        fi
    done
    for ref in refs/heads/main refs/heads/master; do
        if git -C "$repo" rev-parse --verify "$ref^{commit}" >/dev/null 2>&1; then
            printf '%s\n' "$ref"; return 0
        fi
    done
    printf 'Cannot determine default branch; configure a remote HEAD or create main/master.\n' >&2
    return 1
}

discover() {
    local path name
    available=()
    [[ -d $repo_root ]] || fail "Repository root does not exist: $repo_root"
    repo_root=$(canonical "$repo_root")
    for path in "$repo_root"/*; do
        name=${path##*/}
        [[ -d $path && ( -d $path/.git || -f $path/.git ) ]] || continue
        [[ $name != "$marker" && $name != *$'\n'* && $name != *$'\r'* && $name != *$'\t'* ]] || continue
        git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1 || continue
        available+=("$name")
    done
    [[ ${#available[@]} -gt 0 ]] || fail "No Git repositories found in $repo_root"
}
select_repos() {
    local name candidate found token index line
    local tokens=()
    selected=()
    if [[ $# -eq 0 ]]; then
        printf 'Select repositories:\n\n'
        for ((index=0; index<${#available[@]}; index++)); do
            printf '%d) %s\n' "$((index+1))" "${available[index]}"
        done
        printf '\nEnter numbers (space-separated): '
        IFS= read -r line || fail 'No selection received; supply repository names for automation.'
        read -r -a tokens <<< "$line"
        [[ ${#tokens[@]} -gt 0 ]] || fail 'Select at least one repository.'
        for token in "${tokens[@]}"; do
            [[ $token =~ ^[0-9]+$ && ${#token} -le 6 ]] || fail "Invalid selection: $token"
            index=$((10#$token))
            ((index >= 1 && index <= ${#available[@]})) || fail "Invalid selection: $token"
            selected+=("${available[index-1]}")
        done
    else
        selected=("$@")
    fi
    # Validate all names before creating anything; also deduplicate selections.
    tokens=()
    for name in "${selected[@]}"; do
        found=false
        for candidate in "${available[@]}"; do
            [[ $name != "$candidate" ]] || found=true
        done
        $found || fail "Unknown repository: $name"
        found=false
        for candidate in "${tokens[@]+${tokens[@]}}"; do
            [[ $name != "$candidate" ]] || found=true
        done
        $found || tokens+=("$name")
    done
    selected=("${tokens[@]}")
}

create_members() {
    local name repo path location base failures=0
    for name in "${selected[@]}"; do
        repo=$repo_root/$name; path=$workspace/$name
        if exists "$path"; then
            if member "$path" && registered "$repo" "$path"; then
                printf '= %s (already included)\n' "$name"
            else
                printf 'FAIL %s: destination exists and is not this repository’s worktree.\n' "$name" >&2
                failures=$((failures+1))
            fi
            continue
        fi
        if location=$(branch_location "$repo" "refs/heads/$branch"); then
            printf 'FAIL %s: branch %s is checked out at %s\n' "$name" "$branch" "$location" >&2
            failures=$((failures+1)); continue
        fi
        if git -C "$repo" show-ref --verify --quiet "refs/heads/$branch"; then
            if git -C "$repo" worktree add -- "$path" "$branch"; then
                printf 'OK %s (reused %s)\n' "$name" "$branch"; continue
            fi
        elif base=$(default_base "$repo"); then
            if git -C "$repo" worktree add -b "$branch" -- "$path" "$base"; then
                printf 'OK %s (from %s)\n' "$name" "$base"; continue
            fi
        fi
        printf 'FAIL %s: could not finish worktree creation; inspect any destination before retrying.\n' "$name" >&2
        failures=$((failures+1))
    done
    printf '\nWorkspace: %s\nIncluded repositories:\n' "$workspace"
    for path in "$workspace"/*; do
        [[ ${path##*/} == "$marker" ]] && continue
        if member "$path"; then printf '  %s\n' "${path##*/}"; fi
    done
    if ((failures > 0)); then
        printf '%d repositories failed; successful worktrees and branches were kept. Retry with wt:add.\n' "$failures" >&2
        return 1
    fi
}

command=${1:-help}
[[ $# -eq 0 ]] || shift
case $command in
    help|--help|-h) usage; exit 0 ;;
    create|add|status|remove)
        [[ $# -ge 1 ]] || { usage >&2; exit 1; }
        task=$1; shift
        valid_task "$task" || fail "Unsafe task name: $task (use a single alphanumeric/dot/underscore/hyphen name valid as a Git branch)."
        branch=task/$task
        if [[ $command == status || $command == remove ]]; then
            [[ $# -eq 0 ]] || fail "Unexpected arguments for $command"
        fi ;;
    list) [[ $# -eq 0 ]] || fail 'wt:list takes no arguments' ;;
    *) usage >&2; exit 1 ;;
esac
[[ $repo_root == /* && $tasks_root == /* ]] || fail 'WT_REPOS_ROOT and WT_TASKS_ROOT must be absolute paths.'

if [[ $command == create || $command == add ]]; then
    discover
    # Do not allow the workspace root to be inside an original Git checkout.
    parent=$tasks_root
    while [[ ! -d $parent ]]; do
        [[ ! -L $parent ]] || fail "Broken symlink in tasks root: $parent"
        parent=${parent%/*}; [[ -n $parent ]] || parent=/
    done
    if git -C "$parent" rev-parse --git-dir >/dev/null 2>&1; then
        fail 'Tasks root must be outside existing Git repositories.'
    fi
    parent=$(canonical "$parent")
    if [[ -d $tasks_root && $(canonical "$tasks_root") == "$repo_root" ]]; then
        fail 'Repository and tasks roots must differ.'
    fi
    select_repos "$@"
    if [[ $command == add ]]; then
        [[ -d $tasks_root ]] || fail "Tasks root does not exist: $tasks_root"
    else
        mkdir -p -- "$tasks_root"
    fi
fi

if [[ ! -d $tasks_root ]]; then
    if [[ $command == list ]]; then printf 'No task workspaces in %s\n' "$tasks_root"; exit 0; fi
    fail "Tasks root does not exist: $tasks_root"
fi
tasks_root=$(canonical "$tasks_root")
if [[ $command == list ]]; then
    count=0
    for workspace in "$tasks_root"/*; do
        managed "$workspace" || continue
        printf '%s\n' "${workspace##*/}"
        for path in "$workspace"/*; do
            [[ ${path##*/} == "$marker" ]] && continue
            if member "$path"; then printf '  %s\n' "${path##*/}"
            else printf '  %s [unrecognized entry]\n' "${path##*/}"; fi
        done
        count=$((count+1))
    done
    ((count > 0)) || printf 'No task workspaces in %s\n' "$tasks_root"
    exit 0
fi
workspace=$tasks_root/$task
if [[ $command == create ]] && ! exists "$workspace"; then
    mkdir -- "$workspace"
    printf '%s\n' "$version" > "$workspace/$marker"
else
    managed "$workspace" || fail "Not a managed task workspace: $workspace (will not overwrite or remove it)."
fi
case $command in
    create|add) create_members ;;
    status)
        result=0
        for path in "$workspace"/*; do
            [[ ${path##*/} == "$marker" ]] && continue
            printf '\n== %s ==\n' "${path##*/}"
            if member "$path"; then
                git -C "$path" status --short --branch --untracked-files=all --ignore-submodules=none || result=1
            else printf 'Not a registered worktree.\n' >&2; result=1; fi
        done
        exit "$result" ;;
    remove)
        # Full preflight BEFORE removing any worktree. Include ignored files to
        # protect local .env files and build artifacts as well as untracked work.
        unsafe=0
        for path in "$workspace"/*; do
            [[ ${path##*/} == "$marker" ]] && continue
            if ! member "$path"; then
                printf 'UNSAFE %s: not a registered worktree.\n' "${path##*/}" >&2
                unsafe=1; continue
            fi
            if ! changes=$(git -C "$path" status --porcelain --untracked-files=all --ignored --ignore-submodules=none); then
                printf 'UNSAFE %s: cannot read Git status.\n' "${path##*/}" >&2
                unsafe=1; continue
            fi
            if [[ -n $changes ]]; then
                printf 'UNSAFE %s: outstanding changes (including untracked/ignored files):\n%s\n' "${path##*/}" "$changes" >&2
                unsafe=1
            fi
            lock=$(git -C "$path" rev-parse --git-path locked)
            if exists "$lock"; then printf 'UNSAFE %s: worktree is locked.\n' "${path##*/}" >&2; unsafe=1; fi
        done
        ((unsafe == 0)) || fail 'Nothing removed. Resolve the reported issues first.'
        result=0
        for path in "$workspace"/*; do
            [[ ${path##*/} == "$marker" ]] && continue
            if git -C "$path" worktree remove -- "$path"; then
                printf 'Removed %s\n' "${path##*/}"
            else printf 'FAIL %s: Git refused removal; workspace metadata kept.\n' "${path##*/}" >&2; result=1; fi
        done
        ((result == 0)) || exit 1
        # rmdir, not recursive deletion: unexpected new files are never erased.
        remaining=("$workspace"/*)
        [[ ${#remaining[@]} -eq 1 && ${remaining[0]} == "$workspace/$marker" ]] || fail 'Workspace has unexpected files; keeping directory and metadata.'
        rm -- "$workspace/$marker"
        rmdir -- "$workspace" || { printf '%s\n' "$version" > "$workspace/$marker"; fail 'Directory not empty; kept workspace metadata.'; }
        printf 'Removed workspace: %s (branches preserved)\n' "$workspace" ;;
esac
