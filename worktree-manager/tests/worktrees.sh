#!/usr/bin/env bash
# Dependency-free integration tests. All mutations stay in a fresh temp directory.
set -euo pipefail
script=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/worktrees.sh
fixture=$(mktemp -d "${TMPDIR:-/tmp}/mise-worktrees.XXXXXX")
# Canonicalize /var -> /private/var on macOS, just as Git does.
fixture=$(cd "$fixture" && pwd -P)
export WT_REPOS_ROOT="$fixture/repos with spaces"
export WT_TASKS_ROOT="$fixture/tasks with spaces"
mkdir "$WT_REPOS_ROOT" "$WT_TASKS_ROOT"
# Isolate tests from user Git config/hooks and ambient Git context.
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
export GIT_AUTHOR_NAME='Worktree Test' GIT_AUTHOR_EMAIL='test@example.invalid'
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
printf 'Test fixtures (retained for inspection): %s\n' "$fixture"
trap 'printf "Fixtures: %s\n" "$fixture"' EXIT
wt() { bash "$script" "$@"; }
check() { "$@" || { printf 'ASSERTION FAILED: %s\n' "$*" >&2; exit 1; }; }
reject() {
    if "$@" > "$fixture/rejected.log" 2>&1; then
        printf 'EXPECTED FAILURE: %s\n' "$*" >&2; exit 1
    fi
}
contains() { grep -F -- "$2" "$1" >/dev/null; }
init() {
    git init -q -b "$2" "$WT_REPOS_ROOT/$1"
    printf 'initial\n' > "$WT_REPOS_ROOT/$1/tracked"
    git -C "$WT_REPOS_ROOT/$1" add tracked
    git -C "$WT_REPOS_ROOT/$1" commit -qm initial
}
init api main
init auth master
init custom develop
init 'front end' main
init upstream trunk
# Recorded non-main remote default, and discovery via ls-remote when not recorded.
git -C "$WT_REPOS_ROOT/custom" remote add origin "$WT_REPOS_ROOT/custom"
git -C "$WT_REPOS_ROOT/custom" fetch -q origin
git -C "$WT_REPOS_ROOT/custom" symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/develop
git -C "$WT_REPOS_ROOT/upstream" remote add origin "$WT_REPOS_ROOT/upstream"
# A discoverable source repository with a .git FILE, not directory.
git -C "$WT_REPOS_ROOT/api" worktree add -qb source-alias "$WT_REPOS_ROOT/linked"
# Originals can be dirty and on unrelated branches; neither is changed.
git -C "$WT_REPOS_ROOT/api" switch -qc original
printf 'original branch only\n' > "$WT_REPOS_ROOT/api/original-only"
git -C "$WT_REPOS_ROOT/api" add original-only
git -C "$WT_REPOS_ROOT/api" commit -qm 'unrelated original branch commit'
printf 'original dirty change\n' >> "$WT_REPOS_ROOT/api/tracked"
printf 'original untracked\n' > "$WT_REPOS_ROOT/api/untracked"
before=$(git -C "$WT_REPOS_ROOT/api" status --porcelain)

wt list > "$fixture/list-empty.log"
check contains "$fixture/list-empty.log" 'No task workspaces'
wt create first api auth custom 'front end' upstream > "$fixture/create.log"
for repo in api auth custom 'front end' upstream; do
    path=$WT_TASKS_ROOT/first/$repo
    check test -f "$path/.git"
    check test "$(git -C "$path" branch --show-current)" = task/first
    base=HEAD
    [[ $repo != api ]] || base=main
    check test "$(git -C "$path" rev-parse HEAD)" = "$(git -C "$WT_REPOS_ROOT/$repo" rev-parse "$base")"
done
# Repeated create, add, and duplicate names are harmless.
wt create first api api > "$fixture/repeat.log"
check contains "$fixture/repeat.log" 'already included'
wt create linked-file linked linked > "$fixture/add.log"
check test -f "$WT_TASKS_ROOT/linked-file/linked/.git"
# Two source directories sharing one repository cannot check out the same branch.
reject wt add first linked
check contains "$fixture/rejected.log" 'checked out at'
wt create second api auth > "$fixture/second.log"
check test "$(git -C "$WT_TASKS_ROOT/second/api" branch --show-current)" = task/second
check test "$(git -C "$WT_REPOS_ROOT/api" branch --show-current)" = original
check test "$(git -C "$WT_REPOS_ROOT/api" status --porcelain)" = "$before"
wt list > "$fixture/list.log"
check contains "$fixture/list.log" first
check contains "$fixture/list.log" 'front end'
wt status first > "$fixture/status.log"
check contains "$fixture/status.log" task/first

# Interactive numbered selection, whitespace, deduplication, invalid inputs.
# Sorted menu: api, auth, custom, front end, linked, upstream.
printf '1 2 4 4\n' | wt create interactive > "$fixture/menu.log"
check test -f "$WT_TASKS_ROOT/interactive/front end/.git"
check test ! -e "$WT_TASKS_ROOT/interactive/custom"
reject bash "$script" create no-input < /dev/null
check test ! -e "$WT_TASKS_ROOT/no-input"
for selection in 0 999999 x '1;touch bad'; do
    if printf '%s\n' "$selection" | wt create invalid-menu > "$fixture/menu-bad.log" 2>&1; then exit 1; fi
done
check test ! -e "$WT_TASKS_ROOT/invalid-menu"
for task in ../escape /absolute -option 'has space' a..b a.lock a/child; do
    reject wt create "$task" api
done
reject env WT_TASKS_ROOT="$WT_REPOS_ROOT/." bash "$script" create same-root api
reject wt create unknown api missing
check test ! -e "$WT_TASKS_ROOT/unknown"
mkdir "$WT_TASKS_ROOT/unrelated"
printf 'keep\n' > "$WT_TASKS_ROOT/unrelated/file"
reject wt create unrelated api
reject wt remove unrelated
check test -f "$WT_TASKS_ROOT/unrelated/file"
ln -s "$WT_TASKS_ROOT/first" "$WT_TASKS_ROOT/alias"
reject wt remove alias
rm "$WT_TASKS_ROOT/alias"
reject env WT_TASKS_ROOT="$WT_REPOS_ROOT/api/tasks" bash "$script" create inside api
check test ! -e "$WT_REPOS_ROOT/api/tasks"

# Existing branch reuse and a checked-out-elsewhere conflict with partial success.
git -C "$WT_REPOS_ROOT/auth" branch task/reuse master
wt create reuse auth > "$fixture/reuse.log"
check contains "$fixture/reuse.log" 'reused task/reuse'
git -C "$WT_REPOS_ROOT/api" worktree add -qb task/conflict "$fixture/outside"
reject wt create conflict auth api
check contains "$fixture/rejected.log" "$fixture/outside"
check contains "$fixture/rejected.log" 'successful worktrees and branches were kept'
check test -f "$WT_TASKS_ROOT/conflict/auth/.git"
check test ! -e "$WT_TASKS_ROOT/conflict/api"
git -C "$WT_REPOS_ROOT/api" worktree remove "$fixture/outside"
wt add conflict api > "$fixture/conflict-retry.log"
check contains "$fixture/conflict-retry.log" 'reused task/conflict'

# Dirty LAST repository: full preflight must leave even the clean first one.
printf 'dirty\n' >> "$WT_TASKS_ROOT/second/auth/tracked"
reject wt remove second
check contains "$fixture/rejected.log" 'UNSAFE auth'
check test -f "$WT_TASKS_ROOT/second/api/.git"
git -C "$WT_TASKS_ROOT/second/auth" restore tracked
printf 'valuable\n' > "$WT_TASKS_ROOT/second/auth/untracked"
reject wt remove second
check test -f "$WT_TASKS_ROOT/second/api/.git"
rm "$WT_TASKS_ROOT/second/auth/untracked"
# Staged and ignored files are protected too.
printf 'staged\n' >> "$WT_TASKS_ROOT/second/auth/tracked"
git -C "$WT_TASKS_ROOT/second/auth" add tracked
reject wt remove second
git -C "$WT_TASKS_ROOT/second/auth" restore --staged --worktree tracked
printf 'local.secret\n' >> "$WT_REPOS_ROOT/auth/.git/info/exclude"
printf 'secret\n' > "$WT_TASKS_ROOT/second/auth/local.secret"
reject wt remove second
check contains "$fixture/rejected.log" 'local.secret'
rm "$WT_TASKS_ROOT/second/auth/local.secret"
# Unrecognized entries and locked worktrees prevent any removal.
printf 'keep\n' > "$WT_TASKS_ROOT/second/unrelated"
reject wt remove second
check test -f "$WT_TASKS_ROOT/second/api/.git"
rm "$WT_TASKS_ROOT/second/unrelated"
git -C "$WT_REPOS_ROOT/auth" worktree lock "$WT_TASKS_ROOT/second/auth"
reject wt remove second
check contains "$fixture/rejected.log" 'locked'
check test -f "$WT_TASKS_ROOT/second/api/.git"
git -C "$WT_REPOS_ROOT/auth" worktree unlock "$WT_TASKS_ROOT/second/auth"
wt remove second > "$fixture/remove.log"
check test ! -e "$WT_TASKS_ROOT/second"
check git -C "$WT_REPOS_ROOT/api" show-ref --verify --quiet refs/heads/task/second
check git -C "$WT_REPOS_ROOT/auth" show-ref --verify --quiet refs/heads/task/second
reject wt remove second
# Removal/recreation preserves branch commits, not just branch names.
printf 'task work\n' >> "$WT_TASKS_ROOT/reuse/auth/tracked"
git -C "$WT_TASKS_ROOT/reuse/auth" commit -qam 'task work'
saved=$(git -C "$WT_TASKS_ROOT/reuse/auth" rev-parse HEAD)
wt remove reuse > /dev/null
wt create reuse auth > /dev/null
check test "$(git -C "$WT_TASKS_ROOT/reuse/auth" rev-parse HEAD)" = "$saved"

# An existing unrelated destination must not be overwritten.
mkdir "$WT_TASKS_ROOT/first/blocker"
reject wt add first blocker
check test -d "$WT_TASKS_ROOT/first/blocker"
rmdir "$WT_TASKS_ROOT/first/blocker"
# Real known repository with a destination symlink must also be rejected.
wt create destination auth > /dev/null
ln -s "$WT_REPOS_ROOT/api" "$WT_TASKS_ROOT/destination/api"
reject wt add destination api
check test -L "$WT_TASKS_ROOT/destination/api"
rm "$WT_TASKS_ROOT/destination/api"

# Smoke-test included Mise definitions, argument forwarding, and raw stdin.
if command -v mise >/dev/null 2>&1; then
    mise run wt:create via-mise api 'front end' > "$fixture/mise-create.log"
    check test -f "$WT_TASKS_ROOT/via-mise/front end/.git"
    reject mise run wt:create ../unsafe api
    printf '2\n' | mise run wt:add via-mise > "$fixture/mise-menu.log"
    mise -C "$fixture" run wt:list > "$fixture/mise-list.log"
    check contains "$fixture/mise-list.log" via-mise
    mise run wt:status via-mise > "$fixture/mise-status.log"
    check contains "$fixture/mise-status.log" task/via-mise
    mise run wt:remove via-mise > "$fixture/mise-remove.log"
    check test ! -e "$WT_TASKS_ROOT/via-mise"
fi
for task in first interactive conflict reuse destination linked-file; do wt remove "$task" > /dev/null; done
check test "$(git -C "$WT_REPOS_ROOT/api" status --porcelain)" = "$before"
check test "$(git -C "$WT_REPOS_ROOT/api" branch --show-current)" = original
printf '\nPASS: worktree integration tests\n'
