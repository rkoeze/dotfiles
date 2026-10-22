# Task workspaces with Git worktrees

Global Mise tasks create multi-repository workspaces using Python 3.9+ and native
Git. Only Python's standard library is used: no pip packages, virtual environment,
or additional worktree manager is needed. Tasks are available from any directory.

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
├── dlx-server/            # Real Git worktree, branch add-sso
├── dlx-ui/                # Real Git worktree, branch add-sso
├── dl-auth-client/        # Real Git worktree, branch add-sso
└── apphub/                # Real Git worktree, branch add-sso
```

Open `~/Development/tasks/add-sso` in your editor or coding agent. Work only
inside its repository subdirectories. Another task can include the same
repositories on its own `<name>` branches. Worktrees share Git objects and
refs, but have independent working files, indexes, and checked-out branches.

Discovery lists Git repositories that are **direct children** of the repository
root, alphabetically. It accepts both `.git` directories and files. In this
setup `dlx-server` is one repository; its individual service directories are not
separate repositories. Nested clones and submodules are not discovered recursively.
Quote repository names containing spaces when supplying them as arguments.

## Check out an existing remote branch

Use `wt:checkout` for reviewing existing work instead of starting from the default
branch with `wt:create`:

```bash
mise run wt:checkout <branch> [repos...] [--remote <name>]

# Numbered repository picker, just like wt:create
mise run wt:checkout feature/fix-login

# Or select repositories explicitly (no prompts)
mise run wt:checkout feature/fix-login dlx-server dlx-ui
cd ~/Development/tasks/feature-fix-login/dlx-server

# Fetch from a different configured remote
mise run wt:checkout feature/fix-login dlx-server --remote upstream

mise run wt:status feature-fix-login
mise run wt:remove feature-fix-login
```

The command fetches the same named branch in each selected repository from
`origin` by default. **Only the workspace folder replaces `/` with `-`**:
`feature/fix-login` stays the Git branch name, while its workspace folder is
`feature-fix-login`. There is no separate task-name argument or `--task` flag.
Supply the branch name without `origin/`; PR URLs, hashes, tags, and refspecs are
not inputs. The derived folder must satisfy the task-name rules below.

- Omit repositories for a numbered picker, or supply one or more names.
  Missing branches are reported per repository, never replaced with default
  branches. Successful worktrees are kept even if another repository fails;
  the command exits nonzero if any repository fails.
- Can add repositories to an existing managed workspace. Existing members on
  the requested branch are skipped without fetching, resetting, or switching.
  If the workspace contains a different branch (including a slash-to-hyphen
  naming collision), checkout refuses to reuse it.
- Refuses an existing local branch outside the destination worktree, reporting
  its path if checked out elsewhere. It never resets that branch or overwrites
  conflicting destinations.
- Fetches only the requested branch, without fetching tags or submodules or
  updating existing local/remote-tracking branches. It updates Git's `FETCH_HEAD`;
  do not run concurrent fetches in the same repository during this operation.
- Creates no upstream tracking configuration. The original checkout stays
  untouched.
- A failed fetch creates no worktree or local branch for that repository, and
  never falls back to a stale ref. If every fetch fails, no workspace is created.
  For partial failures, resolve the errors and rerun `wt:checkout` with the same
  branch and failed repositories (or use the picker again).
- If worktree creation fails after fetching, inspect any retained workspace and
  branch before retrying. Empty managed workspaces can be removed with
  `wt:remove`; branches are always preserved. After removing a workspace, the
  preserved local branches will cause a fresh checkout to refuse rather than
  silently reset them.

Use the flattened folder name with `wt:status` and `wt:remove`.
`wt:add` still uses the folder name as its local branch and starts from defaults
when that branch does not exist; use `wt:checkout` to add repositories on the same
existing remote branch, especially when the branch name contains slashes.

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
letters, digits, `.`, `_`, or `-`. They must also be valid Git branch names:
no slashes, `..`, trailing dots, `.lock` suffixes, or the reserved name `HEAD`.
Example: `AD1-1234-add-sso`.

## Branch behavior

- For `wt:create` and `wt:add`, each new worktree uses the workspace folder name exactly as its branch name:
  `wt:create add-sso` uses branch `add-sso`, with no prefix. Existing branches
  with that exact name are reused.
- Existing worktrees on older `task/<name>` branches are not renamed or switched.
  Additional repositories added to those workspaces use the new unprefixed name.
- Create/add skip existing workspace members, never resetting or switching them. If you have
  manually changed a member's branch, `wt:status` shows its actual branch.
- A branch checked out elsewhere is reported with that worktree's path; the
  command does not force a second checkout. Two source directory names pointing
  to the same underlying repository are subject to this same Git restriction.
- New branches created by `wt:create`/`wt:add` use a remote's recorded default (`refs/remotes/origin/HEAD`, then
  other remotes). If a remote has no recorded HEAD, the script queries it with
  `git ls-remote --symref`, preferring its local remote-tracking branch and then
  its local branch. If remotes are unavailable or absent, local `main`, then
  `master`, are the fallback. An identified default without a local commit is
  an error, not permission to use a different branch.
- `wt:create` and `wt:add` do not fetch; `wt:checkout` explicitly fetches its source
  branch. Remote queries and fetches may require network access; Git credential
  prompting is disabled. SSH authentication remains
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
├── worktrees.py
├── tasks.toml
├── README.md
└── tests/
    └── test_worktrees.py
```

`worktrees.py` handles command dispatch with `argparse`, filesystem paths with
`pathlib`, and native Git commands with `subprocess` (no shell interpolation).
The existing `.wt-workspace` marker format is unchanged, so workspaces created
by the earlier Bash implementation remain usable without migration.
`tasks.toml` defines the six `wt:*` commands and delegates to that script.
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
Tasks invoke `python3` from your PATH and use raw terminal I/O so numbered
selection also works through Mise. Python 3.9+ and Git must be installed; there
are no third-party Python dependencies. For direct use without Mise:

```bash
python3 ~/worktree-manager/worktrees.py create add-sso dlx-server dlx-ui
```

Run the tests with:

```bash
python3 -B -m unittest discover -s ~/worktree-manager/tests -v
```

Tests use standard-library `unittest` and fresh `TemporaryDirectory` repositories,
automatically clean up only those disposable fixtures, and exercise real Mise
tasks when available. They do not modify your development repositories.
Coverage includes menus and explicit
selection, overlapping tasks, adding, listing, status, main/master/custom defaults,
remote-default discovery, branch reuse/conflicts, `.git` files, paths with spaces,
partial failures, invalid inputs, destination protection, and safe removal.
Checkout coverage includes exact remote branch commits, custom remotes, nested
branch names, original checkout/ref preservation, conflicts, stale-fetch failure,
existing workspace additions, picker/multiple-repository selection, slash-to-hyphen
folder mapping and collisions, partial-failure retries, recovery, and real Mise
argument forwarding and interactive input.
