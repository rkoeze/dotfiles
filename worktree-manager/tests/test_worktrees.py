"""Integration tests using disposable repositories and only Python's standard library."""

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "worktrees.py"
spec = importlib.util.spec_from_file_location("worktrees", SCRIPT)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class WorktreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mise-worktrees-python-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repos = self.root / "repos with spaces"
        self.tasks = self.root / "tasks with spaces"
        self.repos.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(
            WT_REPOS_ROOT=str(self.repos), WT_TASKS_ROOT=str(self.tasks),
            GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Worktree Test", GIT_AUTHOR_EMAIL="test@example.invalid",
            GIT_COMMITTER_NAME="Worktree Test", GIT_COMMITTER_EMAIL="test@example.invalid",
            PYTHONDONTWRITEBYTECODE="1",
        )
        self.init_repo("api", "main")
        self.init_repo("auth", "master")
        self.init_repo("front end", "main")

    def run_command(self, command, *, input="", ok=True, env=None, cwd=None):
        result = subprocess.run(
            list(map(str, command)), input=input, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env or self.env, cwd=cwd or self.root,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def git(self, repo, *args):
        return self.run_command(["git", "-C", repo, *args]).stdout.strip()

    def wt(self, *args, **kwargs):
        return self.run_command([sys.executable, SCRIPT, *args], **kwargs)

    def init_repo(self, name, branch):
        repo = self.repos / name
        self.git(self.root, "init", "-q", "-b", branch, repo)
        (repo / "tracked").write_text("initial\n")
        self.git(repo, "add", "tracked")
        self.git(repo, "commit", "-qm", "initial")
        return repo

    def assert_worktree(self, task, name, branch=None):
        path = self.tasks / task / name
        self.assertTrue((path / ".git").is_file())
        self.assertEqual(self.git(path, "branch", "--show-current"), branch or f"task/{task}")
        return path

    def test_creation_overlap_add_list_status_and_original_checkout(self):
        api = self.repos / "api"
        self.git(api, "switch", "-qc", "original")
        (api / "original-only").write_text("only on original branch\n")
        self.git(api, "add", "original-only")
        self.git(api, "commit", "-qm", "original branch commit")
        (api / "tracked").write_text("original dirty change\n")
        (api / "untracked").write_text("valuable original data\n")
        before = self.git(api, "status", "--porcelain")
        self.assertIn("No task workspaces", self.wt("list").stdout)
        self.assertFalse(self.tasks.exists())
        self.wt("create", "first", "api", "auth")
        first = self.assert_worktree("first", "api")
        self.assertEqual(self.git(first, "rev-parse", "HEAD"), self.git(api, "rev-parse", "main"))
        self.assertFalse((first / "original-only").exists())
        self.wt("create", "second", "api")
        self.assert_worktree("second", "api")
        self.wt("add", "first", "front end", "front end")
        self.assert_worktree("first", "front end")
        self.assertIn("already included", self.wt("create", "first", "api", "api").stdout)
        listing = self.wt("list").stdout
        for name in ("first", "second", "api", "auth", "front end"):
            self.assertIn(name, listing)
        self.assertIn("task/first", self.wt("status", "first").stdout)
        self.assertEqual(self.git(api, "branch", "--show-current"), "original")
        self.assertEqual(self.git(api, "status", "--porcelain"), before)

    def test_interactive_selection_and_add(self):
        result = self.wt("create", "menu", input="1 3 3\n")
        self.assertIn("1) api", result.stdout)
        self.assertIn("2) auth", result.stdout)
        self.assertIn("3) front end", result.stdout)
        self.assert_worktree("menu", "api")
        self.assert_worktree("menu", "front end")
        self.assertFalse((self.tasks / "menu/auth").exists())
        self.wt("add", "menu", input="2\n")
        self.assert_worktree("menu", "auth")

    def test_invalid_selections_and_inputs_have_no_side_effects(self):
        for selection in ("", "\n", "0\n", "999999\n", "x\n", "1;touch bad\n"):
            with self.subTest(selection=selection):
                self.wt("create", "invalid-menu", input=selection, ok=False)
                self.assertFalse((self.tasks / "invalid-menu").exists())
        for task in ("../escape", "/absolute", "-option", "has space", "a..b", "a.lock", "a/child", "a."):
            with self.subTest(task=task):
                self.wt("create", task, "api", ok=False)
        self.wt("create", "unknown", "api", "missing", ok=False)
        self.wt("add", "missing", "api", ok=False)
        self.wt("status", "missing", ok=False)
        self.wt("remove", "missing", ok=False)
        self.assertFalse(self.tasks.exists())
        for args in ((), ("unknown",), ("list", "extra"), ("status", "task", "extra")):
            with self.subTest(args=args):
                self.wt(*args, ok=False)
        self.wt("--help")
        self.wt("create", "--help")

    def test_root_validation(self):
        for tasks_root in (str(self.repos / "api/tasks"), str(self.repos / "."), "relative"):
            with self.subTest(tasks_root=tasks_root):
                env = dict(self.env, WT_TASKS_ROOT=tasks_root)
                self.wt("create", "unsafe", "api", env=env, ok=False)
        self.wt("create", "unsafe", "api", env=dict(self.env, WT_REPOS_ROOT="relative"), ok=False)
        self.assertFalse((self.repos / "api/tasks").exists())
        self.assertFalse((self.repos / "unsafe").exists())
        self.assertFalse(self.tasks.exists())

    def test_default_branches_and_remote_head_discovery(self):
        custom = self.init_repo("custom", "develop")
        self.git(custom, "remote", "add", "origin", custom)
        self.git(custom, "fetch", "-q", "origin")
        self.git(custom, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/develop")
        upstream = self.init_repo("upstream", "trunk")
        self.git(upstream, "remote", "add", "other", upstream)
        self.wt("create", "defaults", "api", "auth", "custom", "upstream")
        for repo, branch in (("api", "main"), ("auth", "master"), ("custom", "develop"), ("upstream", "trunk")):
            with self.subTest(repo=repo):
                path = self.assert_worktree("defaults", repo)
                self.assertEqual(self.git(path, "rev-parse", "HEAD"),
                                 self.git(self.repos / repo, "rev-parse", branch))

    def test_offline_remote_falls_back_to_local_default(self):
        self.git(self.repos / "api", "remote", "add", "origin", self.root / "nonexistent")
        self.wt("create", "offline", "api")
        self.assert_worktree("offline", "api")

    def test_missing_defaults_empty_workspace_and_branch_reuse(self):
        odd = self.init_repo("odd", "develop")
        result = self.wt("create", "empty", "odd", ok=False)
        self.assertIn("Cannot determine default branch", result.stderr)
        self.wt("remove", "empty")
        self.assertFalse((self.tasks / "empty").exists())
        self.git(odd, "branch", "task/reuse")
        self.assertIn("reused task/reuse", self.wt("create", "reuse", "odd").stdout)

    def test_recorded_but_missing_remote_default_does_not_fall_back(self):
        api = self.repos / "api"
        self.git(api, "remote", "add", "origin", api)
        self.git(api, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/missing")
        result = self.wt("create", "missing-default", "api", ok=False)
        self.assertIn("fetch it first", result.stderr)
        self.assertFalse((self.tasks / "missing-default/api").exists())

    def test_source_dotgit_file_and_shared_repository_conflict(self):
        self.git(self.repos / "api", "worktree", "add", "-qb", "source-alias", self.repos / "linked")
        self.wt("create", "file-source", "linked")
        self.assert_worktree("file-source", "linked")
        self.wt("create", "same", "api")
        result = self.wt("add", "same", "linked", ok=False)
        self.assertIn("checked out at", result.stderr)
        self.assertIn(str(self.tasks / "same/api"), result.stderr)

    def test_conflict_partial_success_and_retry(self):
        api = self.repos / "api"
        outside = self.root / "outside"
        self.git(api, "worktree", "add", "-qb", "task/conflict", outside)
        result = self.wt("create", "conflict", "auth", "api", ok=False)
        self.assertIn(str(outside), result.stderr)
        self.assertIn("successful worktrees and branches were kept", result.stderr)
        self.assert_worktree("conflict", "auth")
        self.assertFalse((self.tasks / "conflict/api").exists())
        self.git(api, "worktree", "remove", outside)
        result = self.wt("add", "conflict", "api")
        self.assertIn("reused task/conflict", result.stdout)
        self.assert_worktree("conflict", "api")

    def test_native_add_failure_does_not_prevent_other_repositories(self):
        # A prefix ref prevents Git from creating task/native in this repository.
        self.git(self.repos / "api", "branch", "task")
        result = self.wt("create", "native", "api", "auth", ok=False)
        self.assertIn("FAIL api", result.stderr)
        self.assertIn("OK auth", result.stdout)
        self.assert_worktree("native", "auth")
        self.git(self.repos / "api", "show-ref", "--verify", "refs/heads/task")
        self.assertTrue((self.tasks / "native" / manager.MARKER).is_file())

    def test_removal_preflight_protects_every_worktree_and_every_change_type(self):
        self.wt("create", "dirty", "api", "auth")
        auth = self.tasks / "dirty/auth"
        (self.repos / "auth/.git/info/exclude").write_text("local.secret\n")
        for kind in ("unstaged", "staged", "untracked", "ignored"):
            with self.subTest(kind=kind):
                if kind in ("unstaged", "staged"):
                    (auth / "tracked").write_text("valuable change\n")
                    if kind == "staged":
                        self.git(auth, "add", "tracked")
                else:
                    (auth / ("local.secret" if kind == "ignored" else "untracked")).write_text("valuable\n")
                self.assertIn("task/dirty", self.wt("status", "dirty").stdout)
                result = self.wt("remove", "dirty", ok=False)
                self.assertIn("UNSAFE auth", result.stderr)
                self.assertIn("Nothing removed", result.stderr)
                self.assert_worktree("dirty", "api")  # Clean first repo must survive.
                self.assert_worktree("dirty", "auth")
                if kind in ("unstaged", "staged"):
                    self.git(auth, "restore", "--staged", "--worktree", "tracked")
                else:
                    (auth / ("local.secret" if kind == "ignored" else "untracked")).unlink()
        self.wt("remove", "dirty")
        self.assertFalse((self.tasks / "dirty").exists())
        for repo in ("api", "auth"):
            self.git(self.repos / repo, "show-ref", "--verify", "refs/heads/task/dirty")
        self.wt("remove", "dirty", ok=False)

    def test_locked_and_unrecognized_entries_block_entire_removal(self):
        self.wt("create", "safe", "api", "auth")
        self.git(self.repos / "auth", "worktree", "lock", self.tasks / "safe/auth")
        result = self.wt("remove", "safe", ok=False)
        self.assertIn("locked", result.stderr)
        self.assert_worktree("safe", "api")
        self.git(self.repos / "auth", "worktree", "unlock", self.tasks / "safe/auth")
        note = self.tasks / "safe/notes.txt"
        note.write_text("keep\n")
        self.wt("remove", "safe", ok=False)
        self.assertEqual(note.read_text(), "keep\n")
        self.assert_worktree("safe", "api")
        note.unlink()
        self.wt("remove", "safe")

    def test_branch_commits_survive_removal_and_recreation(self):
        self.git(self.repos / "auth", "branch", "task/reuse", "master")
        self.assertIn("reused task/reuse", self.wt("create", "reuse", "auth").stdout)
        path = self.tasks / "reuse/auth"
        (path / "tracked").write_text("task commit\n")
        self.git(path, "commit", "-qam", "task work")
        saved = self.git(path, "rev-parse", "HEAD")
        self.wt("remove", "reuse")
        self.wt("create", "reuse", "auth")
        self.assertEqual(self.git(path, "rev-parse", "HEAD"), saved)

    def test_unrelated_directories_symlinks_and_conflicting_destinations(self):
        unrelated = self.tasks / "unrelated"
        unrelated.mkdir(parents=True)
        (unrelated / "file").write_text("keep\n")
        self.wt("create", "unrelated", "api", ok=False)
        self.wt("remove", "unrelated", ok=False)
        self.assertEqual((unrelated / "file").read_text(), "keep\n")
        self.wt("create", "first", "auth")
        alias = self.tasks / "alias"
        alias.symlink_to(self.tasks / "first", target_is_directory=True)
        self.wt("remove", "alias", ok=False)
        self.wt("create", "alias", "api", ok=False)
        self.assert_worktree("first", "auth")
        destination = self.tasks / "first/api"
        for kind in ("symlink", "directory", "file"):
            with self.subTest(kind=kind):
                if kind == "symlink":
                    destination.symlink_to(self.repos / "api", target_is_directory=True)
                elif kind == "directory":
                    destination.mkdir()
                else:
                    destination.write_text("keep\n")
                self.wt("add", "first", "api", ok=False)
                if kind == "directory":
                    destination.rmdir()
                else:
                    destination.unlink()

    def test_existing_marker_is_compatible_and_marker_symlinks_are_rejected(self):
        workspace = self.tasks / "legacy"
        workspace.mkdir(parents=True)
        (workspace / manager.MARKER).write_text("mise-worktree-workspace-v1\n")
        self.wt("add", "legacy", "api")
        self.assert_worktree("legacy", "api")
        self.wt("remove", "legacy")
        workspace.mkdir()
        external = self.root / "external-marker"
        external.write_text(manager.VERSION + "\n")
        (workspace / manager.MARKER).symlink_to(external)
        self.wt("remove", "legacy", ok=False)
        self.assertTrue(external.exists())

    def test_environment_cannot_redirect_git_commands(self):
        env = dict(self.env, GIT_DIR=str(self.repos / "api/.git"),
                   GIT_WORK_TREE=str(self.repos / "api"), GIT_COMMON_DIR=str(self.repos / "api/.git"),
                   GIT_INDEX_FILE=str(self.root / "unrelated-index"))
        self.wt("create", "context", "auth", env=env)
        path = self.assert_worktree("context", "auth")
        self.assertEqual(self.git(path, "rev-parse", "--git-common-dir"), str(self.repos / "auth/.git"))
        self.assertFalse((self.root / "unrelated-index").exists())

    def test_failed_status_prevents_any_removal(self):
        self.wt("create", "preflight", "api", "auth")
        native_git = manager.git

        def failing_git(repo, *args, **kwargs):
            if Path(repo).name == "auth" and args[0] == "status":
                raise manager.WorkspaceError("Cannot read Git status")
            return native_git(repo, *args, **kwargs)

        with mock.patch.dict(os.environ, self.env, clear=True), mock.patch.object(manager, "git", side_effect=failing_git):
            with self.assertRaisesRegex(manager.WorkspaceError, "Nothing removed"):
                manager.remove(self.tasks / "preflight")
        self.assert_worktree("preflight", "api")
        self.assert_worktree("preflight", "auth")

    @unittest.skipUnless(shutil.which("mise"), "Mise is not installed")
    def test_mise_includes_argument_forwarding_interactive_io_and_errors(self):
        self.run_command(["mise", "run", "wt:create", "via-mise", "api", "front end"])
        self.assert_worktree("via-mise", "front end")
        self.run_command(["mise", "run", "wt:create", "../unsafe", "api"], ok=False)
        self.run_command(["mise", "run", "wt:add", "via-mise"], input="2\n")
        self.assert_worktree("via-mise", "auth")
        listing = self.run_command(["mise", "run", "wt:list"]).stdout
        self.assertIn("via-mise", listing)
        self.assertIn("task/via-mise", self.run_command(["mise", "run", "wt:status", "via-mise"]).stdout)
        self.run_command(["mise", "run", "wt:remove", "via-mise"])
        self.assertFalse((self.tasks / "via-mise").exists())


if __name__ == "__main__":
    unittest.main()
