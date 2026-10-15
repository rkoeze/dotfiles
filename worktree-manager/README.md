# Task workspaces with Git worktrees

Global Mise tasks create multi-repository workspaces using only Bash and Git.
They are available from any directory; no additional worktree manager is needed.

## Quick start

```bash
# Numbered selection menu (enter e.g. 1 3 5)
mise run wt:create add-sso

# Or supply repository directory names explicitly (no prompts)
mise run wt:create add-sso dlx-server dlx-ui dl-auth-client
mise run wt:add add-sso apphub

# Add interactively; already-included repositories are harmless
mise run wt:add add-sso

mise run wt:list
mise run wt:status add-sso
mise run wt:remove add-sso
```

The example creates:

```text
~/Development/tasks/add-sso/
├── .wt-workspace          # Management marker; leave this file in place
├── dlx-server/            # Real Git worktree, branch task/add-sso
├── dlx-ui/                # Real Git worktree, branch task/add-sso
├── dl-auth-client/        # Real Git worktree, branch task/add-sso
└── apphub/                # Real Git worktree, branch task/add-sso
```

Open `~/Development/tasks/add-sso` in your editor or coding agent. Work only
inside its repository subdirectories. Another task can include the same
repositories on its own `task/<name>` branches. Worktrees share Git objects and
refs, but have independent working files, indexes, and checked-out branches.

Discovery lists Git repositories that are **direct children** of the repository
root, alphabetically. It accepts both `.git` directories and files. In this
setup `dlx-server` is one repository; its individual service directories are not
separate repositories. Nested clones and submodules are not discovered recursively.
Quote repository names containing spaces when supplying them as arguments.

## Configuration

| Environment variable | Default |
| --- | --- |
| `WT_REPOS_ROOT` | `$HOME/Development` |
| `WT_TASKS_ROOT` | `$HOME/Development/tasks` |

Both must be absolute paths. The tasks root must be outside Git repositories
and different from the repository root. Root directories may contain spaces.
The two settings are independent; changing the repository root does not change
the default tasks root. Use the same settings across commands.

For a one-off alternative layout:

```bash
WT_REPOS_ROOT="$HOME/code/repos" WT_TASKS_ROOT="$HOME/code/tasks" \
  mise run wt:create fix-billing api billing-service
```

For persistent configuration, export the variables in your shell configuration,
or add them to the `[env]` section of your Mise configuration:

```toml
[env]
WT_REPOS_ROOT = "{{env.HOME}}/code/repos"
WT_TASKS_ROOT = "{{env.HOME}}/code/tasks"
```

Task names must start with an ASCII letter or digit and otherwise contain only
letters, digits, `.`, `_`, or `-`. They must also be valid Git branch suffixes:
no slashes, `..`, trailing dots, or `.lock` suffixes. Example: `AD1-1234-add-sso`.

## Branch behavior

- Each repository uses `task/<task-name>`. Existing branches are reused.
- Existing workspace members are skipped, never reset or switched. If you have
  manually changed a member's branch, `wt:status` shows its actual branch.
- A branch checked out elsewhere is reported with that worktree's path; the
  command does not force a second checkout. Two source directory names pointing
  to the same underlying repository are subject to this same Git restriction.
- New branches use a remote's recorded default (`refs/remotes/origin/HEAD`, then
  other remotes). If a remote has no recorded HEAD, the script queries it with
  `git ls-remote --symref`, preferring its local remote-tracking branch and then
  its local branch. If remotes are unavailable or absent, local `main`, then
  `master`, are the fallback. An identified default without a local commit is
  an error, not permission to use a different branch.
- No automatic fetch occurs. Remote queries may require network access; Git
  credential prompting is disabled for those queries. SSH authentication remains
  subject to your SSH configuration. For offline use, ensure the remote HEAD
  and its target commit are already available locally. To configure these
  deliberately, outside this workflow, use e.g. `git fetch origin` and
  `git remote set-head origin -a` in the original repository.
- The manager never checks out, resets, commits, merges, rebases, pushes, or
  deletes branches in the original repositories. Like any native worktree
  operation, it updates shared Git metadata. Existing Git hooks still apply.

## Safety and recovery

`wt:remove` checks **all** members before removing **any** of them. Staged,
unstaged, untracked, **and ignored** files block removal, as do locked worktrees
and unrecognized entries. It lists the outstanding issues and leaves everything
in place. Ignored build outputs and local `.env` files count intentionally;
move valuable files elsewhere and remove disposable files yourself before retrying.
`wt:status` uses normal Git short status; inspect ignored files with
`git -C <worktree> status --short --ignored` if needed.

Removal uses native `git worktree remove`, without force. Branches and their
commits are preserved. The task folder is removed only after its worktrees are
gone, using `rmdir` rather than recursive deletion. Git may impose additional
restrictions (for example, initialized submodules); those refusals are reported,
and metadata is kept so removal can be retried. Do not edit files or run competing
workspace operations during removal.

The `.wt-workspace` marker distinguishes managed folders from unrelated data.
Existing unmarked task folders, symlinked workspaces, and conflicting destinations
are not overwritten or deleted. Keep notes or other workspace-level files safe:
extra entries at the task root block removal rather than being silently erased.

If creation or addition partially fails, successful worktrees and branches remain
available. Output lists successes, failures, and the resulting workspace; the
command exits nonzero. Resolve the reported issue and run:

```bash
mise run wt:add add-sso failed-repo-name
```

Repeated create/add commands skip existing valid members. Removing a missing
workspace reports an error without touching anything. Empty managed workspaces
left by a completely failed creation can be safely removed with `wt:remove`.

## Implementation and tests

All manager files live together:

```text
~/worktree-manager/
├── worktrees.sh
├── tasks.toml
├── README.md
└── tests/
    └── worktrees.sh
```

`worktrees.sh` handles command dispatch, selection, and Git operations.
`tasks.toml` defines the five `wt:*` commands and delegates to that script.
There are no separate launcher scripts under Mise's task directory.

The global `~/.config/mise/config.toml` includes the definitions:

```toml
[task_config]
includes = ["~/.config/mise/tasks", "~/worktree-manager/tasks.toml"]
```

The first entry preserves your existing global file tasks. Explicit includes
replace Mise's default task-directory search list; add any other task directories
there if you use them later. Keep unrelated existing Mise configuration unchanged.

Track `~/worktree-manager/` and `~/.config/mise/config.toml` in your dotfiles.
The script is compatible with macOS Bash 3.2; tasks use raw terminal I/O so
numbered selection also works through Mise. No tool installations are required.
For direct use without Mise:

```bash
bash ~/worktree-manager/worktrees.sh create add-sso dlx-server dlx-ui
```

Run the tests with:

```bash
/bin/bash ~/worktree-manager/tests/worktrees.sh
```

Tests use fresh temporary repositories, exercise real Mise tasks when available,
and leave fixtures under the printed temporary path for inspection. They do not
modify your development repositories. Coverage includes menus and explicit
selection, overlapping tasks, adding, listing, status, main/master/custom defaults,
remote-default discovery, branch reuse/conflicts, `.git` files, paths with spaces,
partial failures, invalid inputs, destination protection, and safe removal.
