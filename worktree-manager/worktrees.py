#!/usr/bin/env python3
"""A thin, standard-library-only orchestrator for native Git worktrees."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

MARKER = ".wt-workspace"
# Keep the Bash version's marker so existing workspaces require no migration.
VERSION = "mise-worktree-workspace-v1"


class WorkspaceError(Exception):
    """An actionable workspace or Git error."""


def git(repo, *args, check=True):
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        env.pop(key, None)
    env.update(LC_ALL="C", GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        ["git", "-C", str(repo), *map(str, args)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env,
    )
    # Decode without newline translation: porcelain -z paths must remain exact.
    result = subprocess.CompletedProcess(
        result.args, result.returncode, os.fsdecode(result.stdout), os.fsdecode(result.stderr)
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "Git command failed"
        raise WorkspaceError(f"{repo}: {detail}")
    return result


def exists(path):
    return path.exists() or path.is_symlink()


def managed(path):
    marker = path / MARKER
    if path.is_symlink() or not path.is_dir() or marker.is_symlink() or not marker.is_file():
        return False
    try:
        return marker.read_text(encoding="utf-8").rstrip("\n") == VERSION
    except (OSError, UnicodeError):
        return False


def entries(workspace):
    return sorted((p for p in workspace.iterdir() if p.name != MARKER), key=lambda p: p.name)


def worktrees(repo):
    records = []
    record = {}
    for field in git(repo, "worktree", "list", "--porcelain", "-z").stdout.split("\0"):
        if field:
            key, _, value = field.partition(" ")
            record[key] = value
        elif record:
            records.append(record)
            record = {}
    return records


def registered(repo, path):
    return any(record.get("worktree") == str(path) for record in worktrees(repo))


def member(path):
    """Accept registered worktrees with .git files, not symlinks or ordinary clones."""
    dotgit = path / ".git"
    if path.is_symlink() or not path.is_dir() or dotgit.is_symlink() or not dotgit.is_file():
        return False
    try:
        top = git(path, "rev-parse", "--show-toplevel").stdout.rstrip("\n")
        return str(path.resolve()) == top and registered(path, path.resolve())
    except WorkspaceError:
        return False


def has_commit(repo, ref):
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False).returncode == 0


def default_base(repo):
    """Prefer remote defaults without fetching or changing existing refs."""
    remotes = git(repo, "remote").stdout.splitlines()
    if "origin" in remotes:
        remotes.remove("origin")
        remotes.insert(0, "origin")
    for remote in remotes:
        recorded = git(repo, "symbolic-ref", "-q", f"refs/remotes/{remote}/HEAD", check=False)
        if recorded.returncode == 0:
            ref = recorded.stdout.rstrip("\n")
            if has_commit(repo, ref):
                return ref
            raise WorkspaceError(f"Default ref {ref} has no local commit; fetch it first.")
        query = git(repo, "ls-remote", "--symref", remote, "HEAD", check=False)
        if query.returncode:
            continue  # Offline/unavailable remotes fall back to local main/master.
        for line in query.stdout.splitlines():
            if line.startswith("ref: refs/heads/") and line.endswith("\tHEAD"):
                head = line[len("ref: refs/heads/"):-len("\tHEAD")]
                for ref in (f"refs/remotes/{remote}/{head}", f"refs/heads/{head}"):
                    if has_commit(repo, ref):
                        return ref
                raise WorkspaceError(f"Remote default {head} is not available locally; fetch it first.")
    for ref in ("refs/heads/main", "refs/heads/master"):
        if has_commit(repo, ref):
            return ref
    raise WorkspaceError("Cannot determine default branch; configure a remote HEAD or create main/master.")


def discover(repo_root):
    if not repo_root.is_dir():
        raise WorkspaceError(f"Repository root does not exist: {repo_root}")
    available = []
    for path in sorted(repo_root.iterdir(), key=lambda p: p.name):
        if path.name == MARKER or any(c in path.name for c in "\n\r\t"):
            continue
        if path.is_dir() and ((path / ".git").is_dir() or (path / ".git").is_file()):
            result = git(path, "rev-parse", "--is-inside-work-tree", check=False)
            if result.returncode == 0 and result.stdout.strip() == "true":
                available.append(path.name)
    if not available:
        raise WorkspaceError(f"No Git repositories found in {repo_root}")
    return available


def select_repos(available, requested):
    if not requested:
        print("Select repositories:\n")
        for index, name in enumerate(available, 1):
            print(f"{index}) {name}")
        try:
            tokens = input("\nEnter numbers (space-separated): ").split()
        except EOFError:
            raise WorkspaceError("No selection received; supply repository names for automation.") from None
        if not tokens:
            raise WorkspaceError("Select at least one repository.")
        requested = []
        for token in tokens:
            if not re.fullmatch(r"[0-9]{1,6}", token) or not 1 <= int(token) <= len(available):
                raise WorkspaceError(f"Invalid selection: {token}")
            requested.append(available[int(token) - 1])
    for name in requested:
        if name not in available:
            raise WorkspaceError(f"Unknown repository: {name}")
    return list(dict.fromkeys(requested))


def validate_roots(repo_root, tasks_root):
    if repo_root == tasks_root:
        raise WorkspaceError("Repository and tasks roots must differ.")
    parent = tasks_root
    while not parent.is_dir():
        if exists(parent):
            raise WorkspaceError(f"Tasks root has a non-directory ancestor: {parent}")
        parent = parent.parent
    if git(parent, "rev-parse", "--git-dir", check=False).returncode == 0:
        raise WorkspaceError("Tasks root must be outside existing Git repositories.")


def create_members(workspace, repo_root, selected, branch):
    failures = 0
    for name in selected:
        repo, path = repo_root / name, workspace / name
        try:
            if exists(path):
                if member(path) and registered(repo, path):
                    print(f"= {name} (already included)")
                    continue
                raise WorkspaceError("Destination exists and is not this repository's worktree.")
            location = next((r["worktree"] for r in worktrees(repo)
                             if r.get("branch") == f"refs/heads/{branch}"), None)
            if location:
                raise WorkspaceError(f"Branch {branch} is checked out at {location}")
            if git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0:
                git(repo, "worktree", "add", "--", path, branch)
                print(f"OK {name} (reused {branch})")
            else:
                base = default_base(repo)
                git(repo, "worktree", "add", "-b", branch, "--", path, base)
                print(f"OK {name} (from {base})")
        except (WorkspaceError, OSError) as error:
            print(f"FAIL {name}: {error}", file=sys.stderr)
            failures += 1
    print(f"\nWorkspace: {workspace}\nIncluded repositories:")
    for path in entries(workspace):
        if member(path):
            print(f"  {path.name}")
    if failures:
        print(f"{failures} repositories failed; successful worktrees and branches were kept. "
              "Inspect failed destinations before retrying with wt:add.", file=sys.stderr)
    return int(bool(failures))


def list_workspaces(tasks_root):
    count = 0
    if tasks_root.is_dir():
        for workspace in sorted(tasks_root.iterdir(), key=lambda p: p.name):
            if managed(workspace):
                print(workspace.name)
                for path in entries(workspace):
                    suffix = "" if member(path) else " [unrecognized entry]"
                    print(f"  {path.name}{suffix}")
                count += 1
    if not count:
        print(f"No task workspaces in {tasks_root}")
    return 0


def status(workspace):
    result = 0
    for path in entries(workspace):
        print(f"\n== {path.name} ==")
        try:
            if not member(path):
                raise WorkspaceError("Not a registered worktree.")
            print(git(path, "status", "--short", "--branch", "--untracked-files=all",
                      "--ignore-submodules=none").stdout, end="")
        except WorkspaceError as error:
            print(f"{path.name}: {error}", file=sys.stderr)
            result = 1
    return result


def remove(workspace):
    paths = entries(workspace)
    unsafe = False
    # Preflight ALL worktrees before removing ANY. Protect ignored .env/build files too.
    for path in paths:
        try:
            if not member(path):
                raise WorkspaceError("Not a registered worktree.")
            changes = git(path, "status", "--porcelain", "--untracked-files=all", "--ignored",
                          "--ignore-submodules=none").stdout
            if changes:
                print(f"UNSAFE {path.name}: outstanding changes (including untracked/ignored files):\n"
                      f"{changes}", file=sys.stderr, end="")
                unsafe = True
            lock = Path(git(path, "rev-parse", "--git-path", "locked").stdout.rstrip("\n"))
            if exists(lock if lock.is_absolute() else path / lock):
                raise WorkspaceError("Worktree is locked.")
        except (WorkspaceError, OSError) as error:
            print(f"UNSAFE {path.name}: {error}", file=sys.stderr)
            unsafe = True
    if unsafe:
        raise WorkspaceError("Nothing removed. Resolve the reported issues first.")
    failures = False
    for path in paths:
        try:
            git(path, "worktree", "remove", "--", path)
            print(f"Removed {path.name}")
        except (WorkspaceError, OSError) as error:
            print(f"FAIL {path.name}: {error}; workspace metadata kept.", file=sys.stderr)
            failures = True
    if failures:
        return 1
    if entries(workspace):
        raise WorkspaceError("Workspace has unexpected files; keeping directory and metadata.")
    marker = workspace / MARKER
    marker.unlink()
    try:
        workspace.rmdir()  # Never recursively delete a workspace.
    except OSError:
        # Restore only our metadata, without overwriting any newly-created file.
        if not exists(marker):
            with marker.open("x", encoding="utf-8") as stream:
                stream.write(VERSION + "\n")
        raise WorkspaceError("Directory not empty; kept workspace metadata.") from None
    print(f"Removed workspace: {workspace} (branches preserved)")
    return 0


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    for name in ("create", "add", "status", "remove"):
        command = commands.add_parser(name)
        command.add_argument("task")
        if name in ("create", "add"):
            command.add_argument("repos", nargs="*", help="repository names; omit for a numbered menu")
    commands.add_parser("list")
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        repo_root = Path(os.environ.get("WT_REPOS_ROOT") or Path.home() / "Development")
        tasks_root = Path(os.environ.get("WT_TASKS_ROOT") or Path.home() / "Development/tasks")
        if not repo_root.is_absolute() or not tasks_root.is_absolute():
            raise WorkspaceError("WT_REPOS_ROOT and WT_TASKS_ROOT must be absolute paths.")
        repo_root, tasks_root = repo_root.resolve(), tasks_root.resolve()
        if args.command == "list":
            return list_workspaces(tasks_root)
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.task)
                or git(repo_root if repo_root.is_dir() else Path.cwd(), "check-ref-format",
                       f"refs/heads/task/{args.task}", check=False).returncode):
            raise WorkspaceError(f"Unsafe task name: {args.task} (use a single letter/digit/dot/underscore/hyphen name valid as a Git branch).")
        workspace = tasks_root / args.task
        if args.command != "create" or exists(workspace):
            if not managed(workspace):
                raise WorkspaceError(f"Not a managed task workspace: {workspace} (will not overwrite or remove it).")
        if args.command in ("create", "add"):
            validate_roots(repo_root, tasks_root)
            selected = select_repos(discover(repo_root), args.repos)
            if not exists(workspace):
                tasks_root.mkdir(parents=True, exist_ok=True)
                workspace.mkdir()
                with (workspace / MARKER).open("x", encoding="utf-8") as stream:
                    stream.write(VERSION + "\n")
            return create_members(workspace, repo_root, selected, f"task/{args.task}")
        if args.command == "status":
            return status(workspace)
        return remove(workspace)
    except (WorkspaceError, OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted; existing worktrees and branches were kept.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
